# Four-option stimuli: what has been tested, and what is durable

Compiled `2026-09-08` by sweeping every study folder under `Self_Coordination/`.
Companion data file: `durability_inventory_4opt.csv` (406 rows = 203 stimuli × 2 models).

---

## 1. Scope — there is exactly one 4-option battery

| battery | folder | options | sampled? |
|---|---|---|---|
| **F01–F41** | `study2_4opt_20260830/` | **4** | **yes** — 203 stimuli, 41 families, 9,744 Stage A calls + 4,800 Stage C |
| `proto4` / `noise4` | `source/stimuli/`, copied into `experiments/2026-08-01_confidence_calibration/code/stimuli/` | 4 | **no** — rendered (24 perms each) and never run |
| step1 / study1-HP / policy-specific / study2-partner-policy | `study1_hp_replication_20260905/`, `policy_specific_.../`, `study2_partner_policy_20260822/` | **2** (`identity_1`/`identity_2`, `path_AB`/`path_BA`) | yes, but binary |
| Monitored Schelling | `monitored_schelling_20260905/` | 12 | yes |
| Open-Set Rendezvous | `open_set_rendezvous_20260906/` | open set | yes |

`proto4`/`noise4` appear only in `make_4opt_stimuli.py` and in READMEs — no runner, no
results file. Stage 3 confidence calibration ran the **two**-option `proto`/`mirror`/`noise`/
`rot`/`inkblot`/`nd2` pairs instead, and on `gpt-5.4` / `claude-opus-4-8`.

**So: every 4-option policy we hold is from `study2_4opt_20260830`, on `gpt-5.5-2026-04-23`
and `claude-opus-5`.** Nothing else in the tree re-tests it — grep for any family name
returns files inside that folder only.

---

## 2. The two measurements

| | Stage A (discovery) | Stage C (pilot) |
|---|---|---|
| frame | plain choice | coordination decision + choice on the same call |
| n per stimulus per model | 24 | 39–123 |
| coverage | all 203 | the 29 selected (15 pairs, minus one cell with <2 usable choices) |

Stage C is a genuine independent re-measurement at larger n **and in a different frame**,
so agreement across the two is a stronger durability claim than a simple retest.

---

## 3. Durability tiers

`self_match` = probability two independent draws pick the same item; chance = .25.

| tier | definition | GPT | Claude |
|---|---|---|---|
| **A — durable** | ≥ .75 in *both* stages, modal item stable | **6** (6 fam) | **7** (7 fam) |
| A− — decayed | ≥ .75 at Stage A, < .75 at Stage C | 2 | 0 |
| B — strong, unreplicated | ≥ .75 at Stage A only (n = 24) | 100 (27 fam) | 129 (34 fam) |
| C — intermediate | .45–.75 | 69 | 41 |
| D — low | ≤ .45 (14 confirmed low at both stages) | 26 | 26 |

### Tier A in full — the 13 stimuli with durable, model-specific policies

All 13 are also **model-specific** (own − cross ≥ .15).

| model | stimulus | Stage A | Stage C | n_C | item | cross | own − cross |
|---|---|---|---|---|---|---|---|
| claude | `F03_symmetry_m6` | 1.000 | 1.000 | 97 | 0 | .458 | +0.542 |
| claude | `F10_curvature_m2` | 1.000 | 1.000 | 122 | 0 | .250 | +0.750 |
| claude | `F11_noise_m0` | 1.000 | 1.000 | 45 | 1 | .292 | +0.708 |
| claude | `F12_mirror_m3` | 0.917 | 1.000 | 82 | 1 | .205 | +0.712 |
| claude | `F20_corner_m0` | 1.000 | 1.000 | 107 | 0 | .250 | +0.750 |
| claude | `F27_linecount_m1` | 1.000 | 0.977 | 85 | 0 | .292 | +0.708 |
| claude | `F28_dotarrange_m0` | 1.000 | 1.000 | 91 | 1 | .375 | +0.625 |
| gpt | `F01_oddone_m6` | 1.000 | 0.768 | 88 | 3 | .792 | +0.208 |
| gpt | `F07_contrast_m7` | 1.000 | 0.983 | 114 | 0 | .792 | +0.208 |
| gpt | `F09_convexity_m5` | 1.000 | 0.984 | 122 | 1 | .667 | +0.333 |
| gpt | `F10_curvature_m5` | 1.000 | 1.000 | 123 | 3 | .125 | +0.875 |
| gpt | `F12_mirror_m7` | 0.917 | 0.930 | 85 | 3 | .085 | +0.832 |
| gpt | `F41_contain_m1` | 1.000 | 0.981 | 107 | 2 | .792 | +0.208 |

**"Model-specific" here means `own − cross ≥ .15` — a cross-*match rate*, not a statement
about the other model's modal item or whether it holds a convention at all.** §3a unpacks
that; it does not mean these are divergent items.

`F10_curvature` and `F12_mirror` carry a durable policy for **both** models — on
*different members* (`m2`/`m5`, `m3`/`m7`). No single stimulus is Tier A for both models.

---

## 3a. What the *other* model does on each Tier-A stimulus

Tier A certifies **one side only**. The focal model's partner has to be characterized
separately, and on this battery it usually has not been.

| | stimulus | focal | focal item | other | other item | other Stage A | other Stage C |
|---|---|---|---|---|---|---|---|
| **shared modal — not divergent** | `F01_oddone_m6` | gpt | 3 | claude | **3** | 0.627 | — |
| | `F07_contrast_m7` | gpt | 0 | claude | **0** | 0.656 | — |
| | `F09_convexity_m5` | gpt | 1 | claude | **1** | 0.536 | — |
| | `F41_contain_m1` | gpt | 2 | claude | **2** | 0.634 | — |
| **diff modal, other at chance (replicated)** | `F11_noise_m0` | claude | 1 | gpt | 2 | 0.297 | 0.321 |
| | `F12_mirror_m3` | claude | 1 | gpt | 0 | 0.254 | 0.294 |
| | `F27_linecount_m1` | claude | 0 | gpt | 1 | 0.293 | 0.353 |
| **diff modal, other weak/intermediate, unreplicated** | `F03_symmetry_m6` | claude | 0 | gpt | 1 | 0.482 | — |
| | `F10_curvature_m2` | claude | 0 | gpt | 3 | 0.609 | — |
| | `F12_mirror_m7` | gpt | 3 | claude | 2 | 0.330 | — |
| | `F20_corner_m0` | claude | 0 | gpt | 3 | 0.609 | — |
| | `F28_dotarrange_m0` | claude | 1 | gpt | 0 | 0.460 | — |
| **diff modal, other strong but unreplicated** | `F10_curvature_m5` | gpt | 3 | claude | 0 | **0.772** | — |

Against the three requirements for a divergent relational item — (1) focal durable,
(2) other's modal differs, (3) other's choice also stable — the count is:

- (1) only: **13**
- (1) + (2): **9**
- (1) + (2) + (3): **0**

The single closest is `F10_curvature_m5`, where Claude sits at 0.772 — inside the
.75–.90 band that failed to replicate in §4. On 3 stimuli the other model is at chance
*and that is confirmed by a second measurement*, so those are cleanly "focal has a
convention, partner has none" — a different and possibly useful contrast, but not a
competing convention.

Item indices are comparable across models: shared-modal stimuli average cross-match .816,
divergent-modal ones .319.

### Tier A− — the two that decayed

| model | stimulus | Stage A | Stage C | n_C | modal |
|---|---|---|---|---|---|
| gpt | `F06_density_m0` | 0.772 | 0.648 | 120 | stable |
| gpt | `F31_overlap_m1` | 0.772 | 0.560 | 83 | stable |

---

## 4. The rule that falls out of this — and it is sharp

Stage A at n = 24 predicts durability **only above ~.90**:

| Stage A band | n | held ≥ .75 at Stage C | modal stable | mean abs. shift |
|---|---|---|---|---|
| **≥ .90** | 13 | **13 / 13** | 13 / 13 | **0.031** |
| .75–.90 | 2 | **0 / 2** | 2 / 2 | 0.168 |
| < .45 | 14 | 0 / 14 | 11 / 14 | 0.060 |

Both Tier-A− failures sit at Stage A = 0.772, i.e. inside the .75–.80 band. Everything
measured at ≥ .917 held, and held tightly. The `≥ .75` HIGH threshold used for pair
selection in Study 2 is therefore **too permissive to certify durability**; ≥ .90 is the
threshold the data support.

Caveat: only 2 stimuli fell in the .75–.90 band, so "0/2" is weak evidence on its own —
it is the *contrast* with 13/13 at ≥ .90, plus the size of the shift (0.168 vs 0.031),
that carries the claim.

Low stimuli are stable as *low* (0/14 rose to strong) but their modal item is not
meaningful — 3 of 14 changed modal item between stages, exactly as noise should.

---

## 4a. Divergent items are structurally scarce in this battery

Because a focal × stimulus pairing is the real unit, the question "which stimuli support a
divergent relational item" has to be asked of the **joint** distribution, not of either
model's list. Stage A modal item, all 203 stimuli, cell = n (n with *different* modal item):

| GPT ↓ / Claude → | ≥ .90 | .75–.90 | .45–.75 | < .45 |
|---|---|---|---|---|
| **≥ .90** | **63 (0)** | 8 (2) | 11 (0) | 2 (1) |
| **.75–.90** | 20 (0) | 1 (0) | 2 (1) | 1 (0) |
| **.45–.75** | 28 (8) | 5 (1) | 24 (15) | 10 (5) |
| **< .45** | 11 (5) | 0 (0) | 3 (0) | 14 (10) |

**When both models hold a strong convention (≥ .75), they pick the same item 90 of 92 times
— 97.8%.** In the 63 stimuli where both are ≥ .90, divergence is **zero**.

The complete set of both-strong divergent candidates in the battery is two stimuli, in one
family, and Claude is at 0.772 in both:

| stimulus | GPT | Claude | cross |
|---|---|---|---|
| `F10_curvature_m3` | 0.917 item 3 | 0.772 item 0 | .156 |
| `F10_curvature_m5` | 1.000 item 3 | 0.772 item 0 | .125 |

Divergence lives almost entirely in cells where at least one model is weak — which is
exactly where you cannot claim a competing convention. This is a fact about the two
models' policies on this visual battery, not a defect in how it was built.

**Implication for a new study:** if the design needs items where two models hold *different*
durable conventions, this battery does not supply them, and a third stimulus batch of the
same kind is unlikely to. Either the design targets "focal has a convention, partner does
not" (3 clean replicated cases), or new stimuli have to be built specifically to induce
divergence rather than screened for it.

---

## 5. Available pool for a new study

**Certified durable on the focal side: 13 focal × stimulus pairings (6 GPT, 7 Claude),
12 distinct families.** The unit is the pairing, not the stimulus — and no stimulus is
currently certified on both sides, so none contributes two pairings (see §3a, §4a).

**Unreplicated but strong (Tier B): 229 stimuli.** Of these the scarce and interesting
subset is the model-specific ones:

- **GPT: 16 model-specific strong across 8 families** — `F01_oddone`, `F06_density`,
  `F07_contrast`, `F09_convexity` (6 stimuli, all at own = 1.00), `F10_curvature`,
  `F12_mirror`, `F31_overlap`, `F41_contain`. Eight are already Tier A or A−; the
  remaining 8 are unreplicated.
- **Claude: 43 model-specific strong across 22 families.** Seven are Tier A. The
  unreplicated remainder includes several families GPT has nothing in — `F16_aspect`
  (5 stimuli, .92–1.00), `F33_hole` (3), `F13_count`, `F15_ring`, `F18_stroke`,
  `F25_nested`, `F02_size`, `F21_notch`, `F22_star`, `F26_bumploc`, `F34_jitter`,
  `F39_spacing`, `F40_crossang`.

The asymmetry is a fact about the policies, not the battery: GPT reached ≥ .75 on 108 of
203 stimuli but was model-specific on only 16, because it shares most of its strong
conventions with Claude (90 stimuli are strong for both *and* cross-match ≥ .75).

If a new study needs GPT-specific durable items, that is the binding constraint —
8 unreplicated candidates in 7 families, and `F09_convexity` supplies 6 of the 16.

---

## 6. Caveats

1. **Model versions are pinned to this battery.** All of it is `gpt-5.5-2026-04-23` and
   `claude-opus-5`. Nothing here transfers to `gpt-5.4` / `claude-opus-4-8`, which is what
   the Stage 3 calibration work used.
2. **Tier A is confounded with selection.** The 29 replicated stimuli were chosen for
   Stage C *because* they were extreme (HIGH ≥ .75 or LOW ≤ .45), so the intermediate band
   has no replication data at all. The ≥ .90 rule is estimated only at the extremes.
3. **Stage C n varies 39–123** because it accumulated over pair × level × partner × safe
   cells; it is not a balanced re-measurement.
4. **Cross-match is Stage A only.** No cross-model match was re-estimated at Stage C, so
   "model-specific" rests on the n = 24 pass throughout.
5. Stage B (auditor / generic-salience) was never run, so none of these stimuli are matched
   on how obvious the focal choice looks — still the largest open gap from SUMMARY.md §6.1.
