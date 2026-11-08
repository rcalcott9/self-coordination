#!/usr/bin/env python3
"""EXPLORATORY (2026-10-13; no API calls; not pre-specified): do predictors differentiate targets in Study 1b?
Extends study1b_crossed_object_20261007/code/projection_diagnostic.py (low reasoning only) to the high-reasoning
replication and the Qwen step-316 x base study, and adds the benchmark the original lacked: how far apart the two
targets' measured choice distributions actually are.

Per item and predictor P (other model O):
  pred_tvd   TVD between P's mean prediction for itself and its mean prediction for O
  true_tvd   TVD between P's and O's measured fresh choice distributions (same for both predictors)
  proj_gap   Brier of P's predictions of O scored against O's choices minus scored against P's own choices
             (> 0 = P's prediction of O is closer to P's own behaviour than to O's)
Summaries over the 10 divergent items (controls reported alongside): means, item-bootstrap 95% CI (10,000),
exact two-sided sign-flip p for (true_tvd - pred_tvd) and for proj_gap, and the differentiation ratio
sum(pred_tvd) / sum(true_tvd) (1 = predictions as far apart as the targets really are; 0 = identical predictions).
Frontier choices are pooled over randomised orders, as in the frozen scoring. Qwen choices are order-matched
for Brier (as in its frozen scoring) and pooled over the two orders for TVD.
Asserts that the low-reasoning pred_tvd and proj_gap reproduce the existing diagnostic (.067/.048, .275/.264)."""
import csv, glob, itertools, json
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent.parent
SC = HERE.parent
QW = Path.home() / "Desktop/Superrationality/Stag/qwen_crossed_prediction_20261009"
rng = np.random.default_rng(20261013)
brier = lambda q, p: float(q @ q - 2 * q @ p + 1)
tvd = lambda a, b: float(.5 * np.abs(a - b).sum())


def frontier(root, runs_glob, fsha, arrays, strat, ftask, sha_len):
    rows = [r for f in glob.glob(str(root / runs_glob)) for r in csv.DictReader(open(f))
            if r["frozen_sha8"] == fsha and r["parse_ok"] == "1" and r["array"] in arrays]
    ref, pred = {}, {}
    for r in rows:
        if r["task"] == "REF":
            ref.setdefault((r["answerer"], r["array"]), []).append(int(r["canonical_choice"]))
        elif r["task"] == "PRED":
            pred.setdefault((r["answerer"], r[ftask], r["array"]), []).append(np.array(json.loads(r["p_canonical"])))
    ph = {k: np.bincount(v, minlength=4) / len(v) for k, v in ref.items()}
    out = []
    for x in arrays:
        for P, O in (("gpt", "claude"), ("claude", "gpt")):
            qS, qO = np.mean(pred[(P, P, x)], 0), np.mean(pred[(P, O, x)], 0)
            out.append(dict(item=x, role="divergent" if strat[x] != "S3" else "control", predictor=P,
                            pred_tvd=tvd(qS, qO), true_tvd=tvd(ph[(P, x)], ph[(O, x)]),
                            proj_gap=float(np.mean([brier(q, ph[(O, x)]) - brier(q, ph[(P, x)]) for q in pred[(P, O, x)]]))))
    return out


D = []
# frontier, low reasoning (original 1b)
r1 = SC / "study1b_crossed_object_20261007"
FM = json.load(open(r1 / "design/FROZEN_MAIN.json"))
st1 = {x: s for s, v in FM["strata"].items() for x in v}
for d in frontier(r1, "runs/main/*.csv", open(r1 / "design/FROZEN_MAIN.sha256").read()[:8], FM["arrays"], st1, "target", 8):
    D.append(dict(study="frontier", setting="low", **d))
# frontier, high reasoning (same arrays, fresh draws)
r2 = SC / "study1_highreason_20261009"
F2 = json.load(open(r2 / "design/FROZEN.json"))
st2 = {x: s for s, v in F2["strata_1b"].items() for x in v}
for d in frontier(r2, "runs/main/*.csv", open(r2 / "design/FROZEN.sha256").read().split()[0][:8], F2["arrays_1b"], st2, "focal", 8):
    D.append(dict(study="frontier", setting="high", **d))
# Qwen step-316 x base
FQ = json.loads((QW / "design/FROZEN.json").read_text())
role = {x: "divergent" for x in FQ["selection"]["primary"]} | {x: "control" for x in FQ["selection"]["controls"]}
recs = [json.loads(l) for f in sorted((QW / "results").glob("*/calls.jsonl")) for l in open(f) if l.strip()]
ref, pred = {}, {}
for r in recs:
    if r["status"] != "ok" or r["stage"] == "pilot":
        continue
    for s in r["samples"]:
        if s["parsed"] is None:
            continue
        if r["task"] == "REF":
            ref.setdefault((r["answerer"], r["item_id"], r["orientation"]), []).append(s["parsed"]["object"])
        else:
            pred.setdefault((r["answerer"], r["target"], r["item_id"]), []).append((r["orientation"], np.array(s["parsed"]["q_object"])))
PH = {k: np.bincount(v, minlength=2) / len(v) for k, v in ref.items()}
PHall = {(m, x): np.bincount(ref[(m, x, "canonical")] + ref[(m, x, "swapped")], minlength=2) / (len(ref[(m, x, "canonical")]) + len(ref[(m, x, "swapped")]))
         for m in ("s316", "base") for x in role}
for x in role:
    for P, O in (("s316", "base"), ("base", "s316")):
        qS = np.mean([q for _, q in pred[(P, P, x)]], 0); qO = np.mean([q for _, q in pred[(P, O, x)]], 0)
        D.append(dict(study="qwen", setting="thinking off", item=x, role=role[x], predictor=P,
                      pred_tvd=tvd(qS, qO), true_tvd=tvd(PHall[(P, x)], PHall[(O, x)]),
                      proj_gap=float(np.mean([brier(q, PH[(O, x, o)]) - brier(q, PH[(P, x, o)]) for o, q in pred[(P, O, x)]]))))

# check against the existing low-reasoning diagnostic
for P, a, b in (("gpt", .067, .275), ("claude", .048, .264)):
    s = [d for d in D if d["setting"] == "low" and d["role"] == "divergent" and d["predictor"] == P]
    assert round(np.mean([d["pred_tvd"] for d in s]), 3) == a and round(np.mean([d["proj_gap"] for d in s]), 3) == b, P


def boot(v):
    v = np.asarray(v); m = rng.choice(v, (10000, len(v))).mean(1)
    return [float(np.quantile(m, .025)), float(np.quantile(m, .975))]


def exact(v):
    v = np.asarray(v); pats = np.array(list(itertools.product([-1, 1], repeat=len(v))))
    return float(np.mean(np.abs((pats * v).mean(1)) >= abs(v.mean()) - 1e-12))


NAME = {"gpt": "GPT-5.5", "claude": "Claude Opus 5", "s316": "Qwen step-316", "base": "Qwen base"}
S = []
for (study, setting, rl, P) in dict.fromkeys((d["study"], d["setting"], d["role"], d["predictor"]) for d in D):
    s = [d for d in D if (d["study"], d["setting"], d["role"], d["predictor"]) == (study, setting, rl, P)]
    pt, tt, pg = (np.array([d[k] for d in s]) for k in ("pred_tvd", "true_tvd", "proj_gap"))
    S.append(dict(study=study, setting=setting, items=rl, predictor=NAME[P], n=len(s),
                  pred_tvd=float(pt.mean()), true_tvd=float(tt.mean()), differentiation_ratio=float(pt.sum() / tt.sum()) if tt.sum() > 0 else None,
                  shortfall=float((tt - pt).mean()), shortfall_ci95=boot(tt - pt), shortfall_exact_p=exact(tt - pt),
                  items_pred_tvd_gt_0p1=int((pt > .1).sum()),
                  proj_gap=float(pg.mean()), proj_gap_ci95=boot(pg), proj_gap_exact_p=exact(pg), items_closer_to_own=int((pg > 0).sum())))

with open(HERE / "tables/study1_projection_items.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(D[0])); w.writeheader(); w.writerows(D)
with open(HERE / "tables/study1_projection_summary.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(S[0])); w.writeheader()
    w.writerows([{k: (json.dumps([round(c, 4) for c in v]) if isinstance(v, list) else v) for k, v in r.items()} for r in S])
for r in S:
    print(f"{r['study']:8} {r['setting']:12} {r['items']:9} {r['predictor']:14} n={r['n']:2}  pred {r['pred_tvd']:.3f}  true {r['true_tvd']:.3f}  "
          f"ratio {r['differentiation_ratio'] if r['differentiation_ratio'] is None else round(r['differentiation_ratio'], 3)}  "
          f"short {r['shortfall']:+.3f} {np.round(r['shortfall_ci95'], 3)} p={r['shortfall_exact_p']:.4f}  "
          f"gap {r['proj_gap']:+.3f} {np.round(r['proj_gap_ci95'], 3)} p={r['proj_gap_exact_p']:.4f} own {r['items_closer_to_own']}/{r['n']}")
