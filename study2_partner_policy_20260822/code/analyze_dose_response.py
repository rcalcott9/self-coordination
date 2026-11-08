"""
STUDY 2 (revised) - PRIMARY ANALYSIS: the compatibility DOSE-RESPONSE.

=============================================================================
THE QUESTION, AND WHY IT REPLACED THE INTERACTION
=============================================================================
Study 2's earlier primary test was a Stimulus x Partner interaction on a matched
HIGH/LOW pair. That test has one binary dose level per pair. The revised design
replaces it with a GRADED one: eight stimuli per actor spanning a measured range of
compatibility advantage, from strongly negative to strongly positive
(FROZEN_PARAMS.GRADIENT).

  advantage(actor, stimulus) = own-copy reliability - cross-model reliability

The question is whether the same-vs-different partner effect on P(ATTEMPT) SCALES
with that advantage:

  MODEL A  coarse identity heuristic   partner effect = c,          for every stimulus
  MODEL B  policy-specific sensitivity partner effect = c + b*adv,  b > 0

The primary coefficient is b, the Partner x CompatibilityAdvantage slope, NOT the
average same-model effect. THIS IS THE WHOLE POINT AND IT IS STATED HERE BECAUSE IT
IS EASY TO GET WRONG: MODEL A predicts a positive average same-model effect just as
readily as MODEL B does. A significant partner main effect is therefore evidence for
"the partner label mattered" and evidence for NEITHER model over the other. Only b
separates them. Every place this script prints a partner main effect, it says so.

=============================================================================
THE ESTIMAND, ON THE RISK-DIFFERENCE SCALE
=============================================================================
PRIMARY, trial level, one row per trial (fitted equivalently as weighted least
squares on the (actor x stimulus x partner x payoff) cell counts, which is
algebraically identical to trial-level OLS on the 0/1 outcome):

  ATTEMPT = mu[actor, stimulus]                        stimulus fixed effects
          + bS[actor] * (SAFE - SAFEbar)               payoff response
          + SAME * ( g0[actor] + g1 * advantage )      <- g1 IS THE PRIMARY

Stimulus fixed effects mean g0 and g1 are identified ENTIRELY from within-stimulus
same-minus-different contrasts. The fit is therefore exactly a precision-weighted
regression of the per-stimulus partner effect on advantage - the quantity the main
figure plots - and nothing about the level of P(ATTEMPT) across stimuli can leak
into it. Everything is computed from INTEGER COUNTS; rates are formed only at the
moment of printing. That is Study 1's rounding-bug discipline, carried over
verbatim (see analyze_study2.py's module docstring for the 0.0485-vs-0.1334 case).

A LOGIT-scale version of the same model is fitted alongside and carries the model
comparison, because a constant shift is a different object on the two scales and the
difference is not cosmetic - see "THE SCALE TRAP" below.

=============================================================================
ADVANTAGE IS MEASURED, NOT KNOWN
=============================================================================
advantage is an ESTIMATE from the confirmation screen, with sampling error. Putting
an error-laden regressor on the x-axis and running OLS gives a slope biased TOWARD
ZERO (classical regression dilution / attenuation). The direction is not ambiguous
and it is not conservative for MODEL A: attenuation makes a true MODEL B look more
like MODEL A, so a plug-in null result is weaker evidence for A than it appears.

Four estimators are reported, always together:

  1. PLUG-IN            advantage fixed at its point estimate; bootstrap over Stage C
                        trials only. ATTENUATED. Stated as such at every print.
  2. PLUG-IN + STAGE A BOOTSTRAP
                        additionally resamples the confirmation counts. This WIDENS
                        the interval and does NOT remove the attenuation - the centre
                        stays biased toward zero. Propagating uncertainty and
                        correcting bias are different operations and this script
                        never lets one stand in for the other.
  3. REGRESSION CALIBRATION (method of moments)
                        g1 / reliability, reliability = (Var(adv_hat) - mean SE^2) /
                        Var(adv_hat). Closed form, cheap, a sanity check on (4).
  4. ERRORS-IN-VARIABLES, latent predictor, FULL JOINT BAYESIAN MODEL  <- the fix
                        The confirmation counts are modelled, not summarised:

                          k[m,s]  ~ Binomial(n[m,s], pi[m,s])        Stage A
                          own[m,s]   = pi^2 + (1-pi)^2               exact, binary
                          cross[s]   = pi_g*pi_c + (1-pi_g)(1-pi_c)  exact, binary
                          adv[m,s]   = own[m,s] - cross[s]           deterministic
                          y[trial]   ~ Bernoulli(sigmoid(... + g1*SAME*adv))

                        adv is a LATENT quantity, so g1 is not diluted. Sampled with
                        a blocked adaptive Metropolis sampler written here (pymc is
                        not importable in this environment - numpy ABI clash - and
                        the primary analysis must never depend on it).

  Note the identity-level parameterisation is not a convenience. Every stimulus is a
  BINARY choice, so own and cross are exact functions of the two marginals, and the
  structural constraint of FROZEN_PARAMS section 2,
      |cross - 1/2| = sqrt( (own_g - 1/2) * (own_c - 1/2) ),
  holds automatically instead of being imposed. It also makes the measurement errors
  in GPT's and Claude's advantage on the SAME stimulus correlated, through the shared
  cross term - which they genuinely are, and which no per-actor correction can see.

  Plain OLS on the ~8 aggregated per-stimulus points is computed and reported as a
  descriptive figure-companion ONLY, never as the analysis. It is the most attenuated
  of the lot and it throws away the within-stimulus trial counts.

=============================================================================
THE SCALE TRAP  (why MODEL A is fitted on the logit scale)
=============================================================================
"A constant same-model shift" is scale-dependent. A shift that is constant in LOG
ODDS is NOT constant in risk difference: it is largest where the baseline attempt
rate is near 0.5 and shrinks toward the 0/1 ceilings. So a pure MODEL A process can
manufacture a NONZERO risk-difference dose-response slope whenever the baseline
attempt rate happens to vary systematically with advantage - and the induced slope is
POSITIVE, i.e. it mimics MODEL B, precisely when the low-advantage stimuli sit
further from 0.5 than the high-advantage ones.

This is the same failure mode Study 2's earlier validation named `main_effect_low_base`,
and it is the single most likely way this analysis could report MODEL B when MODEL A
is true. It is handled, not hoped away:

  - the MODEL A / MODEL B comparison is run on the LOGIT scale, where MODEL A's
    "constant shift" is exactly the constant it claims to be. A logit-constant
    process fits MODEL A perfectly, so the comparison is not fooled;
  - a BASELINE-ARTEFACT DIAGNOSTIC is printed with every risk-difference slope: the
    partner effect predicted at each stimulus by the fitted MODEL A alone, and the
    slope of THOSE predictions on advantage. That number is how much of the observed
    risk-difference slope a constant log-odds shift can produce by itself;
  - the simulator carries a `dose_a_logit` ground truth built specifically so the
    artefact points the dangerous way, and its recovered numbers are in
    analysis/DOSE_RESPONSE_VALIDATION.md.

=============================================================================
PERMUTATION INFERENCE  (analogous to Study 1, on raw counts)
=============================================================================
The PARTNER label is permuted within each (actor x stimulus x safe payoff) stratum -
the finest cell the same/different contrast crosses over. The shuffle preserves, by
construction and exactly: the payoff response, every stimulus's own baseline attempt
propensity, every stimulus's advantage, and every cell size. It destroys only the
association between the partner label and the outcome. Draws are exact conditional
hypergeometrics on the integer counts (analyze_study2._hyper), so for a single 2x2
stratum this reduces to Fisher's exact test, and ties with the observed statistic are
counted (the `- 1e-12` tolerance), as a permutation test requires.

The permuted sharp null is "the partner label had no effect at all", which is
STRONGER than the null g1 = 0 that MODEL A also satisfies. The same two-part argument
that licensed it for the old interaction licenses it here, and the algebra is if
anything cleaner:

  (1) ORTHOGONALITY. g1 is the slope of the per-stimulus partner effect on advantage.
      A partner effect that is constant on the risk-difference scale adds the same
      amount to every stimulus's partner effect, which moves the INTERCEPT g0 and
      leaves the SLOPE g1 identically unchanged. So the reference distribution is
      centred on zero under MODEL A as well as under the sharp null.
  (2) CONSERVATISM. Under the permutation, within-stratum variance is that of the
      SAME/DIFFERENT-pooled cell. A real partner main effect inflates that relative
      to the truth, so the reference distribution is slightly too WIDE and the p
      slightly too large. Conservative is the acceptable error here.

  Caveat (1) is exact on the risk-difference scale and only approximate on the logit
  scale - which is the scale trap again, and is why the baseline-artefact diagnostic
  is printed beside the permutation p rather than after it.

Because the design matrix and every cell n are FIXED under this permutation, the WLS
slope is a fixed linear functional of the cell rates. g1 for a replicate is therefore
one dot product, and 20 000 exact replicates cost less than one IRLS fit.

SIDEDNESS. MODEL B makes a signed prediction (b > 0), so the ONE-SIDED p is primary
for g1; two-sided is printed beside it. The partner main effect keeps its two-sided
p, as in the interaction analysis, because the design does not stake a claim on it.

=============================================================================
MODEL COMPARISON
=============================================================================
MODEL A is NESTED in MODEL B (it is B with g1 = 0), so three criteria are reported
and they answer different questions:

  LRT / AIC / BIC   in-sample, on the trial-level binomial likelihood. AIC and BIC
                    disagree by construction when evidence is middling; both are
                    printed rather than whichever one is kinder.
  LEAVE-ONE-STIMULUS-OUT   the honest one, and the one to read. Each stimulus is
                    held out in turn; A and B are fitted on the rest; the held-out
                    stimulus's baseline mu is then estimated from its DIFFERENT-
                    partner cells ONLY (which contain no partner-effect information),
                    and each model predicts its SAME-partner cells. The score is
                    binomial log-loss on those held-out SAME cells. This asks exactly
                    the question the design was built to ask - given a NEW stimulus
                    of known compatibility, does knowing its advantage predict how
                    much more willing the model is to enter against a copy of itself?
                    A coarse identity heuristic cannot win this and a real
                    policy-specific sensitivity can.
  MODEL 0           no partner effect at all, as the floor. If A does not beat 0,
                    then nothing beats 0 and the model comparison is vacuous.

=============================================================================
ROBUSTNESS  (FROZEN_PARAMS section 14)
=============================================================================
  - primary slope with ALL stimuli AND excluding a_chev_ud, which supplies the
    largest advantage for BOTH actors and would otherwise dominate the slope on
    leverage alone. a_chev_ud stays in the primary data; the exclusion is a
    sensitivity analysis, declared in advance;
  - GPT and Claude separately, and pooled (shared g1, actor-specific everything
    else). Pooling is reported as primary only when the two actor-specific slopes
    are not obviously discordant; the per-actor slopes are printed either way and
    the reader can see the disagreement if there is one;
  - EVERY stimulus's partner effect, with the raw integer cells shown, including
    zero cells and negative cells. Nothing is hidden behind a rate.

=============================================================================
SAMPLE SPLITTING - A DELIBERATE DEPARTURE, DECLARED
=============================================================================
The interaction analysis reported HOLDOUT as primary. This one reports FULL, and the
reason is arithmetic, not taste: the frozen allocation gives the large-advantage
cells N_PARTNER = 32, i.e. 8 trials per payoff cell, and halving that leaves 4. The
select/holdout machinery is still run and all three samples are printed, because
agreement across them is worth seeing; but the frozen allocation in FROZEN_PARAMS
section 7 was sized for the full sample and nothing in Study 2 was selected on Study 2
data - the stimulus gradient is inherited from the Stage A battery and the partner
factor is new. `--sample holdout` reproduces the older convention.

RUN
  python3 analyze_dose_response.py
  python3 analyze_dose_response.py --data ../data/sim_dose_b.csv \
                                   --confirm ../data/sim_dose_b_confirmA.csv --tag dose_b
  python3 analyze_dose_response.py --no-eiv        # skip the MCMC, everything else runs
"""
import argparse, csv, glob, json, math, os, sys
from collections import Counter, defaultdict

try:
    import numpy as np
except ImportError:                                     # pragma: no cover
    sys.exit("numpy required")

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(EXP, "design"))

import study2_schema as S
import analyze_study2 as A          # validated machinery: reused, never re-implemented
import FROZEN_PARAMS as F

# Guard: the single source of truth must actually be the source of truth.
assert F.ADVANTAGE_DEF == "own_minus_cross", F.ADVANTAGE_DEF
assert F.PRIMARY_COEF == "partner_x_advantage", F.PRIMARY_COEF

BOOT = 5000
PERM = 20000
SEED = 20260822
LOSO_TIE_NATS = 2.0     # a smaller out-of-sample margin than this is called a tie
TOL = A.TOL
EPS = 1e-12

ATTENUATION_NOTE = (
    "PLUG-IN: advantage treated as error-free, so this slope is ATTENUATED - biased "
    "TOWARD ZERO by regression dilution. It understates MODEL B and flatters MODEL A.")

MODELS = ("gpt", "claude")


# ============================================================ advantage =======
def unbiased_match(n1, n2):
    """sum_k n_k(n_k-1) / [N(N-1)] - Study 1's frozen own-copy estimator.

    Reproduced from targeted_common.unbiased_match rather than imported: that module
    lives in a separate repo and pulls in the API clients. It is a one-line formula
    and the copy is checked against the battery table by reproduce_battery().
    """
    n = n1 + n2
    if n < 2:
        return float("nan")
    return (n1 * (n1 - 1) + n2 * (n2 - 1)) / (n * (n - 1))


def cross_plugin(p_g, p_c):
    """sum_k p_k^g p_k^c for a binary stimulus. Plug-in, already unbiased across the
    two INDEPENDENT cells - cross_model_match.py's documented asymmetry: the (n-1)
    correction belongs to own-copy (where the two draws come from one cell) and would
    over-correct here."""
    return p_g * p_c + (1.0 - p_g) * (1.0 - p_c)


def advantage_point(cc, stimuli):
    """Point estimates from confirmation counts.

    cc: {(model, stimulus): (k_identity1, n)}.  Returns dict with own/cross/adv and
    a parametric-bootstrap SE for adv per (actor, stimulus).
    """
    own, cross, adv = {}, {}, {}
    for s in stimuli:
        ps = {}
        for m in MODELS:
            k, n = cc[(m, s)]
            own[(m, s)] = unbiased_match(k, n - k)
            ps[m] = k / n
        cross[s] = cross_plugin(ps["gpt"], ps["claude"])
        for m in MODELS:
            adv[(m, s)] = own[(m, s)] - cross[s]
    return dict(own=own, cross=cross, adv=adv)


def advantage_draws(cc, stimuli, ndraw, rng, mode="posterior"):
    """(ndraw, n_actor, n_stim) array of advantage.

    mode='posterior'  latent pi ~ Beta(1 + k, 1 + n - k), the exact conjugate
                      posterior under the uniform prior the EIV model also uses. own
                      and cross are then EXACT functions of the latent, so the (n-1)
                      correction is not applied - it is a frequentist device for the
                      plug-in estimator and here it would correct a bias that the
                      latent parameterisation does not have.
    mode='bootstrap'  parametric bootstrap: k* ~ Binomial(n, k/n), re-estimated with
                      the same frequentist estimators as advantage_point. This is what
                      "bootstrap propagating Stage A uncertainty" means, and it moves
                      the interval, not the centre.
    """
    nS = len(stimuli)
    out = np.empty((ndraw, 2, nS))
    for j, s in enumerate(stimuli):
        p = {}
        for m in MODELS:
            k, n = cc[(m, s)]
            if mode == "posterior":
                p[m] = rng.beta(1.0 + k, 1.0 + n - k, size=ndraw)
            else:
                p[m] = rng.binomial(n, k / n, size=ndraw) / n
        cr = cross_plugin(p["gpt"], p["claude"])
        for i, m in enumerate(MODELS):
            k, n = cc[(m, s)]
            if mode == "posterior":
                ow = p[m] ** 2 + (1 - p[m]) ** 2
            else:
                k1 = np.round(p[m] * n).astype(int)
                ow = (k1 * (k1 - 1) + (n - k1) * (n - k1 - 1)) / (n * (n - 1))
            out[:, i, j] = ow - cr
    return out


def counts_from_confirmed_table(path, log):
    """Reconstruct identity-1 counts from confirm_compat.py's confirmed_compatibility.csv.

    RECONCILIATION, 2026-08-22. The confirmation screen (code/confirm_compat.py) landed
    while this analysis was being validated. It does NOT publish raw identity counts; it
    publishes GG, CC, GC, the advantages and their bootstrap CIs, having already done the
    provenance-guarded merge across resume part files and self-checked its code path
    against pairs/cross_model_table.csv. Re-doing that merge here would duplicate it and
    risk disagreeing with it, so this analysis reads its OUTPUT and recovers the counts
    the errors-in-variables model needs.

    THE RECOVERY IS EXACT, NOT AN APPROXIMATION, and it is exact for the same reason the
    design works at all: every stimulus is a BINARY choice. Writing u = 2(pi_gpt - 1/2),

        own_unbiased = [n1(n1-1) + n2(n2-1)] / [n(n-1)]   so   sum_k p_k^2
                                                  = (own_unbiased*(n-1) + 1) / n
        sum_k p_k^2 = 1/2 + u^2/2                 so   |u| = sqrt(2*(sum p^2 - 1/2))

    which fixes the MAGNITUDE of the deviation from chance; the table's `modal_gpt` /
    `modal_claude` columns fix the SIGN against the manifest's identity_1. The
    reconstruction is then verified by recomputing GG, CC, GC and both advantages from
    the recovered counts and comparing with the table. A residual above 0.005 means the
    stimulus is not binary or an estimator changed, and the analysis REFUSES rather than
    proceeding on a reconstruction it cannot vouch for.
    """
    man = load_manifest()
    rows = list(csv.DictReader(open(path)))
    cc, worst, worst_where = {}, 0.0, None
    for r in rows:
        s = r["stimulus"]
        id1 = man.get(s, (None, None))[0]
        if id1 is None:
            log(f"  !! {s} is not in stimulus_manifest.csv; cannot fix the identity "
                "labelling, so it is dropped")
            continue
        got = {}
        for m, own_col, n_col in (("gpt", "GG", "n_gpt"), ("claude", "CC", "n_claude")):
            n = int(float(r[n_col]))
            own = float(r[own_col])
            sump2 = (own * (n - 1) + 1.0) / n
            u = math.sqrt(max(0.0, 2.0 * (sump2 - 0.5)))
            if str(r.get(f"modal_{m}", "")).strip() != id1:
                u = -u                      # the mode is identity_2, so pi < 1/2
            pi = 0.5 + u / 2.0
            k = int(round(pi * n))
            cc[(m, s)] = (k, n)
            got[m] = (k, n)
        # verify
        ps = {m: got[m][0] / got[m][1] for m in MODELS}
        rec_cross = cross_plugin(ps["gpt"], ps["claude"])
        for m, own_col, adv_col in (("gpt", "GG", "advantage_gpt"),
                                    ("claude", "CC", "advantage_claude")):
            k, n = got[m]
            d_own = abs(unbiased_match(k, n - k) - float(r[own_col]))
            d_adv = abs((unbiased_match(k, n - k) - rec_cross) - float(r[adv_col]))
            for d in (d_own, d_adv):
                if d > worst:
                    worst, worst_where = d, (m, s)
        d_cross = abs(rec_cross - float(r["GC"]))
        if d_cross > worst:
            worst, worst_where = d_cross, ("cross", s)
    if worst > 0.005:
        sys.exit(f"REFUSING TO RUN: reconstructing identity counts from {path} does not "
                 f"reproduce its own GG/CC/GC/advantage columns (max residual "
                 f"{worst:.4f} at {worst_where}).\n"
                 "  The recovery is exact only for BINARY stimuli under the frozen "
                 "estimators. Either a stimulus is not binary, or an estimator changed. "
                 "Supply the raw confirmation trials with --confirm instead.")
    log(f"  confirmation counts: {path}  (confirm_compat.py CONFIRMED TABLE; identity "
        f"counts recovered by exact inversion of the binary-stimulus identity, max "
        f"residual against its own GG/CC/GC/advantage columns {worst:.5f})")
    return cc


def load_confirm(paths, log):
    """Confirmation-screen counts. Returns (cc, source).

    Three accepted forms, tried in the order the paths are given:
      (3) confirm_compat.py's design/confirmed_compatibility.csv  <- the real one
      (2) aggregated counts   model, stimulus, n, k_identity1
      (1) per-trial Stage-A rows with parsed_choice_identity
    """
    for path in paths:
        if not path or not os.path.exists(path):
            continue
        rows = list(csv.DictReader(open(path)))
        if not rows:
            continue
        cols = set(rows[0])

        # form (3): the confirmation screen's own published table
        if {"stimulus", "GG", "CC", "GC", "n_gpt", "n_claude"} <= cols:
            return counts_from_confirmed_table(path, log), path

        def find(canon):
            if canon in cols:
                return canon
            for alt in S.CONFIRM_ALIASES.get(canon, []):
                if alt in cols:
                    return alt
            return None

        # form (2): aggregated counts
        c_m, c_s, c_n, c_k = (find("model"), "stimulus" if "stimulus" in cols else None,
                              find("n"), find("k_identity1"))
        if c_m and c_s and c_n and c_k:
            cc = {}
            for r in rows:
                cc[(str(r[c_m]).strip().lower(), r[c_s])] = (int(float(r[c_k])),
                                                             int(float(r[c_n])))
            log(f"  confirmation counts: {path}  (AGGREGATED form, "
                f"{len(cc)} model x stimulus cells)")
            return cc, path
        # form (1): per-trial Stage-A rows
        if c_m and c_s and "parsed_choice_identity" in cols:
            man = load_manifest()
            agg = defaultdict(lambda: [0, 0])
            drop = 0
            for r in rows:
                if "included_in_analysis" in cols and not A._truthy(r["included_in_analysis"]):
                    continue
                if "valid_response" in cols and not A._truthy(r["valid_response"]):
                    continue
                if "superseded_by_retry" in cols and A._truthy(r["superseded_by_retry"]):
                    continue
                m, s = str(r[c_m]).strip().lower(), r[c_s]
                ident = str(r["parsed_choice_identity"]).strip()
                id1 = man.get(s, (None, None))[0]
                if id1 is None:
                    drop += 1
                    continue
                agg[(m, s)][0] += int(ident == id1)
                agg[(m, s)][1] += 1
            cc = {k: tuple(v) for k, v in agg.items()}
            log(f"  confirmation counts: {path}  (PER-TRIAL form, aggregated to "
                f"{len(cc)} cells against stimulus_manifest identity_1"
                + (f"; {drop} rows dropped, stimulus not in the manifest)" if drop else ")"))
            return cc, path
    return {}, None


def load_manifest():
    p = os.path.join(EXP, "stimulus_manifest.csv")
    if not os.path.exists(p):
        return {}
    return {r["stimulus_id"]: (r.get("identity_1"), r.get("identity_2"))
            for r in csv.DictReader(open(p))}


def provisional_advantage():
    """FROZEN_PARAMS.GRADIENT's provisional values. NO uncertainty attached."""
    return {(m, sid): adv for m, tiers in F.GRADIENT.items()
            for sid, adv, _t, _n in tiers}


def tier_map():
    """CURRENT tier labels, from ACTIVE_GRADIENT (= the confirmed re-freeze).

    Deliberately NOT F.GRADIENT. That block holds the superseded provisional
    tiers and is retained only as a record; reading it here would mislabel every
    cell the confirmation screen re-tiered - GPT's c_open_cplx (large, +0.489)
    would print as `medium`, and Claude's c_open_cplx (zero_floor, -0.003) as
    `negative`. Tier drives allocation only, so this is a labelling fix, not an
    inferential one: the slope is fit on the continuous advantage throughout.
    `provisional_advantage()` above and the sign/order gate below DO read
    F.GRADIENT, correctly - their whole job is to compare provisional against
    confirmed.
    """
    return {(m, sid): t for m, tiers in F.ACTIVE_GRADIENT.items()
            for sid, _a, t, _n in tiers}


def reproduce_battery(log):
    """Check the estimators against pairs/cross_model_table.csv before using them.

    The advantage definition is inherited, not invented here, so it is checked
    against the table cross_model_match.py actually produced. A drift shows up now,
    on a known answer, rather than as a wrong slope later.
    """
    p = os.path.join(EXP, "pairs", "cross_model_table.csv")
    if not os.path.exists(p):
        return
    prov = provisional_advantage()
    worst, n = 0.0, 0
    for r in csv.DictReader(open(p)):
        s = r["stimulus"]
        for m in MODELS:
            if (m, s) not in prov:
                continue
            got = float(r[f"own_{m}"]) - float(r["cross"])
            worst = max(worst, abs(got - prov[(m, s)]))
            n += 1
    log(f"  advantage definition check: own_minus_cross reproduced from "
        f"pairs/cross_model_table.csv for {n} (actor x stimulus) cells, "
        f"max |diff| vs FROZEN_PARAMS.GRADIENT = {worst:.4f}")


# ============================================================== loading =======
def load_stage_c(path, log, confirm_adv=None):
    """Stage C trials for the dose-response design.

    analyze_study2.load() is not reused directly because it REQUIRES pair_id and
    stimulus_level, which the revised design does not have - there are no matched
    HIGH/LOW pairs, there is a stimulus gradient. Everything it does that still
    applies is reused function-for-function: _resolve_aliases, the re-derived
    validity filter, check_partner_naming (with its actor_model_name anchor, which
    catches a crossed partner label - the single most damaging possible runner bug)
    and assign_halves.
    """
    raw = list(csv.DictReader(open(path)))
    if not raw:
        sys.exit(f"{path}: no rows")
    col = A._resolve_aliases(raw[0].keys())
    req = [c for c in S.REQUIRED if c not in ("pair_id", "stimulus_level")]
    missing = [c for c in req if c not in col]
    if missing:
        sys.exit(f"{path}: missing required column(s) {missing}\n"
                 f"  present: {sorted(raw[0].keys())}\n"
                 f"  see study2_schema.py (DOSE_COLS) for the revised schema")

    disagree, kept = 0, []
    for r in raw:
        derived = (not A._truthy(r[col["superseded_by_retry"]])) and \
                  A._truthy(r[col["valid_response"]])
        if derived != A._truthy(r[col["included_in_analysis"]]):
            disagree += 1
        if derived:
            kept.append(r)
    if disagree:
        sys.exit(f"REFUSING TO RUN: {disagree} rows where included_in_analysis != "
                 "(not superseded_by_retry) and valid_response.")
    log(f"  {len(raw)} raw rows -> {len(kept)} valid, non-superseded trials "
        "(included_in_analysis re-derived and confirmed)")

    tiers = tier_map()
    out, bad_partner, runner_adv = [], 0, defaultdict(set)
    names, self_names = defaultdict(set), defaultdict(set)
    for r in kept:
        actor = str(r[col["actor_model"]]).strip().lower()
        sid = r[col["stimulus"]]
        w = str(r[col["partner_condition"]]).strip().lower()
        if w not in S.PARTNERS:
            bad_partner += 1
            continue
        if "partner_model_named" in col:
            names[(actor, w)].add(str(r[col["partner_model_named"]]).strip())
            if "actor_model_name" in col:
                self_names[actor].add(str(r[col["actor_model_name"]]).strip())
        if "compatibility_advantage" in col and str(r[col["compatibility_advantage"]]).strip():
            runner_adv[(actor, sid)].add(round(float(r[col["compatibility_advantage"]]), 6))
        tier = (str(r[col["tier"]]).strip() if "tier" in col and str(r[col["tier"]]).strip()
                else tiers.get((actor, sid), ""))
        dec = str(r[col["participation_decision"]]).strip().upper()
        out.append(dict(actor=actor, stimulus=sid, partner=w, tier=tier,
                        safe=int(float(r[col["safe_payoff"]])),
                        y=1 if dec == "ATTEMPT" else 0,
                        run_id=r.get(col.get("run_id", "run_id"), ""),
                        variant=r.get(col.get("variant", "variant"), "")))
    if bad_partner:
        log(f"  !! {bad_partner} rows dropped: partner_condition not in {S.PARTNERS}")
    A.check_partner_naming(names, self_names, log)
    if not out:
        sys.exit("no analysable trials after filtering")

    unresolved = sorted({(r["actor"], r["stimulus"]) for r in out if not r["tier"]})
    if unresolved:
        log(f"  !! {len(unresolved)} (actor, stimulus) combinations carry no tier and "
            f"are not in FROZEN_PARAMS.GRADIENT: {unresolved[:6]}")

    # runner column vs the confirmed value: reported, never silently preferred
    if runner_adv and confirm_adv:
        worst, where = 0.0, None
        multi = [k for k, v in runner_adv.items() if len(v) > 1]
        if multi:
            log(f"  !! compatibility_advantage is NOT constant within "
                f"{len(multi)} (actor x stimulus) cells, e.g. {multi[:3]} - the runner "
                "wrote a per-trial value. The confirmed estimate is used regardless.")
        for k, v in runner_adv.items():
            if k in confirm_adv:
                d = abs(sorted(v)[0] - confirm_adv[k])
                if d > worst:
                    worst, where = d, k
        flag = ("  <-- ABOVE study2_schema.ADVANTAGE_TOL"
                if worst > S.ADVANTAGE_TOL else "")
        log(f"  runner compatibility_advantage vs confirmed: max |diff| {worst:.4f} "
            f"at {where}{flag}")
        log("    The ANALYSED value is always the confirmed one - it is the only one "
            "whose sampling error is available to the errors-in-variables model.")

    A.assign_halves(out, lambda r: (r["actor"], r["stimulus"], r["partner"], r["safe"]))
    return out


def counts_of(rows):
    """(actor, stimulus, partner, safe) -> [k, n]. Integers only."""
    c = defaultdict(lambda: [0, 0])
    for r in rows:
        c[(r["actor"], r["stimulus"], r["partner"], r["safe"])][0] += r["y"]
        c[(r["actor"], r["stimulus"], r["partner"], r["safe"])][1] += 1
    return {k: tuple(v) for k, v in sorted(c.items())}


# ============================================ per-stimulus partner effect =====
def partner_effect(cnt, actor, stim):
    """Pooled counts and the same-minus-different risk difference for one stimulus."""
    kk = {w: 0 for w in S.PARTNERS}
    nn = {w: 0 for w in S.PARTNERS}
    for (a, s, w, _sf), (k, n) in cnt.items():
        if a == actor and s == stim:
            kk[w] += k
            nn[w] += n
    ps = kk["same"] / nn["same"] if nn["same"] else float("nan")
    pd = kk["different"] / nn["different"] if nn["different"] else float("nan")
    return dict(k_same=kk["same"], n_same=nn["same"], k_diff=kk["different"],
                n_diff=nn["different"], p_same=ps, p_diff=pd, effect=ps - pd)


def partner_effect_ci(cnt, actor, stim, b, seed):
    """Percentile bootstrap on the per-stimulus partner effect, resampling trials
    within each (partner x payoff) cell - integers throughout, Binomial(n, k/n)."""
    cells = [(w, k, n) for (a, s, w, _sf), (k, n) in cnt.items()
             if a == actor and s == stim and n > 0]
    if not cells:
        return float("nan"), float("nan")
    rng = np.random.default_rng(A._seed(seed, "pe", actor, stim))
    k = np.array([c[1] for c in cells]); n = np.array([c[2] for c in cells])
    same = np.array([c[0] == "same" for c in cells], float)
    K = rng.binomial(n, k / np.maximum(n, 1), size=(b, len(n))).astype(float)
    ns, nd = (n * same).sum(), (n * (1 - same)).sum()
    if not ns or not nd:
        return float("nan"), float("nan")
    d = (K * same).sum(1) / ns - (K * (1 - same)).sum(1) / nd
    return float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))


def perm_partner_stim(cnt, actor, stim, nperm, seed):
    """Exact permutation of the partner label within (stimulus x payoff) strata."""
    st = defaultdict(dict)
    for (a, s, w, sf), (k, n) in cnt.items():
        if a == actor and s == stim:
            st[sf][w] = (k, n)
    rec = [(d["same"], d["different"]) for d in st.values()
           if "same" in d and "different" in d and d["same"][1] and d["different"][1]]
    if not rec:
        return None
    kS = np.array([r[0][0] for r in rec]); nS = np.array([r[0][1] for r in rec])
    kD = np.array([r[1][0] for r in rec]); nD = np.array([r[1][1] for r in rec])

    def stat(a_, b_):
        return a_.sum(-1) / nS.sum() - b_.sum(-1) / nD.sum()

    obs = stat(kS.astype(float), kD.astype(float))
    rng = np.random.default_rng(A._seed(seed, "pestim", actor, stim))
    ks, kd = A._hyper(rng, kS, nS, kD, nD, nperm)
    d = stat(ks.astype(float), kd.astype(float))
    p1, p2 = A._pvals(obs, d)
    return dict(effect=float(obs), p_one=p1, p_two=p2, n_strata=len(rec))


# ================================================== design and estimation =====
class Design:
    """Cell-level design matrix for the trial-level model.

    Rows are (actor, stimulus, partner, payoff) cells; weights are the cell n, so
    weighted least squares here IS trial-level OLS on the 0/1 outcome, and IRLS here
    IS trial-level logistic regression. Working in 128 cells rather than ~3000 trials
    is what makes 20 000 exact permutation replicates free.

    Columns, in order:
        mu[(actor, stimulus)]              one-hot stimulus fixed effects
        bS[actor] * (SAFE - SAFEbar)       payoff response, per actor
        g0[actor] * SAME                   MODEL A's constant same-model shift
        g1 * SAME * advantage              MODEL B's dose-response       <- PRIMARY
      optionally
        gSP[actor] * SAME * (SAFE-SAFEbar) Partner x SAFE, the robustness variant
    """

    def __init__(self, cnt, adv, model="B", actors=None, drop_stimuli=(),
                 partner_x_safe=False, per_actor_g1=False):
        cells = [(a, s, w, sf, k, n) for (a, s, w, sf), (k, n) in sorted(cnt.items())
                 if n > 0 and s not in drop_stimuli
                 and (actors is None or a in actors) and (a, s) in adv]
        if not cells:
            raise ValueError("no cells")
        self.cells = cells
        self.actors = sorted({c[0] for c in cells})
        self.keys = sorted({(c[0], c[1]) for c in cells})
        self.stimuli = sorted({c[1] for c in cells})
        self.k = np.array([c[4] for c in cells], float)
        self.n = np.array([c[5] for c in cells], float)
        self.y = self.k / self.n
        self.same = np.array([c[2] == "same" for c in cells], float)
        sf = np.array([c[3] for c in cells], float)
        self.sbar = float(np.average(sf, weights=self.n))
        self.sc = sf - self.sbar
        self.aidx = np.array([self.actors.index(c[0]) for c in cells])
        self.kidx = np.array([self.keys.index((c[0], c[1])) for c in cells])
        self.adv = np.array([adv[(c[0], c[1])] for c in cells])
        self.model = model
        self.partner_x_safe = partner_x_safe
        self.per_actor_g1 = per_actor_g1 and len(self.actors) > 1
        self.names = ([f"mu[{a}|{s}]" for a, s in self.keys]
                      + [f"bS[{a}]" for a in self.actors])
        if model in ("A", "B"):
            self.names += [f"g0[{a}]" for a in self.actors]
            if partner_x_safe:
                self.names += [f"gSP[{a}]" for a in self.actors]
        if model == "B":
            self.names += ([f"g1[{a}]" for a in self.actors] if self.per_actor_g1
                           else ["g1"])
        self.X = self._build(self.adv)
        self.g1_cols = [i for i, nm in enumerate(self.names) if nm.startswith("g1")]

    def _build(self, adv):
        nc = len(self.cells)
        blocks = [np.eye(len(self.keys))[self.kidx],
                  np.eye(len(self.actors))[self.aidx] * self.sc[:, None]]
        if self.model in ("A", "B"):
            blocks.append(np.eye(len(self.actors))[self.aidx] * self.same[:, None])
            if self.partner_x_safe:
                blocks.append(np.eye(len(self.actors))[self.aidx]
                              * (self.same * self.sc)[:, None])
        if self.model == "B":
            if self.per_actor_g1:
                blocks.append(np.eye(len(self.actors))[self.aidx]
                              * (self.same * adv)[:, None])
            else:
                blocks.append((self.same * adv)[:, None])
        return np.hstack(blocks)

    def with_adv(self, adv_vec):
        """Same design, a different draw of the latent advantage (EIV / bootstrap)."""
        return self._build(adv_vec)

    def adv_vector(self, adv_map):
        return np.array([adv_map[(c[0], c[1])] for c in self.cells])

    # ---- weighted least squares == trial-level OLS on the 0/1 outcome --------
    def hat(self, X=None):
        X = self.X if X is None else X
        W = self.n
        XtWX = X.T @ (X * W[:, None])
        return np.linalg.solve(XtWX + 1e-10 * np.eye(X.shape[1]), X.T * W)

    def wls(self, X=None, y=None):
        H = self.hat(X)
        return H @ (self.y if y is None else y), H

    def rank_ok(self, X=None):
        X = self.X if X is None else X
        Xw = X * np.sqrt(self.n)[:, None]
        return int(np.linalg.matrix_rank(Xw)) == X.shape[1]


def irls(X, k, n, iters=200, ridge=1e-6, tol=1e-10, pen=None):
    """Binomial IRLS on cell counts == trial-level logistic regression.

    A tiny ridge keeps the fit finite when a cell is at 0 or n (the ceiling controls
    proto and s_arrow can sit there). It shifts the log-likelihood by less than 1e-6
    and is reported if any coefficient still runs away.
    """
    p_ = X.shape[1]
    P = ridge * np.eye(p_) if pen is None else np.diag(np.asarray(pen, float))
    beta = np.zeros(p_)
    for _ in range(iters):
        eta = np.clip(X @ beta, -30, 30)
        mu = 1.0 / (1.0 + np.exp(-eta))
        W = np.maximum(n * mu * (1 - mu), 1e-9)
        z = eta + (k - n * mu) / W
        XtW = X.T * W
        new = np.linalg.solve(XtW @ X + P, XtW @ z)
        if np.max(np.abs(new - beta)) < tol:
            beta = new
            break
        beta = new
    eta = np.clip(X @ beta, -30, 30)
    mu = np.clip(1.0 / (1.0 + np.exp(-eta)), 1e-12, 1 - 1e-12)
    ll = float(np.sum(k * np.log(mu) + (n - k) * np.log(1 - mu)))
    W = np.maximum(n * mu * (1 - mu), 1e-9)
    cov = np.linalg.inv((X.T * W) @ X + P)
    return beta, ll, cov


def loglik_cells(X, beta, k, n):
    eta = np.clip(X @ beta, -30, 30)
    mu = np.clip(1.0 / (1.0 + np.exp(-eta)), 1e-12, 1 - 1e-12)
    return float(np.sum(k * np.log(mu) + (n - k) * np.log(1 - mu)))


# ======================================================== slope inference =====
def slope_plugin(D):
    """WLS slope, its permutation p, and its bootstrap CIs. All from the counts."""
    beta, H = D.wls()
    h = H[D.g1_cols]                      # g1 is a FIXED linear functional of y
    return beta, h


def perm_slope(D, nperm, seed):
    """Permute PARTNER within (actor x stimulus x payoff); recompute g1.

    The design matrix and every cell n are invariant under this permutation, so
    g1* = h @ y* exactly, and 20 000 exact hypergeometric replicates cost one matmul.
    """
    beta, h = slope_plugin(D)
    idx = {}
    for i, (a, s, w, sf, _k, _n) in enumerate(D.cells):
        idx.setdefault((a, s, sf), {})[w] = i
    rec = [(d["same"], d["different"]) for d in idx.values()
           if "same" in d and "different" in d]
    if not rec:
        return None
    iS = np.array([r[0] for r in rec]); iD = np.array([r[1] for r in rec])
    kS, nS = D.k[iS], D.n[iS]
    kD, nD = D.k[iD], D.n[iD]
    rng = np.random.default_rng(A._seed(seed, "slope", tuple(D.actors),
                                        tuple(D.stimuli), D.model))
    ks, kd = A._hyper(rng, kS.astype(int), nS.astype(int),
                      kD.astype(int), nD.astype(int), nperm)
    Y = np.tile(D.y, (nperm, 1))
    Y[:, iS] = ks / nS
    Y[:, iD] = kd / nD
    draws = Y @ h.T                                     # (nperm, n_g1)
    out = []
    for j, c in enumerate(D.g1_cols):
        p1, p2 = A._pvals(beta[c], draws[:, j])
        out.append(dict(name=D.names[c], obs=float(beta[c]), p_one=p1, p_two=p2,
                        null_sd=float(np.std(draws[:, j])), n_strata=len(rec),
                        n_perm=nperm))
    return out


def boot_slope_trials(D, b, seed):
    """Plug-in CI: resample trials within cells. advantage held at its point value."""
    _beta, h = slope_plugin(D)
    rng = np.random.default_rng(A._seed(seed, "boottrial", tuple(D.stimuli), D.model))
    K = rng.binomial(D.n.astype(int), D.y, size=(b, len(D.n))).astype(float)
    draws = (K / D.n) @ h.T
    return draws


def boot_slope_stagea(D, adv_map_keys, cc, b, seed):
    """PLUG-IN + STAGE A: resample the confirmation counts AND the Stage C trials.

    This is uncertainty propagation, not bias correction. The interval widens; the
    centre stays attenuated. Said in the log every time it is printed.
    """
    rng = np.random.default_rng(A._seed(seed, "bootA", tuple(D.stimuli), D.model))
    stim = sorted({s for (_m, s) in cc})
    advd = advantage_draws(cc, stim, b, rng, mode="bootstrap")
    sidx = {s: i for i, s in enumerate(stim)}
    K = rng.binomial(D.n.astype(int), D.y, size=(b, len(D.n))).astype(float)
    Y = K / D.n
    out = np.empty((b, len(D.g1_cols)))
    ai = np.array([MODELS.index(c[0]) for c in D.cells])
    si = np.array([sidx[c[1]] for c in D.cells])
    for i in range(b):
        Xi = D.with_adv(advd[i][ai, si])
        H = D.hat(Xi)
        out[i] = (H @ Y[i])[D.g1_cols]
    return out


def regression_calibration(D, cc, seed, b=2000):
    """Method-of-moments attenuation correction. Closed form, a check on the EIV.

    reliability = (Var(adv_hat) - mean SE^2) / Var(adv_hat), variances taken over the
    (actor x stimulus) points that actually carry the slope, weighted by the leverage
    the design gives them. Returns (reliability, corrected slope, mean SE).
    """
    rng = np.random.default_rng(A._seed(seed, "regcal"))
    stim = sorted({s for (_m, s) in cc})
    advd = advantage_draws(cc, stim, b, rng, mode="bootstrap")
    sidx = {s: i for i, s in enumerate(stim)}
    pts = sorted({(c[0], c[1]) for c in D.cells})
    se2, xs = [], []
    for a, s in pts:
        v = advd[:, MODELS.index(a), sidx[s]]
        se2.append(float(np.var(v, ddof=1)))
        xs.append(float(np.mean(v)))
    vx = float(np.var(xs, ddof=1)) if len(xs) > 1 else float("nan")
    lam = (vx - float(np.mean(se2))) / vx if vx > 0 else float("nan")
    return lam, float(np.sqrt(np.mean(se2))), vx


# ============================================================ EIV sampler =====
def _split_rhat_ess(chains):
    """Split R-hat and bulk ESS. arviz if importable, else computed here.

    chains: (n_chain, n_draw) for ONE scalar.
    """
    try:
        import arviz as az
        return float(az.rhat(chains)), float(az.ess(chains))
    except Exception:                                       # pragma: no cover
        c, d = chains.shape
        h = d // 2
        sp = np.concatenate([chains[:, :h], chains[:, h:2 * h]], 0)
        m, nn = sp.shape
        means, varis = sp.mean(1), sp.var(1, ddof=1)
        B = nn * np.var(means, ddof=1)
        W = np.mean(varis)
        var = ((nn - 1) / nn) * W + B / nn
        return float(np.sqrt(var / W)) if W > 0 else float("nan"), float(m * nn / 10)


def eiv_gate(D, cc, log):
    """Gates run BEFORE any sampling, in the style of analyze_study2's Study 1 lesson."""
    npar = D.X.shape[1] + 2 * len(D.stimuli)      # outcome params + 16 latent pi
    ncell = len(D.cells) + 2 * len(D.stimuli)     # Stage C cells + Stage A cells
    log("\n  EIV IDENTIFIABILITY GATE (before sampling)")
    log(f"    Stage C cells {len(D.cells)} + Stage A cells {2*len(D.stimuli)} "
        f"= {ncell} data cells;  free parameters {npar} "
        f"({D.X.shape[1]} outcome + {2*len(D.stimuli)} latent pi)")
    g1 = npar < ncell
    log(f"    GATE E1  params < cells                         : {'PASS' if g1 else 'FAIL'}")
    g2 = D.rank_ok()
    log(f"    GATE E2  outcome design matrix full rank ({D.X.shape[1]} cols) : "
        f"{'PASS' if g2 else 'FAIL - structurally unidentified'}")
    g3 = True
    for a in D.actors:
        advs = sorted({round(float(D.adv[i]), 6) for i, c in enumerate(D.cells)
                       if c[0] == a})
        arms = {c[2] for c in D.cells if c[0] == a}
        ok = len(advs) >= 3 and arms == set(S.PARTNERS)
        g3 &= ok
        log(f"    GATE E3  {a:7} {len(advs)} distinct advantage values, arms "
            f"{sorted(arms)} : {'PASS' if ok else 'FAIL - the slope is not identified'}")
    missing = [k for k in {(c[0], c[1]) for c in D.cells}
               if (k[0], k[1]) not in {(m, s) for (m, s) in cc}]
    g4 = not [s for s in D.stimuli if any((m, s) not in cc for m in MODELS)]
    log(f"    GATE E4  confirmation counts present for BOTH models on all "
        f"{len(D.stimuli)} stimuli : {'PASS' if g4 else 'FAIL'}")
    log("      (cross[s] needs both marginals; one missing makes advantage undefined "
        "for BOTH actors on that stimulus, not just one)")
    ok = g1 and g2 and g3 and g4
    if not ok:
        log("    -> REFUSING to run the EIV model. Nothing downstream substitutes a "
            "plug-in number for it silently.")
    return ok


def eiv_fit(D, cc, log, draws=3000, warmup=1000, chains=4, seed=SEED):
    """Full joint Bayesian errors-in-variables fit.

    MODEL
        Stage A   k[m,s] ~ Binomial(n[m,s], pi[m,s]),  pi[m,s] ~ Uniform(0, 1)
        latent    own[m,s] = pi^2 + (1-pi)^2
                  cross[s] = pi_g pi_c + (1-pi_g)(1-pi_c)
                  adv[m,s] = own[m,s] - cross[s]                      deterministic
        Stage C   k ~ Binomial(n, sigmoid(mu[a,s] + bS[a]*(S-Sbar)
                                          + SAME*(g0[a] + g1*adv[a,s])))
        priors    mu ~ N(0, 2.5), bS ~ N(0, 1), g0 ~ N(0, 1), g1 ~ N(0, 2)

    advantage is LATENT here, so g1 is not diluted by the confirmation screen's
    sampling error. That is the whole reason this model exists.

    SAMPLER. pymc is not importable in this environment (numpy ABI clash) and the
    primary analysis must not depend on an optional package, so the sampler is
    written out. It is two INDEPENDENCE Metropolis-Hastings blocks, not a random
    walk, because each block has an almost-exact proposal available:

      pi | theta   proposed one coordinate at a time from Beta(1 + k, 1 + n - k),
                   which is EXACTLY the conditional posterior of pi under Stage A
                   alone. The Stage A likelihood and the uniform prior cancel
                   identically against the proposal density, so the acceptance ratio
                   is just the Stage C likelihood ratio - and Stage C depends on pi
                   only through g1*SAME*adv, because mu[a,s] absorbs everything about
                   a stimulus's level. Acceptance is therefore near 1 and the draws
                   are nearly independent.
      theta | pi   proposed from the Laplace approximation at the current advantage:
                   penalised IRLS gives the exact MAP and its Hessian, and the
                   proposal is N(MAP, Hessian^-1). With ~3000 trials the logistic
                   posterior is very close to Gaussian, so acceptance is again high
                   and the draws are nearly independent.

    An earlier random-walk version of this sampler was written, run, and DISCARDED:
    it gave min bulk ESS of 5 at 400 draws and GATE E5 refused to report it. That is
    the gate doing its job, and the fix was a better kernel, not a lower bar.

    WHAT THE EIV BUYS, STATED HONESTLY. Because adv enters only through the
    interaction term, Stage C carries very little information about pi and the
    posterior for adv is dominated by Stage A. So the EIV and the simple
    posterior-propagation calculation should agree closely; both are computed and
    printed, and a disagreement would mean something is wrong, not interesting.
    """
    stim = D.stimuli
    sidx = {s: i for i, s in enumerate(stim)}
    kA = np.array([[cc[(m, s)][0] for s in stim] for m in MODELS], float)
    nA = np.array([[cc[(m, s)][1] for s in stim] for m in MODELS], float)
    ai = np.array([MODELS.index(c[0]) for c in D.cells])
    si = np.array([sidx[c[1]] for c in D.cells])
    kC, nC = D.k, D.n
    npar = D.X.shape[1]
    g1c = D.g1_cols

    prior_sd = np.ones(npar)
    for i, nm in enumerate(D.names):
        prior_sd[i] = 2.5 if nm.startswith("mu") else 1.0
        if nm.startswith("g1"):
            prior_sd[i] = 2.0
    pen = 1.0 / prior_sd ** 2

    def adv_of(pi):
        own = pi ** 2 + (1 - pi) ** 2
        cr = pi[0] * pi[1] + (1 - pi[0]) * (1 - pi[1])
        return own - cr[None, :]

    def llC(theta, advm):
        eta = np.clip(D.with_adv(advm[ai, si]) @ theta, -30, 30)
        mu = np.clip(1.0 / (1.0 + np.exp(-eta)), 1e-12, 1 - 1e-12)
        return float(np.sum(kC * np.log(mu) + (nC - kC) * np.log(1 - mu)))

    def logprior(theta):
        return -0.5 * float(np.sum((theta / prior_sd) ** 2))

    log(f"\n  EIV sampler: {chains} chains x ({warmup} warmup + {draws} kept), "
        f"{npar} outcome parameters + {kA.size} latent pi; two independence-MH blocks")
    keep_t = np.empty((chains, draws, npar))
    keep_a = np.empty((chains, draws, kA.size))
    acc_rep = []
    for ch in range(chains):
        rng = np.random.default_rng(A._seed(seed, "eiv2", ch))
        pi = rng.beta(1.0 + kA, 1.0 + nA - kA)
        advm = adv_of(pi)
        m0, _ll, C0 = irls(D.with_adv(advm[ai, si]), kC, nC, pen=pen)
        L0 = np.linalg.cholesky(C0 + 1e-10 * np.eye(npar))
        Ci = np.linalg.inv(C0 + 1e-10 * np.eye(npar))
        th = m0 + L0 @ rng.standard_normal(npar)
        cur_ll = llC(th, advm)
        a_t = a_p = 0
        tot = warmup + draws
        for it in range(tot):
            # ---- pi | theta : independence MH from the exact Stage A conditional
            for r in range(2):
                for c in range(len(stim)):
                    old_v = pi[r, c]
                    pi[r, c] = rng.beta(1.0 + kA[r, c], 1.0 + nA[r, c] - kA[r, c])
                    adv_p = adv_of(pi)
                    new_ll = llC(th, adv_p)
                    if math.log(rng.random() + 1e-300) < new_ll - cur_ll:
                        cur_ll, advm, a_p = new_ll, adv_p, a_p + 1
                    else:
                        pi[r, c] = old_v
            # ---- theta | pi : independence MH from the Laplace approximation
            Xa = D.with_adv(advm[ai, si])
            m0, _ll, C0 = irls(Xa, kC, nC, pen=pen)
            C0 = C0 + 1e-10 * np.eye(npar)
            L0 = np.linalg.cholesky(C0)
            Ci = np.linalg.inv(C0)
            prop = m0 + L0 @ rng.standard_normal(npar)
            new_ll = llC(prop, advm)
            d_old, d_new = th - m0, prop - m0
            lr = ((new_ll + logprior(prop) + 0.5 * float(d_new @ Ci @ d_new))
                  - (cur_ll + logprior(th) + 0.5 * float(d_old @ Ci @ d_old)))
            if math.log(rng.random() + 1e-300) < lr:
                th, cur_ll, a_t = prop, new_ll, a_t + 1
            if it == warmup:
                a_t = a_p = 0
            if it >= warmup:
                keep_t[ch, it - warmup] = th
                keep_a[ch, it - warmup] = advm.ravel()
        acc_rep.append((a_t / draws, a_p / (draws * kA.size)))
        log(f"    chain {ch}: independence-MH acceptance  theta {acc_rep[-1][0]:.3f}, "
            f"latent pi {acc_rep[-1][1]:.3f}")

    out = dict(reported=True, chains=chains, draws=draws, warmup=warmup, rows=[])
    worst_rhat, worst_ess = 0.0, 1e9
    for i in range(npar):
        rh, es = _split_rhat_ess(keep_t[:, :, i])
        worst_rhat, worst_ess = max(worst_rhat, rh), min(worst_ess, es)
    for i in range(keep_a.shape[2]):
        if np.ptp(keep_a[:, :, i]) < 1e-12:      # a ceiling control pinned at adv = 0
            continue
        rh, es = _split_rhat_ess(keep_a[:, :, i])
        worst_rhat, worst_ess = max(worst_rhat, rh), min(worst_ess, es)
    accs = [a for a, _ in acc_rep] + [b for _, b in acc_rep]
    ok_acc = all(a >= 0.10 for a in accs)
    clean = worst_rhat < 1.01 and worst_ess > 400 and ok_acc
    log(f"    GATE E5  max split R-hat {worst_rhat:.4f}  min bulk ESS {worst_ess:.0f}  "
        f"acceptance >= 0.10 everywhere {ok_acc} : {'PASS' if clean else 'FAIL'}")
    out.update(max_rhat=worst_rhat, min_ess=worst_ess, acceptance_ok=bool(ok_acc),
               acceptance=[list(map(float, a)) for a in acc_rep])
    if not clean:
        log("    -> REFUSING to report the EIV posterior. The plug-in and "
            "regression-calibration numbers stand on their own and are labelled.")
        out["reported"] = False
        out["reason"] = "sampler diagnostics failed"
        return out

    for c in g1c:
        v = keep_t[:, :, c].ravel()
        w_post = float(np.percentile(v, 95) - np.percentile(v, 5))
        w_pri = float(2 * 1.6449 * prior_sd[c])
        ratio = w_post / w_pri
        flag = "" if ratio < 0.9 else "   <-- PRIOR-DOMINATED / NOT IDENTIFIED BY THE DATA"
        log(f"    EIV {D.names[c]:8} (LOGIT scale) median {np.median(v):+.4f}  "
            f"90% [{np.percentile(v, 5):+.4f}, {np.percentile(v, 95):+.4f}]  "
            f"P(>0)={float((v > 0).mean()):.4f}   prior->post 90% width ratio "
            f"{ratio:.2f}{flag}")
        out["rows"].append(dict(param=D.names[c], scale="logit",
                                median=float(np.median(v)),
                                q05=float(np.percentile(v, 5)),
                                q95=float(np.percentile(v, 95)),
                                q025=float(np.percentile(v, 2.5)),
                                q975=float(np.percentile(v, 97.5)),
                                p_gt0=float((v > 0).mean()),
                                width_ratio_prior_to_post=round(ratio, 4),
                                prior_dominated=bool(ratio >= 0.9)))
    out["theta"] = keep_t
    out["adv"] = keep_a
    out["g1_cols"] = g1c
    return out


def eiv_rd_slope(D, eiv, sub=600, seed=SEED):
    """Push the EIV posterior onto the RISK-DIFFERENCE scale.

    The logit-scale g1 is the model's parameter; the estimand the figure plots and
    the permutation test targets is the slope of the per-stimulus risk difference on
    advantage. For each posterior draw the fitted cell probabilities are turned into
    per-stimulus partner effects and regressed on THAT DRAW'S OWN latent advantage,
    so the latent uncertainty travels with the transformation instead of being
    evaluated at a point.
    """
    th, ad = eiv["theta"], eiv["adv"]
    rng = np.random.default_rng(A._seed(seed, "eivrd"))
    flat_t = th.reshape(-1, th.shape[2])
    flat_a = ad.reshape(-1, ad.shape[2])
    idx = rng.choice(len(flat_t), size=min(sub, len(flat_t)), replace=False)
    stim = D.stimuli
    sidx = {s: i for i, s in enumerate(stim)}
    ai = np.array([MODELS.index(c[0]) for c in D.cells])
    si = np.array([sidx[c[1]] for c in D.cells])
    pts = sorted({(c[0], c[1]) for c in D.cells})
    wts = np.array([1.0 for _ in pts])
    out = []
    for t in idx:
        adv = flat_a[t].reshape(2, len(stim))
        X = D.with_adv(adv[ai, si])
        mu = 1.0 / (1.0 + np.exp(-np.clip(X @ flat_t[t], -30, 30)))
        num = defaultdict(lambda: [0.0, 0.0, 0.0, 0.0])
        for i, c in enumerate(D.cells):
            j = 0 if c[2] == "same" else 2
            num[(c[0], c[1])][j] += mu[i] * D.n[i]
            num[(c[0], c[1])][j + 1] += D.n[i]
        xs, ys, ws = [], [], []
        for a_, s_ in pts:
            v = num[(a_, s_)]
            if v[1] and v[3]:
                xs.append(adv[MODELS.index(a_), sidx[s_]])
                ys.append(v[0] / v[1] - v[2] / v[3])
                ws.append(v[1] + v[3])
        if len(xs) > 2:
            xs = np.asarray(xs); ys = np.asarray(ys); ws = np.asarray(ws)
            Xr = np.column_stack([np.ones_like(xs), xs])
            out.append(float(np.linalg.solve((Xr.T * ws) @ Xr, (Xr.T * ws) @ ys)[1]))
    a = np.asarray(out)
    return dict(median=float(np.median(a)), q025=float(np.percentile(a, 2.5)),
                q975=float(np.percentile(a, 97.5)), p_gt0=float((a > 0).mean()),
                n_draw=len(a))


def eiv_propagate(D, cc, b, seed):
    """Posterior propagation: draw the latent adv from its Stage A posterior, refit.

    This is the cross-check on the joint sampler, not a substitute for it. It is the
    correct posterior for g1 ONLY under the assumption that Stage C carries no
    information about the latent advantage - an assumption the joint fit does not
    need and which the agreement between the two verifies.
    """
    rng = np.random.default_rng(A._seed(seed, "prop"))
    stim = sorted({s for (_m, s) in cc})
    advd = advantage_draws(cc, stim, b, rng, mode="posterior")
    sidx = {s: i for i, s in enumerate(stim)}
    ai = np.array([MODELS.index(c[0]) for c in D.cells])
    si = np.array([sidx[c[1]] for c in D.cells])
    K = rng.binomial(D.n.astype(int), D.y, size=(b, len(D.n))).astype(float)
    Y = K / D.n
    out = np.empty((b, len(D.g1_cols)))
    for i in range(b):
        H = D.hat(D.with_adv(advd[i][ai, si]))
        out[i] = (H @ Y[i])[D.g1_cols]
    return out


# ======================================================= model comparison =====
def fit_models(cnt, adv, actors, drop, partner_x_safe=False):
    """MODEL 0 / A / B on the LOGIT scale, from one shared cell set."""
    fits = {}
    for name, mdl in (("0", "0"), ("A", "A"), ("B", "B")):
        D = Design(cnt, adv, model=mdl, actors=actors, drop_stimuli=drop,
                   partner_x_safe=partner_x_safe and mdl != "0")
        beta, ll, _cov = irls(D.X, D.k, D.n)
        ntr = float(D.n.sum())
        fits[name] = dict(D=D, beta=beta, ll=ll, k=D.X.shape[1],
                          aic=-2 * ll + 2 * D.X.shape[1],
                          bic=-2 * ll + D.X.shape[1] * math.log(ntr), n_trials=ntr)
    return fits


def loso(cnt, adv, actors, drop, log, partner_x_safe=False):
    """Leave-one-stimulus-out predictive log-loss on the held-out SAME cells.

    The held-out stimulus's baseline mu is refitted from its DIFFERENT-partner cells
    only. Those cells contain no partner-effect information, so nothing about the
    quantity being predicted leaks into the baseline - the models are asked exactly
    the design question: given a NEW stimulus whose compatibility advantage you know,
    how much more willing is the actor to enter against a copy of itself?
    """
    stimuli = sorted({s for (_a, s, _w, _sf) in cnt
                      if s not in drop and any((m, s) in adv for m in MODELS)})
    tot = {m: 0.0 for m in ("0", "A", "B")}
    per = []
    for held in stimuli:
        d2 = tuple(drop) + (held,)
        fits = fit_models(cnt, adv, actors, d2, partner_x_safe)
        row = dict(stimulus=held)
        for m in ("0", "A", "B"):
            D = fits[m]["D"]
            beta = fits[m]["beta"]
            nb = {nm: beta[i] for i, nm in enumerate(D.names)}
            ll = 0.0
            ok = True
            for a in (actors or MODELS):
                if (a, held) not in adv:
                    continue
                cells = [((w, sf), k, n) for (aa, s, w, sf), (k, n) in cnt.items()
                         if aa == a and s == held and n > 0]
                if not cells:
                    continue
                diff = [c for c in cells if c[0][0] == "different"]
                same = [c for c in cells if c[0][0] == "same"]
                if not diff or not same:
                    ok = False
                    continue
                bS = nb.get(f"bS[{a}]", 0.0)
                sbar = D.sbar
                # 1-D Newton for the held-out baseline, from the DIFFERENT cells only
                mu0 = 0.0
                for _ in range(60):
                    g = h = 0.0
                    for (w, sf), k, n in diff:
                        p = 1.0 / (1.0 + math.exp(-max(-30, min(30,
                                   mu0 + bS * (sf - sbar)))))
                        g += k - n * p
                        h += n * p * (1 - p)
                    step = g / max(h, 1e-9)
                    mu0 += max(-2.0, min(2.0, step))
                    if abs(step) < 1e-10:
                        break
                for (w, sf), k, n in same:
                    eta = mu0 + bS * (sf - sbar)
                    if m in ("A", "B"):
                        eta += nb.get(f"g0[{a}]", 0.0)
                        if partner_x_safe:
                            eta += nb.get(f"gSP[{a}]", 0.0) * (sf - sbar)
                    if m == "B":
                        g1 = nb.get("g1", nb.get(f"g1[{a}]", 0.0))
                        eta += g1 * adv[(a, held)]
                    p = 1.0 / (1.0 + math.exp(-max(-30, min(30, eta))))
                    p = min(max(p, 1e-12), 1 - 1e-12)
                    ll += k * math.log(p) + (n - k) * math.log(1 - p)
            row[m] = -ll if ok else float("nan")
            if ok:
                tot[m] += -ll
        per.append(row)
    return tot, per


# ============================================================ reporting =======
def fmt_slope(name, val, ci, p=None, extra=""):
    s = f"      {name:38} {val:+.4f}"
    if ci is not None:
        s += f"  95% [{ci[0]:+.4f}, {ci[1]:+.4f}]"
    if p is not None:
        s += f"  perm p(1-sided)={p:.4f}"
    return s + extra


def baseline_artefact(fits, D_B, adv, log):
    """How much RD slope a purely logit-constant MODEL A manufactures by itself.

    Takes the FITTED MODEL A, reads off the per-stimulus risk difference it implies,
    and regresses those on advantage. That number is the ceiling on how much of the
    observed risk-difference slope a coarse identity heuristic could produce through
    the logit->risk-difference nonlinearity alone.
    """
    D = fits["A"]["D"]
    beta = fits["A"]["beta"]
    mu = 1.0 / (1.0 + np.exp(-np.clip(D.X @ beta, -30, 30)))
    num = defaultdict(lambda: [0.0, 0.0, 0.0, 0.0])
    for i, c in enumerate(D.cells):
        j = 0 if c[2] == "same" else 2
        num[(c[0], c[1])][j] += mu[i] * D.n[i]
        num[(c[0], c[1])][j + 1] += D.n[i]
    xs, ys = [], []
    for (a, s), v in sorted(num.items()):
        if v[1] and v[3] and (a, s) in adv:
            xs.append(adv[(a, s)])
            ys.append(v[0] / v[1] - v[2] / v[3])
    if len(xs) < 3:
        return float("nan"), xs, ys
    return float(np.polyfit(np.asarray(xs), np.asarray(ys), 1)[0]), xs, ys


# ================================================================== main =====
def resolve_confirm(d):
    for pat in S.CONFIRM_GLOBS:
        f = [x for x in glob.glob(os.path.join(d, pat)) if "_DRY" not in x]
        if f:
            return max(f, key=os.path.getmtime)
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=None)
    ap.add_argument("--confirm", default=None,
                    help="confirmation-screen counts (per-trial or aggregated); "
                         "default resolves ../data via study2_schema.CONFIRM_GLOBS")
    ap.add_argument("--out-dir", default=os.path.join(EXP, "analysis"))
    ap.add_argument("--sample", default="full", choices=["full", "holdout", "select"],
                    help="PRIMARY reported sample. FULL by default - see the module "
                         "docstring for why this departs from the interaction analysis")
    ap.add_argument("--perm", type=int, default=PERM)
    ap.add_argument("--boot", type=int, default=BOOT)
    ap.add_argument("--eiv-draws", type=int, default=1500)
    ap.add_argument("--eiv-warmup", type=int, default=500)
    ap.add_argument("--eiv-chains", type=int, default=4)
    ap.add_argument("--no-eiv", action="store_true")
    ap.add_argument("--allow-provisional", action="store_true",
                    help="run with FROZEN_PARAMS.GRADIENT's provisional advantages "
                         "when no confirmation counts exist. EIV is DISABLED - "
                         "provisional values carry no sampling error to propagate.")
    ap.add_argument("--tag", default="")
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    LOG = []

    def log(*a):
        s = " ".join(str(x) for x in a)
        print(s, flush=True)
        LOG.append(s)

    for t in F.FORBIDDEN_TERMS:
        assert t not in __doc__.lower(), t

    path = args.data or A.resolve_data(os.path.join(EXP, "data"))
    if not path:
        sys.exit("no Study 2 CSV found (pass --data)")

    log("=" * 79)
    log("STUDY 2 (revised) - COMPATIBILITY DOSE-RESPONSE   [frozen primary analysis]")
    log("=" * 79)
    log(f"  data   : {path}")
    log(f"  schema : {S.assert_matches_psc_common()}")
    log(f"  frozen : FROZEN_PARAMS.py  advantage={F.ADVANTAGE_DEF}  "
        f"primary coefficient={F.PRIMARY_COEF}  models={F.MODEL_COMPARISON}")
    reproduce_battery(log)

    # ---------------------------------------------- advantage, from Stage A ---
    cpaths = [args.confirm] if args.confirm else (
        [os.path.join(EXP, "design", "confirmed_compatibility.csv")]
        + [resolve_confirm(d) for d in (os.path.join(EXP, "data"),
                                        os.path.join(EXP, "data", "confirmation", "data"),
                                        EXP)])
    cc, csrc = load_confirm([p for p in cpaths if p], log)
    prov = provisional_advantage()
    eiv_possible = bool(cc)
    if cc:
        stimuli = sorted({s for (_m, s) in cc})
        need = sorted({s for (_m, s) in prov})
        miss = [s for s in need if any((m, s) not in cc for m in MODELS)]
        if miss:
            log(f"  !! confirmation counts missing for {miss}; those stimuli cannot "
                "enter the analysis (cross[s] needs BOTH marginals)")
        stimuli = [s for s in need if s not in miss]
        pt = advantage_point(cc, stimuli)
        adv = {k: v for k, v in pt["adv"].items()}
        log(f"\n  CONFIRMED advantage (own-copy minus cross-model), from {csrc}:")
        log(f"      {'stimulus':14}{'tier(gpt)':12}{'n':>6}{'own_gpt':>9}{'own_cla':>9}"
            f"{'cross':>9}{'adv_gpt':>9}{'adv_cla':>9}{'prov_gpt':>10}{'prov_cla':>10}")
        tm = tier_map()
        for s in stimuli:
            log(f"      {s:14}{tm.get(('gpt', s), ''):12}{cc[('gpt', s)][1]:>6}"
                f"{pt['own'][('gpt', s)]:>9.4f}{pt['own'][('claude', s)]:>9.4f}"
                f"{pt['cross'][s]:>9.4f}{adv[('gpt', s)]:>+9.4f}"
                f"{adv[('claude', s)]:>+9.4f}{prov.get(('gpt', s), float('nan')):>+10.3f}"
                f"{prov.get(('claude', s), float('nan')):>+10.3f}")
        rng0 = np.random.default_rng(A._seed(SEED, "advse"))
        d0 = advantage_draws(cc, stimuli, 3000, rng0, mode="bootstrap")
        ses = {(m, s): float(np.std(d0[:, i, j], ddof=1))
               for i, m in enumerate(MODELS) for j, s in enumerate(stimuli)}
        log("      SE(advantage) from a parametric bootstrap of the confirmation "
            "counts: " + ", ".join(f"{s}={max(ses[('gpt', s)], ses[('claude', s)]):.4f}"
                                   for s in stimuli))
        # gate on sign / order of the critical tiers, FROZEN_PARAMS section 4
        # A "sign flip" only means something when there is a sign to flip. The
        # zero_floor tier sits at advantage ~ 0 BY DESIGN, so its sign is noise and
        # a gate that fired on it would fire on almost every honest replication. The
        # check is therefore applied only where the provisional value AND the
        # confirmed value are both resolved from zero by their own measurement error.
        bad, unresolved_sign = [], []
        for m in MODELS:
            for sid, pa, tier, _n in F.GRADIENT[m]:
                if tier not in F.GATE_CRITICAL_TIERS or (m, sid) not in adv:
                    continue
                se = ses.get((m, sid), 0.0)
                resolved = abs(pa) > 2 * se and abs(adv[(m, sid)]) > 2 * se
                if not resolved:
                    unresolved_sign.append((m, sid, tier, round(pa, 3),
                                            round(adv[(m, sid)], 4), round(se, 4)))
                elif np.sign(adv[(m, sid)]) != np.sign(pa):
                    bad.append((m, sid, pa, round(adv[(m, sid)], 4)))
        if unresolved_sign:
            log(f"  confirmation gate: {len(unresolved_sign)} critical cells sit within "
                "2 SE of zero, so their SIGN is not resolved and is not gated on "
                "(the zero_floor tier is at advantage ~ 0 by design):")
            for u in unresolved_sign:
                log(f"      {u[0]:7}{u[1]:14}{u[2]:12} provisional {u[3]:+.3f}  "
                    f"confirmed {u[4]:+.4f}  SE {u[5]:.4f}")
        if bad:
            log(f"  !! CONFIRMATION GATE (FROZEN_PARAMS section 4): SIGN FLIPPED in a "
                f"critical tier {F.GATE_CRITICAL_TIERS}: {bad}")
            log("     The frozen gate says do not proceed to Stage C. Analysing "
                "existing Stage C data anyway is reported, but flagged here.")
        else:
            log(f"  confirmation gate: sign holds in every critical tier "
                f"{F.GATE_CRITICAL_TIERS}")
    elif args.allow_provisional:
        adv = dict(prov)
        ses = {}
        stimuli = sorted({s for (_m, s) in prov})
        log("\n  !! NO CONFIRMATION COUNTS FOUND. Running on FROZEN_PARAMS.GRADIENT's "
            "PROVISIONAL advantages (n=60 Stage A battery, 2026-08-12).")
        log("     These have NO sampling error attached, so the EIV model is DISABLED "
            "and every slope below is a plug-in slope. " + ATTENUATION_NOTE)
    else:
        ses = {}
        sys.exit("no confirmation-screen counts found and --allow-provisional not "
                 "given.\n  The confirmed advantage is the analysed value (see "
                 "FROZEN_PARAMS section 4 and study2_schema.CONFIRM_GLOBS); the "
                 "analysis will not silently substitute the provisional gradient.")

    rows = load_stage_c(path, log, confirm_adv=adv)
    actors = sorted({r["actor"] for r in rows})
    halves = Counter(r["_half"] for r in rows)
    log(f"  actors : {', '.join(S.DISPLAY.get(a, a) for a in actors)}")
    log(f"  split  : select {halves['select']}, holdout {halves['holdout']} trials")
    log(f"  PRIMARY reported sample: {args.sample.upper()}")

    cell_out, stim_out, slope_out, cmp_out, eiv_out = [], [], [], [], []
    eiv_json, fit_draws = {}, []

    for samp in ("full", "holdout", "select"):
        sub = rows if samp == "full" else [r for r in rows if r["_half"] == samp]
        if not sub:
            continue
        primary = samp == args.sample
        cnt = counts_of(sub)
        log("\n" + "=" * 79)
        log(f"SAMPLE = {samp.upper()}  ({len(sub)} trials)"
            + ("   <-- PRIMARY" if primary else "   [secondary, printed for comparison]"))
        log("=" * 79)

        # ---------------- per-stimulus partner effects, raw cells shown --------
        log("\n--- PER-STIMULUS PARTNER EFFECT  P(ATTEMPT|same) - P(ATTEMPT|different) --")
        log("    Raw integer cells are printed, including zero and negative cells. A "
            "rate never appears without the k/n it came from.")
        for a in actors:
            log(f"\n    {S.DISPLAY.get(a, a)}")
            log(f"      {'stimulus':14}{'tier':12}{'adv':>8}"
                f"{'k/n SAME':>14}{'k/n DIFF':>14}{'p_same':>8}{'p_diff':>8}"
                f"{'effect':>9}{'95% CI':>20}{'perm p1':>9}")
            for s in sorted({x[1] for x in cnt if x[0] == a}):
                if (a, s) not in adv:
                    continue
                pe = partner_effect(cnt, a, s)
                lo, hi = partner_effect_ci(cnt, a, s, args.boot, SEED)
                pm = perm_partner_stim(cnt, a, s, args.perm, SEED)
                tier = tier_map().get((a, s), "")
                zero = " ZERO-CELL" if 0 in (pe["k_same"], pe["k_diff"]) else ""
                neg = " NEG" if pe["effect"] < 0 else ""
                log(f"      {s:14}{tier:12}{adv[(a, s)]:>+8.3f}"
                    f"{pe['k_same']:>7}/{pe['n_same']:<6}"
                    f"{pe['k_diff']:>7}/{pe['n_diff']:<6}"
                    f"{pe['p_same']:>8.3f}{pe['p_diff']:>8.3f}{pe['effect']:>+9.4f}"
                    f"  [{lo:+.3f},{hi:+.3f}]"
                    f"{(pm['p_one'] if pm else float('nan')):>9.4f}{zero}{neg}")
                stim_out.append(dict(sample=samp, primary_sample=primary, actor=a,
                                     actor_name=S.DISPLAY.get(a, a), stimulus=s,
                                     tier=tier, advantage=round(adv[(a, s)], 6),
                                     advantage_se=(round(ses[(a, s)], 6)
                                                   if (a, s) in ses else ""),
                                     k_same=pe["k_same"], n_same=pe["n_same"],
                                     k_diff=pe["k_diff"], n_diff=pe["n_diff"],
                                     p_same=round(pe["p_same"], 6),
                                     p_diff=round(pe["p_diff"], 6),
                                     partner_effect=round(pe["effect"], 6),
                                     ci_lo=round(lo, 6), ci_hi=round(hi, 6),
                                     perm_p_one=(round(pm["p_one"], 6) if pm else ""),
                                     perm_p_two=(round(pm["p_two"], 6) if pm else "")))
            for (aa, s, w, sf), (k, n) in cnt.items():
                if aa == a:
                    cell_out.append(dict(sample=samp, primary_sample=primary, actor=a,
                                         stimulus=s, partner=w, safe_payoff=sf,
                                         k_attempt=k, n=n,
                                         attempt_rate=round(k / n, 6) if n else ""))

        # ---------------------------------------------- the primary slope -----
        variants = []
        for label, acts in ([("POOLED (shared g1, actor-specific everything else)", None)]
                            + [(f"{S.DISPLAY.get(a, a)} only", [a])
                               for a in actors if len(actors) > 1]):
            for dl, drop in (("all stimuli", ()),
                             (f"excluding {F.SENSITIVITY_EXCLUDE[0]}",
                              F.SENSITIVITY_EXCLUDE)):
                variants.append((label, acts, dl, drop))

        for label, acts, dl, drop in variants:
            try:
                D = Design(cnt, adv, model="B", actors=acts, drop_stimuli=drop)
            except ValueError:
                continue
            if not D.rank_ok():
                log(f"\n--- {label} / {dl}: design matrix RANK DEFICIENT, refusing to "
                    "fit. Not enough distinct advantage values or a missing arm.")
                continue
            log("\n" + "-" * 79)
            log(f"PRIMARY SLOPE   {label}   [{dl}]   "
                f"{len(D.stimuli)} stimuli, {int(D.n.sum())} trials")
            log("-" * 79)

            beta, _h = slope_plugin(D)
            g1 = float(beta[D.g1_cols[0]])
            bt = boot_slope_trials(D, args.boot, SEED)[:, 0]
            ci_t = (float(np.percentile(bt, 2.5)), float(np.percentile(bt, 97.5)))
            pm = perm_slope(D, args.perm, SEED)
            p1 = pm[0]["p_one"] if pm else float("nan")
            p2 = pm[0]["p_two"] if pm else float("nan")

            log("  RISK-DIFFERENCE SCALE (trial-level OLS with stimulus fixed effects;")
            log("  identical to a precision-weighted regression of the per-stimulus")
            log("  partner effect on advantage - the quantity the main figure plots).")
            log(fmt_slope("g1 PLUG-IN (Partner x Advantage)", g1, ci_t, p1))
            log(f"        two-sided perm p = {p2:.4f}   permutation null SD "
                f"{pm[0]['null_sd']:.4f} over {pm[0]['n_strata']} strata, "
                f"{pm[0]['n_perm']} exact hypergeometric draws")
            log("      " + ATTENUATION_NOTE)
            g0i = [i for i, nm in enumerate(D.names) if nm.startswith("g0")]
            log("      intercepts g0 (the constant same-model shift MODEL A also has): "
                + ", ".join(f"{D.names[i]}={beta[i]:+.4f}" for i in g0i))
            log("      A nonzero g0 is MODEL A's prediction as much as MODEL B's. It is "
                "NOT evidence for a dose-response.")

            if primary and label.startswith("POOLED") and dl == "all stimuli":
                Hh = D.hat()
                rngf = np.random.default_rng(A._seed(SEED, "fitdraw"))
                Kf = rngf.binomial(D.n.astype(int), D.y,
                                   size=(min(args.boot, 4000), len(D.n))).astype(float)
                Bf = (Kf / D.n) @ Hh.T
                cols_f = [i for i, nm in enumerate(D.names)
                          if nm.startswith("g0") or nm.startswith("g1")]
                fit_draws = [dict(draw=i, **{D.names[c]: round(float(Bf[i, c]), 6)
                                             for c in cols_f})
                             for i in range(Bf.shape[0])]
            ci_a = pr = None
            lam = float("nan")
            if eiv_possible:
                ba = boot_slope_stagea(D, None, cc, min(args.boot, 2000), SEED)[:, 0]
                ci_a = (float(np.percentile(ba, 2.5)), float(np.percentile(ba, 97.5)))
                log(fmt_slope("g1 PLUG-IN + STAGE A BOOTSTRAP",
                              float(np.median(ba)), ci_a))
                log("        Propagates the confirmation screen's sampling error. It "
                    "WIDENS the interval and does NOT undo the attenuation - the "
                    "centre is still biased toward zero.")
                lam, mse, vx = regression_calibration(D, cc, SEED)
                log(f"      measurement-error reliability lambda = {lam:.4f}  "
                    f"(Var(adv_hat)={vx:.5f}, mean SE={mse:.4f})")
                log(fmt_slope("g1 REGRESSION-CALIBRATED (g1 / lambda)",
                              g1 / lam if lam and lam == lam else float("nan"), None))
                log(f"        Method of moments. At lambda={lam:.3f} the attenuation "
                    f"is {100*(1-lam):.1f}% - the plug-in slope is that much too flat.")
                pr = eiv_propagate(D, cc, min(args.boot, 1500), SEED)[:, 0]
                log(fmt_slope("g1 POSTERIOR-PROPAGATION (cross-check on the EIV)",
                              float(np.median(pr)),
                              (float(np.percentile(pr, 2.5)),
                               float(np.percentile(pr, 97.5)))))

            # naive OLS on the aggregated points, for the record only
            pts = sorted({(c[0], c[1]) for c in D.cells})
            xs = np.array([adv[p] for p in pts])
            ys = []
            for a_, s_ in pts:
                pe = partner_effect(cnt, a_, s_)
                ys.append(pe["effect"])
            ys = np.asarray(ys)
            ols = float(np.polyfit(xs, ys, 1)[0]) if len(xs) > 2 else float("nan")
            log(f"      naive OLS on the {len(xs)} aggregated per-stimulus points: "
                f"{ols:+.4f}")
            log("        DESCRIPTIVE ONLY, never the analysis. It weights a 32-trial "
                "stimulus the same as a 160-trial one, so it targets the UNWEIGHTED "
                "estimand and is not comparable in size to the weighted slope above; "
                "its sampling variance is also much larger. Attenuation applies to it "
                "as to every plug-in estimate. " + ATTENUATION_NOTE)

            # -------------------------------------- model comparison ----------
            fits = fit_models(cnt, adv, acts, drop)
            lrt = 2 * (fits["B"]["ll"] - fits["A"]["ll"])
            df = fits["B"]["k"] - fits["A"]["k"]
            try:
                from scipy import stats as _st
                plrt = float(_st.chi2.sf(max(lrt, 0.0), df)) if df > 0 else float("nan")
            except Exception:
                plrt = float("nan")
            log(f"\n  MODEL COMPARISON on the LOGIT scale "
                f"({F.MODEL_COMPARISON[0]} vs {F.MODEL_COMPARISON[1]})")
            log(f"      {'model':34}{'params':>8}{'logLik':>12}{'AIC':>11}{'BIC':>11}")
            desc = {"0": "MODEL 0  no partner effect",
                    "A": "MODEL A  constant same-model shift",
                    "B": "MODEL B  shift proportional to advantage"}
            for m in ("0", "A", "B"):
                log(f"      {desc[m]:34}{fits[m]['k']:>8}{fits[m]['ll']:>12.2f}"
                    f"{fits[m]['aic']:>11.2f}{fits[m]['bic']:>11.2f}")
            log(f"      LRT  B vs A: chi2 = {lrt:.3f} on {df} df, p = {plrt:.4f}")
            log(f"      dAIC (A - B) = {fits['A']['aic'] - fits['B']['aic']:+.2f}   "
                f"dBIC (A - B) = {fits['A']['bic'] - fits['B']['bic']:+.2f}   "
                "(positive favours B)")
            tot, per = loso(cnt, adv, acts, drop, log)
            log("      LEAVE-ONE-STIMULUS-OUT predictive log-loss on the held-out "
                "SAME-partner cells")
            log("        (held-out baseline refitted from its DIFFERENT cells only, so "
                "no partner information leaks in)")
            log(f"        MODEL 0 {tot['0']:.2f}   MODEL A {tot['A']:.2f}   "
                f"MODEL B {tot['B']:.2f}   (lower is better)")
            loso_v = ("MODEL B" if tot["B"] < tot["A"] - 1e-9 else
                      "MODEL A" if tot["A"] < tot["B"] - 1e-9 else "tie")
            log(f"        LOSO verdict: {loso_v}  (A - B = {tot['A'] - tot['B']:+.2f} "
                "nats; positive favours B)")
            if tot["A"] >= tot["0"]:
                log("        NOTE: MODEL A does not beat MODEL 0 out of sample, so the "
                    "partner label itself is not predictive here and the A-vs-B "
                    "comparison is between two models neither of which is earning its "
                    "parameters.")

            art, _xs, _ys = baseline_artefact(fits, D, adv, log)
            log(f"\n      BASELINE-ARTEFACT DIAGNOSTIC: the FITTED MODEL A, which has "
                f"no advantage term at all,")
            log(f"      nevertheless implies a risk-difference slope of {art:+.4f} "
                "through the logit -> risk-difference")
            log(f"      nonlinearity alone. Observed plug-in slope {g1:+.4f}; excess "
                f"over the artefact {g1 - art:+.4f}.")
            if abs(art) > 0.25 * abs(g1) and abs(g1) > 1e-6:
                log("      The artefact is a substantial fraction of the observed "
                    "slope. Read the LOGIT-scale model comparison, not the "
                    "risk-difference slope, as the discriminating evidence.")

            VERDICT_TEXT = {
                "A": "MODEL A (coarse identity heuristic)",
                "B": "MODEL B (policy-specific)",
                "none": "NEITHER - no partner effect survives out of sample",
                "tie": "INDISTINGUISHABLE - the models are within the "
                       "out-of-sample noise of each other",
                "ambiguous": "NEITHER decisively"}
            rank = sorted(("0", "A", "B"), key=lambda m: tot[m])
            best, runner = rank[0], rank[1]
            margin = tot[runner] - tot[best]
            log(f"        LOSO winner {best} by {margin:.2f} nats over {runner}; "
                f"anything under {LOSO_TIE_NATS:.0f} nats over ~{int(D.n.sum())} "
                "trials is a tie, not a result, and is reported as one.")
            if margin < LOSO_TIE_NATS:
                verdict = "tie"
            elif best == "0":
                verdict = "none"
            elif best == "B" and p1 < 0.05 and lrt > 0:
                verdict = "B"
            elif best == "A":
                verdict = "A"
            else:
                verdict = "ambiguous"
            log(f"\n      >>> VERDICT [{label} / {dl}]: {VERDICT_TEXT[verdict]}")
            log("          Decision rule, fixed in advance. The leave-one-stimulus-out "
                "winner decides, with MODEL 0 in the race: if the no-partner-effect "
                "model predicts a new stimulus best, neither A nor B has earned "
                "anything. A verdict of B additionally requires one-sided permutation "
                "p < 0.05 on g1 and the likelihood moving the right way. A positive "
                "same-model shift g0 never counts toward B on its own - MODEL A "
                "predicts one too.")

            slope_out.append(dict(
                sample=samp, primary_sample=primary, scope=label, stimulus_set=dl,
                n_stimuli=len(D.stimuli), n_trials=int(D.n.sum()),
                g1_plugin=round(g1, 6),
                g1_plugin_ci_lo=round(ci_t[0], 6), g1_plugin_ci_hi=round(ci_t[1], 6),
                g1_perm_p_one=round(p1, 6), g1_perm_p_two=round(p2, 6),
                g1_stagea_ci_lo=(round(ci_a[0], 6) if ci_a else ""),
                g1_stagea_ci_hi=(round(ci_a[1], 6) if ci_a else ""),
                g1_propagated_median=(round(float(np.median(pr)), 6)
                                      if pr is not None else ""),
                g1_naive_ols=round(ols, 6),
                modelA_rd_slope_artefact=round(art, 6),
                logLik_0=round(fits["0"]["ll"], 4), logLik_A=round(fits["A"]["ll"], 4),
                logLik_B=round(fits["B"]["ll"], 4),
                aic_A=round(fits["A"]["aic"], 3), aic_B=round(fits["B"]["aic"], 3),
                bic_A=round(fits["A"]["bic"], 3), bic_B=round(fits["B"]["bic"], 3),
                lrt_chi2=round(lrt, 4), lrt_df=df, lrt_p=round(plrt, 6),
                loso_0=round(tot["0"], 4), loso_A=round(tot["A"], 4),
                loso_B=round(tot["B"], 4), loso_verdict=loso_v, verdict=verdict,
                n_perm=args.perm, n_boot=args.boot))
            cmp_out.extend([dict(sample=samp, scope=label, stimulus_set=dl, **r)
                            for r in per])

            # ------------------------------------------------ EIV -------------
            DB = fits["B"]["D"]
            g1_logit_plugin = float(fits["B"]["beta"][DB.g1_cols[0]])
            log(f"      LOGIT-scale plug-in g1 (MODEL B's coefficient): "
                f"{g1_logit_plugin:+.4f}   " + ATTENUATION_NOTE.split(":", 1)[1].strip())
            log("        This is the estimate the EIV posterior below is directly "
                "comparable with - same link, same parameterisation, the ONLY "
                "difference being whether advantage is latent or plugged in. The "
                "risk-difference slope above is a different link and the two should "
                "not be differenced against each other.")

            if primary and eiv_possible and not args.no_eiv and dl == "all stimuli":
                log("\n  ERRORS-IN-VARIABLES / LATENT-PREDICTOR MODEL "
                    f"[{label}]")
                if eiv_gate(D, cc, log):
                    ev = eiv_fit(D, cc, log, draws=args.eiv_draws,
                                 warmup=args.eiv_warmup, chains=args.eiv_chains)
                    if ev.get("reported"):
                        rd = eiv_rd_slope(D, ev)
                        log(f"    EIV g1 on the RISK-DIFFERENCE scale (posterior "
                            f"pushed through the fitted probabilities):")
                        log(f"      median {rd['median']:+.4f}  95% "
                            f"[{rd['q025']:+.4f}, {rd['q975']:+.4f}]  "
                            f"P(>0)={rd['p_gt0']:.4f}  ({rd['n_draw']} draws)")
                        ev_med = [r["median"] for r in ev["rows"]
                                  if r["scale"] == "logit"][0]
                        ev_lo = [r["q05"] for r in ev["rows"]
                                 if r["scale"] == "logit"][0]
                        ev_hi = [r["q95"] for r in ev["rows"]
                                 if r["scale"] == "logit"][0]
                        inv_lam = 1 / lam if (lam == lam and lam) else float("nan")
                        log(f"      LIKE-FOR-LIKE (logit scale): plug-in g1 "
                            f"{g1_logit_plugin:+.4f}  ->  EIV g1 {ev_med:+.4f}")
                        resolved = abs(g1_logit_plugin) > 0.5 * (ev_hi - ev_lo)
                        if resolved:
                            log(f"        ratio {ev_med / g1_logit_plugin:.3f}; "
                                f"attenuation predicts roughly 1/lambda = "
                                f"{inv_lam:.3f}.")
                        else:
                            log("        ratio NOT reported: the plug-in estimate is "
                                "smaller than the EIV posterior's own 90% width, so "
                                "the ratio of two near-zero numbers would be noise "
                                f"dressed as a correction. (1/lambda = {inv_lam:.3f}.)")
                        log(f"        Read the size, not the sign of the difference. "
                            f"1/lambda = {inv_lam:.3f} is a {100*(inv_lam-1):.1f}% "
                            "correction, while g1's own posterior is wide "
                            f"({ev_lo:+.3f} to {ev_hi:+.3f} at 90%). The attenuation "
                            "is real and its DIRECTION is not in doubt, but at "
                            "FROZEN_PARAMS.CONFIRM_N it is an order of magnitude "
                            "below the sampling noise, so plug-in and EIV can land "
                            "either side of one another. That is a statement about "
                            "how large the confirmation screen is, not a licence to "
                            "drop the EIV: at the provisional n = 60 the same "
                            "calculation gives a correction several times bigger.")
                        log(f"      For reference the RISK-DIFFERENCE plug-in slope was "
                            f"{g1:+.4f} and the EIV's risk-difference push-through is "
                            f"{rd['median']:+.4f}. These use DIFFERENT links, so their "
                            "difference is not an attenuation correction and is not "
                            "read as one.")
                        for r in ev["rows"]:
                            eiv_out.append(dict(sample=samp, scope=label, **r))
                        eiv_out.append(dict(sample=samp, scope=label,
                                            param="g1_risk_difference", scale="rd",
                                            median=rd["median"], q05="", q95="",
                                            q025=rd["q025"], q975=rd["q975"],
                                            p_gt0=rd["p_gt0"],
                                            width_ratio_prior_to_post="",
                                            prior_dominated=""))
                        eiv_json[label] = {k: v for k, v in ev.items()
                                           if k not in ("rows", "theta", "adv")}
                        eiv_json[label]["rd_slope"] = rd
                    else:
                        eiv_json[label] = {k: v for k, v in ev.items()
                                           if k not in ("rows", "theta", "adv")}
                else:
                    eiv_json[label] = dict(reported=False,
                                           reason="identifiability gate failed")
            elif primary and not eiv_possible and dl == "all stimuli":
                log("\n  ERRORS-IN-VARIABLES MODEL NOT RUN: no confirmation-screen "
                    "counts, so the advantage has no sampling model. Every slope above "
                    "is a plug-in slope. " + ATTENUATION_NOTE)

    # -------------------------------------------------------------- write ----
    tag = f"_{args.tag}" if args.tag else ""

    def dump(name, rowsx):
        if not rowsx:
            return
        p = os.path.join(args.out_dir, name)
        keys = list({k: None for r in rowsx for k in r})
        with open(p, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=keys)
            w.writeheader()
            w.writerows([{k: r.get(k, "") for k in keys} for r in rowsx])
        log(f"  -> {p}")

    log("\n" + "=" * 79)
    dump(f"dose_stimulus_effects{tag}.csv", stim_out)
    dump(f"dose_cells{tag}.csv", cell_out)
    dump(f"dose_slopes{tag}.csv", slope_out)
    dump(f"dose_loso{tag}.csv", cmp_out)
    dump(f"dose_eiv{tag}.csv", eiv_out)
    dump(f"dose_fit_draws{tag}.csv", fit_draws)
    if eiv_json:
        p = os.path.join(args.out_dir, f"dose_eiv_status{tag}.json")
        with open(p, "w") as fh:
            json.dump(eiv_json, fh, indent=2, default=float)
        log(f"  -> {p}")
    lp = os.path.join(args.out_dir, f"dose_analysis_log{tag}.txt")
    with open(lp, "w") as fh:
        fh.write("\n".join(LOG) + "\n")
    print(f"  -> {lp}")


if __name__ == "__main__":
    main()
