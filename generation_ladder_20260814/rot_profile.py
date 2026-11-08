"""
`rot` across the generation ladder — is the coordinate-perfectly-but-bet-against
inversion a property of the STIMULUS or of the two models that showed it?

BACKGROUND. Two rungs inverted on `rot`:
  Opus 4.7  initial 3-pair Stage C sample, gap -0.103, driven entirely by `rot`;
            50.8% of Stage C rationales call it featureless vs 0% in Stage A
  Opus 4.6  15/16 stimuli at 10/10 ATTEMPT at SAFE=9; `rot` alone at 4/10,
            despite self-match 1.000 and form_consistency 1.00
The 2026-08-18 diary entry proposed reading this as a stimulus property. This
script tests that against every rung's own data. NO API CALLS — all inputs are
already-computed Stage A/B tables and already-collected Stage C / payoff-screen
CSVs.

THREE THINGS IT SEPARATES
  1. is `rot` a convention?      self_match_unbiased, holdout, form_consistency
  2. does it LOOK like one?      generic_salience, auditor_prediction
  3. does the model bet on it?   ATTEMPT rate by safe payoff, vs the same run's
                                 battery mean at the same payoff

The interesting cell is a rung where (1) is high, (2) is low, and (3) is low.
A rung where (1) is low and (3) is low is not an inversion — it is a model
correctly declining a stimulus it cannot coordinate on, and it is the control
that says whether low betting on `rot` is about the picture or about the rule.

Run:  python3 rot_profile.py
Out:  analysis/rot_profile.json, analysis/rot_profile.csv, printed tables
"""
import csv, glob, json, os, re, statistics, random
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
ANALYSIS = os.path.join(HERE, "analysis")
STIM = "rot"
SEED, BOOT = 20260822, 5000

# Same regex as reasoning_traces/trace_analysis.py `hedge_no_rule`, reused verbatim
# so the featureless-language rates here are comparable to the 2026-08-13 lexicon
# result rather than a fresh, differently-tuned proxy.
HEDGE = re.compile(
    r"(unclear|ambiguous|not obvious|no (?:clear|obvious|strong)|"
    r"hard to|difficult to|weak(?:ly)?|too similar|very similar|"
    r"little to distinguish|toss-?up|coin[- ]?flip|50[/-]?50|"
    r"arbitrar|uncertain|either way|no reliable|lacks?)", re.I)

# One entry per ladder rung, pointing at the data folder the ladder figure used.
# `bet` lists every already-collected file in which this rung was actually asked
# to bet on `rot`; most rungs never were, because the frozen selector only puts a
# stimulus into Stage C when it is an eligible pair member for that rung.
RUNGS = [
    ("OpenAI",    "GPT-4o",   1, "generation_ladder_20260814/models/gpt4o/data",           "gpt",    []),
    ("OpenAI",    "GPT-5",    2, "generation_ladder_20260814/models/gpt5_expanded/data",   "gpt",    []),
    ("OpenAI",    "GPT-5.4",  3, "policy_specific_self_coordination_20260812_1401/replication_5_4_4_8/data", "gpt", []),
    ("OpenAI",    "GPT-5.5",  4, "policy_specific_self_coordination_20260812_1401/data",   "gpt",    []),
    ("Anthropic", "Opus 4.5", 1, "generation_ladder_20260814/models/opus45_expanded/data", "claude", []),
    ("Anthropic", "Opus 4.6", 2, "generation_ladder_20260814/models/opus46_expanded/data", "claude",
        ["generation_ladder_20260814/models/opus46_expanded/data/payoffscreen_20260818_110236.csv"]),
    ("Anthropic", "Opus 4.7", 3, "generation_ladder_20260814/models/opus47_expanded/data", "claude",
        ["generation_ladder_20260814/models/opus47/data/stageC_20260815_132504.csv",
         "generation_ladder_20260814/models/opus47/data/payoffscreen_20260815_132427.csv"]),
    ("Anthropic", "Opus 4.8", 4, "generation_ladder_20260814/models/opus48_expanded/data", "claude", []),
    ("Anthropic", "Opus 5",   5, "policy_specific_self_coordination_20260812_1401/data",   "claude",
        ["policy_specific_self_coordination_20260812_1401/data/stageC_20260812_161428.csv"]),
]


def rows(path):
    with open(path, newline="") as fh:
        return list(csv.DictReader(fh))


def f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return float("nan")


def stage_a_rows(folder, model, stimulus=None):
    """Valid, in-analysis Stage A trials, newest merged file wins."""
    pats = ["stageA_MERGED_*.csv", "stageA_*.csv"]
    files = []
    for p in pats:
        files = [x for x in glob.glob(os.path.join(folder, p)) if "_DRY" not in x]
        if files:
            break
    if not files:
        return []
    newest = max(files, key=os.path.getmtime)
    out = []
    for r in rows(newest):
        if r.get("actor_model") != model:
            continue
        if r.get("valid_response", "True") not in ("True", "true", "1", ""):
            continue
        if r.get("included_in_analysis", "True") in ("False", "false", "0"):
            continue
        if stimulus and r["stimulus"] != stimulus:
            continue
        out.append(r)
    return out


def rationale(r):
    return re.split(r"DECISION:", r.get("response_raw", ""), flags=re.I)[0]


def boot_ci(vals, seed, b=BOOT):
    if not vals:
        return float("nan"), float("nan")
    rng = random.Random(seed)
    n = len(vals)
    d = sorted(statistics.fmean(rng.choices(vals, k=n)) for _ in range(b))
    return d[int(0.025 * b)], d[int(0.975 * b)]


# ============================== 1 + 2: is it a convention, does it look like one
profile = []
for provider, label, order, rel, model, betfiles in RUNGS:
    folder = os.path.join(PROJ, rel)
    fsm = os.path.join(folder, "fresh_self_match.csv")
    if not os.path.exists(fsm):
        continue
    battery = [r for r in rows(fsm) if r["model"] == model]
    me = next((r for r in battery if r["stimulus"] == STIM), None)
    if me is None:
        continue

    sm = [f(r["self_match_unbiased"]) for r in battery]
    sm = [x for x in sm if x == x]
    rank = sum(1 for x in sm if x > f(me["self_match_unbiased"])) + 1

    sal = aud = float("nan")
    p = os.path.join(folder, "salience_ratings.csv")
    if os.path.exists(p):
        row = next((r for r in rows(p)
                    if r["stimulus"] == STIM and r["rater_model"] == "pooled"), None)
        if row:
            sal = f(row["salience"])
    p = os.path.join(folder, "auditor_predictions.csv")
    if os.path.exists(p):
        row = next((r for r in rows(p)
                    if r["stimulus"] == STIM and r["focal_model"] == model), None)
        if row:
            aud = f(row["auditor_predicted_match"])

    # featureless language in Stage A, where the model is simply choosing
    a_rows = stage_a_rows(folder, model, STIM)
    hedge_a = (statistics.fmean([bool(HEDGE.search(rationale(r))) for r in a_rows])
               if a_rows else float("nan"))

    profile.append(dict(
        provider=provider, model=label, generation_order=order,
        n_stimuli_battery=len(battery), n_valid=int(f(me["n_valid"])),
        self_match=f(me["self_match_unbiased"]),
        ci_lo=f(me["self_match_ci_lo"]), ci_hi=f(me["self_match_ci_hi"]),
        holdout=f(me["self_match_holdout"]),
        form_consistency=f(me["form_consistency"]),
        p_left=f(me["p_left"]), fallback=me["fallback"],
        rank_in_battery=rank,
        generic_salience=sal, auditor_prediction=aud,
        hedge_rate_stage_a=hedge_a,
        n_stage_a_rationales=len(a_rows),
    ))

# ============================== 3: does it bet on it
betting = []
for provider, label, order, rel, model, betfiles in RUNGS:
    if not betfiles:
        continue
    trials = []
    for bf in betfiles:
        path = os.path.join(PROJ, bf)
        if not os.path.exists(path):
            continue
        for r in rows(path):
            if r.get("actor_model") != model:
                continue
            if r.get("valid_response", "True") in ("False", "false", "0"):
                continue
            if r.get("included_in_analysis", "True") in ("False", "false", "0"):
                continue
            r["_src"] = os.path.basename(path)
            trials.append(r)
    if not trials:
        continue

    by_pay = defaultdict(lambda: {"rot": [], "other": []})
    for r in trials:
        att = 1.0 if r.get("participation_decision", "").upper().startswith("ATTEMPT") else 0.0
        by_pay[f(r["safe_payoff"])]["rot" if r["stimulus"] == STIM else "other"].append(att)

    hedge_c = [bool(HEDGE.search(rationale(r))) for r in trials if r["stimulus"] == STIM]
    hedge_o = [bool(HEDGE.search(rationale(r))) for r in trials if r["stimulus"] != STIM]

    ent = dict(provider=provider, model=label, generation_order=order,
               sources=sorted({r["_src"] for r in trials}),
               hedge_rate_stage_c_rot=(statistics.fmean(hedge_c) if hedge_c else float("nan")),
               n_rot_rationales=len(hedge_c),
               hedge_rate_stage_c_other=(statistics.fmean(hedge_o) if hedge_o else float("nan")),
               n_other_rationales=len(hedge_o), by_payoff=[])
    for pay in sorted(by_pay):
        d = by_pay[pay]
        lo, hi = boot_ci(d["rot"], SEED + int(pay))
        ent["by_payoff"].append(dict(
            safe_payoff=pay,
            rot_attempt=(statistics.fmean(d["rot"]) if d["rot"] else float("nan")),
            rot_ci_lo=lo, rot_ci_hi=hi, n_rot=len(d["rot"]),
            battery_attempt=(statistics.fmean(d["other"]) if d["other"] else float("nan")),
            n_other=len(d["other"])))
    betting.append(ent)

# ============================================================ report
os.makedirs(ANALYSIS, exist_ok=True)
with open(os.path.join(ANALYSIS, "rot_profile.json"), "w") as fh:
    json.dump({"stimulus": STIM, "profile": profile, "betting": betting}, fh, indent=1)
with open(os.path.join(ANALYSIS, "rot_profile.csv"), "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(profile[0].keys()))
    w.writeheader()
    w.writerows(profile)


def s(x, n=3):
    return "  n/a" if x != x else f"{x:.{n}f}"


print(f"\n{'='*94}\n`{STIM}` ACROSS THE LADDER — is it a convention, and does it look like one?\n{'='*94}")
print(f"{'rung':<11}{'n':>4}{'self-match':>13}{'holdout':>9}{'form':>7}{'P(L)':>7}"
      f"{'rank':>7}{'salience':>10}{'auditor':>9}{'hedgeA':>8}")
for r in profile:
    print(f"{r['model']:<11}{r['n_valid']:>4}"
          f"{s(r['self_match']):>7} [{s(r['ci_lo'],2)},{s(r['ci_hi'],2)}]"
          f"{s(r['holdout']):>9}{s(r['form_consistency'],2):>7}{s(r['p_left'],2):>7}"
          f"{str(r['rank_in_battery'])+'/'+str(r['n_stimuli_battery']):>7}"
          f"{s(r['generic_salience']):>10}{s(r['auditor_prediction']):>9}"
          f"{s(r['hedge_rate_stage_a'],2):>8}")
print("\nform = form_consistency (1 - |P(modal|modal left) - P(modal|modal right)|);"
      " 1.00 = position-independent.\nrank = rot's place among that rung's own battery on self-match."
      " hedgeA = share of Stage A\nrationales using featureless/no-rule language.")

print(f"\n{'='*94}\nDOES THE RUNG BET ON `{STIM}`? (only rungs the selector ever put it in front of)\n{'='*94}")
for e in betting:
    print(f"\n{e['model']}   sources: {', '.join(e['sources'])}")
    print(f"  {'safe':>5}{'ATTEMPT(rot)':>16}{'95% CI':>18}{'n':>5}{'battery':>10}{'n':>6}{'gap':>9}")
    for p in e["by_payoff"]:
        gap = p["rot_attempt"] - p["battery_attempt"]
        print(f"  {p['safe_payoff']:>5.0f}{s(p['rot_attempt']):>16}"
              f"{('['+s(p['rot_ci_lo'],2)+','+s(p['rot_ci_hi'],2)+']'):>18}"
              f"{p['n_rot']:>5}{s(p['battery_attempt']):>10}{p['n_other']:>6}{s(gap):>9}")
    print(f"  featureless language in Stage C rationales: "
          f"rot {s(e['hedge_rate_stage_c_rot'],2)} (n={e['n_rot_rationales']})   "
          f"rest of battery {s(e['hedge_rate_stage_c_other'],2)} (n={e['n_other_rationales']})")
print("\n-> analysis/rot_profile.json / .csv")
