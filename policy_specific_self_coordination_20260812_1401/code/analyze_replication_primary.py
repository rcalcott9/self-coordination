"""
PRIMARY replication analysis (spec §7) + frozen secondaries §12.A and §12.B.

Written BEFORE Stage C data existed. Reuses logistic_fit / cluster_boot from
analyze_stage_c.py unchanged - the same estimator code that produced the original
result, so the two generations are analysed identically.

PRIMARY (§7)
  delta_hat = coefficient on is_high in
      logit P(attempt) = alpha_model + beta_model * safe_payoff + delta * is_high
  pooled over ALL Stage C trials from ALL approved pairs, 95% CI from a cluster
  bootstrap resampling WHOLE STIMULI (5,000 draws).
  Replication declared iff delta_hat > 0 AND the 95% CI excludes 0.

  Companion permutation test, same logic as the original: statistic = mean over pairs
  of (p_attempt_high - p_attempt_low), permuting the high/low label WITHIN
  (pair x payoff) strata, one-sided (H1: delta > 0), on RAW COUNTS - never rounded
  rates (the bug caught 2026-08-12). 20,000 permutations (spec §7).

SECONDARY (§12, sensitivity - NEVER replaces the primary)
  A  leave-one-pair-out: recompute pooled delta 5x, omitting one pair each time.
     Direction and magnitude only. NOT five hypothesis tests.
  B  proto-excluded: recompute pooled delta without Pair 1 (gpt proto > s_arrow).

Run:  . replication_5_4_4_8/env.sh && python3 analyze_replication_primary.py
"""
import csv, json, os, random, sys
import numpy as np
import psc_common as P
from analyze_stage_c import logistic_fit, cluster_boot, newest, read, BOOT

PERM = 20000
SEED = 20260816
OUT = os.path.join(P.EXP, "analysis", "primary")


def load():
    ap = list(csv.DictReader(open(os.path.join(P.EXP, "pairs", "approved_pairs.csv"))))
    pairs = [dict(pair_id=p["pair_id"], model=p["focal_model"],
                  model_name=p["focal_model_name"],
                  hi=p["stimulus_high"], lo=p["stimulus_low"]) for p in ap]
    path = newest("stageC_*.csv")
    if not path:
        sys.exit("no Stage C data")
    rows = [r for r in read(path) if r["included_in_analysis"] == "True"]
    cell = {}
    for r in rows:
        cell.setdefault((r["actor_model"], r["stimulus"]), []).append(r)

    trials = []
    for i, p in enumerate(pairs):
        for sid, is_high in ((p["hi"], 1.0), (p["lo"], 0.0)):
            for r in cell.get((p["model"], sid), []):
                trials.append(dict(
                    y=1.0 if r["participation_decision"] == "ATTEMPT" else 0.0,
                    is_high=is_high, safe=float(r["safe_payoff"]),
                    model=p["model"], stimulus=sid, pair=i, pair_id=p["pair_id"]))
    return pairs, trials, path


def design(trials, models):
    """alpha_m + beta_m * safe + delta * is_high, with per-model intercept and slope."""
    names, cols = [], []
    for m in models:                                   # per-model intercept
        names.append(f"alpha[{m}]"); cols.append([1.0 if t["model"] == m else 0.0 for t in trials])
    for m in models:                                   # per-model payoff slope
        names.append(f"beta_safe[{m}]")
        cols.append([t["safe"] if t["model"] == m else 0.0 for t in trials])
    names.append("delta_is_high"); cols.append([t["is_high"] for t in trials])
    return np.column_stack(cols), np.array([t["y"] for t in trials]), names


def pooled_delta(trials, label, boot=BOOT):
    models = sorted({t["model"] for t in trials})
    X, y, names = design(trials, models)
    beta = logistic_fit(X, y)
    ci = cluster_boot(X, y, [t["stimulus"] for t in trials], names, b=boot, seed=SEED)
    i = names.index("delta_is_high")
    d, (lo, hi) = float(beta[i]), ci["delta_is_high"]
    print(f"    {label:34} delta={d:+.3f}  OR={np.exp(d):.2f}  "
          f"95% CI [{lo:+.3f}, {hi:+.3f}]  {'EXCLUDES 0' if lo > 0 or hi < 0 else 'includes 0'}")
    return dict(label=label, delta=d, or_=float(np.exp(d)), ci_lo=lo, ci_hi=hi,
                n_trials=len(trials), n_stimuli=len({t["stimulus"] for t in trials}),
                n_pairs=len({t["pair"] for t in trials}),
                ci_excludes_zero=bool(lo > 0 or hi < 0))


def permutation(pairs, trials):
    """Mean over pairs of (p_hi - p_lo), permuted within (pair x payoff) strata."""
    strata = {}
    for t in trials:
        strata.setdefault((t["pair"], t["safe"]), []).append(t)

    def stat(assign):
        per_pair = {}
        for (pi, _s), ts in strata.items():
            for t, hi in zip(ts, assign[(pi, _s)]):
                k = per_pair.setdefault(pi, [0, 0, 0, 0])   # k_hi n_hi k_lo n_lo
                if hi:
                    k[0] += t["y"]; k[1] += 1
                else:
                    k[2] += t["y"]; k[3] += 1
        vals = [k[0] / k[1] - k[2] / k[3] for k in per_pair.values() if k[1] and k[3]]
        return sum(vals) / len(vals) if vals else 0.0

    obs_assign = {k: [t["is_high"] == 1.0 for t in ts] for k, ts in strata.items()}
    obs = stat(obs_assign)
    rng = random.Random(SEED)
    ge = 0
    for _ in range(PERM):
        a = {}
        for k, ts in strata.items():
            lab = [t["is_high"] == 1.0 for t in ts]
            rng.shuffle(lab)
            a[k] = lab
        if stat(a) >= obs - 1e-12:
            ge += 1
    p = (ge + 1) / (PERM + 1)
    print(f"\n    permutation (within pair x payoff, {PERM:,} draws, raw counts)")
    print(f"      observed mean high-minus-low attempt gap = {obs:+.4f}")
    print(f"      one-sided p = {p:.5f}" + ("   [resolution floor]" if ge == 0 else ""))
    return dict(observed=obs, p_one_sided=p, n_perm=PERM, at_floor=bool(ge == 0))


def per_pair(pairs, trials):
    print(f"\n    {'#':2} {'pair':40}{'p_hi':>7}{'p_lo':>7}{'gap':>8}  n")
    out = []
    for i, p in enumerate(pairs):
        hi = [t for t in trials if t["pair"] == i and t["is_high"] == 1.0]
        lo = [t for t in trials if t["pair"] == i and t["is_high"] == 0.0]
        phi = sum(t["y"] for t in hi) / len(hi)
        plo = sum(t["y"] for t in lo) / len(lo)
        print(f"    {i+1:2} {p['model_name']+' '+p['hi']+' > '+p['lo']:40}"
              f"{phi:7.3f}{plo:7.3f}{phi-plo:+8.3f}  {len(hi)+len(lo)}")
        out.append(dict(pair=i + 1, pair_id=p["pair_id"], model=p["model_name"],
                        high=p["hi"], low=p["lo"], p_high=phi, p_low=plo,
                        gap=phi - plo, n=len(hi) + len(lo)))
    npos = sum(1 for r in out if r["gap"] > 0)
    print(f"       {npos} of {len(out)} pairs have a positive high-minus-low contrast")
    return out, npos


def monotonicity(pairs, trials):
    print(f"\n    payoff monotonicity   {'safe':>6}{'p_hi':>8}{'p_lo':>8}{'gap':>8}")
    out = []
    for s in sorted({t["safe"] for t in trials}):
        hi = [t for t in trials if t["safe"] == s and t["is_high"] == 1.0]
        lo = [t for t in trials if t["safe"] == s and t["is_high"] == 0.0]
        phi = sum(t["y"] for t in hi) / len(hi)
        plo = sum(t["y"] for t in lo) / len(lo)
        print(f"    {'':22}{s:6.0f}{phi:8.3f}{plo:8.3f}{phi-plo:+8.3f}")
        out.append(dict(safe=s, p_high=phi, p_low=plo, gap=phi - plo))
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    pairs, trials, path = load()
    print(f"\n=== REPLICATION PRIMARY ANALYSIS ===\n  source {os.path.basename(path)}")
    print(f"  {len(trials)} trials, {len(pairs)} approved pairs, "
          f"{len({t['stimulus'] for t in trials})} stimuli")

    print("\n--- PRIMARY (spec §7): pooled delta on is_high ---")
    perm = permutation(pairs, trials)
    pp, npos = per_pair(pairs, trials)
    mono = monotonicity(pairs, trials)
    primary = (pooled_delta(trials, f"ALL {len(pairs)} pairs (PRIMARY)")
               if len(pairs) >= 3 else None)

    # SMALL-k GUARD. Below 3 pairs the pooled cluster bootstrap has too few clusters
    # and leave-one-out can empty the design entirely (this crashed on the 1-pair
    # Opus 4.5 run). Return "not estimable" with a reason - never silently substitute
    # a different inference procedure.
    if len(pairs) < 3:
        print(f"\n  *** BELOW MINIMUM PAIR COUNT ({len(pairs)} < 3).")
        print("  *** Pooled delta, leave-one-out and cluster bootstrap are NOT ESTIMABLE.")
        json.dump(dict(primary=None, not_estimable=True, n_pairs=len(pairs),
                       reason=f"only {len(pairs)} selected pairs; pooled cluster "
                              f"bootstrap needs >=3 pairs (>=6 stimulus clusters)",
                       permutation=perm, per_pair=pp, n_positive=npos,
                       monotonicity=mono, source=os.path.basename(path)),
                  open(os.path.join(OUT, "primary_results.json"), "w"), indent=2)
        print(f"  -> {OUT}/primary_results.json")
        return

    print("\n--- §12.A leave-one-pair-out (SENSITIVITY, not 5 tests) ---")
    loo = []
    for i, p in enumerate(pairs):
        sub = [t for t in trials if t["pair"] != i]
        loo.append(pooled_delta(sub, f"omit pair {i+1} ({p['hi']}>{p['lo']})"))

    print("\n--- §12.B proto-excluded (PRE-SPECIFIED SENSITIVITY) ---")
    pi = next((i for i, p in enumerate(pairs) if p["hi"] == "proto"), None)
    proto_ex = (pooled_delta([t for t in trials if t["pair"] != pi], "excluding proto pair")
                if pi is not None else None)

    verdict = primary["delta"] > 0 and primary["ci_excludes_zero"]
    print(f"\n  REPLICATION DECLARED: {verdict}   "
          f"(delta>0 AND 95% CI excludes 0, spec §7)")

    json.dump(dict(primary=primary, permutation=perm, per_pair=pp, n_positive=npos,
                   monotonicity=mono, leave_one_out=loo, proto_excluded=proto_ex,
                   replication_declared=bool(verdict), source=os.path.basename(path)),
              open(os.path.join(OUT, "primary_results.json"), "w"), indent=2)
    print(f"  -> {OUT}/primary_results.json")


if __name__ == "__main__":
    main()
