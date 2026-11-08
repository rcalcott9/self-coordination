# Study 2 — analysis plan (fixed before any Study 2 data exists)

## Notation
For item *i* and focal model *m*: **SELF_i** = m's empirical Stage A distribution over the 4
canonical shapes; **OTHER_i** = the partner family's empirical distribution. Predictions are
mapped from the focal's displayed slots back to canonical shape indices via the stimulus
permutation manifest before anything is computed.

`P_copy`, `P_diff` = mean predicted distribution per (item, focal, condition).

## Primary metric — relational gating

    G_i = [ TVD(P_copy, OTHER) - TVD(P_copy, SELF) ] - [ TVD(P_diff, OTHER) - TVD(P_diff, SELF) ]

Each bracket is "how much closer this prediction sits to SELF than to OTHER". G is the drop in
that quantity when the partner is relabelled DIFFERENT. **G > 0 means the prediction moved away
from the focal's own policy and toward the partner's** — the effect the study is testing.
G = 0 means partner identity did nothing. Reported per focal model, scenario-clustered
bootstrap over items.

## Secondary

1. **Relational shift (identity-free):** TVD(P_copy, P_diff). Does the distribution move at
   all? Can be > 0 while G = 0, which would mean movement in an uninformative direction.
2. **COPY self-match:** TVD(P_copy, SELF). Does the model predict its own behaviour when told
   the target is itself?
3. **DIFFERENT gating:** TVD(P_diff, OTHER) vs TVD(P_copy, OTHER).
4. **Target accuracy:** TVD(prediction, stated partner's empirical distribution) in each
   condition.

## Proper scoring

Multiclass **Brier** against the stated partner's empirical distribution:
`sum_k (p_k - q_k)^2`, where q is the partner's empirical distribution (soft target).
Reported alongside a log score as robustness. TVD is the interpretable descriptive metric;
Brier is the proper rule that determines accuracy claims.

## Reported at

- item level (13 items x 2 focal x 2 conditions)
- model level (aggregate per focal, the headline)
- with per-item CIs and a leave-one-item-out check, since 13 items is few

## Pre-specified exclusions
Any response whose four numbers do not sum to 100 +- 2, or that fails to parse, is dropped and
counted. No re-prompting, no repair.
