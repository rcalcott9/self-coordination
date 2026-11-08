"""Study 1 frontier minimal: pre-specified analysis (plan: ~/Downloads/Study1_frontier_min_collection_plan.md).

Unit = array. y = within_model_match from the reused frame calibration (48 draws/array).
S = mean self-predicted MATCH_PROBABILITY/100; A = mean reciprocal-auditor prediction/100.
One hierarchical bootstrap (B=2000): resample arrays (pairing kept), then within each array
resample the 48 calibration draws, the self reps, the auditor reps and the PLAY/PASS reps.

Primary  P1 self-vs-auditor paired error D = |A-y| - |S-y|   (D>0 = self advantage)
         P2 calibration of S and of A against y
Secondary S1 corrected PLAY/PASS ~ y, and auditor-adjusted (y + A); S ~ y + A
          S2 auditor prediction, old HIGH vs LOW
          S3 old vs corrected PLAY/PASS (descriptive, separate)
          S4 legacy d'/AUC/c on the corrected data
Deviation from plan, stated in the report: S1 uses an array-level binomial GLM (logit) with
hierarchical-bootstrap CIs instead of a random-intercept GLMM (robust to arrays at 0/12 or 12/12).
"""
import csv, glob, json, os
import numpy as np
from scipy import stats
import statsmodels.api as sm
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.style.use("academic")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "analysis", "out"); os.makedirs(OUT, exist_ok=True)
F = json.load(open(os.path.join(ROOT, "design", "FROZEN.json")))
ARR = F["arrays"]; K = len(ARR)
MODEL = {"gpt": "gpt-5.5-2026-04-23", "claude": "claude-opus-5"}
LABEL = {"gpt": "GPT-5.5", "claude": "Claude Opus 5"}
B, SEED = 2000, 20261008
rng = np.random.default_rng(SEED)
SC = os.path.dirname(ROOT)
OLD = {"gpt": os.path.join(SC, "study_playpass_gpt"),
       "claude": os.path.expanduser("~/Desktop/Superrationality/Stag/opus_playpass")}

# ------------------------------------------------------------------ load ----------
frame = {m: {a: [] for a in ARR} for m in MODEL}          # list of (perm, canonical)
for r in csv.DictReader(open(F["calibration_reuse"]["source"])):
    for m, mid in MODEL.items():
        if r["checkpoint_requested"] == mid and r["parse_ok"] == "1":
            frame[m][r["array_id"]].append((int(r["presentation_id"]), int(r["canonical_index"])))
rows = [r for f in glob.glob(os.path.join(ROOT, "runs", "main", "*.csv")) for r in csv.DictReader(open(f))]
integ = {}
for m in MODEL:
    for t in ("PLAYPASS", "SELFPRED", "AUDITOR"):
        s = [r for r in rows if r["focal"] == m and r["task"] == t]
        integ[f"{t}|focal={m}"] = dict(rows=len(s), transport_ok=sum(r["transport_ok"] == "1" for r in s),
                                       parsed=sum(r["parse_ok"] == "1" for r in s),
                                       model_mismatch=sum(r["transport_ok"] == "1" and r["model_match"] != "1" for r in s))
ok = [r for r in rows if r["parse_ok"] == "1"]


def reps(m, task, a):
    v = [r for r in ok if r["focal"] == m and r["task"] == task and r["array"] == a]
    if task == "PLAYPASS":
        return np.array([r["decision"] == "PLAY" for r in v], float)
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
old_pp = {"gpt": {}, "claude": {}}
for r in csv.DictReader(open(os.path.join(OLD["gpt"], "data", "playpass_full_20260912_191607.csv"))):
    if r["parse_ok"] == "1":
        old_pp["gpt"].setdefault(r["array"], []).append(r["decision"] == "PLAY")
for r in json.load(open(os.path.join(OLD["claude"], "results", "parallel_disabled_20260912_191726", "raw_rows.json"))):
    if r["decision"]:
        old_pp["claude"].setdefault(r["item"], []).append(r["decision"] == "PLAY")

# ------------------------------------------------------------- per-model data ----
D = {}
for m in MODEL:
    C = np.array([np.bincount([c for _, c in frame[m][a]], minlength=4) for a in ARR])
    assert (C.sum(1) == 48).all()
    # same-presentation match (for S3 re-scoring of OLD data only)
    sp = []
    for a in ARR:
        byp = {}
        for p, c in frame[m][a]:
            byp.setdefault(p, []).append(c)
        sp.append(np.mean([v[0] == v[1] for v in byp.values() if len(v) == 2]))
    D[m] = dict(C=C, y=wmm(C), same_pres=np.array(sp),
                S=[reps(m, "SELFPRED", a) for a in ARR], A=[reps(m, "AUDITOR", a) for a in ARR],
                PP=[reps(m, "PLAYPASS", a) for a in ARR])
    D[m]["Sm"] = np.array([x.mean() for x in D[m]["S"]])
    D[m]["Am"] = np.array([x.mean() for x in D[m]["A"]])
    D[m]["PPm"] = np.array([x.mean() for x in D[m]["PP"]])
    D[m]["PPn"] = np.array([len(x) for x in D[m]["PP"]])


def boot(m):
    """Hierarchical bootstrap draws: y*, S*, A*, PP* (B x K) on resampled arrays, + index."""
    d = D[m]; P = d["C"] / 48.0
    idx = rng.integers(0, K, size=(B, K))
    yb = np.empty((B, K)); Sb = np.empty((B, K)); Ab = np.empty((B, K)); Pb = np.empty((B, K))
    for j in range(K):
        cnt = rng.multinomial(48, P[j], size=B)
        ys = wmm(cnt)
        def rs(v):
            return v[rng.integers(0, len(v), size=(B, len(v)))].mean(1)
        Ss, As, Ps = rs(d["S"][j]), rs(d["A"][j]), rs(d["PP"][j])
        for arr_, val in ((yb, ys), (Sb, Ss), (Ab, As), (Pb, Ps)):
            arr_[:, j] = val          # within-array resample for array j
    # apply array resampling (pairing preserved: same idx for every quantity)
    take = lambda X: np.take_along_axis(X, idx, axis=1)
    return dict(y=take(yb), S=take(Sb), A=take(Ab), P=take(Pb), y_item=yb, S_item=Sb, A_item=Ab, P_item=Pb)


def ci(v):
    return [float(np.quantile(v, .025)), float(np.quantile(v, .975))]


def calib(pred, y):
    sl, ic = np.polyfit(y, pred, 1)
    return sl, ic, float(np.mean(pred - y)), stats.spearmanr(y, pred)[0]


def logit_glm(p, n, X):
    Xc = sm.add_constant(np.column_stack(X))
    p = np.clip(p, 0, 1)
    fit = sm.GLM(np.column_stack([p * n, (1 - p) * n]), Xc, family=sm.families.Binomial()).fit()
    return fit.params


def dprime(h, f, nh, nf):
    h = np.clip(h, .5 / nh, 1 - .5 / nh); f = np.clip(f, .5 / nf, 1 - .5 / nf)
    return stats.norm.ppf(h) - stats.norm.ppf(f), -(stats.norm.ppf(h) + stats.norm.ppf(f)) / 2


R, BT = {"integrity": integ, "B": B, "seed": SEED}, {}
pvals = []
for m in MODEL:
    d = D[m]; bt = boot(m); BT[m] = bt
    y, S, A = d["y"], d["Sm"], d["Am"]
    Di = np.abs(A - y) - np.abs(S - y)
    Db = (np.abs(bt["A"] - bt["y"]) - np.abs(bt["S"] - bt["y"])).mean(1)
    flips = rng.choice([-1, 1], size=(10000, K))
    perm_p = float(np.mean(np.abs((flips * Di).mean(1)) >= abs(Di.mean())))
    r = dict(P1=dict(mean_D=float(Di.mean()), ci95=ci(Db), n_pos=int((Di > 0).sum()), n_zero=int((Di == 0).sum()),
                     n_neg=int((Di < 0).sum()), signflip_p=perm_p,
                     mae_self=float(np.abs(S - y).mean()), mae_aud=float(np.abs(A - y).mean())))
    pvals.append((f"{m}:P1", perm_p))
    for nm, pred, pb in (("self", S, bt["S"]), ("auditor", A, bt["A"])):
        sl, ic, mse, rho = calib(pred, y)
        bs = np.array([calib(pb[b], bt["y"][b]) for b in range(B)])
        rho_p = float(np.mean([abs(stats.spearmanr(y, rng.permutation(pred))[0]) >= abs(rho) for _ in range(2000)]))
        r[f"P2_{nm}"] = dict(slope=sl, slope_ci=ci(bs[:, 0]), intercept=ic, intercept_ci=ci(bs[:, 1]),
                             mean_signed_error=mse, mse_ci=ci(bs[:, 2]), spearman=rho, spearman_ci=ci(bs[:, 3]),
                             spearman_perm_p=rho_p)
        pvals.append((f"{m}:P2_{nm}", rho_p))
    # S1
    n = d["PPn"]; p = d["PPm"]
    b1 = logit_glm(p, n, [y]); b2 = logit_glm(p, n, [y, A])
    bb1, bb2, bsy = [], [], []
    for b in range(B):
        nb = n[np.zeros(K, int)] if False else np.full(K, n.mean())
        try:
            bb1.append(logit_glm(bt["P"][b], nb, [bt["y"][b]])[1])
            bb2.append(logit_glm(bt["P"][b], nb, [bt["y"][b], bt["A"][b]])[1])
        except Exception:
            pass
        X = sm.add_constant(np.column_stack([bt["y"][b], bt["A"][b]]))
        bsy.append(np.linalg.lstsq(X, bt["S"][b], rcond=None)[0][1])
    Xs = sm.add_constant(np.column_stack([y, A]))
    sy = np.linalg.lstsq(Xs, S, rcond=None)[0]
    r["S1"] = dict(spearman_play_y=float(stats.spearmanr(y, p)[0]), logit_slope_y=float(b1[1]), logit_slope_y_ci=ci(bb1),
                   adj_logit_slope_y=float(b2[1]), adj_logit_slope_y_ci=ci(bb2), adj_logit_slope_A=float(b2[2]),
                   self_on_y_adj_A=float(sy[1]), self_on_y_adj_A_ci=ci(bsy), overall_play=float(p.mean()),
                   n_boot_ok=len(bb1))
    # S2
    hi = np.array([old_lab[m].get(a) == "HIGH" for a in ARR]); lo = np.array([old_lab[m].get(a) == "LOW" for a in ARR])
    hi_i, lo_i = np.flatnonzero(hi), np.flatnonzero(lo)          # resample arrays within arm + reps
    s2b = np.array([bt["A_item"][b][rng.choice(hi_i, len(hi_i))].mean()
                    - bt["A_item"][b][rng.choice(lo_i, len(lo_i))].mean() for b in range(B)])
    r["S2"] = dict(A_high=float(A[hi].mean()), A_low=float(A[lo].mean()), diff=float(A[hi].mean() - A[lo].mean()),
                   diff_ci=ci(s2b), y_high=float(y[hi].mean()), y_low=float(y[lo].mean()))
    # S3 (descriptive)
    on = [i for i, a in enumerate(ARR) if a in old_pp[m]]
    oldp = np.array([np.mean(old_pp[m][ARR[i]]) for i in on])
    r["S3"] = dict(n_items=len(on), old_play=float(oldp.mean()), new_play_same_items=float(p[on].mean()),
                   mean_change=float((p[on] - oldp).mean()),
                   spearman_old_vs_y=float(stats.spearmanr(y[on], oldp)[0]),
                   spearman_old_vs_samepres=float(stats.spearmanr(d["same_pres"][on], oldp)[0]),
                   spearman_new_vs_y=float(stats.spearmanr(y[on], p[on])[0]))
    # S4 legacy
    h, f_ = p[hi].mean(), p[lo].mean()
    dp, c_ = dprime(h, f_, n[hi].sum(), n[lo].sum())
    auc = stats.mannwhitneyu(p[hi], p[lo]).statistic / (hi.sum() * lo.sum())
    r["S4"] = dict(play_high=float(h), play_low=float(f_), dprime=float(dp), criterion=float(c_), auc=float(auc))
    R[m] = r
    D[m]["Di"] = Di; D[m]["old"] = (on, oldp)

# Holm
order = sorted(pvals, key=lambda x: x[1]); holm = {}
for k, (nm, pv) in enumerate(order):
    holm[nm] = min(1.0, max(pv * (len(order) - k), max([holm[o[0]] for o in order[:k]], default=0)))
R["holm"] = holm

# item table
with open(os.path.join(OUT, "item_table.csv"), "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["model", "array", "old_arm", "y_actual", "self_mean", "auditor_mean", "D_paired", "play_rate", "n_play",
                "old_play_rate", "same_pres_match"])
    for m in MODEL:
        d = D[m]; on, oldp = d["old"]; om = dict(zip([ARR[i] for i in on], oldp))
        for i, a in enumerate(ARR):
            w.writerow([m, a, old_lab[m].get(a, "MID"), round(d["y"][i], 4), round(d["Sm"][i], 4), round(d["Am"][i], 4),
                        round(d["Di"][i], 4), round(d["PPm"][i], 4), d["PPn"][i],
                        "" if a not in om else round(om[a], 4), round(d["same_pres"][i], 4)])
json.dump(R, open(os.path.join(OUT, "results.json"), "w"), indent=1, default=float)

# ------------------------------------------------------------------ figures -------
CS, CA = "#1b4f8a", "#d9822b"


def save(fig, name):
    fig.savefig(os.path.join(OUT, name + ".pdf")); fig.savefig(os.path.join(OUT, name + ".png"), dpi=300)
    plt.close(fig)


# Fig 1 calibration
fig, axes = plt.subplots(1, 2, figsize=(5.5, 3.2), sharex=True, sharey=True)
for ax, m in zip(axes, MODEL):
    d, bt = D[m], BT[m]
    y, S, A = d["y"], d["Sm"], d["Am"]
    ylo, yhi = np.quantile(bt["y_item"], [.025, .975], axis=0)
    for v, vb, col, mk, fc in ((S, bt["S_item"], CS, "o", CS), (A, bt["A_item"], CA, "s", "white")):
        lo_, hi_ = np.quantile(vb, [.025, .975], axis=0)
        ax.errorbar(y, v, yerr=[v - lo_, hi_ - v], xerr=[y - ylo, yhi - y], fmt="none", ecolor=col,
                    alpha=.35, elinewidth=.5, capsize=1.2, zorder=1)
    for i in range(K):
        ax.plot([y[i], y[i]], [S[i], A[i]], color="0.8", lw=.5, zorder=2)
    ax.plot([0, 1], [0, 1], color="black", lw=.8, zorder=0)
    xs = np.linspace(0, 1, 50)
    for v, key, col, ls in ((S, "S", CS, "-"), (A, "A", CA, "--")):
        sl, ic = np.polyfit(y, v, 1)
        ax.plot(xs, ic + sl * xs, color=col, ls=ls, lw=.9, zorder=3)
        lines = np.array([np.polyval(np.polyfit(bt["y"][b], bt[key][b], 1), xs) for b in range(0, B, 4)])
        for q in (.025, .975):
            ax.plot(xs, np.quantile(lines, q, axis=0), color=col, ls=":", lw=.6, zorder=3)
    ax.scatter(y, S, marker="o", s=14, color=CS, edgecolor=CS, zorder=4, label="Self-prediction")
    ax.scatter(y, A, marker="s", s=14, facecolor="white", edgecolor=CA, zorder=4, label="Reciprocal auditor")
    ax.set_xlim(.15, 1.03); ax.set_ylim(0, 1.03)
    ax.set_xlabel("Measured matching probability")
    ax.text(0, 1.02, LABEL[m], transform=ax.transAxes, va="bottom", fontsize=9)
axes[0].set_ylabel("Mean predicted matching probability")
axes[1].legend(loc="lower right", frameon=False, fontsize=8)
fig.tight_layout(); save(fig, "fig1_calibration")

# Fig 2 paired error
fig, axes = plt.subplots(1, 2, figsize=(5.5, 3.2), sharey=True)
for ax, m in zip(axes, MODEL):
    d, bt = D[m], BT[m]
    Di = d["Di"]; o = np.argsort(Di)
    Db_item = np.abs(bt["A_item"] - bt["y_item"]) - np.abs(bt["S_item"] - bt["y_item"])
    lo_, hi_ = np.quantile(Db_item, [.025, .975], axis=0)
    x = np.arange(K)
    ax.errorbar(x, Di[o], yerr=[Di[o] - lo_[o], hi_[o] - Di[o]], fmt="o", ms=3, color="black",
                mfc="black", elinewidth=.5, capsize=1.2)
    ax.axhline(0, color="black", lw=.8)
    mD = R[m]["P1"]["mean_D"]; c = R[m]["P1"]["ci95"]
    ax.axhline(mD, color="black", ls="--", lw=.8)
    ax.errorbar([K + 2], [mD], yerr=[[mD - c[0]], [c[1] - mD]], fmt="D", ms=4, color="black", mfc="white",
                elinewidth=1.2, capsize=3, capthick=1.2)
    ax.set_xlim(-1.5, K + 4); ax.set_xticks([])
    ax.set_xlabel("Arrays, ordered by paired difference")
    ax.text(0, 1.02, LABEL[m], transform=ax.transAxes, va="bottom", fontsize=9)
axes[0].set_ylabel("Self-prediction advantage\n|auditor − actual| − |self − actual|")
fig.tight_layout(); save(fig, "fig2_paired_error")

# Fig 3 PLAY/PASS
fig, axes = plt.subplots(1, 2, figsize=(5.5, 3.2), sharex=True, sharey=True)
for ax, m in zip(axes, MODEL):
    d = D[m]; y, p, n, A = d["y"], d["PPm"], d["PPn"], d["Am"]
    k = p * n; z = 1.96
    den = 1 + z * z / n; cen = (p + z * z / (2 * n)) / den
    hw = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    ax.errorbar(y, p, yerr=[p - (cen - hw), (cen + hw) - p], fmt="none", ecolor="0.6", elinewidth=.5, capsize=1.2, zorder=1)
    sc = ax.scatter(y, p, c=A, cmap="cividis", vmin=0, vmax=1, s=16, edgecolor="black", linewidths=.4, zorder=3)
    xs = np.linspace(y.min(), 1, 60)
    b = logit_glm(p, n, [y]); ax.plot(xs, 1 / (1 + np.exp(-(b[0] + b[1] * xs))), color="black", lw=.9, zorder=2)
    bt = BT[m]; curves = []
    for bb in range(0, B, 4):
        try:
            q = logit_glm(bt["P"][bb], np.full(K, n.mean()), [bt["y"][bb]])
            curves.append(1 / (1 + np.exp(-(q[0] + q[1] * xs))))
        except Exception:
            pass
    for qq in (.025, .975):
        ax.plot(xs, np.quantile(curves, qq, axis=0), color="black", ls=":", lw=.6, zorder=2)
    ax.set_ylim(-.03, 1.03); ax.set_xlabel("Measured matching probability")
    ax.text(0, 1.02, LABEL[m], transform=ax.transAxes, va="bottom", fontsize=9)
axes[0].set_ylabel("Proportion choosing PLAY")
cb = fig.colorbar(sc, ax=axes, fraction=.035, pad=.02); cb.set_label("Auditor-predicted matching probability", fontsize=8)
cb.outline.set_linewidth(.5)
save(fig, "fig3_playpass")

# Fig S3 old vs corrected (separate, descriptive)
fig, axes = plt.subplots(1, 2, figsize=(5.5, 3.2), sharex=True, sharey=True)
for ax, m in zip(axes, MODEL):
    on, oldp = D[m]["old"]; newp = D[m]["PPm"][on]
    for i, (a_, b_) in enumerate(zip(oldp, newp)):
        ax.plot([0, 1], [a_, b_], color="0.75", lw=.5)
    hi = [old_lab[m][ARR[i]] == "HIGH" for i in on]
    for flag, mk, fc, lab in ((True, "o", "black", "Old HIGH"), (False, "s", "white", "Old LOW")):
        sel = np.array(hi) == flag
        dx = -.05 if flag else .05
        ax.scatter(np.r_[np.zeros(sel.sum()), np.ones(sel.sum())] + dx, np.r_[oldp[sel], newp[sel]], marker=mk,
                   facecolor=fc, edgecolor="black", s=14, zorder=3, label=lab)
    ax.set_xticks([0, 1]); ax.set_xticklabels(["Old wording", "Corrected"]); ax.set_xlim(-.3, 1.3)
    ax.text(0, 1.02, LABEL[m], transform=ax.transAxes, va="bottom", fontsize=9)
axes[0].set_ylabel("Proportion choosing PLAY")
axes[1].legend(frameon=False, fontsize=8, loc="upper left", bbox_to_anchor=(1.0, 1.0))
fig.tight_layout(rect=(0, 0, .88, 1)); save(fig, "figS3_old_vs_corrected")
print(json.dumps(R, indent=1, default=float))
