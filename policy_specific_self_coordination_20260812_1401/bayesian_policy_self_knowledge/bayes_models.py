"""
Hierarchical Bayesian decision models for Stage C.

DECISION STRUCTURE (shared by M1-M3)

  q_ms                subjective belief that a copy will match, on stimulus s
  dv_i = 10*q - S_i   subjective expected advantage of attempting, in points
  P(attempt) = logistic(alpha_m + beta_m * dv_i),  beta_m > 0 free (not fixed at 1)

The models differ only in where q comes from:

  M0  payoff only          logit P = a_m + bS_m * S            (no stimulus info)
  M1  public only          logit q = g0 + g_aud*logit(aud) + g_sal*z(sal)
  M2  true self-reliability logit q = g0 + g_true*logit(true)
  M3  public + policy-specific  M1 + lambda_m * policy_specific

  policy_specific = logit(true) - logit(aud)     (logit scale, primary)
                  = true - aud                   (raw scale, sensitivity)

Because M3's linear predictor is
  g0 + (g_aud - lambda)*logit(aud) + g_sal*z(sal) + lambda*logit(true),
lambda IS the coefficient on the model's own held-out reliability once the public
terms are in. That is the quantity of interest.

KNOWN IDENTIFIABILITY LIMITS - established BEFORE fitting, not after:

  * There are 10 unique (model, stimulus) cells: 6 GPT, 4 Claude. Every predictor
    is constant within a cell, so 1200 trials carry only 10 independent
    stimulus-level observations.
  * M3 maps stimulus -> q with 4 free parameters per model. For Claude that is
    4 parameters for 4 stimuli: EXACTLY SATURATED, zero residual df. lambda_claude
    is therefore not identified by the cell means; its posterior will be governed
    by the prior and by whatever the trial-level likelihood can add through the
    alpha/beta path. It is reported, but must not be read as evidence.
  * corr(logit(aud), salience) = +0.945 (GPT) / +0.963 (Claude). The two public
    predictors are near-collinear, so "auditor + salience" is close to a single
    public factor. An auditor-only variant is fitted as the honest primary public
    baseline.
  * policy_specific is close to orthogonal to logit(aud) (r = -0.01 / +0.02),
    which is the one favourable feature: where residual df exist (GPT), lambda is
    not confounded with the auditor term.

A pooled-lambda model (one lambda shared across models, partial pooling) is fitted
because it is the only specification with a comfortable df margin.

MEASUREMENT ERROR. In the -me variants, Stage A enters as counts with latent choice
probability p ~ Beta, pushed through match = p^2 + (1-p)^2; auditor and salience
enter as latent means with their sampling SEs. This also removes the arbitrary
clamp needed when an empirical self-match of exactly 1.000 is logit-transformed.
"""
import json, os
import numpy as np
import pymc as pm
import pytensor.tensor as pt

HERE = os.path.dirname(os.path.abspath(__file__))
EPS = 1e-3          # clamp for logit() in the point-estimate models; sensitivity-tested


def load():
    return json.load(open(os.path.join(HERE, "model_data.json")))


def logit_np(x, eps=EPS):
    x = np.clip(np.asarray(x, float), eps, 1 - eps)
    return np.log(x / (1 - x))


def arrays(d):
    tr = d["trials"]
    y = np.array([t["y"] for t in tr], dtype="int8")
    safe = np.array([t["safe"] for t in tr], dtype="float64")
    cell = np.array([t["cell"] for t in tr], dtype="int32")
    mix = np.array([t["model_ix"] for t in tr], dtype="int32")
    C = d["cells"]
    cm = np.array([c["model_ix"] for c in C], dtype="int32")
    k1 = np.array([c["k1"] for c in C], dtype="float64")
    nA = np.array([c["n_A"] for c in C], dtype="float64")
    aud = np.array([c["aud_mean"] for c in C])
    aud_se = np.array([max(c["aud_se"], 1e-3) for c in C])
    sal = np.array([c["sal_mean"] for c in C])
    sal_se = np.array([max(c["sal_se"], 1e-3) for c in C])
    true = np.array([c["true_point"] for c in C])
    # salience standardised across cells; documented in the summary output
    z_sal = (sal - sal.mean()) / sal.std(ddof=0)
    return dict(y=y, safe=safe, cell=cell, mix=mix, cm=cm, k1=k1, nA=nA,
                aud=aud, aud_se=aud_se, sal=sal, sal_se=sal_se, true=true,
                z_sal=z_sal, sal_mu=float(sal.mean()), sal_sd=float(sal.std(ddof=0)),
                nC=len(C), nM=len(d["models"]))


def _decision(alpha, beta, q, cell, safe, y, obs=True):
    dv = 10.0 * q[cell] - safe
    p = pm.math.sigmoid(alpha + beta * dv)
    return pm.Bernoulli("y", p=p, observed=y if obs else None)


def build(kind, d, raw_scale=False, stim_re=False, auditor_only=False,
          pooled_lambda=False, measurement_error=False, subset=None):
    """kind in {m0, m1, m2, m3, interp}."""
    a = arrays(d)
    if subset is not None:
        keep = np.isin(a["cell"], subset)
        for k in ("y", "safe", "cell", "mix"):
            a[k] = a[k][keep]
    y, safe, cell, mix = a["y"], a["safe"], a["cell"], a["mix"]
    cm, nM, nC = a["cm"], a["nM"], a["nC"]

    with pm.Model() as model:
        alpha = pm.Normal("alpha", 0.0, 1.5, shape=nM)
        beta = pm.LogNormal("beta", np.log(1.0), 0.75, shape=nM)

        if kind == "m0":
            bS = pm.Normal("bS", 0.0, 1.0, shape=nM)
            p = pm.math.sigmoid(alpha[mix] + bS[mix] * safe)
            pm.Bernoulli("y", p=p, observed=y)
            return model

        # ---- latent or fixed cell predictors ----
        if measurement_error:
            p_choice = pm.Beta("p_choice", 1.0 + a["k1"], 1.0 + (a["nA"] - a["k1"]),
                               shape=nC)
            true_l = pm.Deterministic("true_lat", p_choice ** 2 + (1 - p_choice) ** 2)
            aud_l = pm.TruncatedNormal("aud_lat", mu=a["aud"], sigma=a["aud_se"],
                                       lower=1e-3, upper=1 - 1e-3, shape=nC)
            sal_l = pm.TruncatedNormal("sal_lat", mu=a["sal"], sigma=a["sal_se"],
                                       lower=1e-3, upper=1 - 1e-3, shape=nC)
            lg = lambda v: pt.log(pt.clip(v, EPS, 1 - EPS) / (1 - pt.clip(v, EPS, 1 - EPS)))
            L_aud, L_true = lg(aud_l), lg(true_l)
            Z_sal = (sal_l - a["sal_mu"]) / a["sal_sd"]
            polspec = (true_l - aud_l) if raw_scale else (L_true - L_aud)
        else:
            L_aud = logit_np(a["aud"]); L_true = logit_np(a["true"])
            Z_sal = a["z_sal"]
            polspec = (a["true"] - a["aud"]) if raw_scale else (L_true - L_aud)

        g0 = pm.Normal("g0", 0.0, 1.0, shape=nM)
        lin = g0[cm]

        if kind in ("m1", "m3"):
            g_aud = pm.Normal("g_aud", 0.0, 1.0, shape=nM)
            lin = lin + g_aud[cm] * L_aud
            if not auditor_only:
                g_sal = pm.Normal("g_sal", 0.0, 1.0, shape=nM)
                lin = lin + g_sal[cm] * Z_sal
        if kind == "m2":
            g_true = pm.Normal("g_true", 0.0, 1.0, shape=nM)
            lin = lin + g_true[cm] * L_true
        if kind == "m3":
            if pooled_lambda:
                lam_mu = pm.Normal("lambda_mu", 0.0, 1.0)
                lam_sd = pm.HalfNormal("lambda_sd", 0.5)
                lam_z = pm.Normal("lambda_z", 0.0, 1.0, shape=nM)
                lam = pm.Deterministic("lambda", lam_mu + lam_sd * lam_z)
            else:
                lam = pm.Normal("lambda", 0.0, 1.0, shape=nM)
            lin = lin + lam[cm] * polspec

        if kind == "interp":
            # constrained interpolation: q sits between auditor and true
            lam = pm.Beta("lambda_interp", 1.5, 1.5, shape=nM)
            delta = pm.Normal("delta", 0.0, 1.0, shape=nM)
            lin = (1 - lam[cm]) * L_aud + lam[cm] * L_true + delta[cm]

        if stim_re:
            sig = pm.HalfNormal("sigma_stim", 0.5)
            u = pm.Normal("u_stim", 0.0, 1.0, shape=nC)
            lin = lin + sig * u

        q = pm.Deterministic("q", pm.math.sigmoid(lin))
        _decision(alpha[mix], beta[mix], q, cell, safe, y)
    return model
