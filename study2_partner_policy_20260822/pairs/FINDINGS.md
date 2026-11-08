# Study 2 is NOT identifiable on the 15-stimulus battery

**Headline: zero clean Study-2 pairs exist for GPT-5.5, and one usable HIGH stimulus
(not three independent pairs) exists for Claude Opus 5. All five of Study 1's approved
pairs are confounded on the cross-model axis.** The Stimulus x Partner interaction
cannot be tested with the pairs we have.

Numbers from `code/cross_model_match.py` (no arguments, no API calls). Its own-copy
column reproduces `fresh_self_match.csv` exactly on **30/30** model x stimulus cells.
Estimators: own-copy = frozen `targeted_common.unbiased_match` (bias-corrected,
same-draw pairs removed); cross-model = `sum_k p_k^gpt * p_k^claude` (plug-in, already
unbiased -- two disjoint samples, no same-draw pair to remove; the (n-1) correction
would bias cross downward here).

## 1. Study 1's five approved pairs, audited (full sample)

Usable requires |d_own| >= 0.20 AND |d_cross| <= 0.10.

| pair | d_own | d_cross | verdict |
|---|---|---|---|
| gpt__c_contr_subtle__vs__b_spiral_cw | +0.345 | **+0.217** | CONFOUNDED |
| gpt__s_convexity__vs__d_dens_extreme | +0.475 | **+0.478** | CONFOUNDED |
| gpt__c_open_cplx__vs__s_density | +0.506 | **+0.133** | CONFOUNDED |
| claude__b_spiral_cw__vs__rot | +0.508 | **+0.283** | CONFOUNDED |
| claude__s_convexity__vs__d_dens_extreme | +0.463 | **+0.478** | CONFOUNDED |

**0 of 5 usable.** Every pair moves cross-model coordination in the same direction as
own-copy coordination, two by nearly the same amount (+0.478 vs +0.47). A null
interaction from these pairs would be uninterpretable.

## 2. Why: own and cross are collinear on this battery

corr(own_gpt, cross) = **+0.726**; corr(own_claude, cross) = **+0.682** over 15 stimuli.
Study 1 matched on generic salience and auditor prediction; both are roughly orthogonal
to this axis, so the collinearity survived the matching untouched.

Only two stimuli dissociate own from cross:

| stimulus | own_gpt | own_claude | cross | modal gpt / claude |
|---|---|---|---|---|
| a_chev_ud | 0.817 | 0.845 | **0.167** | `up` / `down` (opposite) |
| d_texture | 0.501 | 0.845 | **0.444** | `fine` / `coarse` |

`a_chev_ud` is the ideal HIGH type -- both models near-deterministic on OPPOSITE
identities -- but has no partner: no LOW-own stimulus sits near cross = 0.17.

## 3. Study 2 candidates (selected on SELECT half, reported on HOLDOUT)

105 within-model pairs per model. Two tiers, because Study 1's literal gate
(`meets_criteria`) never bounded raw salience:

- `eligible_study1_parity` = |d_own| >= 0.20, |d_cross| <= 0.10, |d_aud| <= 0.10
- `eligible` (strict) = the above AND |d_sal| <= 0.10

**GPT-5.5: 0 parity-eligible, 0 strict-eligible.** Best available is
`gpt__c_open_cplx__vs__s_density` (d_own +0.515, d_cross **+0.165**, fails), then
`gpt__rot__vs__mirror` (d_cross +0.004, clean, but d_own only +0.184 select and
**+0.011** holdout -- the separation is noise).

**Claude Opus 5: 4 parity-eligible, 0 strict-eligible, all 4 sharing one HIGH stimulus
(`d_texture`)** -- re-tests of one stimulus against four controls, not independent
replications.

| pair | d_own (sel) | d_cross (sel) | d_sal (sel) | holdout d_own | holdout d_cross |
|---|---|---|---|---|---|
| claude__d_texture__vs__s_density | +0.276 | -0.027 | -0.168 | +0.448 | -0.091 |
| claude__d_texture__vs__rot | +0.278 | -0.024 | +0.311 | +0.451 | -0.093 |
| claude__d_texture__vs__mirror | +0.269 | -0.020 | +0.378 | +0.414 | -0.075 |
| claude__d_texture__vs__d_dens_extreme | +0.241 | -0.033 | -0.199 | +0.393 | -0.093 |

All four survive the holdout (d_own grows, d_cross stays in tolerance); all four fail
generic salience. `claude__d_texture__vs__s_density` is the least-bad single cell.

## 4. What would be needed

Three independent clean pairs per model needs more stimuli of the `a_chev_ud` type
(high own-copy, chance-or-below cross). This battery has one.

The expanded 45-stimulus battery (these 15 plus the 30 in `stimuli/expansion/`, run in
`generation_ladder_20260814/models/`) is the obvious source, but **every Stage A run
there is an older generation** -- gpt-4o, gpt-5, opus-4.5/4.6/4.7/4.8 -- and none pairs
GPT-5.5 with Claude Opus 5, so no cross-model rate can be formed from it. Using it means
a fresh Stage A for this generation on the 30 new stimuli: 30 x 60 x 2 = 3600 calls plus
matching Stage B (auditor 1800 + salience 1800) ~= **7200 paid calls**. Not run here.

Interim option: run Study 2 as a **single-pair** design on
`claude__d_texture__vs__s_density`, Claude only, acknowledging (a) no GPT arm, (b) one
contrast rather than three, (c) an unmatched salience gap of 0.14. A demonstration,
not a test.

---
`pairs/cross_model_table.csv` -- 15 stimuli x {own_gpt, own_claude, cross} with bootstrap
CIs, select/holdout halves, salience, both auditor predictions.
`pairs/study2_candidate_pairs.csv` -- all 210 candidates, ranked, every row
`approved=False`. A human approves; the script never does.
