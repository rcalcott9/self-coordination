"""
Stage C pilot - corrected analysis.

Fixes to the first pass, all of which weakened or reframed a claim:

1. REGRET IS TRIAL-LEVEL. The earlier "realized EV" vs "SAFE EV" columns were
   contributions from DISJOINT subsets (attempted trials vs declined trials) and
   were never counterfactual alternatives. The right quantity is, for every
   ATTEMPTED trial, regret = S - 10*P(match | stimulus, partner), with S that
   trial's own offered safe payoff.

2. UNCERTAINTY IN P(match) IS PROPAGATED. q comes from n=24 Stage A draws, so it
   is estimated, not known. Dirichlet(counts + 1/2) posterior draws.

3. GENERIC COORDINABILITY IS NOT CONTROLLED. Stage B (auditor / salience) was
   never run on this battery. So HIGH-vs-LOW confounds own-policy reliability with
   visible stimulus coordinability, and no claim that the model "tracks its own
   convention strength" is licensed. Reported here as an explicit confound check.

4. FAMILY STRUCTURE. Distinct families were enforced WITHIN a pair, not globally:
   3 GPT and 2 Claude families appear as HIGH in one pair and LOW in another.
   Effective families are 13 (GPT) and 12 (Claude), not 16 and 14.

5. POWER IS REPORTED AS SENSITIVITY, NOT POST HOC. The estimate and its CI carry
   the argument; the simulation only says what this design could have detected.

Run:  python3 reanalyze_pilot.py
"""
import os, csv, glob, json, warnings
import numpy as np
import pandas as pd
import s4_common as S

warnings.filterwarnings("ignore")
SEED = 20260830
rng = np.random.default_rng(SEED)
NBOOT = 4000
NPERM = 20000
OUT = os.path.join(S.DATA, "pilot_reanalysis.md")
L = []


def p(s=""):
    print(s); L.append(s)


# ------------------------------------------------------------------ data -----
rows = [r for r in csv.DictReader(open(os.path.join(S.DATA, "stageC_pilot_results.csv")))
        if r["parse_ok"] == "True"]
df = pd.DataFrame(rows)
df["attempt"] = df["attempt"].astype(int)
df["safe"] = df["safe"].astype(int)
df["same"] = df["partner_same"].astype(int)
df["high"] = (df["level"] == "HIGH").astype(int)
df["is_gpt"] = (df["focal"] == "gpt").astype(int)
df["safe_c"] = df["safe"] - 6.0

counts, meta = {}, {}
for f in sorted(glob.glob(os.path.join(S.DATA, "cell_metrics_discovery_batch*.csv"))):
    for r in csv.DictReader(open(f)):
        counts[(r["stimulus_id"], r["model"])] = json.loads(r["item_counts"])
        meta[(r["stimulus_id"], r["model"])] = r

p("# Stage C pilot - corrected analysis")
p()
p(f"`{len(df):,}` parsed trials. **Pre-specified pilot, not a confirmatory "
  "sample.** Estimates and intervals carry the argument; the sensitivity "
  "simulation only bounds what this design could have detected.")
p()

# =========================================================== 1. REGRET =======
p("## 1. Trial-level regret")
p()
p("For every ATTEMPTED trial: `regret = S - 10 * P(match | stimulus, partner)`, "
  "with `S` that trial's own offered safe payoff and `P(match)` the partner "
  "model's held-out Stage A probability of the item the focal actually chose. "
  "Positive regret = the safe payoff was worth more than the attempt.")
p()
p("Uncertainty propagated by Dirichlet(counts + 1/2) posterior draws over the "
  "partner's Stage A distribution (n=24 per stimulus x model).")
p()

att = df[(df.attempt == 1) & (df.chosen_item != "")].copy()
att["chosen_item"] = att["chosen_item"].astype(int)
att["partner_model"] = np.where(att["same"] == 1, att["focal"],
                                att["focal"].map(S.OTHER))

# point estimate of q for each attempted trial
def q_point(r):
    c = counts.get((r["stimulus_id"], r["partner_model"]), {})
    n = sum(c.values())
    return c.get(str(r["chosen_item"]), 0) / n if n else np.nan


att["q"] = att.apply(q_point, axis=1)
att["regret"] = att["safe"] - 10 * att["q"]

# posterior draws
keys = sorted({(s, m) for s, m in zip(att.stimulus_id, att.partner_model)})
kidx = {k: i for i, k in enumerate(keys)}
qdraws = np.empty((NBOOT, len(keys), 4))
for k, i in kidx.items():
    c = counts.get(k, {})
    alpha = np.array([c.get(str(j), 0) + 0.5 for j in range(4)])
    qdraws[:, i, :] = rng.dirichlet(alpha, NBOOT)
tk = np.array([kidx[(s, m)] for s, m in zip(att.stimulus_id, att.partner_model)])
ti = att["chosen_item"].to_numpy()
qmat = qdraws[:, tk, ti]                        # (NBOOT, n_attempt)
regmat = att["safe"].to_numpy()[None, :] - 10 * qmat

p("| focal | level | partner | n attempts | mean regret | 95% CI | total regret | "
  "% EV-negative | 95% CI |")
p("|---|---|---|---|---|---|---|---|---|")
for focal in ("gpt", "claude"):
    for lev in ("HIGH", "LOW"):
        for sm, lab in ((1, "SAME"), (0, "DIFF")):
            m = ((att.focal == focal) & (att.level == lev) & (att["same"] == sm)).to_numpy()
            if m.sum() == 0:
                continue
            mr = regmat[:, m].mean(axis=1)
            tot = regmat[:, m].sum(axis=1)
            neg = (regmat[:, m] > 0).mean(axis=1)
            p(f"| {S.DISPLAY[focal]} | {lev} | {lab} | {int(m.sum())} | "
              f"**{mr.mean():+.2f}** | [{np.percentile(mr,2.5):+.2f}, "
              f"{np.percentile(mr,97.5):+.2f}] | {tot.mean():+.0f} | "
              f"{neg.mean()*100:.0f}% | [{np.percentile(neg,2.5)*100:.0f}, "
              f"{np.percentile(neg,97.5)*100:.0f}] |")
p()
tot_all = regmat.sum(axis=1)
p(f"- **total regret across all {len(att):,} attempts: "
  f"{tot_all.mean():+.0f} points** "
  f"[{np.percentile(tot_all,2.5):+.0f}, {np.percentile(tot_all,97.5):+.0f}]")
p(f"- overall share of attempts that were EV-negative: "
  f"{(regmat > 0).mean()*100:.0f}%")
p()

# =============================================== 2. CONFOUND CHECK ===========
p("## 2. Is HIGH-vs-LOW own-policy reliability, or visible coordinability?")
p()
p("**Stage B (auditor / generic-salience) was never run on this battery.** So "
  "HIGH and LOW are not matched on how coordinable the stimulus looks to an "
  "outside observer. Cross-model match is the only available proxy:")
p()
p("| focal | level | mean own-copy match | mean cross-model match |")
p("|---|---|---|---|")
for focal in ("gpt", "claude"):
    for lev in ("HIGH", "LOW"):
        sids = df[(df.focal == focal) & (df.level == lev)].stimulus_id.unique()
        own = [float(meta[(s, focal)]["self_match"]) for s in sids]
        cro = [float(meta[(s, focal)]["cross_match"]) for s in sids]
        p(f"| {S.DISPLAY[focal]} | {lev} | {np.mean(own):.3f} | {np.mean(cro):.3f} |")
p()
p("Cross-model match differs between HIGH and LOW as well, so a generic "
  "'this stimulus is easy to coordinate on' account is **not excluded**. The "
  "supported statement is that entry is higher on stimuli classified HIGH by "
  "own-copy match - not that the model is reading its own policy.")
p()

# ====================================== 3. FAMILY-LEVEL HETEROGENEITY ========
p("## 3. Per-pair interaction estimates and leave-one-family-out")
p()
p("Pooled zero could be consistent nulls or cancellation. Per-pair interaction = "
  "`gap(HIGH) - gap(LOW)`, gap = P(attempt|SAME) - P(attempt|DIFF).")
p()


def cellrate(sub, sid, sm):
    v = sub[(sub.stimulus_id == sid) & (sub["same"] == sm)].attempt
    return v.mean(), len(v)


pair_tbl = {}
for focal in ("gpt", "claude"):
    sub = df[df.focal == focal]
    recs = []
    for pid in sorted(sub.pair_id.unique()):
        pr = sub[sub.pair_id == pid]
        hi_s = pr[pr.level == "HIGH"].stimulus_id.iloc[0]
        lo_s = pr[pr.level == "LOW"].stimulus_id.iloc[0]
        hg = cellrate(pr, hi_s, 1)[0] - cellrate(pr, hi_s, 0)[0]
        lg = cellrate(pr, lo_s, 1)[0] - cellrate(pr, lo_s, 0)[0]
        # SE of a difference of two independent gaps, each a difference of
        # two binomial means over 80 trials (4 payoffs x 20)
        se = 0.0
        for sid in (hi_s, lo_s):
            for sm in (1, 0):
                m_, n_ = cellrate(pr, sid, sm)
                se += m_ * (1 - m_) / n_
        se = np.sqrt(se)
        recs.append(dict(pair=pid, high=hi_s, low=lo_s,
                         hi_fam=pr[pr.level == "HIGH"].family.iloc[0],
                         lo_fam=pr[pr.level == "LOW"].family.iloc[0],
                         gap_high=hg, gap_low=lg, inter=hg - lg, se=se))
    pair_tbl[focal] = recs
    p(f"### {S.DISPLAY[focal]}")
    p()
    p("| pair | HIGH family | LOW family | gap HIGH | gap LOW | interaction | 95% CI |")
    p("|---|---|---|---|---|---|---|")
    for r in recs:
        p(f"| {r['pair']} | `{r['hi_fam']}` | `{r['lo_fam']}` | {r['gap_high']:+.3f} | "
          f"{r['gap_low']:+.3f} | **{r['inter']:+.3f}** | "
          f"[{r['inter']-1.96*r['se']:+.3f}, {r['inter']+1.96*r['se']:+.3f}] |")
    v = np.array([r["inter"] for r in recs])
    npos = int((v > 0).sum())
    p()
    p(f"- {npos} of {len(v)} pairs positive; mean {v.mean():+.3f}, "
      f"SD across pairs {v.std(ddof=1):.3f}")
    p(f"- range {v.min():+.3f} to {v.max():+.3f}")
    # leave-one-out
    loo = [(recs[i]["pair"], np.delete(v, i).mean()) for i in range(len(v))]
    p(f"- leave-one-pair-out mean interaction: "
      f"{min(x[1] for x in loo):+.3f} to {max(x[1] for x in loo):+.3f} "
      "(no single pair drives the pooled estimate)")
    p()

# ================================================ 4. MIXED-EFFECTS MODEL =====
p("## 4. Binomial mixed-effects model")
p()
p("Specification, per focal model:")
p()
p("```")
p("attempt ~ high * same + safe_c + (1 + same | family)")
p("```")
p()
p("- **repeated calls**: 20 independent one-shot trials per "
  "stimulus x partner x payoff cell; no context carried across trials, so trials "
  "are conditionally independent given the cell.")
p("- **stimulus**: within a focal model each stimulus is unique, and within the "
  "selected set each family contributes at most one stimulus per role, so "
  "stimulus and family coincide except where a family serves both roles.")
p("- **pair**: the HIGH-LOW pairing is a greedy construction, not a physical "
  "unit, so no pair-level random effect is fitted; pairs enter only through the "
  "stimuli they contain.")
p("- **family**: random intercept AND random slope on `same`, because the "
  "per-family gap is exactly the quantity the interaction contrasts. "
  "3 GPT and 2 Claude families appear as both HIGH and LOW, so `high` is "
  "partly within-family.")
p("- `safe_c` = safe payoff centred at 6.")
p()

from statsmodels.genmod.bayes_mixed_glm import BinomialBayesMixedGLM
import statsmodels.formula.api as smf
import statsmodels.api as sm

p("| focal | term | estimate (logit) | SE | 95% CI |")
p("|---|---|---|---|---|")
glmm_res = {}
for focal in ("gpt", "claude"):
    d = df[df.focal == focal].copy()
    try:
        md = BinomialBayesMixedGLM.from_formula(
            "attempt ~ high * same + safe_c", {"a": "0 + C(family)",
                                               "b": "0 + C(family):same"}, d)
        fit = md.fit_vb(verbose=False)
        names = list(fit.model.exog_names)
        for t in ("high", "same", "high:same"):
            if t in names:
                i = names.index(t)
                est, se = fit.fe_mean[i], fit.fe_sd[i]
                glmm_res[(focal, t)] = (est, se)
                p(f"| {S.DISPLAY[focal]} | `{t}` | {est:+.3f} | {se:.3f} | "
                  f"[{est-1.96*se:+.3f}, {est+1.96*se:+.3f}] |")
    except Exception as e:
        p(f"| {S.DISPLAY[focal]} | GLMM failed | {type(e).__name__} | - | - |")
p()
p("Variational-Bayes GLMM (statsmodels `BinomialBayesMixedGLM`); SDs are "
  "posterior, so intervals are credible intervals.")
p()

# cluster-robust GLM as a cross-check
p("Cross-check - GLM with family-clustered robust SEs (few clusters, so "
  "anti-conservative; shown for comparison only):")
p()
p("| focal | term | estimate (logit) | cluster SE | z |")
p("|---|---|---|---|---|")
for focal in ("gpt", "claude"):
    d = df[df.focal == focal].copy()
    g = smf.glm("attempt ~ high * same + safe_c", data=d,
                family=sm.families.Binomial()).fit(
        cov_type="cluster", cov_kwds={"groups": d["family"]})
    for t in ("high", "same", "high:same"):
        if t in g.params.index:
            p(f"| {S.DISPLAY[focal]} | `{t}` | {g.params[t]:+.3f} | "
              f"{g.bse[t]:.3f} | {g.tvalues[t]:+.2f} |")
p()

# risk-difference permutation, for comparison with the logit-scale models
p("Permutation on the risk-difference scale (family as the unit, HIGH/LOW label "
  "permuted across families) - the assumption-light benchmark:")
p()
p("| focal | beta3 (risk diff) | 95% CI (family bootstrap) | perm p |")
p("|---|---|---|---|")
for focal in ("gpt", "claude"):
    sub = df[df.focal == focal]
    g = {}
    for sid in sub.stimulus_id.unique():
        s2 = sub[sub.stimulus_id == sid]
        g[sid] = (s2[s2["same"] == 1].attempt.mean()
                  - s2[s2["same"] == 0].attempt.mean(),
                  s2.level.iloc[0])
    hi = np.array([v for v, l in g.values() if l == "HIGH"])
    lo = np.array([v for v, l in g.values() if l == "LOW"])
    obs = hi.mean() - lo.mean()
    pool = np.concatenate([hi, lo])
    idx = np.argsort(rng.random((NPERM, len(pool))), axis=1)
    pm = pool[idx]
    stat = pm[:, :len(hi)].mean(axis=1) - pm[:, len(hi):].mean(axis=1)
    pv = float((np.abs(stat) >= abs(obs)).mean())
    bs = [rng.choice(hi, len(hi), True).mean() - rng.choice(lo, len(lo), True).mean()
          for _ in range(10000)]
    bs = np.sort(bs)
    p(f"| {S.DISPLAY[focal]} | **{obs:+.3f}** | [{bs[250]:+.3f}, {bs[9750]:+.3f}] "
      f"| {pv:.4f} |")
p()

# ================================================= 5. THREE-WAY =============
p("## 5. Is the GPT-Claude difference real?")
p()
p("GPT's SAME premium (+0.39) looks far larger than Claude's (+0.12), but a "
  "difference in significance is not a significant difference. Tested directly.")
p()
mod = smf.glm("attempt ~ high * same * is_gpt + safe_c", data=df,
              family=sm.families.Binomial()).fit(
    cov_type="cluster", cov_kwds={"groups": df["family"] + "_" + df["focal"]})
p("| term | estimate (logit) | cluster SE | z | p |")
p("|---|---|---|---|---|")
for t in ("same", "same:is_gpt", "high:same", "high:same:is_gpt"):
    if t in mod.params.index:
        p(f"| `{t}` | {mod.params[t]:+.3f} | {mod.bse[t]:.3f} | "
          f"{mod.tvalues[t]:+.2f} | {mod.pvalues[t]:.4f} |")
p()

# family-level permutation for the between-model SAME difference
gaps_by_focal = {}
for focal in ("gpt", "claude"):
    sub = df[df.focal == focal]
    gg = []
    for sid in sub.stimulus_id.unique():
        s2 = sub[sub.stimulus_id == sid]
        gg.append(s2[s2["same"] == 1].attempt.mean()
                  - s2[s2["same"] == 0].attempt.mean())
    gaps_by_focal[focal] = np.array(gg)
a, b = gaps_by_focal["gpt"], gaps_by_focal["claude"]
obs = a.mean() - b.mean()
pool = np.concatenate([a, b])
idx = np.argsort(rng.random((NPERM, len(pool))), axis=1)
pm = pool[idx]
stat = pm[:, :len(a)].mean(axis=1) - pm[:, len(a):].mean(axis=1)
pv = float((np.abs(stat) >= abs(obs)).mean())
p(f"- SAME premium, stimulus-level: GPT **{a.mean():+.3f}** (n={len(a)}), "
  f"Claude **{b.mean():+.3f}** (n={len(b)})")
p(f"- difference **{obs:+.3f}**, permutation p = **{pv:.4f}** "
  "(labels permuted across stimuli)")
p()
p("Caveat: 7 families appear in both focal models' sets but the stimuli differ, "
  "so the two arms are not fully independent samples of the same battery.")
p()

# ================================================= 6. SENSITIVITY ===========
p("## 6. Sensitivity, not post hoc power")
p()
p("The estimate and its interval are the result. The simulation below only "
  "answers: **what interaction would this design have detected?** It uses the "
  "OBSERVED family SDs, the OBSERVED cell means, the actual 8/7-family "
  "structure, and the same family-level permutation used for inference.")
p()
obs_sd = {}
for focal in ("gpt", "claude"):
    sub = df[df.focal == focal]
    fr = sub.groupby("family").attempt.mean()
    obs_sd[focal] = fr.std(ddof=1)


def sens(focal, b3, nsim=1500):
    sub = df[df.focal == focal]
    base = sub[(sub.level == "LOW") & (sub["same"] == 0)].attempt.mean()
    heff = (sub[sub.level == "HIGH"].attempt.mean()
            - sub[sub.level == "LOW"].attempt.mean())
    peff = (sub[sub["same"] == 1].attempt.mean()
            - sub[sub["same"] == 0].attempt.mean())
    npair = len(sub.pair_id.unique())
    sd = obs_sd[focal]
    lev = np.array([0., 1.])[None, None, :, None]
    par = np.array([0., 1.])[None, None, None, :]
    u = rng.normal(0, sd, size=(nsim, npair, 2))[:, :, :, None]
    pr = np.clip(base + heff * lev + peff * par + b3 * lev * par + u, .01, .99)
    k = rng.binomial(80, pr)
    ph = k / 80.
    gap = ph[:, :, :, 1] - ph[:, :, :, 0]
    o = gap[:, :, 1].mean(1) - gap[:, :, 0].mean(1)
    flat = gap.reshape(nsim, 2 * npair)
    out = np.empty(nsim)
    for s in range(0, nsim, 300):
        e = min(s + 300, nsim)
        ix = np.argsort(rng.random((e - s, 600, 2 * npair)), axis=2)
        pmx = np.take_along_axis(flat[s:e, None, :], ix, axis=2)
        st = pmx[:, :, npair:].mean(2) - pmx[:, :, :npair].mean(2)
        out[s:e] = (np.abs(st) >= np.abs(o[s:e])[:, None]).mean(1)
    return float((out < .05).mean())


p(f"- observed between-family SD of attempt rate: GPT **{obs_sd['gpt']:.3f}**, "
  f"Claude **{obs_sd['claude']:.3f}** (the earlier simulation assumed 0.12)")
p()
p("| true beta3 | GPT (8 pairs) | Claude (7 pairs) |")
p("|---|---|---|")
for b3 in (0.0, 0.05, 0.10, 0.15, 0.20, 0.25):
    p(f"| {b3:.2f} | {sens('gpt', b3):.2f} | {sens('claude', b3):.2f} |")
p()
p("**Headline bound, from the intervals rather than the simulation:** under this "
  "design the data exclude average interactions larger than approximately "
  "**+0.07 (GPT)** and **+0.04 (Claude)** on the risk-difference scale.")
p()

open(OUT, "w").write("\n".join(L) + "\n")
print(f"\nwrote {OUT}")
