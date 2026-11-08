# Study 3A policy-knowledge pilot — PROPOSED (2026-10-16). Not frozen; no dispatch; $0 spent preparing it.

- **Objective:** real use of policy knowledge, with strong vs weak **in-game** policies. User correction, verbatim: "wait. we dont just want to test partner identity framing; we also want to test real use of policy knowledge".
- The identity-only proposals (v2, memo options B and C) stay separate and are **superseded as the sole target**.
- Game unchanged: PASS = 7; PLAY 10 only when both players PLAY the same object; otherwise 0.
- Focal model GPT-5.5. Actual partners: GPT-5.5 under COPY; Claude Opus 5 under the generic DIFFERENT description.

## 1. Three claims and what identifies each
| claim | observation / contrast | supports it | does not establish |
|---|---|---|---|
| (i) accurate knowledge of its own in-game policy | Spontaneous forecasts F_COPY (the partner is a copy, so this forecasts the model's own policy) scored by TVD/Brier against independent P_GPT_COPY draws | better than the uniform baseline; **item-specific** (better on its own item than when scored against other items' q); tracks strong vs diffuse; **better than the Opus auditor (AU_COPY)** | if self ≈ auditor, the knowledge is publicly inferable from the stimulus, not privileged |
| (ii) knowledge targets the actual partner | F_DIFF scored against q_Opus vs q_GPT (projection index = TVD(F_DIFF, q_Opus) − TVD(F_DIFF, q_GPT)); F_COPY against q_GPT | projection index < 0 on items where q_GPT and q_Opus diverge (TVD ≥ .3 between the policy samples, a rule fixed in advance) | partner knowledge on items where the two policies coincide |
| (iii) the knowledge is used to decide better | Δregret = regret(E1 forecast-then-act) − regret(E0 act-only), both against the **same independent** q; BR-consistency of E1 actions with their own forecasts; direction (more PASS on diffuse COPY and on Opus-incompatible DIFF; PLAY j* on strong COPY) | Δregret < 0 with the correct direction, together with (i) | that spontaneous (E0) play uses knowledge; mechanism; the elicitation confound (see DD3) |

Not sufficient on their own: partner-identity effects, correlation between forecast and action, and successful parsing.

**Knowledge source.** The core tests **access** (spontaneous self-forecasts validated against independent draws) and **elicited use**. Supplying an empirical summary of the partner's policy would test use of supplied evidence instead. That is not introspection and is not substituted here (DD2).

## 2. Policy definitions and the screening rule (fixed before new outcomes)
- **Descriptors of q (PASS included):**
  - participation π = 1 − q(PASS);
  - conditional object concentration c = s/π;
  - overall concentration h = max_a q(a);
  - s = max_j q(PLAY j).
- Low s is not automatically weak: a policy that always passes has h = 1.
- **Screening**, applied to the new P_GPT_COPY draws with a Jeffreys posterior:
  - strong-PLAY if P(s > .7) ≥ .9;
  - concentrated-PASS if P(q(PASS) > .7) ≥ .9;
  - diffuse ("weak") if P(h < .6) ≥ .9;
  - otherwise intermediate.
- **Every item is retained and reported in its observed class.** No replacement, no relabelling. If a candidate's archived class is not reproduced, report that. Historical labels are provenance only. F27 is preserved.

## 3. Candidate items (for user review; chosen from descriptive archived/independent in-game data)
| item | candidate | in-game evidence | partner data |
|---|---|---|---|
| F27_linecount_m1 | strong-PLAY | independent 0/0/0/0/24 (archived 54/54); historical LOW | Opus Oct policy reused (DD4) |
| F14_bars_m1 | strong-PLAY | archived 1/0/0/29/0 (n = 30) | none; new |
| F05_orient_m5 | diffuse | archived 9/2/3/3/2 (n = 19), P(h < .6) = .93 | none; new |
| F12_mirror_m3 | diffuse | archived 9/5/1/1/3 (n = 19), P(h < .6) = .93 | none; new |

- **Alternates:** strong F09_m5 or F41_m1; diffuse F11_m3, F12_m4, F05_m1.
- **Precision:** diffuse candidates have only 19 archived draws, and no candidate other than F27 has contemporary Opus data.
- **Reuse:** archived act-prompt draws are the same prompt but are provenance only; the core uses new contemporaneous policy draws. Forecast and forecast-then-act prompts are new, so nothing is reusable for them.

## 4. Arms (per item; positions shuffled; separate calls unless stated)
| arm | model | prompt (sha8) | n | role |
|---|---|---|---|---|
| P_GPT_COPY | GPT | ACT_COPY 49e35910 (archived) | 24 | own policy = COPY partner q |
| P_OPUS_DIFF | Opus | ACT_DIFFERENT 8222a371 (archived) | 24 (F27: 0, reused) | DIFFERENT partner q |
| F_COPY / F_DIFF | GPT | 35c06a75 / c28eef64 (new) | 12 / 12 | spontaneous forecasts |
| AU_COPY | Opus | 435f63ff (new) | 12 | external auditor |
| E0_COPY / E0_DIFF | GPT | archived act prompts | 12 / 12 | focal act-only |
| E1_COPY / E1_DIFF | GPT | 7a0aa6c6 / 1ff4d414 (new) | 12 / 12 | focal forecast-then-act |

Total **504 calls**. Exact texts are in `prompts_PROPOSED/PROMPTS_PROPOSED.md`. Each partner q comes from its actual model, settings and description, and is independent of the focal draws.

## 5. Estimands and reporting
- **Primary:** Δregret per item × condition. Same-q plug-in regret, which is ≥ 0 and biased upward; the bias largely cancels in Δ.
- **Forecast validation:** (i) and (ii) as above.
- **Companion measures:** V(p, q)/10, match rate (p × q), focal and partner PASS rates, descriptors with intervals.
- Independent realized shortfall (which can be negative) is **not** in the core, because there are no fresh-partner arms (DD5).
- Item-bootstrap intervals over 4 items are descriptive only.

**Negative or inconclusive outcomes:**
- (i) self-forecast is no better than uniform, not item-specific, or no better than the auditor;
- (ii) projection index ≥ 0 where policies diverge;
- (iii) Δregret ≥ 0, or E1 actions not BR-consistent with their own forecasts;
- screening fails to give at least one strong and one diffuse item → inconclusive for strong vs weak;
- unanimous cells and k = 4 → pilot-level only, never population certainty.

## 6. Budget
- Prior cumulative spend $4.7525 (recompute at launch); remaining $15.2475 under the binding $20 cap.
- **Expected about $6.73**, range $4.59–8.87 when the forecast-call estimates are varied ±50%.
- **Hard token-limit bound $60.44.** It requires GPT `max_output_tokens` = 4000 (DD6).
- **Proposed pilot cap $8**, reserving each call's bound before dispatch against min($8, $20 − recomputed cumulative). That leaves ≥ $7.25 for a follow-up. The run may stop incomplete; dispatching item by item would leave complete items (DD7).
- Prices are verified on launch day. No paid plumbing checks.

## 7. Design decisions (user + ChatGPT)
1. Adopt this core (spontaneous access + elicited use) as the pilot target?
2. Add a **supplied-evidence** arm (empirical partner summary vs a format-matched control) as a positive control for using evidence? It is not introspection.
3. The elicitation confound: add a **matched non-diagnostic elicitation control** (same format and length, irrelevant estimate) to E1? It costs about +12 GPT calls per condition per item.
4. Reuse F27's October Opus policy, or recollect it (+24 Opus)?
5. Add fresh-partner arms for an independent realized shortfall?
6. GPT `max_output_tokens` = 4000 (a settings change from the archived runs).
7. Dispatch order: interleaved, or item blocks?
8. Approve the candidate items and the screening rule.
9. Forecast-only framing: the archived game text addresses the model as a player, and the forecast prompts then say "you do not play". Acceptable?
