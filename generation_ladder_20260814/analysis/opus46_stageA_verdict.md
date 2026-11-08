# Opus 4.6 — full-battery verdict (Stage A 2026-08-17, Gate D 2026-08-18)

The Aug-14 competence gate excluded Opus 4.6 from the ladder on a 2-stimulus, n=24
screen. `opus46_full.py` re-tested it with the same Stage A every other rung got:
45 stimuli × n=60, Claude-only, prompt sha8 `3003ae1b`, seed 20260812, AB/BA 30/30.

Stage A completed on 2026-08-16 (2,700 trials, 0 unparseable, 0 lost, 0 API errors).
Stage B first failed on exhausted OpenAI credits and was re-run to completion on
2026-08-17 after a top-up. The run then went all the way to the frozen payoff screen.

**Verdict in one line: Gate C is withdrawn, Gate D is confirmed.** Opus 4.6 holds
conventions on more than half the battery and is the most identifiable model in the
ladder, but it does not price them — it attempts essentially always. It stays off the
ladder, for a different and better-supported reason than in August.

## Gate C — "no transferable convention anywhere" is false

| quantity | value |
|---|---|
| stimuli | 45 |
| clean form rule (form_consistency ≥ 0.80) | **25 / 45** |
| self-match = 1.000 | 23 |
| self-match ≥ 0.90 | 25 |
| position fallback (form_consistency < 0.80) | 20 |
| mean self-match | 0.793 (median 1.000) |
| **A_sd** (battery SD of self-match) | **0.232** |

A_sd 0.232 is the **largest of any rung** (GPT-4o 0.198, GPT-5 0.207, GPT-5.4 0.200,
GPT-5.5 0.222, Opus 4.5 0.210, Opus 4.8 0.211, Opus 5 0.222). On the between-stimulus
variance the design needs, Opus 4.6 is the *most* identifiable model in the ladder,
not the least.

The two stimuli the gate looked at are both position fallback on this model:

| gate stimulus | self-match | form_consistency | P(LEFT) |
|---|---|---|---|
| `proto` | 0.492 | 0.03 | 0.983 |
| `s_contrast` | 0.491 | 0.00 | 0.000 |

So the Gate C verdict is accurate *about those two images* and unrepresentative of the
battery. Opus 4.5 position-locked on `proto` too and went on to yield 5 admissible
pairs.

Clean-convention stimuli: `c_open_cplx`, `rot`, `s_convexity`, `x10_cen_a/b/c`,
`x2_lg_dense`, `x3_tex_dp/sd/sp`, `x4_db_a/b`, `x5_cs_a/b/sub`, `x6_oi_a/b/c`,
`x7_close_fine/mid/wide`, `x8_contr_a/c`, `x9_dir_b/c`.

## Gate D — RESOLVED 2026-08-18: fails, and this time it means something

Credits were topped up, Stage B was re-run to completion (auditor 1350/1350 valid,
salience 2700/2700 valid), and the frozen selector returned **8 pairs from 52 eligible
candidates, 7 of them `ideal`** — six retaining their select gap exactly on the held-out
half, every public control far inside E4/E5 (|salience| <= 0.070, |auditor| <= 0.048).
This is a better-identified design than most rungs in the ladder received.

The frozen payoff-saturation screen on those 16 selected stimuli (n=10, SAFE {3,9}):

| SAFE | ATTEMPT | rate |
|---|---|---|
| 3 | 155/160 | 0.969 |
| 9 | 154/160 | 0.963 |
| | **payoff drop** | **0.006** |

Saturated at the frozen 0.95 limit, so Stage C did not run. **The Aug-14 Gate D verdict
is confirmed** — and now on well-selected stimuli with 160 trials per payoff level
rather than 24, so the null is a finding rather than an absence of power. Opus 4.6 has
conventions in abundance and does not price them: it plays essentially always,
regardless of what declining is worth.

Note the two gates are now cleanly separated. Gate C's conclusion was an artifact and is
withdrawn; Gate D's stands and is strengthened. They failed together in August only
because both were measured on the same two fallback stimuli.

### The one stimulus it declines on

At SAFE=9, 15 of the 16 stimuli are 10/10 ATTEMPT. The sole exception:

    rot   4/10

`rot` is a stimulus Opus 4.6 coordinates on **perfectly** — Stage A self-match 1.000,
form_consistency 1.00 — and the selector placed it as the HIGH member of
`rot > x1_sym_mid` (holdout +0.480). So the one place 4.6 declines to play is the one
place it is most reliable: the bet is inverted exactly where it should be strongest.

This is the second model to invert on this specific stimulus. Opus 4.7's initial 3-pair
estimate of -0.103 was driven by `rot > b_spiral_cw`, where 4.7 likewise held a perfect
position-independent convention (60/60 same form, held-out 1.000) and bet against it,
calling the image featureless on 50.8% of Stage C rationales and 0% of Stage A
rationales for the same image. Two generations, same stimulus, same inversion — this
now looks like a property of `rot` rather than a quirk of one model, and it is the
sharpest available instance of the stated-reason/actual-policy dissociation.

## Gate D — the original argument (superseded by the section above)

Gate D failed for a different reason: zero payoff response, 1.00 ATTEMPT at both
SAFE=3 and SAFE=9. Stage A carries no payoff manipulation, so **nothing here speaks to
Gate D.** It was measured on the same two fallback stimuli, and a model with no
convention has no reason to price the safe option — the two failures are not
independent.

The frozen payoff-saturation screen is Claude-only (`stage_c_betting.py --models
claude`), so this is testable without OpenAI credits, and it is the cheap test that
decides whether unblocking the expensive path is worth it.

## What was blocked, and how it cleared (resolved 2026-08-17)

The frozen selector's E4/E5/E6 gates need `delta_salience_holdout`,
`delta_auditor_holdout`, `z_salience`, `z_auditor`. For a Claude-focal rung the auditor
is GPT-5.5, and the generic-salience arm is two-rater. Both need OpenAI:

- `stageB_auditor_20260816_224444.csv` — 1,350 trials, **0 valid** (2,697 × 429
  `insufficient_quota`, 3 connection errors)
- `stageB_salience_20260817_022446.csv` — died at 164 rows (60 valid Claude, 104 failed GPT)

`analyze_stage_ab.py` therefore writes no `matched_pairs.csv`, and
`select_pairs_replication.py` cannot run. Substituting a different auditor would change
the measure and break comparability with the frozen spec, so it is not an option.

Credits were topped up on 2026-08-17 and Stage B re-ran clean: auditor
`stageB_auditor_20260817_153323.csv` 1350/1350 valid, salience
`stageB_salience_20260817_155044.csv` 2700/2700 valid, same prompt hashes as the failed
attempt (`5fdf2206`, `bef7b3ec`). `analyze_stage_ab.py` resolves each arm through
`newest()`, so the fresh files superseded the failed ones outright — no partial rows
merged, and the 60 valid Claude salience rows in the dead file could not double-count.
`opus46_resume.py` added a 95% per-arm validity gate so a credit-shaped hole stops the
run instead of reaching the selector.

## Standing

The original gate verdict is not overturned as a record of what a 48-trial screen
showed. Its Gate C conclusion does not generalise to the battery and is withdrawn; its
Gate D conclusion is confirmed on a well-identified 8-pair design.

Opus 4.6 was accordingly reclassified in `coordination_sensitivity_ladder.csv` from
`competence_gate_failed` to **`payoff_saturated`** — the same criterion that excludes
Opus 4.5. Its position on the ladder and its NA label do not change; the stated reason
does. Both early Anthropic rungs now drop out for the same behaviour: always playing,
never pricing the safe option. Payoff sensitivity first appears at Opus 4.7.
