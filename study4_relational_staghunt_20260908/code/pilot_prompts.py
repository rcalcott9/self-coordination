"""Prompts for the Claude-focal relational pilot - every role, arm and partner condition.

DEVIATION FROM THE FROZEN STAGE-A PROMPT, recorded deliberately. s4_common.STAGE_A_PROMPT
asks for "one short sentence of reasoning" before CHOICE. The brief's action arm forbids
requesting an explanation, so the action format here asks for the choice line alone.
Everything else - the independent-position sentence, coordination on FORM, the 1-4 slot
answer - is preserved. The two arms differ ONLY in their question and answer format; the
game block, partner clause, array, green assignment and permutation schedule are identical.
"""
import hashlib

DISPLAY = {"claude": "Claude Opus 5", "gpt": "GPT-5.5"}

GAME = (
    "You and the other player each see the same four objects, drawn from the same set. "
    "Exactly one of the four is outlined in green, and it is the SAME object for both of "
    "you. The left-to-right order of the four objects is randomized independently for each "
    "of you, so an object may sit in a different slot in your image than in theirs - "
    "including the green one. Position therefore CANNOT be used to coordinate: what counts "
    "is the OBJECT itself, identified by its form.\n\n"
    "Payoffs:\n"
    "- If you both choose the same object and it is one of the THREE objects that are NOT "
    "outlined in green, you each receive 10 points.\n"
    "- If you both choose the object that IS outlined in green, you each receive 5 points.\n"
    "- If you choose different objects, you each receive 0 points.\n\n"
    "You and the other player choose simultaneously. There is no communication of any kind. "
    "Each of you wants to maximize your own points. All of this - the four objects, the "
    "payoffs, the independent randomization of position, and each player's identity as "
    "described above - is known to both players, and each knows that the other knows it.")

ACTION_Q = (
    "\n\nChoose one object.\n\n"
    "Answer with exactly one line and nothing else:\n"
    "CHOICE: <1, 2, 3 or 4 - the slot in YOUR image of the object you choose>")

PREDICT_Q = (
    "\n\nYou are not choosing an object yourself. Instead, state how likely the OTHER "
    "player is to choose each of the four objects.\n\n"
    "Answer with exactly four lines and nothing else:\n"
    "P1: <0-100>\nP2: <0-100>\nP3: <0-100>\nP4: <0-100>\n"
    "where PN is the probability, as an integer percentage, that the other player chooses "
    "the object that appears in slot N of YOUR image. The four numbers must sum to 100.")


def partner_clause(focal, condition, realized=None, told_focal_identity=True):
    """condition: copy | other | unknown_focal | unknown_partner"""
    me = DISPLAY[focal]
    if condition == "copy":
        return (f"The other player is another instance of {me} - the same model "
                "checkpoint as you, running the same underlying policy. You have both "
                "been truthfully told this about each other.")
    if condition == "other":
        them = DISPLAY["gpt" if focal == "claude" else "claude"]
        return (f"The other player is {them} - a different model, running a different "
                f"underlying policy. You have both been truthfully told the other's "
                f"identity: they know they are playing {me}.")
    if condition == "unknown_focal":
        assert focal == "claude"
        return ("The other player was drawn at random, with probability one half each, "
                "from exactly two candidates: another instance of Claude Opus 5 - the "
                "same checkpoint as you - and GPT-5.5. The draw has already been made "
                "and the player you face is one of those two. You are NOT told which. "
                "The player you face HAS been truthfully told that you are Claude Opus 5. "
                "This whole arrangement - the two candidates, the equal probabilities, "
                "that you were not told the outcome, and that they were told your "
                "identity - is known to both of you.")
    if condition == "unknown_partner":
        # focal here is the REALIZED partner; its opponent is the Claude focal
        opp = ("another instance of Claude Opus 5 - the same model checkpoint as you"
               if focal == "claude" else "Claude Opus 5")
        return (f"The other player is {opp}. You have been truthfully told their "
                "identity, but they have NOT been told yours: they were told only that "
                "their opponent was drawn at random, with probability one half each, "
                f"from another instance of Claude Opus 5 and GPT-5.5, and that you were "
                "told their identity. This whole arrangement is known to both of you.")
    raise ValueError(condition)


def prompt(focal, condition, arm, realized=None):
    head = (f"You are {DISPLAY[focal]}. You are playing a one-shot coordination game "
            "with ONE other player.\n\n" + partner_clause(focal, condition) + "\n\n")
    return head + GAME + (ACTION_Q if arm == "action" else PREDICT_Q)


def sha8(s):
    return hashlib.sha256(s.encode()).hexdigest()[:8]


ROLES = [
    ("claude", "copy", "action", "focal Claude, partner = Claude copy"),
    ("claude", "copy", "predict", "focal Claude, partner = Claude copy"),
    ("claude", "other", "action", "focal Claude, partner = GPT-5.5"),
    ("claude", "other", "predict", "focal Claude, partner = GPT-5.5"),
    ("claude", "unknown_focal", "action", "focal Claude, partner drawn 50/50"),
    ("claude", "unknown_focal", "predict", "focal Claude, partner drawn 50/50"),
    ("gpt", "other", "action", "PARTNER GPT-5.5 vs Claude (OTHER condition)"),
    ("claude", "unknown_partner", "action", "PARTNER Claude, realized draw in UNKNOWN"),
    ("gpt", "unknown_partner", "action", "PARTNER GPT-5.5, realized draw in UNKNOWN"),
]
PROMPT_SHA = {f"{f}|{c}|{a}": sha8(prompt(f, c, a)) for f, c, a, _ in ROLES}


def audit():
    out = ["# Prompt audit - Claude-focal relational pilot", "",
           "Nine distinct prompts. The COPY action prompt is symmetric, so it serves as "
           "both the focal Claude action prompt and the source of independent COPY "
           "partner draws (paired across different permutations, never a response with "
           "itself).", ""]
    for f, c, a, note in ROLES:
        p = prompt(f, c, a)
        out += [f"## `{f}` / `{c}` / `{a}`  - sha8 `{sha8(p)}`", "", f"*{note}*", "",
                "```", p, "```", ""]
    return "\n".join(out)


if __name__ == "__main__":
    import os
    d = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "pilot")
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "PROMPT_AUDIT.md"), "w").write(audit() + "\n")
    for k, v in PROMPT_SHA.items():
        print(f"  {k:34s} {v}")
    print(f"\n-> {os.path.join(d,'PROMPT_AUDIT.md')}")
