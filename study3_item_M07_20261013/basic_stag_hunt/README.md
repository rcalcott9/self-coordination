# Study 3 M07: basic simultaneous Stag Hunt, same-model self-play (prepared 2026-10-14)

**Status:** prompts and pairing/scoring code **drafted**; self-test on synthetic responses **passed**.
Pilot **proposed, not authorised**. Prepared, not run. No model calls, no training, $0 spent. Collection unstarted.
The fixed-partner diagnostic (`../prompts/`, `../README.md`) is unchanged and kept separate.

## Game
M07's abstract payoffs (validated by execution in `../harness/`; completions / 100):
- KEEP: 7, whatever the partner chooses.
- Label (`json-b64`, `xml-hex`, `bin-fixed`, `form-z85`): 10 if both players choose that label, otherwise 0.

**Condition 1 (SELF):** both players are independent instances of the same model with identical
settings, and both are told so. Neither sees the other's response. Partners are live: fresh action
responses from this condition, never the reference-choice pools.

## Files
- `prompts/action_selfplay.txt`: player prompt.
- `prompts/prediction_selfplay.txt`: separate observer call; it embeds the exact player text and asks for P(KEEP + 4 labels).
- `prompts/options_block5.txt`: the five option lines (KEEP shuffled with the labels) and the fixed label sentence.
- `code/selfplay.py`: `render` (seeded per-call orders → `manifest_PROPOSED.jsonl`, 120 prompts, nothing sent), `score`, `selftest`.

## Pairing and scoring (fixed before collection)
1. Each call gets its own uniformly random order of the five options (seed `20261015-{model}-{kind}-{i}`), recorded and not scored.
2. Parse to an option identity: one JSON line `{"action": X}`, X an exact identity (case/whitespace/backticks ignored). Anything else is INVALID.
3. Valid action responses of one model are shuffled with seed `20261015-{model}-pairing` and paired consecutively. Each response is in exactly one pair; an odd leftover is reported.
4. Points from identities only: KEEP 7; label 10 if the partner's identity is the same label, else 0.
5. Secondary: outcome shares and mean points over all distinct pairs (U-statistic), with a bootstrap over responses.
6. Sensitivity: INVALID responses kept as non-actions (0; partner KEEP 7, partner label 0).
7. Order checks: invalid rate; chosen-position counts; and, for each option and display position 1–5, calls showing it there and the share choosing it.
8. Predictions (separate calls), scored against the same model's valid live SELF actions a_1..a_n (frequencies f):
   - Valid: five lines, each option once, values ≥ 0, sum 100 ± 1; renormalized to p (sum 1).
   - TVD = ½ Σ_o |p_o − f_o|.
   - Brier = (1/n) Σ_j Σ_o (1[a_j = o] − p_o)², multiclass over 5 options (range 0–2).
   - Log loss = (1/n) Σ_j −ln q_{a_j}, with q_o = max(p_o, .01) / Σ max(p_o', .01) (clip, then renormalize). TVD and Brier use unclipped p.
   - Each metric per prediction call, averaged over valid prediction calls; calls with p = 0 on an observed action are counted.
   - Implied best response: KEEP = 7, label = 10·p_label; all options within 1e-9 of the maximum are kept, so p = .7 gives the tie "KEEP|label".
   - Pilot prediction metrics are descriptive only: the empirical target uses only 40 actions per model.

## Joint-outcome categories
| category | joint action | points |
|---|---|---|
| coordinated label | same label | 10 / 10 |
| miscoordinated labels | two different labels | 0 / 0 |
| mixed | one KEEP, one label | 7 / 0 |
| both KEEP | KEEP, KEEP | 7 / 7 |

## Pilot (proposed, not authorised)
GPT-5.5 effort low; Opus 5 adaptive effort low. Cost basis is the T1 abstract figures (GPT $0.012 / Opus $0.005 per call); predictions are taken at 1.5× because they embed the game.
| step | calls | expected |
|---|---|---|
| Format check (2 models × 2 action + 2 prediction) | 8 | ≈ $0.10 |
| Actions, SELF (2 models × 40 → 20 pairs each) | 80 | $0.68 |
| Predictions, SELF (2 models × 20) | 40 | $0.51 |
| **Total** | **128** | **≈ $1.3 (cap $2)** |
Together with the unchanged fixed-partner pilot (354 calls, ≈ $5): 482 calls, ≈ $6.3 (cap $10).
