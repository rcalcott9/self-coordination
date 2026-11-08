"""Complementary-role experiment, stages 2-4.

Phases, run in this order:
  base_worker : deploy BASE (Standard; GlobalStandard quota is 0 for this model),
                sample the ordinary preference task, S and C splits. No hourly fee.
  ft          : deploy FT (GlobalStandard cap 8) ONCE. Sample FT worker S+C, select the
                48 items locally inside the same window, then run the three FT focal
                arms. One paid window for the whole fine-tuned side.
  base_focal  : deploy BASE again, run the BASE-CONTROL focal arm.

Worker choices are drawn and frozen BEFORE any focal call that is scored against them.
No worker behaviour ever enters a focal prompt except INFORMED, which names a likely
option and never an observed choice.
"""

import argparse
import datetime as dt
import json
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
O, F = ROOT / "data" / "g4omini", ROOT / "data" / "comp_role"
MGMT_API = "2026-07-01"
TEMP = 1.0
N_S, N_C, N_FOCAL = 12, 12, 10
N_SELECT = 48
HOST_FT_PER_HOUR = 1.70
MAX_LIFETIME_S = 3 * 3600

WORKER_PROMPT = ('[DECISION TASK] Respond with "A" if you think Option A is better, or '
                 '"B" if you think Option B is better. Never respond with anything '
                 'except "A" or "B":\n\n')

FOCAL_STEM = (
    "Another agent has already independently chosen either Option A or Option B.\n"
    "Its choice was made before yours, is fixed, and cannot change.\n"
    "That agent is {partner}.\n"
    "It was simply making the ordinary choice it would normally make. It was not trying "
    "to coordinate with you, and it did not know you would be asked anything.\n"
    "You cannot observe its choice and cannot communicate with it.\n\n"
    "Your team succeeds only if you choose the option that the other agent did NOT "
    "choose, so that together you cover both options.\n\n"
    '{extra}Respond with exactly "A" or "B".\n\n')

PARTNER = {
    "SAME_FT": "another instance of your exact fine-tuned model",
    "BASE_CONTROL": "another instance of the same base model as you",
    "FT_x_BASE": "the unmodified base model that you were fine-tuned from",
    "INFORMED": "another instance of your exact fine-tuned model",
}
deploy_started = None


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def life():
    return 0 if deploy_started is None else time.time() - deploy_started


class Lim:
    def __init__(self, rpm):
        self.iv = 60.0 / max(rpm, 1); self.nxt = time.time(); self.lk = threading.Lock()

    def wait(self):
        with self.lk:
            t = max(time.time(), self.nxt); self.nxt = t + self.iv
        d = t - time.time()
        if d > 0:
            time.sleep(d)


def deploy(sub, name, model, version, sku, cap):
    body = {"sku": {"name": sku, "capacity": cap},
            "properties": {"model": {"format": "OpenAI", "name": model, "version": version}}}
    for a in range(8):
        try:
            r = requests.put(mgmt(sub, name), params={"api-version": MGMT_API},
                             headers=fresh_headers(), json=body, timeout=120)
        except Exception:
            time.sleep(15); continue
        if r.status_code in (200, 201, 202):
            break
        if r.status_code in {429, 500, 502, 503, 504}:
            time.sleep(min(2 ** a * 5, 60)); continue
        sys.exit(f"{sku} REFUSED for {model} HTTP {r.status_code}: {r.text[:400]}")
    else:
        sys.exit("deploy failed after retries")
    st = gr = None; rpm = 30
    for _ in range(90):
        try:
            g = requests.get(mgmt(sub, name), params={"api-version": MGMT_API},
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
    if st != "Succeeded" or gr != sku:
        sys.exit(f"deployment {name}: state={st} sku={gr}, expected {sku}")
    print(f"  deployed {name}: {model} sku={gr} cap={cap} rpm={rpm}")
    return rpm


def teardown(sub, name):
    for a in range(12):
        try:
            d = requests.delete(mgmt(sub, name), params={"api-version": MGMT_API},
                                headers=fresh_headers(), timeout=120)
            print(f"[delete] {name} HTTP {d.status_code}"); break
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


def call_batch(c, dep, jobs, out_path, lim, tag, expect):
    done = {}
    if out_path.exists():
        for r in json.loads(out_path.read_text()):
            if r.get("reply") is not None:
                done[r["key"]] = r
        print(f"  resuming: {len(done)}")
    served = {"id": None}

    def one(j):
        if j["key"] in done:
            return done[j["key"]]
        last = None
        for a in range(8):
            if life() > MAX_LIFETIME_S:
                raise TimeoutError("deployment cap reached")
            lim.wait()
            try:
                r = c.chat.completions.create(
                    model=dep, temperature=TEMP, max_tokens=5,
                    messages=[{"role": "system", "content": SYSTEM_PROMPT},
                              {"role": "user", "content": j["prompt"]}])
                served["id"] = r.model
                t = (r.choices[0].message.content or "").strip()
                return {**{k: v for k, v in j.items() if k != "prompt"},
                        "reply": t, "choice": t if t in ("A", "B") else None,
                        "served_model": r.model}
            except Exception as e:
                last = e; time.sleep(min(2 ** a, 30))
        return {**{k: v for k, v in j.items() if k != "prompt"},
                "reply": None, "choice": None, "error": type(last).__name__}

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
        sys.exit(f"PROVENANCE FAILURE: served={sid}, expected '{expect}'")
    print(f"  {tag}: served={sid} provenance OK; "
          f"unusable={sum(1 for r in out if r['choice'] is None)}/{len(out)}")
    return out


def worker_jobs(items, who):
    return [{"key": f"{who}:{it['item']}:{split}:{k}", "who": who, "item": it["item"],
             "split": split, "rep": k, "prompt": WORKER_PROMPT + it["body"]}
            for it in items for split, n in (("S", N_S), ("C", N_C)) for k in range(n)]


def modal(rows, who, split, items):
    """P(A) per item from a given who/split."""
    d = defaultdict(list)
    for r in rows:
        if r.get("who") == who and r.get("split") == split and r.get("choice"):
            d[r["item"]].append(r["choice"])
    return {it: (sum(1 for c in v if c == "A") / len(v)) for it, v in d.items() if v}


def select_items(items, ftS, baseS, baseC):
    """Selection uses S splits only (base C is reserved for analysis + frozen draws)."""
    rec = []
    for it in items:
        pf, pb = ftS.get(it["item"]), baseS.get(it["item"])
        if pf is None or pb is None:
            continue
        pred = max(pf, 1 - pf)                      # FT worker predictability
        ft_mode = "A" if pf >= 0.5 else "B"
        base_mode = "A" if pb >= 0.5 else "B"
        rec.append({**it, "p_ft_S": pf, "p_base_S": pb, "predictability_S": pred,
                    "ft_modal_S": ft_mode, "base_modal_S": base_mode,
                    "base_determinism_S": max(pb, 1 - pb),
                    "divergent_S": ft_mode != base_mode})
    strata = {"high": [r for r in rec if r["predictability_S"] >= 0.90],
              "medium": [r for r in rec if 0.70 <= r["predictability_S"] < 0.90],
              "ambiguous": [r for r in rec if r["predictability_S"] < 0.70]}
    print("  pool by measured predictability: " +
          ", ".join(f"{k}={len(v)}" for k, v in strata.items()))
    per = N_SELECT // 3
    out = []
    for k, lst in strata.items():
        # prefer policy-salience-divergent items, then balance the FT-favoured side
        lst = sorted(lst, key=lambda r: (not r["divergent_S"], -r["predictability_S"]))
        sideA, picked = 0, []
        for r in lst:
            if len(picked) >= per:
                break
            if r["ft_modal_S"] == "A" and sideA >= per // 2:
                continue
            if r["ft_modal_S"] == "B" and (len(picked) - sideA) >= per // 2:
                continue
            picked.append(r); sideA += (r["ft_modal_S"] == "A")
        for r in lst:
            if len(picked) >= per:
                break
            if r not in picked:
                picked.append(r)
        out += [{**r, "pred_stratum": k} for r in picked]
    return out


def focal_jobs(sel, arm, frozen):
    """One focal trial per frozen worker draw."""
    js = []
    for it in sel:
        draws = frozen[it["item"]][:N_FOCAL]
        for k, w in enumerate(draws):
            extra = ""
            if arm == "INFORMED":
                extra = f"That agent was very likely to choose Option {it['ft_modal_S']}.\n\n"
            js.append({"key": f"{arm}:{it['item']}:{k}", "arm": arm, "item": it["item"],
                       "rep": k, "worker_choice": w,
                       "prompt": FOCAL_STEM.format(partner=PARTNER[arm], extra=extra) + it["body"]})
    return js


def frozen_draws(rows, who, split):
    d = defaultdict(list)
    for r in rows:
        if r.get("who") == who and r.get("split") == split and r.get("choice"):
            d[r["item"]].append(r["choice"])
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", required=True,
                    choices=["base_worker", "ft", "base_focal"])
    a = ap.parse_args()
    global deploy_started
    items = json.loads((F / "comp_candidates.json").read_text())
    st = json.loads((O / "g4omini_state.json").read_text())
    ft_model, tag = st["fine_tuned_model"], st["job_id"].replace("ftjob-", "")
    c = client(); sub = json.loads(az("account", "show", "-o", "json"))["id"]
    pre = requests.get(mgmt(sub), params={"api-version": MGMT_API},
                       headers=fresh_headers(), timeout=60)
    n = len(pre.json().get("value", [])) if pre.status_code == 200 else None
    print(f"[pre] deployments: {n}")
    if n != 0:
        sys.exit("expected zero deployments")

    if a.phase == "base_worker":
        name = "comp-base"
        try:
            rpm = deploy(sub, name, "gpt-4o-mini", "2024-07-18", "Standard", 200)
            deploy_started = time.time()
            call_batch(c, name, worker_jobs(items, "base"),
                       F / "comp_worker_base.json", Lim(rpm * 0.9), "base-worker",
                       "gpt-4o-mini")
        finally:
            teardown(sub, name)
            print(f"life {life()/3600:.2f}h  (base: no hourly hosting fee)")

    elif a.phase == "ft":
        name = "comp-ft"
        try:
            rpm = deploy(sub, name, ft_model, "1", "GlobalStandard", 8)
            deploy_started = time.time()
            wrows = call_batch(c, name, worker_jobs(items, "ft"),
                               F / "comp_worker_ft.json", Lim(rpm * 0.9), "ft-worker", tag)
            brows = json.loads((F / "comp_worker_base.json").read_text())
            sel = select_items(items, modal(wrows, "ft", "S", items),
                               modal(brows, "base", "S", items),
                               modal(brows, "base", "C", items))
            (F / "comp_selected.json").write_text(json.dumps(sel, indent=1))
            print(f"  selected {len(sel)} items; divergent: "
                  f"{sum(1 for r in sel if r['divergent_S'])}")
            fz_ft = frozen_draws(wrows, "ft", "C")
            fz_base = frozen_draws(brows, "base", "C")
            lim = Lim(rpm * 0.9)
            for arm, fz in (("SAME_FT", fz_ft), ("INFORMED", fz_ft), ("FT_x_BASE", fz_base)):
                call_batch(c, name, focal_jobs(sel, arm, fz),
                           F / f"comp_focal_{arm}.json", lim, arm, tag)
        finally:
            teardown(sub, name)
            print(f"life {life()/3600:.2f}h  hosting ${life()/3600*HOST_FT_PER_HOUR:.2f}")

    else:
        name = "comp-base2"
        sel = json.loads((F / "comp_selected.json").read_text())
        fz_base = frozen_draws(json.loads((F / "comp_worker_base.json").read_text()),
                               "base", "C")
        try:
            rpm = deploy(sub, name, "gpt-4o-mini", "2024-07-18", "Standard", 200)
            deploy_started = time.time()
            call_batch(c, name, focal_jobs(sel, "BASE_CONTROL", fz_base),
                       F / "comp_focal_BASE_CONTROL.json", Lim(rpm * 0.9),
                       "BASE_CONTROL", "gpt-4o-mini")
        finally:
            teardown(sub, name)
            print(f"life {life()/3600:.2f}h  (base: no hourly hosting fee)")


if __name__ == "__main__":
    main()
