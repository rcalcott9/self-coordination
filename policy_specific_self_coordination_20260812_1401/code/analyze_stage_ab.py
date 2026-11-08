"""
Analysis for Stages A and B, ending in the matched-pair table that gates Stage C.

Outputs (all into ../data):
  fresh_self_match.csv        per model x stimulus: choice distribution, P(LEFT),
                              modal identity/share, unbiased dyadic self-match with
                              bootstrap CI, form consistency, fallback flags,
                              old-vs-new comparison against the confirmed battery
  auditor_predictions.csv     per focal x stimulus: mean predicted match, CI, n
  salience_ratings.csv        per rater x stimulus and pooled
  matched_pairs.csv           candidate pairs + selection, with approved=False

Every per-cell statistic comes from targeted_common.cell_metrics / unbiased_match /
boot_draws - the same code that produced the confirmed n=60 numbers.

Run:  python3 analyze_stage_ab.py --stage-a <A.csv> --auditor <B_auditor.csv> \
                                  --salience <B_salience.csv>
      (with no arguments it picks the newest non-dry file of each kind)
"""
import argparse, csv, glob, math, os, statistics, sys
from collections import Counter, defaultdict
import psc_common as P
import targeted_common as tc

# ============================ DESCRIPTIVE HEURISTICS ==========================
# Every threshold below is a DESCRIPTIVE HEURISTIC for surfacing candidates. None
# is an inferential criterion, none performs a test, and none selects a pair. All
# are printed prominently at run time so a reader always sees the values in force.
#
# The two public controls are distinct things and are labelled consistently:
#
#   generic_salience     how obvious / focal the stimulus appears from public
#                        stimulus structure alone (asked about a GENERIC player,
#                        no model named)
#   auditor_prediction   an external MODEL's prediction of the focal model's
#                        self-coordination reliability
#
# auditor_prediction is NOT a pure public baseline: the auditor may have learned
# model-specific information about GPT or Claude, so it can partly anticipate the
# focal model's reliability for reasons unavailable from stimulus structure alone.
# The strongest matched pair therefore differs substantially in true self-match
# while differing little in BOTH public measures.
#
# Primary comparison scale is the standardized difference z_* (difference / battery
# SD). The reliability statistics t_* (difference / SE) are DESCRIPTIVE ONLY: the
# SEs are recovered approximately from bootstrap percentile intervals, so no |t|
# threshold (1.96 or otherwise) is used anywhere as a matching criterion.

LARGE_TRUE_Z = 0.75    # |z_true|   at or above this = a large true-self-match gap
SMALL_PUBLIC_Z = 0.35  # |z_public| at or below this = a small public-measure gap

# Raw-probability-scale advisory flags, reported alongside the z diagnostics because
# probability units are easier to sanity-check than standard deviations.
AUD_TOL = 0.10         # |d_auditor| at or below this = well matched on the auditor
TRUE_MIN = 0.20        # |d_true|    at or above this = usefully separated

TOP_N_SHOWN = 8        # candidates printed per focal model (ALL are written to CSV)
REPEAT_WARN = 2        # warn if one stimulus occupies more than this many of the top N

# Score weights. 1.0 puts a one-SD public mismatch on equal footing with a one-SD
# gain in true-self-match separation.
W_SALIENCE = 1.0
W_AUDITOR = 1.0


def newest(pattern):
    files = [f for f in glob.glob(os.path.join(P.DATA, pattern)) if "_DRY" not in f]
    return max(files, key=os.path.getmtime) if files else None


def as_tc_rows(rows):
    """Adapt our CSV shape to the row shape targeted_common.cell_metrics expects."""
    return [{"choice_identity": r["parsed_choice_identity"],
             "response_side": r["parsed_choice_side"],
             "variant": r["variant"],
             "response_raw": r["response_raw"]} for r in rows]


def assign_halves(rows, cellkey):
    """Deterministic, AB/BA-balanced 50/50 split within every cell.

    WHY. Pairs are ordered high/low, separated, and 'matched' on public measures
    using the same estimates they are then reported with, over 105 within-model
    pairs. Every one of those is an in-sample extremum, so the reported gaps are
    inflated by the sampling noise that helped select them - a winner's curse in
    both directions (d_true too big, d_public too small).

    The split breaks that: the SELECT half orders high/low, drives the score,
    ranking and diagnostic; the HOLDOUT half supplies an independent estimate of the
    same gaps for the pairs so surfaced. Shrinkage from select to holdout is the
    honest measure of how much of a gap was real.

    Within (cell, variant) rows are ordered by run_id and cut in half, so each half
    is exactly AB/BA balanced and the split is reproducible from the data alone with
    no extra seed.
    """
    groups = defaultdict(list)
    for r in rows:
        groups[(cellkey(r), r["variant"])].append(r)
    for g in groups.values():
        g.sort(key=lambda r: r["run_id"])
        half = len(g) // 2
        for i, r in enumerate(g):
            r["_half"] = "select" if i < half else "holdout"
    return rows


def mean_ci(vals, seed, b=5000):
    """Bootstrap percentile CI for a mean."""
    import random
    if not vals:
        return float("nan"), float("nan"), float("nan")
    rng = random.Random(seed)
    n = len(vals)
    draws = sorted(statistics.fmean(rng.choices(vals, k=n)) for _ in range(b))
    return (statistics.fmean(vals), draws[int(0.025 * b)], draws[int(0.975 * b)])


def _match_on(rs, m, model, sid, tag):
    """unbiased self-match + bootstrap CI for a subset of a cell's trials."""
    idents = [r["parsed_choice_identity"] for r in rs]
    if len(idents) < 2:
        return {f"self_match_{tag}": "", f"self_match_{tag}_ci_lo": "",
                f"self_match_{tag}_ci_hi": "", f"n_{tag}": len(idents)}
    v = tc.unbiased_match(Counter(idents))
    draws = tc.boot_draws(idents, seed=f"{tc.BOOT_SEED}|{tag}|{model}|{sid}", b=tc.BOOT_B)
    lo, hi = tc.pct_ci(draws)
    return {f"self_match_{tag}": round(v, 4), f"self_match_{tag}_ci_lo": round(lo, 4),
            f"self_match_{tag}_ci_hi": round(hi, 4), f"n_{tag}": len(idents)}


def analyze_stage_a(path, man):
    rows = P.load_analysis_rows(path)
    assign_halves(rows, lambda r: (r["actor_model"], r["stimulus"]))
    by = defaultdict(list)
    for r in rows:
        by[(r["actor_model"], r["stimulus"])].append(r)

    out = []
    for (model, sid), rs in sorted(by.items()):
        m = man[sid]
        entry = {"stimulus_id": sid, "identity_1": m["identity_1"],
                 "identity_2": m["identity_2"]}
        met = tc.cell_metrics(as_tc_rows(rs), entry)
        idents = [r["parsed_choice_identity"] for r in rs]
        # Seeded per cell, as targeted_analysis.py / calibration_analysis.py do
        # (f"{BOOT_SEED}|{model}|{stimulus}"), so CIs reproduce under the
        # established convention instead of sharing one stream across cells.
        draws = tc.boot_draws(idents, seed=f"{tc.BOOT_SEED}|{model}|{sid}", b=tc.BOOT_B)
        lo, hi = tc.pct_ci(draws)
        cnt = Counter(idents)
        n = len(idents)
        prior_key = "prior_gpt_match" if model == "gpt" else "prior_claude_match"
        fc_key = "prior_gpt_form_consistency" if model == "gpt" else "prior_claude_form_consistency"
        out.append(dict(
            model=model, model_name=P.DISPLAY[model], stimulus=sid,
            stimulus_category=m["prior_class_report"], note=m["prior_note_report"],
            identity_1=m["identity_1"], identity_2=m["identity_2"],
            n_valid=met["n_valid"],
            p_identity_1=round(cnt.get(m["identity_1"], 0) / n, 4) if n else "",
            p_identity_2=round(cnt.get(m["identity_2"], 0) / n, 4) if n else "",
            p_left=met["p_left"],
            modal_identity=met["modal_identity"], modal_share=met["modal_share"],
            self_match_unbiased=met["match_unbiased"],
            self_match_ci_lo=round(lo, 4), self_match_ci_hi=round(hi, 4),
            match_plugin=met["match_plugin"], entropy_bits=met["entropy_bits"],
            p_modal_given_modal_left=met["p_modal_given_modal_left"],
            p_modal_given_modal_right=met["p_modal_given_modal_right"],
            form_consistency=met["form_consistency"],
            fallback=met["form_consistency"] < P.FC_CLEAN if met["form_consistency"] == met["form_consistency"] else "",
            rationale_mentions_position=met["rationale_mentions_position"],
            n_AB=met["n_AB"], n_BA=met["n_BA"],
            prior_match_old_model=m[prior_key],
            prior_form_consistency_old_model=m[fc_key],
            # Expansion-battery stimuli have no prior run, so prior_* are blank and
            # the old-vs-new delta is undefined rather than zero.
            delta_vs_old=(round(met["match_unbiased"] - float(m[prior_key]), 4)
                          if str(m[prior_key]).strip() not in ("", "nan") else ""),
            **_match_on([r for r in rs if r["_half"] == "select"], m, model, sid, "select"),
            **_match_on([r for r in rs if r["_half"] == "holdout"], m, model, sid, "holdout"),
        ))
    return out


def analyze_auditor(path):
    rows = [r for r in P.load_analysis_rows(path) if r["predicted_match_probability"]]
    assign_halves(rows, lambda r: (r["focal_model"], r["stimulus"]))
    by, halves = defaultdict(list), defaultdict(lambda: defaultdict(list))
    for r in rows:
        v = float(r["predicted_match_probability"]) / 100.0
        by[(r["focal_model"], r["stimulus"])].append(v)
        halves[(r["focal_model"], r["stimulus"])][r["_half"]].append(v)
    out = []
    for (focal, sid), vals in sorted(by.items()):
        mu, lo, hi = mean_ci(vals, seed=tc.BOOT_SEED)
        row = dict(focal_model=focal, focal_model_name=P.DISPLAY[focal],
                   auditor_model=P.OTHER[focal],
                   auditor_model_name=P.DISPLAY[P.OTHER[focal]],
                   stimulus=sid, n=len(vals),
                   auditor_predicted_match=round(mu, 4),
                   ci_lo=round(lo, 4), ci_hi=round(hi, 4),
                   sd=round(statistics.pstdev(vals), 4) if len(vals) > 1 else "")
        for tag in ("select", "holdout"):
            hv = halves[(focal, sid)][tag]
            if hv:
                m2, l2, h2 = mean_ci(hv, seed=f"{tc.BOOT_SEED}|{tag}|{focal}|{sid}")
                row.update({f"auditor_{tag}": round(m2, 4),
                            f"auditor_{tag}_ci_lo": round(l2, 4),
                            f"auditor_{tag}_ci_hi": round(h2, 4), f"n_{tag}": len(hv)})
            else:
                row.update({f"auditor_{tag}": "", f"auditor_{tag}_ci_lo": "",
                            f"auditor_{tag}_ci_hi": "", f"n_{tag}": 0})
        out.append(row)
    return out


def analyze_salience(path):
    rows = [r for r in P.load_analysis_rows(path) if r["salience_rating"]]
    assign_halves(rows, lambda r: (r["actor_model"], r["stimulus"]))
    by, pooled = defaultdict(list), defaultdict(list)
    half_by = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    for r in rows:
        v = float(r["salience_rating"]) / 100.0
        by[(r["actor_model"], r["stimulus"])].append(v)
        pooled[r["stimulus"]].append(v)
        half_by[r["stimulus"]][r["_half"]][r["actor_model"]].append(v)
    out = []
    for (rater, sid), vals in sorted(by.items()):
        mu, lo, hi = mean_ci(vals, seed=tc.BOOT_SEED)
        out.append(dict(rater_model=rater, rater_model_name=P.DISPLAY[rater],
                        stimulus=sid, n=len(vals), salience=round(mu, 4),
                        ci_lo=round(lo, 4), ci_hi=round(hi, 4)))
    # Pooled salience: the two raters are systematically different instruments (that
    # is why the arm reports them separately), so pooling their ratings into one
    # exchangeable list and bootstrapping within it understates between-rater
    # uncertainty. Bootstrap over raters instead, and surface their disagreement.
    by_rater = defaultdict(dict)
    for (rater, sid), vals in by.items():
        by_rater[sid][rater] = vals
    for sid, per in sorted(by_rater.items()):
        means = [statistics.fmean(v) for v in per.values() if v]
        if not means:
            continue
        rng = __import__("random").Random(f"{tc.BOOT_SEED}|pooled|{sid}")
        raters = list(per.values())
        draws = []
        for _ in range(5000):                    # two-level: raters, then within
            pick = [rng.choice(raters) for _ in raters]
            draws.append(statistics.fmean(
                statistics.fmean(rng.choices(r, k=len(r))) for r in pick if r))
        draws.sort()
        disagree = (max(means) - min(means)) if len(means) > 1 else 0.0
        row = dict(rater_model="pooled", rater_model_name="pooled (over raters)",
                   stimulus=sid, n=sum(len(v) for v in per.values()),
                   salience=round(statistics.fmean(means), 4),
                   ci_lo=round(draws[int(0.025 * len(draws))], 4),
                   ci_hi=round(draws[int(0.975 * len(draws))], 4),
                   between_rater_abs_diff=round(disagree, 4),
                   n_raters=len(means))
        for tag in ("select", "holdout"):
            hm = [statistics.fmean(v) for v in half_by[sid][tag].values() if v]
            row[f"salience_{tag}"] = round(statistics.fmean(hm), 4) if hm else ""
            row[f"n_{tag}"] = sum(len(v) for v in half_by[sid][tag].values())
        out.append(row)
    return out


def _se(row, lo_key="ci_lo", hi_key="ci_hi"):
    """SE implied by a 95% percentile bootstrap interval: (hi - lo) / 3.92."""
    try:
        lo, hi = float(row[lo_key]), float(row[hi_key])
    except (TypeError, ValueError, KeyError):
        return float("nan")
    return (hi - lo) / 3.919928 if hi >= lo else float("nan")


def _sd(vals):
    vals = [v for v in vals if v == v]
    return statistics.pstdev(vals) if len(vals) > 1 else float("nan")


def diagnose(z_true, z_sal, z_aud):
    """Qualitative label from the standardized differences. Descriptive, not a test.

      ideal              large true gap, small gap in BOTH public measures
      auditor_informed   large true gap, salience matched, auditor NOT matched
      salience_mismatch  large true gap, but the stimuli differ visibly in salience
      non_diagnostic     the true gap is too small to be diagnostic at all

    Thresholds are the module constants, printed at run time.
    """
    if any(v != v for v in (z_true, z_sal, z_aud)):
        return "incomplete"
    large_true = abs(z_true) >= LARGE_TRUE_Z
    small_sal = abs(z_sal) <= SMALL_PUBLIC_Z
    small_aud = abs(z_aud) <= SMALL_PUBLIC_Z
    if not large_true:
        return "non_diagnostic"
    if small_sal and small_aud:
        return "ideal"
    if small_sal:
        return "auditor_informed"
    return "salience_mismatch"


def build_pairs(fresh, auditor, salience, man):
    """Enumerate every within-model stimulus pair and describe it. Selects nothing.

    PRIMARY comparison scale - standardized difference:

      z_true, z_salience, z_auditor
          difference / SD of that measure across the battery (within focal model).
          Scale-free: "how large is this gap relative to the spread the battery
          actually offers?" Comparable across the three measures, so these are what
          the scores combine and what pair_diagnostic is built from.

    RELIABILITY DIAGNOSTICS ONLY - never a matching criterion:

      t_true, t_salience, t_auditor
          difference / SE of the difference, SE recovered approximately from the
          per-stimulus bootstrap percentile intervals (independent samples, so SEs
          add in quadrature). Read these as "is this gap distinguishable from
          zero?", nothing more. Because the SEs are approximate, NO |t| threshold
          is applied anywhere - not 1.96, not any other value.

    Scores, both ranking aids only:

      matching_score        = z_true - W_SALIENCE * |z_salience|
      matching_score_public = z_true - W_SALIENCE * |z_salience| - W_AUDITOR * |z_auditor|

    matching_score_public is the stricter one: auditor_prediction is not a pure
    public baseline (the auditor may hold model-specific knowledge about the focal
    model), so a pair matched on generic_salience but not on auditor_prediction is
    still only partly matched. matching_score cannot see that; matching_score_public
    can.

    NOTHING IS SELECTED HERE. Every row is written with approved=False. Ranking,
    flags and diagnostics exist to SURFACE candidates for a human; Stage C reads
    only the `approved` column. Overlapping pairs are reported, never suppressed -
    pair independence and diversity are decided manually.
    """
    truth = {(r["model"], r["stimulus"]): r for r in fresh}
    aud = {(r["focal_model"], r["stimulus"]): r for r in auditor}
    sal = {r["stimulus"]: r for r in salience if r["rater_model"] == "pooled"}

    cands = []
    for model in ("gpt", "claude"):
        sids = [s for s in P.BATTERY if (model, s) in truth and (model, s) in aud]
        # Battery-relative SDs, computed within focal model, used for the z scale.
        # SAMPLE SPLITTING. Ordering, scoring, ranking and the diagnostic all come
        # from the SELECT half only. The HOLDOUT half is never consulted until after
        # a pair has been surfaced, so its gaps are an independent estimate of the
        # same quantities and shrinkage measures how much of a gap was selection
        # noise. Fall back to the full sample only if a half is missing entirely.
        def gv(row, tag, base):
            v = row.get(f"{base}_{tag}", "")
            return float(v) if v not in ("", None) else float(row[base_full[base]])
        base_full = {"self_match": "self_match_unbiased",
                     "auditor": "auditor_predicted_match", "salience": "salience"}

        sd_true = _sd([gv(truth[(model, s)], "select", "self_match") for s in sids])
        sd_aud = _sd([gv(aud[(model, s)], "select", "auditor") for s in sids])
        sd_sal = _sd([gv(sal[s], "select", "salience") for s in sids if s in sal])

        for i, a in enumerate(sids):
            for b in sids[i + 1:]:
                ta, tb = truth[(model, a)], truth[(model, b)]
                # high/low ordered on the SELECT half - never on the full sample
                hi_s, lo_s = ((a, b) if gv(ta, "select", "self_match")
                              >= gv(tb, "select", "self_match") else (b, a))
                th, tl = truth[(model, hi_s)], truth[(model, lo_s)]
                ah, al = aud[(model, hi_s)], aud[(model, lo_s)]
                have_sal = hi_s in sal and lo_s in sal

                # All differences are HIGH minus LOW on the true-self-match axis, so
                # d_true >= 0 by construction ON THE SELECT HALF (it can and often
                # will go negative on the holdout - that is the point) and the sign
                # of the other two is informative.
                d_true = gv(th, "select", "self_match") - gv(tl, "select", "self_match")
                d_aud = gv(ah, "select", "auditor") - gv(al, "select", "auditor")
                d_sal = (gv(sal[hi_s], "select", "salience")
                         - gv(sal[lo_s], "select", "salience")) if have_sal else float("nan")

                # held-out estimates of the same three gaps
                d_true_ho = gv(th, "holdout", "self_match") - gv(tl, "holdout", "self_match")
                d_aud_ho = gv(ah, "holdout", "auditor") - gv(al, "holdout", "auditor")
                d_sal_ho = (gv(sal[hi_s], "holdout", "salience")
                            - gv(sal[lo_s], "holdout", "salience")) if have_sal else float("nan")
                z_true_ho = d_true_ho / sd_true if sd_true == sd_true and sd_true else float("nan")
                shrink = d_true - d_true_ho          # >0 means the gap shrank out of sample

                z_true = d_true / sd_true if sd_true == sd_true and sd_true else float("nan")
                z_aud = d_aud / sd_aud if sd_aud == sd_aud and sd_aud else float("nan")
                z_sal = d_sal / sd_sal if sd_sal == sd_sal and sd_sal else float("nan")

                se_true = math.hypot(_se(th, "self_match_ci_lo", "self_match_ci_hi"),
                                     _se(tl, "self_match_ci_lo", "self_match_ci_hi"))
                se_aud = math.hypot(_se(ah), _se(al))
                se_sal = (math.hypot(_se(sal[hi_s]), _se(sal[lo_s])) if have_sal
                          else float("nan"))
                t_true = d_true / se_true if se_true else float("nan")
                t_aud = d_aud / se_aud if se_aud else float("nan")
                t_sal = d_sal / se_sal if se_sal else float("nan")

                score = (z_true - W_SALIENCE * abs(z_sal)) if z_sal == z_sal else float("nan")
                score_pub = (score - W_AUDITOR * abs(z_aud)) if score == score and z_aud == z_aud \
                    else float("nan")

                cats = {th["stimulus_category"], tl["stimulus_category"]}
                kind = ("fallback_disparity" if "fallback_disparity" in cats
                        else ("clean_disparity" if "clean_disparity" in cats else "shared_control"))
                rnd = lambda v: (round(v, 4) if v == v else "")
                cands.append(dict(
                    focal_model=model, focal_model_name=P.DISPLAY[model],
                    pair_id=f"{model}__{hi_s}__vs__{lo_s}",
                    stimulus_high=hi_s, stimulus_low=lo_s,
                    # --- raw levels ---
                    true_self_match_high=th["self_match_unbiased"],
                    true_self_match_low=tl["self_match_unbiased"],
                    true_self_match_high_select=th.get("self_match_select", ""),
                    true_self_match_low_select=tl.get("self_match_select", ""),
                    true_self_match_high_holdout=th.get("self_match_holdout", ""),
                    true_self_match_low_holdout=tl.get("self_match_holdout", ""),
                    auditor_prediction_high=ah["auditor_predicted_match"],
                    auditor_prediction_low=al["auditor_predicted_match"],
                    generic_salience_high=(sal[hi_s]["salience"] if have_sal else ""),
                    generic_salience_low=(sal[lo_s]["salience"] if have_sal else ""),
                    # --- raw differences (high minus low) ---
                    delta_true=rnd(d_true),
                    delta_auditor=rnd(d_aud),
                    delta_salience=rnd(d_sal),
                    abs_delta_true=rnd(abs(d_true)),
                    abs_delta_auditor=rnd(abs(d_aud)),
                    abs_delta_salience=rnd(abs(d_sal)),
                    # --- PRIMARY: standardized, battery-relative effect size ---
                    z_true=rnd(z_true), z_salience=rnd(z_sal), z_auditor=rnd(z_aud),
                    # --- reliability diagnostics only, never a matching criterion ---
                    t_true=rnd(t_true), t_salience=rnd(t_sal), t_auditor=rnd(t_aud),
                    se_delta_true=rnd(se_true), se_delta_salience=rnd(se_sal),
                    se_delta_auditor=rnd(se_aud),
                    # --- scores (ranking aids, NOT selection rules) ---
                    matching_score=rnd(score),
                    matching_score_public=rnd(score_pub),
                    pair_diagnostic=diagnose(z_true, z_sal, z_aud),
                    # --- HELD-OUT: independent estimates of the same gaps ---
                    delta_true_holdout=rnd(d_true_ho),
                    delta_auditor_holdout=rnd(d_aud_ho),
                    delta_salience_holdout=rnd(d_sal_ho),
                    z_true_holdout=rnd(z_true_ho),
                    delta_true_shrinkage=rnd(shrink),
                    holdout_sign_agrees=(d_true_ho > 0) if d_true_ho == d_true_ho else "",
                    holdout_retained_frac=(rnd(d_true_ho / d_true)
                                           if d_true and d_true_ho == d_true_ho else ""),
                    rank_in_model="",
                    stimulus_high_use_count="", stimulus_low_use_count="",
                    # --- context for the human deciding ---
                    form_consistency_high=th["form_consistency"],
                    form_consistency_low=tl["form_consistency"],
                    fallback_high=th["fallback"], fallback_low=tl["fallback"],
                    category_high=th["stimulus_category"], category_low=tl["stimulus_category"],
                    pair_kind=kind,
                    either_fallback=(str(th["fallback"]) == "True"
                                     or str(tl["fallback"]) == "True"),
                    well_matched_auditor=(abs(d_aud) <= AUD_TOL),
                    usefully_separated=(d_true >= TRUE_MIN),
                    meets_criteria=(abs(d_aud) <= AUD_TOL and d_true >= TRUE_MIN),
                    approved=False,          # <- the ONLY field Stage C reads
                ))

    # Rank by matching_score within focal model. Ranking is NOT selection: every
    # candidate is written out and every row leaves here with approved=False.
    for model in ("gpt", "claude"):
        pool = [c for c in cands if c["focal_model"] == model]
        pool.sort(key=lambda c: -(c["matching_score"] if c["matching_score"] != "" else -9e9))
        for i, c in enumerate(pool, 1):
            c["rank_in_model"] = i
        # How often does each stimulus appear among this model's top-N candidates?
        # Reported so a human can see rank-list domination; never auto-suppressed.
        top = pool[:TOP_N_SHOWN]
        use = Counter()
        for c in top:
            use[c["stimulus_high"]] += 1
            use[c["stimulus_low"]] += 1
        for c in pool:
            c["stimulus_high_use_count"] = use.get(c["stimulus_high"], 0)
            c["stimulus_low_use_count"] = use.get(c["stimulus_low"], 0)
    cands.sort(key=lambda c: (c["focal_model"],
                              c["rank_in_model"] if c["rank_in_model"] != "" else 9999))
    return cands


def top_use_counts(pairs, model):
    """Counter of stimulus occurrences among this model's top-N candidate pairs."""
    top = [p for p in pairs if p["focal_model"] == model][:TOP_N_SHOWN]
    use = Counter()
    for p in top:
        use[p["stimulus_high"]] += 1
        use[p["stimulus_low"]] += 1
    return use


def payoff_recommendation(pairs):
    """Payoff guidance for a given set of pairs.

    Called on APPROVED pairs when any exist; otherwise on the top-ranked candidates
    as an indicative preview, clearly labelled as such. Re-run this script after
    approving pairs to get the figure that actually applies.
    """
    if not pairs:
        return None
    vals = ([float(p["true_self_match_high"]) for p in pairs]
            + [float(p["true_self_match_low"]) for p in pairs])
    lo, hi = min(vals), max(vals)
    default = P.SAFE_VALUES_DEFAULT
    inside = [s for s in default if lo * 10 <= s <= hi * 10]
    lo_pt, hi_pt = lo * 10, hi * 10
    span = [round(x, 1) for x in
            (lo_pt + (hi_pt - lo_pt) * f for f in (0.1, 0.37, 0.63, 0.9))]
    return dict(true_range=(round(lo, 3), round(hi, 3)),
                ev_neutral_payoffs=(round(lo_pt, 2), round(hi_pt, 2)),
                default_inside=inside, suggested=span)


def write(path, rows):
    """Write rows, taking fieldnames from the UNION of all rows' keys.

    Rows in one table are not always homogeneous - the pooled salience rows carry
    between-rater and split columns the per-rater rows do not - so keying off
    rows[0] alone raises on the first heterogeneous row.
    """
    if not rows:
        print(f"  (no rows for {os.path.basename(path)})"); return
    fields = list(rows[0])
    for r in rows:
        for k in r:
            if k not in fields:
                fields.append(k)
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, restval="")
        w.writeheader(); w.writerows(rows)
    print(f"  -> {path}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage-a", default=None)
    ap.add_argument("--auditor", default=None)
    ap.add_argument("--salience", default=None)
    args = ap.parse_args()

    a = args.stage_a or newest("stageA_*.csv")
    au = args.auditor or newest("stageB_auditor_*.csv")
    sa = args.salience or newest("stageB_salience_*.csv")
    for label, f in (("Stage A", a), ("Stage B auditor", au), ("Stage B salience", sa)):
        if not f:
            sys.exit(f"missing {label} raw CSV - run that stage first")
    man = {r["stimulus_id"]: r for r in P.load_manifest()}

    print("=== analysis inputs ===")
    for label, f in (("Stage A", a), ("auditor", au), ("salience", sa)):
        print(f"  {label:9} {os.path.basename(f)}")

    fresh = analyze_stage_a(a, man)
    auditor = analyze_auditor(au)
    salience = analyze_salience(sa)
    pairs = build_pairs(fresh, auditor, salience, man)

    print("\n=== outputs ===")
    write(os.path.join(P.DATA, "fresh_self_match.csv"), fresh)
    write(os.path.join(P.DATA, "auditor_predictions.csv"), auditor)
    write(os.path.join(P.DATA, "salience_ratings.csv"), salience)

    # Carry existing approvals forward. Without this, re-running the analysis after
    # approving pairs would silently reset every approved=True back to False (and
    # the "payoff guidance from APPROVED pairs" branch below could never fire).
    pairs_path = os.path.join(P.EXP, "matched_pairs.csv")
    carried = 0
    if os.path.exists(pairs_path):
        prev = {r["pair_id"]: r for r in csv.DictReader(open(pairs_path))}
        for p in pairs:
            old = prev.get(p["pair_id"])
            if old and str(old.get("approved", "")).lower() in ("true", "1", "yes"):
                p["approved"] = True
                carried += 1
        stale = [pid for pid, r in prev.items()
                 if str(r.get("approved", "")).lower() in ("true", "1", "yes")
                 and pid not in {p["pair_id"] for p in pairs}]
        if stale:
            print(f"\n  !! {len(stale)} previously-approved pair(s) no longer exist as "
                  f"candidates and were dropped:")
            for pid in stale:
                print(f"       {pid}")
    write(pairs_path, pairs)
    if carried:
        print(f"  ({carried} existing approval(s) carried forward)")

    print("\n=== fresh self-match vs the confirmed (old-model) battery ===")
    print(f"{'stimulus':16}{'model':8}{'new':>7}{'old':>7}{'delta':>8}{'FC':>6}  flag")
    for r in sorted(fresh, key=lambda r: (r["stimulus"], r["model"])):
        flag = "FALLBACK" if r["fallback"] is True else ""
        # expansion-battery stimuli have no old-model value; print a dash, not a crash
        _pm = str(r["prior_match_old_model"]).strip()
        _dv = str(r["delta_vs_old"]).strip()
        _old = f"{float(_pm):7.3f}" if _pm not in ("", "nan") else f"{'-':>7}"
        _del = f"{float(_dv):+8.3f}" if _dv not in ("", "nan") else f"{'-':>8}"
        print(f"{r['stimulus']:16}{r['model']:8}{r['self_match_unbiased']:7.3f}"
              f"{_old}{_del}{r['form_consistency']:6.2f}  {flag}")

    print("\n" + "=" * 78)
    print("CANDIDATE PAIRS - ranked for review. NOTHING IS SELECTED; approved=False on all.")
    print("=" * 78)
    print("\n  DESCRIPTIVE HEURISTICS IN FORCE (not inferential criteria, no test is run):")
    print(f"    LARGE_TRUE_Z   = {LARGE_TRUE_Z:.2f}   |z_true| at or above this = large true gap")
    print(f"    SMALL_PUBLIC_Z = {SMALL_PUBLIC_Z:.2f}   |z_public| at or below this = small public gap")
    print(f"    AUD_TOL        = {AUD_TOL:.2f}   raw-scale advisory flag on |d_auditor|")
    print(f"    TRUE_MIN       = {TRUE_MIN:.2f}   raw-scale advisory flag on  d_true")
    print("\n  SCALES:")
    print("    z_* = difference / battery SD    PRIMARY comparison scale")
    print("    t_* = difference / SE            reliability diagnostic ONLY - the SEs are")
    print("          recovered approximately from bootstrap intervals, so no |t| cutoff")
    print("          (1.96 or otherwise) is used anywhere to decide whether a pair matches")
    print("\n  THE TWO PUBLIC CONTROLS ARE DIFFERENT THINGS:")
    print("    generic_salience    how focal the stimulus looks from public structure alone")
    print("    auditor_prediction  an external MODEL's prediction of the focal model's")
    print("                        self-coordination reliability - NOT a pure public")
    print("                        baseline, since the auditor may hold model-specific")
    print("                        knowledge about GPT or Claude")
    print("    The strongest pair differs substantially in true self-match while differing")
    print("    little in BOTH public measures.")
    print("\n  score  = z_true - |z_salience|                 ranking aid only")
    print("  score+ = z_true - |z_salience| - |z_auditor|   stricter ranking aid only")

    for model in ("gpt", "claude"):
        pool = [p for p in pairs if p["focal_model"] == model]
        if not pool:
            continue
        n_ok = sum(1 for p in pool if p["meets_criteria"])
        diag = Counter(p["pair_diagnostic"] for p in pool)
        print(f"\n  {'-' * 74}")
        print(f"  {P.DISPLAY[model]} - {len(pool)} candidate pairs "
              f"({n_ok} meet both raw advisory flags)")
        print(f"  all candidates by diagnostic: "
              + "  ".join(f"{k}={v}" for k, v in sorted(diag.items())))
        print(f"  top {min(TOP_N_SHOWN, len(pool))} by matching_score:")
        hdr = (f"    {'#':>2} {'high stimulus':15}{'low stimulus':15}"
               f"{'d_tru':>6}{'d_sal':>6}{'d_aud':>6} "
               f"{'z_tru':>6}{'z_sal':>6}{'z_aud':>6} "
               f"{'t_tru':>6}{'t_sal':>6}{'t_aud':>6} "
               f"{'score':>7}{'score+':>7} || {'HOd_tru':>8}{'HOd_sal':>8}{'HOd_aud':>8}"
               f"{'shrink':>8}{'keep':>7}  {'diagnostic':18}{'kind':19}{'fb':>3} {'appr':>5}")
        print(hdr)
        print("    " + "-" * (len(hdr) - 4))
        for p in pool[:TOP_N_SHOWN]:
            g = lambda k: (f"{float(p[k]):+.2f}" if p[k] not in ("", None) else "    .")
            keep = (f"{float(p['holdout_retained_frac']):+.0%}"
                    if p["holdout_retained_frac"] not in ("", None) else "     .")
            print(f"    {p['rank_in_model']:>2} {p['stimulus_high'][:14]:15}{p['stimulus_low'][:14]:15}"
                  f"{g('delta_true'):>6}{g('delta_salience'):>6}{g('delta_auditor'):>6} "
                  f"{g('z_true'):>6}{g('z_salience'):>6}{g('z_auditor'):>6} "
                  f"{g('t_true'):>6}{g('t_salience'):>6}{g('t_auditor'):>6} "
                  f"{g('matching_score'):>7}{g('matching_score_public'):>7} || "
                  f"{g('delta_true_holdout'):>8}{g('delta_salience_holdout'):>8}"
                  f"{g('delta_auditor_holdout'):>8}{g('delta_true_shrinkage'):>8}{keep:>7}  "
                  f"{p['pair_diagnostic']:18}{p['pair_kind']:19}"
                  f"{('Y' if p['either_fallback'] else '-'):>3} "
                  f"{str(p['approved']):>5}")

        # Does the separation survive out of sample?
        top = [q for q in pool[:TOP_N_SHOWN] if q["holdout_retained_frac"] not in ("", None)]
        if top:
            kept = [float(q["holdout_retained_frac"]) for q in top]
            agree = sum(1 for q in top if q["holdout_sign_agrees"] is True)
            med = sorted(kept)[len(kept) // 2]
            print(f"\n    HELD-OUT SURVIVAL (top {len(top)}): {agree}/{len(top)} keep the sign of"
                  f" d_true; median retained {med:+.0%} of the select-half gap")
            if agree < len(top) * 0.6 or med < 0.4:
                print("    !! THE SEPARATION LARGELY DOES NOT SURVIVE OUT OF SAMPLE.")
                print("       These gaps were substantially selection noise. Betting a Stage C")
                print("       result on them is not warranted - the honest read is that the")
                print("       battery lacks cleanly separated pairs and needs more targeted")
                print("       stimuli before Stage C is worth running.")

        use = top_use_counts(pairs, model)
        over = [(s, c) for s, c in use.most_common() if c > REPEAT_WARN]
        if over:
            print(f"\n    !! REPEATED-STIMULUS WARNING - in the top {TOP_N_SHOWN}:")
            for s, c in over:
                print(f"       '{s}' appears in {c} of the top {TOP_N_SHOWN} pairs")
            print("       The ranking is being dominated by this stimulus. Pairs are NOT")
            print("       de-duplicated automatically - decide pair independence yourself.")
        if not n_ok:
            print("\n    !! no candidate meets both raw advisory flags. Do not force a pair -")
            print("       report it, loosen a threshold deliberately, or extend the battery.")

    print("\n  DIAGNOSTIC LEGEND")
    print("    ideal              large true self-coordination difference with little")
    print("                       difference in either public measure.")
    print("    auditor_informed   generic visual salience is matched, but an external model")
    print("                       can partly anticipate the focal model's reliability")
    print("                       difference.")
    print("    salience_mismatch  the stimuli themselves differ visibly in apparent")
    print("                       coordinability, so the pair does not cleanly isolate")
    print("                       policy-specific knowledge.")
    print("    non_diagnostic     true and public differences move together too strongly to")
    print("                       separate self-policy knowledge from generic coordination")
    print("                       difficulty - here, the true gap is below LARGE_TRUE_Z, so")
    print("                       there is too little self-coordination difference to test.")
    print("    incomplete         a measure was missing for one of the two stimuli.")
    print("\n  What the ranking CANNOT see:")
    print("   - it is blind to pair_kind; the clean vs fallback distinction must not be")
    print("     collapsed, so check the kind and fb columns before accepting a pair;")
    print("   - it does not de-duplicate: one stimulus can dominate the top of the list;")
    print("   - a high score with a small |t_true| is a large gap that is not yet reliable.")
    print("\n  SAMPLE SPLITTING: every score, rank, z and diagnostic above is computed on")
    print("  the SELECT half only (AB/BA-balanced, deterministic). The HO* columns are the")
    print("  same gaps re-estimated on the untouched HELD-OUT half; 'shrink' is select minus")
    print("  holdout and 'keep' is the fraction of the select gap that survived. d_true >= 0")
    print("  holds by construction on the select half ONLY - a negative HOd_tru means the")
    print("  ordering itself was noise. Judge pairs on the held-out columns, not the score.")

    approved = [p for p in pairs if str(p.get("approved")).lower() == "true"]
    basis = approved or [p for p in pairs if p["meets_criteria"]][:TOP_N_SHOWN]
    rec = payoff_recommendation(basis)
    if rec:
        print("\n  (payoff guidance below is based on "
              + ("the APPROVED pairs)" if approved
                 else "top-ranked CANDIDATES - indicative only; re-run after approval)"))
    if rec:
        print("\n=== payoff grid ===")
        print(f"  selected stimuli span true self-match {rec['true_range'][0]}-{rec['true_range'][1]}")
        print(f"  EV-neutral safe payoffs for that span: "
              f"{rec['ev_neutral_payoffs'][0]}-{rec['ev_neutral_payoffs'][1]} points")
        print(f"  default grid {P.SAFE_VALUES_DEFAULT}: {len(rec['default_inside'])} of 4 "
              f"values fall inside the span {rec['default_inside']}")
        if len(rec["default_inside"]) >= 3:
            print("  -> default grid brackets the range adequately; no change proposed.")
        else:
            print(f"  -> default grid brackets this range POORLY. Proposed alternative: "
                  f"{rec['suggested']}")
            print("     Rationale: safe payoffs are informative where they straddle the")
            print("     EV-neutral point 10*p for the stimuli actually being bet on; a grid")
            print("     entirely above or below that span yields near-0 or near-1 attempt")
            print("     rates everywhere and cannot discriminate between the paired stimuli.")
            print("     This change requires approval before Stage C (spec §7).")

    print("\nSTOP. Stage C must not run until the matched-pair table is reviewed and")
    print(f"rows are marked approved=True in {os.path.join(P.EXP, 'matched_pairs.csv')}.")


if __name__ == "__main__":
    main()
