"""Study 1b crossed object-level prediction prompt: FINAL (2026-10-07).

ONE template for all four predictor x target cells. The text differs ONLY in the target's display
name and configuration, and is identical across predictors, including the self case. The predictor
is never told whether it is the target. All four cells of an array use the same balanced ordering
schedule, so the images are identical.

Order resolution: RANDOM-ORDER prediction. The predicted quantity is the target's choice over
underlying shapes when the target sees the four shapes in an independently randomized order.
This is the condition stated in the target's own reference prompt (d40ea45d). The scoring draws
are fresh d40ea45d choices whose orderings are balanced across shapes x slots, so the empirical
canonical distribution estimates exactly that marginal. Displayed-order prediction was rejected:
d40ea45d tells the target that order is randomized, and per-ordering target distributions would
need about 24x more scoring draws.

Response: four probabilities A-D anchored to left-to-right positions in the PREDICTOR's image.
common.parse_pred maps them to canonical shapes via the perm manifest, requires all four and a
sum of 95-105, renormalises, and never defaults.
"""
PLACEHOLDER = False
NAME = {"gpt": "GPT-5.5", "claude": "Claude Opus 5"}
CFG = {"gpt": "reasoning effort set to low", "claude": "extended thinking turned off"}


def build_predict(predictor, target):
    assert predictor in NAME and target in NAME
    n, c = NAME[target], CFG[target]
    role = (f"An instance of {n} (with {c}) is playing a one-shot coordination game with ONE other "
            f"player - another instance of {n}.")
    game = (" Each player independently picks one of the four shapes shown and wants to pick the SAME "
            "shape as the other player. No communication. IMPORTANT: the left-to-right order of the "
            "four shapes is randomized independently for each player, so position CANNOT be used to "
            "coordinate - each must choose a shape by its FORM. The instance therefore sees these same "
            "four shapes, possibly in a different left-to-right order from your image.")
    task = (f"\n\nWhat probability do you assign to that instance of {n} choosing each shape? Label the "
            "shapes A, B, C, D by their left-to-right position in YOUR image; for each, give the "
            "probability that it chooses that underlying shape (wherever it appears in its own image). "
            "The four probabilities must sum to 100.")
    fmt = ("\n\nGive one short sentence of reasoning, then end with exactly four lines:\n"
           "A: <integer from 0 to 100>\nB: <integer from 0 to 100>\nC: <integer from 0 to 100>\n"
           "D: <integer from 0 to 100>")
    return role + game + task + fmt
