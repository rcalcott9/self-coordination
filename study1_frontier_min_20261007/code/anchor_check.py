"""Calibration drift gate (FROZEN gates.anchor). No API calls.

Statistic: total log-likelihood of the anchor choices (41 arrays x 4, canonical shape) under
the frame distribution, smoothed with pseudo-count 0.5. Null: 10,000 posterior-predictive
replicates. Each replicate draws a "true" distribution per array from Dirichlet(frame counts + 0.5),
samples anchor-sized choices from it, and scores them under the same smoothed frame estimate.
This carries the frame's own sampling noise. The drift p is the share of replicates with
log-lik <= observed (one-sided: drift lowers fit). p < .01 => do NOT reuse frame calibration
for that model; recollect 48/array first.
"""
import csv, glob, json, os, sys
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
F = json.load(open(os.path.join(ROOT, "design", "FROZEN.json")))
FRAME = F["calibration_reuse"]["source"]
MODEL = {"gpt": "gpt-5.5-2026-04-23", "claude": "claude-opus-5"}
ALPHA, B, SEED = 0.5, 10000, 20261008

frame = {m: {a: np.zeros(4) for a in F["arrays"]} for m in MODEL}
for r in csv.DictReader(open(FRAME)):
    for m, mid in MODEL.items():
        if r["checkpoint_requested"] == mid and r["parse_ok"] == "1":
            frame[m][r["array_id"]][int(r["canonical_index"])] += 1
anc = {m: {a: [] for a in F["arrays"]} for m in MODEL}
for f in glob.glob(os.path.join(ROOT, "runs", "anchor", "*.csv")):
    for r in csv.DictReader(open(f)):
        if r["parse_ok"] == "1":
            anc[r["answerer"]][r["array"]].append(int(r["canonical_choice"]))

rng = np.random.default_rng(SEED)
report = {}
for m in MODEL:
    A = F["arrays"]
    C = np.array([frame[m][a] for a in A])                    # 41 x 4
    assert (C.sum(1) == 48).all(), C.sum(1)
    ph = (C + ALPHA) / (C + ALPHA).sum(1, keepdims=True)
    lp = np.log(ph)
    n = np.array([len(anc[m][a]) for a in A])
    obs = sum(lp[i, c] for i, a in enumerate(A) for c in anc[m][a])
    modal = C.argmax(1)
    hit = np.mean([c == modal[i] for i, a in enumerate(A) for c in anc[m][a]])
    exp_hit = float(np.sum(ph[np.arange(41), modal] * n) / n.sum())
    sims = np.empty(B)
    for b in range(B):
        P = np.vstack([rng.dirichlet(C[i] + ALPHA) for i in range(41)])
        tot = 0.0
        for i in range(41):
            k = rng.multinomial(n[i], P[i])
            tot += float(k @ lp[i])
        sims[b] = tot
    p = float(np.mean(sims <= obs))
    worst = sorted(((sum(lp[i, c] for c in anc[m][a]) - float(n[i] * (ph[i] * lp[i]).sum()), a,
                     anc[m][a], C[i].astype(int).tolist()) for i, a in enumerate(A)))[:5]
    report[m] = dict(n_anchor=int(n.sum()), loglik_obs=round(obs, 2),
                     loglik_null_median=round(float(np.median(sims)), 2),
                     loglik_null_1pct=round(float(np.quantile(sims, .01)), 2), p_drift=p,
                     modal_hit_rate=round(float(hit), 3), expected_modal_hit=round(exp_hit, 3),
                     reuse_frame_calibration=p >= .01,
                     least_typical_arrays=[dict(array=a, anchor=c, frame_counts=fc, excess_loglik=round(e, 2))
                                           for e, a, c, fc in worst])
out = os.path.join(ROOT, "runs", "anchor", "ANCHOR_CHECK.json")
json.dump(dict(rule=__doc__.strip(), alpha=ALPHA, B=B, seed=SEED, results=report), open(out, "w"), indent=1)
print(json.dumps(report, indent=1))
