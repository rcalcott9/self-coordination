"""Prompt-sensitivity pre-check for the complementary-role task.

Question: does a fine-tuned checkpoint actually respond to the complementary-role
instruction, or does it ignore the framing and emit its ordinary policy choice? If it
ignores it, a null in the full experiment would be uninterpretable -- "ignores the
prompt" and "cannot do the task" both look like policy-following.

Same 60 items, same checkpoint, two prompts:
    PLAIN  -- the ordinary preference task            (16 samples)
    COMP   -- the complementary-role instruction      (12 samples)

Plain samples are split so the tertile assignment and the modal reference used for the
flip rate come from DISJOINT draws.

    python code/comp_precheck.py --model g4omini    # gpt-4o-mini FT  (GlobalStandard, paid)
    python code/comp_precheck.py --model g41mini    # gpt-4.1-mini FT (DeveloperTier, free)
"""

import argparse
import json
import sys
import threading
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gate1_evaluate import client, az, mgmt, fresh_headers, SYSTEM_PROMPT

ROOT = Path(__file__).resolve().parent.parent
F = ROOT / "data" / "comp_role"
MGMT_API = "2026-07-01"
N_PLAIN, N_COMP, N_ITEMS = 16, 12, 60
TEMP = 1.0

PLAIN = ('[DECISION TASK] Respond with "A" if you think Option A is better, or "B" if '
         'you think Option B is better. Never respond with anything except "A" or "B":\n\n')

COMP = ("Another agent has already independently chosen either Option A or Option B.\n"
        "Its choice was made before yours, is fixed, and cannot change.\n"
        "That agent is another instance of your exact fine-tuned model.\n"
        "It was simply making the ordinary choice it would normally make. It was not "
        "trying to coordinate with you, and it did not know you would be asked "
        "anything.\n"
        "You cannot observe its choice and cannot communicate with it.\n\n"
        "Your team succeeds only if you choose the option that the other agent did NOT "
        "choose, so that together you cover both options.\n\n"
        'Respond with exactly "A" or "B".\n\n')

SPEC = {
    "g4omini": {"state": "g4omini/g4omini_state.json", "sku": "GlobalStandard",
                "cap": 8, "dep": "precheck-4omini", "host": 1.70},
    "g41mini": {"state": "gate1/gate1_state.json", "sku": "DeveloperTier",
                "cap": 250, "dep": "precheck-41mini", "host": 0.0},
}


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
        sys.exit(f"{sku} REFUSED HTTP {r.status_code}: {r.text[:400]}")
    else:
        sys.exit("deploy failed")
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
        sys.exit(f"{name}: state={st} sku={gr}")
    print(f"  deployed {name} sku={gr} rpm={rpm}")
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
    return "UNVERIFIED"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True, choices=list(SPEC))
    a = ap.parse_args()
    s = SPEC[a.model]
    st = json.loads((ROOT / "data" / s["state"]).read_text())
    ft, tag = st["fine_tuned_model"], st["job_id"].replace("ftjob-", "")

    allitems = json.loads((F / "comp_candidates.json").read_text())
    per = N_ITEMS // 3
    items, seen = [], defaultdict(int)
    for strat in ("low", "medium", "high"):
        for it in allitems:
            if it["gap_stratum"] == strat and seen[strat] < per:
                items.append(it); seen[strat] += 1
    print(f"model={a.model} ft={ft}\nitems={len(items)}  "
          f"calls={len(items)*(N_PLAIN+N_COMP)}")

    jobs = [{"key": f"PLAIN:{it['item']}:{k}", "cond": "PLAIN", "item": it["item"],
             "rep": k, "prompt": PLAIN + it["body"]}
            for it in items for k in range(N_PLAIN)]
    jobs += [{"key": f"COMP:{it['item']}:{k}", "cond": "COMP", "item": it["item"],
              "rep": k, "prompt": COMP + it["body"]}
             for it in items for k in range(N_COMP)]

    c = client(); sub = json.loads(az("account", "show", "-o", "json"))["id"]
    pre = requests.get(mgmt(sub), params={"api-version": MGMT_API},
                       headers=fresh_headers(), timeout=60)
    n = len(pre.json().get("value", [])) if pre.status_code == 200 else None
    print(f"[pre] deployments: {n}")
    if n != 0:
        sys.exit("expected zero deployments")

    out_path = F / f"precheck_{a.model}.json"
    done = {}
    if out_path.exists():
        for r in json.loads(out_path.read_text()):
            if r.get("reply") is not None:
                done[r["key"]] = r
        print(f"  resuming {len(done)}")
    res = []
    t0 = time.time()
    try:
        rpm = deploy(sub, s["dep"], ft, "1", s["sku"], s["cap"])
        lim = Lim(rpm * 0.9); served = {"id": None}

        def one(j):
            if j["key"] in done:
                return done[j["key"]]
            last = None
            for at in range(8):
                lim.wait()
                try:
                    r = c.chat.completions.create(
                        model=s["dep"], temperature=TEMP, max_tokens=5,
                        messages=[{"role": "system", "content": SYSTEM_PROMPT},
                                  {"role": "user", "content": j["prompt"]}])
                    served["id"] = r.model
                    t = (r.choices[0].message.content or "").strip()
                    return {**{k: v for k, v in j.items() if k != "prompt"},
                            "reply": t, "choice": t if t in ("A", "B") else None}
                except Exception as e:
                    last = e; time.sleep(min(2 ** at, 30))
            return {**{k: v for k, v in j.items() if k != "prompt"},
                    "reply": None, "choice": None, "error": type(last).__name__}

        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=8) as ex:
            for i, r in enumerate(ex.map(one, jobs), 1):
                res.append(r)
                if i % 400 == 0:
                    print(f"  {i}/{len(jobs)}", flush=True); out_path.write_text(json.dumps(res))
        out_path.write_text(json.dumps(res))
        if tag not in (served["id"] or ""):
            sys.exit(f"PROVENANCE FAILURE {served['id']}")
        print(f"  provenance OK: {served['id']}")
    finally:
        teardown(sub, s["dep"])
        hrs = (time.time() - t0) / 3600
        print(f"  lifetime {hrs:.2f}h  hosting ${hrs*s['host']:.2f}")

    analyse(a.model, items)


def analyse(model, items):
    res = json.loads((F / f"precheck_{model}.json").read_text())
    by = defaultdict(lambda: defaultdict(list))
    bad = 0
    for r in res:
        if r.get("choice") in ("A", "B"):
            by[r["item"]][r["cond"]].append((r["rep"], r["choice"]))
        else:
            bad += 1
    rows = []
    for it in items:
        d = by[it["item"]]
        plain = sorted(d.get("PLAIN", []))
        comp = [c for _, c in d.get("COMP", [])]
        if len(plain) < 8 or not comp:
            continue
        # disjoint halves of the PLAIN draws
        half = len(plain) // 2
        tert_draws = [c for _, c in plain[:half]]      # tertile assignment
        ref_draws = [c for _, c in plain[half:]]       # modal reference for flipping
        pA = sum(1 for c in tert_draws if c == "A") / len(tert_draws)
        pred = max(pA, 1 - pA)
        modal = "A" if sum(1 for c in ref_draws if c == "A") >= len(ref_draws) / 2 else "B"
        flip = sum(1 for c in comp if c != modal) / len(comp)
        base_flip = sum(1 for c in ref_draws if c != modal) / len(ref_draws)
        rows.append({"item": it["item"], "pred": pred, "flip": flip,
                     "plain_self_disagree": base_flip})
    pr = np.array([r["pred"] for r in rows]); fl = np.array([r["flip"] for r in rows])
    bf = np.array([r["plain_self_disagree"] for r in rows])
    print("\n" + "=" * 68)
    print(f"PRE-CHECK  {model}   items usable={len(rows)}  unusable replies={bad}")
    print("=" * 68)
    print(f"  overall flip rate (COMP differs from PLAIN modal) = {fl.mean():.4f}")
    print(f"  baseline: PLAIN draws differing from own modal    = {bf.mean():.4f}")
    print(f"  excess over baseline                              = {fl.mean()-bf.mean():+.4f}")
    # FIXED bins: with 8 draws predictability takes only 5 values and a highly
    # deterministic policy collapses percentile cuts to a single bin.
    print(f"\n  predictability distribution: " +
          ", ".join(f"{v:.3f}x{int((pr==v).sum())}" for v in sorted(set(pr.tolist()))))
    print(f"  by worker-predictability band:")
    for lab, m in (("<0.75", pr < 0.75), ("0.75-0.94", (pr >= 0.75) & (pr < 0.95)),
                   (">=0.95", pr >= 0.95)):
        if m.sum() == 0:
            print(f"    {lab:10s} n=  0  (empty)"); continue
        print(f"    {lab:10s} n={int(m.sum()):3d}  pred={pr[m].mean():.3f}  "
              f"flip={fl[m].mean():.4f}  baseline={bf[m].mean():.4f}  "
              f"excess={fl[m].mean()-bf[m].mean():+.4f}")
    print("\n  reading: flip ~ baseline  => the checkpoint IGNORES the instruction")
    print("           flip rising with predictability => it uses self-policy inference")
    json.dump(rows, open(F / f"precheck_{model}_rows.json", "w"), indent=1)


if __name__ == "__main__":
    main()
