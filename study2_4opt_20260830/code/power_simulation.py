"""
Power for beta3 (convention_strength x partner_same), FAMILY as the unit.

WHY FAMILY. Variants within a family are settings of one structural manipulation.
The partner manipulation is WITHIN stimulus, so each stimulus yields a gap
(P(ENTER|same) - P(ENTER|diff)); beta3 is the difference in mean gap between
high-convention and low-convention stimuli. Because our selected pairs use
DISTINCT families on each side, the effective sample size for that contrast is the
number of FAMILIES per side, not the number of trials. Power therefore scales with
families, which is exactly why the spec asks to vary stimulus count, not reps.

EFFECT SIZE IS EMPIRICAL, NOT ASSUMED. From the 384-call manipulation check, the
SAME-minus-DIFF gap in predicted P(match) rises with the focal model's own
convention strength at +0.051/unit (GPT) and +0.066/unit (Claude). Over a
HIGH(.95) vs LOW(.30) contrast that implies beta3 = +0.033 / +0.043 in
risk-difference terms. Those are the anchored values; larger ones are shown as
optimistic scenarios, and the prior Study 2's GPT arm ruled out anything above
+0.118, which bounds the plausible range from the other side.

CAVEAT ON UNITS. The anchor comes from a PREDICTION task; Stage C measures a
DECISION. A decision near a payoff threshold can amplify a small probability
difference, or a safe payoff can swamp it. The anchor is the best available, not a
guarantee, so the whole grid is reported rather than a single number.

TEST. Statistic = mean(gap | high families) - mean(gap | low families).
Inference = permutation of the high/low label across families. This treats family
as the unit and needs no distributional assumption - the same frozen-statistic
style used in the prior Study 2's dose-response analysis.

Run:  python3 power_simulation.py
"""
import os, json
import numpy as np
import s4_common as S

SEED = 20260830
NSIM = 1500
NPERM = 600
CHUNK = 250
ALPHA = 0.05

# ---- anchored parameters ----------------------------------------------------
BASE = 0.40          # P(ENTER) on a LOW stimulus with a DIFFERENT partner, mid payoff
HIGH_EFF = 0.25      # main effect of a strong own convention (risk difference)
PARTNER_EFF = 0.10   # main effect of a same-model partner; manipulation check gave
                     # a flat discount of ~0.11 in predicted P(match)
PAYOFF_EFF = 0.055   # per point of safe payoff, from the Study 1 betting logistic
                     # (-0.527/point on the logit scale near p=.5)
SD_FAM = 0.12        # between-family sd of attempt rate, probability scale
SAFE = np.array([3, 5, 7, 9])

B3_GRID = [0.00, 0.033, 0.043, 0.06, 0.10, 0.15, 0.20]
NPAIR_GRID = [4, 6, 7, 8, 10, 12, 15, 20, 30, 40]
REPS_GRID = [20, 30]


def simulate(n_pairs, reps, b3, nsim, rng):
    """Return (nsim,) array of permutation p-values for the beta3 contrast."""
    # cells: (nsim, n_pairs, level, partner, payoff); level 0 = LOW, 1 = HIGH
    lev = np.array([0.0, 1.0])[None, None, :, None, None]
    par = np.array([0.0, 1.0])[None, None, None, :, None]     # 1 = SAME
    pay = SAFE[None, None, None, None, :]

    # one family per (pair, level) -> distinct families on the two sides
    u = rng.normal(0, SD_FAM, size=(nsim, n_pairs, 2))[:, :, :, None, None]

    p = (BASE + HIGH_EFF * lev + PARTNER_EFF * par + b3 * lev * par
         - PAYOFF_EFF * (pay - 6.0) + u)
    p = np.clip(p, 0.01, 0.99)
    k = rng.binomial(reps, p)                      # attempt counts
    phat = k / reps

    # gap per stimulus, averaged over payoffs
    gap = (phat[:, :, :, 1, :] - phat[:, :, :, 0, :]).mean(axis=3)   # (nsim,np,2)
    obs = gap[:, :, 1].mean(axis=1) - gap[:, :, 0].mean(axis=1)

    # permutation across the 2*n_pairs family-level gaps.
    # Chunked over simulations: the full (nsim, NPERM, 2*n_pairs) index array is
    # >1GB at the top of the grid, and argsort on it dominates runtime.
    flat = gap.reshape(nsim, 2 * n_pairs)
    out = np.empty(nsim)
    for a in range(0, nsim, CHUNK):
        b = min(a + CHUNK, nsim)
        idx = np.argsort(rng.random((b - a, NPERM, 2 * n_pairs)), axis=2)
        perm = np.take_along_axis(flat[a:b, None, :], idx, axis=2)
        stat = (perm[:, :, n_pairs:].mean(axis=2)
                - perm[:, :, :n_pairs].mean(axis=2))
        out[a:b] = (np.abs(stat) >= np.abs(obs[a:b])[:, None]).mean(axis=1)
    return out


def main():
    rng = np.random.default_rng(SEED)
    L = []

    def p(s=""):
        print(s); L.append(s)

    p("# Power for beta3 - family as the unit of independence")
    p()
    p(f"`{NSIM}` simulations per cell, permutation test with `{NPERM}` "
      f"re-labellings, alpha = {ALPHA}.")
    p()
    p("Parameters anchored in this project's own data:")
    p()
    p(f"- baseline P(ENTER) on LOW x DIFFERENT, mid payoff: {BASE}")
    p(f"- main effect of strong own convention: {HIGH_EFF}")
    p(f"- main effect of same-model partner: {PARTNER_EFF} "
      "(manipulation check flat discount ~0.11)")
    p(f"- safe-payoff effect: {PAYOFF_EFF}/point (Study 1 betting logistic)")
    p(f"- between-family sd of attempt rate: {SD_FAM}")
    p()
    p("**Empirically anchored beta3 = +0.033 (GPT) / +0.043 (Claude)**, from the "
      "manipulation check's own-convention gradient. The prior Study 2's GPT arm "
      "excluded partner effects above +0.118, bounding the range from above.")
    p()

    results = {}
    for reps in REPS_GRID:
        p(f"## {reps} trials per focal x stimulus x partner x payoff cell")
        p()
        p("| pairs/model | " + " | ".join(f"b3={b:.3f}" for b in B3_GRID) + " |")
        p("|---" * (len(B3_GRID) + 1) + "|")
        for npair in NPAIR_GRID:
            row = []
            for b3 in B3_GRID:
                pv = simulate(npair, reps, b3, NSIM, rng)
                pw = float((pv < ALPHA).mean())
                results[(reps, npair, b3)] = pw
                row.append(f"{pw:.2f}")
            calls = npair * 2 * 2 * 4 * reps * 2      # x2 focal models
            p(f"| **{npair}** ({calls:,} calls) | " + " | ".join(row) + " |")
        p()
        p("First column (b3=0) is the empirical SIZE of the test; it should sit "
          f"near {ALPHA}.")
        p()

    # ---- minimum families for 80% / 90% -------------------------------------
    p("## Families needed for 80% / 90% power")
    p()
    p("| b3 | reps | families/side for 80% | for 90% |")
    p("|---|---|---|---|")
    for b3 in B3_GRID[1:]:
        for reps in REPS_GRID:
            n80 = next((n for n in NPAIR_GRID if results[(reps, n, b3)] >= 0.80), None)
            n90 = next((n for n in NPAIR_GRID if results[(reps, n, b3)] >= 0.90), None)
            p(f"| {b3:.3f} | {reps} | {n80 if n80 else '>40'} | "
              f"{n90 if n90 else '>40'} |")
    p()

    # ---- verdict at achieved n ----------------------------------------------
    p("## At the battery we actually have")
    p()
    p("Discovery yielded **8** distinct-family pairs for GPT and **7** for Claude.")
    p()
    p("| focal | pairs | anchored b3 | power @20 reps | power @30 reps |")
    p("|---|---|---|---|---|")
    for focal, npair, b3 in (("GPT-5.5", 8, 0.033), ("Claude Opus 5", 7, 0.043)):
        p(f"| {focal} | {npair} | {b3:.3f} | "
          f"{results[(20, npair, b3)]:.2f} | {results[(30, npair, b3)]:.2f} |")
    p()
    p("| focal | pairs | power @ b3=0.10 | @ b3=0.15 | @ b3=0.20 |")
    p("|---|---|---|---|---|")
    for focal, npair in (("GPT-5.5", 8), ("Claude Opus 5", 7)):
        p(f"| {focal} | {npair} | {results[(30, npair, 0.10)]:.2f} | "
          f"{results[(30, npair, 0.15)]:.2f} | {results[(30, npair, 0.20)]:.2f} |")
    p()

    out = os.path.join(S.DATA, "power_simulation.md")
    open(out, "w").write("\n".join(L) + "\n")
    json.dump({f"{k[0]}_{k[1]}_{k[2]}": v for k, v in results.items()},
              open(os.path.join(S.DATA, "power_simulation.json"), "w"), indent=1)
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
