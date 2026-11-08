"""
Simulate a Study 2 dataset in the EXACT runner schema, under a known ground truth.

WHY. `analyze_study2.py` is frozen before any data exist. A frozen analysis that has
never been run is a frozen guess. This generates data whose truth we set, so the
analysis can be checked on the only thing that matters: does it recover the right
answer, and - the harder half - does it REFUSE to find an interaction when there
isn't one?

THREE GROUND TRUTHS
  a  interaction      HIGH-LOW gap is larger under SAME than under DIFFERENT
  b  main_effect      HIGH-LOW gap is real and IDENTICAL in both partner conditions,
                      plus a genuine Partner main effect (fewer attempts against a
                      different model). This is the case a naive analysis fails:
                      the partner factor visibly "does something", and a test that
                      cannot separate a main effect from an interaction will call it
                      significant.
  c  null             no partner effect, no stimulus effect, payoff response only.
  d  main_effect_low_base
                      THE ADVERSARIAL CASE. Same logit-scale truth as (b) - a real
                      Partner main effect and theta EXACTLY ZERO - but with low
                      baseline attempt rates. A main effect that is additive on the
                      LOGIT scale is NOT additive on the RISK-DIFFERENCE scale, and
                      the frequentist primary statistic is a risk difference. Which
                      way the induced artefact points depends on where the base rate
                      sits relative to 0.5: above it (case b) the artefact is
                      NEGATIVE and harmless; below it the artefact is POSITIVE, i.e.
                      it mimics the hypothesis. This case exists to measure how big
                      that artefact gets and to check that the Bayesian theta, which
                      lives on the logit scale, stays at zero when the risk-difference
                      contrast does not. It is the reason the design carries a
                      convergent model at all rather than a decorative one.

GENERATIVE MODEL (logit scale, matching the analysis's Bayesian parameterisation so
the Bayesian recovery target is unambiguous):

  logit p = alpha[actor] + bS*(S - Sbar) + u[pair]
            + delta*is_high + gamma*is_same + theta*is_high*is_same

The analysis's PRIMARY statistic is on the RISK-DIFFERENCE scale, not the logit
scale, so this script also computes the implied TRUE pooled risk-difference
interaction exactly from the generating probabilities (equal cell n, so the pooled
cell rate is the unweighted mean of the cell probabilities). That number, not the
logit theta, is what the frequentist estimate should land on.

REALISM. Structure is taken from Study 1: the same 5 approved matched pairs (3 GPT,
2 Claude), the same {3,5,7,9} payoff grid, n=30 per cell, exact AB/BA balance, and
the same retry convention - ~5% of first attempts unparseable and superseded, a
small residual fraction lost on the retry too. Those rows are written to the CSV
so the validity filters are actually exercised rather than assumed.

Run:
  python3 simulate_study2_data.py --truth interaction  --out ../data/sim_a.csv
  python3 simulate_study2_data.py --truth main_effect  --out ../data/sim_b.csv
  python3 simulate_study2_data.py --truth null         --out ../data/sim_c.csv
"""
import argparse, csv, hashlib, json, math, os, random, sys
from datetime import datetime, timezone

import numpy as np

import study2_schema as S

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(EXP, "design"))

# The five approved Study 1 matched pairs (from matched_pairs.csv / matched_pair_results.csv).
PAIRS = [
    ("gpt", "gpt__c_open_cplx__vs__s_density", "c_open_cplx", "s_density"),
    ("gpt", "gpt__s_convexity__vs__d_dens_extreme", "s_convexity", "d_dens_extreme"),
    ("gpt", "gpt__c_contr_subtle__vs__b_spiral_cw", "c_contr_subtle", "b_spiral_cw"),
    ("claude", "claude__b_spiral_cw__vs__rot", "b_spiral_cw", "rot"),
    ("claude", "claude__s_convexity__vs__d_dens_extreme", "s_convexity", "d_dens_extreme"),
]
SAFES = S.SAFE_VALUES_DEFAULT

# Actor baselines and payoff slope. Chosen so pooled attempt rates sit around
# 0.5-0.8 and away from the 0.0/1.0 ceilings that flattened several Study 1 cells -
# a validation run must be able to SEE an effect it is asked to detect or it tests
# the generator, not the analysis.
ALPHA = {"gpt": 0.45, "claude": 0.60}
B_SAFE = -0.55
PAIR_U = {p[1]: u for p, u in zip(PAIRS, [0.25, -0.20, 0.10, -0.15, 0.30])}

TRUTHS = {
    # delta = HIGH-LOW effect under DIFFERENT; gamma = SAME main; theta = interaction.
    # alpha_shift moves every actor's baseline, which is what decides whether the
    # logit->risk-difference nonlinearity helps or hurts (see case d).
    "interaction": dict(delta=0.30, gamma=0.25, theta=1.40, alpha_shift=0.0),
    "main_effect": dict(delta=1.40, gamma=0.80, theta=0.00, alpha_shift=0.0),
    "null":        dict(delta=0.00, gamma=0.00, theta=0.00, alpha_shift=0.0),
    "main_effect_low_base":
                   dict(delta=1.40, gamma=0.80, theta=0.00, alpha_shift=-2.2),
}

P_INVALID_FIRST = 0.05      # first attempt unparseable -> retried, row superseded
P_INVALID_RETRY = 0.08      # of those, the retry also fails -> trial lost


def logit_p(actor, pid, is_high, is_same, safe, t, sbar):
    eta = (ALPHA[actor] + t.get("alpha_shift", 0.0)
           + B_SAFE * (safe - sbar) + PAIR_U[pid]
           + t["delta"] * is_high + t["gamma"] * is_same
           + t["theta"] * is_high * is_same)
    return 1.0 / (1.0 + np.exp(-eta))


def true_contrasts(t):
    """Exact population contrasts implied by the generating probabilities.

    Cell n is equal everywhere by construction, so the pooled cell rate is the
    unweighted mean of the generating probabilities over pairs and payoffs. These
    are the numbers the frequentist estimates should recover.
    """
    sbar = float(np.mean(SAFES))
    out = {}
    for actor in ("gpt", "claude"):
        cells = {}
        for lvl, h in (("high", 1), ("low", 0)):
            for w, sm in (("same", 1), ("different", 0)):
                ps = [logit_p(actor, pid, h, sm, s, t, sbar)
                      for (a, pid, _hi, _lo) in PAIRS if a == actor for s in SAFES]
                cells[(lvl, w)] = float(np.mean(ps))
        gs = cells[("high", "same")] - cells[("low", "same")]
        gd = cells[("high", "different")] - cells[("low", "different")]
        pm = ((cells[("high", "same")] + cells[("low", "same")]) / 2
              - (cells[("high", "different")] + cells[("low", "different")]) / 2)
        out[actor] = dict(cells={f"{k[0]}|{k[1]}": round(v, 4) for k, v in cells.items()},
                          gap_same=round(gs, 4), gap_diff=round(gd, 4),
                          interaction_rd=round(gs - gd, 4), partner_main_rd=round(pm, 4))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--truth", required=True,
                    choices=sorted(TRUTHS) + sorted(DOSE_TRUTHS),
                    help="a dose_* truth selects the revised dose-response design and "
                         "the frozen GRADIENT allocation; the others keep the original "
                         "matched-pair interaction design unchanged")
    ap.add_argument("--out", required=True)
    ap.add_argument("--n", type=int, default=30, help="valid calls per cell (must be even)")
    ap.add_argument("--seed", type=int, default=20260822)
    ap.add_argument("--no-pair-cols", action="store_true",
                    help="omit pair_id/stimulus_level, forcing the pairs-table fallback")
    ap.add_argument("--clean", action="store_true", help="no invalid/retry rows")
    ap.add_argument("--use-confirmed", action="store_true",
                    help="dose designs only: take the TRUE marginals from the real "
                         "confirmation screen (design/confirmed_compatibility.csv) "
                         "instead of inverting FROZEN_PARAMS.GRADIENT's provisional "
                         "advantages, so the validation runs on the advantage range "
                         "the study actually has")
    ap.add_argument("--confirm-per-trial", action="store_true",
                    help="dose designs only: write the confirmation screen as Stage-A "
                         "style per-trial rows instead of aggregated counts, so the "
                         "analysis's per-trial ingest path is exercised too")
    args = ap.parse_args()
    if args.truth in DOSE_TRUTHS:
        return dose_main(args)
    if args.n % 2:
        sys.exit("--n must be even so AB/BA is exactly balanced")

    t = TRUTHS[args.truth]
    sbar = float(np.mean(SAFES))
    rng = np.random.default_rng(args.seed)
    prng = random.Random(args.seed)

    cells = []
    for actor, pid, hi_s, lo_s in PAIRS:
        for lvl, sid in (("high", hi_s), ("low", lo_s)):
            for w in ("same", "different"):
                for safe in SAFES:
                    cells.append((actor, pid, lvl, sid, w, safe))

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    cols = [c for c in S.COLS
            if not (args.no_pair_cols and c in ("pair_id", "stimulus_level"))]
    fh = open(args.out, "w", newline="")
    wtr = csv.DictWriter(fh, fieldnames=cols)
    wtr.writeheader()

    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    n_rows = n_valid = n_lost = 0
    for actor, pid, lvl, sid, w, safe in cells:
        p = logit_p(actor, pid, 1 if lvl == "high" else 0,
                    1 if w == "same" else 0, safe, t, sbar)
        variants = ["AB"] * (args.n // 2) + ["BA"] * (args.n // 2)
        prng.shuffle(variants)
        key = f"{actor}__{sid}__{w}__S{safe}"
        for i, var in enumerate(variants):
            run_id = f"{key}__{i:03d}"
            attempts = []
            if not args.clean and rng.random() < P_INVALID_FIRST:
                attempts.append((1, "", False, True))      # superseded
                ok = args.clean or rng.random() >= P_INVALID_RETRY
                attempts.append((2, "ATTEMPT" if (ok and rng.random() < p) else
                                 ("SAFE" if ok else ""), ok, False))
            else:
                attempts.append((1, "ATTEMPT" if rng.random() < p else "SAFE", True, False))
            for att, dec, valid, sup in attempts:
                inc = (not sup) and valid
                n_rows += 1
                n_valid += int(inc)
                n_lost += int((not sup) and (not valid))
                side = prng.choice(["LEFT", "RIGHT"])
                left, right = ("id1", "id2") if var == "AB" else ("id2", "id1")
                row = dict(
                    stage="C2", actor_model=actor, actor_model_name=S.DISPLAY[actor],
                    actor_model_id_requested="SIMULATED",
                    actor_model_id_returned="SIMULATED",
                    focal_model=actor, focal_model_name=S.DISPLAY[actor],
                    stimulus=sid, stimulus_category="simulated",
                    prior_class_report="simulated",
                    run_id=run_id, attempt_number=att, prompt_sha8="SIMULATE",
                    seed=args.seed, variant=var,
                    left_identity=left, right_identity=right, safe_payoff=safe,
                    response_raw=(f"DECISION: {dec}" if valid else "no clear decision"),
                    visible_reasoning="simulated",
                    parsed_choice_side=(side if dec == "ATTEMPT" else ""),
                    parsed_choice_identity=(
                        (left if side == "LEFT" else right) if dec == "ATTEMPT" else ""),
                    predicted_match_probability="", salience_rating="",
                    participation_decision=dec,
                    valid_response=valid, superseded_by_retry=sup,
                    included_in_analysis=inc,
                    api_settings=json.dumps({"simulated": True, "truth": args.truth},
                                            sort_keys=True),
                    timestamp=ts,
                    partner_condition=w,
                    partner_model_named=(S.DISPLAY[actor] if w == "same"
                                         else S.DISPLAY[S.OTHER[actor]]),
                    pair_id=pid, stimulus_level=lvl,
                    # Runner provenance columns: emitted so the simulated file is the
                    # runner's schema exactly, not a subset of it. The analysis
                    # ignores all five, which is itself worth exercising.
                    partner_model_id=(S.MODEL_ID[actor] if w == "same"
                                      else S.MODEL_ID[S.OTHER[actor]]),
                    partner_condition_text=(
                        "You are playing with another instance of "
                        + (S.DISPLAY[actor] if w == "same"
                           else S.DISPLAY[S.OTHER[actor]]) + "."),
                    n_per_cell=args.n,
                    cell_key=f"{actor}|{pid}|{lvl}|{w}|S{safe}",
                    study="study2_partner_policy_20260822_SIMULATED")
                wtr.writerow({c: row[c] for c in cols})
    fh.close()

    # pairs table, so the pair_id/stimulus_level fallback path is available
    pdir = os.path.join(EXP, "pairs")
    os.makedirs(pdir, exist_ok=True)
    ppath = os.path.join(pdir, "matched_pairs.csv")
    with open(ppath, "w", newline="") as pf:
        pw = csv.DictWriter(pf, fieldnames=["pair_id", "focal_model", "stimulus_high",
                                            "stimulus_low", "approved"])
        pw.writeheader()
        for actor, pid, hi_s, lo_s in PAIRS:
            pw.writerow(dict(pair_id=pid, focal_model=actor, stimulus_high=hi_s,
                             stimulus_low=lo_s, approved=True))

    truth = true_contrasts(t)
    print(f"=== SIMULATED Study 2, ground truth = {args.truth.upper()} ===")
    print(f"  logit-scale truth: delta={t['delta']:+.2f} (HIGH-LOW under DIFFERENT)  "
          f"gamma={t['gamma']:+.2f} (SAME main)  theta={t['theta']:+.2f} (INTERACTION)"
          f"  alpha_shift={t.get('alpha_shift', 0.0):+.2f}")
    print(f"  cells {len(cells)}   rows written {n_rows}   valid {n_valid}   "
          f"lost to failed retry {n_lost}")
    print(f"  -> {args.out}")
    print(f"  -> {ppath}")
    print("  TRUE population contrasts on the RISK-DIFFERENCE scale "
          "(what the frequentist test must recover):")
    for a, d in truth.items():
        print(f"    {S.DISPLAY[a]:16} gap_SAME {d['gap_same']:+.4f}  "
              f"gap_DIFF {d['gap_diff']:+.4f}  INTERACTION {d['interaction_rd']:+.4f}  "
              f"partner main {d['partner_main_rd']:+.4f}")
    side = os.path.splitext(args.out)[0] + "_truth.json"
    with open(side, "w") as f:
        json.dump(dict(truth=args.truth, logit=t, risk_difference=truth,
                       n_per_cell=args.n, seed=args.seed,
                       sha8_of_csv=hashlib.sha256(
                           open(args.out, "rb").read()).hexdigest()[:8]), f, indent=2)
    print(f"  -> {side}")


# (entry point moved to the end of the file: the dose-response design and its
# DOSE_TRUTHS table are defined below, and main() dispatches on them.)


# =============================================================================
# STUDY 2 (revised) - DOSE-RESPONSE DESIGN
# =============================================================================
"""
Everything above generates the OLD matched-pair interaction design and is left
untouched, because analysis/VALIDATION.md's numbers were produced from it.

Below generates the REVISED design: FROZEN_PARAMS.GRADIENT's eight stimuli per actor
at the frozen allocation, plus the confirmation screen that measures each stimulus's
compatibility advantage. Three ground truths, and a fourth that exists because the
third has a scale trap in it:

  dose_b        MODEL B TRUE.  The same-model shift is proportional to the stimulus's
                compatibility advantage. This is the hypothesis.
  dose_a_logit  MODEL A TRUE, on the LOG-ODDS scale. A constant same-model shift,
                identical for every stimulus, g1 EXACTLY ZERO. This is the case the
                whole design has to survive, and it is built to be ADVERSARIAL: the
                baseline attempt rate is set to fall from 0.88 at the most negative
                advantage to 0.50 at the largest, so that the logit -> risk-difference
                nonlinearity makes the constant shift LOOK like a dose-response, in
                the POSITIVE direction, i.e. it mimics the hypothesis. A risk-
                difference slope alone therefore CANNOT distinguish A from B, and the
                validation reports exactly how big the induced artefact is.
  dose_a_rd     MODEL A TRUE, on the RISK-DIFFERENCE scale. A constant additive shift
                in P(ATTEMPT). The literal reading of "constant same-model shift", and
                the case in which the primary risk-difference slope must be flat.
  dose_null     No partner effect anywhere. Payoff response only.

THE CONFIRMATION SCREEN IS SIMULATED TOO, and that is the point of this generator
rather than a decoration. The analysis is not handed the true advantage; it is handed
BINOMIAL COUNTS at FROZEN_PARAMS.CONFIRM_N and must re-estimate the advantage from
them, with real sampling error. That is what makes the errors-in-variables machinery
testable at all.

TRUE MARGINALS BY INVERSION. Every stimulus is a binary choice, so with
u = 2(pi_gpt - 1/2) and v = 2(pi_claude - 1/2),

    own_g = 1/2 + u^2/2 ,  own_c = 1/2 + v^2/2 ,  cross = 1/2 + uv/2
    adv_g = u(u - v)/2  ,  adv_c = -v(u - v)/2

so, writing w = u - v,   adv_g + adv_c = w^2/2, and the pair is recovered exactly:

    w = sqrt(2 (adv_g + adv_c)) ,   u = 2 adv_g / w ,   v = u - w

The provisional GRADIENT advantages therefore determine the true marginals, up to a
global sign (u, v) -> (-u, -v), which leaves own and cross unchanged and only relabels
the two identities. Recovered marginals are clipped to [0, 1] where the rounded
provisional values push just past the boundary, and the residual error in the
reconstructed advantage is printed so the clipping is visible rather than silent.
The zero-advantage ceiling controls (proto, s_arrow) are the degenerate w = 0 case and
are set directly to pi = 1.
"""
import FROZEN_PARAMS as F

SAFES_D = list(F.SAFE_PAYOFFS)
B_SAFE_D = -0.55

# Baseline P(ATTEMPT) at the mean payoff, as a function of the stimulus's advantage.
# DELIBERATELY DECREASING: it puts the low-advantage stimuli far from 0.5 and the
# high-advantage ones on top of it, which is the configuration that makes a constant
# LOG-ODDS shift masquerade as a POSITIVE risk-difference dose-response. Any other
# arrangement would make dose_a_logit easier to pass than it should be.
BASE_HI, BASE_LO = 0.88, 0.50

DOSE_TRUTHS = {
    "dose_b":       dict(scale="logit", g0=0.10, g1=1.40, c_rd=0.0),
    "dose_a_logit": dict(scale="logit", g0=0.60, g1=0.00, c_rd=0.0),
    "dose_a_rd":    dict(scale="rd",    g0=0.00, g1=0.00, c_rd=0.10),
    "dose_null":    dict(scale="logit", g0=0.00, g1=0.00, c_rd=0.0),
}


def _logit(p):
    return math.log(p / (1 - p))


def _sig(x):
    return 1.0 / (1.0 + math.exp(-max(-30.0, min(30.0, x))))


def marginals_from_confirmed(verbose=True):
    """True marginals taken from the REAL confirmation screen, if it has run.

    design/confirmed_compatibility.csv publishes GG, CC, GC and the modal identities,
    not raw counts, so the marginals are recovered by the same exact inversion the
    analysis uses (analyze_dose_response.counts_from_confirmed_table): for a binary
    stimulus sum_k p_k^2 = (own_unbiased*(n-1) + 1)/n = 1/2 + u^2/2 fixes |u|, and the
    modal identity fixes its sign against the manifest's identity_1.

    WHY THIS MATTERS FOR VALIDATION. The confirmation screen came back with a much
    FLATTER gradient than the provisional n=60 battery: a_chev_ud fell from +0.650 to
    +0.294 for GPT, and d_texture's Claude advantage collapsed from +0.401 to +0.003.
    Validating only against the provisional spread would overstate the design's power,
    so `--use-confirmed` re-runs the same ground truths on the range the study actually
    has. Returns None if the confirmation has not run.
    """
    path = os.path.join(EXP, "design", "confirmed_compatibility.csv")
    mp = os.path.join(EXP, "stimulus_manifest.csv")
    if not (os.path.exists(path) and os.path.exists(mp)):
        return None
    id1 = {r["stimulus_id"]: r["identity_1"] for r in csv.DictReader(open(mp))}
    pi = {}
    for r in csv.DictReader(open(path)):
        s = r["stimulus"]
        if s not in id1:
            continue
        for m, own_col, n_col in (("gpt", "GG", "n_gpt"), ("claude", "CC", "n_claude")):
            n = int(float(r[n_col]))
            sump2 = (float(r[own_col]) * (n - 1) + 1.0) / n
            u = math.sqrt(max(0.0, 2.0 * (sump2 - 0.5)))
            if str(r.get(f"modal_{m}", "")).strip() != id1[s]:
                u = -u
            pi[(m, s)] = 0.5 + u / 2.0
    if verbose:
        print(f"  true marginals taken from the CONFIRMED screen ({path})")
    return pi or None


def invert_marginals(verbose=True):
    """Provisional advantages -> true binary marginals pi[(model, stimulus)]."""
    gpt = {sid: adv for sid, adv, _t, _n in F.GRADIENT["gpt"]}
    cla = {sid: adv for sid, adv, _t, _n in F.GRADIENT["claude"]}
    pi, err = {}, {}
    for sid in gpt:
        ag, ac = gpt[sid], cla[sid]
        tot = ag + ac
        if tot <= 1e-12:
            u = v = 1.0                       # ceiling controls: both models certain
        else:
            w = math.sqrt(2.0 * tot)
            u = 2.0 * ag / w
            v = u - w
        u, v = max(-1.0, min(1.0, u)), max(-1.0, min(1.0, v))
        pg, pc = 0.5 + u / 2.0, 0.5 + v / 2.0
        pi[("gpt", sid)], pi[("claude", sid)] = pg, pc
        og, oc = pg ** 2 + (1 - pg) ** 2, pc ** 2 + (1 - pc) ** 2
        cr = pg * pc + (1 - pg) * (1 - pc)
        err[sid] = (og - cr - ag, oc - cr - ac)
    if verbose:
        w = max(max(abs(a), abs(b)) for a, b in err.values())
        print(f"  true marginals recovered by inversion; max |reconstructed advantage "
              f"- provisional| = {w:.4f} (clipping at the |u|<=1 boundary)")
    return pi


def true_advantage(pi, stimuli):
    adv = {}
    for s in stimuli:
        pg, pc = pi[("gpt", s)], pi[("claude", s)]
        cr = pg * pc + (1 - pg) * (1 - pc)
        adv[("gpt", s)] = pg ** 2 + (1 - pg) ** 2 - cr
        adv[("claude", s)] = pc ** 2 + (1 - pc) ** 2 - cr
    return adv


def base_rate(adv, lo, hi):
    """Linear in advantage, from BASE_HI at the minimum to BASE_LO at the maximum."""
    z = (adv - lo) / (hi - lo) if hi > lo else 0.0
    return BASE_HI + (BASE_LO - BASE_HI) * z


def dose_p(actor, sid, partner, safe, t, adv, lo, hi, sbar):
    eta0 = _logit(base_rate(adv[(actor, sid)], lo, hi)) + B_SAFE_D * (safe - sbar)
    p0 = _sig(eta0)
    if partner == "different":
        return p0
    if t["scale"] == "rd":
        return min(0.995, max(0.005, p0 + t["c_rd"]))
    return _sig(eta0 + t["g0"] + t["g1"] * adv[(actor, sid)])


def dose_true_slopes(t, adv, stimuli, sbar, lo, hi):
    """The EXACT population risk-difference dose-response slope implied by the truth.

    This, not the logit-scale g1, is what the primary risk-difference estimate must
    recover. Both an unweighted and an allocation-weighted version are returned,
    because the frozen allocation is deliberately non-uniform across stimuli.
    """
    npart = {(m, sid): n for m, tiers in F.GRADIENT.items() for sid, _a, _t, n in tiers}
    xs, ys, ws = [], [], []
    per = {}
    for m in ("gpt", "claude"):
        for sid in stimuli:
            if (m, sid) not in npart:
                continue
            rd = np.mean([dose_p(m, sid, "same", s, t, adv, lo, hi, sbar)
                          - dose_p(m, sid, "different", s, t, adv, lo, hi, sbar)
                          for s in SAFES_D])
            xs.append(adv[(m, sid)]); ys.append(float(rd)); ws.append(npart[(m, sid)])
            per[f"{m}|{sid}"] = round(float(rd), 4)
    keep = np.array([True] * len(xs))
    ex = F.SENSITIVITY_EXCLUDE[0]
    j = 0
    for m in ("gpt", "claude"):
        for sid in stimuli:
            if (m, sid) not in npart:
                continue
            keep[j] = sid != ex
            j += 1
    xs, ys, ws = np.array(xs), np.array(ys), np.array(ws, float)

    def _wslope(x, y, w):
        X = np.column_stack([np.ones_like(x), x])
        return float(np.linalg.solve((X.T * w) @ X, (X.T * w) @ y)[1])

    return dict(rd_slope_unweighted=round(float(np.polyfit(xs, ys, 1)[0]), 4),
                rd_slope_n_weighted=round(_wslope(xs, ys, ws), 4),
                rd_slope_n_weighted_excl_a_chev_ud=round(
                    _wslope(xs[keep], ys[keep], ws[keep]), 4),
                mean_partner_effect=round(float(np.average(ys, weights=ws)), 4),
                per_stimulus_rd=per)


def dose_main(args):
    t = DOSE_TRUTHS[args.truth]
    rng = np.random.default_rng(args.seed)
    prng = random.Random(args.seed)
    man = {}
    mp = os.path.join(EXP, "stimulus_manifest.csv")
    if os.path.exists(mp):
        man = {r["stimulus_id"]: (r["identity_1"], r["identity_2"])
               for r in csv.DictReader(open(mp))}

    print(f"=== SIMULATED Study 2 DOSE-RESPONSE, ground truth = {args.truth.upper()} ===")
    pi = marginals_from_confirmed() if args.use_confirmed else None
    if args.use_confirmed and pi is None:
        sys.exit("--use-confirmed given but design/confirmed_compatibility.csv is not "
                 "there yet; run code/confirm_compat.py first")
    if pi is None:
        pi = invert_marginals()
    stimuli = sorted({sid for tiers in F.GRADIENT.values() for sid, *_ in tiers})
    adv = true_advantage(pi, stimuli)
    advs = [adv[(m, s)] for m in ("gpt", "claude") for s in stimuli]
    lo, hi = min(advs), max(advs)
    sbar = float(np.mean(SAFES_D))

    # ---- confirmation screen: BINOMIAL COUNTS, not the truth ------------------
    conf = {}
    for s in stimuli:
        for m in ("gpt", "claude"):
            n = F.CONFIRM_N[s]
            conf[(m, s)] = (int(rng.binomial(n, pi[(m, s)])), n)
    stem = os.path.splitext(os.path.abspath(args.out))[0]
    cpath = stem + "_confirmA.csv"
    os.makedirs(os.path.dirname(stem), exist_ok=True)
    if args.confirm_per_trial:
        with open(cpath, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=[
                "stage", "actor_model", "stimulus", "run_id", "variant",
                "parsed_choice_identity", "valid_response", "superseded_by_retry",
                "included_in_analysis"])
            w.writeheader()
            for (m, s), (k, n) in sorted(conf.items()):
                i1, i2 = man.get(s, ("identity_1", "identity_2"))
                picks = [i1] * k + [i2] * (n - k)
                prng.shuffle(picks)
                for i, ident in enumerate(picks):
                    w.writerow(dict(stage="A_confirm", actor_model=m, stimulus=s,
                                    run_id=f"{m}__{s}__{i:04d}",
                                    variant="AB" if i % 2 == 0 else "BA",
                                    parsed_choice_identity=ident, valid_response=True,
                                    superseded_by_retry=False, included_in_analysis=True))
        form = "PER-TRIAL"
    else:
        with open(cpath, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=S.CONFIRM_COUNT_COLS)
            w.writeheader()
            for (m, s), (k, n) in sorted(conf.items()):
                w.writerow(dict(model=m, stimulus=s, n=n, k_identity1=k))
        form = "AGGREGATED"

    # what the analysis will estimate from those counts (the runner's column)
    est = {}
    for s in stimuli:
        pg = conf[("gpt", s)][0] / conf[("gpt", s)][1]
        pc = conf[("claude", s)][0] / conf[("claude", s)][1]
        cr = pg * pc + (1 - pg) * (1 - pc)
        for m, p in (("gpt", pg), ("claude", pc)):
            k, n = conf[(m, s)]
            k2 = n - k
            own = (k * (k - 1) + k2 * (k2 - 1)) / (n * (n - 1))
            est[(m, s)] = own - cr

    # ---- Stage C at the frozen allocation ------------------------------------
    cols = [c for c in S.COLS_DOSE]
    fh = open(args.out, "w", newline="")
    wtr = csv.DictWriter(fh, fieldnames=cols)
    wtr.writeheader()
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    n_rows = n_valid = n_lost = 0
    for actor, tiers in F.GRADIENT.items():
        for sid, _prov, tier, npart in tiers:
            per_payoff = F.per_payoff_n(npart)
            for w in F.PARTNER_CONDITIONS:
                for safe in SAFES_D:
                    p = dose_p(actor, sid, w, safe, t, adv, lo, hi, sbar)
                    variants = ["AB"] * (per_payoff // 2) + ["BA"] * (per_payoff // 2)
                    prng.shuffle(variants)
                    key = f"{actor}__{sid}__{w}__S{safe}"
                    for i, var in enumerate(variants):
                        attempts = []
                        if not args.clean and rng.random() < P_INVALID_FIRST:
                            attempts.append((1, "", False, True))
                            ok = rng.random() >= P_INVALID_RETRY
                            attempts.append((2, "ATTEMPT" if (ok and rng.random() < p)
                                             else ("SAFE" if ok else ""), ok, False))
                        else:
                            attempts.append((1, "ATTEMPT" if rng.random() < p else "SAFE",
                                             True, False))
                        for att, dec, valid, sup in attempts:
                            inc = (not sup) and valid
                            n_rows += 1
                            n_valid += int(inc)
                            n_lost += int((not sup) and (not valid))
                            side = prng.choice(["LEFT", "RIGHT"])
                            left, right = ("id1", "id2") if var == "AB" else ("id2", "id1")
                            wtr.writerow(dict(
                                stage="C2", actor_model=actor,
                                actor_model_name=S.DISPLAY[actor],
                                actor_model_id_requested="SIMULATED",
                                actor_model_id_returned="SIMULATED",
                                focal_model=actor, focal_model_name=S.DISPLAY[actor],
                                stimulus=sid, stimulus_category=tier,
                                prior_class_report="simulated",
                                run_id=f"{key}__{i:03d}", attempt_number=att,
                                prompt_sha8="SIMULATE", seed=args.seed, variant=var,
                                left_identity=left, right_identity=right,
                                safe_payoff=safe,
                                response_raw=(f"DECISION: {dec}" if valid
                                              else "no clear decision"),
                                visible_reasoning="simulated",
                                parsed_choice_side=(side if dec == "ATTEMPT" else ""),
                                parsed_choice_identity=(
                                    (left if side == "LEFT" else right)
                                    if dec == "ATTEMPT" else ""),
                                predicted_match_probability="", salience_rating="",
                                participation_decision=dec, valid_response=valid,
                                superseded_by_retry=sup, included_in_analysis=inc,
                                api_settings=json.dumps({"simulated": True,
                                                         "truth": args.truth},
                                                        sort_keys=True),
                                timestamp=ts,
                                pair_id="", stimulus_level="",
                                partner_condition=w,
                                partner_model_named=(S.DISPLAY[actor] if w == "same"
                                                     else S.DISPLAY[S.OTHER[actor]]),
                                partner_model_id=(S.MODEL_ID[actor] if w == "same"
                                                  else S.MODEL_ID[S.OTHER[actor]]),
                                partner_condition_text=(
                                    "You are playing with another instance of "
                                    + (S.DISPLAY[actor] if w == "same"
                                       else S.DISPLAY[S.OTHER[actor]]) + "."),
                                n_per_cell=per_payoff,
                                cell_key=f"{actor}|{sid}|{w}|S{safe}",
                                study="study2_dose_response_20260822_SIMULATED",
                                compatibility_advantage=round(est[(actor, sid)], 6),
                                tier=tier))
    fh.close()

    truth = dose_true_slopes(t, adv, stimuli, sbar, lo, hi)
    print(f"  logit-scale truth: scale={t['scale']}  g0={t['g0']:+.2f} "
          f"(constant same-model shift)  g1={t['g1']:+.2f} (dose-response)  "
          f"c_rd={t['c_rd']:+.2f}")
    print(f"  baseline P(ATTEMPT) runs {BASE_HI:.2f} at adv={lo:+.3f} down to "
          f"{BASE_LO:.2f} at adv={hi:+.3f} - the ADVERSARIAL arrangement, chosen so a "
          "constant log-odds shift produces a POSITIVE risk-difference slope")
    print(f"  rows written {n_rows}   valid {n_valid}   lost to failed retry {n_lost}")
    print(f"  TRUE risk-difference dose-response slope (what the primary must recover):")
    print(f"    unweighted over the 16 (actor x stimulus) points : "
          f"{truth['rd_slope_unweighted']:+.4f}")
    print(f"    weighted by the frozen allocation                : "
          f"{truth['rd_slope_n_weighted']:+.4f}")
    print(f"    weighted, EXCLUDING {F.SENSITIVITY_EXCLUDE[0]:<25}: "
          f"{truth['rd_slope_n_weighted_excl_a_chev_ud']:+.4f}")
    print(f"    mean partner effect (MODEL A's quantity)         : "
          f"{truth['mean_partner_effect']:+.4f}")
    print(f"  -> {args.out}")
    print(f"  -> {cpath}   ({form} confirmation counts at FROZEN_PARAMS.CONFIRM_N)")
    side = stem + "_truth.json"
    with open(side, "w") as f:
        json.dump(dict(truth=args.truth, design="dose", params=t,
                       base_hi=BASE_HI, base_lo=BASE_LO, b_safe=B_SAFE_D,
                       true_marginals={f"{m}|{s}": round(v, 6)
                                       for (m, s), v in sorted(pi.items())},
                       true_advantage={f"{m}|{s}": round(v, 6)
                                       for (m, s), v in sorted(adv.items())},
                       confirm_counts={f"{m}|{s}": list(v)
                                       for (m, s), v in sorted(conf.items())},
                       estimated_advantage={f"{m}|{s}": round(v, 6)
                                            for (m, s), v in sorted(est.items())},
                       implied=truth, seed=args.seed,
                       sha8_of_csv=hashlib.sha256(
                           open(args.out, "rb").read()).hexdigest()[:8]), f, indent=2)
    print(f"  -> {side}")


if __name__ == "__main__":
    main()
