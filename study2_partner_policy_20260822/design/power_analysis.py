"""
STUDY 2 POWER ANALYSIS - Stimulus x Partner interaction on P(ATTEMPT).

No arguments. Paths resolve from this file's location. NO API CALLS.

    python3 power_analysis.py

WHAT IS SIMULATED
-----------------
Study 2 is a 2 (Stimulus: HIGH vs LOW own-copy match) x 2 (Partner: SAME model vs
DIFFERENT model, both named explicitly) within-model design. The primary test is the
interaction: is the HIGH-minus-LOW attempt gap larger under SAME than under DIFFERENT?

The data-generating process is anchored to Study 1's OBSERVED Stage C cell rates
(data/attempt_rates.csv of the 20260812_1401 run). Each of Study 1's five matched
pairs supplies, at each safe payoff, the pair of attempt rates
(p_high, p_low). Those are taken as the SAME-partner arm of Study 2. The
DIFFERENT-partner arm is constructed as

    p_low_diff  = clip(p_low_same + M)                 M = partner main effect
    p_high_diff = clip(p_low_diff + r * gap_same)      r = interaction leakage

with gap_same = ATTEN * (p_high_same - p_low_same). r = 0 is a pure interaction
(the model differentiates HIGH from LOW only when the partner is a copy of itself);
r = 1 is the null (no interaction, only main effects). ATTEN < 1 shrinks Study 1's
observed gaps to guard against the point estimates being optimistic.

TEST STATISTIC - FROZEN, AND ON RAW COUNTS
------------------------------------------
Per (pair p, payoff s), from raw counts k and equal per-cell n:

    DiD(p,s) = (k_HS - k_LS)/n - (k_HD - k_LD)/n

    T = mean over pairs of ( mean over payoffs of DiD(p,s) )

Null distribution: permute the PARTNER label within each (pair x payoff x stimulus
role) stratum. With equal n per cell that permutation is exactly a hypergeometric
draw on the pooled successes, so it is executed exactly rather than by shuffling.
One-sided (H1: T > 0), p = (#{T* >= T_obs - 1e-12} + 1) / (PERM + 1).

The `- 1e-12` tolerance and the use of RAW COUNTS rather than a rounded rate column
are carried over deliberately from Study 1's fix (2026-08-12 adversarial review:
p = 0.0485 reported vs 0.1334 true, because round(k/n, 4) moved the observed
statistic off the achievable lattice and silently dropped the tied permutation
replicates that carry most of the one-sided tail at n = 30).

Permuting the partner label within (pair x payoff x role) is EXACT under the sharp
null of no partner effect at all, and APPROXIMATE under the additive null (a partner
main effect but no interaction), because the main effect cancels from the
difference-of-differences in expectation but not from the within-stratum variance.
The script therefore measures the empirical size of the test under the additive null
with a large partner main effect and reports it; do not take calibration on faith.
"""
import csv
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY2 = os.path.dirname(HERE)
PROJ = os.path.dirname(STUDY2)
STUDY1 = os.path.join(PROJ, "policy_specific_self_coordination_20260812_1401")
ATTEMPT_RATES = os.path.join(STUDY1, "data", "attempt_rates.csv")

OUT_TABLE = os.path.join(HERE, "power_table.csv")
FIG_PNG = os.path.join(STUDY2, "figures", "study2_power.png")
FIG_PDF = os.path.join(STUDY2, "figures", "study2_power.pdf")

SEED = 20260822
ALPHA = 0.05          # one-sided
N_REPS = 1000         # simulated experiments per condition
N_PERM = 500          # permutation replicates per simulated experiment

# Study 1's five approved matched pairs (pair_id -> focal model, HIGH, LOW).
PAIRS = [
    ("gpt__c_contr_subtle__vs__b_spiral_cw", "gpt", "c_contr_subtle", "b_spiral_cw"),
    ("gpt__s_convexity__vs__d_dens_extreme", "gpt", "s_convexity", "d_dens_extreme"),
    ("gpt__c_open_cplx__vs__s_density", "gpt", "c_open_cplx", "s_density"),
    ("claude__b_spiral_cw__vs__rot", "claude", "b_spiral_cw", "rot"),
    ("claude__s_convexity__vs__d_dens_extreme", "claude", "s_convexity", "d_dens_extreme"),
]

PAYOFFS = [3, 5, 7, 9]

# Trial ALLOCATIONS over the safe-payoff grid, as weights that are normalised to a
# fixed TOTAL number of trials per (pair x stimulus x partner) block. "spread" is
# Study 1's allocation; the others concentrate on the payoffs where Study 1's
# attempt rate was away from ceiling.
ALLOCATIONS = {
    "spread_3579":  {3: 1, 5: 1, 7: 1, 9: 1},     # Study 1
    "focus_79":     {7: 1, 9: 1},
    "focus_9":      {9: 1},
    "anchored_79":  {3: 1, 5: 1, 7: 4, 9: 4},     # 10/10/40/40
}

# ---- cost model -------------------------------------------------------------
# Study 1 measured Stage C betting input at 1,084 Claude tokens/call (README, via
# Anthropic count_tokens) with 300-500 output tokens. Study 2's prompt adds the
# named-partner clause; budget 1,150 input. Claude Opus 5 is $5 / $25 per MTok.
# GPT-5.5 pricing is NOT verified (no OpenAI pricing endpoint); Study 1's README
# assumes it is comparable and so does this, which is why a range is reported.
COST_IN_PER_CALL = 1150 * 5.0e-6
COST_OUT_LO = 300 * 25.0e-6
COST_OUT_HI = 500 * 25.0e-6
COST_LO = COST_IN_PER_CALL + COST_OUT_LO      # ~$0.0133
COST_HI = COST_IN_PER_CALL + COST_OUT_HI      # ~$0.0183


def load_pair_profiles():
    """-> list of (pair_id, model, dict payoff -> (p_high, p_low))."""
    if not os.path.exists(ATTEMPT_RATES):
        sys.exit(f"missing Study 1 input: {ATTEMPT_RATES}")
    rate = {}
    for r in csv.DictReader(open(ATTEMPT_RATES)):
        # RAW COUNTS, not the rounded attempt_rate column.
        rate[(r["model"], r["stimulus"], int(r["safe_payoff"]))] = (
            int(r["n_attempt"]), int(r["n"]))
    profiles = []
    for pid, m, hi, lo in PAIRS:
        prof = {}
        for s in PAYOFFS:
            kh, nh = rate[(m, hi, s)]
            kl, nl = rate[(m, lo, s)]
            prof[s] = (kh / nh, kl / nl)
        profiles.append((pid, m, prof))
    return profiles


def cell_probs(profiles, pair_idx, payoffs, r, atten, main_eff):
    """-> array (n_draws, n_pairs, n_payoffs, 4) of [p_HS, p_LS, p_HD, p_LD]."""
    tmpl = np.zeros((len(profiles), len(payoffs), 4))
    for i, (_pid, _m, prof) in enumerate(profiles):
        for j, s in enumerate(payoffs):
            ph, pl = prof[s]
            gap = atten * (ph - pl)
            p_LS = pl
            p_HS = min(1.0, max(0.0, pl + gap))
            p_LD = min(1.0, max(0.0, pl + main_eff))
            p_HD = min(1.0, max(0.0, p_LD + r * gap))
            tmpl[i, j] = (p_HS, p_LS, p_HD, p_LD)
    return tmpl[pair_idx]


def simulate(profiles, n_pairs, per_cell, allocation, r, atten=1.0, main_eff=0.0,
             n_reps=N_REPS, n_perm=N_PERM, seed=SEED, rep_chunk=100):
    """Return (power, mean_T, mean_p). per_cell = trials in EACH of the four cells
    at EACH payoff carried by `allocation` (weights scale it)."""
    rng = np.random.default_rng(seed)
    w = ALLOCATIONS[allocation]
    payoffs = sorted(w)
    # Normalise so total trials per (pair x stimulus x partner) block is fixed at
    # per_cell * 4 (Study 1's spread over four payoffs at `per_cell` each).
    tot = per_cell * len(PAYOFFS)
    ns = np.array([max(2, int(round(tot * w[s] / sum(w.values())))) for s in payoffs])

    rejects = 0
    T_sum = 0.0
    p_sum = 0.0
    done = 0
    while done < n_reps:
        R = min(rep_chunk, n_reps - done)
        pair_idx = rng.integers(0, len(profiles), size=(R, n_pairs))
        P = cell_probs(profiles, pair_idx, payoffs, r, atten, main_eff)   # (R,G,S,4)
        N = np.broadcast_to(ns[None, None, :, None], P.shape)
        k = rng.binomial(N, P)                                            # (R,G,S,4)
        nS = ns[None, None, :]

        kHS, kLS, kHD, kLD = k[..., 0], k[..., 1], k[..., 2], k[..., 3]
        did = (kHS - kLS) / nS - (kHD - kLD) / nS
        denom = n_pairs * len(payoffs)
        T_obs = did.sum(axis=(1, 2)) / denom                              # (R,)

        # A (pair,payoff) cell whose four probabilities are all 0 or 1 with the SAME
        # value in both partner arms yields DiD == 0 for the observed statistic and
        # for every permutation replicate. Skip it: exact, and roughly halves the
        # work under the Study 1 allocation where SAFE=3 and 5 sit at ceiling.
        det = ((P == 0) | (P == 1)).all(axis=-1) & (P[..., 0] == P[..., 2]) \
            & (P[..., 1] == P[..., 3])
        live = ~det
        idx = np.flatnonzero(live.ravel())
        if idx.size == 0:
            T_perm_sum = np.zeros((n_perm, R))
        else:
            KH = (kHS + kHD).ravel()[idx]
            KL = (kLS + kLD).ravel()[idx]
            nvec = np.broadcast_to(nS, kHS.shape).ravel()[idx]
            twoN = 2 * nvec
            # exact permutation of the partner label within each role stratum
            aHS = rng.hypergeometric(KH, twoN - KH, nvec, size=(n_perm, idx.size))
            aLS = rng.hypergeometric(KL, twoN - KL, nvec, size=(n_perm, idx.size))
            did_p = (2 * (aHS - aLS) - (KH - KL)[None, :]) / nvec[None, :]
            rep_of = (idx // (n_pairs * len(payoffs))).astype(np.int64)
            # sum live cells back into their replicate (one-hot matmul; add.at is slow)
            onehot = np.zeros((idx.size, R))
            onehot[np.arange(idx.size), rep_of] = 1.0
            T_perm_sum = did_p @ onehot
        T_perm = T_perm_sum / denom
        ge = (T_perm >= T_obs[None, :] - 1e-12).sum(axis=0)
        pv = (ge + 1) / (n_perm + 1)

        rejects += int((pv <= ALPHA).sum())
        T_sum += float(T_obs.sum())
        p_sum += float(pv.sum())
        done += R

    n_calls_per_pair = 2 * 2 * int(ns.sum())     # 2 stimuli x 2 partners x trials
    return dict(power=rejects / n_reps, mean_T=T_sum / n_reps, mean_p=p_sum / n_reps,
                payoffs="+".join(str(s) for s in payoffs),
                n_per_payoff_cell="+".join(str(int(v)) for v in ns),
                calls_per_pair=n_calls_per_pair)


def row(profiles, block, n_pairs, per_cell, allocation, r, atten=1.0, main_eff=0.0):
    res = simulate(profiles, n_pairs, per_cell, allocation, r, atten, main_eff)
    total = n_pairs * res["calls_per_pair"]
    return dict(
        block=block, n_pairs=n_pairs, trials_per_cell=per_cell, allocation=allocation,
        payoffs=res["payoffs"], n_per_payoff_cell=res["n_per_payoff_cell"],
        diff_gap_ratio=r, gap_attenuation=atten, partner_main_effect=main_eff,
        power=round(res["power"], 4), mean_stat_T=round(res["mean_T"], 4),
        mean_perm_p=round(res["mean_p"], 4),
        total_calls=total,
        cost_usd_lo=round(total * COST_LO, 1), cost_usd_hi=round(total * COST_HI, 1),
        n_reps=N_REPS, n_perm=N_PERM)


def main():
    profiles = load_pair_profiles()
    print("=== STUDY 2 POWER ANALYSIS - Stimulus x Partner interaction ===")
    print(f"    source of effect sizes : {ATTEMPT_RATES}")
    print(f"    {N_REPS} simulated experiments x {N_PERM} permutations per condition")
    print(f"    one-sided alpha = {ALPHA}; statistic on RAW COUNTS\n")

    print("  Study 1 observed SAME-arm cell rates (the simulation's ground truth):")
    print(f"    {'pair':44}" + "".join(f"  S{s}:high/low" for s in PAYOFFS))
    for pid, m, prof in profiles:
        cells = "".join(f"  {prof[s][0]:.2f}/{prof[s][1]:.2f}" for s in PAYOFFS)
        print(f"    {pid:44}{cells}")
    print()

    rows = []

    # ---- 0. calibration: r = 1 is the additive null (no interaction) ----------
    print("  [0] NULL CALIBRATION (r = 1.0 -> no interaction). Empirical size:")
    for me in (0.0, -0.10, -0.25):
        for alloc in ("spread_3579", "focus_79"):
            rr = row(profiles, "null_calibration", 5, 60, alloc, 1.0, main_eff=me)
            rows.append(rr)
            print(f"      partner main effect {me:+.2f}  {alloc:12} "
                  f"size = {rr['power']:.3f}")
    print()

    # ---- 1. main power grid ---------------------------------------------------
    print("  [1] POWER GRID")
    hdr = f"    {'alloc':12}{'pairs':>6}{'n/cell':>8}{'r':>6}{'power':>8}{'calls':>8}{'$':>9}"
    print(hdr)
    for alloc in ("spread_3579", "focus_79"):
        for n_pairs in (3, 5, 8):
            for per_cell in (30, 60, 100):
                for r in (0.0, 0.25, 0.5, 0.75):
                    rr = row(profiles, "power_grid", n_pairs, per_cell, alloc, r)
                    rows.append(rr)
                    print(f"    {alloc:12}{n_pairs:>6}{per_cell:>8}{r:>6.2f}"
                          f"{rr['power']:>8.3f}{rr['total_calls']:>8}"
                          f"{rr['cost_usd_lo']:>6.0f}-{rr['cost_usd_hi']:<3.0f}",
                          flush=True)
    print()

    # ---- 2. allocation comparison at MATCHED total budget ---------------------
    print("  [2] ALLOCATION at matched total trials (5 pairs, r = 0.25)")
    print(f"    {'alloc':13}{'payoffs':>10}{'n each':>16}{'power':>8}{'calls':>8}")
    for per_cell in (30, 60, 100):
        for alloc in ALLOCATIONS:
            rr = row(profiles, "allocation", 5, per_cell, alloc, 0.25)
            rows.append(rr)
            print(f"    {alloc:13}{rr['payoffs']:>10}{rr['n_per_payoff_cell']:>16}"
                  f"{rr['power']:>8.3f}{rr['total_calls']:>8}", flush=True)
    print()

    # ---- 3. attenuated-gap sensitivity ---------------------------------------
    print("  [3] SENSITIVITY: Study 1 gaps shrunk to 70% (guards optimistic points)")
    for n_pairs in (5, 8):
        for per_cell in (60, 100):
            for r in (0.0, 0.25):
                rr = row(profiles, "attenuated", n_pairs, per_cell, "focus_79", r,
                         atten=0.7)
                rows.append(rr)
                print(f"    pairs={n_pairs} n/cell={per_cell} r={r:.2f} "
                      f"power={rr['power']:.3f}", flush=True)
    print()

    with open(OUT_TABLE, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"  -> {OUT_TABLE}  ({len(rows)} rows)")

    make_figure(rows)


def make_figure(rows):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    try:
        plt.style.use("academic")
    except Exception:
        plt.rcParams.update({
            "font.family": "sans-serif", "font.sans-serif": ["Arial", "Helvetica"],
            "font.size": 9, "axes.linewidth": 0.8, "axes.spines.top": False,
            "axes.spines.right": False, "xtick.direction": "out",
            "ytick.direction": "out", "figure.dpi": 300})

    grid = [r for r in rows if r["block"] == "power_grid"
            and r["allocation"] == "focus_79" and r["gap_attenuation"] == 1.0]
    fig, axes = plt.subplots(1, 2, figsize=(5.5, 3.2), sharey=True)
    styles = {3: ("o", "-", "0.0"), 5: ("s", "--", "0.35"), 8: ("^", ":", "0.6")}
    for ax, r_val in zip(axes, (0.0, 0.5)):
        for npair in (3, 5, 8):
            sub = sorted([q for q in grid if q["n_pairs"] == npair
                          and q["diff_gap_ratio"] == r_val],
                         key=lambda q: q["trials_per_cell"])
            mk, ls, col = styles[npair]
            ax.plot([q["trials_per_cell"] for q in sub],
                    [q["power"] for q in sub], marker=mk, linestyle=ls, color=col,
                    markerfacecolor="none" if npair != 3 else col,
                    markersize=4, linewidth=0.9, label=f"{npair} pairs")
        ax.axhline(0.80, color="0.0", linewidth=0.6, linestyle=(0, (1, 3)))
        ax.set_xlabel("trials per cell (budget unit)")
        ax.set_xticks([30, 60, 100])
        ax.set_ylim(0, 1.02)
        ax.text(0.03, 0.96, f"DIFFERENT gap = {r_val:g}" + r"$\times$ SAME",
                transform=ax.transAxes, va="top", ha="left", fontsize=8)
    axes[0].set_ylabel("power (one-sided, " + r"$\alpha$" + " = 0.05)")
    axes[0].legend(frameon=False, fontsize=8, loc="lower right")
    fig.tight_layout()
    os.makedirs(os.path.dirname(FIG_PNG), exist_ok=True)
    fig.savefig(FIG_PNG, dpi=300, bbox_inches="tight")
    fig.savefig(FIG_PDF, bbox_inches="tight")
    print(f"  -> {FIG_PNG}\n  -> {FIG_PDF}")


if __name__ == "__main__":
    main()
