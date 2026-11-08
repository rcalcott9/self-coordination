"""
FROZEN trace-coding rubric v1. Written 2026-09-10 after inspecting a 24-trace stratified
random sample (seed 20260910) and BEFORE coding the full set.

Construct: does the trace explicitly represent the choice as a coordination GAMBLE
against the safe outside option?

  A  PAYOFF_ENGAGED  - references the outside option, the odds of matching, an
                       expected-value/risk tradeoff, or sufficiency of confidence
  B  SHAPE_ONLY      - reasons about form/salience and picks, with none of A
  C  OTHER           - neither (e.g. pure output-format deliberation)

Precedence A > B > C: a trace that does both A and B is A, because the construct is
whether the gamble is represented at all.

KNOWN LIMITATION, recorded before coding. The two arms' `visible_reasoning` fields are
different artifacts: GPT = OpenAI reasoning summary (median 477 chars, 100% headed,
74% discussing output format); Opus = Anthropic summarized thinking (median 159 chars,
0% / 0%). Category RATES ARE NOT COMPARABLE ACROSS MODELS. Only the within-model
gradient over payoff is interpretable, because that holds the summarizer fixed.
"""
import re


# A - the gamble is represented
# v2 (2026-09-10): bare "safe payoff" REMOVED. The response format is
# `DECISION: <ATTEMPT or SAFE>`, and GPT's summaries deliberate about which literal
# string to write ("I should probably start with 'Safe payoff,' then ...") -- caught as a
# false positive during blind validation of v1. Retained forms all require the outside
# option to be reasoned ABOUT, not merely named as an output token.
OUTSIDE = (r"(safe (option|choice|bet)|guaranteed|walk away|take the (safe|guaranteed)|"
           r"play(ing)? it safe|safer (option|choice|to)|beat a guarantee|"
           r"prioriti[sz]e safety|choos(e|ing) the safest)")
# v3: bare "chance" disambiguated. "a chance that symmetry affects the selection" is
# possibility, not matching odds; "a high chance of the same model selecting it" is odds.
# Require chance/likely to sit near a matching/coordination referent.
ODDS    = (r"(probabilit|odds|\d{1,3}\s*%|likelihood|50/50|coin ?flip|"
           r"chance (of|that)?[^.]{0,60}?(match|same|coordinat|pick|choos|instance)|"
           r"(match|coordinat)[^.]{0,60}?\b(chance|likely|probable)\b)")
TRADE   = r"(expected value|\bEV\b|risk[- ]reward|worth (the )?(risk|attempt)|not worth|beat a guaranteed|versus a guarantee|stakes)"
CONF    = r"(confiden(t|ce)|sure enough|high enough|not (confident|sure)|threshold)"
A_PAT = re.compile("|".join((OUTSIDE, ODDS, TRADE, CONF)), re.I)

# B - form/salience reasoning
B_PAT = re.compile(r"(shape|circle|square|triangle|star|chevron|arrow|dot|stripe|curve|arc|"
                   r"hexagon|polygon|spiral|texture|salien|focal|distinctive|natural|default|"
                   r"stands out|darker|lighter|denser|sparser|bigger|larger|smaller)", re.I)

# excluded from B: output-format deliberation only
FMT_PAT = re.compile(r"(answer format|output format|two lines|exactly two|line count|formatting)", re.I)


def code(trace):
    t = (trace or "").strip()
    if not t:
        return "C_OTHER", "empty"
    a = bool(A_PAT.search(t))
    b = bool(B_PAT.search(t))
    if a:
        return "A_PAYOFF_ENGAGED", "gamble represented"
    # v3: B is the DEFAULT for any substantive non-A trace. v2 required a hit on a fixed
    # shape-word list, which produced spurious C on perfectly ordinary shape reasoning
    # ("fatter, wider petals rather than thin spokes"). C is now reserved for traces that
    # are empty or contain nothing but output-format deliberation.
    stripped = FMT_PAT.sub("", t)
    if b or len(stripped.split()) >= 12:
        return "B_SHAPE_ONLY", "form/salience or other task content, no gamble"
    return "C_OTHER", "empty or format-only"
