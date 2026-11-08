"""
Ground-truth validation of the determinism/similarity separation.

MAKES NO API CALLS. Everything here is simulated from known parameters.

Ground truth is defined in STANDARDISED space: every model's underlying preference
vector q is a point on the simplex whose effective support is exactly S* = 2.0, and the
observed policy is p = temper(q, beta). "beta" is the model's DETERMINISM, "q" is its
CONVENTION, and the two are orthogonal by construction -- which is exactly the
separation MASTER_DESIGN S5 requires the analysis to make.

All four cases are built so the two models SHARE a modal option and differ only in the
tail. That is the dangerous configuration named in MASTER_DESIGN S5 -- "if both models
sharpen toward the same option, expected match rises with no change in mutual
similarity" -- and it is the configuration the existing 4-option data actually shows.

  A  PURE DETERMINISM      q_A, q_B FIXED and different;  beta rises across vintage.
                           TRUTH: similarity FLAT, determinism rising.
                           Raw cross_model_match MUST rise. DAS MUST NOT.

  B  PURE SIMILARITY       beta FIXED at 1;  q_B moves toward q_A, restandardised at
                           every step so its determinism never changes.
                           TRUTH: similarity UP, determinism flat.  DAS MUST rise.

  C  BOTH                  beta rises AND q_B moves toward q_A.
                           TRUTH: both up. DAS MUST rise by roughly the amount it rises
                           in B, NOT by the amount raw match rises.

  D  ADVERSARIAL           beta rises while q_B moves AWAY from q_A.
                           TRUTH: determinism up, similarity DOWN.
                           DAS MUST fall. A merely rescaled statistic fails here.

Usage:  python3 synthetic_validation.py [--reps 200] [--out out/]
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import convergence_metrics as cm  # noqa: E402

K = 4
S_STAR = cm.DEFAULT_TARGET_SUPPORT     # 2.0
ALPHA = cm.DEFAULT_ALPHA               # 0.5
N_ITEMS = 24
N_PER_CELL = 48                        # the FROZEN FLOOR from MASTER_DESIGN S5
VINTAGES = np.array([0., 1., 2., 3., 4.])
BETAS_RISING = np.array([1.0, 1.6, 2.5, 3.9, 6.0])
BETAS_FLAT = np.ones(5)
LAMBDAS = np.array([0.0, 0.22, 0.44, 0.66, 0.88])
SEED = 20260909
CASE_OFFSET = {"A": 0, "B": 1000, "C": 2000, "D": 3000}   # deterministic, not hash()


# ------------------------------------------------------------------ ground truth build


def draw_bases(rng, n_items):
    """Per item return q_A, q_B0, q_AWAY, all standardised to support S*.

    SHARED MODE by construction: both q_A and q_B0 are Dirichlet draws sorted
    descending, with q_B0's tail (indices 1..K-1) randomly permuted. Both therefore put
    their largest mass on canonical option 0 and differ only in how the remaining mass
    is ordered -- the configuration in which raw match is most badly confounded by
    determinism.

    q_AWAY is q_A reversed: most mass where q_A has least. Mixing q_B toward it strictly
    lowers true alignment, which Case D needs (a third random draw would move alignment
    by an unsigned amount).
    """
    a = np.sort(rng.dirichlet(np.ones(K) * 1.2, size=n_items), axis=1)[:, ::-1]
    b = np.sort(rng.dirichlet(np.ones(K) * 1.2, size=n_items), axis=1)[:, ::-1]
    for i in range(n_items):                       # shuffle only the tail of q_B
        b[i, 1:] = rng.permutation(b[i, 1:])
    qa = cm.standardize_probs_batch(a.copy(), S_STAR)
    qb = cm.standardize_probs_batch(b.copy(), S_STAR)
    qw = cm.standardize_probs_batch(qa[:, ::-1].copy(), S_STAR)
    return qa, qb, qw


def true_das(qa, qb):
    """The ground-truth determinism-adjusted similarity: S* * <q_A, q_B>."""
    return S_STAR * (qa * qb).sum(axis=1)


def build_case(case, qa, qb0, qaway):
    v = len(VINTAGES)
    if case == "A":
        betas, QB = BETAS_RISING, [qb0 for _ in range(v)]
    elif case == "B":
        betas = BETAS_FLAT
        QB = [cm.standardize_probs_batch((1 - l) * qb0 + l * qa, S_STAR) for l in LAMBDAS]
    elif case == "C":
        betas = BETAS_RISING
        QB = [cm.standardize_probs_batch((1 - l) * qb0 + l * qa, S_STAR) for l in LAMBDAS]
    elif case == "D":
        betas = BETAS_RISING
        QB = [cm.standardize_probs_batch((1 - l) * qb0 + l * qaway, S_STAR)
              for l in LAMBDAS]
    else:
        raise ValueError(case)
    truth = np.array([true_das(qa, QB[i]).mean() for i in range(v)])
    true_support = np.array([cm.support_batch(cm.temper_batch(
        qa, np.full(qa.shape[0], bb))).mean() for bb in betas])
    return betas, QB, truth, true_support


def simulate(rng, qa, QB, betas, n=N_PER_CELL):
    v, m = len(betas), qa.shape[0]
    CA, CB = [], []
    for i in range(v):
        Pa = cm.temper_batch(qa, np.full(m, betas[i]))
        Pb = cm.temper_batch(QB[i], np.full(m, betas[i]))
        CA.append(np.array([rng.multinomial(n, Pa[j]) for j in range(m)], float))
        CB.append(np.array([rng.multinomial(n, Pb[j]) for j in range(m)], float))
    return CA, CB


# ------------------------------------------------------------------------ measurement

LADDER = ("cross_model_match", "cos_raw", "das", "dajs", "rank_similarity",
          "js_distance", "hellinger", "modal_agreement",
          "eff_support_A", "eff_support_B", "det_channel", "align_channel")


def measure_rows(CA, CB):
    """Return per-(vintage x item) arrays for every rung of the ladder, plus the
    design columns needed for the item-clustered bootstrap."""
    cols = {kk: [] for kk in LADDER}
    vint, item = [], []
    for vi, (ca, cb) in enumerate(zip(CA, CB)):
        m = len(ca)
        cols["cross_model_match"].append(cm.cross_match_batch(ca, cb))
        cols["cos_raw"].append(cm.cos_raw_batch(ca, cb, ALPHA))
        cols["das"].append(cm.das_batch(ca, cb, S_STAR, ALPHA))
        cols["eff_support_A"].append(cm.effective_support_batch(ca))
        cols["eff_support_B"].append(cm.effective_support_batch(cb))
        cols["modal_agreement"].append(np.array(
            [cm.modal_agreement(ca[i], cb[i]) for i in range(m)], float))
        cols["dajs"].append(np.array(
            [cm.dajs(ca[i], cb[i], S_STAR, ALPHA) for i in range(m)]))
        cols["rank_similarity"].append(np.array(
            [cm.rank_similarity(ca[i], cb[i]) for i in range(m)]))
        cols["js_distance"].append(np.array(
            [cm.js_distance(ca[i], cb[i], ALPHA) for i in range(m)]))
        cols["hellinger"].append(np.array(
            [cm.hellinger(ca[i], cb[i], ALPHA) for i in range(m)]))
        maa = cm.effective_support_batch(ca, ALPHA)
        mbb = cm.effective_support_batch(cb, ALPHA)
        cols["det_channel"].append(-0.5 * np.log(maa) - 0.5 * np.log(mbb))
        cols["align_channel"].append(np.log(cm.cos_raw_batch(ca, cb, ALPHA)))
        vint.append(np.full(m, VINTAGES[vi]))
        item.append(np.arange(m))
    out = {kk: np.concatenate(vv) for kk, vv in cols.items()}
    out["_vintage"] = np.concatenate(vint)
    out["_item"] = np.concatenate(item)
    return out


def boot_ci_slope(x, y, item, b, rng):
    """Item-clustered bootstrap CI for the OLS slope. Items are the resampling unit
    because the same item contributes a row at every vintage."""
    uniq = np.unique(item)
    idx = {u: np.flatnonzero(item == u) for u in uniq}
    point, _ = cm.ols_slope(x, y)
    d = np.empty(b)
    for i in range(b):
        sel = np.concatenate([idx[u] for u in rng.choice(uniq, len(uniq), replace=True)])
        d[i], _ = cm.ols_slope(x[sel], y[sel])
    g = d[np.isfinite(d)]
    lo, hi = np.percentile(g, [2.5, 97.5])
    return point, float(lo), float(hi)


# ------------------------------------------------------------------------- experiment


def run_case(case, reps, boot_b, null_reps, null_b, seed=SEED):
    rng = np.random.default_rng(seed + CASE_OFFSET[case])
    qa, qb0, qaway = draw_bases(rng, N_ITEMS)
    betas, QB, truth, true_support = build_case(case, qa, qb0, qaway)
    true_slope = float(cm.ols_slope(VINTAGES, truth)[0])
    true_support_slope = float(cm.ols_slope(VINTAGES, true_support)[0])

    slopes = {kk: [] for kk in LADDER}
    curves = {kk: np.zeros(len(VINTAGES)) for kk in LADDER}
    verdict = {kk: dict(up=0, down=0, flat=0) for kk in ("cross_model_match", "das",
                                                         "cos_raw", "rank_similarity")}
    for r in range(reps):
        CA, CB = simulate(rng, qa, QB, betas)
        rows = measure_rows(CA, CB)
        x, it = rows["_vintage"], rows["_item"]
        for kk in LADDER:
            slopes[kk].append(cm.ols_slope(x, rows[kk])[0])
            for vi, vv in enumerate(VINTAGES):
                curves[kk][vi] += rows[kk][x == vv].mean()
        # what would a single study CONCLUDE, using an item-clustered bootstrap CI?
        brng = np.random.default_rng(seed + 77 * r + CASE_OFFSET[case])
        for kk in verdict:
            pt, lo, hi = boot_ci_slope(x, rows[kk], it, boot_b, brng)
            verdict[kk]["up" if lo > 0 else ("down" if hi < 0 else "flat")] += 1
    for kk in LADDER:
        curves[kk] /= reps

    # PRIMARY INFERENCE: determinism-matched null band.
    # Size in Case A (truth: no similarity change) / power in B, C, D.
    null_out = []
    rng2 = np.random.default_rng(seed + 555 + CASE_OFFSET[case])
    for r in range(null_reps):
        CA, CB = simulate(rng2, qa, QB, betas)
        nrows = [dict(item_id=it_, vintage=float(VINTAGES[vi]), n_a=N_PER_CELL,
                      n_b=N_PER_CELL, counts_a=CA[vi][it_], counts_b=CB[vi][it_])
                 for vi in range(len(betas)) for it_ in range(N_ITEMS)]
        null_out.append(cm.determinism_matched_null_band(nrows, b=null_b,
                                                         seed=seed + 31 * r))

    def summ(v):
        v = np.asarray(v, float)
        return dict(mean=float(v.mean()), sd=float(v.std(ddof=1)),
                    lo=float(np.percentile(v, 2.5)), hi=float(np.percentile(v, 97.5)))

    return dict(
        case=case, reps=reps,
        truth=dict(das_by_vintage=[float(t) for t in truth],
                   das_slope=true_slope,
                   effective_support_by_vintage=[float(t) for t in true_support],
                   effective_support_slope=true_support_slope,
                   betas=betas.tolist(),
                   determinism="rising" if betas[-1] > betas[0] + 1e-9 else "flat",
                   similarity=("flat" if abs(true_slope) < 1e-6
                               else ("rising" if true_slope > 0 else "falling"))),
        mean_curves={kk: [float(x) for x in vv] for kk, vv in curves.items()},
        slope_dist={kk: summ(vv) for kk, vv in slopes.items()},
        das_bias=float(np.mean(slopes["das"]) - true_slope),
        verdict_rates={kk: {s: v[s] / reps for s in v} for kk, v in verdict.items()},
        null_band_test=dict(
            n=len(null_out), b=null_b,
            reject_rate=float(np.mean([o["reject"] for o in null_out])) if null_out else None,
            median_p=float(np.median([o["p_two_sided"] for o in null_out])) if null_out else None,
            mean_observed_slope=float(np.mean([o["observed_slope"] for o in null_out]))
            if null_out else None,
            mean_null_slope=float(np.mean([o["null_mean"] for o in null_out]))
            if null_out else None,
            mean_band=[float(np.mean([o["null_lo"] for o in null_out])),
                       float(np.mean([o["null_hi"] for o in null_out]))] if null_out else None,
            mean_excess_slope=float(np.mean([o["excess_slope"] for o in null_out]))
            if null_out else None,
            mean_reference_rows=float(np.mean([o["n_reference_rows"] for o in null_out]))
            if null_out else None,
            identifiable=bool(np.all([o["identifiable"] for o in null_out]))
            if null_out else None),
        identifiability_table=identifiability_table(qa, QB, betas, truth, seed),
    )


def identifiability_table(qa, QB, betas, truth, seed, reps=40):
    """The key exhibit: estimated DAS against effective support, at CONSTANT true DAS.

    Shows directly how far the DAS point estimate is carried by the add-alpha prior as
    a cell collapses, which is why inference uses the null band rather than a test
    against zero."""
    rng = np.random.default_rng(seed + 9091)
    rowsout = []
    for vi, bb in enumerate(betas):
        est, sup = [], []
        for _ in range(reps):
            Pa = cm.temper_batch(qa, np.full(qa.shape[0], bb))
            Pb = cm.temper_batch(QB[vi], np.full(qa.shape[0], bb))
            ca = np.array([rng.multinomial(N_PER_CELL, p) for p in Pa], float)
            cb = np.array([rng.multinomial(N_PER_CELL, p) for p in Pb], float)
            est.append(cm.das_batch(ca, cb, S_STAR, ALPHA).mean())
            sup.append(cm.support_targets(ca).mean())
        rowsout.append(dict(vintage=vi, beta=float(bb),
                            true_effective_support=float(cm.support_batch(
                                cm.temper_batch(qa, np.full(qa.shape[0], bb))).mean()),
                            observed_effective_support=float(np.mean(sup)),
                            true_das=float(truth[vi]),
                            estimated_das=float(np.mean(est)),
                            bias=float(np.mean(est) - truth[vi])))
    return rowsout


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=200)
    ap.add_argument("--boot-b", type=int, default=400)
    ap.add_argument("--null-reps", type=int, default=20)
    ap.add_argument("--null-b", type=int, default=200)
    ap.add_argument("--out", default=os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "out"))
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)

    results = {}
    for case in ("A", "B", "C", "D"):
        print(f"[case {case}] {a.reps} replicates ...", flush=True)
        r = results[case] = run_case(case, a.reps, a.boot_b, a.null_reps, a.null_b)
        t = r["truth"]
        print(f"  TRUTH  determinism {t['determinism']:>7} | similarity {t['similarity']:>7}"
              f" | true DAS slope {t['das_slope']:+.4f}")
        for kk in ("cross_model_match", "cos_raw", "das", "rank_similarity"):
            s = r["slope_dist"][kk]
            v = r["verdict_rates"][kk]
            print(f"  {kk:<18} slope {s['mean']:+.4f} +/-{s['sd']:.4f}"
                  f"   verdict up/flat/down = {v['up']:.2f}/{v['flat']:.2f}/{v['down']:.2f}")
        print(f"  DAS bias vs truth {r['das_bias']:+.4f}")
        nb = r["null_band_test"]
        print(f"  NULL BAND  observed {nb['mean_observed_slope']:+.4f} vs null "
              f"{nb['mean_null_slope']:+.4f} band [{nb['mean_band'][0]:+.4f},"
              f"{nb['mean_band'][1]:+.4f}]  reject rate {nb['reject_rate']:.2f}"
              f"  (ref rows {nb['mean_reference_rows']:.0f})")

    meta = dict(k=K, s_star=S_STAR, alpha=ALPHA, n_items=N_ITEMS,
                n_per_cell=N_PER_CELL, vintages=VINTAGES.tolist(),
                reps=a.reps, boot_b=a.boot_b, seed=SEED, numpy=np.__version__)
    path = os.path.join(a.out, "synthetic_validation.json")
    with open(path, "w") as f:
        json.dump(dict(meta=meta, results=results), f, indent=1)
    print("\nwrote", path)


if __name__ == "__main__":
    main()
