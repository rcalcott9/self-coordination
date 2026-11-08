"""
2x2 added-variable (partial regression) plot.

Each panel regresses BOTH the outcome and one predictor on the OTHER predictor,
then plots the residuals against each other. The slope of the residual fit is the
partial regression coefficient, and the correlation of the residuals is the partial
correlation - so the panel shows the unique contribution of that predictor with the
other held fixed.

Left column  : own-copy match's unique contribution, cross-match held fixed
Right column : cross-model match's unique contribution, own-match held fixed

Reading it: if entry were driven by how coordinable a stimulus looks to ANY agent,
the right column would carry the signal. If it is driven by the focal model's own
convention, the left column does.

Builds the stimulus-level frame from the Stage C pilot (entry) and Stage A
discovery (own_match, cross_match).
"""
import os, csv, glob
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import s4_common as S

plt.style.use("academic")
ACCENT = "#B4432E"          # the single accent, used only for the fit line
HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(os.path.dirname(HERE), "figures")
os.makedirs(FIG, exist_ok=True)


# ------------------------------------------------- stimulus-level dataframe ---
def build():
    rows = [r for r in csv.DictReader(
        open(os.path.join(S.DATA, "stageC_pilot_results.csv")))
        if r["parse_ok"] == "True"]
    meta = {}
    for f in glob.glob(os.path.join(S.DATA, "cell_metrics_discovery_batch*.csv")):
        for r in csv.DictReader(open(f)):
            meta[(r["stimulus_id"], r["model"])] = r
    out = []
    for focal in ("gpt", "claude"):
        sub = [r for r in rows if r["focal"] == focal]
        for sid in sorted({r["stimulus_id"] for r in sub}):
            m = meta[(sid, focal)]
            out.append(dict(
                model=focal, stimulus_id=sid,
                entry=np.mean([int(r["attempt"]) for r in sub
                               if r["stimulus_id"] == sid]),
                own_match=float(m["self_match"]),
                cross_match=float(m["cross_match"])))
    return out


def resid(y, x):
    """Residuals of y after OLS on [1, x]."""
    X = np.c_[np.ones(len(x)), x]
    return y - X @ np.linalg.lstsq(X, y, rcond=None)[0]


def corr(a, b):
    a, b = np.asarray(a), np.asarray(b)
    da, db = a - a.mean(), b - b.mean()
    d = np.sqrt((da ** 2).sum() * (db ** 2).sum())
    return float((da * db).sum() / d) if d else np.nan


df = build()
with open(os.path.join(S.DATA, "stimulus_level.csv"), "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(df[0].keys()))
    w.writeheader(); w.writerows(df)

# ------------------------------------------------------------------- plot -----
fig, axes = plt.subplots(2, 2, figsize=(5.5, 4.8), sharey="row")
COLS = [("own_match", "cross_match", "own-copy match, cross-match held fixed"),
        ("cross_match", "own_match", "cross-model match, own-match held fixed")]

for i, focal in enumerate(("gpt", "claude")):
    d = [r for r in df if r["model"] == focal]
    entry = np.array([r["entry"] for r in d])
    for j, (target, ctrl, title) in enumerate(COLS):
        ax = axes[i, j]
        xv = np.array([r[target] for r in d])
        cv = np.array([r[ctrl] for r in d])
        rx, ry = resid(xv, cv), resid(entry, cv)

        ax.axhline(0, color="0.85", lw=0.6, zorder=1)
        ax.axvline(0, color="0.85", lw=0.6, zorder=1)
        ax.plot(rx, ry, "o", mfc="none", mec="k", mew=0.9, ms=4.5, lw=0, zorder=3)

        b1, b0 = np.polyfit(rx, ry, 1)
        xs = np.linspace(rx.min(), rx.max(), 50)
        ax.plot(xs, b0 + b1 * xs, "-", color=ACCENT, lw=1.4, zorder=2)

        r = corr(rx, ry)
        ax.text(0.04, 0.94, f"r = {r:+.2f}", transform=ax.transAxes,
                fontsize=8.5, va="top", ha="left")
        if j == 0:
            ax.set_ylabel("entry rate (residual)")
        if i == 0:
            ax.set_title(title, fontsize=8, pad=6)
        if i == 1:
            ax.set_xlabel(f"{target.replace('_', '-')} (residual)")
        ax.text(0.96, 0.06, S.DISPLAY[focal], transform=ax.transAxes,
                fontsize=7.5, ha="right", va="bottom", color="0.35")

fig.tight_layout()
for ext in ("pdf", "png"):
    fig.savefig(os.path.join(FIG, f"added_variable.{ext}"), dpi=300)
print("wrote", os.path.join(FIG, "added_variable.[pdf|png]"))
for focal in ("gpt", "claude"):
    d = [r for r in df if r["model"] == focal]
    e = np.array([r["entry"] for r in d])
    o = np.array([r["own_match"] for r in d])
    c = np.array([r["cross_match"] for r in d])
    print(f"  {focal:7} n={len(d):2d}  own|cross r={corr(resid(o,c), resid(e,c)):+.3f}"
          f"   cross|own r={corr(resid(c,o), resid(e,o)):+.3f}")
