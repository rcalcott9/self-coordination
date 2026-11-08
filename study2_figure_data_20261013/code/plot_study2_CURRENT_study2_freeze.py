#!/usr/bin/env python3
"""Study 2 freeze (no API calls): PLAY/PASS policy class x partner 2x2 per model, and relational G.
Primary cells only in the figure; exploratory configurations are tabulated and labelled.
Primary: GPT-5.5 effort low; Claude Opus 5 adaptive effort low; Qwen step-316 thinking off,
PI-approved symmetric-wording run s2_20260912_181428 (run B). Run A (pp2x2_20260912_173541) is a
separate earlier run with different partner wording, reported separately.
Interaction = partner shift (COPY - DIFFERENT) on LOW items minus on HIGH items; Qwen's frozen report states
the same quantity with the opposite sign (policy effect COPY - DIFFERENT = -.059)."""
import json
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib.pyplot as plt
plt.style.use("academic")
HERE = Path(__file__).resolve().parent.parent
SC = Path.home() / "Desktop/Coordination/Self_Coordination"; ST = Path.home() / "Desktop/Superrationality/Stag"
SEED, NB = 20261010, 10000
rng = np.random.default_rng(SEED)

# ---------- load PLAY/PASS trials: columns model, config, status, partner, cls (HIGH/LOW), item, play ----------
T = []
G = SC / "study_playpass_gpt/data"
for eff, part, fn in (("effort low", "COPY", "playpass_full_20260912_191607.csv"),
                      ("effort low", "DIFFERENT", "playpass_full_different_low_20260912_195055.csv"),
                      ("effort high", "COPY", "playpass_full_high_20260912_194050.csv"),
                      ("effort high", "DIFFERENT", "playpass_full_different_high_20260912_210001.csv")):
    t = pd.read_csv(G / fn); t = t[t.parse_ok == 1]
    T.append(pd.DataFrame(dict(model="GPT-5.5", config=eff, partner=part, cls=t.arm, item=t.array,
                               play=(t.decision == "PLAY").astype(int))))
O = pd.read_csv(ST / "opus_playpass/results/opus_2x2_clean.csv")
T.append(pd.DataFrame(dict(model="Claude Opus 5", config="adaptive, effort " + O.effort, partner=O.partner,
                           cls=O.group, item=O.item, play=O.play)))
q = [json.loads(l) for l in open(ST / "plunkett_qwen/results/s2_20260912_181428/raw/s2_trials.jsonl")]
q = pd.DataFrame(q); q = q[q.decision.isin(["PLAY", "PASS"])]
T.append(pd.DataFrame(dict(model="Qwen step-316", config="thinking off", partner=q.partner,
                           cls=np.where(q.arm == "PLAY_correct", "HIGH", "LOW"), item=q.scenario,
                           play=(q.decision == "PLAY").astype(int))))
T = pd.concat(T, ignore_index=True)
PRIMARY = {("GPT-5.5", "effort low"), ("Claude Opus 5", "adaptive, effort low"), ("Qwen step-316", "thinking off")}
T["status"] = [("frozen primary" if (m, c) in PRIMARY else "exploratory") for m, c in zip(T.model, T.config)]


# Estimator as frozen: cell P(PLAY) pools trials (item means weighted by trial count); items are the
# resampling unit (item-cluster bootstrap within class). For GPT/Opus every item has 20 trials per cell.
P = lambda X: X[:, 0].sum() / X[:, 1].sum()          # X rows: [k_play, n] per item
CONTRASTS = {
    "partner shift, all items": lambda h, l: P(np.r_[h[:, :2], l[:, :2]]) - P(np.r_[h[:, 2:], l[:, 2:]]),
    "partner shift, HIGH items": lambda h, l: P(h[:, :2]) - P(h[:, 2:]),
    "partner shift, LOW items": lambda h, l: P(l[:, :2]) - P(l[:, 2:]),
    "policy effect (HIGH-LOW), COPY": lambda h, l: P(h[:, :2]) - P(l[:, :2]),
    "policy effect (HIGH-LOW), DIFFERENT": lambda h, l: P(h[:, 2:]) - P(l[:, 2:]),
    "interaction (LOW shift - HIGH shift)": lambda h, l: (P(l[:, :2]) - P(l[:, 2:])) - (P(h[:, :2]) - P(h[:, 2:])),
}
cells, contrasts = [], []
for (m, c), d in T.groupby(["model", "config"], sort=False):
    st = d.status.iloc[0]
    for (cls, part), g in d.groupby(["cls", "partner"]):
        X = g.groupby("item").play.agg(["sum", "size"]).values.astype(float)
        bs = [P(X[rng.integers(0, len(X), len(X))]) for _ in range(NB)]
        cells.append(dict(model=m, config=c, status=st, cls=cls, partner=part, n_items=len(X), n_trials=int(X[:, 1].sum()),
                          p_play=float(P(X)), ci_lo=float(np.quantile(bs, .025)), ci_hi=float(np.quantile(bs, .975))))
    W = d.groupby(["cls", "item", "partner"]).play.agg(["sum", "size"]).unstack("partner")
    if W.shape[1] < 4:
        continue  # single-partner configuration (none at present)
    W = W.dropna()
    M = {k: np.c_[W.loc[k][("sum", "COPY")], W.loc[k][("size", "COPY")], W.loc[k][("sum", "DIFFERENT")],
                  W.loc[k][("size", "DIFFERENT")]].astype(float) for k in ("HIGH", "LOW")}
    h, l = M["HIGH"], M["LOW"]
    for name, f in CONTRASTS.items():
        est = float(f(h, l))
        bs = [f(h[rng.integers(0, len(h), len(h))], l[rng.integers(0, len(l), len(l))]) for _ in range(NB)]
        if name.startswith("partner shift"):  # sign-flip: swap COPY/DIFFERENT within resampled-sign items
            cnt = 0
            for _ in range(NB):
                fh = rng.random(len(h)) < .5; fl = rng.random(len(l)) < .5
                hh = h.copy(); hh[fh] = hh[fh][:, [2, 3, 0, 1]]; ll = l.copy(); ll[fl] = ll[fl][:, [2, 3, 0, 1]]
                cnt += abs(f(hh, ll)) >= abs(est) - 1e-12
            test = "item sign-flip (COPY/DIFFERENT swapped within item)"
        else:  # class-label permutation
            pool = np.r_[h, l]; k = len(h); cnt = 0
            for _ in range(NB):
                pr = pool[rng.permutation(len(pool))]; cnt += abs(f(pr[:k], pr[k:])) >= abs(est) - 1e-12
            test = "class-label permutation"
        contrasts.append(dict(model=m, config=c, status=st, contrast=name, n_high=len(h), n_low=len(l), estimate=est,
                              ci_lo=float(np.quantile(bs, .025)), ci_hi=float(np.quantile(bs, .975)),
                              p=float((cnt + 1) / (NB + 1)), test=test))
cells = pd.DataFrame(cells); contrasts = pd.DataFrame(contrasts)

# ---------- reproduction checks against frozen reports ----------
chk = contrasts.set_index(["model", "config", "contrast"]).estimate
checks = {"GPT partner shift +.140": chk[("GPT-5.5", "effort low", "partner shift, all items")],
          "GPT interaction +.0733": chk[("GPT-5.5", "effort low", "interaction (LOW shift - HIGH shift)")],
          "Opus adaptive-low partner +.155": chk[("Claude Opus 5", "adaptive, effort low", "partner shift, all items")],
          "Qwen partner +.155": chk[("Qwen step-316", "thinking off", "partner shift, all items")],
          "Qwen policy COPY +.133": chk[("Qwen step-316", "thinking off", "policy effect (HIGH-LOW), COPY")],
          "Qwen policy DIFFERENT +.193": chk[("Qwen step-316", "thinking off", "policy effect (HIGH-LOW), DIFFERENT")]}
target = dict(zip(checks, [.140, .0733, .155, .155, .133, .193]))
checks["Qwen interaction (frozen -.059, sign flipped)"] = chk[("Qwen step-316", "thinking off", "interaction (LOW shift - HIGH shift)")]
target["Qwen interaction (frozen -.059, sign flipped)"] = .059
for k, v in checks.items():
    assert abs(v - target[k]) < .0015, (k, v)

# ---------- relational G (study2_relational_prediction_20260912, run_20260912_154308) ----------
R = pd.DataFrame(json.load(open(SC / "study2_relational_prediction_20260912/results/run_20260912_154308/report_rows.json")))
Rg = []
for foc, d in R.groupby("focal", sort=False):
    x = d.G.values; fam = d.groupby("family").G.mean().values
    for unit, v in (("items", x), ("families (F10 collapsed)", fam)):
        bs = [v[rng.integers(0, len(v), len(v))].mean() for _ in range(NB)]
        Rg.append(dict(focal={"gpt": "GPT-5.5", "claude": "Claude Opus 5", "opus": "Claude Opus 5"}.get(foc, foc),
                       unit=unit, n=len(v), G=float(v.mean()), ci_lo=float(np.quantile(bs, .025)),
                       ci_hi=float(np.quantile(bs, .975)), n_pos=int((v > 0).sum())))
Rg = pd.DataFrame(Rg)
assert abs(Rg.query("unit=='items'").G.values[0] - .0206) < 5e-4

(HERE / "tables").mkdir(exist_ok=True)
T.to_csv(HERE / "tables/study2_playpass_trials.csv", index=False)  # input to study2_logit_interaction.R
cells.to_csv(HERE / "tables/study2_playpass_cells.csv", index=False)
contrasts.to_csv(HERE / "tables/study2_playpass_contrasts.csv", index=False)
R.to_csv(HERE / "tables/study2_relational_G_items.csv", index=False)
Rg.to_csv(HERE / "tables/study2_relational_G_summary.csv", index=False)

# ---------- figure: a-c interaction plots (primary only), d forest of G ----------
fig, ax = plt.subplots(1, 4, figsize=(6.5, 2.4), gridspec_kw=dict(width_ratios=[1, 1, 1, 1.15]), layout="constrained")
for a, (m, c), lab in zip(ax[:3], [("GPT-5.5", "effort low"), ("Claude Opus 5", "adaptive, effort low"),
                                   ("Qwen step-316", "thinking off")], "abc"):
    d = cells[(cells.model == m) & (cells.config == c)]
    for part, mk, ls, fc, dx in (("COPY", "o", "-", "black", -.04), ("DIFFERENT", "s", "--", "white", .04)):
        e = d[d.partner == part].set_index("cls").loc[["HIGH", "LOW"]]
        xs = np.array([0, 1]) + dx
        a.errorbar(xs, e.p_play, yerr=[e.p_play - e.ci_lo, e.ci_hi - e.p_play], fmt=mk + ls, color="black",
                   mfc=fc, mec="black", ms=4.5, capsize=2, lw=.8, elinewidth=.8, label=part.capitalize())
    a.set_xticks([0, 1]); a.set_xticklabels(["High", "Low"] if m != "Qwen step-316" else ["Clear", "Weak"])
    a.set_xlim(-.4, 1.4); a.set_ylim(0, 1.02)
    a.set_xlabel("Own agreement class"); a.text(.02, 1.0, f"{lab}  {m}", transform=a.transAxes, va="bottom")
    if lab != "a": a.set_yticklabels([])
ax[0].set_ylabel("P(PLAY)"); ax[0].legend(loc="lower left", frameon=False, fontsize=6, handlelength=1.6)
a = ax[3]
for i, (foc, unit, mk) in enumerate([("GPT-5.5", "items", "o"), ("GPT-5.5", "families (F10 collapsed)", "s"),
                                    ("Claude Opus 5", "items", "o"), ("Claude Opus 5", "families (F10 collapsed)", "s")]):
    r = Rg[(Rg.focal == foc) & (Rg.unit == unit)].iloc[0]; y = 3 - i
    a.errorbar(r.G, y, xerr=[[r.G - r.ci_lo], [r.ci_hi - r.G]], fmt=mk, color="black",
               mfc="black" if unit == "items" else "white", ms=4.5, capsize=2, lw=.8)
a.axvline(0, color="black", lw=.6, ls=":")
a.set_yticks([3, 2, 1, 0]); a.set_yticklabels(["GPT items", "GPT fam.", "Opus items", "Opus fam."], fontsize=7)
a.set_xlabel("Gating G"); a.set_ylim(-.6, 3.6); a.set_xlim(-.09, .09)
a.text(.02, 1.0, "d", transform=a.transAxes, va="bottom")
fig.get_layout_engine().set(w_pad=.02, wspace=.06)
(HERE / "figures").mkdir(exist_ok=True)
for ext in ("png", "pdf"): fig.savefig(HERE / f"figures/fig_study2.{ext}", dpi=300)
print(contrasts.round(4).to_string()); print(Rg.round(4).to_string())
print("reproduction checks passed:", {k: round(v, 4) for k, v in checks.items()})
