"""
Pair-constrained Bayesian models for Stage C.

WHY THIS REPLACES THE LATENT-BELIEF-FUNCTION MODEL

The experiment identifies a WITHIN-PAIR CONTRAST, not a belief function over stimuli.
Reconstructing q from auditor + salience + policy-specific terms needed 4 parameters
per model against 6 (GPT) and 4 (Claude) stimuli - saturated for Claude, and with the
two public predictors correlated at r = 0.95+. These models ask only the question the
design was built to answer.

MODELS

  B0  payoff only          logit P = a_m + b_m * S
  B1  payoff + is_high     logit P = a_m + b_m * S + delta * is_high     <- direct effect
  B2  pair-constrained q   logit P = a_m + beta_m * (10*q_cond - S)      <- primary
  B3  B1 + auditor         adds a standardized auditor term (robustness)
  B3b B1 + auditor + sal   both public terms (collinear; not separately interpreted)

B2's parameterisation keeps q in (0,1) by construction:

  logit q_high[p] = mid[p] + d[p]/2
  logit q_low[p]  = mid[p] - d[p]/2
  mid[p] ~ Normal(mu_mid, sigma_mid)
  d[p]   ~ Normal(mu_delta, sigma_delta)      <- mu_delta is the primary parameter

A KNOWN, DELIBERATE RIDGE. alpha_m and mu_mid are only weakly separately identified:
adding c to alpha_m and subtracting c/(10*beta_m) from every mid in that model gives
almost the same fit. This is a property of the design, not a coding error - the data
pin down where each pair sits RELATIVE to the model's own baseline, not the absolute
level. It does not touch the quantity of interest: d[p] is a within-pair contrast and
alpha_m is common to both members of a pair, so alpha cannot absorb it. Expect the
posterior for q LEVELS to be wider than for q DIFFERENCES, and read mu_delta, not
mu_mid. A no-alpha variant (alpha fixed at 0, q carries the level) is fitted as a
diagnostic to confirm mu_delta is unaffected.
"""
import json, os
import numpy as np
import pymc as pm

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(os.path.dirname(HERE), "bayesian_policy_self_knowledge",
                    "model_data.json")


def load():
    """Stage C trials tagged with pair index and is_high, plus cell predictors."""
    d = json.load(open(DATA))
    cell_pair, cell_high = {}, {}
    for pi, pr in enumerate(d["pairs"]):
        cell_pair[pr["hi_ix"]] = pi; cell_high[pr["hi_ix"]] = 1
        cell_pair[pr["lo_ix"]] = pi; cell_high[pr["lo_ix"]] = 0
    missing = [c for c in range(len(d["cells"])) if c not in cell_pair]
    if missing:
        raise SystemExit(f"cells not in any approved pair: {missing}")
    for t in d["trials"]:
        t["pair"] = cell_pair[t["cell"]]
        t["is_high"] = cell_high[t["cell"]]
    return d


def arrays(d, keep_pairs=None):
    tr = d["trials"]
    if keep_pairs is not None:
        tr = [t for t in tr if t["pair"] in keep_pairs]
    C = d["cells"]
    aud = np.array([c["aud_mean"] for c in C]); sal = np.array([c["sal_mean"] for c in C])
    z_aud = (aud - aud.mean()) / aud.std(ddof=0)
    z_sal = (sal - sal.mean()) / sal.std(ddof=0)
    return dict(
        y=np.array([t["y"] for t in tr], dtype="int8"),
        safe=np.array([t["safe"] for t in tr], dtype="float64"),
        cell=np.array([t["cell"] for t in tr], dtype="int32"),
        mix=np.array([t["model_ix"] for t in tr], dtype="int32"),
        pair=np.array([t["pair"] for t in tr], dtype="int32"),
        high=np.array([t["is_high"] for t in tr], dtype="float64"),
        z_aud=z_aud, z_sal=z_sal,
        aud_mu=float(aud.mean()), aud_sd=float(aud.std(ddof=0)),
        sal_mu=float(sal.mean()), sal_sd=float(sal.std(ddof=0)),
        nP=len(d["pairs"]), nM=2, nC=len(C),
        pair_model=np.array([d["models"].index(p["model"]) for p in d["pairs"]],
                            dtype="int32"))


def build(kind, d, keep_pairs=None, by_model=False, no_alpha=False):
    a = arrays(d, keep_pairs)
    y, safe, mix, pair, high, cell = (a["y"], a["safe"], a["mix"], a["pair"],
                                      a["high"], a["cell"])
    nM, nP = a["nM"], a["nP"]

    with pm.Model() as m:
        if no_alpha:
            alpha = pm.math.constant(np.zeros(nM))
        else:
            alpha = pm.Normal("alpha", 0.0, 1.5, shape=nM)

        if kind == "b2":
            beta = pm.LogNormal("beta", np.log(1.0), 0.75, shape=nM)
            mu_mid = pm.Normal("mu_mid", 0.0, 1.5)
            sig_mid = pm.HalfNormal("sigma_mid", 1.0)
            mid_z = pm.Normal("mid_z", 0.0, 1.0, shape=nP)
            mid = pm.Deterministic("mid", mu_mid + sig_mid * mid_z)

            if by_model:                      # exploratory, weakly identified
                mu_delta = pm.Normal("mu_delta_by_model", 0.0, 1.0, shape=nM)
                mu_d_p = mu_delta[a["pair_model"]]
            else:
                mu_delta = pm.Normal("mu_delta", 0.0, 1.0)
                mu_d_p = mu_delta
            sig_delta = pm.HalfNormal("sigma_delta", 1.0)
            d_z = pm.Normal("d_z", 0.0, 1.0, shape=nP)
            dlt = pm.Deterministic("delta_logit_q", mu_d_p + sig_delta * d_z)

            q_hi = pm.Deterministic("q_high", pm.math.sigmoid(mid + dlt / 2))
            q_lo = pm.Deterministic("q_low", pm.math.sigmoid(mid - dlt / 2))
            pm.Deterministic("delta_q", q_hi - q_lo)
            q_cond = pm.math.switch(pm.math.eq(high, 1.0), q_hi[pair], q_lo[pair])
            eta = alpha[mix] + beta[mix] * (10.0 * q_cond - safe)
        else:
            bS = pm.Normal("bS", 0.0, 1.0, shape=nM)
            eta = alpha[mix] + bS[mix] * safe
            if kind in ("b1", "b3", "b3b"):
                if by_model:
                    dl = pm.Normal("delta_by_model", 0.0, 1.0, shape=nM)
                    eta = eta + dl[mix] * high
                else:
                    dl = pm.Normal("delta", 0.0, 1.0)
                    eta = eta + dl * high
            if kind in ("b3", "b3b"):
                g_aud = pm.Normal("gamma_aud", 0.0, 1.0)
                eta = eta + g_aud * a["z_aud"][cell]
            if kind == "b3b":
                g_sal = pm.Normal("gamma_sal", 0.0, 1.0)
                eta = eta + g_sal * a["z_sal"][cell]

        pm.Bernoulli("y", p=pm.math.sigmoid(eta), observed=y)
    return m
