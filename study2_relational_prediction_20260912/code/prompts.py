"""Study 2 prompts. Prediction only - no game, no payoffs, no coordination choice."""
DISPLAY = {"gpt": "GPT-5.5", "claude": "Claude Opus 5"}

BASE = ("You are {focal}. You are looking at the four shapes below.\n\n"
        "Another AI model is shown these same four shapes, in an independently randomized "
        "left-to-right order. That model is {target}.\n\n")

TARGET = {
 "COPY": "another independent instance of you - the same model, with the same policy",
 "DIFFERENT": "{other} - a different model, developed separately",
}

# The two images are independently shuffled, so "A" is ambiguous across them unless the
# question is anchored to the FOCAL's own image and to the SHAPE rather than the slot.
ASK = ("What probability do you assign to the other model choosing each option?\n\n"
       "Label the options A, B, C, D by their left-to-right order in YOUR image. For each, "
       "give the probability that the other model chooses that same underlying shape "
       "(wherever it happens to appear in their own image).\n\n"
       "Return probabilities for all four options that sum to 100%. Answer with exactly "
       "four lines and nothing else:\n"
       "A: __%\nB: __%\nC: __%\nD: __%")


def build(focal, cond):
    other = DISPLAY["claude" if focal == "gpt" else "gpt"]
    tgt = TARGET[cond].format(other=other)
    return BASE.format(focal=DISPLAY[focal], target=tgt) + ASK


if __name__ == "__main__":
    for f in ("gpt", "claude"):
        for c in ("COPY", "DIFFERENT"):
            print(f"===== focal={f}  condition={c} =====")
            print(build(f, c)); print()
