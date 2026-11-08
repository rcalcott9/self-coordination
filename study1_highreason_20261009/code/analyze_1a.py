"""Study 1a, high reasoning: the existing pre-specified contrasts (study1_frontier_min_20261007/code/analyze.py),
with one substitution: y = within_model_match from FRESH high-reasoning REF draws (48/array, balanced Latin
orderings, prompt d40ea45d) instead of the reused low-setting frame calibration.

P1 self-vs-auditor paired error D = |A-y| - |S-y| (sign-flip, 10,000 flips; hierarchical bootstrap B=2000)
P2 calibration of S and A against y (slope, intercept, mean signed error, Spearman + permutation p); Holm over P1/P2
S1 PLAY ~ y: array-level binomial GLM (population-averaged) + GLMM (glmm.R; primary per the 1a audit), and
   adjusted for A; S ~ y + A
S2 auditor prediction on old HIGH vs LOW arrays;  S4 legacy d'/AUC/c on old HIGH/LOW labels
S3 (old-wording PLAY/PASS) is not repeated: it described the low-reasoning legacy data.

  python code/analyze_1a.py [--runs runs|runs_mock]
"""
import argparse, csv, glob, json, os, subprocess
import numpy as np
from scipy import stats
import statsmodels.api as sm
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.style.use("academic")
ap = argparse.ArgumentParser(); ap.add_argument("--runs", default="runs"); a = ap.parse_args()
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "analysis", "out_1a" + ("_mock" if a.runs != "runs" else "")); os.makedirs(OUT, exist_ok=True)
F = json.load(open(os.path.join(ROOT, "design", "FROZEN.json")))
FSHA = open(os.path.join(ROOT, "design", "FROZEN.sha256")).read().split()[0][:8]
ARR_ALL = F["arrays_1a"]
LABEL = {"gpt": "GPT-5.5", "claude": "Claude Opus 5"}
B, SEED = 2000, 20261009
rng = np.random.default_rng(SEED)
SC = os.path.dirname(ROOT)
OLD = {"gpt": os.path.join(SC, "study_playpass_gpt"), "claude": os.path.expanduser("~/Desktop/Superrationality/Stag/opus_playpass")}
MIN = dict(REF=40, PLAYPASS=9, SELFPRED=6, AUDITOR=6)

rows = [r for f in glob.glob(os.path.join(ROOT, a.runs, "main", "*.csv")) for r in csv.DictReader(open(f))
        if r["frozen_sha8"] == FSHA]
integ = {}
for m in LABEL:
    for t in ("REF", "PLAYPASS", "SELFPRED", "AUDITOR"):
        s = [r for r in rows if r["focal"] == m and r["task"] == t and r["array"] in ARR_ALL]
        integ[f"{t}|focal={m}"] = dict(rows=len(s), transport_ok=sum(r["transport_ok"] == "1" for r in s),
                                       parsed=sum(r["parse_ok"] == "1" for r in s),
                                       model_mismatch=sum(r["transport_ok"] == "1" and r["model_match"] != "1" for r in s),
                                       cost=round(sum(float(r["cost_usd"] or 0) for r in s), 4))
ok = [r for r in rows if r["parse_ok"] == "1"]
by = {}
for r in ok:
    by.setdefault((r["focal"], r["task"], r["array"]), []).append(r)


def reps(m, task, x):
    v = by.get((m, task, x), [])
    if task == "PLAYPASS":
        return np.array([r["decision"] == "PLAY" for r in v], float)
    if task == "REF":
        return np.array([int(r["canonical_choice"]) for r in v], int)
    return np.array([int(r["match_probability"]) / 100 for r in v], float)


def wmm(c):
    c = np.asarray(c, float); n = c.sum(-1)
    return (c * (c - 1)).sum(-1) / (n * (n - 1))


old_lab = {"gpt": {}, "claude": {}}
for m, p in (("gpt", os.path.join(OLD["gpt"], "data", "frozen_items.json")),
             ("claude", os.path.join(OLD["claude"], "design", "FROZEN_PARALLEL.json"))):
    fz = json.load(open(p))
    for arm in ("HIGH", "LOW"):
        for x in fz[arm]:
            old_lab[m][x["array"]] = arm

D, excluded = {}, {}
for m in LABEL:
    keep = [x for x in ARR_ALL if all(len(reps(m, t, x)) >= MIN[t] for t in MIN)]
    excluded[m] = {x: {t: len(reps(m, t, x)) for t in MIN} for x in ARR_ALL if x not in keep}
    Cn = np.array([np.bincount(reps(m, "REF", x), minlength=4) for x in keep])
    D[m] = dict(arr=keep, C=Cn, n=Cn.sum(1), y=wmm(Cn), S=[reps(m, "SELFPRED", x) for x in keep],
                A=[reps(m, "AUDITOR", x) for x in keep], PP=[reps(m, "PLAYPASS", x) for x in keep])
    for k, src in (("Sm", "S"), ("Am", "A"), ("PPm", "PP")):
        D[m][k] = np.array([v.mean() for v in D[m][src]])
    D[m]["PPn"] = np.array([len(v) for v in D[m]["PP"]])


def boot(m):
    d = D[m]; K = len(d["arr"]); Pr = d["C"] / d["n"][:, None]
    idx = rng.integers(0, K, size=(B, K))
    yb, Sb, Ab, Pb = (np.empty((B, K)) for _ in range(4))
    for j in range(K):
        yb[:, j] = wmm(rng.multinomial(d["n"][j], Pr[j], size=B))
        rs = lambda v: v[rng.integers(0, len(v), size=(B, len(v)))].mean(1)
        Sb[:, j], Ab[:, j], Pb[:, j] = rs(d["S"][j]), rs(d["A"][j]), rs(d["PP"][j])
    take = lambda X: np.take_along_axis(X, idx, axis=1)
    return dict(y=take(yb), S=take(Sb), A=take(Ab), P=take(Pb), y_item=yb, S_item=Sb, A_item=Ab, P_item=Pb)


ci = lambda v: [float(np.quantile(v, .025)), float(np.quantile(v, .975))]


def calib(pred, y):
    sl, ic = np.polyfit(y, pred, 1)
    return sl, ic, float(np.mean(pred - y)), stats.spearmanr(y, pred)[0]


def logit_glm(p, n, X):
    Xc = sm.add_constant(np.column_stack(X))
    p = np.clip(p, 0, 1)
    return sm.GLM(np.column_stack([p * n, (1 - p) * n]), Xc, family=sm.families.Binomial()).fit().params


def dprime(h, f, nh, nf):
    h = np.clip(h, .5 / nh, 1 - .5 / nh); f = np.clip(f, .5 / nf, 1 - .5 / nf)
    return stats.norm.ppf(h) - stats.norm.ppf(f), -(stats.norm.ppf(h) + stats.norm.ppf(f)) / 2


R = {"frozen_sha8": FSHA, "integrity": integ, "excluded": excluded, "B": B, "seed": SEED,
     "n_arrays": {m: len(D[m]["arr"]) for m in LABEL}}
BT, pvals = {}, []
for m in LABEL:
    d = D[m]; K = len(d["arr"]); bt = boot(m); BT[m] = bt
    y, S, A = d["y"], d["Sm"], d["Am"]
    Di = np.abs(A - y) - np.abs(S - y)
    Db = (np.abs(bt["A"] - bt["y"]) - np.abs(bt["S"] - bt["y"])).mean(1)
    flips = rng.choice([-1, 1], size=(10000, K))
    perm_p = float(np.mean(np.abs((flips * Di).mean(1)) >= abs(Di.mean())))
    r = dict(P1=dict(mean_D=float(Di.mean()), ci95=ci(Db), n_pos=int((Di > 0).sum()), n_zero=int((Di == 0).sum()),
                     n_neg=int((Di < 0).sum()), signflip_p=perm_p, mae_self=float(np.abs(S - y).mean()),
                     mae_aud=float(np.abs(A - y).mean()), mean_y=float(y.mean()), mean_S=float(S.mean()), mean_A=float(A.mean())))
    pvals.append((f"{m}:P1", perm_p))
    for nm, pred, pb in (("self", S, bt["S"]), ("auditor", A, bt["A"])):
        sl, ic, mse, rho = calib(pred, y)
        bs = np.array([calib(pb[b], bt["y"][b]) for b in range(B)])
        rho_p = float(np.mean([abs(stats.spearmanr(y, rng.permutation(pred))[0]) >= abs(rho) for _ in range(2000)]))
        r[f"P2_{nm}"] = dict(slope=sl, slope_ci=ci(bs[:, 0]), intercept=ic, intercept_ci=ci(bs[:, 1]),
                             mean_signed_error=mse, mse_ci=ci(bs[:, 2]), spearman=rho, spearman_ci=ci(bs[:, 3]),
                             spearman_perm_p=rho_p)
        pvals.append((f"{m}:P2_{nm}", rho_p))
    n, p = d["PPn"], d["PPm"]
    try:
        b1 = logit_glm(p, n, [y]); b2 = logit_glm(p, n, [y, A])
    except Exception as e:
        b1 = b2 = [np.nan] * 3
    bb1, bb2, bsy = [], [], []
    for b in range(B):
        nb = np.full(K, n.mean())
        try:
            bb1.append(logit_glm(bt["P"][b], nb, [bt["y"][b]])[1])
            bb2.append(logit_glm(bt["P"][b], nb, [bt["y"][b], bt["A"][b]])[1])
        except Exception:
            pass
        X = sm.add_constant(np.column_stack([bt["y"][b], bt["A"][b]]))
        bsy.append(np.linalg.lstsq(X, bt["S"][b], rcond=None)[0][1])
    sy = np.linalg.lstsq(sm.add_constant(np.column_stack([y, A])), S, rcond=None)[0]
    r["S1"] = dict(spearman_play_y=float(stats.spearmanr(y, p)[0]), glm_slope_y=float(b1[1]),
                   glm_slope_y_ci=ci(bb1) if bb1 else None, glm_adj_slope_y=float(b2[1]),
                   glm_adj_slope_y_ci=ci(bb2) if bb2 else None, glm_adj_slope_A=float(b2[2]),
                   self_on_y_adj_A=float(sy[1]), self_on_y_adj_A_ci=ci(bsy), overall_play=float(p.mean()),
                   n_boot_ok=len(bb1))
    hi = np.array([old_lab[m].get(x) == "HIGH" for x in d["arr"]]); lo = np.array([old_lab[m].get(x) == "LOW" for x in d["arr"]])
    if hi.sum() and lo.sum():
        hi_i, lo_i = np.flatnonzero(hi), np.flatnonzero(lo)
        s2b = np.array([bt["A_item"][b][rng.choice(hi_i, len(hi_i))].mean() - bt["A_item"][b][rng.choice(lo_i, len(lo_i))].mean()
                        for b in range(B)])
        r["S2"] = dict(A_high=float(A[hi].mean()), A_low=float(A[lo].mean()), diff=float(A[hi].mean() - A[lo].mean()),
                       diff_ci=ci(s2b), y_high=float(y[hi].mean()), y_low=float(y[lo].mean()), n_high=int(hi.sum()), n_low=int(lo.sum()))
        h, f_ = p[hi].mean(), p[lo].mean()
        dp, c_ = dprime(h, f_, n[hi].sum(), n[lo].sum())
        auc = stats.mannwhitneyu(p[hi], p[lo]).statistic / (hi.sum() * lo.sum())
        r["S4"] = dict(play_high=float(h), play_low=float(f_), dprime=float(dp), criterion=float(c_), auc=float(auc))
    R[m] = r; d["Di"] = Di

order = sorted(pvals, key=lambda x: x[1]); holm = {}
for k, (nm, pv) in enumerate(order):
    holm[nm] = min(1.0, max(pv * (len(order) - k), max([holm[o[0]] for o in order[:k]], default=0)))
R["holm"] = holm

# trial-level file for the GLMM (primary S1), run with glmm.R (lme4), same specification as the 1a audit
tri = os.path.join(OUT, "glmm_trials.csv")
with open(tri, "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["model", "array", "play", "y", "A"])
    for m in LABEL:
        d = D[m]
        for i, x in enumerate(d["arr"]):
            for v in d["PP"][i]:
                w.writerow([m, x, int(v), d["y"][i], d["Am"][i]])
try:
    g = subprocess.run(["Rscript", os.path.join(HERE, "glmm.R"), tri], capture_output=True, text=True, timeout=1800)
    R["S1_glmm"] = g.stdout.strip().splitlines() or [g.stderr[-800:]]
except Exception as e:
    R["S1_glmm"] = f"failed: {e}"

with open(os.path.join(OUT, "item_table.csv"), "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["model", "array", "family", "old_arm", "n_ref", "y_actual", "self_mean", "auditor_mean", "D_paired",
                "play_rate", "n_play"])
    for m in LABEL:
        d = D[m]
        for i, x in enumerate(d["arr"]):
            w.writerow([m, x, x.rsplit("_m", 1)[0], old_lab[m].get(x, "MID"), d["n"][i], round(d["y"][i], 4),
                        round(d["Sm"][i], 4), round(d["Am"][i], 4), round(d["Di"][i], 4), round(d["PPm"][i], 4), d["PPn"][i]])
json.dump(R, open(os.path.join(OUT, "results.json"), "w"), indent=1, default=float)

# figures (academic style; series distinguished by marker as well as tone)
CS, CA = "#1b4f8a", "#d9822b"
fig, axes = plt.subplots(1, 2, figsize=(5.5, 3.2), sharex=True, sharey=True)
for ax, m in zip(axes, LABEL):
    d = D[m]; y, S, A = d["y"], d["Sm"], d["Am"]
    for i in range(len(y)):
        ax.plot([y[i], y[i]], [S[i], A[i]], color="0.8", lw=.5, zorder=1)
    ax.plot([0, 1], [0, 1], color="black", lw=.8, zorder=0)
    xs = np.linspace(0, 1, 50)
    for v, col, ls in ((S, CS, "-"), (A, CA, "--")):
        sl, ic = np.polyfit(y, v, 1); ax.plot(xs, ic + sl * xs, color=col, ls=ls, lw=.9)
    ax.scatter(y, S, marker="o", s=14, color=CS, zorder=3, label="Self-prediction")
    ax.scatter(y, A, marker="s", s=14, facecolor="white", edgecolor=CA, zorder=3, label="Reciprocal auditor")
    ax.set_xlim(.15, 1.03); ax.set_ylim(0, 1.03); ax.set_xlabel("Measured matching probability")
    ax.text(0, 1.02, LABEL[m], transform=ax.transAxes, va="bottom", fontsize=9)
axes[0].set_ylabel("Mean predicted matching probability"); axes[1].legend(loc="lower right", frameon=False, fontsize=8)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "fig1_calibration.pdf")); fig.savefig(os.path.join(OUT, "fig1_calibration.png"), dpi=300)
plt.close(fig)
fig, axes = plt.subplots(1, 2, figsize=(5.5, 3.2), sharex=True, sharey=True)
for ax, m in zip(axes, LABEL):
    d = D[m]; y, p, n = d["y"], d["PPm"], d["PPn"]
    z = 1.96; den = 1 + z * z / n; cen = (p + z * z / (2 * n)) / den
    hw = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    ax.errorbar(y, p, yerr=[p - (cen - hw), (cen + hw) - p], fmt="o", ms=3.5, color="black", mfc="black",
                ecolor="0.6", elinewidth=.5, capsize=1.2)
    ax.set_ylim(-.03, 1.03); ax.set_xlabel("Measured matching probability")
    ax.text(0, 1.02, LABEL[m], transform=ax.transAxes, va="bottom", fontsize=9)
axes[0].set_ylabel("Proportion choosing PLAY")
fig.tight_layout(); fig.savefig(os.path.join(OUT, "fig3_playpass.pdf")); fig.savefig(os.path.join(OUT, "fig3_playpass.png"), dpi=300)
plt.close(fig)
print(json.dumps({m: {k: R[m][k] for k in ("P1",)} for m in LABEL}, indent=1, default=float))
print("excluded:", {m: len(v) for m, v in excluded.items()}, "| out:", OUT)
