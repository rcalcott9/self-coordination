# Study 3A read-only design diagnostic — 2026-10-16

- **Authorisation:** "okay. send CC to do the read-only diagnostic" (user, relayed by the ChatGPT research manager; message `study3a-readonly-design-diagnostic-01`).
- **Scope:** local analysis of existing action records only. No calls, $0 experiment spend. No item was selected, dropped or relabelled, and no design is adopted.
- **Files:**
  - `diagnostic_items.csv`: one row per item, with every source, n, distribution, s and payoffs.
  - `diagnostic.py`: the code.
  - `validation.json`.

## Sources: held-out vs exploratory
| source | what it is | items |
|---|---|---|
| COPY_POLICY | independent GPT COPY partner-policy sample (10-15 pilot) | 4 |
| COPY_ARCHIVED | archived GPT COPY game draws. Plan v2 designates these as **focal evaluation draws**, so using them as q is **exploratory reuse** | 19 |
| DIFF_POLICY / DIFF_FRESH | independent Opus DIFFERENT partner samples (10-15 pilot) | 4 |
| DIFF_OPUS_SEP | archived Opus DIFFERENT game draws (September). These are actual partner behaviour, but Sep/Oct pooling is not established | 3 |
| GPT_DIFF_FOCAL | GPT focal actions under DIFFERENT framing. **Not** an Opus partner sample; context only | 19 |

- **Fixed for all items:** focal GPT-5.5 (`gpt-5.5-2026-04-23`, effort low); prompts `49e35910` / `8222a371`.
- **Excluded by construction:** Stage 0/Stage A, high effort, GREEN, SHAPES and M07.
- q includes participation: PASS + Σ PLAY(j) = 1.

## Per item
- s = max_j q_COPY(PLAY j), with a Jeffreys 95% interval and P(s > .7).
- **s source:** POL = independent policy sample; arch = exploratory archived draws.
- **COPY payoff:** 10·q_COPY(PLAY j*), against PASS = 7.
- **DIFF payoff:** 10·q_DIFF(PLAY j*), shown only where Opus was actually measured.

| item | s [95%] | P(s>.7) | src (n) | GPT COPY PASS | j* | COPY payoff | DIFF payoff | Opus PASS |
|---|---|---|---|---|---|---|---|---|
| F01_oddone_m0 | 1.00 [.80, .99] | 1.00 | POL 24 | .00 | 3 | 10.00 | 10.00 (Oct pol); 10.00 (Sep) | .00 / .00 |
| F02_size_m2 | 1.00 [.80, .99] | 1.00 | POL 24 | .00 | 3 | 10.00 | 8.75 (Oct pol) | .125 |
| F27_linecount_m1 | 1.00 [.80, .99] | 1.00 | POL 24 | .00 | 3 | 10.00 | **1.67** (Oct pol) | .75 |
| F41_contain_m2 | .63 [.40, .76] | .11 | POL 24 | .04 | 2 | 6.25 | **0.00** (Oct pol) | 1.00 |
| F09_convexity_m5 | 1.00 [.77, .99] | 1.00 | arch 20 | .00 | 1 | 10.00 | missing | – |
| F41_contain_m1 | 1.00 [.77, .99] | .99 | arch 20 | .00 | 2 | 10.00 | missing | – |
| F14_bars_m1 | .97 [.79, .98] | 1.00 | arch 30 | .03 | 2 | 9.67 | missing | – |
| F10_curvature_m5 | .95 [.70, .97] | .98 | arch 20 | .00 | 3 | 9.50 | missing | – |
| F03_symmetry_m1 | .93 [.75, .96] | .99 | arch 30 | .00 | 0 | 9.33 | missing | – |
| F36_split_m0 | .90 [.71, .95] | .98 | arch 30 | .00 | 3 | 9.00 | **1.50** (Sep, n = 20) | .85 (Sep) |
| F07_contrast_m7 | .79 [.52, .89] | .61 | arch 19 | .00 | 0 | 7.89 | missing | – |
| F18_stroke_m1 | .70 [.50, .81] | .34 | arch 30 | .00 | 3 | 7.00 | missing | – |
| F15_ring_m0 | .67 [.49, .79] | .21 | arch 30 | .00 | 3 | 6.67 | missing | – |
| F05_orient_m1 | .42 [.23, .61] | .00 | arch 19 | .37 | 1 | 4.21 | 0.00 (Sep, n = 20) | 1.00 (Sep) |
| F11_noise_m3 | .37 [.21, .56] | .00 | arch 19 | .42 | 2 | 3.68 | missing | – |
| F12_mirror_m4 | .37 [.19, .56] | .00 | arch 19 | .42 | 1 | 3.68 | missing | – |
| F12_mirror_m3 | .26 [.15, .46] | .00 | arch 19 | .47 | 0 | 2.63 | missing | – |
| F11_noise_m0 | .22 [.14, .34] | .00 | arch 49 | .63 | 1 | 2.24 | missing | – |
| F05_orient_m5 | .16 [.13, .38] | .00 | arch 19 | .47 | **1 or 2 (tie)** | 1.58 each | missing (tie unresolved) | – |

- No item has zero COPY PLAY, so the no-PLAY case did not occur.
- For the 4 POL items the archived estimate of s is reported alongside in the CSV.
- Items with n = 19 lost one job to the gpt_staghunt_pilot budget stop. Those jobs were never collected; they are not invalid responses.

## Synthesis
1. **Spread in s is wide**: .16 to 1.00.
   - 9 items have P(s > .7) ≥ .95.
   - 4 sit near the threshold: F07 .61, F18 .34, F15 .21, F41_m2 .11.
   - 6 are clearly below, with P ≈ 0.
   - **Only 4 of the 19 s values come from independent policy samples.** Three of those are unanimous (24/24), which does not establish s = 1 in the population. The other 15 are exploratory reuse of evaluation draws.
2. **PASS vs PLAY concentration.**
   - Where s is high, GPT almost never passes in COPY (PASS ≤ .04).
   - All 6 low-s items combine heavy passing (.37–.63) with objects split among the plays.
   - So low s reflects both abstention and object dispersion. It is not one mechanism.
3. **Partner incompatibility is measured on only 6 items.** Three have September Opus draws (F01, F05_orient_m1, F36_split_m0), but only 2 rely exclusively on them (F05_orient_m1, F36_split_m0). F01 also has independent October data (24 policy + 12 fresh).
   - *Correction 2026-10-16 (ChatGPT review, message `study3a-diagnostic-review-correction-01`, verified against `diagnostic_items.csv`). This line previously said "on 3 of them only with September Opus draws". No result changed.*
   - Where it is measured, incompatibility comes from **Opus passing** (.75–1.00), not from Opus playing a different object.
   - Strong COPY plus incompatible partner: F27 (independent samples on both sides) and F36 (archived on both sides, exploratory).
   - Strong COPY plus compatible partner: F01 and F02.
   - The 9 high-s items have no Opus measurement except F01, F02, F27 and F36.
4. **What the evidence supports.**
   - Independent samples: the 4 pilot items only.
   - Everything else is descriptive and archived. The GPT pooling checks were non-significant, which is not proof of equivalence.
5. **For the design decision** (not made here):
   - The data show enough apparent variation in s to compare coordination opportunity across items, provided independent policy draws confirm it.
   - A narrower strong-COPY / partner-incompatibility design currently rests on 2 items, and its incompatibility is participation-based.
   - Either direction first needs Opus DIFFERENT measurements on the high-s items.
