"""
Is the null interaction masked by a ceiling?

If entry is pinned near 1.0 at low safe payoffs, no interaction can express itself
there, and a real beta3 would only appear once the safe payoff pulls entry off the
ceiling. Three tests:

  1. beta3 fitted SEPARATELY at each safe payoff, with a paired permutation test.
  2. A pooled three-way term HIGH x SAME x safe (safe continuous): does the
     interaction grow as the safe payoff rises?
  3. Entry rate per cell at each payoff, so the ceiling is visible beside the
     estimate.

PERMUTATION SCHEME. Paired sign-flip, which is what the pairing licenses: under the
null the gap does not depend on level, so within a pair the HIGH/LOW label is
exchangeable and the pair's interaction may flip sign. With 8 and 7 pairs the
2^n arrangements (256, 128) are enumerated EXACTLY - no sampling error, and the
smallest attainable p is 1/256 = 0.0039 (GPT) and 1/128 = 0.0078 (Claude).

This differs from the pooled test reported earlier, which permuted the HIGH/LOW
label across families and ignored the pairing. Both are reported so the comparison
is visible.
"""
import os, csv, itertools
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import statsmodels.formula.api as smf
import statsmodels.api as sm
import pandas as pd
import s4_common as S

plt.style.use("academic")
ACCENT = "#B4432E"
SEED = 20260831
rng = np.random.default_rng(SEED)
HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(os.path.dirname(HERE), "figures")
os.makedirs(FIG, exist_ok=True)
SAFE = [3, 5, 7, 9]

rows = [r for r in csv.DictReader(
    open(os.path.join(S.DATA, "stageC_pilot_results.csv"))) if r["parse_ok"] == "True"]
df = pd.DataFrame(rows)
df["attempt"] = df["attempt"].astype(int)
df["safe"] = df["safe"].astype(int)
df["same"] = df["partner_same"].astype(int)
df["high"] = (df["level"] == "HIGH").astype(int)
df["is_gpt"] = (df["focal"] == "gpt").astype(int)


def pair_inter(focal, safe=None):
    """Per-pair interaction: gap(HIGH) - gap(LOW). gap = P(att|SAME)-P(att|DIFF)."""
    d = df[df.focal == focal]
    if safe is not None:
        d = d[d.safe == safe]
    out = []
    for pid in sorted(d.pair_id.unique()):
        pr = d[d.pair_id == pid]
        g = {}
        for lev in ("HIGH", "LOW"):
            s = pr[pr.level == lev]
            g[lev] = (s[s["same"] == 1].attempt.mean()
                      - s[s["same"] == 0].attempt.mean())
        out.append(g["HIGH"] - g["LOW"])
    return np.array(out)


def signflip_p(v):
    """Exact paired sign-flip test on the pair-level interactions."""
    obs = v.mean()
    n = len(v)
    signs = np.array(list(itertools.product([-1, 1], repeat=n)))
    stat = (signs * v).mean(axis=1)
    return obs, float((np.abs(stat) >= abs(obs)).mean()), len(signs)


def boot_ci(v, b=10000):
    d = np.sort([rng.choice(v, len(v), replace=True).mean() for _ in range(b)])
    return d[int(.025 * b)], d[int(.975 * b)]


L = []


def p(s=""):
    print(s); L.append(s)


p("=" * 92)
p("1. beta3 AT EACH SAFE PAYOFF  (paired sign-flip, exact enumeration)")
p("=" * 92)
p(f"{'focal':8}{'safe':>6}{'beta3':>9}{'95% CI':>20}{'perm p':>9}{'#perms':>8}"
  f"{'n pairs':>9}")
p("-" * 92)
res = {}
for focal in ("gpt", "claude"):
    for s in SAFE:
        v = pair_inter(focal, s)
        obs, pv, nperm = signflip_p(v)
        lo, hi = boot_ci(v)
        res[(focal, s)] = (obs, lo, hi, pv)
        p(f"{focal:8}{s:>6}{obs:>+9.3f}{f'[{lo:+.3f}, {hi:+.3f}]':>20}"
          f"{pv:>9.4f}{nperm:>8}{len(v):>9}")
    v = pair_inter(focal)
    obs, pv, nperm = signflip_p(v)
    lo, hi = boot_ci(v)
    res[(focal, "all")] = (obs, lo, hi, pv)
    p(f"{focal:8}{'all':>6}{obs:>+9.3f}{f'[{lo:+.3f}, {hi:+.3f}]':>20}"
      f"{pv:>9.4f}{nperm:>8}{len(v):>9}")
p()

p("=" * 92)
p("2. POOLED THREE-WAY:  attempt ~ HIGH * SAME * safe   (safe continuous)")
p("=" * 92)
p(f"{'focal':8}{'term':>22}{'coef (logit)':>14}{'SE':>8}{'95% CI':>22}{'p':>9}")
p("-" * 92)
for focal in ("gpt", "claude"):
    d = df[df.focal == focal].copy()
    d["safe_c"] = d["safe"] - 6.0
    m = smf.glm("attempt ~ high * same * safe_c", data=d,
                family=sm.families.Binomial()).fit(
        cov_type="cluster", cov_kwds={"groups": d["family"]})
    for t in ("high:same", "high:same:safe_c"):
        if t in m.params.index:
            b, se = m.params[t], m.bse[t]
            p(f"{focal:8}{t:>22}{b:>+14.3f}{se:>8.3f}"
              f"{f'[{b-1.96*se:+.3f}, {b+1.96*se:+.3f}]':>22}{m.pvalues[t]:>9.4f}")
p()
p("Risk-difference read: OLS of the four per-payoff beta3 estimates on safe payoff")
p(f"{'focal':8}{'slope/point':>14}{'95% CI':>22}")
p("-" * 92)
for focal in ("gpt", "claude"):
    y = np.array([res[(focal, s)][0] for s in SAFE])
    X = np.c_[np.ones(4), SAFE]
    b = np.linalg.lstsq(X, y, rcond=None)[0]
    resd = y - X @ b
    s2 = (resd ** 2).sum() / 2
    se = np.sqrt(s2 * np.linalg.inv(X.T @ X)[1, 1])
    p(f"{focal:8}{b[1]:>+14.4f}"
      f"{f'[{b[1]-4.303*se:+.4f}, {b[1]+4.303*se:+.4f}]':>22}")
p("  (t crit 4.303 at 2 df; 4 points, so this is descriptive)")
p()

p("=" * 92)
p("3/4. ENTRY RATE PER CELL - where does the ceiling bind?")
p("=" * 92)
p(f"{'focal':8}{'safe':>6}{'HIGH·SAME':>11}{'HIGH·DIFF':>11}{'LOW·SAME':>10}"
  f"{'LOW·DIFF':>10}{'gap HIGH':>10}{'gap LOW':>9}")
p("-" * 92)
cell = {}
for focal in ("gpt", "claude"):
    for s in SAFE:
        d = df[(df.focal == focal) & (df.safe == s)]
        v = {}
        for lev in ("HIGH", "LOW"):
            for sm_ in (1, 0):
                v[(lev, sm_)] = d[(d.level == lev) & (d["same"] == sm_)].attempt.mean()
        cell[(focal, s)] = v
        p(f"{focal:8}{s:>6}{v[('HIGH',1)]:>11.3f}{v[('HIGH',0)]:>11.3f}"
          f"{v[('LOW',1)]:>10.3f}{v[('LOW',0)]:>10.3f}"
          f"{v[('HIGH',1)]-v[('HIGH',0)]:>+10.3f}{v[('LOW',1)]-v[('LOW',0)]:>+9.3f}")
p()
p("HIGH x SAME is the cell the ceiling argument is about:")
for focal in ("gpt", "claude"):
    vals = [cell[(focal, s)][("HIGH", 1)] for s in SAFE]
    p(f"  {S.DISPLAY[focal]:16} " + "  ".join(f"safe={s}: {v:.3f}"
                                              for s, v in zip(SAFE, vals)))
p()

# ------------------------------------------------------------------ plot -----
fig, axes = plt.subplots(2, 2, figsize=(5.5, 4.8), sharex=True)
for j, focal in enumerate(("gpt", "claude")):
    ax = axes[0, j]
    y = [res[(focal, s)][0] for s in SAFE]
    lo = [res[(focal, s)][0] - res[(focal, s)][1] for s in SAFE]
    hi = [res[(focal, s)][2] - res[(focal, s)][0] for s in SAFE]
    ax.axhline(0, color="0.55", lw=0.8, ls=(0, (4, 3)), zorder=1)
    ax.errorbar(SAFE, y, yerr=[lo, hi], fmt="o", mfc="k", mec="k", ms=4.5,
                color="k", lw=0, elinewidth=0.9, capsize=2.5, zorder=3)
    ax.set_ylim(-0.55, 0.55)
    if j == 0:
        ax.set_ylabel(r"interaction $\beta_3$")
    ax.set_title(S.DISPLAY[focal], fontsize=8.5, pad=5)

    ax = axes[1, j]
    for lev, sm_, mk, mfc, ls in (("HIGH", 1, "o", "k", "-"),
                                  ("HIGH", 0, "s", "none", "-"),
                                  ("LOW", 1, "^", ACCENT, "--"),
                                  ("LOW", 0, "v", "none", "--")):
        yy = [cell[(focal, s)][(lev, sm_)] for s in SAFE]
        ax.plot(SAFE, yy, mk, ls=ls, mfc=mfc, mec="k" if mfc != ACCENT else ACCENT,
                mew=0.9, ms=4.2, lw=0.9,
                color="k" if lev == "HIGH" else ACCENT,
                label=f"{lev}·{'SAME' if sm_ else 'DIFF'}")
    ax.set_ylim(-0.03, 1.03)
    ax.set_xticks(SAFE)
    ax.set_xlabel("safe payoff")
    if j == 0:
        ax.set_ylabel("entry rate")
        ax.legend(frameon=False, fontsize=6.5, loc="lower left",
                  handletextpad=0.5, borderaxespad=0.3, labelspacing=0.25)
fig.tight_layout()
for ext in ("pdf", "png"):
    fig.savefig(os.path.join(FIG, f"ceiling_test.{ext}"), dpi=300)
p(f"wrote {os.path.join(FIG, 'ceiling_test.[pdf|png]')}")
open(os.path.join(S.DATA, "ceiling_test.txt"), "w").write("\n".join(L) + "\n")
