# Figure — Open-set online rendezvous (composite, `osr_main.pdf`)

**Monitoring buys evasion by destroying coordination, not by relocating it.**
Agent A, Agent B and the Monitor are all the same checkpoint
(`gpt-5.5-2026-04-23`, `reasoning_effort=low`). The action space is open: agents
name any public online location, with nothing enumerated for them. 18 contexts ×
6 families × 60 samples per condition (1,080 agent calls per arm).

**(A)** Baseline convergence is strong and context-specific. Each point is one
context: within-context pairwise match against the match rate for draws taken
from *different* contexts. All 18 lie far above the identity line (mean 0.839 vs
0.073), so the copies are not reusing one global answer. This is pre-registered
criterion (f), which passes by 7.7× its +0.10 threshold.

**(B)** The pre-registered diversity criterion (d) required ≥ 30 distinct
locations. It **fails at canonical host** (15, open bar) and passes at the two
finer levels (48 exact URLs, 38 canonical pages) — the action space is open, but
the model varies so little at host level that few hosts appear. Amendment 01
moved (d) to canonical page with the threshold unchanged; the frozen analyzer was
not edited, and both verdicts are reported throughout.

**(C)** Change in joint payoff (two independent draws coincide on a location the
monitor did **not** name) under monitoring, by monitor list depth and
canonicalization level. Points are means over the 18 contexts; bars are 95%
bootstrap CIs (20,000 resamples over contexts). The effect exists only at k ≥ 5
and only after canonicalization: null at k = 1 at every level, and null at every
depth at the exact-URL level.

**(D–F)** The decomposition at k = 5, canonical host, paired by context (filled
circle = baseline, open square = monitored; heavy line = the mean). Coordination
collapses (0.839 → 0.374), evasion rises (0.012 → 0.463), and their conjunction —
the only quantity that pays — rises to 0.096 from a near-zero base of 0.002.
Annotations give the mean difference with its 95% bootstrap CI and the
per-context sign count. This is pre-specified outcome **F** (evasion at full
cost) with a small real **E** component; it is not outcome E, because the
monitored monitor still top-1-predicts the monitored mode in 10/18 contexts.

**Limitation, not patched.** 7 monitored rows in C13 are the identical string
`Wikipedia:Village pump (policy)` — a genuinely coordinated answer in wiki-title
form that the frozen parser scores `not_a_location`. Alias tables stay frozen by
design; this biases *against* detecting evasion in C13.

Source: `code/osr_plots.py`. Every plotted value is recomputed from the frozen
raw data through the frozen helpers in `osr_analyze.py` / `osr_strategic.py`;
no new statistic is defined in the plotting code.
