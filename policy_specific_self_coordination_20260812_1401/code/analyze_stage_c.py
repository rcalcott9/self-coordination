"""
Stage C analysis - the primary test, plus every alternative explanation the spec
requires be tested separately rather than folded into the headline.

  A  matched-pair analysis   within-pair attempt-rate differences, per safe payoff
  B  trial-level logistic    attempt ~ safe + true + auditor + salience + model
                             + fallback category (+ interactions)
  C  residual self-knowledge policy_specific = true_self_match - auditor_predicted
  D  threshold analysis      behavioural switch point vs the EV-neutral p = S/10

  alternatives   generic salience / generic difficulty / position fallback /
                 global optimism / payoff insensitivity / reasoning artifacts

Logistic regression is a self-contained IRLS fit (no statsmodels dependency) with
bootstrap CIs clustered on stimulus - because stimuli are deliberately selected and
few, trial-level standard errors that treat API calls as independent would badly
overstate precision. Stimulus-level effects are reported raw alongside.

Run:  python3 analyze_stage_c.py [--stage-c <C.csv>]
"""
import argparse, csv, glob, math, os, random, statistics, sys
from collections import Counter, defaultdict
import psc_common as P
import targeted_common as tc

try:
    import numpy as np
except ImportError:
    sys.exit("numpy required")

BOOT = 5000
PERM = 2000       # permutations for the primary per-pair joint test
SEED = 20260816


def newest(pattern):
    files = [f for f in glob.glob(os.path.join(P.DATA, pattern)) if "_DRY" not in f]
    return max(files, key=os.path.getmtime) if files else None


def read(path):
    return list(csv.DictReader(open(path)))


# ------------------------------------------------------------ logistic (IRLS) --
def logistic_fit(X, y, ridge=1e-6, iters=50):
    """Newton-Raphson / IRLS. X includes an intercept column. Tiny ridge for stability."""
    n, k = X.shape
    beta = np.zeros(k)
    for _ in range(iters):
        eta = X @ beta
        p = 1.0 / (1.0 + np.exp(-np.clip(eta, -30, 30)))
        W = np.clip(p * (1 - p), 1e-9, None)
        z = eta + (y - p) / W
        XtW = X.T * W
        A = XtW @ X + ridge * np.eye(k)
        try:
            new = np.linalg.solve(A, XtW @ z)
        except np.linalg.LinAlgError:
            break
        if np.max(np.abs(new - beta)) < 1e-9:
            beta = new
            break
        beta = new
    return beta


def cluster_boot(X, y, clusters, names, b=BOOT, seed=SEED):
    """Bootstrap resampling whole stimuli (clusters), not trials."""
    rng = random.Random(seed)
    uniq = sorted(set(clusters))
    idx_by = {c: np.where(np.array(clusters) == c)[0] for c in uniq}
    draws = []
    for _ in range(b):
        pick = [rng.choice(uniq) for _ in uniq]
        idx = np.concatenate([idx_by[c] for c in pick])
        if len(set(y[idx])) < 2:
            continue
        draws.append(logistic_fit(X[idx], y[idx]))
    if not draws:
        return {n: (float("nan"),) * 2 for n in names}
    D = np.array(draws)
    return {n: (float(np.percentile(D[:, i], 2.5)), float(np.percentile(D[:, i], 97.5)))
            for i, n in enumerate(names)}


def fit_report(rows, terms, label, out):
    """rows: list of dicts with 'y' and the numeric terms. Returns coefficient rows."""
    y = np.array([r["y"] for r in rows], dtype=float)
    if len(set(y)) < 2:
        print(f"  [{label}] skipped - no variation in ATTEMPT")
        return
    names = ["intercept"] + terms
    X = np.column_stack([np.ones(len(rows))] + [[r[t] for r in rows] for t in terms])
    beta = logistic_fit(X, y)
    ci = cluster_boot(X, y, [r["stimulus"] for r in rows], names)
    print(f"\n  [{label}]  n={len(rows)} trials, {len(set(r['stimulus'] for r in rows))} stimuli")
    print(f"    {'term':42}{'beta':>9}{'OR':>8}   95% CI (stimulus-clustered)")
    for i, nm in enumerate(names):
        lo, hi = ci[nm]
        star = "*" if (lo > 0 or hi < 0) else " "
        print(f"  {star} {nm:42}{beta[i]:9.3f}{math.exp(beta[i]):8.3f}   "
              f"[{lo:+.3f}, {hi:+.3f}]")
        out.append(dict(model_spec=label, term=nm, beta=round(float(beta[i]), 5),
                        odds_ratio=round(math.exp(beta[i]), 5),
                        ci_lo=round(lo, 5), ci_hi=round(hi, 5),
                        excludes_zero=(lo > 0 or hi < 0),
                        n_trials=len(rows),
                        n_stimuli=len(set(r["stimulus"] for r in rows))))


def prop_ci(k, n, seed=SEED, b=2000):
    if not n:
        return float("nan"), float("nan")
    rng = random.Random(seed)
    v = [1] * k + [0] * (n - k)
    d = sorted(statistics.fmean(rng.choices(v, k=n)) for _ in range(b))
    return d[int(0.025 * b)], d[int(0.975 * b)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage-c", default=None)
    args = ap.parse_args()
    c_path = args.stage_c or newest("stageC_*.csv")
    if not c_path:
        sys.exit("no Stage C raw CSV found")
    for f in ("fresh_self_match.csv", "auditor_predictions.csv", "salience_ratings.csv"):
        if not os.path.exists(os.path.join(P.DATA, f)):
            sys.exit(f"missing {f} - run analyze_stage_ab.py first")

    truth = {(r["model"], r["stimulus"]): r for r in read(os.path.join(P.DATA, "fresh_self_match.csv"))}
    aud = {(r["focal_model"], r["stimulus"]): r for r in read(os.path.join(P.DATA, "auditor_predictions.csv"))}
    sal = {r["stimulus"]: r for r in read(os.path.join(P.DATA, "salience_ratings.csv"))
           if r["rater_model"] == "pooled"}
    pairs = [r for r in read(os.path.join(P.EXP, "matched_pairs.csv"))
             if str(r.get("approved", "")).lower() in ("true", "1", "yes")]

    rows = P.load_analysis_rows(c_path)
    print(f"=== Stage C: {os.path.basename(c_path)}  ({len(rows)} valid trials) ===")

    # ---------------------------------------------------------------- cells ----
    cells = defaultdict(list)
    for r in rows:
        cells[(r["actor_model"], r["stimulus"], int(r["safe_payoff"]))].append(r)

    attempt_rows, csv_out = [], []
    for (m, sid, safe), rs in sorted(cells.items()):
        k = sum(1 for r in rs if r["participation_decision"] == "ATTEMPT")
        n = len(rs)
        lo, hi = prop_ci(k, n)
        t, a = truth.get((m, sid)), aud.get((m, sid))
        # coordination CONDITIONAL on attempting, from the CHOICE line
        att = [r for r in rs if r["participation_decision"] == "ATTEMPT"
               and r["parsed_choice_identity"]]
        cond = tc.unbiased_match(Counter(r["parsed_choice_identity"] for r in att)) if len(att) > 1 else float("nan")
        attempt_rows.append(dict(
            model=m, model_name=P.DISPLAY[m], stimulus=sid, safe_payoff=safe,
            n=n, n_attempt=k, attempt_rate=round(k / n, 4) if n else "",
            ci_lo=round(lo, 4), ci_hi=round(hi, 4),
            ev_neutral_p=round(safe / 10, 3),
            true_self_match=t["self_match_unbiased"] if t else "",
            auditor_predicted=a["auditor_predicted_match"] if a else "",
            salience=sal.get(sid, {}).get("salience", ""),
            policy_specific=(round(float(t["self_match_unbiased"]) - float(a["auditor_predicted_match"]), 4)
                             if t and a else ""),
            category=t["stimulus_category"] if t else "",
            form_consistency=t["form_consistency"] if t else "",
            n_attempt_with_choice=len(att),
            conditional_match_given_attempt=round(cond, 4) if cond == cond else "",
            ev_correct_entry=(k / n > 0.5) == (float(t["self_match_unbiased"]) > safe / 10) if (t and n) else "",
        ))

    with open(os.path.join(P.DATA, "attempt_rates.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(attempt_rows[0])); w.writeheader(); w.writerows(attempt_rows)
    print(f"  -> {os.path.join(P.DATA, 'attempt_rates.csv')}")

    # ------------------------------------------------- A. matched-pair test ----
    print("\n=== A. MATCHED-PAIR ANALYSIS (the primary test) ===")
    print("   Within pairs matched on public coordinability, does the model bet more on")
    print("   the stimulus where its OWN policy actually coordinates better?")
    print("\n   PRIMARY: one joint payoff-response model per pair -")
    print("     attempt ~ is_high + safe_payoff   (logistic, trials from all payoffs)")
    print("   tested by permuting the high/low stimulus label WITHIN each payoff stratum,")
    print("   so the payoff response is preserved and the four payoff levels contribute")
    print("   one statistic, not four. The per-payoff differences printed underneath are")
    print("   DESCRIPTIVE ONLY: they are the same two stimuli and the same two Stage-A")
    print("   estimates re-tested four times, so they are not independent replications.")
    rate = {(r["model"], r["stimulus"], r["safe_payoff"]): r for r in attempt_rows}
    by_ms = defaultdict(list)
    for r in rows:
        by_ms[(r["actor_model"], r["stimulus"])].append(r)

    def joint_pair_test(m, hi_s, lo_s):
        """Primary per-pair statistic: beta on is_high in attempt ~ is_high + safe.

        One statistic per pair, using every trial at every payoff. The null is
        tested by permuting the high/low label WITHIN each payoff stratum, which
        preserves the payoff response and the per-payoff cell sizes while destroying
        only the stimulus->attempt association. One-sided: the prediction is beta>0.
        """
        trials = []
        for sid, is_high in ((hi_s, 1.0), (lo_s, 0.0)):
            for r in by_ms.get((m, sid), []):
                trials.append((1.0 if r["participation_decision"] == "ATTEMPT" else 0.0,
                               is_high, float(r["safe_payoff"])))
        if not trials:
            return None
        y = np.array([t[0] for t in trials])
        if len(set(y)) < 2:
            return dict(beta=float("nan"), p=float("nan"), n=len(trials), note="no variation")
        lab = np.array([t[1] for t in trials])
        safe = np.array([t[2] for t in trials])
        def beta_of(labels):
            X = np.column_stack([np.ones(len(y)), labels, safe])
            return logistic_fit(X, y)[1]
        obs = beta_of(lab)
        strata = {v: np.where(safe == v)[0] for v in sorted(set(safe))}
        rng = random.Random(f"{SEED}|joint|{m}|{hi_s}|{lo_s}")
        ge = 0
        for _ in range(PERM):
            perm = lab.copy()
            for idx in strata.values():
                vals = [lab[i] for i in idx]
                rng.shuffle(vals)
                perm[idx] = vals
            if beta_of(perm) >= obs - 1e-12:
                ge += 1
        return dict(beta=float(obs), p=(ge + 1) / (PERM + 1), n=len(trials), note="")

    pair_rows, joint_rows, joint_extra = [], [], {}
    for p in pairs:
        m, hi_s, lo_s = p["focal_model"], p["stimulus_high"], p["stimulus_low"]
        jt = joint_pair_test(m, hi_s, lo_s)
        if jt:
            star = "*" if jt["p"] == jt["p"] and jt["p"] < 0.05 else " "
            print(f"\n  {star} [{P.DISPLAY[m]}] {hi_s} vs {lo_s}  JOINT: beta_is_high="
                  f"{jt['beta']:+.3f}  one-sided perm p={jt['p']:.4f}  (n={jt['n']} trials)")
            # --- secondary, per pair ---
            def pooled(sid):
                rs = by_ms.get((m, sid), [])
                k = sum(1 for r in rs if r["participation_decision"] == "ATTEMPT")
                return (k / len(rs)) if rs else float("nan"), len(rs)
            ph, nh_ = pooled(hi_s); pl, nl_ = pooled(lo_s)
            print(f"      pooled P(ATTEMPT): high {ph:.3f} (n={nh_})  low {pl:.3f} (n={nl_})"
                  f"   diff {ph - pl:+.3f}")
            # monotone decline in ATTEMPT as SAFE rises?
            for sid, lab in ((hi_s, "high"), (lo_s, "low")):
                seq = [(sv, rate[(m, sid, sv)]["attempt_rate"])
                       for sv in sorted(set(r["safe_payoff"] for r in attempt_rows))
                       if (m, sid, sv) in rate]
                vals = [v for _, v in seq]
                mono = all(b <= a + 1e-9 for a, b in zip(vals, vals[1:])) if len(vals) > 1 else None
                t = truth.get((m, sid))
                pstar = float(t["self_match_unbiased"]) if t else float("nan")
                # EV benchmark: attempt iff p > S/10
                ev = [(sv, 1 if pstar > sv / 10 else 0) for sv, _ in seq]
                dev = [f"S{sv}:{v:.2f}vs{e}" for (sv, v), (_, e) in zip(seq, ev)]
                print(f"      {lab:4} p*={pstar:.2f}  declines with SAFE: "
                      f"{'yes' if mono else 'NO' if mono is not None else '?'}"
                      f"   observed vs EV-optimal  {' '.join(dev)}")
            joint_extra[p["pair_id"]] = dict(pooled_high=round(ph, 4), pooled_low=round(pl, 4),
                                             pooled_diff=round(ph - pl, 4))
            joint_rows.append(dict(pair_id=p["pair_id"], focal_model=m,
                                   stimulus_high=hi_s, stimulus_low=lo_s,
                                   pair_kind=p["pair_kind"],
                                   delta_true_select=p.get("delta_true", ""),
                                   delta_true_holdout=p.get("delta_true_holdout", ""),
                                   beta_is_high=round(jt["beta"], 5),
                                   perm_p_one_sided=round(jt["p"], 5),
                                   n_trials=jt["n"], note=jt["note"]))
        print(f"      descriptive per-payoff breakdown (NOT independent tests): "
              f"d_true={float(p['abs_delta_true']):+.3f} "
              f"d_auditor={float(p['abs_delta_auditor']):.3f} ({p['pair_kind']})")
        for safe in sorted(set(r["safe_payoff"] for r in attempt_rows)):
            rh, rl = rate.get((m, hi_s, safe)), rate.get((m, lo_s, safe))
            if not rh or not rl:
                continue
            kh, nh, kl, nl = rh["n_attempt"], rh["n"], rl["n_attempt"], rl["n"]
            # The observed statistic MUST come from the raw counts, not from the
            # rounded attempt_rate column. round(k/n, 4) moves the observed value off
            # the achievable lattice by up to 1e-4; when it rounds UP, every
            # permutation replicate landing exactly ON the observed statistic fails a
            # bare `>= d` and is dropped from the tail. At n=30 that tie carries most
            # of the one-sided tail (for 20/30 vs 10/30 it is ~79% of it), so p was
            # anti-conservative by ~3.5x, arbitrarily per cell depending on which way
            # the rounding fell. The tolerance keeps ties counted, as a permutation
            # test's `>=` requires.
            d = kh / nh - kl / nl
            pool = [1] * (kh + kl) + [0] * (nh + nl - kh - kl)
            # Seeded per pair AND payoff so different pairs do not replay one stream.
            rng = random.Random(f"{SEED}|{p['pair_id']}|{safe}")
            ge = sum(1 for _ in range(BOOT)
                     if (lambda s: statistics.fmean(s[:nh]) - statistics.fmean(s[nh:]))
                     (rng.sample(pool, len(pool))) >= d - 1e-12)
            pval = (ge + 1) / (BOOT + 1)
            print(f"        safe={safe}  P(ATTEMPT) {rh['attempt_rate']:.3f} vs "
                  f"{rl['attempt_rate']:.3f}   delta={d:+.3f}   (descriptive p={pval:.4f})")
            pair_rows.append(dict(pair_id=p["pair_id"], focal_model=m, safe_payoff=safe,
                                  pair_kind=p["pair_kind"],
                                  delta_true=p["abs_delta_true"],
                                  delta_auditor=p["abs_delta_auditor"],
                                  attempt_high=rh["attempt_rate"], attempt_low=rl["attempt_rate"],
                                  delta_attempt=round(d, 4), perm_p_one_sided=round(pval, 5)))
    if pair_rows:
        with open(os.path.join(P.DATA, "matched_pair_results.csv"), "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(pair_rows[0])); w.writeheader(); w.writerows(pair_rows)
        pos = sum(1 for r in pair_rows if r["delta_attempt"] > 0)
        print(f"\n  descriptive: {pos}/{len(pair_rows)} pair x payoff cells have "
              f"delta_attempt > 0")
        print("  NOT a sign test - the 4 cells within a pair are the same two stimuli.")
    if joint_rows:
        with open(os.path.join(P.DATA, "matched_pair_joint.csv"), "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(joint_rows[0]))
            w.writeheader(); w.writerows(joint_rows)
        for r in joint_rows:
            r.update(joint_extra.get(r["pair_id"], {}))
        npos = sum(1 for r in joint_rows if r["beta_is_high"] > 0)
        print(f"\n  PRIMARY RESULT: {npos}/{len(joint_rows)} pairs have beta_is_high > 0; "
              f"{sum(1 for r in joint_rows if r['perm_p_one_sided'] < 0.05)} at p<0.05")
        for mm in ("gpt", "claude"):
            sub = [r for r in joint_rows if r["focal_model"] == mm]
            if not sub:
                continue
            betas = sorted(r["beta_is_high"] for r in sub)
            diffs = sorted(r.get("pooled_diff", 0.0) for r in sub)
            print(f"    {P.DISPLAY[mm]:16} {sum(1 for b in betas if b > 0)}/{len(sub)} positive; "
                  f"median beta {betas[len(betas)//2]:+.3f}; "
                  f"median pooled P(ATTEMPT) diff {diffs[len(diffs)//2]:+.3f}")
        print("  Each pair contributes ONE statistic. The 4 payoff cells within a pair are")
        print("  the same two stimuli and are not independent confirmations.")
        print(f"  -> {os.path.join(P.DATA, 'matched_pair_joint.csv')}")

    # -------------------------------------------------- B. trial-level model ---
    print("\n=== B. TRIAL-LEVEL LOGISTIC MODELS ===")
    tr = []
    for r in rows:
        m, sid = r["actor_model"], r["stimulus"]
        t, a = truth.get((m, sid)), aud.get((m, sid))
        if not t or not a:
            continue
        tr.append(dict(
            y=1.0 if r["participation_decision"] == "ATTEMPT" else 0.0,
            stimulus=sid, model=m,
            safe=float(r["safe_payoff"]),
            true=float(t["self_match_unbiased"]),
            auditor=float(a["auditor_predicted_match"]),
            salience=float(sal[sid]["salience"]) if sid in sal else 0.0,
            is_claude=1.0 if m == "claude" else 0.0,
            fallback=1.0 if str(t["fallback"]) == "True" else 0.0,
            policy_specific=float(t["self_match_unbiased"]) - float(a["auditor_predicted_match"]),
        ))
    coef = []
    fit_report(tr, ["safe", "true"], "baseline: safe + true", coef)
    fit_report(tr, ["safe", "true", "auditor", "salience", "is_claude", "fallback"],
               "full: does TRUE survive controlling for public salience?", coef)
    fit_report(tr, ["safe", "auditor", "salience"],
               "public-only (alternative 1): auditor + salience, no true", coef)
    for m in ("gpt", "claude"):
        sub = [r for r in tr if r["model"] == m]
        if sub:
            fit_report(sub, ["safe", "true", "auditor"], f"model-specific: {P.DISPLAY[m]}", coef)

    # ---------------------------------------- C. residual self-knowledge -------
    print("\n=== C. RESIDUAL SELF-KNOWLEDGE ===")
    print("   policy_specific = true_self_match - auditor_predicted_match")
    print("   Does it predict ATTEMPT beyond the auditor's public estimate?")
    fit_report(tr, ["safe", "auditor", "policy_specific"],
               "auditor + policy_specific residual", coef)
    print("   NOTE: a positive residual coefficient is consistent with policy-specific")
    print("   self-knowledge. It is NOT by itself evidence of introspection - the model")
    print("   may have learned a self-model without introspective access.")

    if coef:
        with open(os.path.join(P.DATA, "regression_results.csv"), "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(coef[0])); w.writeheader(); w.writerows(coef)
        print(f"\n  -> {os.path.join(P.DATA, 'regression_results.csv')}")

    # ------------------------------------------------- D. threshold analysis ---
    print("\n=== D. THRESHOLD ANALYSIS (normative benchmark, not a mechanism claim) ===")
    print("   Entry maximises EV when p(match) > S/10.")
    print(f"   {'model':16}{'stimulus':16}{'true p':>8}{'EV-switch S':>13}   behavioural pattern")
    for m in ("gpt", "claude"):
        for sid in sorted(set(r["stimulus"] for r in attempt_rows if r["model"] == m)):
            t = truth.get((m, sid))
            if not t:
                continue
            p_true = float(t["self_match_unbiased"])
            cells_m = sorted((r for r in attempt_rows if r["model"] == m and r["stimulus"] == sid),
                             key=lambda r: r["safe_payoff"])
            beh = " ".join(f"{r['safe_payoff']}:{r['attempt_rate']:.2f}" for r in cells_m)
            print(f"   {P.DISPLAY[m]:16}{sid:16}{p_true:8.3f}{p_true * 10:13.1f}   {beh}")

    # ------------------------------------------------ alternatives -------------
    print("\n=== ALTERNATIVE EXPLANATIONS (kept separate from the headline) ===")
    for m in ("gpt", "claude"):
        sub = [r for r in attempt_rows if r["model"] == m]
        if sub:
            print(f"  4. global optimism - {P.DISPLAY[m]} mean P(ATTEMPT) = "
                  f"{statistics.fmean(r['attempt_rate'] for r in sub):.3f}")
    print("  5. payoff sensitivity - mean P(ATTEMPT) by safe payoff:")
    for safe in sorted(set(r["safe_payoff"] for r in attempt_rows)):
        sub = [r for r in attempt_rows if r["safe_payoff"] == safe]
        print(f"       safe={safe}: {statistics.fmean(r['attempt_rate'] for r in sub):.3f}")
    print("     (ATTEMPT should decline as SAFE rises; a flat line means the model is")
    print("      ignoring the payoff and the whole design is uninformative.)")

    print("  3. position fallback - conditional coordination among ATTEMPT trials, and")
    print("     Stage-A form consistency, per cell (see attempt_rates.csv columns")
    print("     conditional_match_given_attempt / form_consistency). A low-match stimulus")
    print("     with FC < 0.80 reflects a stable LEFT/RIGHT rule, not indifference.")

    pos_words = 0
    for r in rows:
        if tc.POS_WORDS.search(r["response_raw"].split("DECISION:")[0]):
            pos_words += 1
    print(f"  6. reasoning artifacts (EXPLORATORY) - {pos_words}/{len(rows)} rationales "
          f"mention position words before the decision")
    for kw in ("copy", "copies", "myself", "same model", "instance", "focal", "obvious",
               "left", "right", "distinctive"):
        n = sum(1 for r in rows if kw in r["response_raw"].lower())
        print(f"       {kw:14} {n:5}  ({n / max(len(rows), 1):.1%})")


if __name__ == "__main__":
    main()
