"""Study 1b analysis: final design section 7 as amended by AMENDMENT_1.

Primary: selected S1+S2_G+S2_O arrays; pooled self-minus-cross Brier advantage
  D_j = 0.5*[(B_O->G + B_G->O) - (B_G->G + B_O->O)]   (D > 0 = self more accurate),
two-sided array sign-flip, p = (k+1)/(B+1) with B = 10,000 SIMULATED FLIP VECTORS; array bootstrap CI.
Target-specific D_GPT = B_O->G - B_G->G, D_Opus = B_G->O - B_O->O (Holm over 2).
Secondary: S3; continuous TVD moderation (screen distributions) over all selected arrays; strata.
Sensitivity: hierarchical bootstrap; log score (floor .01); linear mixed model on cell means.
Brier per response vs fresh REF distribution p_hat: B = sum q^2 - 2 q.p_hat + 1.
"""
import csv, glob, json, os
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "analysis", "out"); os.makedirs(OUT, exist_ok=True)
FM = json.load(open(os.path.join(ROOT, "design", "FROZEN_MAIN.json")))
SEL = json.load(open(os.path.join(ROOT, "design", "SELECTION.json")))
FSHA = open(os.path.join(ROOT, "design", "FROZEN_MAIN.sha256")).read().split()[0][:8]
M = ["gpt", "claude"]; B_FLIP, B_BOOT = 10000, 10000
rng = np.random.default_rng(20261008)
PRIMARY = {"S1", "S2_G", "S2_O"}

rows = [r for f in glob.glob(os.path.join(ROOT, "runs", "main", "*.csv")) for r in csv.DictReader(open(f))
        if r["frozen_sha8"] == FSHA]
strat = {x: s for s, v in FM["strata"].items() for x in v}
ref = {(m, x): [] for m in M for x in FM["arrays"]}
pred = {(p, t, x): [] for p in M for t in M for x in FM["arrays"]}
integ = {}
for r in rows:
    k = f"{r['task']}|{r['answerer']}->{r['target']}"
    d = integ.setdefault(k, dict(rows=0, transport_ok=0, parsed=0, mismatch=0, cost=0.0))
    d["rows"] += 1; d["transport_ok"] += r["transport_ok"] == "1"; d["parsed"] += r["parse_ok"] == "1"
    d["mismatch"] += r["transport_ok"] == "1" and r["model_match"] != "1"; d["cost"] += float(r["cost_usd"] or 0)
    if r["parse_ok"] != "1":
        continue
    if r["task"] == "REF":
        ref[(r["answerer"], r["array"])].append(int(r["canonical_choice"]))
    else:
        pred[(r["answerer"], r["target"], r["array"])].append(np.array(json.loads(r["p_canonical"])))

# exclusion rule: any cell < 6/8 parsed predictions
excluded = [x for x in FM["arrays"] if any(len(pred[(p, t, x)]) < 6 for p in M for t in M)]
arrays = [x for x in FM["arrays"] if x not in excluded]


def brier(q, ph):
    return float(q @ q - 2 * q @ ph + 1)


def logscore(q, ph):
    return float(-(ph * np.log(np.maximum(q, .01) / np.maximum(q, .01).sum())).sum())


def cell_scores(score, phat, P):
    return {(p, t, x): np.mean([score(q, phat[(t, x)]) for q in P[(p, t, x)]]) for p in M for t in M for x in arrays}


def phat_of(R):
    return {(m, x): np.bincount(R[(m, x)], minlength=4) / len(R[(m, x)]) for m in M for x in arrays}


def contrasts(S, xs):
    G, O = "gpt", "claude"
    dG = np.array([S[(O, G, x)] - S[(G, G, x)] for x in xs])
    dO = np.array([S[(G, O, x)] - S[(O, O, x)] for x in xs])
    pooled = (dG + dO) / 2
    pred_eff = np.array([0.5 * ((S[(G, G, x)] + S[(G, O, x)]) - (S[(O, G, x)] + S[(O, O, x)])) for x in xs])
    targ_eff = np.array([0.5 * ((S[(G, G, x)] + S[(O, G, x)]) - (S[(G, O, x)] + S[(O, O, x)])) for x in xs])
    return dict(pooled=pooled, target_gpt=dG, target_opus=dO, predictor_effect=pred_eff, target_effect=targ_eff)


def signflip(v):
    v = np.asarray(v); fl = rng.choice([-1, 1], size=(B_FLIP, len(v)))
    k = int(np.sum(np.abs((fl * v).mean(1)) >= abs(v.mean()) - 1e-12))
    return (k + 1) / (B_FLIP + 1), k


def boot_ci(v):
    v = np.asarray(v); idx = rng.integers(0, len(v), size=(B_BOOT, len(v)))
    m = v[idx].mean(1); return [float(np.quantile(m, .025)), float(np.quantile(m, .975))]


def summarize(v):
    p, k = signflip(v)
    return dict(n=len(v), mean=float(np.mean(v)), ci95=boot_ci(v), signflip_p=p, k_exceed=k, B_flips=B_FLIP,
                n_pos=int((v > 0).sum()), n_neg=int((v < 0).sum()))


PH = phat_of(ref)
S = cell_scores(brier, PH, pred)
prim = [x for x in arrays if strat[x] in PRIMARY]
sec3 = [x for x in arrays if strat[x] == "S3"]
R = dict(frozen_main=FSHA, selection_sha8=FM["selection_sha8"], integrity=integ, excluded=excluded,
         n_selected={s: len(v) for s, v in FM["strata"].items()}, n_primary=len(prim), n_S3=len(sec3))
C1 = contrasts(S, prim)
R["primary"] = {k: summarize(v) for k, v in C1.items()}
ps = [R["primary"]["target_gpt"]["signflip_p"], R["primary"]["target_opus"]["signflip_p"]]
o = np.argsort(ps); holm = [0, 0]
holm[o[0]] = min(1, 2 * ps[o[0]]); holm[o[1]] = min(1, max(holm[o[0]], ps[o[1]]))
R["primary"]["target_gpt"]["holm_p"], R["primary"]["target_opus"]["holm_p"] = holm
R["cell_mean_brier_primary"] = {f"{p}->{t}": float(np.mean([S[(p, t, x)] for x in prim])) for p in M for t in M}
# secondary: S3 + strata
if sec3:
    C3 = contrasts(S, sec3); R["S3"] = {k: summarize(v) for k, v in C3.items() if k in ("pooled", "target_gpt", "target_opus")}
R["by_stratum"] = {}
for s in ["S1", "S2_G", "S2_O", "S3"]:
    xs = [x for x in arrays if strat[x] == s]
    if xs:
        c = contrasts(S, xs)
        R["by_stratum"][s] = {k: dict(n=len(xs), mean=float(c[k].mean()), ci95=boot_ci(c[k]) if len(xs) > 1 else None)
                              for k in ("pooled", "target_gpt", "target_opus")}
# moderation: TVD from SCREEN distributions (selection draws), all selected arrays
pa = SEL["per_array"]
tvd = np.array([0.5 * np.abs(np.array(pa[x]["gpt"]["counts"]) / sum(pa[x]["gpt"]["counts"])
                             - np.array(pa[x]["claude"]["counts"]) / sum(pa[x]["claude"]["counts"])).sum() for x in arrays])
call = contrasts(S, arrays)
mod = {}
for k in ("pooled", "target_gpt", "target_opus"):
    y = call[k]; b = np.polyfit(tvd, y, 1)[0]
    idx = rng.integers(0, len(y), size=(B_BOOT, len(y)))
    bs = [np.polyfit(tvd[i], y[i], 1)[0] for i in idx[:4000] if np.ptp(tvd[i]) > 0]
    perm = np.array([np.polyfit(rng.permutation(tvd), y, 1)[0] for _ in range(B_FLIP)])
    mod[k] = dict(slope=float(b), ci95=[float(np.quantile(bs, .025)), float(np.quantile(bs, .975))],
                  perm_p=(int(np.sum(np.abs(perm) >= abs(b))) + 1) / (B_FLIP + 1), n=len(y))
tvd_fresh = np.array([0.5 * np.abs(PH[("gpt", x)] - PH[("claude", x)]).sum() for x in arrays])
mod["tvd_reliability_screen_vs_fresh_r"] = float(np.corrcoef(tvd, tvd_fresh)[0, 1])
R["moderation_TVD"] = mod
# sensitivity
hb = []
for _ in range(2000):
    xs = [prim[i] for i in rng.integers(0, len(prim), len(prim))]
    Rb = {(m, x): list(rng.choice(ref[(m, x)], len(ref[(m, x)]))) for m in M for x in set(xs)}
    Pb = {(p, t, x): [pred[(p, t, x)][i] for i in rng.integers(0, len(pred[(p, t, x)]), len(pred[(p, t, x)]))]
          for p in M for t in M for x in set(xs)}
    phb = {(m, x): np.bincount(Rb[(m, x)], minlength=4) / len(Rb[(m, x)]) for (m, x) in Rb}
    Sb = {(p, t, x): np.mean([brier(q, phb[(t, x)]) for q in Pb[(p, t, x)]]) for (p, t, x) in Pb}
    hb.append(np.mean([0.5 * ((Sb[("claude", "gpt", x)] + Sb[("gpt", "claude", x)]) - (Sb[("gpt", "gpt", x)] + Sb[("claude", "claude", x)])) for x in xs]))
R["sensitivity"] = dict(hierarchical_boot_ci_pooled=[float(np.quantile(hb, .025)), float(np.quantile(hb, .975))])
SL = cell_scores(logscore, PH, pred); CL = contrasts(SL, prim)
R["sensitivity"]["logscore_pooled"] = summarize(CL["pooled"])
try:
    import pandas as pd, statsmodels.formula.api as smf
    d = pd.DataFrame([dict(array=x, pred=p, targ=t, B=S[(p, t, x)], self=int(p == t)) for p in M for t in M for x in prim])
    fit = smf.mixedlm("B ~ C(pred) * C(targ)", d, groups=d["array"]).fit(reml=True)
    # pooled self effect = -(interaction)/... report the interaction coefficient and its CI
    name = [n for n in fit.params.index if ":" in n][0]
    R["sensitivity"]["lmm_interaction"] = dict(term=name, coef=float(fit.params[name]),
                                               ci95=[float(v) for v in fit.conf_int().loc[name]],
                                               note="pooled self-minus-cross D = -coef/2 under treatment coding with gpt/claude levels; sign checked against primary")
except Exception as e:
    R["sensitivity"]["lmm_interaction"] = f"failed: {e}"
# power for the ACTUAL primary N (frozen assumptions)
pw = {}
for tau in (.085, .05):
    for delta in (.03, .05, .08):
        hits = 0
        for _ in range(1000):
            c = delta + rng.normal(0, tau, len(prim)) + rng.normal(0, .105 / np.sqrt(8), len(prim)) + rng.normal(0, np.sqrt(.0017), len(prim))
            fl = rng.choice([-1, 1], size=(1000, len(prim)))
            hits += (np.sum(np.abs((fl * c).mean(1)) >= abs(c.mean())) + 1) / 1001 < .05
        pw[f"tau={tau},delta={delta}"] = hits / 1000
R["power_actual_primary_N"] = dict(n=len(prim), power=pw)
# item table
with open(os.path.join(OUT, "item_table.csv"), "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["array", "stratum", "tvd_screen", "tvd_fresh", "gpt_fresh", "opus_fresh"] +
               [f"B_{p}->{t}" for p in M for t in M] + ["D_pooled", "D_gpt", "D_opus"])
    for i, x in enumerate(arrays):
        w.writerow([x, strat[x], round(tvd[i], 4), round(tvd_fresh[i], 4), np.round(PH[("gpt", x)], 3).tolist(),
                    np.round(PH[("claude", x)], 3).tolist()] + [round(S[(p, t, x)], 4) for p in M for t in M] +
                   [round(call["pooled"][i], 4), round(call["target_gpt"][i], 4), round(call["target_opus"][i], 4)])
json.dump(R, open(os.path.join(OUT, "results.json"), "w"), indent=1, default=float)

# figure: per-array pooled D (primary sample) and S3, academic style
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
plt.style.use("academic")
fig, ax = plt.subplots(figsize=(5.5, 3.2))
mk = {"S1": ("o", "black"), "S2_G": ("s", "black"), "S2_O": ("^", "black"), "S3": ("D", "white")}
order = sorted(arrays, key=lambda x: (strat[x] == "S3", call["pooled"][arrays.index(x)]))
npr = len(prim)
for i, x in enumerate(order):
    m_, fc = mk[strat[x]]
    xpos = i if strat[x] != "S3" else i + 2
    ax.plot(xpos, call["pooled"][arrays.index(x)], marker=m_, mfc=fc, mec="black", ls="none", ms=4.5)
ax.axhline(0, color="black", lw=.8)
mp = R["primary"]["pooled"]
ax.errorbar([npr], [mp["mean"]], yerr=[[mp["mean"] - mp["ci95"][0]], [mp["ci95"][1] - mp["mean"]]],
            fmt="_", ms=12, mew=1.5, color="black", ecolor="black", elinewidth=1.2, capsize=3)
ax.axvline(npr + 1, color="0.7", lw=.5, ls=":")
for s_, (m_, fc) in mk.items():
    ax.plot([], [], marker=m_, mfc=fc, mec="black", ls="none", label=s_)
ax.legend(frameon=False, fontsize=8, ncol=4, loc="lower left", bbox_to_anchor=(0, 1.0))
ax.set_xticks([]); ax.set_xlabel("Arrays: primary (S1, S2) then shared-policy controls (S3)")
ax.set_ylabel("Self-minus-cross Brier advantage")
fig.tight_layout(); fig.savefig(os.path.join(OUT, "fig_selfcross.pdf")); fig.savefig(os.path.join(OUT, "fig_selfcross.png"), dpi=300)
print(json.dumps(R, indent=1, default=float))
