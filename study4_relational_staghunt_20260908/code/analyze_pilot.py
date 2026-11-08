"""STAGE 2 analysis - action arm, prediction arm, and the asymmetric-vs-control interaction.

SAMPLING UNITS. Responses within an array; arrays across the item-type contrast. All
uncertainty is a model-free cluster bootstrap: arrays resampled with replacement within
item type, then the 24 responses resampled within each drawn array. Combinatorial
response pairs are NEVER treated as independent observations - COPY coordination uses
the bias-corrected estimator sum_k n_k(n_k-1)/[N(N-1)], which excludes self-pairs by
construction, and a seeded 12-disjoint-pair draw supplies the realized payoff.
"""
import json, math, os, re, sys
from collections import Counter, defaultdict

EXP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(EXP, "pilot")
STIM = os.path.join(EXP, "stimuli_pilot")
BOOT, BSEED = 4000, 20260908104

_CH = re.compile(r"CHOICE:\s*\[?\s*([1-4])\b", re.I)
_PR = re.compile(r"^\s*P([1-4])\s*:\s*\[?\s*(\d{1,3})", re.I | re.M)


def parse_choice(t):
    m = _CH.findall(t or "")
    return int(m[-1]) - 1 if m else None


def parse_probs(t):
    """Four probabilities over SLOTS, or None. Never a default on failure."""
    d = {}
    for k, v in _PR.findall(t or ""):
        d[int(k) - 1] = int(v)
    if len(d) != 4:
        return None
    tot = sum(d.values())
    if not (90 <= tot <= 110) or tot == 0:
        return None
    return [d[i] / tot for i in range(4)]


def load(run_dir):
    man = json.load(open(os.path.join(P, "PILOT_MANIFEST_FINAL.json")))
    spec = json.load(open(os.path.join(P, "STRATEGIC_RUN_LOCKED.json")))
    recs = {r["array_id"]: r for r in man["asymmetric"] + man["controls"]}
    mf = {sid: json.load(open(os.path.join(STIM, sid, "manifest.json"))) for sid in recs}
    # One job_key can appear more than once: a transport failure recorded by the main
    # pass and its SUCCESS recorded by the later repair pass. Keep the successful
    # attempt. A key with only failures stays a failure and is counted as one - it is
    # never dropped, and no attempt is deleted from the jsonl.
    best, attempts = {}, Counter()
    for fn in sorted(os.listdir(os.path.join(run_dir, "data"))):
        if not fn.endswith(".jsonl"):
            continue
        for line in open(os.path.join(run_dir, "data", fn)):
            d = json.loads(line)
            k = d["job_key"]
            attempts[k] += 1
            if k not in best or (d["ok"] and not best[k]["ok"]):
                best[k] = d
    dup = {k: n for k, n in attempts.items() if n > 1}
    rows = list(best.values())
    for r in rows:
        r["_attempts"] = attempts[r["job_key"]]
    return man, spec, recs, mf, rows, dup


def build(run_dir):
    man, spec, recs, mf, rows, dup = load(run_dir)
    integ = dict(n_rows=len(rows), transport_fail=0, parse_fail_action=0,
                 parse_fail_predict=0, prob_sum_fail=0, checkpoints=Counter(),
                 retried_job_keys=len(dup), n_unique_jobs=len(rows))
    A = defaultdict(list)          # (sid, role, arm, condition) -> parsed trials
    for d in rows:
        integ["checkpoints"][d["api_model"]] += 1
        if not d["ok"]:
            integ["transport_fail"] += 1
            continue
        perm = mf[d["sid"]][str(d["perm_id"])]
        key = (d["sid"], d["role"], d["arm"], d["condition"])
        if d["arm"] == "action":
            pos = parse_choice(d["raw"])
            if pos is None:
                integ["parse_fail_action"] += 1
                continue
            A[key].append(dict(perm_id=d["perm_id"], pos=pos, item=perm[pos],
                               actor=d["actor"], realized=d["realized_partner"]))
        else:
            pv = parse_probs(d["raw"])
            if pv is None:
                integ["parse_fail_predict"] += 1
                continue
            byitem = [0.0] * 4
            for slot, p in enumerate(pv):
                byitem[perm[slot]] = p
            A[key].append(dict(perm_id=d["perm_id"], probs=byitem, actor=d["actor"]))
    integ["checkpoints"] = dict(integ["checkpoints"])
    return man, spec, recs, mf, A, integ


# ------------------------------------------------------------------ estimators --
def payoff_vec(rec):
    return [5.0 if i == rec["green_index"] else 10.0 for i in range(4)]


def action_stats(trials, rec):
    n = len(trials)
    c = Counter(t["item"] for t in trials)
    return dict(n=n,
                p_claude_modal=c.get(rec["claude_modal_index"], 0) / n,
                p_gpt_modal=c.get(rec["gpt_modal_index"], 0) / n,
                p_green=c.get(rec["green_index"], 0) / n,
                p_unmarked=1 - c.get(rec["green_index"], 0) / n,
                counts={str(i): c.get(i, 0) for i in range(4)})


def self_coord(trials, rec):
    """Bias-corrected COPY coordination + expected payoff. Self-pairs excluded."""
    c = Counter(t["item"] for t in trials); N = sum(c.values())
    if N < 2:
        return float("nan"), float("nan")
    pv = payoff_vec(rec)
    m = sum(v * (v - 1) for v in c.values()) / (N * (N - 1))
    pay = sum(pv[k] * v * (v - 1) for k, v in c.items()) / (N * (N - 1))
    return m, pay


def cross_coord(focal, partner, rec):
    """Coordination and expected payoff against an INDEPENDENT partner distribution."""
    f = Counter(t["item"] for t in focal); q = Counter(t["item"] for t in partner)
    nf, nq = sum(f.values()), sum(q.values())
    if not nf or not nq:
        return float("nan"), float("nan")
    pv = payoff_vec(rec)
    m = sum((f.get(k, 0) / nf) * (q.get(k, 0) / nq) for k in range(4))
    pay = sum(pv[k] * (f.get(k, 0) / nf) * (q.get(k, 0) / nq) for k in range(4))
    return m, pay


def predict_stats(trials, rec, partner_counts):
    n = len(trials)
    mean = [sum(t["probs"][i] for t in trials) / n for i in range(4)]
    ent = sum(-sum(p * math.log2(p) for p in t["probs"] if p > 0) for t in trials) / n
    out = dict(n=n, p_claude_modal=mean[rec["claude_modal_index"]],
               p_gpt_modal=mean[rec["gpt_modal_index"]],
               p_green=mean[rec["green_index"]], entropy_bits=ent, mean_probs=mean)
    if partner_counts:
        N = sum(partner_counts.values())
        q = [partner_counts.get(k, 0) / N for k in range(4)]
        # E[sum_k (p_k - o_k)^2] with o ~ q  =  sum_k (p_k^2 - 2 p_k q_k + q_k)
        out["brier"] = sum(sum(t["probs"][k] ** 2 - 2 * t["probs"][k] * q[k] + q[k]
                               for k in range(4)) for t in trials) / n
    else:
        out["brier"] = float("nan")
    return out


# ------------------------------------------------------------------ assembly ---
def partner_pool(A, sid, cond):
    """The INDEPENDENT partner action draws for a condition. COPY has none - it is
    handled by the self-pairing estimator on the focal pool itself."""
    if cond == "copy":
        return None
    return A[(sid, "partner", "action", cond)]


def per_array(A, recs, spec):
    out = {}
    for sid, rec in recs.items():
        row = dict(array_id=sid, item_type=rec["item_type"], mechanism=rec["mechanism"],
                   claude_modal=rec["claude_modal_object"], green=rec["green_object"],
                   gpt_modal=rec["gpt_modal_object"])
        for cond in ("copy", "other", "unknown"):
            act = A[(sid, "focal", "action", cond)]
            prd = A[(sid, "focal", "predict", cond)]
            pool = partner_pool(A, sid, cond)
            s = action_stats(act, rec)
            if cond == "copy":
                m, pay = self_coord(act, rec)
                pc = Counter(t["item"] for t in act)      # own pool, self-pairs excluded
            else:
                m, pay = cross_coord(act, pool, rec)
                pc = Counter(t["item"] for t in pool)
            row[f"act_{cond}"] = dict(s, coord=m, exp_payoff=pay)
            row[f"prd_{cond}"] = predict_stats(prd, rec, pc)
            row[f"partner_{cond}"] = {str(k): pc.get(k, 0) for k in range(4)}
        out[sid] = row
    return out


CONTRASTS = [
    ("act_claude_modal_copy_minus_other", "act", "p_claude_modal", "copy", "other"),
    ("act_green_other_minus_copy", "act", "p_green", "other", "copy"),
    ("act_claude_modal_copy_minus_unknown", "act", "p_claude_modal", "copy", "unknown"),
    ("act_claude_modal_other_minus_unknown", "act", "p_claude_modal", "other", "unknown"),
    ("act_green_unknown_minus_copy", "act", "p_green", "unknown", "copy"),
    ("prd_claude_modal_copy_minus_other", "prd", "p_claude_modal", "copy", "other"),
    ("prd_green_other_minus_copy", "prd", "p_green", "other", "copy"),
    ("prd_claude_modal_copy_minus_unknown", "prd", "p_claude_modal", "copy", "unknown"),
    ("prd_claude_modal_other_minus_unknown", "prd", "p_claude_modal", "other", "unknown"),
    ("prd_gpt_modal_other_minus_copy", "prd", "p_gpt_modal", "other", "copy"),
    ("prd_entropy_other_minus_copy", "prd", "entropy_bits", "other", "copy"),
]


def contrast_value(row, arm, field, c1, c2):
    return row[f"{arm}_{c1}"][field] - row[f"{arm}_{c2}"][field]


def group_mean(rows, arm, field, c1, c2):
    v = [contrast_value(r, arm, field, c1, c2) for r in rows]
    return sum(v) / len(v) if v else float("nan")


def boot_did(pa, name, arm, field, c1, c2, exclude=(), seed=BSEED):
    """Cluster bootstrap over ARRAYS within item type. Returns asym, ctrl, DiD with CIs."""
    import random
    rows = [r for r in pa.values() if r["array_id"] not in exclude]
    asym = [r for r in rows if r["item_type"] == "asymmetric"]
    ctrl = [r for r in rows if r["item_type"] == "control"]
    pt = dict(asym=group_mean(asym, arm, field, c1, c2),
              control=group_mean(ctrl, arm, field, c1, c2))
    pt["did"] = pt["asym"] - pt["control"]
    rng = random.Random(f"{seed}|{name}|{exclude}")
    draws = {k: [] for k in ("asym", "control", "did")}
    for _ in range(BOOT):
        a = [asym[rng.randrange(len(asym))] for _ in range(len(asym))]
        c = [ctrl[rng.randrange(len(ctrl))] for _ in range(len(ctrl))]
        va = group_mean(a, arm, field, c1, c2)
        vc = group_mean(c, arm, field, c1, c2)
        draws["asym"].append(va); draws["control"].append(vc); draws["did"].append(va - vc)
    out = dict(point=pt, n_asym=len(asym), n_control=len(ctrl))
    for k, v in draws.items():
        v.sort()
        out[f"{k}_ci"] = [round(v[int(.025 * BOOT)], 4), round(v[int(.975 * BOOT)], 4)]
    return out


def main(run_dir):
    man, spec, recs, mf, A, integ = build(run_dir)
    # ---- integrity: every cell complete and counterbalanced ----
    cells = {}
    for (sid, role, arm, cond), v in A.items():
        cells[f"{sid}|{role}|{arm}|{cond}"] = len(v)
        perms = sorted(t["perm_id"] for t in v)
        integ.setdefault("incomplete_cells", [])
        if perms != list(range(24)):
            integ["incomplete_cells"].append(f"{sid}|{role}|{arm}|{cond}:{len(v)}")
    integ["n_cells"] = len(cells)
    integ["expected_cells"] = 14 * (3 * 2 + 2)
    pa = per_array(A, recs, spec)

    res = dict(run_dir=os.path.basename(run_dir), integrity=integ,
               manifest_sha=open(os.path.join(P, "PILOT_MANIFEST_FINAL.json.sha256")).read().strip(),
               run_sha=open(os.path.join(P, "STRATEGIC_RUN_LOCKED.json.sha256")).read().strip(),
               per_array=pa, contrasts={}, robustness={})
    for name, arm, field, c1, c2 in CONTRASTS:
        res["contrasts"][name] = boot_did(pa, name, arm, field, c1, c2)
    # ---- is it one array or one mechanism? ----
    key = ("act_claude_modal_copy_minus_other", "act", "p_claude_modal", "copy", "other")
    for drop in sorted(pa):
        res["robustness"][f"drop_array:{drop}"] = boot_did(pa, key[0], *key[1:], exclude=(drop,))
    for mech in sorted({r["mechanism"] for r in pa.values()}):
        ex = tuple(s for s, r in pa.items() if r["mechanism"] == mech)
        res["robustness"][f"drop_mechanism:{mech}"] = boot_did(pa, key[0], *key[1:], exclude=ex)
    numer = tuple(s for s, r in pa.items() if r["mechanism"] == "numerosity")
    res["robustness"]["drop_unmatched_numerosity"] = {
        n: boot_did(pa, n, a, f, c1, c2, exclude=numer) for n, a, f, c1, c2 in CONTRASTS}
    json.dump(res, open(os.path.join(run_dir, "pilot_results.json"), "w"), indent=1,
              default=lambda o: None if o != o else o)
    print(json.dumps({k: v["point"] for k, v in res["contrasts"].items()}, indent=1))
    return res


if __name__ == "__main__":
    main(sys.argv[1])
