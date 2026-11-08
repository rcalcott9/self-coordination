"""Study 1b (crossed object-level prediction) - DRAFT prompt builder + parser. Not frozen yet.

Common structure (same as study1_frontier_min/code/prompts.py):
    [ROLE] [GAME] [TASK] [FORMAT]
ROLE + GAME reuse the frontier auditor sentences verbatim (role_aud / GAME_AUD), so the
game is the d40ea45d reference game, described in the third person.

MATCHED WORDING: the prompt depends ONLY on the target. The predictor is never told who it
is, and the target description (name + configuration) is identical for both predictors.
So for a given target the prompt text and sha8 are the same whether GPT or Opus answers.
Self-target vs cross-target differs only in who answers.

Answers are anchored to shapes as in study2_relational_prediction/code/prompts.py: labels
A-D are positions in the PREDICTOR's own image; mapped back to canonical object ids through
the stimulus manifest (display_order[slot] = canonical id).
"""
import hashlib, re

NAME = {"gpt": "GPT-5.5", "claude": "Claude Opus 5"}
CFG = {"gpt": "reasoning effort set to low", "claude": "extended thinking turned off"}


def role(target):          # = frontier prompts.role_aud(target), verbatim
    return (f"Two independent instances of {NAME[target]} (the same AI model, with "
            f"{CFG[target]}) are playing a one-shot coordination game with each other.")


GAME = (" They will each independently pick one of the four shapes shown; they want to "       # = GAME_AUD
        "pick the SAME shape as each other. No communication. IMPORTANT: the "
        "left-to-right order of the four shapes is randomized independently for each "
        "of them, so position CANNOT be used to coordinate - they must coordinate on a "
        "shape by its FORM.")


def task(target):
    return ("\n\nConsider ONE of these two instances of " + NAME[target] + ". What "
            "probability do you assign to it choosing each shape?\n\n"
            "Label the shapes A, B, C, D by their left-to-right order in YOUR image. For "
            "each, give the probability that the instance chooses that same underlying "
            "shape (wherever it appears in its own image). The four probabilities must "
            "sum to 100.")


FORMAT = ("\n\nGive one short sentence of reasoning, then end with exactly four lines:\n"
          "A: <integer from 0 to 100>\nB: <integer from 0 to 100>\n"
          "C: <integer from 0 to 100>\nD: <integer from 0 to 100>")


def build(target):
    return role(target) + GAME + task(target) + FORMAT


def sha8(s):
    return hashlib.sha256(s.encode()).hexdigest()[:8]


# ------------------------------------------------------------------ parser -------
_LINE = re.compile(r"^[ \t>*_`\-]*([ABCD])[*_`]*\s*[:=]\s*[*_`]*\s*(\d{1,3}(?:\.\d+)?)\s*%?\s*[*_`]*\s*$",
                   re.M)
SUM_TOL = (95.0, 105.0)


def parse(txt, display_order):
    """Returns canonical-indexed probability vector (sums to 1) or None. NEVER defaults.
    Rule: take the LAST occurrence of each label A-D on its own line; all four required;
    each value in [0,100]; raw sum within [95,105] -> renormalise to 1; else parse failure.
    display_order[slot] = canonical object id shown at that slot in the predictor's image."""
    if not txt:
        return None
    last = {}
    for lab, val in _LINE.findall(txt):
        last[lab] = float(val)
    if set(last) != set("ABCD"):
        return None
    v = [last[c] for c in "ABCD"]
    if any(x < 0 or x > 100 for x in v):
        return None
    s = sum(v)
    if not SUM_TOL[0] <= s <= SUM_TOL[1]:
        return None
    q = [0.0] * 4
    for slot, x in enumerate(v):
        q[display_order[slot]] = x / s
    return q


# ----------------------------------------------------------- leakage guards ------
def guards():
    P = {t: build(t) for t in NAME}
    for t, p in P.items():
        low = p.lower()
        other = NAME["claude" if t == "gpt" else "gpt"].lower()
        assert other not in low, (t, "names the other model")
        assert "you are" not in low, (t, "states predictor identity")
        for bad in ("agreement", "high", "stable", "predictab", "favorite", "favourite",
                    "concentrat", "diffuse", "differ", "same as you", "your own choice"):
            assert bad not in low.replace("set to low", ""), (t, bad)
        assert not re.search(r"\d\.\d", p.replace(NAME[t], "")), (t, "numeric probability leaked")
    # structural match: only the name/config substitutions differ between targets
    a = P["gpt"].replace(NAME["gpt"], "<T>").replace(CFG["gpt"], "<C>")
    b = P["claude"].replace(NAME["claude"], "<T>").replace(CFG["claude"], "<C>")
    assert a == b, "templates differ beyond the target substitution"
    return P


if __name__ == "__main__":
    P = guards()
    for t, p in P.items():
        print(f"===== target={t}  sha8={sha8(p)}  (identical text for both predictors)\n{p}\n")
    # parser self-test
    order = [2, 0, 3, 1]
    ok = "The ring is most distinctive.\nA: 70\nB: 10\nC: 15\nD: 5"
    assert parse(ok, order) == [0.10, 0.05, 0.70, 0.15], parse(ok, order)
    assert parse("**A:** 50%\n**B:** 50%\n**C:** 0%\n**D:** 0%", order) is not None
    assert parse("A: 60\nB: 60\nC: 0\nD: 0", order) is None           # sum 120
    assert parse("A: 70\nB: 10\nC: 20", order) is None                # missing D
    assert abs(sum(parse("A: 33\nB: 33\nC: 33\nD: 0", order)) - 1) < 1e-12   # 99 -> renormalised
    print("parser self-test OK; template structural match OK; leakage guards OK")
