"""Five follow-up analyses on the existing gpt-4o-mini introspection data.
No API calls. Nothing is refit that was not already fit.

1. Spearman r(report, learned), ours vs Plunkett's shipped gpt-4o-mini
2. Regression of reported on learned -- standardised and unstandardised
3. Reliability ceiling from repeated reports (and from split-half behavioural fits)
4. Context-level heterogeneity -- distribution and sign counts, not just the mean
5. Matched-sample test that r(report, learned) > r(report, true)
"""

import csv
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gate2a_elicit import parse_strict
from gate1_score import fit_context, normalise, z

ROOT = Path(__file__).resolve().parent.parent
O, G1, G2 = ROOT / "data" / "g4omini", ROOT / "data" / "gate1", ROOT / "data" / "gate2a"
REF = ROOT / "reference_plunkett" / "data"
RNG = np.random.default_rng(20260905)


def load_ours():
    V = json.loads((O / "g4omini_eval_verdict.json").read_text())
    learned = {k: np.array(v, float) for k, v in V["learned_weights"].items()}
    true_w = {k: np.array([v[f"attr{i}"] for i in range(1, 6)], float)
              for k, v in json.loads((G1 / "gate1_true_weights.json").read_text()).items()}
    trials = {(r["scenario"], r["idx"]): r
              for r in json.loads((G2 / "gate2a_report_trials.json").read_text())}
    reps = {}
    for r in json.loads((O / "g4omini_reports.json").read_text()):
        v, s = parse_strict(r.get("reply"), trials[(r["scenario"], r["idx"])]["attr_names"])
        if v is not None:
            reps.setdefault(r["scenario"], []).append(np.array(v, float))
    return learned, true_w, reps


def flatten(reps, target):
    ctx = sorted(set(reps) & set(target))
    R = np.array([np.mean(reps[s], axis=0) for s in ctx]).ravel()
    T = np.concatenate([target[s] for s in ctx])
    return ctx, R, T


def cluster_boot(ctx, fn, n=4000):
    """Bootstrap resampling CONTEXTS (the unit of independence)."""
    out = []
    for _ in range(n):
        pick = RNG.choice(len(ctx), size=len(ctx), replace=True)
        val = fn([ctx[i] for i in pick])
        if val is not None and np.isfinite(val):
            out.append(val)
    return float(np.percentile(out, 2.5)), float(np.percentile(out, 97.5)), np.array(out)


# ---------------------------------------------------------------- 1. Spearman
def plunkett_spearman():
    """Their gpt-4o-mini: mean reports vs their shipped brms behavioural weights."""
    rep = {}
    with (REF / "gpt-4o-mini-2024-07-18_instilled_weight_reports.csv").open() as f:
        for r in csv.DictReader(f):
            rep.setdefault(r["scenario"], []).append(
                np.array([float(r[f"report_attr{i}"]) for i in range(1, 6)]))
    beh = {}
    with (REF / "gpt-4o-mini-2024-07-18_regression_results.csv").open() as f:
        for r in csv.DictReader(f):
            beh[r["scenario"]] = np.array([float(r[f"b_attr{i}"]) for i in range(1, 6)])
    ctx = sorted(set(rep) & set(beh))
    R = np.array([np.mean(rep[s], axis=0) for s in ctx]).ravel()
    B = np.concatenate([beh[s] for s in ctx])
    return ctx, R, B


# ------------------------------------------------- 3. reliability of reports
def report_reliability(reps, min_n=4):
    """Split-half across the repeated reports within a context, Spearman-Brown
    corrected. This is the ceiling that report NOISE alone imposes."""
    A, B = [], []
    used = 0
    for s, lst in reps.items():
        if len(lst) < min_n:
            continue
        used += 1
        idx = RNG.permutation(len(lst))
        h1 = np.mean([lst[i] for i in idx[:len(lst)//2]], axis=0)
        h2 = np.mean([lst[i] for i in idx[len(lst)//2:]], axis=0)
        A.append(h1); B.append(h2)
    A = np.concatenate(A); B = np.concatenate(B)
    r_half = np.corrcoef(z(A), z(B))[0, 1]
    # Spearman-Brown up to the FULL number of reports (halves -> whole)
    r_full = 2 * r_half / (1 + r_half)
    return r_half, r_full, used


def learned_reliability():
    """Split the 5,000 held-out choices in half per context, refit, correlate.
    Gives the reliability of the behavioural weight estimate itself."""
    rows = {(r["scenario"], r["idx"]): r
            for r in json.loads((G1 / "gate1_heldout_5000.json").read_text())}
    byc = {}
    for r in json.loads((O / "g4omini_acq.json").read_text()):
        ch = (r.get("reply") or "").strip()
        if ch not in ("A", "B"):
            continue
        s = rows[(r["scenario"], r["idx"])]
        rng = [s[f"range_{i}"] for i in range(1, 6)]
        byc.setdefault(r["scenario"], []).append((
            [(s[f"A_attribute_{i}"] - s[f"B_attribute_{i}"]) / rng[i-1] for i in range(1, 6)],
            1 if ch == "A" else 0))
    A, B = [], []
    for s, dat in byc.items():
        idx = RNG.permutation(len(dat))
        halves = []
        for h in (idx[:len(dat)//2], idx[len(dat)//2:]):
            X = np.array([dat[i][0] for i in h]); y = np.array([dat[i][1] for i in h])
            c, _ = fit_context(X, y)
            halves.append(None if c is None else normalise(c))
        if all(h is not None for h in halves):
            A.append(halves[0]); B.append(halves[1])
    A = np.concatenate(A); B = np.concatenate(B)
    r_half = np.corrcoef(z(A), z(B))[0, 1]
    return r_half, 2 * r_half / (1 + r_half), len(A) // 5


def main():
    learned, true_w, reps = load_ours()
    ctx, R, L = flatten(reps, learned)
    _, R2, T = flatten(reps, true_w)
    print("=" * 74)
    print(f"gpt-4o-mini follow-ups   contexts with usable reports: {len(ctx)}/100")
    print("=" * 74)

    # ---- 1. Spearman -----------------------------------------------------
    sp_ours = stats.spearmanr(R, L)
    pe_ours = stats.pearsonr(R, L)
    pctx, pR, pB = plunkett_spearman()
    sp_p = stats.spearmanr(pR, pB)
    pe_p = stats.pearsonr(pR, pB)
    print("\n[1] SPEARMAN vs PEARSON, report vs LEARNED behavioural")
    print(f"    ours      (n={len(ctx)} ctx): Spearman rho={sp_ours.statistic:+.4f}  "
          f"Pearson r={pe_ours.statistic:+.4f}")
    print(f"    Plunkett  (n={len(pctx)} ctx): Spearman rho={sp_p.statistic:+.4f}  "
          f"Pearson r={pe_p.statistic:+.4f}")
    print("    (Plunkett recomputed from their shipped CSVs, identical procedure)")

    # ---- 2. regression ----------------------------------------------------
    sl_s, ic_s = np.polyfit(z(L), z(R), 1)
    sl_u, ic_u = np.polyfit(L, R, 1)
    print("\n[2] REGRESSION of REPORTED on LEARNED")
    print(f"    standardised : slope={sl_s:+.4f}  intercept={ic_s:+.4f}")
    print(f"    unstandardised: slope={sl_u:+.4f}  intercept={ic_u:+.4f}")
    print(f"    reported |w| mean={np.abs(R).mean():.2f} sd={R.std():.2f}")
    print(f"    learned  |w| mean={np.abs(L).mean():.2f} sd={L.std():.2f}")
    print(f"    sd ratio (reported/learned) = {R.std()/L.std():.3f}")

    # ---- 3. reliability ceiling ------------------------------------------
    rh, rfull, nused = report_reliability(reps)
    lh, lfull, nl = learned_reliability()
    ceiling = np.sqrt(max(rfull, 0) * max(lfull, 0))
    print("\n[3] RELIABILITY CEILING")
    print(f"    report split-half r={rh:+.4f} -> Spearman-Brown full={rfull:+.4f} "
          f"({nused} contexts)")
    print(f"    learned split-half r={lh:+.4f} -> Spearman-Brown full={lfull:+.4f} "
          f"({nl} contexts)")
    print(f"    attenuation ceiling = sqrt(rel_report * rel_learned) = {ceiling:.4f}")
    print(f"    observed r = {pe_ours.statistic:+.4f}   "
          f"disattenuated = {pe_ours.statistic/ceiling if ceiling>0 else float('nan'):+.4f}")
    print(f"    -> observed is {pe_ours.statistic/ceiling*100 if ceiling>0 else 0:.0f}% of ceiling")

    # ---- 4. heterogeneity -------------------------------------------------
    within = []
    for s in ctx:
        m = np.mean(reps[s], axis=0)
        if np.std(m) > 0 and np.std(learned[s]) > 0:
            within.append((s, float(np.corrcoef(m, learned[s])[0, 1])))
    w = np.array([x[1] for x in within])
    qs = np.percentile(w, [0, 10, 25, 50, 75, 90, 100])
    print("\n[4] CONTEXT-LEVEL HETEROGENEITY (within-context r, 5 points each)")
    print(f"    n={len(w)}  mean={w.mean():+.3f}  median={np.median(w):+.3f}  sd={w.std(ddof=1):.3f}")
    print(f"    quantiles 0/10/25/50/75/90/100: " + " ".join(f"{q:+.2f}" for q in qs))
    print(f"    positive={int((w>0).sum())}/{len(w)}  negative={int((w<0).sum())}  "
          f"|r|>0.5: {int((np.abs(w)>0.5).sum())}  r>0.5: {int((w>0.5).sum())}")
    sign = stats.binomtest(int((w > 0).sum()), len(w), 0.5)
    print(f"    sign test vs 50/50: p={sign.pvalue:.4g}")
    # leave-one-context-out on the pooled correlation
    loo = []
    for s in ctx:
        keep = [x for x in ctx if x != s]
        Rk = np.array([np.mean(reps[k], axis=0) for k in keep]).ravel()
        Lk = np.concatenate([learned[k] for k in keep])
        loo.append(np.corrcoef(z(Rk), z(Lk))[0, 1])
    print(f"    leave-one-context-out pooled r: min={min(loo):+.4f} max={max(loo):+.4f}")

    # ---- 5. matched-sample test r(rep,learned) > r(rep,true) --------------
    r_rl = pe_ours.statistic
    r_rt = stats.pearsonr(R2, T).statistic
    _, _, Lp = flatten(reps, learned)
    r_lt = np.corrcoef(z(np.concatenate([learned[s] for s in ctx])),
                       z(np.concatenate([true_w[s] for s in ctx])))[0, 1]
    n = len(R)
    # Williams' test for dependent correlations sharing one variable
    k = (1 - r_rl**2 - r_rt**2 - r_lt**2) + 2*r_rl*r_rt*r_lt
    t_w = ((r_rl - r_rt) * np.sqrt((n-1)*(1+r_lt) /
           (2*((n-1)/(n-3))*k + ((r_rl+r_rt)**2/4)*(1-r_lt)**3)))
    p_w = 2 * (1 - stats.t.cdf(abs(t_w), n-3))

    def diff(cs):
        Rk = np.array([np.mean(reps[s], axis=0) for s in cs]).ravel()
        Lk = np.concatenate([learned[s] for s in cs])
        Tk = np.concatenate([true_w[s] for s in cs])
        if Rk.std() == 0 or Lk.std() == 0 or Tk.std() == 0:
            return None
        return np.corrcoef(z(Rk), z(Lk))[0, 1] - np.corrcoef(z(Rk), z(Tk))[0, 1]
    lo, hi, dist = cluster_boot(ctx, diff)
    print("\n[5] MATCHED-SAMPLE TEST  r(report,learned) > r(report,true)")
    print(f"    r(report, learned) = {r_rl:+.4f}")
    print(f"    r(report, true)    = {r_rt:+.4f}")
    print(f"    r(learned, true)   = {r_lt:+.4f}   (shared-variable dependence)")
    print(f"    difference         = {r_rl - r_rt:+.4f}")
    print(f"    cluster bootstrap 95% CI on the difference: [{lo:+.4f}, {hi:+.4f}]")
    print(f"    P(diff <= 0) under bootstrap = {float((dist <= 0).mean()):.4f}")
    print(f"    Williams' t({n-3}) = {t_w:.3f}, p = {p_w:.4g}  (parametric cross-check,")
    print(f"      treats the 5 attrs per context as independent, so it OVERSTATES n)")

    json.dump({
        "spearman": {"ours_rho": sp_ours.statistic, "ours_pearson": pe_ours.statistic,
                     "plunkett_rho": sp_p.statistic, "plunkett_pearson": pe_p.statistic,
                     "ours_n_contexts": len(ctx), "plunkett_n_contexts": len(pctx)},
        "regression": {"standardised_slope": sl_s, "standardised_intercept": ic_s,
                       "unstandardised_slope": sl_u, "unstandardised_intercept": ic_u,
                       "sd_ratio_reported_over_learned": R.std()/L.std()},
        "reliability": {"report_split_half": rh, "report_full": rfull,
                        "learned_split_half": lh, "learned_full": lfull,
                        "attenuation_ceiling": ceiling,
                        "observed": pe_ours.statistic,
                        "disattenuated": pe_ours.statistic/ceiling,
                        "pct_of_ceiling": pe_ours.statistic/ceiling*100},
        "heterogeneity": {"n": len(w), "mean": w.mean(), "median": float(np.median(w)),
                          "sd": w.std(ddof=1), "positive": int((w > 0).sum()),
                          "negative": int((w < 0).sum()),
                          "quantiles": dict(zip(["0","10","25","50","75","90","100"], qs.tolist())),
                          "sign_test_p": sign.pvalue,
                          "loo_min": min(loo), "loo_max": max(loo)},
        "matched_test": {"r_report_learned": r_rl, "r_report_true": r_rt,
                         "r_learned_true": r_lt, "difference": r_rl - r_rt,
                         "boot_ci95": [lo, hi], "boot_p_diff_le_0": float((dist <= 0).mean()),
                         "williams_t": float(t_w), "williams_p": float(p_w)},
    }, open(O / "g4omini_followups.json", "w"), indent=2, default=str)
    print(f"\n-> {O/'g4omini_followups.json'}")


if __name__ == "__main__":
    main()
