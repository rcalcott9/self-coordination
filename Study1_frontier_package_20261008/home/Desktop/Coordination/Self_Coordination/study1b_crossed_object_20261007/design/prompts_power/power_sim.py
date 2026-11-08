"""Power / sample size for the Study 1b PRIMARY test. Simulation only, no API calls.

Primary statistic, per predictor k (pooled over arrays j and objects o):
    beta_k = sum_j sum_o dhat_kjo * d_jo  /  sum_j [ sum_o d_jo^2  - bias_j ]
d_j    = p_GPT,j - p_Opus,j       measured on FRESH held-out reference draws
dhat_kj = q_k(GPT),j - q_k(Opus),j  mean predicted distributions (m reps each)
bias_j = sum_o [ phatG(1-phatG)/(nG-1) + phatO(1-phatO)/(nO-1) ]  (unbiased for sum d^2)
beta = 1 means the predictor reproduces the full measured difference; 0 means none.
Test: H0 beta_k = 0, two-sided, sign-flip of per-array numerators N_kj (array = unit).
Predictor difference: sign-flip on N_GPT,j - N_Opus,j (common denominator).

Generative model for predictions (mean of predictor k about target t on array j):
  m = (1 - ws - wt - wp - we) * uniform + ws * s_j + wt(k,t) * p_t + wp * p_k + we * e_kjt
  s_j shared salience = (pG + pO)/2;  p_k = predictor's own policy (projection);
  e_kjt ~ Dirichlet(1): idiosyncratic target-specific error (NOT shared across targets)
  each call q ~ Dirichlet(kappa * m); kappa from existing relational data (~50-80 median).
s_j and projection cancel in dhat when wt is target-invariant: dhat = wt * d + noise.
"""
import itertools, json, os
import numpy as np

rng = np.random.default_rng(20261007)
OUT = os.path.dirname(os.path.abspath(__file__))
CONC = np.array([.85, .05, .05, .05]); DIFF = np.array([.40, .25, .20, .15])
K0 = 60.0          # dispersion of true distributions around templates
WS, WP, WE = .30, .15, .20


def perm_to(v, modal):
    out = np.empty(4); others = [i for i in range(4) if i != modal]
    rng.shuffle(others)
    out[modal] = v[0]; out[others] = v[1:]
    return out


def true_arrays(S):
    G, O, strat = [], [], []
    for _ in range(S):                                  # opposing concentrated
        a, b = rng.choice(4, 2, replace=False)
        G.append(perm_to(CONC, a)); O.append(perm_to(CONC, b)); strat.append(0)
    for i in range(S):                                  # concentrated / diffuse (both directions)
        a = rng.integers(4)
        c, d = perm_to(CONC, a), perm_to(DIFF, a)
        (G.append(c), O.append(d)) if i % 2 == 0 else (G.append(d), O.append(c)); strat.append(1)
    for _ in range(S):                                  # shared-policy controls
        a = rng.integers(4); G.append(perm_to(CONC, a)); O.append(perm_to(CONC, a)); strat.append(2)
    G = np.array([rng.dirichlet(K0 * g) for g in G]); O = np.array([rng.dirichlet(K0 * o) for o in O])
    return G, O, np.array(strat)


def predict(P, own, target, wt, m, kappa):
    J = P.shape[0]
    s = (P["gpt"] if False else None)


def sim_once(S, m, nref, kappa, W, nflip=2000):
    G, O, strat = true_arrays(S)
    J = len(G); u = np.full(4, .25); s = (G + O) / 2
    pol = {"gpt": G, "claude": O}
    q = {}
    for k in ("gpt", "claude"):
        for t in ("gpt", "claude"):
            wt = W[(k, t)]
            e = rng.dirichlet(np.ones(4), size=J)
            mean = (1 - WS - wt - WP - WE) * u + WS * s + wt * pol[t] + WP * pol[k] + WE * e
            draws = np.array([[rng.dirichlet(kappa * mean[j]) for _ in range(m)] for j in range(J)])
            q[(k, t)] = draws.mean(1)
    pG = np.array([rng.multinomial(nref, g) for g in G]) / nref
    pO = np.array([rng.multinomial(nref, o) for o in O]) / nref
    d = pG - pO
    bias = (pG * (1 - pG)).sum(1) / (nref - 1) + (pO * (1 - pO)).sum(1) / (nref - 1)
    den = ((d ** 2).sum(1) - bias).sum()
    N = {k: ((q[(k, "gpt")] - q[(k, "claude")]) * d).sum(1) for k in ("gpt", "claude")}
    flips = rng.choice([-1.0, 1.0], size=(nflip, J))
    res = {}
    for k in N:
        b = N[k].sum() / den
        null = np.abs(flips @ N[k]) / den
        res[f"beta_{k}"] = b; res[f"p_{k}"] = (1 + (null >= abs(b)).sum()) / (nflip + 1)
    dd = N["gpt"] - N["claude"]
    nul = np.abs(flips @ dd)
    res["p_diff"] = (1 + (nul >= abs(dd.sum())).sum()) / (nflip + 1)
    res["beta_diff"] = dd.sum() / den
    # stratum-specific betas (secondary; control stratum has d ~ 0 so beta undefined -> report mean dhat^2)
    for sname, sid in (("opp", 0), ("cd", 1)):
        sel = strat == sid
        dens = ((d[sel] ** 2).sum(1) - bias[sel]).sum()
        for k in N:
            res[f"beta_{k}_{sname}"] = N[k][sel].sum() / dens
    return res


SCEN = {
    "null (wt=0)":             {("gpt", "gpt"): 0, ("gpt", "claude"): 0, ("claude", "gpt"): 0, ("claude", "claude"): 0},
    "weak shared (wt=.10)":    {k: .10 for k in itertools.product(("gpt", "claude"), repeat=2)},
    "moderate (wt=.20)":       {k: .20 for k in itertools.product(("gpt", "claude"), repeat=2)},
    "self-adv (.25 self/.10 cross)": {("gpt", "gpt"): .25, ("gpt", "claude"): .10, ("claude", "gpt"): .10, ("claude", "claude"): .25},
    "pred-diff (GPT .25, Opus .05)": {("gpt", "gpt"): .25, ("gpt", "claude"): .25, ("claude", "gpt"): .05, ("claude", "claude"): .05},
}

if __name__ == "__main__":
    NSIM = 400
    rows = []
    for (S, m, nref, kappa) in itertools.product((8, 12, 16), (4, 8), (24, 48), (40,)):
        for sc, W in SCEN.items():
            R = [sim_once(S, m, nref, kappa, W) for _ in range(NSIM)]
            row = dict(arrays_per_stratum=S, reps=m, nref=nref, kappa=kappa, scenario=sc,
                       power_gpt=np.mean([r["p_gpt"] < .05 for r in R]),
                       power_opus=np.mean([r["p_claude"] < .05 for r in R]),
                       power_diff=np.mean([r["p_diff"] < .05 for r in R]),
                       mean_beta_gpt=np.mean([r["beta_gpt"] for r in R]),
                       mean_beta_opus=np.mean([r["beta_claude"] for r in R]),
                       sd_beta_gpt=np.std([r["beta_gpt"] for r in R]))
            rows.append(row)
            print(json.dumps({k: (round(v, 3) if isinstance(v, float) else v) for k, v in row.items()}), flush=True)
    json.dump(rows, open(os.path.join(OUT, "power_results.json"), "w"), indent=1)
