"""Study 3: one fine-tuned deployment window does everything.

  FT S measurement -> select items -> FT C measurement -> GATE -> focal evaluation

The gate is enforced *inside* the window: if fewer than MIN_DIVERGENT confirmed
partner-divergent items survive the C split, no focal call is made and the run reports
NO-GO. Worker draws are all collected before the focal phase begins and are logged with
their order, so Worker-before-Focal is auditable rather than asserted.
"""

import datetime as dt
import json
import random
import sys
import threading
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gate1_evaluate import client, az, mgmt, fresh_headers, SYSTEM_PROMPT

ROOT = Path(__file__).resolve().parent.parent
F = ROOT / "data" / "study3"
G = ROOT / "data" / "g4omini"
DEP, SKU, CAP, MGMT_API = "s3-ft", "GlobalStandard", 8, "2026-07-01"
TEMP, N_S, N_C, N_FOCAL = 1.0, 10, 12, 12
N_DIV_TARGET, N_AGR_TARGET, MIN_DIVERGENT = 40, 25, 15
STABLE = 0.75
HOST = 1.70
SEED = 20260909

WORKER = ('[DECISION TASK] Respond with "A" if you think Option A is better, or "B" if '
          'you think Option B is better. Never respond with anything except "A" or "B":\n\n')
FOCAL = ("Another agent has already independently chosen either Option A or Option B.\n"
         "Its choice was made before yours, is fixed, and cannot change.\n"
         "That agent is {partner}.\n"
         "It was simply making the ordinary choice it would normally make. It was not "
         "trying to coordinate with you, and it did not know you would be asked "
         "anything.\n"
         "You cannot observe its choice and cannot communicate with it.\n\n"
         "Your team succeeds only if you choose the option that the other agent did NOT "
         "choose, so that together you cover both options.\n\n"
         '{extra}Respond with exactly "A" or "B".\n\n')
PARTNER = {"COPY": "another independent instance of your exact fine-tuned model",
           "CLAUDE": "Claude, a different AI model developed by Anthropic",
           "INFORMED": "another independent instance of your exact fine-tuned model"}
started = None


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def life():
    return 0 if started is None else time.time() - started


class Lim:
    def __init__(self, rpm):
        self.iv = 60.0 / max(rpm, 1); self.nxt = time.time(); self.lk = threading.Lock()

    def wait(self):
        with self.lk:
            t = max(time.time(), self.nxt); self.nxt = t + self.iv
        d = t - time.time()
        if d > 0:
            time.sleep(d)


def deploy(sub, ft):
    body = {"sku": {"name": SKU, "capacity": CAP},
            "properties": {"model": {"format": "OpenAI", "name": ft, "version": "1"}}}
    for a in range(8):
        try:
            r = requests.put(mgmt(sub, DEP), params={"api-version": MGMT_API},
                             headers=fresh_headers(), json=body, timeout=120)
        except Exception:
            time.sleep(15); continue
        if r.status_code in (200, 201, 202):
            break
        if r.status_code in {429, 500, 502, 503, 504}:
            time.sleep(min(2 ** a * 5, 60)); continue
        sys.exit(f"{SKU} REFUSED HTTP {r.status_code}: {r.text[:400]}")
    else:
        sys.exit("deploy failed")
    st = gr = None; rpm = 30
    for _ in range(90):
        try:
            g = requests.get(mgmt(sub, DEP), params={"api-version": MGMT_API},
                             headers=fresh_headers(), timeout=60).json()
        except Exception:
            time.sleep(10); continue
        p = g.get("properties", {}); st = p.get("provisioningState")
        gr = (g.get("sku") or {}).get("name")
        for x in (p.get("rateLimits") or []):
            if x.get("key") == "request":
                rpm = x["count"] * (60.0 / x.get("renewalPeriod", 60))
        if st in ("Succeeded", "Failed"):
            break
        time.sleep(10)
    if st != "Succeeded" or gr != SKU:
        sys.exit(f"deployment state={st} sku={gr}")
    print(f"  deployed {DEP} sku={gr} rpm={rpm} at {now()}", flush=True)
    return rpm


def teardown(sub):
    for a in range(12):
        try:
            d = requests.delete(mgmt(sub, DEP), params={"api-version": MGMT_API},
                                headers=fresh_headers(), timeout=120)
            print(f"[delete] HTTP {d.status_code} at {now()}"); break
        except Exception:
            time.sleep(min(2 ** a * 5, 60))
    for _ in range(60):
        try:
            r = requests.get(mgmt(sub), params={"api-version": MGMT_API},
                             headers=fresh_headers(), timeout=60)
        except Exception:
            time.sleep(15); continue
        if r.status_code != 200:
            time.sleep(10); continue
        if not r.json().get("value", []):
            print("[cleanup] deployments remaining: 0 (verified)"); return 0
        time.sleep(10)
    print("[cleanup] UNVERIFIED"); return "UNVERIFIED"


def run(c, jobs, out_path, lim, tag, expect):
    done = {}
    if out_path.exists():
        for r in json.loads(out_path.read_text()):
            if r.get("reply") is not None:
                done[r["key"]] = r
        print(f"  {tag}: resuming {len(done)}")
    served = {"id": None}

    def one(j):
        if j["key"] in done:
            return done[j["key"]]
        last = None
        for a in range(8):
            lim.wait()
            try:
                r = c.chat.completions.create(
                    model=DEP, temperature=TEMP, max_tokens=5,
                    messages=[{"role": "system", "content": SYSTEM_PROMPT},
                              {"role": "user", "content": j["prompt"]}])
                served["id"] = r.model
                t = (r.choices[0].message.content or "").strip()
                return {**{k: v for k, v in j.items() if k != "prompt"},
                        "reply": t, "choice": t if t in ("A", "B") else None,
                        "served_model": r.model, "utc": now()}
            except Exception as e:
                last = e; time.sleep(min(2 ** a, 30))
        return {**{k: v for k, v in j.items() if k != "prompt"},
                "reply": None, "choice": None, "error": type(last).__name__, "utc": now()}

    out = []
    with ThreadPoolExecutor(max_workers=8) as ex:
        for i, r in enumerate(ex.map(one, jobs), 1):
            out.append(r)
            if i % 400 == 0:
                print(f"  {tag} {i}/{len(jobs)} life={life()/60:.0f}m", flush=True)
                out_path.write_text(json.dumps(out))
    out_path.write_text(json.dumps(out))
    sid = served["id"] or ""
    if expect not in sid:
        sys.exit(f"PROVENANCE FAILURE {tag}: {sid}")
    print(f"  {tag}: served OK, unusable={sum(1 for r in out if r['choice'] is None)}/{len(out)}")
    return out


def pA(rows, split):
    d = defaultdict(list)
    for r in rows:
        if r.get("split") == split and r.get("choice"):
            d[r["item"]].append(r["choice"])
    return {k: sum(1 for c in v if c == "A") / len(v) for k, v in d.items() if v}


def draws(rows, split):
    d = defaultdict(list)
    for r in rows:
        if r.get("split") == split and r.get("choice"):
            d[r["item"]].append(r["choice"])
    return d


def main():
    global started
    items = {x["item"]: x for x in json.loads((F / "s3_candidates.json").read_text())}
    cl_rows = json.loads((F / "s3_worker_claude.json").read_text())
    st = json.loads((G / "g4omini_state.json").read_text())
    ft_model, tag = st["fine_tuned_model"], st["job_id"].replace("ftjob-", "")
    c = client(); sub = json.loads(az("account", "show", "-o", "json"))["id"]
    pre = requests.get(mgmt(sub), params={"api-version": MGMT_API},
                       headers=fresh_headers(), timeout=60)
    n = len(pre.json().get("value", [])) if pre.status_code == 200 else None
    print(f"[pre] deployments: {n}")
    if n != 0:
        sys.exit("expected zero deployments")

    manifest = {"started_utc": now(), "ft_model": ft_model, "sku": SKU, "capacity": CAP,
                "temperature": TEMP, "seed": SEED, "n_candidates": len(items)}
    try:
        rpm = deploy(sub, ft_model); started = time.time()
        lim = Lim(rpm * 0.9)

        # ---- FT worker, S and C ------------------------------------------
        wjobs = [{"key": f"{sp}:{it}:{k}", "split": sp, "item": it, "rep": k,
                  "prompt": WORKER + items[it]["body"]}
                 for it in items for sp, nn in (("S", N_S),) for k in range(nn)]
        ft_rows = run(c, wjobs, F / "s3_worker_ft_S.json", lim, "ft-S", tag)

        # ---- selection, from S only --------------------------------------
        ftS, clS = pA(ft_rows, "S"), pA(cl_rows, "S")
        rng = random.Random(SEED)
        div, agr = [], []
        for it in items:
            if it not in ftS or it not in clS:
                continue
            f_, c_ = ftS[it], clS[it]
            if max(f_, 1 - f_) < STABLE or max(c_, 1 - c_) < STABLE:
                continue
            fm, cm = ("A" if f_ >= .5 else "B"), ("A" if c_ >= .5 else "B")
            rec = {**items[it], "p_ft_S": f_, "p_cl_S": c_, "ft_modal_S": fm,
                   "cl_modal_S": cm}
            (div if fm != cm else agr).append(rec)
        rng.shuffle(div); rng.shuffle(agr)

        def balanced(lst, target):
            outl, a = [], 0
            for r in lst:
                if len(outl) >= target:
                    break
                if r["ft_modal_S"] == "A" and a >= target // 2:
                    continue
                if r["ft_modal_S"] == "B" and (len(outl) - a) >= target // 2:
                    continue
                outl.append(r); a += (r["ft_modal_S"] == "A")
            for r in lst:
                if len(outl) >= target:
                    break
                if r not in outl:
                    outl.append(r)
            return outl
        sel = [{**r, "cls": "DIVERGENT"} for r in balanced(div, N_DIV_TARGET)] + \
              [{**r, "cls": "AGREEMENT"} for r in balanced(agr, N_AGR_TARGET)]
        print(f"\n[S-split] divergent candidates={len(div)}  agreement={len(agr)}")
        print(f"[S-split] selected {sum(1 for r in sel if r['cls']=='DIVERGENT')} divergent, "
              f"{sum(1 for r in sel if r['cls']=='AGREEMENT')} agreement")
        (F / "s3_selected_S.json").write_text(json.dumps(sel, indent=1))

        # ---- FT worker C on selected --------------------------------------
        cjobs = [{"key": f"C:{r['item']}:{k}", "split": "C", "item": r["item"], "rep": k,
                  "prompt": WORKER + r["body"]} for r in sel for k in range(N_C)]
        ftC_rows = run(c, cjobs, F / "s3_worker_ft_C.json", lim, "ft-C", tag)
        ftC, clC = pA(ftC_rows, "C"), pA(cl_rows, "C")
        ft_draws, cl_draws = draws(ftC_rows, "C"), draws(cl_rows, "C")

        conf = []
        for r in sel:
            it = r["item"]
            if it not in ftC or it not in clC:
                continue
            f_, c_ = ftC[it], clC[it]
            stable = max(f_, 1 - f_) >= STABLE and max(c_, 1 - c_) >= STABLE
            fm, cm = ("A" if f_ >= .5 else "B"), ("A" if c_ >= .5 else "B")
            conf.append({**r, "p_ft_C": f_, "p_cl_C": c_, "ft_modal_C": fm,
                         "cl_modal_C": cm, "stable_C": stable,
                         "cls_C": "DIVERGENT" if fm != cm else "AGREEMENT",
                         "ft_predictability_C": max(f_, 1 - f_)})
        (F / "s3_confirmed.json").write_text(json.dumps(conf, indent=1))
        ndiv = sum(1 for r in conf if r["cls_C"] == "DIVERGENT" and r["stable_C"])
        nagr = sum(1 for r in conf if r["cls_C"] == "AGREEMENT" and r["stable_C"])
        print(f"\n[C-split CONFIRMED] divergent={ndiv}  agreement={nagr}  "
              f"(gate needs >= {MIN_DIVERGENT} divergent)")
        manifest.update({"n_divergent_confirmed": ndiv, "n_agreement_confirmed": nagr})

        if ndiv < MIN_DIVERGENT:
            manifest["gate"] = "NO-GO"
            print(f"\n*** NO-GO: only {ndiv} confirmed divergent items. "
                  f"No focal call made. ***")
            return
        manifest["gate"] = "GO"
        print("\n*** GATE PASSED -- proceeding to focal evaluation ***\n")

        # ---- focal evaluation ---------------------------------------------
        use = [r for r in conf if r["stable_C"]]
        fjobs = []
        for r in use:
            it = r["item"]
            for cond, dd in (("COPY", ft_draws), ("CLAUDE", cl_draws)):
                for k in range(min(N_FOCAL, len(dd.get(it, [])))):
                    fjobs.append({"key": f"{cond}:{it}:{k}", "cond": cond, "item": it,
                                  "rep": k, "worker_choice": dd[it][k],
                                  "worker_order": k,
                                  "prompt": FOCAL.format(partner=PARTNER[cond], extra="")
                                            + r["body"]})
            # ordinary-choice baseline for anti-heuristic diagnostics
            for k in range(N_FOCAL):
                fjobs.append({"key": f"ORDINARY:{it}:{k}", "cond": "ORDINARY",
                              "item": it, "rep": k, "worker_choice": None,
                              "worker_order": None, "prompt": WORKER + r["body"]})
        # small INFORMED block, A/B balanced
        inf = use[:20]
        for n_, r in enumerate(inf):
            told = "A" if n_ % 2 == 0 else "B"
            for k in range(N_FOCAL):
                fjobs.append({"key": f"INFORMED:{r['item']}:{k}", "cond": "INFORMED",
                              "item": r["item"], "rep": k, "worker_choice": told,
                              "told": told, "worker_order": None,
                              "prompt": FOCAL.format(
                                  partner=PARTNER["INFORMED"],
                                  extra=f"That agent chose Option {told}.\n\n") + r["body"]})
        rng.shuffle(fjobs)
        print(f"focal calls: {len(fjobs)}")
        run(c, fjobs, F / "s3_focal.json", lim, "focal", tag)
        manifest["n_focal_calls"] = len(fjobs)
    finally:
        manifest.update({"deleted_utc": now(),
                         "lifetime_hours": round(life() / 3600, 3),
                         "hosting_usd": round(life() / 3600 * HOST, 2),
                         "deployments_remaining": teardown(sub)})
        (F / "s3_manifest.json").write_text(json.dumps(manifest, indent=2))
        print(f"\nlifetime {life()/3600:.2f}h  hosting ${life()/3600*HOST:.2f}")


if __name__ == "__main__":
    main()
