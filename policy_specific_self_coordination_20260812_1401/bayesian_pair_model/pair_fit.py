"""
Fit and report the pair-constrained Bayesian analysis.

Secondary analysis. No API calls, no design changes, and the pre-specified
frequentist matched-pair test remains the primary evidence.

Run:  ../bayesian_policy_self_knowledge/.venv/bin/python pair_fit.py
"""
import json, os, warnings
import numpy as np
import pymc as pm
import arviz as az
import pair_models as PM

warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__))
DRAWS, TUNE, CHAINS, SEED = 2000, 2000, 4, 20260812
LBL = ["GPT-5.5", "Claude Opus 5"]
LOG = []


def say(*a):
    s = " ".join(str(x) for x in a); print(s, flush=True); LOG.append(s)


def fit(model, draws=DRAWS, tune=TUNE, ll=True):
    with model:
        return pm.sample(draws=draws, tune=tune, chains=CHAINS, cores=4,
                         random_seed=SEED, target_accept=0.95, progressbar=False,
                         compute_convergence_checks=False,
                         idata_kwargs={"log_likelihood": ll})


def diag(idata, name, params):
    ps = [p for p in params if p in idata.posterior]
    s = az.summary(idata, var_names=ps, round_to=4)
    div = int(idata.sample_stats["diverging"].sum())
    rhat = float(np.nanmax(s["r_hat"])); ess = float(np.nanmin(s["ess_bulk"]))
    ok = div == 0 and rhat < 1.01 and ess > 400
    say(f"  [{name:26}] div={div:3}  max R-hat={rhat:.4f}  min ESS={ess:6.0f}"
        f"   {'OK' if ok else '<-- NOT CLEAN'}")
    return dict(model=name, divergences=div, max_rhat=rhat, min_ess=ess, clean=bool(ok))


def q(v, p):
    return float(np.quantile(v, p))


def main():
    d = PM.load()
    a = PM.arrays(d)
    say("=" * 78); say("PAIR-CONSTRAINED BAYESIAN ANALYSIS  (secondary)"); say("=" * 78)
    say(f"  Stage C trials {len(a['y'])}   approved pairs {a['nP']}   cells {a['nC']}")
    say(f"  pairs per model: GPT {int((a['pair_model']==0).sum())}, "
        f"Claude {int((a['pair_model']==1).sum())}")
    say(f"  auditor standardised z=(x-{a['aud_mu']:.4f})/{a['aud_sd']:.4f};"
        f"  salience z=(x-{a['sal_mu']:.4f})/{a['sal_sd']:.4f}")
    ca = np.corrcoef(a["z_aud"], a["z_sal"])[0, 1]
    say(f"  corr(auditor, salience) across cells = {ca:+.3f}"
        f"  -> {'NOT separately interpretable' if abs(ca) > 0.9 else 'separable'}")

    # -------- prior predictive --------
    say("\nPRIOR PREDICTIVE")
    for k, nm in (("b2", "B2 pair-constrained"), ("b1", "B1 payoff+is_high")):
        with PM.build(k, d):
            pp = pm.sample_prior_predictive(draws=400, random_seed=SEED)
        r = pp.prior_predictive["y"].values.reshape(400, -1).mean(axis=1)
        say(f"  {nm:22} prior attempt rate median {np.median(r):.2f}"
            f"  90% [{q(r,.05):.2f}, {q(r,.95):.2f}]   observed {a['y'].mean():.3f}")
    # prior for the two headline parameters, for the prior-vs-posterior check
    with PM.build("b2", d):
        pri2 = pm.sample_prior_predictive(draws=4000, random_seed=SEED,
                                          var_names=["mu_delta"])
    prior_mu = pri2.prior["mu_delta"].values.ravel()
    with PM.build("b1", d):
        pri1 = pm.sample_prior_predictive(draws=4000, random_seed=SEED,
                                          var_names=["delta"])
    prior_dl = pri1.prior["delta"].values.ravel()

    # -------- fit --------
    say("\nFITTING")
    specs = [("B0 payoff-only", dict(kind="b0"), ["alpha", "bS"]),
             ("B1 payoff+is_high", dict(kind="b1"), ["alpha", "bS", "delta"]),
             ("B2 pair-constrained q", dict(kind="b2"),
              ["alpha", "beta", "mu_mid", "sigma_mid", "mu_delta", "sigma_delta"]),
             ("B3 +auditor", dict(kind="b3"), ["alpha", "bS", "delta", "gamma_aud"]),
             ("B3b +auditor+salience", dict(kind="b3b"),
              ["alpha", "bS", "delta", "gamma_aud", "gamma_sal"])]
    idatas, diags = {}, []
    for nm, kw, ps in specs:
        idatas[nm] = fit(PM.build(d=d, **kw)); diags.append(diag(idatas[nm], nm, ps))

    # -------- primary quantities --------
    say("\nPRIMARY: B2 pair-constrained latent q")
    p2 = idatas["B2 pair-constrained q"].posterior
    mu = p2["mu_delta"].values.ravel()
    say(f"  mu_delta (logit scale)  median {np.median(mu):+.3f}"
        f"  90% [{q(mu,.05):+.3f}, {q(mu,.95):+.3f}]"
        f"  95% [{q(mu,.025):+.3f}, {q(mu,.975):+.3f}]   P(>0) = {(mu>0).mean():.4f}")
    sd = p2["sigma_delta"].values.ravel()
    say(f"  sigma_delta             median {np.median(sd):+.3f}"
        f"  90% [{q(sd,.05):+.3f}, {q(sd,.95):+.3f}]   (5 pairs - weakly identified)")
    # prior vs posterior overlap
    say(f"  prior-vs-posterior: prior mu_delta 90% [{q(prior_mu,.05):+.2f},"
        f" {q(prior_mu,.95):+.2f}] -> posterior 90% [{q(mu,.05):+.2f}, {q(mu,.95):+.2f}]"
        f"   width ratio {(q(mu,.95)-q(mu,.05))/(q(prior_mu,.95)-q(prior_mu,.05)):.2f}")

    qh = p2["q_high"].values.reshape(-1, a["nP"])
    ql = p2["q_low"].values.reshape(-1, a["nP"])
    dq = p2["delta_q"].values.reshape(-1, a["nP"])
    say("\n  per-pair posteriors (probability scale):")
    pair_rows = []
    for i, pr in enumerate(d["pairs"]):
        P = float((dq[:, i] > 0).mean())
        say(f"    Pair {i+1}  {pr['model']:7}{pr['hi']:15}vs {pr['lo']:16}"
            f" q_hi {np.median(qh[:,i]):.3f} [{q(qh[:,i],.05):.3f},{q(qh[:,i],.95):.3f}]"
            f"  q_lo {np.median(ql[:,i]):.3f} [{q(ql[:,i],.05):.3f},{q(ql[:,i],.95):.3f}]"
            f"  d_q {np.median(dq[:,i]):+.3f}  P(q_hi>q_lo)={P:.3f}")
        pair_rows.append(dict(pair=f"Pair {i+1}", pair_id=pr["pair_id"], model=pr["model"],
                              stimulus_high=pr["hi"], stimulus_low=pr["lo"],
                              q_high_median=float(np.median(qh[:, i])),
                              q_high_q05=q(qh[:, i], .05), q_high_q95=q(qh[:, i], .95),
                              q_low_median=float(np.median(ql[:, i])),
                              q_low_q05=q(ql[:, i], .05), q_low_q95=q(ql[:, i], .95),
                              delta_q_median=float(np.median(dq[:, i])),
                              delta_q_q05=q(dq[:, i], .05), delta_q_q95=q(dq[:, i], .95),
                              p_q_high_gt_low=P))

    say("\nSECONDARY: B1 direct effect of higher own-copy reliability")
    dl = idatas["B1 payoff+is_high"].posterior["delta"].values.ravel()
    say(f"  delta (log-odds)        median {np.median(dl):+.3f}"
        f"  90% [{q(dl,.05):+.3f}, {q(dl,.95):+.3f}]"
        f"  95% [{q(dl,.025):+.3f}, {q(dl,.975):+.3f}]   P(>0) = {(dl>0).mean():.4f}")
    say(f"                          odds ratio median {np.exp(np.median(dl)):.2f}")
    say(f"  prior-vs-posterior: prior 90% [{q(prior_dl,.05):+.2f}, {q(prior_dl,.95):+.2f}]"
        f" -> posterior 90% [{q(dl,.05):+.2f}, {q(dl,.95):+.2f}]"
        f"   width ratio {(q(dl,.95)-q(dl,.05))/(q(prior_dl,.95)-q(prior_dl,.05)):.2f}")

    say("\nROBUSTNESS: does delta survive public controls?")
    rows = [dict(model="B1 payoff+is_high", param="delta", median=float(np.median(dl)),
                 q05=q(dl, .05), q95=q(dl, .95), q025=q(dl, .025), q975=q(dl, .975),
                 p_gt0=float((dl > 0).mean()))]
    for nm in ("B3 +auditor", "B3b +auditor+salience"):
        v = idatas[nm].posterior["delta"].values.ravel()
        say(f"  {nm:24} delta median {np.median(v):+.3f}"
            f"  90% [{q(v,.05):+.3f}, {q(v,.95):+.3f}]   P(>0) = {(v>0).mean():.4f}")
        rows.append(dict(model=nm, param="delta", median=float(np.median(v)),
                         q05=q(v, .05), q95=q(v, .95), q025=q(v, .025), q975=q(v, .975),
                         p_gt0=float((v > 0).mean())))
    say("  (auditor and salience are collinear at r=%.2f; their individual"
        " coefficients are not interpreted)" % ca)

    # -------- exploratory by-model + no-alpha diagnostic --------
    say("\nEXPLORATORY / DIAGNOSTIC (not confirmatory)")
    try:
        ide = fit(PM.build("b2", d, by_model=True), draws=1500, tune=2000, ll=False)
        dg = diag(ide, "B2 by-model mu_delta", ["mu_delta_by_model"]); diags.append(dg)
        mm = ide.posterior["mu_delta_by_model"].values
        for mi, lb in enumerate(LBL):
            v = mm[..., mi].ravel()
            say(f"    mu_delta[{lb:14}] median {np.median(v):+.3f}"
                f"  90% [{q(v,.05):+.3f}, {q(v,.95):+.3f}]  P(>0)={(v>0).mean():.3f}"
                f"   ({int((a['pair_model']==mi).sum())} pairs - weakly identified)")
            rows.append(dict(model=f"B2 exploratory {lb}", param="mu_delta",
                             median=float(np.median(v)), q05=q(v, .05), q95=q(v, .95),
                             q025=q(v, .025), q975=q(v, .975), p_gt0=float((v > 0).mean())))
    except Exception as e:
        say(f"    by-model model FAILED: {type(e).__name__}: {e}")
    try:
        idn = fit(PM.build("b2", d, no_alpha=True), draws=1500, tune=2000, ll=False)
        dg = diag(idn, "B2 no-alpha (ridge check)", ["mu_delta"]); diags.append(dg)
        v = idn.posterior["mu_delta"].values.ravel()
        say(f"    alpha fixed at 0: mu_delta median {np.median(v):+.3f}"
            f"  90% [{q(v,.05):+.3f}, {q(v,.95):+.3f}]  P(>0)={(v>0).mean():.3f}")
        say("      -> compare with the primary mu_delta above; a similar value confirms")
        say("         the alpha/mu_mid ridge does not contaminate the pair contrast")
        rows.append(dict(model="B2 no-alpha diagnostic", param="mu_delta",
                         median=float(np.median(v)), q05=q(v, .05), q95=q(v, .95),
                         q025=q(v, .025), q975=q(v, .975), p_gt0=float((v > 0).mean())))
    except Exception as e:
        say(f"    no-alpha model FAILED: {type(e).__name__}: {e}")

    # -------- comparison --------
    say("\nMODEL COMPARISON - trial-level PSIS-LOO")
    try:
        cmp = az.compare({k: idatas[k] for k in
                          ("B0 payoff-only", "B1 payoff+is_high",
                           "B2 pair-constrained q", "B3 +auditor")})
        say(cmp.to_string())
    except Exception as e:
        say(f"  unavailable: {type(e).__name__}: {e}")

    say("\nMODEL COMPARISON - leave-one-pair-out (5 folds; VERY low power)")
    grouped = {}
    for nm, kw, _ in specs[:4]:
        lp = []
        for held in range(a["nP"]):
            keep = [p for p in range(a["nP"]) if p != held]
            idl = fit(PM.build(d=d, keep_pairs=keep, **kw), draws=1000, tune=1500, ll=False)
            lp.append(score(idl, d, held, kw))
        grouped[nm] = lp
        say(f"  {nm:24} ELPD {np.sum(lp):9.2f}   per-pair " +
            " ".join(f"{x:7.1f}" for x in lp))
    base = "B0 payoff-only"
    say(f"\n  differences vs {base} (positive favours the other model):")
    for nm in grouped:
        if nm == base:
            continue
        df = np.array(grouped[nm]) - np.array(grouped[base])
        se = df.std(ddof=1) * np.sqrt(len(df))
        say(f"    {nm:24} dELPD {df.sum():+8.2f}   SE {se:7.2f}"
            f"   {'indistinguishable' if abs(df.sum()) < 2*se else 'separated'}")
    say("  With 5 folds these SEs are large by construction; treat the ranking as")
    say("  uninformative unless a difference clearly exceeds twice its SE.")

    # -------- posterior predictive --------
    say("\nPOSTERIOR PREDICTIVE (B2)")
    with PM.build("b2", d):
        ppc = pm.sample_posterior_predictive(idatas["B2 pair-constrained q"],
                                             random_seed=SEED, progressbar=False)
    yrep = ppc.posterior_predictive["y"].values.reshape(-1, len(a["y"]))
    inside = 0
    for c in range(a["nC"]):
        m = a["cell"] == c
        lo, hi = np.quantile(yrep[:, m].mean(axis=1), [.025, .975])
        inside += int(lo <= a["y"][m].mean() <= hi)
    say(f"  observed cell attempt rate inside 95% predictive: {inside}/{a['nC']} cells")

    np.save(os.path.join(HERE, "ppc_b2.npy"), yrep)
    np.save(os.path.join(HERE, "q_high.npy"), qh); np.save(os.path.join(HERE, "q_low.npy"), ql)
    np.save(os.path.join(HERE, "mu_delta.npy"), mu)
    np.save(os.path.join(HERE, "delta_b1.npy"), dl)
    np.save(os.path.join(HERE, "prior_mu_delta.npy"), prior_mu)
    np.save(os.path.join(HERE, "prior_delta.npy"), prior_dl)

    import csv
    def w(fn, rws):
        if not rws: return
        f = list(rws[0])
        for r in rws:
            for k in r:
                if k not in f: f.append(k)
        with open(os.path.join(HERE, fn), "w", newline="") as fh:
            wr = csv.DictWriter(fh, fieldnames=f, restval=""); wr.writeheader(); wr.writerows(rws)
        say(f"  -> {fn}")
    say("\nOUTPUTS")
    w("pair_model_summary.csv", rows)
    w("pair_posteriors.csv", pair_rows)
    w("pair_model_comparison.csv",
      [dict(model=k, grouped_elpd=float(np.sum(v)),
            per_pair=";".join(f"{x:.2f}" for x in v)) for k, v in grouped.items()])
    w("pair_diagnostics.csv", diags)
    open(os.path.join(HERE, "pair_diagnostics.txt"), "w").write("\n".join(LOG))
    say("  -> pair_diagnostics.txt")


def score(idata, d, held_pair, kw):
    a = PM.arrays(d)
    m = a["pair"] == held_pair
    y, safe, mix, high, cell = (a["y"][m], a["safe"][m], a["mix"][m],
                                a["high"][m], a["cell"][m])
    po = idata.posterior
    S = po.sizes["chain"] * po.sizes["draw"]
    al = po["alpha"].values.reshape(S, -1)
    if kw["kind"] == "b2":
        # held-out pair has no data: draw its q from the fitted population prior
        mu = po["mu_mid"].values.reshape(S); sm = po["sigma_mid"].values.reshape(S)
        md = po["mu_delta"].values.reshape(S); sd = po["sigma_delta"].values.reshape(S)
        rng = np.random.default_rng(SEED + held_pair)
        mid = mu + sm * rng.standard_normal(S)
        dlt = md + sd * rng.standard_normal(S)
        qh = 1 / (1 + np.exp(-(mid + dlt / 2))); ql = 1 / (1 + np.exp(-(mid - dlt / 2)))
        be = po["beta"].values.reshape(S, -1)
        qc = np.where(high[None, :] == 1, qh[:, None], ql[:, None])
        eta = al[:, mix] + be[:, mix] * (10.0 * qc - safe[None, :])
    else:
        bS = po["bS"].values.reshape(S, -1)
        eta = al[:, mix] + bS[:, mix] * safe[None, :]
        if kw["kind"] in ("b1", "b3", "b3b"):
            eta = eta + po["delta"].values.reshape(S, 1) * high[None, :]
        if kw["kind"] in ("b3", "b3b"):
            eta = eta + po["gamma_aud"].values.reshape(S, 1) * a["z_aud"][cell][None, :]
        if kw["kind"] == "b3b":
            eta = eta + po["gamma_sal"].values.reshape(S, 1) * a["z_sal"][cell][None, :]
    p = 1 / (1 + np.exp(-np.clip(eta, -30, 30)))
    ll = y[None, :] * np.log(p + 1e-12) + (1 - y[None, :]) * np.log(1 - p + 1e-12)
    mx = ll.max(axis=0)
    return float((mx + np.log(np.exp(ll - mx).mean(axis=0))).sum())


if __name__ == "__main__":
    main()
