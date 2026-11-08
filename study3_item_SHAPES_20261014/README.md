# Study 3 item SHAPES: basic simultaneous Stag Hunt, same-model self-play (prepared 2026-10-14)

**Status:** prepared, not run. Offline validation passed. No API calls, no training. Both pilots
not authorised. Cumulative Study 3 M07/SHAPES API spend so far: **$0.04687** (all on M07).

## What changed from M07 (and why it is a new item)
- The four labels are now `CIRCLE`, `SQUARE`, `TRIANGLE`, `STAR`, each shown as `- NAME (label)`. KEEP is unchanged.
- Removed: the protocol descriptions and the sentence "The four labels are names of message protocols; all four work equally well, and other services in the setting exchange JSON."
- Unchanged:
  - the action and prediction templates (byte-identical to M07's: sha256 `f3289159…` / `1ef17834…`);
  - KEEP 7 / matching label 10 / otherwise 0;
  - per-call uniform shuffle of all five options;
  - parsing, pairing, scoring, order checks and prediction scoring.
- Seed namespace `20261014` (M07: `20261015`). The procedure is the same.
- **Removing protocol semantics and the explicit JSON cue changes the stimulus.** M07 observations (including the 4 GPT-5.5 format-check replies) must not be pooled with this item.
- M07, its prompts and all results are unchanged (27 files hash-identical before and after).

## Stimulus identity across models
Both models get identical text apart from the model name. This is checked offline: for the same slot and order, the GPT-5.5 and Opus 5 prompts are equal once the model name is masked. Each call still draws its own option order.

## Offline validation (`code/selfplay.py selftest`)
- **Rendered prompts:** every prompt has all five options exactly once, and orders vary.
- **Wording:** no protocol or JSON vocabulary appears in any rendered prompt (checked terms: json, protocol, base64, base85, hex, zlib, xml, binary, payload, encod, service, request, message).
- **Same text for both models:** the GPT-5.5 and Opus 5 prompts match once the model name is masked.
- **Scoring:** the synthetic-response checks inherited from M07 pass: identity scoring, no reuse in pairing, all-pairs shares, Brier and log-loss formulas, and the KEEP|label tie at p = .7.

## Files
- `prompts/action_selfplay.txt`, `prompts/prediction_selfplay.txt`: templates.
- `code/selfplay.py`: render / score / selftest; sha256 `527341f9…`.
- `manifest_PROPOSED.jsonl`: 120 rendered prompts (2 models × 40 action + 20 prediction); nothing sent; sha256 `30cd5890…`.
- No API runner has been copied here. One is needed (with the full logging from M07's runner) before any format check.

## Parser amendment (2026-10-14, recorded before pilot collection)
- **What changed:** the prediction parser now accepts an optional trailing `(label)` after CIRCLE / SQUARE / TRIANGLE / STAR and maps it to the bare identity. It is not accepted after KEEP. It applies identically to both models.
- **Unchanged:** all other validation rules, including duplicates after normalization being rejected. Raw replies are retained.
- **No prompt change.** The action parser is unchanged.
- **Trigger:** format-check call `gpt-5.5|fc_prediction|1` replied "CIRCLE (label): 4%" …, which was rejected under the original parser.
- **Records:** the original failure record (`results/run_20261014_002715/format_check_responses.jsonl`, `run_log.json`) is unchanged. The corrected parse of all 7 saved replies is appended as `format_check_amended_parse.jsonl`: 7/7 valid.
- **Offline checks** (selftest): the saved failing reply parses; a duplicate after normalization, "KEEP (label)", "(lab)", a double suffix and a bad sum are all rejected. `code/selfplay.py` sha256 7181cba7….
