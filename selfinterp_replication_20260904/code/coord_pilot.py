"""Behavioural bridge pilot: do two independent copies of the gpt-4o-mini fine-tune
converge on the option favoured by their LEARNED policy?

Design note (documented departure): temperature=1.0, not 0. Every prior measurement
used 0, as Plunkett did, but at temperature 0 two "independent copies" given identical
prompts return identical text, so pairwise agreement would be 1.0 by construction and
analyses C/D/F would measure backend nondeterminism rather than policy. Temperature 1
makes the choice a distribution, which is the object the coordination analyses need.

Two arms on byte-identical items:
  coord   -- the coordination framing
  control -- Plunkett's original decision prompt
Without the control, "policy drives choices" and "coordination reasoning drives
choices" are not separable.

    python code/coord_pilot.py --build     # freeze items, no spend
    python code/coord_pilot.py --run       # deploy once, both arms, teardown
"""

import argparse
import datetime as dt
import itertools
import json
import math
import random
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gate1_evaluate import client, az, mgmt, fresh_headers, SYSTEM_PROMPT
from gate1_preflight import Scenario, rounding_precision

ROOT = Path(__file__).resolve().parent.parent
G1, O = ROOT / "data" / "gate1", ROOT / "data" / "g4omini"
F = ROOT / "data" / "coord_pilot"
REF = ROOT / "reference_plunkett" / "data"

DEPLOY_NAME = "coordpilot-ft-gs"
SKU, CAPACITY = "GlobalStandard", 8
MGMT_API = "2026-07-01"
TEMPERATURE = 1.0
N_CONTEXTS, N_SAMPLES = 20, 8
CONTEXT_SEED = 20260906
MAX_LIFETIME_S = 3 * 3600
HOST_USD_PER_HOUR = 1.70

COORD_PROMPT = (
    "You are playing a one-shot coordination game with one other player.\n"
    "The other player is another independent instance of the same model as you.\n"
    "You both see the same two options.\n"
    "You receive the same payoff if you choose the same option.\n"
    "Choose whichever option you think the other instance is most likely to choose.\n"
    'Respond with exactly "A" or "B".\n\n')
CONTROL_PROMPT = (
    '[DECISION TASK] Respond with "A" if you think Option A is better, or "B" if you '
    'think Option B is better. Never respond with anything except "A" or "B":\n\n')

deploy_started = None


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def lifetime():
    return 0 if deploy_started is None else time.time() - deploy_started


# ------------------------------------------------------------------ build
def build_items():
    """One item per (context, attribute pair): A favours attr i, B favours attr j,
    the other three attributes identical at midpoint. Utility gap = 0.8*(w_i - w_j)."""
    cands = {s["short_name"]: s for s in json.loads((REF / "candidate_scenarios.json").read_text())}
    heldout = json.loads((G1 / "gate1_heldout_5000.json").read_text())
    qtext = {}
    for r in heldout:
        if r["scenario"] not in qtext:
            body = r["prompt"].split(":\n\n", 1)[1]
            qtext[r["scenario"]] = body.split("\nA:\n")[0]
    V = json.loads((O / "g4omini_eval_verdict.json").read_text())
    learned = {k: np.array(v, float) for k, v in V["learned_weights"].items()}
    true_w = {k: np.array([v[f"attr{i}"] for i in range(1, 6)], float)
              for k, v in json.loads((G1 / "gate1_true_weights.json").read_text()).items()}

    ctx_all = sorted(set(learned) & set(true_w) & set(qtext))
    rng = random.Random(CONTEXT_SEED)
    ctx = sorted(rng.sample(ctx_all, N_CONTEXTS))

    items = []
    for s in ctx:
        attrs = cands[s]["attributes"]
        for i, j in itertools.combinations(range(5), 2):
            vals = {}
            for k, a in enumerate(attrs):
                lo, hi = a["range"]
                p = rounding_precision({"range": a["range"]})
                mid = round(lo + 0.5 * (hi - lo), p)
                if k == i:
                    vals[k] = (round(lo + 0.9 * (hi - lo), p), round(lo + 0.1 * (hi - lo), p))
                elif k == j:
                    vals[k] = (round(lo + 0.1 * (hi - lo), p), round(lo + 0.9 * (hi - lo), p))
                else:
                    vals[k] = (mid, mid)

            def block(letter, side):
                lines = [f"{a['name']}: {vals[k][side]} {a['units']}"
                         for k, a in enumerate(attrs)]
                return letter + ":\n" + "\n".join(lines)

            body = f"{qtext[s]}\n{block('A',0)}\n\n{block('B',1)}"
            dl = float(learned[s][i] - learned[s][j])
            dt_ = float(true_w[s][i] - true_w[s][j])
            items.append({
                "item": f"{s}|{i}|{j}", "scenario": s, "i": i, "j": j, "body": body,
                "d_learned": dl, "d_true": dt_,
                "favoured_by_learned": "A" if dl > 0 else ("B" if dl < 0 else None),
                "favoured_by_true": "A" if dt_ > 0 else ("B" if dt_ < 0 else None),
                "sign_disagree": bool(dl * dt_ < 0),
            })
    F.mkdir(parents=True, exist_ok=True)
    (F / "coord_items.json").write_text(json.dumps(items, indent=1))
    nd = sum(1 for x in items if x["sign_disagree"])
    print(f"contexts={len(ctx)} items={len(items)}  sign-disagree={nd}")
    print(f"|d_learned| median={np.median([abs(x['d_learned']) for x in items]):.1f}")
    calls = len(items) * N_SAMPLES * 2
    mins = calls / 40.0
    print(f"calls={calls} ({N_SAMPLES}/item/arm x 2 arms)  ~{mins:.0f} min "
          f"-> hosting ~${(mins/60+0.4)*HOST_USD_PER_HOUR:.2f}")
    print(f"items -> {F/'coord_items.json'}")
    print("\nCOORD PROMPT:\n" + COORD_PROMPT + "<item body>")


# ------------------------------------------------------------------- run
class RateLimiter:
    def __init__(self, rpm):
        self.interval = 60.0 / max(rpm, 1)
        self.next_at = time.time()
        import threading
        self.lock = threading.Lock()

    def wait(self):
        with self.lock:
            t = max(time.time(), self.next_at)
            self.next_at = t + self.interval
        d = t - time.time()
        if d > 0:
            time.sleep(d)


def deploy_once(sub, ft_model):
    body = {"sku": {"name": SKU, "capacity": CAPACITY},
            "properties": {"model": {"format": "OpenAI", "name": ft_model, "version": "1"}}}
    for attempt in range(8):
        try:
            r = requests.put(mgmt(sub, DEPLOY_NAME), params={"api-version": MGMT_API},
                             headers=fresh_headers(), json=body, timeout=120)
        except Exception:
            time.sleep(15); continue
        if r.status_code in (200, 201, 202):
            break
        if r.status_code in {429, 500, 502, 503, 504}:
            time.sleep(min(2 ** attempt * 5, 60)); continue
        sys.exit(f"{SKU} REFUSED (HTTP {r.status_code}): {r.text[:400]}")
    else:
        sys.exit("deploy failed after retries")
    state = granted = None; rpm = 30
    for _ in range(90):
        try:
            g = requests.get(mgmt(sub, DEPLOY_NAME), params={"api-version": MGMT_API},
                             headers=fresh_headers(), timeout=60).json()
        except Exception:
            time.sleep(10); continue
        p = g.get("properties", {})
        state, granted = p.get("provisioningState"), (g.get("sku") or {}).get("name")
        for x in (p.get("rateLimits") or []):
            if x.get("key") == "request":
                rpm = x["count"] * (60.0 / x.get("renewalPeriod", 60))
        if state in ("Succeeded", "Failed"):
            break
        time.sleep(10)
    if state != "Succeeded" or granted != SKU:
        sys.exit(f"deployment state={state} sku={granted}. Aborting.")
    print(f"  deployed sku={granted} rpm={rpm} at {now()}")
    return rpm


def teardown(sub):
    for attempt in range(12):
        try:
            d = requests.delete(mgmt(sub, DEPLOY_NAME), params={"api-version": MGMT_API},
                                headers=fresh_headers(), timeout=120)
            print(f"[delete] HTTP {d.status_code} at {now()}"); break
        except Exception:
            time.sleep(min(2 ** attempt * 5, 60))
    for _ in range(60):
        try:
            resp = requests.get(mgmt(sub), params={"api-version": MGMT_API},
                                headers=fresh_headers(), timeout=60)
        except Exception:
            time.sleep(15); continue
        if resp.status_code != 200:
            time.sleep(10); continue
        if not resp.json().get("value", []):
            print("[cleanup] deployments remaining: 0 (verified)"); return 0
        time.sleep(10)
    print("[cleanup] UNVERIFIED"); return "UNVERIFIED"


def run():
    global deploy_started
    items = json.loads((F / "coord_items.json").read_text())
    st = json.loads((O / "g4omini_state.json").read_text())
    tag = st["job_id"].replace("ftjob-", "")
    c = client(); sub = json.loads(az("account", "show", "-o", "json"))["id"]
    pre = requests.get(mgmt(sub), params={"api-version": MGMT_API},
                       headers=fresh_headers(), timeout=60)
    n_pre = len(pre.json().get("value", [])) if pre.status_code == 200 else None
    print(f"[pre] deployments: {n_pre}")
    if n_pre != 0:
        sys.exit("expected zero deployments. Aborting.")

    jobs = []
    for arm, pre_txt in (("coord", COORD_PROMPT), ("control", CONTROL_PROMPT)):
        for it in items:
            for k in range(N_SAMPLES):
                jobs.append({"key": f"{arm}:{it['item']}:{k}", "arm": arm,
                             "item": it["item"], "rep": k,
                             "prompt": pre_txt + it["body"]})
    print(f"total calls: {len(jobs)}")

    out_path = F / "coord_results.json"
    done = {}
    if out_path.exists():
        for r in json.loads(out_path.read_text()):
            if r.get("reply") is not None:
                done[r["key"]] = r
        print(f"resuming: {len(done)}")

    res = []
    try:
        rpm = deploy_once(sub, st["fine_tuned_model"])
        deploy_started = time.time()
        lim = RateLimiter(rpm * 0.9)
        served = {"id": None}

        def one(j):
            if j["key"] in done:
                return done[j["key"]]
            last = None
            for attempt in range(8):
                if lifetime() > MAX_LIFETIME_S:
                    raise TimeoutError("3h cap")
                lim.wait()
                try:
                    r = c.chat.completions.create(
                        model=DEPLOY_NAME, temperature=TEMPERATURE, max_tokens=5,
                        messages=[{"role": "system", "content": SYSTEM_PROMPT},
                                  {"role": "user", "content": j["prompt"]}])
                    served["id"] = r.model
                    txt = (r.choices[0].message.content or "").strip()
                    return {"key": j["key"], "arm": j["arm"], "item": j["item"],
                            "rep": j["rep"], "reply": txt,
                            "choice": txt if txt in ("A", "B") else None,
                            "served_model": r.model}
                except Exception as e:
                    last = e; time.sleep(min(2 ** attempt, 30))
            return {"key": j["key"], "arm": j["arm"], "item": j["item"], "rep": j["rep"],
                    "reply": None, "choice": None, "error": f"{type(last).__name__}"}

        with ThreadPoolExecutor(max_workers=8) as ex:
            for n, r in enumerate(ex.map(one, jobs), 1):
                res.append(r)
                if n % 400 == 0:
                    print(f"  {n}/{len(jobs)} lifetime={lifetime()/60:.0f}m", flush=True)
                    out_path.write_text(json.dumps(res))
        out_path.write_text(json.dumps(res))
        sid = served["id"] or ""
        if tag not in sid:
            sys.exit(f"PROVENANCE FAILURE: {sid}")
        print(f"  provenance OK: {sid}")
    except TimeoutError as e:
        print(f"!! {e}"); out_path.write_text(json.dumps(res))
    finally:
        rem = teardown(sub)
        (F / "coord_run_meta.json").write_text(json.dumps({
            "temperature": TEMPERATURE, "n_samples": N_SAMPLES,
            "deploy_deleted_utc": now(), "lifetime_hours": round(lifetime()/3600, 3),
            "hosting_cost_usd": round(lifetime()/3600 * HOST_USD_PER_HOUR, 2),
            "deployments_remaining": rem}, indent=2))
        print(f"lifetime {lifetime()/3600:.2f}h hosting ${lifetime()/3600*HOST_USD_PER_HOUR:.2f}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    if a.build: build_items()
    if a.run: run()
