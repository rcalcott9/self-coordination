"""
Fit, diagnose and compare the Stage C decision models.

Workflow, in order: prior predictive -> M0, M1 -> diagnostics -> M2, M3 ->
trial-level PSIS-LOO -> leave-one-PAIR-out grouped CV -> posterior predictive ->
sensitivity suite -> outputs.

Grouped (leave-one-pair-out) predictive comparison carries the interpretive weight.
Trial-level LOO is reported but overstates evidence here: 240 trials share each
pair's stimulus-level predictors, so dropping one trial leaves the predictor
essentially estimable from its 239 neighbours.

Run with the local venv:  ./.venv/bin/python bayes_fit.py
"""
import json, os, sys, warnings
import numpy as np
import pymc as pm
import arviz as az

import bayes_models as BM

warnings.filterwarnings("ignore", category=FutureWarning)
HERE = os.path.dirname(os.path.abspath(__file__))
DRAWS, TUNE, CHAINS = 2000, 2000, 4
SEED = 20260812
LOG = []


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    LOG.append(s)


def fit(model, draws=DRAWS, tune=TUNE, seed=SEED, idata_kwargs=None):
    with model:
        idata = pm.sample(draws=draws, tune=tune, chains=CHAINS, cores=4,
                          random_seed=seed, target_accept=0.95,
                          progressbar=False, compute_convergence_checks=False,
                          idata_kwargs=idata_kwargs or {"log_likelihood": True})
    return idata


def diag(idata, name, params):
    """Return a diagnostics dict and log a one-line summary."""
    s = az.summary(idata, var_names=[p for p in params if p in idata.posterior],
                   round_to=4)
    div = int(idata.sample_stats["diverging"].sum())
    rhat = float(np.nanmax(s["r_hat"])) if len(s) else float("nan")
    ess = float(np.nanmin(s["ess_bulk"])) if len(s) else float("nan")
    tree = idata.sample_stats.get("tree_depth")
    maxtree = int(tree.max()) if tree is not None else -1
    try:                                   # arviz 1.x may return a DataTree
        eb = az.bfmi(idata)
        eb = np.asarray(getattr(eb, "values", eb), dtype=float)
        ebfmi = float(np.nanmin(eb))
    except Exception:
        ebfmi = float("nan")
    say(f"  [{name}] divergences={div}  max R-hat={rhat:.4f}  min ESS_bulk={ess:.0f}"
        f"  max treedepth={maxtree}  min E-BFMI={ebfmi:.2f}")
    ok = (div == 0) and (rhat < 1.01) and (ess > 400)
    if not ok:
        say(f"      !! diagnostics NOT clean for {name}")
    return dict(name=name, divergences=div, max_rhat=rhat, min_ess=ess,
                max_treedepth=maxtree, min_ebfmi=ebfmi, clean=bool(ok)), s


def main():
    d = BM.load()
    a = BM.arrays(d)
    models_lbl = [{"gpt": "GPT-5.5", "claude": "Claude Opus 5"}[m] for m in d["models"]]
    say("=" * 78)
    say("BAYESIAN DECISION MODEL - Stage C")
    say("=" * 78)
    say(f"  trials={len(d['trials'])}  cells={len(d['cells'])}  pairs={len(d['pairs'])}"
        f"  models={d['models']}")
    say(f"  salience standardised: z = (sal - {a['sal_mu']:.4f}) / {a['sal_sd']:.4f}")
    say(f"  logit clamp EPS = {BM.EPS}")

    say("\nPREDICTOR CORRELATIONS (cell level, held-out)")
    for mi, m in enumerate(d["models"]):
        ix = np.where(a["cm"] == mi)[0]
        L = BM.logit_np(a["aud"][ix]); Z = a["z_sal"][ix]
        PS = BM.logit_np(a["true"][ix]) - L
        C = np.corrcoef(np.vstack([L, Z, PS]))
        say(f"  {models_lbl[mi]:14} n_stim={len(ix)}  "
            f"r(aud,sal)={C[0,1]:+.3f}  r(aud,polspec)={C[0,2]:+.3f}  "
            f"r(sal,polspec)={C[1,2]:+.3f}")
        say(f"                 M3 uses 4 params for {len(ix)} stimuli -> "
            f"{'SATURATED, lambda NOT identified' if len(ix) <= 4 else f'{len(ix)-4} residual df'}")

    # ---------------- prior predictive ----------------
    say("\nPRIOR PREDICTIVE CHECK (M3)")
    with BM.build("m3", d):
        pp = pm.sample_prior_predictive(draws=500, random_seed=SEED)
    ypp = pp.prior_predictive["y"].values.reshape(500, -1).mean(axis=1)
    say(f"  prior attempt rate: median {np.median(ypp):.2f}, "
        f"90% interval [{np.quantile(ypp,0.05):.2f}, {np.quantile(ypp,0.95):.2f}]")
    say(f"  observed attempt rate: {a['y'].mean():.3f}  -> "
        f"{'inside' if np.quantile(ypp,0.05) <= a['y'].mean() <= np.quantile(ypp,0.95) else 'OUTSIDE'}"
        " the prior 90% interval (priors are weakly informative, not tight)")

    # ---------------- fit the four models ----------------
    specs = [("M0 payoff-only", dict(kind="m0"), ["alpha", "beta", "bS"]),
             ("M1 public-only", dict(kind="m1"), ["alpha", "beta", "g0", "g_aud", "g_sal"]),
             ("M2 true-self-reliability", dict(kind="m2"), ["alpha", "beta", "g0", "g_true"]),
             ("M3 public+policy-specific", dict(kind="m3"),
              ["alpha", "beta", "g0", "g_aud", "g_sal", "lambda"])]
    say("\nFITTING")
    idatas, diags, summaries = {}, [], {}
    for name, kw, params in specs:
        idata = fit(BM.build(d=d, **kw))
        dg, s = diag(idata, name, params)
        idatas[name] = idata; diags.append(dg); summaries[name] = s

    # ---------------- trial-level LOO ----------------
    say("\nTRIAL-LEVEL PSIS-LOO  (overstates evidence here - see grouped CV below)")
    try:
        cmp = az.compare({k: v for k, v in idatas.items()})
        say(cmp.to_string())
        cmp_d = cmp.to_dict()
    except Exception as e:
        say(f"  trial-level LOO unavailable ({type(e).__name__}: {e})")
        cmp_d = {}

    # ---------------- grouped leave-one-pair-out ----------------
    say("\nLEAVE-ONE-PAIR-OUT PREDICTIVE COMPARISON  (the interpretive one)")
    say("  each fold refits without one approved pair's 240 trials and scores them")
    pairs = d["pairs"]
    trials = d["trials"]
    y_all = np.array([t["y"] for t in trials])
    cell_all = np.array([t["cell"] for t in trials])
    grouped = {}
    for name, kw, _ in specs:
        fold_lpd = []
        for pr in pairs:
            heldout_cells = [pr["hi_ix"], pr["lo_ix"]]
            train = np.array([c for c in range(len(d["cells"])) if c not in heldout_cells])
            m = BM.build(d=d, subset=train, **kw)
            idl = fit(m, draws=1000, tune=1500, idata_kwargs={"log_likelihood": False})
            # score the held-out trials under the posterior
            mask = np.isin(cell_all, heldout_cells)
            lp = score_heldout(idl, d, np.where(mask)[0], kw)
            fold_lpd.append(lp)
        grouped[name] = fold_lpd
        say(f"  {name:28} sum ELPD = {np.sum(fold_lpd):9.2f}   per-pair: "
            + " ".join(f"{x:7.1f}" for x in fold_lpd))

    base = "M1 public-only"
    say(f"\n  pairwise differences vs {base} (positive favours the other model):")
    for name in grouped:
        if name == base:
            continue
        diffs = np.array(grouped[name]) - np.array(grouped[base])
        se = diffs.std(ddof=1) / np.sqrt(len(diffs)) * len(diffs)
        say(f"    {name:28} dELPD = {diffs.sum():+8.2f}  SE(pair-level) = {se:6.2f}")

    json.dump({"trial_loo": cmp_d, "grouped": grouped},
              open(os.path.join(HERE, "comparison_raw.json"), "w"), indent=1, default=str)

    # ---------------- key posteriors ----------------
    say("\nKEY POSTERIORS - M3")
    post = idatas["M3 public+policy-specific"].posterior
    rows = []
    for mi, lbl in enumerate(models_lbl):
        lam = post["lambda"].values[..., mi].ravel()
        bet = post["beta"].values[..., mi].ravel()
        say(f"  {lbl:14} lambda median {np.median(lam):+.3f}  "
            f"90% [{np.quantile(lam,0.05):+.3f}, {np.quantile(lam,0.95):+.3f}]  "
            f"95% [{np.quantile(lam,0.025):+.3f}, {np.quantile(lam,0.975):+.3f}]  "
            f"P(lambda>0) = {(lam>0).mean():.3f}")
        say(f"                 beta   median {np.median(bet):+.3f}  "
            f"90% [{np.quantile(bet,0.05):+.3f}, {np.quantile(bet,0.95):+.3f}]")
        rows.append(dict(model=lbl, param="lambda", median=float(np.median(lam)),
                         q05=float(np.quantile(lam, .05)), q95=float(np.quantile(lam, .95)),
                         q025=float(np.quantile(lam, .025)), q975=float(np.quantile(lam, .975)),
                         p_gt0=float((lam > 0).mean())))
        rows.append(dict(model=lbl, param="beta", median=float(np.median(bet)),
                         q05=float(np.quantile(bet, .05)), q95=float(np.quantile(bet, .95)),
                         q025=float(np.quantile(bet, .025)), q975=float(np.quantile(bet, .975)),
                         p_gt0=float((bet > 0).mean())))

    # per-pair P(q_high > q_low)
    say("\n  P(q_high > q_low | data), M3:")
    qq = post["q"].values.reshape(-1, len(d["cells"]))
    pair_rows = []
    for i, pr in enumerate(pairs, start=1):
        ph = float((qq[:, pr["hi_ix"]] > qq[:, pr["lo_ix"]]).mean())
        say(f"    Pair {i}  {pr['model']:7}{pr['hi']:15}vs {pr['lo']:16} "
            f"P = {ph:.3f}   q_hi={np.median(qq[:,pr['hi_ix']]):.3f} "
            f"q_lo={np.median(qq[:,pr['lo_ix']]):.3f}")
        pair_rows.append(dict(pair=f"Pair {i}", pair_id=pr["pair_id"], model=pr["model"],
                              stimulus_high=pr["hi"], stimulus_low=pr["lo"],
                              both_form=pr["both_form"],
                              p_q_high_gt_low=ph,
                              q_high_median=float(np.median(qq[:, pr["hi_ix"]])),
                              q_low_median=float(np.median(qq[:, pr["lo_ix"]])),
                              q_high_q05=float(np.quantile(qq[:, pr["hi_ix"]], .05)),
                              q_high_q95=float(np.quantile(qq[:, pr["hi_ix"]], .95)),
                              q_low_q05=float(np.quantile(qq[:, pr["lo_ix"]], .05)),
                              q_low_q95=float(np.quantile(qq[:, pr["lo_ix"]], .95))))

    # per-cell q vs auditor vs true
    cell_rows = []
    for ci, c in enumerate(d["cells"]):
        qs = qq[:, ci]
        cell_rows.append(dict(model=c["model"], stimulus=c["stimulus"],
                              q_median=float(np.median(qs)),
                              q_q05=float(np.quantile(qs, .05)),
                              q_q95=float(np.quantile(qs, .95)),
                              auditor=c["aud_mean"], true_heldout=c["true_point"],
                              salience=c["sal_mean"],
                              q_minus_auditor=float(np.median(qs) - c["aud_mean"]),
                              q_minus_true=float(np.median(qs) - c["true_point"])))

    np.save(os.path.join(HERE, "q_posterior.npy"), qq)
    for vn in ("alpha", "beta", "g0", "g_aud", "g_sal"):
        if vn in post:
            np.save(os.path.join(HERE, f"{vn}_posterior.npy"),
                    post[vn].values.reshape(-1, post[vn].shape[-1]))
    np.save(os.path.join(HERE, "lambda_posterior.npy"),
            post["lambda"].values.reshape(-1, len(d["models"])))
    for nm, fn in (("M3 public+policy-specific", "idata_m3.nc"),
                   ("M1 public-only", "idata_m1.nc")):
        try:
            idatas[nm].to_netcdf(os.path.join(HERE, fn))
        except Exception as e:      # netCDF backend optional; posteriors already in .npy
            say(f"  (idata not saved for {nm}: {type(e).__name__})")

    # ---------------- posterior predictive ----------------
    say("\nPOSTERIOR PREDICTIVE CHECK (M3)")
    with BM.build("m3", d) as m:
        ppc = pm.sample_posterior_predictive(idatas["M3 public+policy-specific"],
                                             random_seed=SEED, progressbar=False)
    yrep = ppc.posterior_predictive["y"].values.reshape(-1, len(y_all))
    obs_cell = {}
    for ci in range(len(d["cells"])):
        mask = cell_all == ci
        obs_cell[ci] = (y_all[mask].mean(), yrep[:, mask].mean(axis=1))
    bad = 0
    for ci, (o, rep) in obs_cell.items():
        lo, hi = np.quantile(rep, [0.025, 0.975])
        if not (lo <= o <= hi):
            bad += 1
    say(f"  observed cell attempt rate inside 95% posterior predictive: "
        f"{len(obs_cell)-bad}/{len(obs_cell)} cells")
    np.save(os.path.join(HERE, "ppc_m3.npy"), yrep)

    # ---------------- sensitivity ----------------
    say("\nSENSITIVITY (lambda median [90% CI], P>0)")
    sens = [("primary: logit polspec, aud+sal", dict(kind="m3")),
            ("raw-probability polspec", dict(kind="m3", raw_scale=True)),
            ("auditor only (no salience)", dict(kind="m3", auditor_only=True)),
            ("+ stimulus random intercept", dict(kind="m3", stim_re=True)),
            ("pooled lambda (partial pooling)", dict(kind="m3", pooled_lambda=True)),
            ("measurement-error version", dict(kind="m3", measurement_error=True))]
    sens_rows = []
    for lbl, kw in sens:
        try:
            idl = fit(BM.build(d=d, **kw), draws=1500, tune=2000,
                      idata_kwargs={"log_likelihood": False})
            lam = idl.posterior["lambda"].values
            dv = int(idl.sample_stats["diverging"].sum())
            line = f"  {lbl:34}"
            for mi, ml in enumerate(models_lbl):
                v = lam[..., mi].ravel()
                line += (f" | {ml.split()[0]:6} {np.median(v):+.2f} "
                         f"[{np.quantile(v,.05):+.2f},{np.quantile(v,.95):+.2f}] "
                         f"P={np.mean(v>0):.2f}")
                sens_rows.append(dict(spec=lbl, model=ml, median=float(np.median(v)),
                                      q05=float(np.quantile(v, .05)),
                                      q95=float(np.quantile(v, .95)),
                                      p_gt0=float(np.mean(v > 0)), divergences=dv))
            say(line + f"  div={dv}")
        except Exception as e:
            say(f"  {lbl:34} FAILED: {type(e).__name__}: {e}")

    # excluding pairs
    for lbl, drop in (("excluding the both-form-based pair", 0),
                      ("excluding the Stage C null pair (GPT c_open_cplx/s_density)", 2)):
        pr = pairs[drop]
        keep = np.array([c for c in range(len(d["cells"]))
                         if c not in (pr["hi_ix"], pr["lo_ix"])])
        try:
            idl = fit(BM.build("m3", d, subset=keep), draws=1500, tune=2000,
                      idata_kwargs={"log_likelihood": False})
            lam = idl.posterior["lambda"].values
            line = f"  {lbl:34}"
            for mi, ml in enumerate(models_lbl):
                v = lam[..., mi].ravel()
                line += (f" | {ml.split()[0]:6} {np.median(v):+.2f} "
                         f"[{np.quantile(v,.05):+.2f},{np.quantile(v,.95):+.2f}] "
                         f"P={np.mean(v>0):.2f}")
                sens_rows.append(dict(spec=lbl, model=ml, median=float(np.median(v)),
                                      q05=float(np.quantile(v, .05)),
                                      q95=float(np.quantile(v, .95)),
                                      p_gt0=float(np.mean(v > 0)), divergences=-1))
            say(line)
        except Exception as e:
            say(f"  {lbl:34} FAILED: {type(e).__name__}: {e}")

    # constrained interpolation model
    say("\nCONSTRAINED INTERPOLATION MODEL (lambda in [0,1]) - secondary")
    try:
        idl = fit(BM.build("interp", d), draws=1500, tune=2000,
                  idata_kwargs={"log_likelihood": False})
        dg, _ = diag(idl, "interp", ["alpha", "beta", "lambda_interp", "delta"])
        li = idl.posterior["lambda_interp"].values
        for mi, ml in enumerate(models_lbl):
            v = li[..., mi].ravel()
            say(f"  {ml:14} lambda_interp median {np.median(v):.3f} "
                f"90% [{np.quantile(v,.05):.3f}, {np.quantile(v,.95):.3f}]  "
                f"(0 = follows auditor, 1 = follows true self-match)")
            sens_rows.append(dict(spec="constrained interpolation", model=ml,
                                  median=float(np.median(v)),
                                  q05=float(np.quantile(v, .05)),
                                  q95=float(np.quantile(v, .95)),
                                  p_gt0=float(np.mean(v > 0)),
                                  divergences=dg["divergences"]))
        diags.append(dg)
    except Exception as e:
        say(f"  interpolation model FAILED: {type(e).__name__}: {e}")

    # ---------------- write outputs ----------------
    import csv as _csv

    def w(path, rws):
        if not rws:
            return
        fields = list(rws[0])
        for r in rws:
            for k in r:
                if k not in fields:
                    fields.append(k)
        with open(path, "w", newline="") as fh:
            wr = _csv.DictWriter(fh, fieldnames=fields, restval="")
            wr.writeheader(); wr.writerows(rws)
        say(f"  -> {os.path.basename(path)}")

    say("\nOUTPUTS")
    w(os.path.join(HERE, "bayes_model_summary.csv"), rows + cell_rows + sens_rows)
    w(os.path.join(HERE, "bayes_pair_posteriors.csv"), pair_rows)
    comp_rows = []
    for name in grouped:
        comp_rows.append(dict(model=name, grouped_elpd=float(np.sum(grouped[name])),
                              per_pair=";".join(f"{x:.2f}" for x in grouped[name])))
    w(os.path.join(HERE, "bayes_model_comparison.csv"), comp_rows)
    with open(os.path.join(HERE, "bayes_diagnostics.txt"), "w") as fh:
        fh.write("\n".join(LOG))
        fh.write("\n\nPER-MODEL DIAGNOSTICS\n")
        for dg in diags:
            fh.write(json.dumps(dg) + "\n")
    say(f"  -> bayes_diagnostics.txt")


def score_heldout(idata, d, idx, kw):
    """Log predictive density of held-out trials under a fitted posterior."""
    a = BM.arrays(d)
    post = idata.posterior
    S = post.sizes["chain"] * post.sizes["draw"]
    alpha = post["alpha"].values.reshape(S, -1)
    beta = post["beta"].values.reshape(S, -1)
    y = a["y"][idx]; safe = a["safe"][idx]; cell = a["cell"][idx]; mix = a["mix"][idx]
    if kw["kind"] == "m0":
        bS = post["bS"].values.reshape(S, -1)
        eta = alpha[:, mix] + bS[:, mix] * safe[None, :]
    else:
        q = post["q"].values.reshape(S, -1)
        eta = alpha[:, mix] + beta[:, mix] * (10.0 * q[:, cell] - safe[None, :])
    p = 1.0 / (1.0 + np.exp(-np.clip(eta, -30, 30)))
    ll = y[None, :] * np.log(p + 1e-12) + (1 - y[None, :]) * np.log(1 - p + 1e-12)
    # log mean exp over draws, per trial, then sum
    m = ll.max(axis=0)
    lpd = m + np.log(np.exp(ll - m).mean(axis=0))
    return float(lpd.sum())


if __name__ == "__main__":
    main()
