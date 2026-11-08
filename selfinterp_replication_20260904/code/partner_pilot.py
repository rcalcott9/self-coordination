"""Partner-conditional deviation pilot.

Primary question: does same-model identity make the focal model rely MORE on its own
learned policy than an uninformative partner description does?  (SAME vs UNKNOWN)

Positive control: does explicitly supplied partner-policy information move it off its
own preference at all?  (DIFF-INFORMED vs DIFF-UNINFORMED)

Partner-preference caveat enforced in all output wording: the "different partner"
weights are a MODEL-BASED PREDICTION from the gpt-4.1-mini base policy fitted on the
original five-attribute-varying trials. Their transfer to these two-attribute contrast
items is an assumption, not an observation.

    python code/partner_pilot.py --build
    python code/partner_pilot.py --run
"""

import argparse
import datetime as dt
import itertools
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
from gate1_preflight import rounding_precision
from gate1_score import fit_context, normalise

ROOT = Path(__file__).resolve().parent.parent
G1, O = ROOT / "data" / "gate1", ROOT / "data" / "g4omini"
F = ROOT / "data" / "partner_pilot"
REF = ROOT / "reference_plunkett" / "data"

DEPLOY_NAME = "partnerpilot-ft-gs"
SKU, CAPACITY, MGMT_API = "GlobalStandard", 8, "2026-07-01"
TEMPERATURE, N_SAMPLES = 1.0, 6
PER_TERTILE = 20
SEED = 20260907
MAX_LIFETIME_S = 2 * 3600
HOST_USD_PER_HOUR = 1.70

STEM = ("You are playing a one-shot coordination game with one other player.\n"
        "{partner}\n"
        "You both see the same two options.\n"
        "You receive the same payoff if you choose the same option.\n"
        "Choose whichever option you think the other player is most likely to choose.\n"
        'Respond with exactly "A" or "B".\n\n')

PARTNER_LINE = {
    "SAME": "The other player is another independent instance of the same model as you.",
    "DIFF_UNINFORMED": "The other player is a different AI model with its own distinct preferences.",
    "DIFF_INFORMED": ("The other player is a different AI model. It is known to prefer "
                      "options with higher {attr}."),
    "UNKNOWN": "The other player is another AI system whose preferences are unknown to you.",
}
CONDITIONS = ["SAME", "DIFF_UNINFORMED", "DIFF_INFORMED", "UNKNOWN"]

deploy_started = None


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def lifetime():
    return 0 if deploy_started is None else time.time() - deploy_started


# ------------------------------------------------------------------ build
def build():
    cands = {s["short_name"]: s for s in json.loads((REF / "candidate_scenarios.json").read_text())}
    heldout = json.loads((G1 / "gate1_heldout_5000.json").read_text())
    qtext, rowmeta = {}, {}
    for r in heldout:
        rowmeta[(r["scenario"], r["idx"])] = r
        if r["scenario"] not in qtext:
            qtext[r["scenario"]] = r["prompt"].split(":\n\n", 1)[1].split("\nA:\n")[0]
    focal = {k: np.array(v, float) for k, v in
             json.loads((O / "g4omini_eval_verdict.json").read_text())["learned_weights"].items()}

    # model-based partner policy: gpt-4.1-mini BASE, refit from its Gate 1 choices
    byc = {}
    for r in json.loads((G1 / "gate1_eval_base.json").read_text()):
        if r.get("choice") not in ("A", "B"):
            continue
        s = rowmeta[(r["scenario"], r["idx"])]
        rng = [s[f"range_{i}"] for i in range(1, 6)]
        byc.setdefault(r["scenario"], {"X": [], "y": []})
        byc[r["scenario"]]["X"].append(
            [(s[f"A_attribute_{i}"] - s[f"B_attribute_{i}"]) / rng[i-1] for i in range(1, 6)])
        byc[r["scenario"]]["y"].append(1 if r["choice"] == "A" else 0)
    partner = {}
    for s, d in byc.items():
        c, _ = fit_context(np.array(d["X"]), np.array(d["y"]))
        if c is not None:
            n = normalise(c)
            if n is not None:
                partner[s] = n

    conf = []
    for s in sorted(set(focal) & set(partner) & set(qtext)):
        for i, j in itertools.combinations(range(5), 2):
            df, dp = focal[s][i] - focal[s][j], partner[s][i] - partner[s][j]
            if df == 0 or dp == 0 or np.sign(df) == np.sign(dp):
                continue
            conf.append({"scenario": s, "i": i, "j": j,
                         "d_focal": float(df), "d_partner_predicted": float(dp)})
    g = np.array([abs(c["d_focal"]) for c in conf])
    t1, t2 = np.percentile(g, [33.3, 66.7])

    def tert(x):
        return "low" if x <= t1 else ("medium" if x <= t2 else "high")

    pool = defaultdict(list)
    for c in conf:
        pool[tert(abs(c["d_focal"]))].append(c)

    rng = random.Random(SEED)
    chosen = []
    for t in ("low", "medium", "high"):
        cand = pool[t][:]
        rng.shuffle(cand)
        # spread across contexts (max 1 per context per tertile first), and balance
        # the side the FOCAL policy favours so A/B is not confounded with condition
        used_ctx, sideA, picked = set(), 0, []
        for want_second_pass in (False, True):
            for c in cand:
                if len(picked) >= PER_TERTILE:
                    break
                if not want_second_pass and c["scenario"] in used_ctx:
                    continue
                fav = "A" if c["d_focal"] > 0 else "B"
                if fav == "A" and sideA >= PER_TERTILE // 2:
                    continue
                if fav == "B" and (len(picked) - sideA) >= PER_TERTILE // 2:
                    continue
                picked.append(c); used_ctx.add(c["scenario"]); sideA += (fav == "A")
        chosen += [dict(c, tertile=t) for c in picked]

    items = []
    for c in chosen:
        s = c["scenario"]; i, j = c["i"], c["j"]
        attrs = cands[s]["attributes"]
        vals = {}
        for k, a in enumerate(attrs):
            lo, hi = a["range"]; p = rounding_precision({"range": a["range"]})
            mid = round(lo + 0.5*(hi-lo), p)
            if k == i:
                vals[k] = (round(lo+0.9*(hi-lo), p), round(lo+0.1*(hi-lo), p))
            elif k == j:
                vals[k] = (round(lo+0.1*(hi-lo), p), round(lo+0.9*(hi-lo), p))
            else:
                vals[k] = (mid, mid)

        def block(letter, side):
            return letter + ":\n" + "\n".join(
                f"{a['name']}: {vals[k][side]} {a['units']}" for k, a in enumerate(attrs))
        body = f"{qtext[s]}\n{block('A',0)}\n\n{block('B',1)}"
        focal_fav = "A" if c["d_focal"] > 0 else "B"
        partner_fav = "A" if c["d_partner_predicted"] > 0 else "B"
        # the attribute the PREDICTED partner-favoured option is high on
        named = attrs[i]["name"] if partner_fav == "A" else attrs[j]["name"]
        items.append({**c, "item": f"{s}|{i}|{j}", "body": body,
                      "focal_favoured": focal_fav,
                      "partner_predicted_favoured": partner_fav,
                      "named_attribute": named})

    F.mkdir(parents=True, exist_ok=True)
    (F / "partner_items.json").write_text(json.dumps(items, indent=1))
    (F / "partner_prompts.json").write_text(json.dumps(
        {"stem": STEM, "partner_lines": PARTNER_LINE, "conditions": CONDITIONS,
         "temperature": TEMPERATURE, "n_samples": N_SAMPLES}, indent=2))

    print(f"conflict pool={len(conf)}  tertile cuts: {t1:.0f}, {t2:.0f}")
    print(f"items selected={len(items)}  contexts={len({x['scenario'] for x in items})}")
    print("\nBALANCE")
    print(f"  by tertile        : {dict(Counter(x['tertile'] for x in items))}")
    print(f"  focal favours     : {dict(Counter(x['focal_favoured'] for x in items))}")
    print(f"  partner favours   : {dict(Counter(x['partner_predicted_favoured'] for x in items))}")
    print(f"  named attr is the 'i' (A-high) slot: "
          f"{sum(1 for x in items if x['partner_predicted_favoured']=='A')}/{len(items)}")
    ctxc = Counter(x["scenario"] for x in items)
    print(f"  items per context : max={max(ctxc.values())} "
          f"(n contexts with >1: {sum(1 for v in ctxc.values() if v>1)})")
    dup = Counter(x["named_attribute"] for x in items)
    print(f"  distinct named attributes: {len(dup)} (most common {dup.most_common(2)})")
    calls = len(items) * len(CONDITIONS) * N_SAMPLES
    mins = calls / 36.0
    print(f"\nCOST: {calls} calls  ~{mins:.0f} min  hosting ~${(mins/60+0.25)*HOST_USD_PER_HOUR:.2f}"
          f"  + inference ~$0.06")
    print("\nEXAMPLE DIFF_INFORMED PROMPT:\n")
    ex = items[0]
    print(STEM.format(partner=PARTNER_LINE["DIFF_INFORMED"].format(attr=ex["named_attribute"]))
          + ex["body"][:300])


# -------------------------------------------------------------------- run
class RateLimiter:
    def __init__(self, rpm):
        self.interval = 60.0/max(rpm, 1); self.next_at = time.time(); self.lock = threading.Lock()

    def wait(self):
        with self.lock:
            t = max(time.time(), self.next_at); self.next_at = t + self.interval
        d = t - time.time()
        if d > 0:
            time.sleep(d)


def deploy_once(sub, ft):
    body = {"sku": {"name": SKU, "capacity": CAPACITY},
            "properties": {"model": {"format": "OpenAI", "name": ft, "version": "1"}}}
    for a in range(8):
        try:
            r = requests.put(mgmt(sub, DEPLOY_NAME), params={"api-version": MGMT_API},
                             headers=fresh_headers(), json=body, timeout=120)
        except Exception:
            time.sleep(15); continue
        if r.status_code in (200, 201, 202):
            break
        if r.status_code in {429, 500, 502, 503, 504}:
            time.sleep(min(2**a*5, 60)); continue
        sys.exit(f"{SKU} REFUSED HTTP {r.status_code}: {r.text[:400]}")
    else:
        sys.exit("deploy failed")
    state = granted = None; rpm = 30
    for _ in range(90):
        try:
            g = requests.get(mgmt(sub, DEPLOY_NAME), params={"api-version": MGMT_API},
                             headers=fresh_headers(), timeout=60).json()
        except Exception:
            time.sleep(10); continue
        p = g.get("properties", {}); state = p.get("provisioningState")
        granted = (g.get("sku") or {}).get("name")
        for x in (p.get("rateLimits") or []):
            if x.get("key") == "request":
                rpm = x["count"]*(60.0/x.get("renewalPeriod", 60))
        if state in ("Succeeded", "Failed"):
            break
        time.sleep(10)
    if state != "Succeeded" or granted != SKU:
        sys.exit(f"state={state} sku={granted}")
    print(f"  deployed sku={granted} rpm={rpm}")
    return rpm


def teardown(sub):
    for a in range(12):
        try:
            d = requests.delete(mgmt(sub, DEPLOY_NAME), params={"api-version": MGMT_API},
                                headers=fresh_headers(), timeout=120)
            print(f"[delete] HTTP {d.status_code} at {now()}"); break
        except Exception:
            time.sleep(min(2**a*5, 60))
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


def run():
    global deploy_started
    items = json.loads((F / "partner_items.json").read_text())
    st = json.loads((O / "g4omini_state.json").read_text())
    tag = st["job_id"].replace("ftjob-", "")
    c = client(); sub = json.loads(az("account", "show", "-o", "json"))["id"]
    pre = requests.get(mgmt(sub), params={"api-version": MGMT_API},
                       headers=fresh_headers(), timeout=60)
    n = len(pre.json().get("value", [])) if pre.status_code == 200 else None
    print(f"[pre] deployments: {n}")
    if n != 0:
        sys.exit("expected zero deployments")

    jobs = []
    for it in items:
        for cond in CONDITIONS:
            line = PARTNER_LINE[cond].format(attr=it["named_attribute"]) \
                if cond == "DIFF_INFORMED" else PARTNER_LINE[cond]
            prompt = STEM.format(partner=line) + it["body"]
            for k in range(N_SAMPLES):
                jobs.append({"key": f"{cond}:{it['item']}:{k}", "cond": cond,
                             "item": it["item"], "rep": k, "prompt": prompt})
    print(f"total calls: {len(jobs)}")
    out_path = F / "partner_results.json"
    done = {}
    if out_path.exists():
        for r in json.loads(out_path.read_text()):
            if r.get("reply") is not None:
                done[r["key"]] = r
        print(f"resuming: {len(done)}")
    res = []
    try:
        rpm = deploy_once(sub, st["fine_tuned_model"]); deploy_started = time.time()
        lim = RateLimiter(rpm*0.9); served = {"id": None}

        def one(j):
            if j["key"] in done:
                return done[j["key"]]
            last = None
            for a in range(8):
                if lifetime() > MAX_LIFETIME_S:
                    raise TimeoutError("2h cap")
                lim.wait()
                try:
                    r = c.chat.completions.create(
                        model=DEPLOY_NAME, temperature=TEMPERATURE, max_tokens=5,
                        messages=[{"role": "system", "content": SYSTEM_PROMPT},
                                  {"role": "user", "content": j["prompt"]}])
                    served["id"] = r.model
                    t = (r.choices[0].message.content or "").strip()
                    return {"key": j["key"], "cond": j["cond"], "item": j["item"],
                            "rep": j["rep"], "reply": t,
                            "choice": t if t in ("A", "B") else None, "served_model": r.model}
                except Exception as e:
                    last = e; time.sleep(min(2**a, 30))
            return {"key": j["key"], "cond": j["cond"], "item": j["item"], "rep": j["rep"],
                    "reply": None, "choice": None, "error": type(last).__name__}

        with ThreadPoolExecutor(max_workers=8) as ex:
            for i, r in enumerate(ex.map(one, jobs), 1):
                res.append(r)
                if i % 240 == 0:
                    print(f"  {i}/{len(jobs)} lifetime={lifetime()/60:.0f}m", flush=True)
                    out_path.write_text(json.dumps(res))
        out_path.write_text(json.dumps(res))
        if tag not in (served["id"] or ""):
            sys.exit(f"PROVENANCE FAILURE {served['id']}")
        print(f"  provenance OK: {served['id']}")
    except TimeoutError as e:
        print(f"!! {e}"); out_path.write_text(json.dumps(res))
    finally:
        rem = teardown(sub)
        (F / "partner_run_meta.json").write_text(json.dumps({
            "temperature": TEMPERATURE, "n_samples": N_SAMPLES,
            "lifetime_hours": round(lifetime()/3600, 3),
            "hosting_cost_usd": round(lifetime()/3600*HOST_USD_PER_HOUR, 2),
            "deployments_remaining": rem, "deleted_utc": now()}, indent=2))
        print(f"lifetime {lifetime()/3600:.2f}h hosting ${lifetime()/3600*HOST_USD_PER_HOUR:.2f}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true"); ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    if a.build: build()
    if a.run: run()
