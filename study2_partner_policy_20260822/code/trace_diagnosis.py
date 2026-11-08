"""
Why did Study 2's GPT arm return no partner effect? A trace-level diagnosis.

EXPLORATORY AND POST HOC. Nothing here was pre-specified; it does not touch the
frozen primary analysis and cannot change its verdict. Lexical counts measure what
a rationale SAYS, which is not the same as what the policy DOES - the project's
own 2026-08-13 result is precisely that these two come apart. Read accordingly.

THE QUESTION. The frozen analysis found no partner effect at all: not the
dose-response (MODEL B), not even a constant same-model shift (MODEL A), with
MODEL 0 winning out of sample. Three mechanisms would produce that, and they are
distinguishable in the traces:

  IGNORED     the partner is never attended to. The rationale does not mention it,
              and the decision is made on stimulus salience alone.
  ATTENDED-
  BUT-UNUSED  the partner is named and discussed, but the decision does not move
              with it. Partner information reaches the rationale and stops there.
  MISPRICED   the partner is attended AND used, but in the wrong direction or on
              the wrong quantity - e.g. treating "a different model" as generic
              uncertainty rather than as a specific policy that agrees on some
              stimuli and disagrees on others.

The decisive split is PARTNER-MENTIONED vs NOT: if a partner effect appears only
inside the mentioned subset, the null is an attention failure, not a strategic
one. That subset split is post hoc and self-selected - a model that mentions the
partner may differ in other ways - so it is reported as a diagnostic, never as an
estimate of a causal effect.

Reuses the frozen lexicons from reasoning_traces/trace_analysis.py verbatim where
they apply, so the numbers are comparable to the 2026-08-13 analysis.

Run:  python3 trace_diagnosis.py
"""
import csv, json, os, random, re, statistics, sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
S2 = os.path.dirname(HERE)
DATA = os.path.join(S2, "data", "study2C_20260822_173757.csv")   # GPT arm, complete
OUT = os.path.join(S2, "analysis")
SEED, BOOT = 20260823, 5000

# ---- frozen lexicons, copied verbatim from reasoning_traces/trace_analysis.py
HEDGE = re.compile(r"(unclear|ambiguous|not obvious|no (?:clear|obvious|strong)|"
                   r"hard to|difficult to|weak(?:ly)?|too similar|very similar|"
                   r"little to distinguish|toss-?up|coin[- ]?flip|50[/-]?50|"
                   r"arbitrar|uncertain|either way|no reliable|lacks?)", re.I)
SALIENT = re.compile(r"(salient|distinctive|obvious|focal|canonical|stands out|"
                     r"more (?:visually )?(?:striking|prominent|notable)|clearly)", re.I)

# ---- new, built by reading the Study 2 corpus first
# Any reference to the partner at all, in either arm's vocabulary.
PARTNER_ANY = re.compile(r"(claude|gpt|opus|another instance|other instance|"
                         r"identical model|same model|different model|a copy|copies|"
                         r"the other (?:player|model|agent|instance)|my copy|"
                         r"other ai|another ai|partner)", re.I)
# Names a SPECIFIC model - the manipulation actually landing in the text.
PARTNER_NAMED = re.compile(r"(claude|gpt|opus)", re.I)
# Reasons about the partner's POLICY rather than merely its existence.
POLICY_TALK = re.compile(r"(same (?:policy|training|model|architecture)|"
                         r"different (?:policy|training|model|architecture)|"
                         r"trained|shares? my|share the same|like me|as i would|"
                         r"i would (?:choose|pick)|my own choice|same way i|"
                         r"differently than|differ from me|another model might|"
                         r"may not (?:share|agree)|might not (?:share|agree))", re.I)


def rationale(r):
    return re.split(r"DECISION:", r.get("response_raw", ""), flags=re.I)[0]


def boot_ci(vals, seed, b=BOOT):
    if not vals:
        return float("nan"), float("nan")
    rng = random.Random(seed)
    n = len(vals)
    d = sorted(statistics.fmean(rng.choices(vals, k=n)) for _ in range(b))
    return d[int(0.025 * b)], d[int(0.975 * b)]


def diff_ci(a, b, seed, nb=BOOT):
    """Bootstrap CI on mean(a) - mean(b), resampling each group independently."""
    if not a or not b:
        return float("nan"), float("nan"), float("nan")
    rng = random.Random(seed)
    d = sorted(statistics.fmean(rng.choices(a, k=len(a)))
               - statistics.fmean(rng.choices(b, k=len(b))) for _ in range(nb))
    return statistics.fmean(a) - statistics.fmean(b), d[int(0.025 * nb)], d[int(0.975 * nb)]


rows = [r for r in csv.DictReader(open(DATA))
        if r["valid_response"] == "True" and r.get("included_in_analysis") != "False"]
for r in rows:
    r["_rat"] = rationale(r)
    r["_att"] = 1.0 if r["participation_decision"].upper().startswith("ATTEMPT") else 0.0
    r["_adv"] = float(r["compatibility_advantage"])

print(f"\n{'='*94}\nTRACE DIAGNOSIS - GPT-5.5 arm, {len(rows)} valid trials"
      f"\n{'='*94}")
print("EXPLORATORY / POST HOC. Does not touch the frozen primary analysis.\n")

# =============================================== 1. does the manipulation land?
print(f"{'-'*94}\n1. DOES THE PARTNER MANIPULATION REACH THE RATIONALE AT ALL?\n{'-'*94}")
print(f"  {'condition':<12}{'n':>6}{'any partner ref':>18}{'names a model':>16}"
      f"{'policy talk':>14}{'salience talk':>15}{'hedging':>10}")
for w in ("same", "different"):
    sub = [r for r in rows if r["partner_condition"] == w]
    f = lambda rx: statistics.fmean([bool(rx.search(r["_rat"])) for r in sub])
    print(f"  {w:<12}{len(sub):>6}{f(PARTNER_ANY):>18.3f}{f(PARTNER_NAMED):>16.3f}"
          f"{f(POLICY_TALK):>14.3f}{f(SALIENT):>15.3f}{f(HEDGE):>10.3f}")

# ================================= 2. the decisive split: mentioned vs not
print(f"\n{'-'*94}\n2. PARTNER EFFECT, SPLIT BY WHETHER THE RATIONALE MENTIONS THE PARTNER\n{'-'*94}")
print("  If a partner effect exists ONLY where the partner is mentioned, the null is an\n"
      "  ATTENTION failure. If it is absent in both, the information is attended and unused.\n"
      "  The split is self-selected and post hoc - a diagnostic, not a causal estimate.\n")
print(f"  {'subset':<22}{'n same':>8}{'n diff':>8}{'P(att|same)':>13}{'P(att|diff)':>13}"
      f"{'effect':>10}{'95% CI':>20}")
for label, pred in (("mentions partner", lambda r: bool(PARTNER_ANY.search(r["_rat"]))),
                    ("does not mention", lambda r: not PARTNER_ANY.search(r["_rat"])),
                    ("names a model", lambda r: bool(PARTNER_NAMED.search(r["_rat"]))),
                    ("policy talk", lambda r: bool(POLICY_TALK.search(r["_rat"])))):
    sm = [r["_att"] for r in rows if r["partner_condition"] == "same" and pred(r)]
    df = [r["_att"] for r in rows if r["partner_condition"] == "different" and pred(r)]
    if not sm or not df:
        print(f"  {label:<22}{len(sm):>8}{len(df):>8}{'  - empty cell -':>36}")
        continue
    e, lo, hi = diff_ci(sm, df, SEED)
    print(f"  {label:<22}{len(sm):>8}{len(df):>8}{statistics.fmean(sm):>13.3f}"
          f"{statistics.fmean(df):>13.3f}{e:>+10.3f}"
          f"{('['+f'{lo:+.3f}'+','+f'{hi:+.3f}'+']'):>20}")

# ================================ 3. does mentioning scale with the advantage?
print(f"\n{'-'*94}\n3. MENTION RATE BY STIMULUS - is the partner attended MORE where it matters?\n{'-'*94}")
print("  Under a policy-specific account the model should think about the partner most on\n"
      "  stimuli where partner identity actually changes the payoff.\n")
print(f"  {'stimulus':<14}{'adv':>8}{'tier':<13}{'mention|same':>14}{'mention|diff':>14}"
      f"{'named|diff':>12}{'policy talk':>13}")
by_stim = defaultdict(list)
for r in rows:
    by_stim[r["stimulus"]].append(r)
for sid in sorted(by_stim, key=lambda s: -by_stim[s][0]["_adv"]):
    sub = by_stim[sid]
    sm = [r for r in sub if r["partner_condition"] == "same"]
    df = [r for r in sub if r["partner_condition"] == "different"]
    g = lambda ss, rx: statistics.fmean([bool(rx.search(r["_rat"])) for r in ss]) if ss else float("nan")
    print(f"  {sid:<14}{sub[0]['_adv']:>+8.3f}{sub[0]['tier']:<13}"
          f"{g(sm, PARTNER_ANY):>14.3f}{g(df, PARTNER_ANY):>14.3f}"
          f"{g(df, PARTNER_NAMED):>12.3f}{g(sub, POLICY_TALK):>13.3f}")

# ============================ 4. the action-choice test on the anti-coordinated cell
print(f"\n{'-'*94}\n4. SECONDARY (spec section 12): does the CHOSEN FORM move with the partner?\n{'-'*94}")
print("  On an anti-coordinated stimulus the two models are decisive on OPPOSITE identities.\n"
      "  A model that modelled its partner's policy should ABANDON its own convention when\n"
      "  told the partner is the other model. This is the strongest available evidence of\n"
      "  fine-grained policy knowledge, and it is free - the choice is already collected.\n")
print(f"  {'stimulus':<14}{'adv':>8}{'modal|same':>22}{'modal|diff':>22}{'share same':>12}{'share diff':>12}")
for sid in sorted(by_stim, key=lambda s: -by_stim[s][0]["_adv"]):
    sub = [r for r in by_stim[sid] if r["_att"] == 1.0 and r.get("parsed_choice_identity")]
    if not sub:
        continue
    out = []
    for w in ("same", "different"):
        ids = Counter(r["parsed_choice_identity"] for r in sub if r["partner_condition"] == w)
        if not ids:
            out.append(("-", float("nan")))
            continue
        top, c = ids.most_common(1)[0]
        out.append((top, c / sum(ids.values())))
    print(f"  {sid:<14}{by_stim[sid][0]['_adv']:>+8.3f}{out[0][0]:>22}{out[1][0]:>22}"
          f"{out[0][1]:>12.3f}{out[1][1]:>12.3f}")

os.makedirs(OUT, exist_ok=True)
print(f"\n{'-'*94}\nNote: `visible_reasoning` is present on "
      f"{sum(1 for r in rows if r.get('visible_reasoning','').strip())}/{len(rows)} trials "
      f"({100*sum(1 for r in rows if r.get('visible_reasoning','').strip())/len(rows):.0f}%),\n"
      "a provider-summarised subsample, so it is described but never used for inference.")
