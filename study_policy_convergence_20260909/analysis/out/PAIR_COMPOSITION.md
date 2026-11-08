# Which models make up within-family and cross-family

Nine checkpoints, two lineages, 36 unordered pairs. Identical panel for both arms; only the
item battery differs (41 visual items / 12 code items), so the pair structure below applies
to both figures.

## The nine checkpoints

| checkpoint | family | vintage (yr since 2025-01) | stratum |
|---|---|---|---|
| gpt-4-turbo-2024-04-09 | gpt | −0.750 | G-SAMPLE |
| gpt-4.1-2025-04-14 | gpt | +0.250 | G-SAMPLE |
| gpt-5-2025-08-07 | gpt | +0.583 | G-REASON |
| gpt-5.5-2026-04-23 | gpt | +1.250 | G-REASON |
| claude-opus-4-5-20251101 | claude | +0.833 | C-OFF |
| claude-opus-4-6 | claude | +1.083 | C-OFF |
| claude-opus-4-7 | claude | +1.250 | C-OFF |
| claude-opus-4-8 | claude | +1.333 | C-OFF |
| claude-opus-5 | claude | +1.500 | C-OFF |

A pair's plotted vintage is the **mean** of its two checkpoints' vintages.

## Within-family — 16 pairs, and it is two lineages pooled

**within-GPT, 6 pairs** — C(4,2). Pair vintage −0.250 … +0.917 (span 1.167 yr).

    4-turbo x 4.1 · 4-turbo x 5 · 4-turbo x 5.5 · 4.1 x 5 · 4.1 x 5.5 · 5 x 5.5

**within-Claude, 10 pairs** — C(5,2). Pair vintage +0.958 … +1.417 (span 0.458 yr).

    4-5 x 4-6 · 4-5 x 4-7 · 4-5 x 4-8 · 4-5 x opus-5 · 4-6 x 4-7 · 4-6 x 4-8
    4-6 x opus-5 · 4-7 x 4-8 · 4-7 x opus-5 · 4-8 x opus-5

## Cross-family — 20 pairs

Every GPT x every Claude (4 x 5). Pair vintage +0.042 … +1.375.

---

## Three things this composition does to panel C

**1. The two within-family lineages barely overlap in vintage.** Every within-GPT pair sits
at ≤ +0.917 and every within-Claude pair at ≥ +0.958. The pooled within-family line is
therefore fitted across a gap whose low end is entirely GPT-GPT and whose high end is
entirely Claude-Claude.

**2. The 6 GPT pairs carry 69.2% of the regression leverage**, because leverage goes with
spread in vintage and GPT's checkpoints span 24 months against Claude's 8. The 10 Claude
pairs — the numerical majority — carry 30.8%.

**3. Split by lineage, the within-family result is a GPT result.**

| arm | group | pairs | mean das | slope/yr | 95% item-clustered CI |
|---|---|---|---|---|---|
| visual | within-family (pooled) | 16 | +0.864 | **+0.0875** | [+0.032, +0.147] |
| visual | within-GPT | 6 | +0.821 | **+0.1173** | [+0.049, +0.189] |
| visual | within-Claude | 10 | +0.890 | +0.0285 | [−0.098, +0.152] |
| visual | cross-family | 20 | +0.834 | +0.0365 | [−0.027, +0.101] |
| code | within-family (pooled) | 16 | +0.970 | +0.0222 | [−0.041, +0.103] |
| code | within-GPT | 6 | +0.960 | +0.0454 | [−0.009, +0.142] |
| code | within-Claude | 10 | +0.976 | **−0.0399** | [−0.108, −0.004] |
| code | cross-family | 20 | +0.934 | +0.0390 | [−0.027, +0.132] |

On the visual battery the only interval excluding zero within the family split is
**within-GPT**. Claude-Claude, which supplies 10 of the 16 pairs, shows nothing. On the code
battery within-Claude is *negative* and excludes zero — the opposite direction.

**A confound rides along with the GPT lineage.** GPT crosses a control-surface boundary
mid-ladder (G-SAMPLE for 4-turbo and 4.1, G-REASON for 5 and 5.5); Claude is C-OFF
throughout. So the within-GPT slope confounds checkpoint vintage with the sampling →
reasoning surface change. This is the study's own Threat 13, and it lands on precisely the
subgroup that carries the result.

**Reading.** "Within-family similarity rises, cross-family does not" is, on this panel,
better stated as "similarity rises among four GPT checkpoints that also change request
surface; it does not rise among five Claude checkpoints spanning eight months, and it does
not rise across families."
