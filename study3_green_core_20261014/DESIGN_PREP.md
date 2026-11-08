# GREEN core — preparation (2026-10-14)

Local preparation only. No model calls were made, nothing was collected and nothing was spent.

**Preserved unchanged**
- SHAPES (all raw records, and its original bootstrap interval [4.48, 5.73]; the copy-excluded resampling is not adopted).
- M07.
- The archived GREEN pilot.

**Kept separate:** fixed-partner diagnostics. **Deferred:** bargaining extensions.

## Concrete preparation changes (done)

**1. Candidates frozen before any new outcome** (`FROZEN_CANDIDATES.json` + `.sha256`, built by `code/freeze_candidates.py`)
- The 14 archived pilot arrays are frozen. For each one the file records:
  - its objects, GREEN index and object;
  - sha256 of all 24 archived PNGs, `manifest.json` and `green.json`.
- The old labels ("asymmetric" / "control", mechanism, strong/weak) are kept only as **historical strata**, together with their source runs and prompt.
- Pilot responses were not opened.
- No item will be dropped or relabelled on the basis of new measurements.
- Not in the pilot, listed but not frozen as core items:
  - `m5_numerosity_v6`: failed control validation before the pilot;
  - `m2_texture_v1`: an unused spare.

**2. m3_mirror_v6 restored**
- **Renderer:** `make_pilot_stimuli.render_array` with the `make_battery5` M3 variant 6 callables (SEED 20260909).
- **Objects:** [sym3, twinTrue, sym1, sym2]. Cue rules: threefold_symmetry→0, mirrored_pair→1, most_irregular→2, bilateral_symmetry→3, most_compact→3.
- **GREEN:** index 3, `sym2`, chosen with seed 20260908. Outline #0E9F4F, line width 6.
- **Check:** the permutation mapping and the GREEN position per permutation are identical to the archive, and the re-render matches pixel for pixel (max diff 0.0).
- **Stimuli to send:** the PNG bytes differ (encoder metadata), so the **archived files, identified by sha256, are the stimuli**. The re-render is only a check.

**3. Prompts** (`code/green_core_prompts.py` → `prompts/PROMPTS_RENDERED.md`)
- The game block, action question and prediction question are imported verbatim from the archived `pilot_prompts.py`.
- Every reused archived prompt is checked against its archived sha8.
- The only new text is the WITHHELD clause.

| cell | Claude prompt (action / predict) | GPT prompt (action / predict) | pairing |
|---|---|---|---|
| COPY × disclosed | `ef91ca28` / `e289f820` (archived, sent) | `ce258781` / `e92b41b4` (archived builder, **never sent**) | within model |
| DIFFERENT × disclosed | `c54aeae8` / `ed1c57e9` (archived, sent) | `de185e62` (sent as partner) / `5835d8fe` (**never sent**) | Claude × GPT |
| COPY × withheld | `ca7ce3b8` / `5e31720d` (NEW) | `902f85cb` / `15c0dcf9` (NEW) | within model |
| DIFFERENT × withheld | same withheld prompts | same withheld prompts | Claude × GPT |

- **WITHHELD clause:** "The other player is an AI model. You are not told which model it is or how it was produced, and it has been told exactly the same about you."
- **Symmetric information:** in every cell both players receive the same kind of description.
  - The archived UNKNOWN cell was asymmetric (the focal player was not told the partner's identity, but the partner was told the focal player's), so it is not used.
- **Withheld pool:** under WITHHELD the prompt does not depend on the actual partner. One withheld pool per model therefore serves both actual partners; only the pairing differs.
- **Predictions:** separate calls with the archived P1–P4 format (slot in the player's own image, mapped back to object identity through the frozen manifest).

**4. Proposed independent policy-measurement split** (not built; no job list)
- **Draws:** for each model × prompt (copy, other, withheld) × array, take 48 action draws, i.e. each of the 24 permutations twice.
- **Assignment:** a seed fixed before collection assigns one draw per permutation to POLICY and the other to LIVE.
- **POLICY set**, used to describe each array:
  - the in-game action distribution;
  - COPY compatibility: within-model self-match, a U-statistic over different permutations;
  - DIFFERENT compatibility: the Claude × GPT match rate.

  These are reported as **measured covariates**. They never define strength, never relabel an item and never drop one.
- **LIVE set**, the only set paired for payoffs:
  - COPY: within model, across different permutations;
  - DIFFERENT: Claude × GPT within the same disclosure state.
- **Predictions:** 24 per model × prompt × array, scored against the actual partner's LIVE distribution. Each WITHHELD prediction is scored against both actual partners.
- **Size:** 288 action calls + 144 prediction calls = 432 calls per array. Not costed; no collection.

**5. Same-game measurements found** (archived pilot `pilot_run_20260908_231250`; counts for m3_mirror_v6 only; outcomes not examined)

| model / settings | role and cell | n | prompt |
|---|---|---|---|
| Claude Opus 5: adaptive thinking (summarized), effort low, max_tokens 4000; image before text | focal action COPY / OTHER / UNKNOWN | 24 / 24 / 24 | ef91ca28 / c54aeae8 / 60b60492 |
| | focal predict COPY / OTHER / UNKNOWN | 24 / 24 / 24 | e289f820 / ed1c57e9 / f97a59ca |
| | partner action UNKNOWN | 12 | fd611221 |
| GPT-5.5-2026-04-23: reasoning effort low, summary auto, no output cap; text before image | partner action OTHER / UNKNOWN | 24 / 12 | de185e62 / 5053da40 |

- No GPT COPY action, GPT predictions or WITHHELD measurements exist in the GREEN game.
- Earlier m3_mirror_v6 measurements (discovery5 n = 24, ctrlval n = 24) used the **Stage A prompt** (`d40ea45d`): pure coordination with a copy, no GREEN, no payoffs. None of the existing validations included the GREEN option or the strategic payoffs.

**6. Flags**
- **Selection on COPY-frame outcomes:**
  - Every historical label comes from Stage A, which is a copy-framed coordination game.
  - The 8 asymmetric arrays were selected on confirm5 results (n = 72).
  - The controls were chosen from discovery5 and then retained by the rule "Claude modal share closest to .962".
  - The GREEN placement excluded Claude's modal object and any object with ≥ .35 share of either model's choices.

  All of these are frozen as they were and are disclosed.
- **In the GREEN pilot, COPY partners were drawn from the focal COPY calls themselves.** The split in item 4 removes this overlap.
- **Missing provenance in the pilot:**
  - Rows keep only the visible text and token counts: no stop reason, reasoning summaries, raw response or response id.
  - Settings can be recovered only from `run_pilot.py`.
  - `repair/` is byte-identical to `data/`.
  - `data/pilot_s0of1.jsonl` is an earlier single-shard pass (155 rows; 131 job keys also appear in the four shards). Because the analysis reads it first, its rows win ties. m3_mirror_v6 is not affected.
- **Choice of worked item:** the record of why m3_mirror_v6 was chosen as the worked item, and whether pilot outcomes had been seen at that point, is missing. Treat it as a worked example, not a sampled item.

**7. Migration changes needed for an exact match to the GREEN payoff table**

| | GREEN game (archived) | M07 executable (implemented) | required change |
|---|---|---|---|
| options | 4 objects, 1 marked GREEN | KEEP + 4 labels (5 options) | 4 formats, 1 publicly marked (GREEN analogue); **remove KEEP** |
| marked option | 5 each, only if both choose it | KEEP 700 whatever the partner does | Marked format delivers **500 only when both services use it**. Rewire the broker so it relays only between two registered peers; a lone user gets 0. |
| same unmarked option | 10 each | 1,000 | unchanged (1,000) |
| any mismatch, including marked vs unmarked | 0 each | 0 | 0 for both |
| validation | n/a | 25 profiles × 3 reps exact | all 16 profiles × 3 reps over localhost TCP; must measure exactly 1,000 / 500 / 0 |

- Points = jobs / 100.
- The mark must be the same object for both players and must not be coded by position. Option order stays independently shuffled.
- The m3_mirror_v6 images cannot be the migration options. The migration needs its own item, frozen in the same way.

## Unresolved decisions

1. **Payoff for a GREEN match:** 5 (archived; exact restoration) or 7 (the earlier core proposal).
   - Choosing 7 creates a new game that cannot be pooled with the pilot.
   - The GREEN-placement rule was justified by "green pays 5".
   - The migration figure follows this choice: 500 or 700.
2. **Archived disclosure wording:** "same / different underlying policy". Keep it for exact restoration, or remove it?
   - For m3_mirror_v6, the historical labels show the same modal object for both models, so "different underlying policy" is not established.
3. **WITHHELD clause:** approve the wording.
4. **Scope:** is m3_mirror_v6 only the worked example, with all 14 frozen arrays as the core?
5. **Image/text order:** keep the archived per-model order (Claude image→text, GPT text→image), or make it the same for both models?
6. **Split:** approve 1 POLICY + 1 LIVE draw per permutation (48 per cell), and the seed.
7. **Logging and caps for any new run:** adopt M07 full logging (stop reason, usage, blocks, raw, reasoning summaries)? Add a GPT `max_output_tokens` of 4000? The archived pilot had no GPT cap, so adding one is a settings change.
8. **Migration item:** which four formats to use, and which one carries the public mark.
