"""
Build the modelling dataset for the Bayesian decision analysis.

Uses ONLY completed Stage A / B / C outputs. No API calls, no design changes, and
none of the pre-specified frequentist analyses are touched.

HELD-OUT THROUGHOUT. Every predictor comes from the held-out half of the Stage A/B
sample split - the half that was not used to order high/low, select pairs, or
compute the matching score. The explanatory variables were therefore not estimated
on the data that chose them.

Stage A is carried as COUNTS, not as a point estimate. With two identities, if k of
n trials pick identity 1 then the unbiased dyadic self-match is a deterministic
function of the latent choice probability p:

    match(p) = p^2 + (1 - p)^2

so the measurement-error model can put a Beta posterior on p and push it through.
This also removes an artefact of the point-estimate version: five of the ten cells
have k = 0 (or 1) out of 30, giving an empirical self-match of exactly 1.000, whose
logit is infinite and has to be clamped by hand. The latent-p formulation keeps the
quantity strictly inside (0,1) with an honest amount of uncertainty.

Writes model_data.json.
"""
import csv, glob, json, math, os, sys
from collections import defaultdict

CODE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "code")
sys.path.insert(0, CODE)
import psc_common as P
import analyze_stage_ab as A

HERE = os.path.dirname(os.path.abspath(__file__))
SAFES = [3, 5, 7, 9]


def newest(pat):
    fs = [f for f in glob.glob(os.path.join(P.DATA, pat)) if "_DRY" not in f]
    return max(fs, key=os.path.getmtime)


def build():
    man = {r["stimulus_id"]: r for r in P.load_manifest()}

    # ---------------- Stage A: held-out identity counts -------------------
    rows = P.load_analysis_rows(newest("stageA_2*.csv"))
    A.assign_halves(rows, lambda r: (r["actor_model"], r["stimulus"]))
    sa = defaultdict(lambda: {"k1": 0, "n": 0})
    for r in rows:
        if r["_half"] != "holdout":
            continue
        d = sa[(r["actor_model"], r["stimulus"])]
        d["n"] += 1
        d["k1"] += int(r["parsed_choice_identity"] == man[r["stimulus"]]["identity_1"])

    # ---------------- Stage B: held-out auditor + salience -----------------
    arows = [r for r in P.load_analysis_rows(newest("stageB_auditor_2*.csv"))
             if r["predicted_match_probability"]]
    A.assign_halves(arows, lambda r: (r["focal_model"], r["stimulus"]))
    aud = defaultdict(list)
    for r in arows:
        if r["_half"] == "holdout":
            aud[(r["focal_model"], r["stimulus"])].append(
                float(r["predicted_match_probability"]) / 100.0)

    srows = [r for r in P.load_analysis_rows(newest("stageB_salience_2*.csv"))
             if r["salience_rating"]]
    A.assign_halves(srows, lambda r: (r["actor_model"], r["stimulus"]))
    sal = defaultdict(list)
    for r in srows:
        if r["_half"] == "holdout":
            sal[r["stimulus"]].append(float(r["salience_rating"]) / 100.0)

    # ---------------- Stage C: trial level ---------------------------------
    crows = P.load_analysis_rows(newest("stageC_2*.csv"))
    pairs = [r for r in csv.DictReader(open(os.path.join(P.EXP, "matched_pairs.csv")))
             if str(r.get("approved", "")).lower() in ("true", "1", "yes")]
    cand = {r["pair_id"]: r for r in
            csv.DictReader(open(os.path.join(P.DATA, "stage_c_candidates.csv")))}

    cells = sorted({(r["actor_model"], r["stimulus"]) for r in crows})
    cell_ix = {c: i for i, c in enumerate(cells)}
    models = ["gpt", "claude"]

    def mean(v):
        return sum(v) / len(v)

    def sd(v):
        m = mean(v)
        return math.sqrt(sum((x - m) ** 2 for x in v) / (len(v) - 1)) if len(v) > 1 else 0.0

    cellinfo = []
    for (m, s) in cells:
        a = sa[(m, s)]
        av, sv = aud[(m, s)], sal[s]
        p_hat = a["k1"] / a["n"]
        cellinfo.append(dict(
            model=m, stimulus=s, model_ix=models.index(m),
            k1=a["k1"], n_A=a["n"],
            true_point=p_hat ** 2 + (1 - p_hat) ** 2,
            aud_mean=mean(av), aud_se=sd(av) / math.sqrt(len(av)), n_aud=len(av),
            sal_mean=mean(sv), sal_se=sd(sv) / math.sqrt(len(sv)), n_sal=len(sv),
        ))

    # pair bookkeeping (for grouped CV and pair-level posteriors)
    pinfo = []
    for r in pairs:
        m, hi, lo = r["focal_model"], r["stimulus_high"], r["stimulus_low"]
        c = cand.get(r["pair_id"], {})
        ch, cl = c.get("fresh_classification_high", ""), c.get("fresh_classification_low", "")
        pinfo.append(dict(pair_id=r["pair_id"], model=m, hi=hi, lo=lo,
                          hi_ix=cell_ix[(m, hi)], lo_ix=cell_ix[(m, lo)],
                          fresh_high=ch, fresh_low=cl,
                          both_form=ch.startswith("form_rule") and cl.startswith("form_rule")))

    trials = [dict(y=1 if r["participation_decision"] == "ATTEMPT" else 0,
                   safe=int(r["safe_payoff"]),
                   cell=cell_ix[(r["actor_model"], r["stimulus"])],
                   model_ix=models.index(r["actor_model"]))
              for r in crows]

    out = dict(models=models, cells=cellinfo, pairs=pinfo, trials=trials, safes=SAFES)
    with open(os.path.join(HERE, "model_data.json"), "w") as fh:
        json.dump(out, fh, indent=1)
    return out


if __name__ == "__main__":
    d = build()
    print("=" * 74)
    print("MODELLING DATASET  (all predictors from the HELD-OUT half)")
    print("=" * 74)
    print(f"  Stage C trials      : {len(d['trials'])}")
    print(f"  unique (model,stim) : {len(d['cells'])}")
    print(f"  approved pairs      : {len(d['pairs'])}")
    print(f"  safe payoffs        : {d['safes']}")
    for m in d["models"]:
        cs = [c for c in d["cells"] if c["model"] == m]
        print(f"    {P.DISPLAY[m]:16} {len(cs)} stimuli")
    print("\n  columns used: y, safe_payoff, cell index, model index;")
    print("  cell predictors: Stage A (k1, n) counts, auditor mean+SE, salience mean+SE")
    print(f"\n{'model':7}{'stimulus':16}{'k1/n':>8}{'true':>7}{'aud':>7}{'+-':>6}{'sal':>7}{'+-':>6}")
    for c in d["cells"]:
        print(f"{c['model']:7}{c['stimulus']:16}{c['k1']:4}/{c['n_A']:<3}{c['true_point']:7.3f}"
              f"{c['aud_mean']:7.3f}{c['aud_se']:6.3f}{c['sal_mean']:7.3f}{c['sal_se']:6.3f}")
    print(f"\n-> {os.path.join(HERE, 'model_data.json')}")
