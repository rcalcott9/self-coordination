"""
Study 2 runner output schema - the single place the analysis records what it
assumes about the CSV the runner writes.

WHY THIS FILE EXISTS. `analyze_study2.py` and `simulate_study2_data.py` were
written BEFORE the runner (`study2_betting.py`, a sibling agent's deliverable) and
before any data. Freezing the analysis pre-registration means freezing the schema
it consumes. Everything the analysis needs is listed here, so a schema mismatch
shows up as one explicit failure at load time rather than as a silent mis-analysis.

BASE. Study 1's Stage C column list (psc_common.COLS, verbatim) is the base. It is
copied rather than imported because psc_common imports the API clients, dotenv and
two modules from a separate repo; the analysis must run on a machine with no keys.
`assert_matches_psc_common()` checks the copy against the original by PARSING
psc_common.py with `ast` - no import, no side effects - so the copy cannot silently
drift and the check itself needs nothing installed.

STUDY 2 ADDITIONS (the assumptions the analysis makes):

  partner_condition     {"same", "different"}   REQUIRED
      Whether the focal model was told its partner is another instance of the same
      model, or an instance of the other model.

  partner_model_named   free text               REQUIRED (recorded, not analysed)
      The partner's display name as it appeared in the prompt, e.g. "GPT-5.5" or
      "Claude Opus 5". Used only for a consistency check: for actor=gpt the SAME
      rows must name the GPT display string and the DIFFERENT rows the Claude one,
      and vice versa. A crossed-up condition label is the single most damaging
      possible runner bug for this design, so it is checked, not trusted.

  pair_id               free text               REQUIRED-OR-DERIVED
  stimulus_level        {"high", "low"}         REQUIRED-OR-DERIVED
      Which matched pair the stimulus belongs to and whether it is the HIGH or LOW
      own-copy-match member. If the runner does not emit these two columns, the
      analysis derives them from a pairs table (--pairs, default
      ../pairs/matched_pairs.csv) with columns focal_model, stimulus_high,
      stimulus_low and either pair_id or approved. If NEITHER source is present the
      analysis exits; it will not guess which stimulus is the high one.

  RUNNER RECONCILIATION (2026-08-22). study2_betting.py landed while this analysis
  was being validated, and its schema was checked against these assumptions:
      COLS            = psc_common.COLS + EXTRA_COLS, psc_common.COLS unchanged and
                        in order                                           CONFIRMED
      stimulus_level  values ("high", "low")                               CONFIRMED
      partner_condition values ("same", "different")                       CONFIRMED
      partner_model_named = DISPLAY[actor if same else OTHER[actor]]       CONFIRMED
      included_in_analysis = (not superseded_by_retry) and valid_response  CONFIRMED
      run_id / variant emitted with Study 1's AB/BA convention             CONFIRMED
  Two assumptions were WRONG and have been corrected here rather than left to fail:
      - output file stem is study2C_<ts>.csv, not study2_<ts>.csv, with a
        study2C_MERGED_<ts>.csv written when several part files contribute; the
        analysis now resolves DATA_GLOBS in order and refuses to guess between
        multiple unmerged parts.
      - the pairs table is pairs/study2_candidate_pairs.csv (Study 1's
        matched_pairs.csv layout plus diagnostics); matched_pairs.csv is kept as a
        secondary fallback. It is only a FALLBACK either way, since the runner emits
        pair_id and stimulus_level directly.
  One further runner property changes interpretation, not validity: the payoff
  allocation may be deliberately NON-UNIFORM (the runner accepts a per-payoff n from
  design/*.json, e.g. 10/10/40/40 across S = 3/5/7/9). See analyze_study2.py's
  balance_report for what that does to the pooled estimand. The permutation test is
  unaffected: it strata by payoff, so it stays exact under any allocation.

  Accepted aliases, so a reasonable runner is not rejected on a naming quibble:
      stimulus_level  <- is_high, own_copy_match_level, stim_level
      pair_id         <- pair
      partner_condition <- partner  (values still {same, different})

COLUMNS THE ANALYSIS ACTUALLY READS:
      actor_model, stimulus, safe_payoff, run_id, variant,
      participation_decision, valid_response, superseded_by_retry,
      included_in_analysis, partner_condition, partner_model_named,
      pair_id, stimulus_level
  Everything else in the schema is carried for provenance and ignored.

VALIDITY FILTER. Identical to Study 1: a row enters analysis iff
`included_in_analysis` is true. The runner is expected to set that to
`(not superseded_by_retry) and valid_response`; the analysis re-derives it from the
two component columns and refuses to run if the runner's column disagrees, so a
broken retry policy cannot pass silently.
"""

# --- Study 1 Stage C columns, copied verbatim from psc_common.COLS -------------
PSC_COLS = [
    "stage", "actor_model", "actor_model_name", "actor_model_id_requested",
    "actor_model_id_returned", "focal_model", "focal_model_name",
    "stimulus", "stimulus_category", "prior_class_report",
    "run_id", "attempt_number", "prompt_sha8", "seed", "variant",
    "left_identity", "right_identity", "safe_payoff",
    "response_raw", "visible_reasoning",
    "parsed_choice_side", "parsed_choice_identity",
    "predicted_match_probability", "salience_rating",
    "participation_decision", "valid_response", "superseded_by_retry",
    "included_in_analysis", "api_settings", "timestamp",
]

# --- Study 2 additions --------------------------------------------------------
# RECONCILED 2026-08-22 against the sibling runner study2_betting.py, which had
# landed by the time the analysis was validated. Its EXTRA_COLS are reproduced here
# in its order, so COLS is byte-comparable with the runner's schema.
STUDY2_COLS = ["pair_id", "stimulus_level", "partner_condition", "partner_model_named",
               "partner_model_id", "partner_condition_text", "n_per_cell", "cell_key",
               "study"]

# Of those, the analysis reads only the first four. The rest are provenance.
STUDY2_ANALYSED = ["pair_id", "stimulus_level", "partner_condition", "partner_model_named"]

COLS = PSC_COLS + STUDY2_COLS

# The runner writes one part CSV per invocation (resumability), and a MERGED file when
# more than one part contributes. Newest MERGED wins; a bare set of parts must NOT be
# concatenated blindly by the analysis, because parts can overlap on partially
# completed cells - that is precisely what the runner's merge step exists to resolve.
DATA_GLOBS = ["study2C_MERGED_*.csv", "study2C_*.csv"]

# Columns without which the analysis cannot proceed at all.
REQUIRED = [
    "actor_model", "stimulus", "safe_payoff", "run_id",
    "participation_decision", "valid_response", "superseded_by_retry",
    "included_in_analysis", "partner_condition",
]

ALIASES = {
    "stimulus_level": ["is_high", "own_copy_match_level", "stim_level"],
    "pair_id": ["pair"],
    "partner_condition": ["partner"],
    "partner_model_named": ["partner_model", "partner_name"],
}

PARTNERS = ("same", "different")
LEVELS = ("high", "low")

# Display names, matching psc_common.DISPLAY defaults.
DISPLAY = {"gpt": "GPT-5.5", "claude": "Claude Opus 5"}
OTHER = {"gpt": "claude", "claude": "gpt"}

SAFE_VALUES_DEFAULT = [3, 5, 7, 9]

# Model ids as psc_common resolved them from the provider model-list endpoints on
# 2026-08-12. Recorded for provenance in simulated data; the analysis never uses them.
MODEL_ID = {"gpt": "gpt-5.5", "claude": "claude-opus-5"}


def assert_matches_psc_common(path=None):
    """Confirm the copied column list is exact, by PARSING psc_common.py, not importing it.

    Importing psc_common would pull in dotenv, the API clients and two modules from a
    separate repo, and it asserts a prompt hash at import time - none of which the
    analysis needs or should require. The column list is a literal, so it is read out
    of the source with `ast`, which has no side effects at all.

    Returns a status string; a missing or unparseable source is reported, not fatal.
    """
    import ast, os
    if path is None:
        path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__)))),
            "policy_specific_self_coordination_20260812_1401", "code", "psc_common.py")
    if not os.path.exists(path):
        return f"psc_common.py not found at {path}; PSC_COLS copy unverified"
    try:
        tree = ast.parse(open(path).read())
    except SyntaxError as exc:
        return f"psc_common.py unparseable ({exc}); PSC_COLS copy unverified"
    found = None
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == "COLS" for t in node.targets):
            try:
                found = ast.literal_eval(node.value)
            except ValueError:
                pass
    if found is None:
        return "COLS literal not found in psc_common.py; PSC_COLS copy unverified"
    if list(found) != PSC_COLS:
        raise SystemExit(
            "study2_schema.PSC_COLS has drifted from psc_common.COLS:\n"
            f"  only in psc_common : {[c for c in found if c not in PSC_COLS]}\n"
            f"  only in this copy  : {[c for c in PSC_COLS if c not in found]}")
    return f"PSC_COLS verified identical to psc_common.COLS ({len(PSC_COLS)} columns)"


# =============================================================================
# STUDY 2 REVISED (dose-response) - ADDITIONS
# =============================================================================
# The revised primary test is a DOSE-RESPONSE relation between a stimulus's
# empirically measured compatibility advantage and the same-vs-different partner
# effect on P(ATTEMPT). That needs two things the interaction schema did not carry:
#
#   compatibility_advantage   float, per (actor_model x stimulus)   REQUIRED-OR-DERIVED
#       own-copy reliability minus cross-model reliability for THIS actor on THIS
#       stimulus (FROZEN_PARAMS.ADVANTAGE_DEF = "own_minus_cross"). The runner may
#       emit it for provenance; the ANALYSIS never trusts it as the analysed value.
#       The analysed value comes from the confirmation-screen counts (below) so that
#       its sampling error is available to the errors-in-variables model. If the
#       runner's column and the confirmed value disagree by more than
#       ADVANTAGE_TOL the analysis says so loudly rather than silently preferring one.
#
#   tier                      str                                   REQUIRED-OR-DERIVED
#       The frozen gradient tier: large / medium / small / zero_ceil / zero_floor /
#       negative, from FROZEN_PARAMS.GRADIENT. Derived from GRADIENT when absent.
#
# NOTE these are appended as a SEPARATE list rather than into COLS, because
# simulate_study2_data.py's interaction mode writes exactly `S.COLS` and would raise
# on a column its row dict does not have. COLS_DOSE is the revised study's full list.
DOSE_COLS = ["compatibility_advantage", "tier"]
COLS_DOSE = COLS + DOSE_COLS

ADVANTAGE_TOL = 0.02        # runner column vs confirmed value: report above this

# Merged into ALIASES so _resolve_aliases picks them up without touching COLS.
ALIASES.update({
    "compatibility_advantage": ["advantage", "compat_advantage", "adv",
                                "compatibility_adv"],
    "tier": ["tier_label", "gradient_tier", "stimulus_tier"],
})

# --- confirmation screen (Stage A re-estimation) ------------------------------
# FROZEN_PARAMS section 4: independent one-shot calls at CONFIRM_N per (model x
# stimulus), unchanged prompt / parse rules / API settings. The analysis accepts
# EITHER of two forms and says which it used:
#
#   (1) PER-TRIAL, Stage-A style rows - the same shape as Study 1's
#       data/stageA_*.csv. Columns read: actor_model (or model / focal_model),
#       stimulus, parsed_choice_identity, and the usual validity columns. Counts
#       are aggregated here.
#
#   (2) AGGREGATED counts, one row per (model x stimulus):
#       model, stimulus, n, k_identity1
#
# CANONICAL IDENTITY LABELLING. Every stimulus is a BINARY choice, and both models
# must be counted against the SAME labelling of the two options, namely
# stimulus_manifest.csv's identity_1 / identity_2. k_identity1 is the number of
# valid trials on which the model named identity_1. Counting each model against its
# OWN modal identity instead would destroy the sign of the cross-model rate, which
# is the only free quantity in the structural constraint of FROZEN_PARAMS section 2
# and is exactly what separates a compatible stimulus from an anti-coordinating one.
CONFIRM_GLOBS = ["study2_confirmA_MERGED_*.csv", "study2_confirmA_*.csv",
                 "confirm_counts*.csv", "stage_a_confirm*.csv"]
CONFIRM_COUNT_COLS = ["model", "stimulus", "n", "k_identity1"]
CONFIRM_ALIASES = {
    "model": ["actor_model", "focal_model", "actor"],
    "k_identity1": ["k_id1", "k1", "n_identity1", "k_identity_1"],
    "n": ["n_valid", "n_trials", "total"],
}
