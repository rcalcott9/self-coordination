"""Study 1b power, REDIRECTED primary: within-target self-vs-other predictor accuracy.
Simulation only, no API calls.

Crossed 2x2 per array j: predictor k in {G, O} x target t in {G, O}.
Score s_ktj = proper score of the MEAN forecast qbar_kt,j (average of m reps) against the
FRESH measured distribution phat_t,j (48 draws per target per array):
   quadratic (primary)  QS = sum_o phat_o * (2 q_o) - sum_o q_o^2      (higher = better)
   log (secondary)      LS = sum_o phat_o * log(max(q_o, 0.01)), q floored then renormalised
Both are linear in phat, so they are UNBIASED for the score against the true p, even with
sampling noise in the fresh draws.

Self effect (= predictor x target interaction in score ~ predictor + target + predictor:target
+ (1|array); balanced 2x2, so the LMM interaction equals the array-level contrast):
   SE_G,j = s_GG,j - s_OG,j      (target GPT: GPT predicting itself minus Opus predicting GPT)
   SE_O,j = s_OO,j - s_GO,j
   pooled SE_j = (SE_G,j + SE_O,j)/2 = interaction contrast / 2
Test: two-sided sign-flip over arrays on mean SE (per target and pooled).
Moderation: SE_j ~ TVD_j, with TVD computed from the INDEPENDENT SELECTION draws (n_sel per
model), not the fresh scoring draws. Permutation test of the slope. Also a stratum contrast:
divergent strata (S1, S2_G, S2_O) minus shared controls (S3).

Generative model, mean forecast of predictor k about target t on array j:
   m = (1-ws-wt-wp-we) u + ws s_j + wt(k,t) p_t + wp p_k + we e_kjt
 s_j = shared salience (pG+pO)/2; p_k = predictor's own policy (projection);
 e_kjt ~ Dir(1) target-specific idiosyncratic error. Each call q ~ Dir(kappa m), kappa = 40
 (existing relational data: median per-call kappa GPT ~79, Opus ~52, so 40 is conservative).
Note: projection (wp > 0) ALSO yields a self advantage, and it grows with divergence. The design
measures self-prediction advantage whatever its mechanism; it cannot by itself separate
simulation/projection from privileged access.
"""
import itertools, json, os
import numpy as np

rng = np.random.default_rng(202610072)
OUT = os.path.dirname(os.path.abspath(__file__))
CONC = np.array([.85, .05, .05, .05]); DIFF = np.array([.40, .25, .20, .15])
K0, KAPPA, WS, WE, NREF, NSEL, FLOOR = 60.0, 40.0, .30, .20, 48, 24, .01


def perm_to(v, modal):
    out = np.empty(4); oth = [i for i in range(4) if i != modal]; rng.shuffle(oth)
    out[modal] = v[0]; out[oth] = v[1:]; return out


def arrays(n1, n2g, n2o, n3):
    G, O, st = [], [], []
    for _ in range(n1):
        a, b = rng.choice(4, 2, replace=False); G.append(perm_to(CONC, a)); O.append(perm_to(CONC, b)); st.append("S1")
    for _ in range(n2g):
        a = rng.integers(4); G.append(perm_to(CONC, a)); O.append(perm_to(DIFF, a)); st.append("S2_G")
    for _ in range(n2o):
        a = rng.integers(4); G.append(perm_to(DIFF, a)); O.append(perm_to(CONC, a)); st.append("S2_O")
    for _ in range(n3):
        a = rng.integers(4); c = perm_to(CONC, a); G.append(c); O.append(c.copy()); st.append("S3")
    G = np.array([rng.dirichlet(K0 * g) for g in G]); O = np.array([rng.dirichlet(K0 * o) for o in O])
    return G, O, np.array(st)


def scores(q, p):
    qs = (p * 2 * q).sum(1) - (q ** 2).sum(1)
    qf = np.maximum(q, FLOOR); qf = qf / qf.sum(1, keepdims=True)
    ls = (p * np.log(qf)).sum(1)
    return qs, ls


def signflip_p(x, nflip=2000):
    f = rng.choice([-1.0, 1.0], size=(nflip, len(x)))
    return (1 + (np.abs(f @ x) >= abs(x.sum())).sum()) / (nflip + 1)


def perm_slope_p(x, y, nperm=2000):
    xc = x - x.mean(); b = (xc * y).sum() / (xc ** 2).sum()
    P = np.array([rng.permutation(y) for _ in range(nperm)])
    bn = (P @ xc) / (xc ** 2).sum()
    return b, (1 + (np.abs(bn) >= abs(b)).sum()) / (nperm + 1)


def sim_once(design, m, W, wp):
    G, O, st = arrays(*design); J = len(G); u = np.full(4, .25); s = (G + O) / 2
    pol = {"G": G, "O": O}
    qbar = {}
    for k in "GO":
        for t in "GO":
            e = rng.dirichlet(np.ones(4), size=J)
            mean = (1 - WS - W[(k, t)] - wp - WE) * u + WS * s + W[(k, t)] * pol[t] + wp * pol[k] + WE * e
            qbar[(k, t)] = np.array([rng.dirichlet(KAPPA * mean[j], size=m).mean(0) for j in range(J)])
    fresh = {t: np.array([rng.multinomial(NREF, x) for x in pol[t]]) / NREF for t in "GO"}
    sel = {t: np.array([rng.multinomial(NSEL, x) for x in pol[t]]) / NSEL for t in "GO"}
    tvd = .5 * np.abs(sel["G"] - sel["O"]).sum(1)
    res = {}
    for nm, ix in (("QS", 0), ("LS", 1)):
        sc = {(k, t): scores(qbar[(k, t)], fresh[t])[ix] for k in "GO" for t in "GO"}
        seG = sc[("G", "G")] - sc[("O", "G")]; seO = sc[("O", "O")] - sc[("G", "O")]; se = (seG + seO) / 2
        res[f"{nm}_self_pooled"] = se.mean(); res[f"{nm}_p_pooled"] = signflip_p(se)
        res[f"{nm}_p_G"] = signflip_p(seG); res[f"{nm}_p_O"] = signflip_p(seO)
        res[f"{nm}_self_G"] = seG.mean(); res[f"{nm}_self_O"] = seO.mean()
        b, pb = perm_slope_p(tvd, se); res[f"{nm}_mod_slope"] = b; res[f"{nm}_p_mod"] = pb
        div = st != "S3"
        res[f"{nm}_strat_contrast"] = se[div].mean() - se[~div].mean()
        lab = div.astype(float); _, pc = perm_slope_p(lab, se); res[f"{nm}_p_strat"] = pc
    return res


DESIGNS = {"25 (3/4/6/12)": (3, 4, 6, 12), "28 (5/5/7/11)": (5, 5, 7, 11), "32 (6/6/8/12)": (6, 6, 8, 12)}
SCEN = {   # (wt dict, wp)
    "null: equal wt=.10, no projection": ({kt: .10 for kt in itertools.product("GO", repeat=2)}, 0.0),
    "projection only (wp=.15, wt=.10)":  ({kt: .10 for kt in itertools.product("GO", repeat=2)}, .15),
    "weak privileged (self .16/cross .10)": ({("G", "G"): .16, ("O", "O"): .16, ("G", "O"): .10, ("O", "G"): .10}, 0.0),
    "privileged (self .25/cross .10)":  ({("G", "G"): .25, ("O", "O"): .25, ("G", "O"): .10, ("O", "G"): .10}, 0.0),
    "GPT-only self adv (G .25, else .10)": ({("G", "G"): .25, ("O", "O"): .10, ("G", "O"): .10, ("O", "G"): .10}, 0.0),
}

if __name__ == "__main__":
    NSIM = 400; rows = []
    for (dn, d), m, (sn, (W, wp)) in itertools.product(DESIGNS.items(), (4, 8, 12), SCEN.items()):
        R = [sim_once(d, m, W, wp) for _ in range(NSIM)]
        row = dict(design=dn, reps=m, scenario=sn)
        for nm in ("QS", "LS"):
            row.update({f"{nm}_pow_pooled": np.mean([r[f"{nm}_p_pooled"] < .05 for r in R]),
                        f"{nm}_pow_G": np.mean([r[f"{nm}_p_G"] < .05 for r in R]),
                        f"{nm}_pow_O": np.mean([r[f"{nm}_p_O"] < .05 for r in R]),
                        f"{nm}_pow_mod": np.mean([r[f"{nm}_p_mod"] < .05 for r in R]),
                        f"{nm}_pow_strat": np.mean([r[f"{nm}_p_strat"] < .05 for r in R]),
                        f"{nm}_mean_self": float(np.mean([r[f"{nm}_self_pooled"] for r in R])),
                        f"{nm}_sd_self": float(np.std([r[f"{nm}_self_pooled"] for r in R]))})
        rows.append(row)
        print(json.dumps({k: (round(v, 4) if isinstance(v, float) else v) for k, v in row.items()}), flush=True)
    json.dump(rows, open(os.path.join(OUT, "power_self_results.json"), "w"), indent=1)
