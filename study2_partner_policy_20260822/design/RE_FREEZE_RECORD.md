# Study 2 — RE-FREEZE RECORD

**Date:** 2026-08-22 · **Stage C had not started when this was written.**
**Scope:** the stimulus gradient (tiers, per-cell n) and the Stage C live-run gate.

---

## 1. What changed

The design was originally frozen on **provisional** compatibility advantages estimated
at n=60 in the Stage A battery. The confirmation screen (n=180 on the four load-bearing
stimuli, 120 on the floor controls, 60 on the ceiling controls, both actors; 2,160
trials, 0 API errors, 0 lost trials, exact AB/BA balance) re-estimated them. The design
has been **re-frozen on the confirmed values**:

- `FROZEN_PARAMS.CONFIRMED_GRADIENT` now holds the confirmed table.
- `FROZEN_PARAMS.ACTIVE_GRADIENT = CONFIRMED_GRADIENT` is what every downstream module
  reads: `code/design_table.py`, `code/study2_betting.py`, `code/test_study2.py`.
- `FROZEN_PARAMS.GRADIENT` (the provisional table) is **retained deliberately as the
  provisional record and is read by nothing**, per this project's standing practice of
  reporting both samples and averaging neither away.
- `design/frozen_design_table.csv` was re-emitted: `confirmed_advantage` is now filled
  for all 128 rows from `design/confirmed_compatibility.csv`, with a new
  `advantage_source` column set to `confirmed` on every row.
- Total Stage C calls: **2,976 → 2,832**.

## 2. Why this is legitimate, not a post-hoc adjustment

`STUDY2_SPEC_FROZEN.md` **§3** states the provisional values are *not final* until the
confirmation screen completes, and **§4** states a confirmed value simply *replaces* a
provisional one. Re-tiering here is that substitution.

The decisive point is temporal: **no Stage C ATTEMPT outcome exists yet.** There is no
dependent variable in hand, so there is nothing for the allocation to be adjusted
*toward*. The allocation rule itself (§3b, reproduced below) is unchanged — only the
advantages it is applied to have been replaced by better-measured ones. Which stimuli
enter the design was frozen before the confirmation screen and did not change.

## 3. The two tables, side by side

`prov` = provisional (n=60, Stage A, 2026-08-12) · `conf` = confirmed (n=180/120/60,
2026-08-22). `n/p` = N_PARTNER, `n/c` = per-payoff cell size.

### GPT-5.5 as actor

| stimulus | prov adv | prov tier | prov n/p | conf adv | conf tier | conf n/p | n/c |
|---|---|---|---|---|---|---|---|
| c_open_cplx | +0.367 | medium | 64 | **+0.489** | **large** | **32** | 8 |
| a_chev_ud | +0.650 | large | 32 | **+0.294** | large | 32 | 8 |
| rot | +0.073 | zero_floor | 120 | +0.070 | **small** | 120 | 30 |
| d_texture | +0.057 | small | 120 | +0.048 | small | 120 | 30 |
| mirror | +0.007 | zero_floor | 120 | −0.012 | zero_floor | 120 | 30 |
| b_spiral_cw | −0.128 | negative | 160 | −0.127 | negative | 160 | 40 |
| proto | 0.000 | zero_ceil | 64 | 0.000 | zero_ceil | 64 | 16 |
| s_arrow | 0.000 | zero_ceil | 64 | 0.000 | zero_ceil | 64 | 16 |

### Claude Opus 5 as actor

| stimulus | prov adv | prov tier | prov n/p | conf adv | conf tier | conf n/p | n/c |
|---|---|---|---|---|---|---|---|
| a_chev_ud | +0.678 | large | 32 | **+0.319** | large | 32 | 8 |
| b_spiral_cw | +0.217 | small | 120 | **+0.250** | **medium** | **64** | 16 |
| mirror | +0.022 | zero_floor | 120 | **+0.114** | **small** | 120 | 30 |
| c_open_cplx | −0.106 | **negative** | 160 | **−0.003** | **zero_floor** | **120** | 30 |
| d_texture | +0.401 | **medium** | 64 | **+0.003** | **zero_floor** | **120** | 30 |
| rot | −0.009 | zero_floor | 120 | −0.004 | zero_floor | 120 | 30 |
| proto | 0.000 | zero_ceil | 64 | 0.000 | zero_ceil | 64 | 16 |
| s_arrow | 0.000 | zero_ceil | 64 | 0.000 | zero_ceil | 64 | 16 |

### The two substantive changes

1. **GPT: large and medium swap.** `c_open_cplx` (+0.489) now exceeds `a_chev_ud`
   (+0.294), so `a_chev_ud` no longer dominates the GPT slope on its own.
2. **Claude loses its negative cell.** `c_open_cplx` moved −0.106 → −0.003 and
   `d_texture` +0.401 → +0.003, with the old and new CIs disjoint. The mechanism is
   visible in the confirmation counts: Claude **position-responds** on `c_open_cplx`
   (100% of trials) and `d_texture` (97%), which pins own-copy reliability at chance
   under AB/BA randomisation. **No negative Claude cell has been invented to replace
   them.** Claude runs as a positive-to-zero gradient; that is a real limitation on the
   Claude arm and is to be reported as one, not patched.

**Winner's curse, quantified.** `a_chev_ud` roughly halved on both actors
(+0.650 → +0.294 GPT; +0.678 → +0.319 Claude). The confirmed values are the honest
ones and still span a usable range (GPT −0.127 … +0.489; Claude −0.004 … +0.319).

## 4. The allocation rule (unchanged, now machine-readable)

Fixed before Stage C and never altered after seeing any ATTEMPT outcome. n rises as
|advantage| falls, because the small, zero and negative cells carry the entire
discrimination between the coarse-identity and policy-specific accounts.

| condition on the confirmed advantage | tier | N_PARTNER |
|---|---|---|
| own-copy pinned at 1.000 (no variance left) | `zero_ceil` | 64 |
| adv < −0.03 | `negative` | 160 |
| \|adv\| < 0.03 | `zero_floor` | 120 |
| 0.03 ≤ \|adv\| ≤ 0.15 | `small` | 120 |
| 0.15 < \|adv\| ≤ 0.25 | `medium` | 64 |
| \|adv\| > 0.25 | `large` | 32 |

The prose rule is now encoded once, in `FROZEN_PARAMS.allocation_for()`, which asserts
at import that it reproduces `ACTIVE_GRADIENT` exactly. It introduces no new number.

**Boundary convention, recorded rather than silently chosen.** The prose left the band
edges open. Exactly one cell sits on one — Claude / `b_spiral_cw` at exactly **+0.250**
— and the frozen table calls it `medium`, so the band tops are treated as **inclusive of
the lower band** (`≤ 0.25 → medium`). Ceiling status is read off the confirmation
counts (both own-copy rates at 1.000), never asserted by stimulus name.

## 5. The live-run gate: replaced, not bypassed

`code/study2_betting.py` previously refused a live run unless
`design/CONFIRMATION_RESULTS.md` contained a *passing verdict sentence*. That verdict
was a FAIL — written against the **superseded provisional table** (its two failing rows
are `claude/mirror` leaving the floor band and the consequent critical-order line).
Re-freezing on the confirmed values resolves what the verdict was flagging.

**No bypass flag was added.** The prose check was replaced by five machine-checked
requirements, all of which must hold, none of which any flag can skip:

1. `design/confirmed_compatibility.csv` exists and parses.
2. `design/CONFIRMATION_RESULTS.md` exists — the confirmation screen demonstrably ran.
   Its verdict line is still **read and printed for provenance**; it no longer decides.
3. Every planned (actor, stimulus) cell has a confirmed advantage.
4. The `confirmed_advantage` carried in the design table equals the confirmation
   screen's own value for that cell — a hand-edited table is refused.
5. **The tier and n recorded for every planned cell are exactly what
   `FROZEN_PARAMS.allocation_for()` assigns to that cell's confirmed advantage.**

(5) is the point of the exercise: "the design matches the confirmed data" becomes a
property the machine verifies on every invocation, over the cells actually about to
run, rather than a sentence a human wrote in a markdown file. A re-tiering that was
never propagated into the table, or a table edited away from the confirmed advantages,
now cannot reach a provider. `design_table.py` enforces the same property as validator
V6, so the table cannot even be emitted in an inconsistent state.

`--single-actor-gate` is retained for CLI compatibility and is now **inert**: none of
the five requirements is a per-actor prose verdict, so it has nothing to relax.

## 6. What is unchanged

Payoffs (match 10 / mismatch 0 / safe 3,5,7,9), neutral framing, the partner clause and
its single substitution point, the prompt hash lineage (Stage A sha8 `3003ae1b`), the
AB/BA randomisation and seed (20260822), which stimuli enter the design, the primary
analysis specification (`ATTEMPT ~ Partner × CompatibilityAdvantage + SAFE + …`, key
coefficient `partner_x_advantage`, errors-in-variables plus a bootstrap propagating
Stage A uncertainty), and the `a_chev_ud`-excluded sensitivity analysis.
