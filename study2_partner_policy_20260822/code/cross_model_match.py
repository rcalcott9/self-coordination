"""
CROSS-MODEL coordination on the Study-1 battery, and what it does to Study 2.

WHY THIS EXISTS
---------------
Study 1 matched its HIGH/LOW stimulus pairs on PUBLIC measures only: generic
salience (how focal the stimulus looks to a generic player) and an external
auditor model's prediction of the focal model's self-coordination. It never
matched them on the quantity that actually pays out in Study 2's DIFFERENT-model
partner arm: the true CROSS-model coordination rate

    cross(s) = P( a GPT-5.5 trial and a Claude-Opus-5 trial on stimulus s
                  select the SAME IDENTITY )

Study 2 is a 2x2, Stimulus {HIGH own-copy, LOW own-copy} x Partner {SAME model,
DIFFERENT model}, and its critical test is the Stimulus x Partner interaction.
That interaction is only identifiable if the HIGH/LOW contrast moves own-copy
match WITHOUT moving cross-model match. If a pair's HIGH stimulus is also the
high-cross stimulus, then a same-model partner and a different-model partner both
face a better-coordinating stimulus, the interaction is attenuated toward zero by
construction, and a null result cannot be read as evidence about policy-specific
self-knowledge. This script measures cross(s), audits Study 1's five approved
pairs against it, and re-derives Study 2 candidates that separate own-copy match
while holding cross-model match matched.

WHAT IS INFERENTIAL AND WHAT IS DESCRIPTIVE
-------------------------------------------
INFERENTIAL (estimates with uncertainty, reported as such):
    own-copy match per (model, stimulus), with bootstrap percentile CI
    cross-model match per stimulus, with bootstrap percentile CI
    the select/holdout split of both
Nothing here performs a hypothesis test, and no p-value is computed anywhere.

DESCRIPTIVE HEURISTIC (thresholds for SURFACING candidates to a human; every one
is a module constant, all are printed at run time, none is an inferential
criterion, and none selects anything):
    OWN_SEP_MIN, CROSS_TOL, AUD_TOL      raw-probability tolerances
    LARGE_OWN_Z, SMALL_NUISANCE_Z        battery-standardized tolerances
    W_CROSS, W_SALIENCE, W_AUDITOR       ranking-score weights

Every candidate pair is written out with approved=False. A human approves pairs;
this script never does.

THE TWO ESTIMATORS
------------------
OWN-COPY (frozen, imported, not reimplemented). targeted_common.unbiased_match:

    own(m,s) = sum_k n_k (n_k - 1) / [ N (N - 1) ]

  BIAS-CORRECTED. Both draws come from the SAME finite sample of trials, so the
  plug-in sum_k p_k^2 counts each trial as agreeing with itself and is inflated by
  roughly 1/N. Removing the same-draw pairs (the n_k - 1 and N - 1) gives the
  unbiased probability that two INDEPENDENT draws from that cell agree.

CROSS-MODEL (new, defined below). This script's cross_match:

    cross(s) = sum_k p_k^gpt * p_k^claude ,   p_k^m = n_k^m / N^m

  PLUG-IN, AND DELIBERATELY SO -- it is already unbiased. The two draws come from
  two DISJOINT samples (a GPT trial and a Claude trial), so there is no same-draw
  pair to remove. By independence of the two cells,
      E[ p_k^gpt * p_k^claude ] = E[p_k^gpt] E[p_k^claude] = q_k^gpt q_k^claude,
  so the plug-in product estimator is exactly unbiased for the estimand. Applying
  unbiased_match's (n-1) correction here would over-correct and bias cross(s)
  DOWNWARD. This asymmetry -- correction for own-copy, none for cross-model -- is
  the whole reason the two estimators are written differently, and it is why the
  frozen unbiased_match is imported for own-copy but not reused for cross.

  Note this is a MARGINAL, not a trial-level, agreement rate: it is the payoff
  probability for one GPT instance and one Claude instance drawn independently,
  which is exactly the DIFFERENT-model partner arm's payoff. It is not a paired
  statistic over matched trials, because no trial-level pairing exists.

VALIDITY FILTERS AND AB/BA BALANCE
----------------------------------
Both estimators consume the SAME rows: psc_common.load_analysis_rows keeps only
included_in_analysis==True, which is the deduplicated valid_response==True trial
for each run_id (the runner writes the unparseable first attempt and its retry
under one run_id; the valid one survives, and a run whose retry also failed
contributes nothing rather than being silently patched).

AB/BA. The estimand is the layout-marginal agreement rate, i.e. agreement when
each player independently gets a randomized layout. Pooling AB and BA trials
delivers that exactly when n_AB == n_BA, which is how Stage A was run (30/30 per
cell) and what analyze_stage_ab.assign_halves preserves inside each half. This
script therefore pools -- identically to the frozen own-copy estimator -- and
ASSERTS the balance at run time rather than assuming it, printing any cell whose
AB/BA counts differ. A variant-balanced estimator (average the two per-variant
cross rates with weight 1/2) is also computed and reported as a diagnostic column
so a reader can see that the two agree under the balanced design.

BOOTSTRAP
---------
Percentile CI, B and seed convention inherited from targeted_common (BOOT_B,
f"{BOOT_SEED}|...|{stimulus}"). Own-copy resamples that cell's identity labels.
Cross-model resamples the GPT cell and the Claude cell INDEPENDENTLY, with
replacement, and recomputes the product estimator -- which propagates both cells'
sampling error and reproduces the independence structure of the estimand.

SAMPLE SPLITTING
----------------
analyze_stage_ab.assign_halves is imported and used unchanged: deterministic,
AB/BA-balanced 50/50 split within every (model, stimulus) cell, ordered by run_id.
The SELECT half orders high/low, drives every threshold, the score and the rank.
The HOLDOUT half is consulted only after a pair has been surfaced, and supplies an
independent estimate of the same gaps. This is Study 1's winner's-curse control,
carried over unchanged; without it the |d_own| large / |d_cross| small search over
105 pairs per model would report gaps inflated by the noise that selected them.

Run:  python3 cross_model_match.py           (no arguments; paths resolve from
                                              this file's own location)
Writes: ../pairs/cross_model_table.csv
        ../pairs/study2_candidate_pairs.csv
"""
import csv, glob, math, os, statistics, sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "pairs")
STUDY1 = os.path.normpath(os.path.join(
    os.path.dirname(os.path.dirname(HERE)),
    "policy_specific_self_coordination_20260812_1401"))
STUDY1_CODE = os.path.join(STUDY1, "code")
if STUDY1_CODE not in sys.path:
    sys.path.insert(0, STUDY1_CODE)

import psc_common as P                     # battery, loaders, display names
import targeted_common as tc               # frozen own-copy estimator + bootstrap
from analyze_stage_ab import assign_halves  # frozen select/holdout discipline

# ============================ DESCRIPTIVE HEURISTICS ==========================
# Raw-probability tolerances. OWN_SEP_MIN and AUD_TOL are Study 1's own constants
# (analyze_stage_ab.TRUE_MIN and .AUD_TOL) reused verbatim so eligibility on the
# inherited axes is unchanged. CROSS_TOL is new and is set to AUD_TOL, i.e. the
# cross-model rate is held to the same "matched" bar the auditor prediction was.
OWN_SEP_MIN = 0.20     # |d_own|   at or above this = usefully separated
CROSS_TOL = 0.10       # |d_cross| at or below this = matched on cross-model
AUD_TOL = 0.10         # |d_aud|   at or below this = matched on the auditor
SAL_TOL = 0.10         # |d_sal|   at or below this = matched on generic salience

# TWO ELIGIBILITY TIERS, because Study 1's own gate and Study 1's own labelling
# disagreed and both are worth carrying forward honestly:
#   eligible_study1_parity  = Study 1's literal meets_criteria (|d_aud| <= AUD_TOL
#                             and d_own >= OWN_SEP_MIN) PLUS the new |d_cross| <=
#                             CROSS_TOL. Salience entered Study 1 only through the
#                             z-scale diagnostic and the score, not through the
#                             gate -- two of its five approved pairs were labelled
#                             salience_mismatch and approved anyway.
#   eligible_strict         = the above AND |d_sal| <= SAL_TOL.
# The strict tier is the one to prefer; the parity tier exists so that "how many
# pairs would Study 1's own bar have admitted once cross-model is added?" has an
# answer that is not confounded with a newly tightened salience rule.

# Battery-standardized tolerances (difference / battery SD of that measure, within
# focal model). Study 1's LARGE_TRUE_Z / SMALL_PUBLIC_Z, renamed for the nuisance
# set that now includes cross-model match.
LARGE_OWN_Z = 0.75
SMALL_NUISANCE_Z = 0.35

# Ranking-score weights. 1.0 puts a one-SD nuisance mismatch on equal footing with
# a one-SD gain in own-copy separation. W_CROSS is deliberately the largest: for
# Study 2, cross-model contamination is not a nuisance among others, it is the
# thing that makes the interaction unidentifiable.
W_CROSS = 2.0
W_SALIENCE = 1.0
W_AUDITOR = 1.0

TOP_N_SHOWN = 10       # printed per focal model; ALL candidates go to the CSV

# Study 1's five approved pairs (focal, HIGH own-copy stimulus, LOW own-copy
# stimulus), as frozen in reasoning_traces/trace_analysis.py CANON. Audited, not
# recomputed.
CANON = [("gpt", "c_contr_subtle", "b_spiral_cw"),
         ("gpt", "s_convexity", "d_dens_extreme"),
         ("gpt", "c_open_cplx", "s_density"),
         ("claude", "b_spiral_cw", "rot"),
         ("claude", "s_convexity", "d_dens_extreme")]

MODELS = ("gpt", "claude")


# ------------------------------------------------------------- estimators ----
def cross_match(counts_a, counts_b):
    """Plug-in cross-model match: sum_k p_k^A * p_k^B. Already unbiased -- see the
    module docstring. counts_* are Counters of choice IDENTITY for the two models'
    trials on one stimulus. Returns NaN if either cell is empty."""
    na, nb = sum(counts_a.values()), sum(counts_b.values())
    if not na or not nb:
        return float("nan")
    keys = set(counts_a) | set(counts_b)
    return sum((counts_a.get(k, 0) / na) * (counts_b.get(k, 0) / nb) for k in keys)


def cross_boot_ci(idents_a, idents_b, seed, b=tc.BOOT_B):
    """Bootstrap percentile CI for cross_match: resample the two cells
    INDEPENDENTLY with replacement, recompute, take the 2.5/97.5 percentiles.
    Same B and same percentile convention as targeted_common.boot_draws/pct_ci."""
    import random
    if len(idents_a) < 2 or len(idents_b) < 2:
        return float("nan"), float("nan")
    rng = random.Random(seed)
    na, nb = len(idents_a), len(idents_b)
    draws = [cross_match(Counter(rng.choices(idents_a, k=na)),
                         Counter(rng.choices(idents_b, k=nb))) for _ in range(b)]
    return tc.pct_ci(draws)


def cross_match_variant_balanced(rows_a, rows_b):
    """Diagnostic only. Average the AB-cross and BA-cross rates with weight 1/2
    instead of pooling. Equals the pooled estimator when n_AB == n_BA in both
    cells, which the design guarantees; reported so that equality is visible."""
    vals = []
    for v in ("AB", "BA"):
        ca = Counter(r["parsed_choice_identity"] for r in rows_a if r["variant"] == v)
        cb = Counter(r["parsed_choice_identity"] for r in rows_b if r["variant"] == v)
        x = cross_match(ca, cb)
        if x == x:
            vals.append(x)
    return statistics.fmean(vals) if vals else float("nan")


def own_match_ci(idents, seed):
    """Frozen own-copy estimator + its frozen bootstrap, for reproduction checks."""
    if len(idents) < 2:
        return float("nan"), float("nan"), float("nan")
    v = tc.unbiased_match(Counter(idents))
    lo, hi = tc.pct_ci(tc.boot_draws(idents, seed=seed, b=tc.BOOT_B))
    return v, lo, hi


# ------------------------------------------------------------------ utils ----
def newest(pattern):
    files = [f for f in glob.glob(os.path.join(STUDY1, "data", pattern))
             if "_DRY" not in f]
    return max(files, key=os.path.getmtime) if files else None


def _sd(vals):
    vals = [v for v in vals if v == v]
    return statistics.pstdev(vals) if len(vals) > 1 else float("nan")


def rnd(v, k=4):
    return round(v, k) if isinstance(v, float) and v == v else ("" if v != v else v)


def fnum(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return float("nan")


def write_csv(path, rows):
    if not rows:
        return
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


# --------------------------------------------------------------- build it ----
def build_table(stage_a_path, sal, aud):
    """Per-stimulus own-copy (both models) + cross-model match, full/select/holdout."""
    rows = P.load_analysis_rows(stage_a_path)
    rows = [r for r in rows if r["stage"] == "A" and r["parsed_choice_identity"]]
    assign_halves(rows, lambda r: (r["actor_model"], r["stimulus"]))

    cell = defaultdict(list)                      # (model, stimulus) -> rows
    for r in rows:
        cell[(r["actor_model"], r["stimulus"])].append(r)

    # AB/BA balance audit -- asserted, not assumed (see docstring).
    imbalanced = []
    for (m, s), rs in sorted(cell.items()):
        for tag, sub in (("full", rs),
                         ("select", [x for x in rs if x["_half"] == "select"]),
                         ("holdout", [x for x in rs if x["_half"] == "holdout"])):
            nab = sum(x["variant"] == "AB" for x in sub)
            nba = sum(x["variant"] == "BA" for x in sub)
            if nab != nba:
                imbalanced.append((m, s, tag, nab, nba))

    sids = [s for s in P.BATTERY if ("gpt", s) in cell and ("claude", s) in cell]

    def idents(m, s, tag):
        rs = cell[(m, s)]
        if tag != "full":
            rs = [r for r in rs if r["_half"] == tag]
        return [r["parsed_choice_identity"] for r in rs]

    def subrows(m, s, tag):
        rs = cell[(m, s)]
        return rs if tag == "full" else [r for r in rs if r["_half"] == tag]

    out = []
    for s in sids:
        row = dict(stimulus=s)
        for m in MODELS:
            for tag, suf in (("full", ""), ("select", "_select"), ("holdout", "_holdout")):
                ids = idents(m, s, tag)
                v, lo, hi = own_match_ci(
                    ids, seed=(f"{tc.BOOT_SEED}|{m}|{s}" if tag == "full"
                               else f"{tc.BOOT_SEED}|{tag}|{m}|{s}"))
                row[f"own_{m}{suf}"] = rnd(v)
                if tag == "full":
                    row[f"own_{m}_ci_lo"] = rnd(lo)
                    row[f"own_{m}_ci_hi"] = rnd(hi)
                    row[f"n_{m}"] = len(ids)
                    c = Counter(ids)
                    row[f"modal_{m}"] = max(c, key=lambda k: (c[k], k)) if c else ""
                    row[f"modal_share_{m}"] = rnd(c[row[f"modal_{m}"]] / len(ids)) if ids else ""
        for tag, suf in (("full", ""), ("select", "_select"), ("holdout", "_holdout")):
            ga, ca = idents("gpt", s, tag), idents("claude", s, tag)
            x = cross_match(Counter(ga), Counter(ca))
            row[f"cross{suf}"] = rnd(x)
            if tag == "full":
                lo, hi = cross_boot_ci(ga, ca, seed=f"{tc.BOOT_SEED}|cross|{s}")
                row["cross_ci_lo"], row["cross_ci_hi"] = rnd(lo), rnd(hi)
                row["cross_variant_balanced"] = rnd(cross_match_variant_balanced(
                    subrows("gpt", s, "full"), subrows("claude", s, "full")))
                row["same_modal_identity"] = (row["modal_gpt"] == row["modal_claude"])
        # public measures, carried over from Stage B unchanged
        row["generic_salience"] = sal.get(s, {}).get("salience", "")
        row["generic_salience_select"] = sal.get(s, {}).get("salience_select", "")
        row["generic_salience_holdout"] = sal.get(s, {}).get("salience_holdout", "")
        for m in MODELS:
            a = aud.get((m, s), {})
            row[f"auditor_pred_{m}"] = a.get("auditor_predicted_match", "")
            row[f"auditor_pred_{m}_select"] = a.get("auditor_select", "")
            row[f"auditor_pred_{m}_holdout"] = a.get("auditor_holdout", "")
        out.append(row)
    return out, imbalanced, sids


def selfcheck(table, path):
    """Reproduce fresh_self_match.csv's own-copy column from this script's rows."""
    ref = {(r["model"], r["stimulus"]): r for r in csv.DictReader(open(path))}
    tab = {r["stimulus"]: r for r in table}
    checks = []
    for (m, s), r in sorted(ref.items()):
        if s not in tab:
            continue
        got = fnum(tab[s][f"own_{m}"])
        want = fnum(r["self_match_unbiased"])
        checks.append((m, s, want, got, abs(want - got) < 1e-9))
    return checks


# ------------------------------------------------------------------ pairs ----
def build_pairs(table, sids):
    """Enumerate every within-model stimulus pair. Selects nothing.

    high/low is ordered on own-copy match, on the SELECT half. All differences are
    HIGH minus LOW, so d_own >= 0 by construction on the select half (and may go
    negative on the holdout -- that is the point of the split).

    Eligibility (descriptive, on the SELECT half only):
        |d_own|   >= OWN_SEP_MIN   the pair moves own-copy match at all
        |d_cross| <= CROSS_TOL     it does NOT move cross-model match
        |d_aud|   <= AUD_TOL       Study 1's auditor matching, unchanged
        |d_sal|   <= SAL_TOL       Study 1's salience matching, unchanged

    Score (a ranking aid, not a selection rule):
        z_own - W_CROSS*|z_cross| - W_SALIENCE*|z_sal| - W_AUDITOR*|z_aud|
    """
    tab = {r["stimulus"]: r for r in table}
    cands = []
    for model in MODELS:
        sd_own = _sd([fnum(tab[s][f"own_{model}_select"]) for s in sids])
        sd_cross = _sd([fnum(tab[s]["cross_select"]) for s in sids])
        sd_sal = _sd([fnum(tab[s]["generic_salience_select"]) for s in sids])
        sd_aud = _sd([fnum(tab[s][f"auditor_pred_{model}_select"]) for s in sids])

        for i, a in enumerate(sids):
            for b in sids[i + 1:]:
                hi, lo = ((a, b) if fnum(tab[a][f"own_{model}_select"])
                          >= fnum(tab[b][f"own_{model}_select"]) else (b, a))
                H, L = tab[hi], tab[lo]

                def d(col, tag):
                    return fnum(H[f"{col}{tag}"]) - fnum(L[f"{col}{tag}"])

                d_own = d(f"own_{model}", "_select")
                d_cross = d("cross", "_select")
                d_sal = d("generic_salience", "_select")
                d_aud = d(f"auditor_pred_{model}", "_select")

                d_own_h = d(f"own_{model}", "_holdout")
                d_cross_h = d("cross", "_holdout")
                d_sal_h = d("generic_salience", "_holdout")
                d_aud_h = d(f"auditor_pred_{model}", "_holdout")

                z = lambda v, sd: (v / sd) if (sd == sd and sd) else float("nan")
                z_own, z_cross = z(d_own, sd_own), z(d_cross, sd_cross)
                z_sal, z_aud = z(d_sal, sd_sal), z(d_aud, sd_aud)

                score = float("nan")
                if all(v == v for v in (z_own, z_cross, z_sal, z_aud)):
                    score = (z_own - W_CROSS * abs(z_cross)
                             - W_SALIENCE * abs(z_sal) - W_AUDITOR * abs(z_aud))

                ok_own = abs(d_own) >= OWN_SEP_MIN
                ok_cross = abs(d_cross) <= CROSS_TOL
                ok_aud = abs(d_aud) <= AUD_TOL
                ok_sal = abs(d_sal) <= SAL_TOL
                elig_parity = ok_own and ok_cross and ok_aud
                eligible = elig_parity and ok_sal

                cands.append(dict(
                    focal_model=model, focal_model_name=P.DISPLAY[model],
                    pair_id=f"{model}__{hi}__vs__{lo}",
                    stimulus_high=hi, stimulus_low=lo,
                    # --- levels, full sample (for reading; NOT used to select) ---
                    own_high=H[f"own_{model}"], own_low=L[f"own_{model}"],
                    cross_high=H["cross"], cross_low=L["cross"],
                    salience_high=H["generic_salience"], salience_low=L["generic_salience"],
                    auditor_high=H[f"auditor_pred_{model}"],
                    auditor_low=L[f"auditor_pred_{model}"],
                    # --- SELECT half: everything below drives eligibility & rank ---
                    d_own_select=rnd(d_own), d_cross_select=rnd(d_cross),
                    d_salience_select=rnd(d_sal), d_auditor_select=rnd(d_aud),
                    z_own=rnd(z_own), z_cross=rnd(z_cross),
                    z_salience=rnd(z_sal), z_auditor=rnd(z_aud),
                    score=rnd(score),
                    # --- HOLDOUT half: independent estimates of the same gaps ---
                    d_own_holdout=rnd(d_own_h), d_cross_holdout=rnd(d_cross_h),
                    d_salience_holdout=rnd(d_sal_h), d_auditor_holdout=rnd(d_aud_h),
                    d_own_shrinkage=rnd(d_own - d_own_h),
                    holdout_own_sign_agrees=(d_own_h > 0) if d_own_h == d_own_h else "",
                    holdout_cross_still_matched=(abs(d_cross_h) <= CROSS_TOL)
                    if d_cross_h == d_cross_h else "",
                    # --- full-sample gaps, reported for transparency only ---
                    d_own_full=rnd(d("own_" + model, "")),
                    d_cross_full=rnd(d("cross", "")),
                    # --- eligibility flags (descriptive) ---
                    ok_own_separated=ok_own, ok_cross_matched=ok_cross,
                    ok_auditor_matched=ok_aud, ok_salience_matched=ok_sal,
                    eligible_study1_parity=elig_parity, eligible=eligible,
                    large_own_z=(abs(z_own) >= LARGE_OWN_Z) if z_own == z_own else "",
                    small_cross_z=(abs(z_cross) <= SMALL_NUISANCE_Z) if z_cross == z_cross else "",
                    same_modal_high=H["same_modal_identity"],
                    same_modal_low=L["same_modal_identity"],
                    rank_in_model="",
                    approved=False,          # <- a human approves, never the script
                ))

    for model in MODELS:
        pool = [c for c in cands if c["focal_model"] == model]
        pool.sort(key=lambda c: -(c["score"] if c["score"] != "" else -9e9))
        for i, c in enumerate(pool, 1):
            c["rank_in_model"] = i
    cands.sort(key=lambda c: (c["focal_model"], c["rank_in_model"]))
    return cands


# ------------------------------------------------------------------- main ----
def main():
    stage_a = newest("stageA_*.csv")
    fresh = os.path.join(STUDY1, "data", "fresh_self_match.csv")
    sal = {r["stimulus"]: r for r in
           csv.DictReader(open(os.path.join(STUDY1, "data", "salience_ratings.csv")))
           if r["rater_model"] == "pooled"}
    aud = {(r["focal_model"], r["stimulus"]): r for r in
           csv.DictReader(open(os.path.join(STUDY1, "data", "auditor_predictions.csv")))}

    print("=" * 78)
    print("CROSS-MODEL COORDINATION  --  Study-1 battery, Study-2 pair re-derivation")
    print("=" * 78)
    print(f"  stage A            : {os.path.basename(stage_a)}")
    print(f"  bootstrap          : B={tc.BOOT_B}, percentile, seed base {tc.BOOT_SEED}")
    print("  own-copy estimator : targeted_common.unbiased_match  (BIAS-CORRECTED,")
    print("                       same-draw pairs removed; both draws, one sample)")
    print("  cross estimator    : sum_k p_k^gpt * p_k^claude       (PLUG-IN, already")
    print("                       unbiased; two disjoint samples, no same-draw pair)")
    print("\n  DESCRIPTIVE HEURISTICS IN FORCE (none is a test, none selects):")
    print(f"    OWN_SEP_MIN={OWN_SEP_MIN}  CROSS_TOL={CROSS_TOL}  "
          f"AUD_TOL={AUD_TOL}  SAL_TOL={SAL_TOL}")
    print(f"    LARGE_OWN_Z={LARGE_OWN_Z}  SMALL_NUISANCE_Z={SMALL_NUISANCE_Z}")
    print(f"    W_CROSS={W_CROSS}  W_SALIENCE={W_SALIENCE}  W_AUDITOR={W_AUDITOR}")

    table, imbalanced, sids = build_table(stage_a, sal, aud)
    os.makedirs(OUT, exist_ok=True)
    write_csv(os.path.join(OUT, "cross_model_table.csv"), table)

    print(f"\n  AB/BA balance: {'OK, every cell and half balanced' if not imbalanced else 'IMBALANCED CELLS:'}")
    for m, s, tag, a, b in imbalanced:
        print(f"    {m:7s} {s:16s} {tag:8s} nAB={a} nBA={b}")

    # ---- self-check ----------------------------------------------------------
    checks = selfcheck(table, fresh)
    bad = [c for c in checks if not c[4]]
    print(f"\n  SELF-CHECK vs fresh_self_match.csv own-copy column: "
          f"{len(checks) - len(bad)}/{len(checks)} exact")
    for m, s, want, got, ok in checks[:5]:
        print(f"    {m:7s} {s:16s} ref={want:.4f} recomputed={got:.4f} "
              f"{'MATCH' if ok else 'MISMATCH'}")
    for m, s, want, got, ok in bad:
        print(f"    MISMATCH {m} {s}: ref={want} got={got}")

    # ---- per-stimulus table --------------------------------------------------
    print("\n" + "=" * 78)
    print("PER-STIMULUS: own-copy match, cross-model match, public measures")
    print("=" * 78)
    print(f"  {'stimulus':16s} {'own_gpt':>18s} {'own_claude':>18s} {'cross':>18s}"
          f" {'sal':>6s} {'audG':>6s} {'audC':>6s} same")
    for r in table:
        f = lambda v, l, h: f"{fnum(v):.3f}[{fnum(l):.2f},{fnum(h):.2f}]"
        print(f"  {r['stimulus']:16s} "
              f"{f(r['own_gpt'], r['own_gpt_ci_lo'], r['own_gpt_ci_hi']):>18s} "
              f"{f(r['own_claude'], r['own_claude_ci_lo'], r['own_claude_ci_hi']):>18s} "
              f"{f(r['cross'], r['cross_ci_lo'], r['cross_ci_hi']):>18s} "
              f"{fnum(r['generic_salience']):>6.3f} "
              f"{fnum(r['auditor_pred_gpt']):>6.3f} "
              f"{fnum(r['auditor_pred_claude']):>6.3f} "
              f"{'Y' if r['same_modal_identity'] else 'n'}")

    tab = {r["stimulus"]: r for r in table}
    og = [fnum(tab[s]["own_gpt"]) for s in sids]
    oc = [fnum(tab[s]["own_claude"]) for s in sids]
    xs = [fnum(tab[s]["cross"]) for s in sids]
    print(f"\n  battery SD  own_gpt={_sd(og):.3f}  own_claude={_sd(oc):.3f}  "
          f"cross={_sd(xs):.3f}")
    for m, ov in (("gpt", og), ("claude", oc)):
        n = len(sids)
        mo, mx = statistics.fmean(ov), statistics.fmean(xs)
        so, sx = _sd(ov), _sd(xs)
        cov = sum((a - mo) * (b - mx) for a, b in zip(ov, xs)) / n
        rr = cov / (so * sx) if so and sx else float("nan")
        print(f"  corr(own_{m}, cross) over the {n} stimuli = {rr:+.3f}   "
              "[descriptive; a high positive value is exactly the confound]")

    # ---- where own and cross come apart -------------------------------------
    # A Study-2 pair needs stimuli that move own-copy match WITHOUT moving cross.
    # That is only possible if the battery contains stimuli where own and cross
    # DISSOCIATE. Listing them is the cheapest way to see whether it does.
    print("\n  DISSOCIATION own vs cross (max over the two models of own - cross):")
    print("    a HIGH stimulus for Study 2 wants own >> cross; a LOW stimulus wants")
    print("    own ~ cross ~ chance. Descriptive listing, selects nothing.")
    diss = sorted(sids, key=lambda s: -max(
        fnum(tab[s]["own_gpt"]) - fnum(tab[s]["cross"]),
        fnum(tab[s]["own_claude"]) - fnum(tab[s]["cross"])))
    for s in diss[:6]:
        print(f"    {s:16s} own_gpt={fnum(tab[s]['own_gpt']):.3f} "
              f"own_claude={fnum(tab[s]['own_claude']):.3f} "
              f"cross={fnum(tab[s]['cross']):.3f}   "
              f"modal gpt={tab[s]['modal_gpt']!r} claude={tab[s]['modal_claude']!r}")

    # ---- Study 1's approved pairs, audited ----------------------------------
    print("\n" + "=" * 78)
    print("STUDY 1's FIVE APPROVED PAIRS, AUDITED AGAINST THE CROSS-MODEL AXIS")
    print("=" * 78)
    print(f"  usable for Study 2 requires |d_own| >= {OWN_SEP_MIN} AND "
          f"|d_cross| <= {CROSS_TOL}")
    print(f"\n  {'pair':44s} {'d_own':>7s} {'d_cross':>8s}  verdict")
    canon_rows = []
    for model, hi, lo in CANON:
        H, L = tab[hi], tab[lo]
        d_own = fnum(H[f"own_{model}"]) - fnum(L[f"own_{model}"])
        d_cross = fnum(H["cross"]) - fnum(L["cross"])
        ok = abs(d_own) >= OWN_SEP_MIN and abs(d_cross) <= CROSS_TOL
        verdict = "USABLE" if ok else (
            "CONFOUNDED (cross moves with own)" if abs(d_cross) > CROSS_TOL
            else "own-copy gap too small")
        pid = f"{model}__{hi}__vs__{lo}"
        print(f"  {pid:44s} {d_own:>+7.3f} {d_cross:>+8.3f}  {verdict}")
        canon_rows.append((pid, d_own, d_cross, ok))
    n_ok = sum(1 for _, _, _, ok in canon_rows if ok)
    print(f"\n  --> {n_ok} of {len(CANON)} Study-1 approved pairs are usable for Study 2.")

    # ---- Study 2 candidates --------------------------------------------------
    cands = build_pairs(table, sids)
    write_csv(os.path.join(OUT, "study2_candidate_pairs.csv"), cands)

    print("\n" + "=" * 78)
    print("STUDY 2 CANDIDATE PAIRS  (selected on SELECT half, reported on HOLDOUT)")
    print("=" * 78)
    for model in MODELS:
        pool = [c for c in cands if c["focal_model"] == model]
        elig = [c for c in pool if c["eligible"]]
        par = [c for c in pool if c["eligible_study1_parity"]]
        print(f"\n  {P.DISPLAY[model]}: {len(pool)} within-model pairs")
        print(f"    eligible_study1_parity  (|d_own|>={OWN_SEP_MIN}, "
              f"|d_cross|<={CROSS_TOL}, |d_aud|<={AUD_TOL})            : {len(par)}")
        print(f"    eligible_strict         (the above AND |d_sal|<={SAL_TOL})"
              f"                       : {len(elig)}")
        hdr = (f"    {'rank':>4s} {'pair':40s} {'d_own':>7s} {'d_cross':>8s} "
               f"{'d_sal':>7s} {'d_aud':>7s} {'score':>6s} | "
               f"{'HOd_own':>8s} {'HOd_cross':>9s}  elig")
        print(hdr)
        for c in pool[:TOP_N_SHOWN]:
            print(f"    {c['rank_in_model']:>4d} {c['pair_id']:40s} "
                  f"{fnum(c['d_own_select']):>+7.3f} {fnum(c['d_cross_select']):>+8.3f} "
                  f"{fnum(c['d_salience_select']):>+7.3f} {fnum(c['d_auditor_select']):>+7.3f} "
                  f"{fnum(c['score']):>+6.2f} | "
                  f"{fnum(c['d_own_holdout']):>+8.3f} {fnum(c['d_cross_holdout']):>+9.3f}"
                  f"  {'YES' if c['eligible'] else '-'}")
        if par:
            print("    pairs passing eligible_study1_parity, in rank order:")
            for c in par:
                print(f"      rank {c['rank_in_model']:>3d}  {c['pair_id']:40s} "
                      f"d_own={fnum(c['d_own_select']):+.3f} "
                      f"d_cross={fnum(c['d_cross_select']):+.3f} "
                      f"d_sal={fnum(c['d_salience_select']):+.3f}"
                      f"{'' if c['eligible'] else '  [fails SAL_TOL]'}"
                      f"  | holdout d_own={fnum(c['d_own_holdout']):+.3f}, "
                      f"d_cross={fnum(c['d_cross_holdout']):+.3f}")
            # INDEPENDENCE. Three eligible pairs are only three usable design cells
            # if they do not recycle the same stimulus. Reported, never auto-pruned.
            use = Counter()
            for c in par:
                use[c["stimulus_high"]] += 1
                use[c["stimulus_low"]] += 1
            distinct_high = {c["stimulus_high"] for c in par}
            print(f"    stimulus reuse among those pairs: "
                  + ", ".join(f"{k}x{v}" for k, v in use.most_common()))
            print(f"    distinct HIGH stimuli among them : {len(distinct_high)} "
                  f"({', '.join(sorted(distinct_high))})")
            print("      -> pairs sharing one HIGH stimulus are NOT independent "
                  "replications; they")
            print("         re-test the same stimulus against different controls.")

    print("\n" + "=" * 78)
    print("OUTPUTS")
    print("=" * 78)
    print(f"  {os.path.join(OUT, 'cross_model_table.csv')}")
    print(f"  {os.path.join(OUT, 'study2_candidate_pairs.csv')}  "
          f"(every row approved=False)")
    print("\n" + "=" * 78)
    print("SUFFICIENCY")
    print("=" * 78)
    for model in MODELS:
        par = [c for c in cands
               if c["focal_model"] == model and c["eligible_study1_parity"]]
        n_strict = sum(1 for c in par if c["eligible"])
        n_hi = len({c["stimulus_high"] for c in par})
        print(f"\n  {P.DISPLAY[model]}: {len(par)} parity-eligible, "
              f"{n_strict} strict-eligible, {n_hi} distinct HIGH stimulus/stimuli")
        if n_hi < 3:
            print(f"    *** INSUFFICIENT. Fewer than 3 INDEPENDENT clean pairs exist "
                  f"for this model on the")
            print(f"        15-stimulus battery: the parity-eligible pairs rest on "
                  f"{n_hi} distinct HIGH stimulus/")
            print(f"        stimuli, so they are re-tests of the same stimulus, not "
                  f"replications.")
            print("    *** WHAT WOULD BE NEEDED: the expanded 45-stimulus battery "
                  "(these 15 plus the 30 in")
            print("        stimuli/expansion/, run in generation_ladder_20260814/"
                  "models/). Every Stage A run")
            print("        there is an OLDER generation -- gpt-4o, gpt-5, "
                  "opus-4.5/4.6/4.7/4.8 -- and none")
            print("        pairs GPT-5.5 with Claude Opus 5, so no cross-model rate "
                  "can be formed from it.")
            print("        Using it means a FRESH Stage A for this generation on the "
                  "30 new stimuli:")
            print("        30 x 60 x 2 models = 3600 calls, plus a matching Stage B "
                  "(auditor 30 x 30 x 2 =")
            print("        1800, salience 30 x 30 x 2 = 1800) ~= 7200 paid calls. "
                  "NOT RUN HERE -- this")
            print("        script makes no API calls.")


if __name__ == "__main__":
    main()
