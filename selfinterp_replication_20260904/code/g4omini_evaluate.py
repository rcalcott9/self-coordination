"""gpt-4o-mini introspection replication -- stage 2. ONE deployment, both phases.

Sequence (frozen):
  confirm 0 deployments -> deploy once on GlobalStandard -> verify granted SKU
  -> verify served-model provenance -> 5,000 acquisition calls -> score locally
  -> apply frozen threshold r >= 0.70
     FAIL: stop, no introspection calls, delete, verify, write verdict
     PASS: continue in the SAME deployment to 1,000 Plunkett self-report calls
  -> delete, retry until independent verification shows zero -> score -> verdict

Hard stop: if deployment lifetime reaches 4h, evaluation stops and teardown runs
rather than exceeding the preflight cap.
"""

import datetime as dt
import json
import sys
import threading
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gate1_evaluate import client, az, mgmt, fresh_headers, SYSTEM_PROMPT
from gate1_score import fit_context, normalise, z, boot_ci
from gate2a_elicit import parse_strict

ROOT = Path(__file__).resolve().parent.parent
G1 = ROOT / "data" / "gate1"
G2 = ROOT / "data" / "gate2a"
OUT = ROOT / "data" / "g4omini"
STATE = OUT / "g4omini_state.json"

DEPLOY_NAME = "g4omini-ft-gs"
SKU = "GlobalStandard"          # the ONLY sku this script may send
CAPACITY = 8                    # subscription quota ceiling for this model
MGMT_API = "2026-07-01"
ACQ_THRESHOLD = 0.70            # frozen, identical to Gate 1
MAX_LIFETIME_S = 4 * 3600       # preflight cap
HOST_USD_PER_HOUR = 1.70

deploy_started = None


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def lifetime():
    return 0 if deploy_started is None else time.time() - deploy_started


def check_cap(phase):
    if lifetime() > MAX_LIFETIME_S:
        raise TimeoutError(f"4h deployment cap reached during {phase}; tearing down")


class RateLimiter:
    """Requests-per-minute bucket. Quota here is ~8k TPM, far tighter than Gate 1."""
    def __init__(self, rpm):
        self.interval = 60.0 / max(rpm, 1)
        self.lock = threading.Lock()
        self.next_at = time.time()

    def wait(self):
        with self.lock:
            t = max(time.time(), self.next_at)
            self.next_at = t + self.interval
        d = t - time.time()
        if d > 0:
            time.sleep(d)


def deploy_once(sub):
    body = {"sku": {"name": SKU, "capacity": CAPACITY},
            "properties": {"model": {"format": "OpenAI",
                                     "name": json.loads(STATE.read_text())["fine_tuned_model"],
                                     "version": "1"}}}
    TRANSIENT = {429, 500, 502, 503, 504}
    for attempt in range(8):
        try:
            r = requests.put(mgmt(sub, DEPLOY_NAME), params={"api-version": MGMT_API},
                             headers=fresh_headers(), json=body, timeout=120)
        except Exception as e:
            print(f"  deploy transport {type(e).__name__}; retry"); time.sleep(15); continue
        if r.status_code in (200, 201, 202):
            break
        if r.status_code in TRANSIENT:
            print(f"  transient HTTP {r.status_code}; retry"); time.sleep(min(2**attempt*5, 60)); continue
        sys.exit(f"{SKU} deployment REFUSED (HTTP {r.status_code}):\n{r.text[:600]}\n"
                 f"Aborting -- no SKU substitution.")
    else:
        sys.exit("deployment failed after retries")

    state = granted = rl = None
    for _ in range(90):
        try:
            g = requests.get(mgmt(sub, DEPLOY_NAME), params={"api-version": MGMT_API},
                             headers=fresh_headers(), timeout=60).json()
        except Exception:
            time.sleep(10); continue
        p = g.get("properties", {})
        state, granted = p.get("provisioningState"), (g.get("sku") or {}).get("name")
        rl = p.get("rateLimits")
        if state in ("Succeeded", "Failed"):
            break
        time.sleep(10)
    if state != "Succeeded" or granted != SKU:
        sys.exit(f"deployment state={state} granted_sku={granted}; expected {SKU}. Aborting.")
    print(f"  deployed {DEPLOY_NAME}: sku={granted} capacity={CAPACITY} at {now()}")
    rpm = 30
    for x in (rl or []):
        if x.get("key") == "request":
            rpm = x["count"] * (60.0 / x.get("renewalPeriod", 60))
        print(f"    rateLimit: {x}")
    return granted, rpm


def run_calls(c, jobs, out_path, limiter, phase, expect_tag):
    done = {}
    if out_path.exists():
        for r in json.loads(out_path.read_text()):
            if r.get("reply") is not None:
                done[r["key"]] = r
        print(f"  resuming: {len(done)} present")
    served = {"id": None}

    def one(j):
        if j["key"] in done:
            return done[j["key"]]
        last = None
        for attempt in range(8):
            check_cap(phase)
            limiter.wait()
            try:
                resp = c.chat.completions.create(
                    model=DEPLOY_NAME, temperature=0, max_tokens=j["max_tokens"],
                    messages=j["messages"])
                served["id"] = resp.model
                return {"key": j["key"], "scenario": j["scenario"], "idx": j["idx"],
                        "reply": resp.choices[0].message.content,
                        "finish_reason": resp.choices[0].finish_reason,
                        "completion_tokens": resp.usage.completion_tokens,
                        "served_model": resp.model}
            except Exception as e:
                last = e
                time.sleep(min(2 ** attempt, 30))
        return {"key": j["key"], "scenario": j["scenario"], "idx": j["idx"],
                "reply": None, "error": f"{type(last).__name__}: {last}"}

    out = []
    with ThreadPoolExecutor(max_workers=8) as ex:
        for i, r in enumerate(ex.map(one, jobs), 1):
            out.append(r)
            if i % 250 == 0:
                print(f"  [{phase}] {i}/{len(jobs)}  lifetime={lifetime()/60:.0f}m", flush=True)
                out_path.write_text(json.dumps(out))
    out_path.write_text(json.dumps(out))
    sid = served["id"] or ""
    if expect_tag not in sid:
        sys.exit(f"PROVENANCE FAILURE: served={sid}, expected to contain {expect_tag}")
    print(f"  [{phase}] served_model={sid}  provenance OK")
    return out


def score_acquisition(res):
    rows = {(r["scenario"], r["idx"]): r
            for r in json.loads((G1 / "gate1_heldout_5000.json").read_text())}
    true_w = json.loads((G1 / "gate1_true_weights.json").read_text())
    byc = {}; invalid = 0
    for r in res:
        ch = (r.get("reply") or "").strip()
        if ch not in ("A", "B"):
            invalid += 1; continue
        s = rows[(r["scenario"], r["idx"])]
        rng = [s[f"range_{i}"] for i in range(1, 6)]
        d = byc.setdefault(r["scenario"], {"X": [], "y": [], "hit": []})
        d["X"].append([(s[f"A_attribute_{i}"] - s[f"B_attribute_{i}"]) / rng[i-1] for i in range(1, 6)])
        d["y"].append(1 if ch == "A" else 0)
        d["hit"].append(1 if ch == s["target"] else 0)
    L, T, ctxs, per, fails, learned = [], [], [], [], [], {}
    for s in sorted(byc):
        d = byc[s]; acc = float(np.mean(d["hit"]))
        co, status = fit_context(np.array(d["X"]), np.array(d["y"]))
        if co is None:
            fails.append({"scenario": s, "reason": status}); per.append(
                {"scenario": s, "n": len(d["y"]), "accuracy": acc, "fit": status, "usable": False}); continue
        nb = normalise(co)
        if nb is None:
            fails.append({"scenario": s, "reason": "all-zero"}); per.append(
                {"scenario": s, "n": len(d["y"]), "accuracy": acc, "fit": "all-zero", "usable": False}); continue
        tw = np.array([true_w[s][f"attr{i}"] for i in range(1, 6)], float)
        learned[s] = nb; L.append(nb); T.append(tw); ctxs += [s]*5
        per.append({"scenario": s, "n": len(d["y"]), "accuracy": acc, "fit": status,
                    "usable": True, "r_within_context": float(np.corrcoef(nb, tw)[0, 1])})
    L = np.concatenate(L); T = np.concatenate(T)
    r = float(np.corrcoef(z(L), z(T))[0, 1]); lo, hi = boot_ci(L, T, ctxs)
    return {"r": r, "ci95": [lo, hi],
            "heldout_choice_accuracy": float(np.mean([p["accuracy"] for p in per])),
            "n_contexts_total": len(byc), "n_contexts_usable": len(learned),
            "n_contexts_failed": len(fails), "failures": fails,
            "n_invalid_responses": invalid, "per_context": per}, learned


def teardown(sub):
    for attempt in range(12):
        try:
            d = requests.delete(mgmt(sub, DEPLOY_NAME), params={"api-version": MGMT_API},
                                headers=fresh_headers(), timeout=120)
            print(f"[delete] HTTP {d.status_code} at {now()}")
            break
        except Exception as e:
            print(f"[delete] attempt {attempt}: {type(e).__name__}; retry")
            time.sleep(min(2**attempt*5, 60))
    for _ in range(60):
        try:
            resp = requests.get(mgmt(sub), params={"api-version": MGMT_API},
                                headers=fresh_headers(), timeout=60)
        except Exception as e:
            print(f"[cleanup] list {type(e).__name__}; retry"); time.sleep(15); continue
        if resp.status_code != 200:
            time.sleep(10); continue
        items = resp.json().get("value", [])
        if not items:
            print("[cleanup] deployments remaining: 0 (verified)"); return 0
        time.sleep(10)
    print("[cleanup] !! COULD NOT VERIFY -- check manually")
    return "UNVERIFIED"


def main():
    global deploy_started
    st = json.loads(STATE.read_text())
    if st.get("job_status") != "succeeded":
        sys.exit(f"training not succeeded (status={st.get('job_status')})")
    tag = st["job_id"].replace("ftjob-", "")
    c = client(); sub = json.loads(az("account", "show", "-o", "json"))["id"]

    pre = requests.get(mgmt(sub), params={"api-version": MGMT_API},
                       headers=fresh_headers(), timeout=60)
    n_pre = len(pre.json().get("value", [])) if pre.status_code == 200 else None
    print(f"[pre] deployments before start: {n_pre}")
    if n_pre != 0:
        sys.exit("expected zero deployments before starting. Aborting.")

    verdict = {"model": st["fine_tuned_model"], "sku": SKU, "capacity": CAPACITY,
               "acquisition_threshold": ACQ_THRESHOLD}
    try:
        granted, rpm = deploy_once(sub)
        deploy_started = time.time()
        verdict.update({"granted_sku": granted, "deploy_created_utc": now(),
                        "measured_rpm_limit": rpm})
        limiter = RateLimiter(rpm * 0.9)
        print(f"  rate limiter set to {rpm*0.9:.0f} req/min")

        # ---- phase 1: acquisition -------------------------------------------
        heldout = json.loads((G1 / "gate1_heldout_5000.json").read_text())
        jobs = [{"key": f"acq:{r['scenario']}:{r['idx']}", "scenario": r["scenario"],
                 "idx": r["idx"], "max_tokens": 5,
                 "messages": [{"role": "system", "content": SYSTEM_PROMPT},
                              {"role": "user", "content": r["prompt"]}]} for r in heldout]
        res = run_calls(c, jobs, OUT / "g4omini_acq.json", limiter, "acq", tag)
        acq, learned = score_acquisition(res)
        verdict["acquisition"] = acq
        passed = acq["r"] >= ACQ_THRESHOLD
        verdict["acquisition_pass"] = bool(passed)
        print(f"\n  ACQUISITION r={acq['r']:+.4f} [{acq['ci95'][0]:+.4f},{acq['ci95'][1]:+.4f}] "
              f"acc={acq['heldout_choice_accuracy']:.4f} usable={acq['n_contexts_usable']}"
              f"/{acq['n_contexts_total']} -> {'PASS' if passed else 'FAIL'}")

        # ---- phase 2: zero-shot self-report (same deployment) ----------------
        if passed:
            trials = json.loads((G2 / "gate2a_report_trials.json").read_text())
            jobs = [{"key": f"rep:{r['scenario']}:{r['idx']}", "scenario": r["scenario"],
                     "idx": r["idx"], "max_tokens": 800,
                     "messages": [{"role": "system", "content": SYSTEM_PROMPT},
                                  {"role": "user", "content": r["prompt"]}]} for r in trials]
            rep = run_calls(c, jobs, OUT / "g4omini_reports.json", limiter, "report", tag)
            verdict["self_report_ran"] = True
            verdict["learned_weights"] = {k: list(map(float, v)) for k, v in learned.items()}
        else:
            verdict["self_report_ran"] = False
            print("  acquisition FAILED -- no introspection calls made")
    except TimeoutError as e:
        verdict["aborted"] = str(e)
        print(f"!! {e}")
    finally:
        verdict["deploy_deleted_utc"] = now()
        verdict["deployment_lifetime_hours"] = round(lifetime()/3600, 3)
        verdict["deployments_remaining"] = teardown(sub)
        verdict["hosting_cost_usd"] = round(lifetime()/3600 * HOST_USD_PER_HOUR, 2)
        (OUT / "g4omini_eval_verdict.json").write_text(json.dumps(verdict, indent=2, default=str))
        print(f"\nlifetime {verdict['deployment_lifetime_hours']}h  "
              f"hosting ${verdict['hosting_cost_usd']}")


if __name__ == "__main__":
    main()
