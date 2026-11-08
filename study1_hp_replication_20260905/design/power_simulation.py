"""Simulation-based power for the higher-powered Study 1 replication.

Unit of evidence is the MATCHED PAIR. A pair contributes
    delta_i = P(ATTEMPT | high own-copy reliability) - P(ATTEMPT | low)
Pairs are independent: non-reuse of stimuli is enforced by the selector, and a
GPT pair and a Claude pair are separate contrasts.

Baseline attempt rates are the OBSERVED Study 1 marginals, so the ceiling at
safe = 3 and 5 is modelled rather than assumed away.

Primary test simulated: paired sign-flip permutation on pair-level deltas
(exact enumeration under 2^N when N <= 20, else 20,000 sampled flips).
Reported alongside: proportion of pairs in the predicted direction.
"""
import numpy as np, json, sys
from pathlib import Path

RNG = np.random.default_rng(20260905)

# Observed Study 1 marginals, P(ATTEMPT) for the LOW member at each safe payoff.
BASE_LOW = {3: 1.000, 5: 0.973, 7: 0.740, 9: 0.207}
PAYOFFS = [3, 5, 7, 9]

def sim_once(n_pairs, mu, tau, n_per_cell, payoffs, rng):
    """One synthetic study. Returns (mean delta, permutation p, frac positive)."""
    eff = rng.normal(mu, tau, size=n_pairs)              # per-pair true effect
    p_lo = np.array([BASE_LOW[s] for s in payoffs])       # (P,)
    # headroom scaling: the effect can only act where the LOW rate leaves room,
    # normalised so the stated mu is recovered at the most informative payoff.
    room = (1.0 - p_lo) / (1.0 - BASE_LOW[9])
    p_hi = np.clip(p_lo[None, :] + eff[:, None] * room[None, :], 0.001, 0.999)
    hi = rng.binomial(n_per_cell, np.broadcast_to(p_hi, (n_pairs, len(payoffs))))
    lo = rng.binomial(n_per_cell, np.broadcast_to(p_lo, (n_pairs, len(payoffs))))
    deltas = (hi.sum(1) - lo.sum(1)) / (n_per_cell * len(payoffs))
    obs = deltas.mean()
    exact = n_pairs <= 12                  # exact enumeration stays cheap here
    if exact:
        signs = np.array([[1 if (k >> j) & 1 else -1 for j in range(n_pairs)]
                          for k in range(2 ** n_pairs)], dtype=np.int8)
    else:
        signs = rng.choice([-1, 1], size=(4000, n_pairs)).astype(np.int8)
    null = (signs * deltas).mean(axis=1)
    # Under EXACT enumeration the observed arrangement is already a member of the
    # null set, so adding it again would double-count it and inflate p. The +1
    # correction applies only to the sampled case.
    p = (float(np.sum(null >= obs)) / len(null) if exact
         else float((np.sum(null >= obs) + 1) / (len(null) + 1)))
    return obs, p, float((deltas > 0).mean())

def power(n_pairs, mu, tau, n_per_cell, payoffs, n_sim, alpha=0.05):
    rng = np.random.default_rng(abs(hash((n_pairs, mu, n_per_cell))) % 2**31)
    hits = 0; ds = []; fps = []
    for _ in range(n_sim):
        d, p, fp = sim_once(n_pairs, mu, tau, n_per_cell, payoffs, rng)
        hits += (p <= alpha); ds.append(d); fps.append(fp)
    return {"power": hits / n_sim, "mean_delta": float(np.mean(ds)),
            "mean_frac_positive": float(np.mean(fps))}

if __name__ == "__main__":
    N_SIM = int(sys.argv[1]) if len(sys.argv) > 1 else 600
    TAU = 0.0903                      # observed between-pair SD (Study 1, 5 pairs)
    SCEN = [("observed Study 1", 0.1450), ("moderate", 0.100),
            ("small", 0.070), ("very small", 0.050), ("null", 0.000)]
    NP = [5, 10, 20, 30]
    out = {"tau": TAU, "n_sim": N_SIM, "baseline_low": BASE_LOW, "grids": {}}

    for gname, grid in (("frozen {3,5,7,9}", PAYOFFS), ("informative {7,9}", [7, 9])):
        print(f"\n{'='*74}\nPAYOFF GRID: {gname}   n = 30 trials per member per payoff\n{'='*74}")
        print(f"{'scenario':<20}{'mu':>7}" + "".join(f"{f'{n} pairs':>11}" for n in NP))
        out["grids"][gname] = {}
        for label, mu in SCEN:
            row = []
            for n in NP:
                r = power(n, mu, TAU, 30, grid, N_SIM)
                row.append(r["power"]); out["grids"][gname][f"{label}|{n}"] = r
            tag = "  <- size (alpha)" if mu == 0 else ""
            print(f"{label:<20}{mu:>7.3f}" + "".join(f"{p:>11.3f}" for p in row) + tag)

    print(f"\n{'='*74}\nMORE PAIRS vs MORE CALLS  (mu = 0.100, frozen grid)\n{'='*74}")
    print(f"{'design':<34}{'pairs':>7}{'n/cell':>8}{'calls':>9}{'power':>9}")
    for n_pairs, n_cell in ((5,30),(5,60),(5,120),(5,240),(10,30),(20,30),(30,30)):
        r = power(n_pairs, 0.100, TAU, n_cell, PAYOFFS, N_SIM)
        calls = n_pairs * 2 * len(PAYOFFS) * n_cell
        print(f"{f'{n_pairs} pairs x {n_cell}/cell':<34}{n_pairs:>7}{n_cell:>8}{calls:>9}{r['power']:>9.3f}")
        out.setdefault("pairs_vs_calls", {})[f"{n_pairs}x{n_cell}"] = {**r, "calls": calls}

    Path("design/power_simulation.json").write_text(json.dumps(out, indent=1))
    print("\nwritten -> design/power_simulation.json")
