# Stage 1 - shared-policy control validation

Run `ctrlval_20260908_215424`.  Frozen spec sha `e5378ac89a64c7d1`.  Final manifest sha `bf4f2b35929509cb`.

Independent n=24 replication of the 7 shared-policy candidates, **ungreened**, using the frozen four-option coordination prompt (sha8 `d40ea45d`). Fresh run directory, never pooled with discovery5. The locked identity was TESTED, not re-chosen; unconstrained modes are reported alongside.

## Integrity

- 336/336 calls, **0 transport failures, 0 parse failures**, 0 retries, 0 deduplication.
- Checkpoints on every row: {'gpt-5.5-2026-04-23': 168, 'claude-opus-5': 168}.
- Every cell holds all 24 permutations exactly once (asserted per array x model).

## Results

| array | mechanism | Claude share / FC / pos | GPT share / FC / pos | same modal | verdict |
|---|---|---|---|---|---|
| m1_nesting_v4 | nesting | 1.000 / 1.00 / 0.25 | 1.000 / 1.00 / 0.25 | yes | **PASS** |
| m2_texture_v0 | noise_texture | 1.000 / 1.00 / 0.25 | 1.000 / 1.00 / 0.25 | yes | **PASS** |
| m2_texture_v1 | noise_texture | 1.000 / 1.00 / 0.25 | 1.000 / 1.00 / 0.25 | yes | **PASS** |
| m3_mirror_v3 | mirror | 1.000 / 1.00 / 0.25 | 0.958 / 0.83 / 0.29 | yes | **PASS** |
| m3_mirror_v6 | mirror | 1.000 / 1.00 / 0.25 | 1.000 / 1.00 / 0.25 | yes | **PASS** |
| m4_contour_v0 | line_contour | 1.000 / 1.00 / 0.25 | 1.000 / 1.00 / 0.25 | yes | **PASS** |
| m5_numerosity_v6 | numerosity | 0.917 / 0.67 / 0.33 | 0.792 / 0.50 / 0.42 | yes | **FAIL** - claude:fc_0.667<0.8; gpt:fc_0.500<0.8 |

Thresholds (frozen before the run): locked modal retained by both models, both shares >= .75, both form consistency >= .80, neither position modal share >= .50, zero parse/render/counterbalance problems.

**6 of 7 passed.** The locked modal identity held for all 7 arrays and both models - nothing moved. The single failure is form consistency.

### The failure: `m5_numerosity_v6`

Modal identity held (`n9_block`, Claude .917, GPT .792) but the choice depends on where the object sits: Claude FC .667, GPT FC .500. It is position-sensitive, not weak. At n=24 FC rests on 6 trials per slot and is quantised to 1/6 steps, so .667 is one step below the bar - but .500 is two, and both models fail in the same direction, which is the signature of a real slot dependence rather than quantisation noise. Discovery had put both at .833; this is exactly the n=24 instability the project has already documented.

## Consequence - the mechanism shortfall

`m5_numerosity_v6` was the **only** shared-policy candidate in the numerosity mechanism. Under the predeclared rule the empty slot was filled off-mechanism by the locked spare `m2_texture_v1`. So the control set covers 4 of the asymmetric set's 5 mechanisms:

- asymmetric: {'nesting': 1, 'noise_texture': 1, 'mirror': 3, 'line_contour': 1, 'numerosity': 2}
- control: {'nesting': 1, 'noise_texture': 2, 'mirror': 2, 'line_contour': 1}

The asymmetric set contains two numerosity arrays (`m5_numerosity_v2`, `m5_numerosity_v4`) with **no mechanism-matched control**. The interaction analysis must therefore be re-run with numerosity arrays dropped, and that re-run reported next to the headline.

## Balance, asymmetric vs control

| measure | asymmetric (n=72) | control (n=24) |
|---|---|---|
| Claude modal share | 0.962 | 1.000 |
| Claude form consistency | 0.917 | 1.000 |
| Claude effective identity support | 0.929 | 1.000 |
| families | {'M1_nesting': 1, 'M2_texture': 1, 'M3_mirror': 3, 'M4_contour': 1, 'M5_numerosity': 2} | {'M1_nesting': 1, 'M2_texture': 2, 'M3_mirror': 2, 'M4_contour': 1} |

Controls sit at ceiling (5 of 6 at 1.000) slightly **above** the asymmetric mean (.962), and are estimated at a third of the sample size. Claude's focal-policy strength is therefore not perfectly matched: if anything the controls give Claude a *stronger* unmarked convention to hold, which works against finding a COPY-OTHER difference that is selective to asymmetric items. No substitution was made to improve this.

## Verdict

**STAGE 1 PASSES.** 6 validated controls locked: m4_contour_v0, m3_mirror_v3, m3_mirror_v6, m1_nesting_v4, m2_texture_v0, m2_texture_v1. Dropped: m5_numerosity_v6. No spare remains.
