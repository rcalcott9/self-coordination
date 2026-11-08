"""
Reader-facing redesign of the Stage C figures.

VISUALISATION ONLY. Same data, same analysis, same approved pairs. Nothing is
recomputed except pooled attempt counts (a sum of numbers already in
attempt_rates.csv) and closed-form Wilson / Newcombe display intervals.

The hero figure is laid out as the argument itself: one row per approved pair,
three columns that read left to right as

    publicly similar  ->  own policy very different  ->  betting follows own policy

Consistent encoding everywhere: HIGH self-coordination stimulus = filled dark
circle; LOW = open light circle. One legend per figure. No raw column names, no
stimulus IDs as primary axis labels.

Run:  python3 hero_figures.py
"""
import csv, math, os
import psc_common as P

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
    "font.size": 9, "axes.labelsize": 9,
    "xtick.labelsize": 8, "ytick.labelsize": 8, "legend.fontsize": 8,
    "axes.linewidth": 0.8, "axes.edgecolor": "black", "text.color": "black",
    "axes.spines.top": False, "axes.spines.right": False,
    "xtick.direction": "out", "ytick.direction": "out",
    "axes.grid": False, "legend.frameon": False,
    "figure.facecolor": "white", "axes.facecolor": "white",
    "figure.dpi": 300, "savefig.dpi": 300, "savefig.bbox": "tight",
})

HIGH = dict(marker="o", markerfacecolor="black", markeredgecolor="black",
            markersize=7, linestyle="none", markeredgewidth=0.9)
LOW = dict(marker="o", markerfacecolor="white", markeredgecolor="black",
           markersize=7, linestyle="none", markeredgewidth=0.9)
HIGH_S = {**HIGH, "markersize": 5.5}
LOW_S = {**LOW, "markersize": 5.5}
LINK = dict(color="0.45", linewidth=1.0, zorder=1, solid_capstyle="round")
EB = dict(elinewidth=0.8, capsize=2.5, capthick=0.8, ecolor="black")
SAFES = [3, 5, 7, 9]

# Row order is fixed by the brief.
# Canonical row order. Defaults to the original 5.5/Opus-5 approved set so the Aug-12
# figures reproduce byte-for-byte. Under a replication env (PSC_EXP_DIR), the approved
# set is read from pairs/approved_pairs.csv and pair_kind is derived from the measured
# form consistency of both members, not hard-coded.
ORDER_ORIGINAL = [("gpt", "c_contr_subtle", "b_spiral_cw", "both form-based"),
                  ("gpt", "s_convexity", "d_dens_extreme", "form-rule vs fallback"),
                  ("gpt", "c_open_cplx", "s_density", "form-rule vs fallback"),
                  ("claude", "b_spiral_cw", "rot", "form-rule vs fallback"),
                  ("claude", "s_convexity", "d_dens_extreme", "form-rule vs fallback")]


def _order():
    ap = os.path.join(P.EXP, "pairs", "approved_pairs.csv")
    if not os.path.exists(ap):
        return ORDER_ORIGINAL
    rows = list(csv.DictReader(open(ap)))
    def kind(r):
        try:
            hi = float(r["form_consistency_high"]); lo = float(r["form_consistency_low"])
        except (KeyError, ValueError):
            return "form-rule vs fallback"
        return "both form-based" if hi >= P.FC_CLEAN and lo >= P.FC_CLEAN \
            else "form-rule vs fallback"
    # GPT rows first, then Claude - matching the original figure's model blocking
    rows.sort(key=lambda r: (r["focal_model"] != "gpt", r["pair_id"]))
    return [(r["focal_model"], r["stimulus_high"], r["stimulus_low"], kind(r)) for r in rows]


ORDER = _order()
_NGPT = sum(1 for o in ORDER if o[0] == "gpt")


def wilson(k, n, z=1.959964):
    if not n:
        return float("nan"), float("nan")
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = (z / d) * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return max(0.0, c - h), min(1.0, c + h)


def newcombe(k1, n1, k2, n2):
    p1, p2 = k1 / n1, k2 / n2
    l1, u1 = wilson(k1, n1); l2, u2 = wilson(k2, n2)
    d = p1 - p2
    return (d, d - math.sqrt((p1 - l1) ** 2 + (u2 - p2) ** 2),
            d + math.sqrt((u1 - p1) ** 2 + (p2 - l2) ** 2))


def load():
    D = P.DATA
    mp = {r["pair_id"]: r for r in
          csv.DictReader(open(os.path.join(P.EXP, "matched_pairs.csv")))
          if str(r.get("approved", "")).lower() in ("true", "1", "yes")}
    joint = {r["pair_id"]: r for r in
             csv.DictReader(open(os.path.join(D, "matched_pair_joint.csv")))}
    cell = {(r["model"], r["stimulus"], int(r["safe_payoff"])): r
            for r in csv.DictReader(open(os.path.join(D, "attempt_rates.csv")))}
    fresh = {(r["model"], r["stimulus"]): r
             for r in csv.DictReader(open(os.path.join(D, "fresh_self_match.csv")))}
    aud = {(r["focal_model"], r["stimulus"]): r
           for r in csv.DictReader(open(os.path.join(D, "auditor_predictions.csv")))}
    sal = {r["stimulus"]: r for r in
           csv.DictReader(open(os.path.join(D, "salience_ratings.csv")))
           if r["rater_model"] == "pooled"}

    rows = []
    for i, (m, hi, lo, kind) in enumerate(ORDER, start=1):
        pid = f"{m}__{hi}__vs__{lo}"
        if pid not in mp:
            raise SystemExit(f"approved pair missing: {pid}")
        j = joint.get(pid, {})

        def pool(sid):
            k = sum(int(cell[(m, sid, s)]["n_attempt"]) for s in SAFES)
            n = sum(int(cell[(m, sid, s)]["n"]) for s in SAFES)
            return k, n
        kh, nh = pool(hi); kl, nl = pool(lo)
        d, dlo, dhi = newcombe(kh, nh, kl, nl)
        f = lambda dct, key: float(dct[key])
        rows.append(dict(
            n=i, model=m, model_name=P.DISPLAY[m], hi=hi, lo=lo, kind=kind,
            sal_hi=f(sal[hi], "salience_holdout"), sal_lo=f(sal[lo], "salience_holdout"),
            aud_hi=f(aud[(m, hi)], "auditor_holdout"), aud_lo=f(aud[(m, lo)], "auditor_holdout"),
            true_hi=f(fresh[(m, hi)], "self_match_holdout"),
            true_lo=f(fresh[(m, lo)], "self_match_holdout"),
            p_hi=kh / nh, p_lo=kl / nl,
            p_hi_ci=wilson(kh, nh), p_lo_ci=wilson(kl, nl),
            dpool=d, dlo=dlo, dhi=dhi,
            perm_p=float(j["perm_p_one_sided"]) if j else float("nan"),
            curve={s: (cell[(m, hi, s)], cell[(m, lo, s)]) for s in SAFES},
        ))
    return rows


def save(fig, stem, note):
    os.makedirs(P.VIZ, exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(P.VIZ, f"{stem}.{ext}"), facecolor="white")
    plt.close(fig)
    print(f"\n{'=' * 76}\n{stem}.png / .pdf\n{'=' * 76}\n{note.strip()}")


# =============================================================== HERO ==========
def hero(rows):
    fig, axes = plt.subplots(1, 3, figsize=(8.4, 5.3), sharey=True,
                             gridspec_kw={"width_ratios": [1.05, 1.0, 1.15],
                                          "wspace": 0.16})
    yy = {r["n"]: (r["n"] - 1) + (0.85 if r["n"] >= 4 else 0.0) for r in rows}
    for ax in axes:
        ax.set_ylim(-1.25, 5.45)
        ax.invert_yaxis()
        ax.set_xlim(-0.04, 1.06)
        ax.set_xticks([0, 0.5, 1.0])
        ax.set_yticks([])
        ax.spines["left"].set_visible(False)
        ax.axhline(_NGPT + 0.28, color="0.75", linewidth=0.8)  # model divider

    # ---- column 1: public measures, actual values ----
    ax = axes[0]
    for r in rows:
        y = yy[r["n"]]
        for off, key_hi, key_lo in ((-0.17, "sal_hi", "sal_lo"), (0.17, "aud_hi", "aud_lo")):
            ax.plot([r[key_lo], r[key_hi]], [y + off] * 2, **LINK)
            # HIGH first, then LOW as an UNFILLED ring on top. Where the two values
            # coincide - which is the whole point of this column - the result reads
            # as a ring around a dot rather than one marker hiding the other.
            ax.plot([r[key_hi]], [y + off], **{**HIGH_S, "zorder": 3})
            ax.plot([r[key_lo]], [y + off],
                    **{**LOW_S, "markerfacecolor": "none", "markersize": 7.5,
                       "zorder": 4})
    ax.text(0.0, -0.95, "upper row: generic salience", fontsize=6.6, color="0.3",
            va="center", ha="left")
    ax.text(0.0, -0.70, "lower row: external-model prediction", fontsize=6.6, color="0.3",
            va="center", ha="left")
    ax.text(0.0, -0.45, "ring around a dot = the two values coincide", fontsize=6.0,
            color="0.45", va="center", ha="left", style="italic")
    ax.set_title("Looks similarly coordinable\nfrom outside", fontsize=9.5, pad=10)
    ax.set_xlabel("probability")

    # ---- column 2: own-copy coordination ----
    ax = axes[1]
    for r in rows:
        y = yy[r["n"]]
        ax.plot([r["true_lo"], r["true_hi"]], [y] * 2, color="0.25", linewidth=2.2,
                zorder=1, solid_capstyle="round")
        ax.plot([r["true_lo"]], [y], **LOW)
        ax.plot([r["true_hi"]], [y], **HIGH)
        ax.text(r["true_lo"] - 0.055, y, f"{r['true_lo']:.2f}", fontsize=7.4,
                va="center", ha="right")
        ax.text(r["true_hi"] + 0.055, y, f"{r['true_hi']:.2f}", fontsize=7.4,
                va="center", ha="left", fontweight="bold")
    ax.set_title("But own-copy coordination\ndiffers", fontsize=9.5, pad=10)
    ax.set_xlabel("own-copy match probability")

    # ---- column 3: betting ----
    ax = axes[2]
    for r in rows:
        y = yy[r["n"]]
        ax.plot([r["p_lo"], r["p_hi"]], [y] * 2, **LINK)
        for val, ci, sty in ((r["p_lo"], r["p_lo_ci"], LOW), (r["p_hi"], r["p_hi_ci"], HIGH)):
            ax.errorbar([val], [y], xerr=[[val - ci[0]], [ci[1] - val]], **EB, zorder=2)
            ax.plot([val], [y], **sty, zorder=3)
        pv = "p < 0.001" if r["perm_p"] <= 0.0005 else f"p = {r['perm_p']:.3f}"
        ax.text(1.045, y - 0.30,
                f"$\\Delta$ = {r['dpool']:+.2f}  [{r['dlo']:+.2f}, {r['dhi']:+.2f}]",
                fontsize=6.6, va="center", ha="right")
        ax.text(1.045, y + 0.30, pv, fontsize=6.6, va="center", ha="right", color="0.35")
    ax.set_title("Model bets more on\nthe reliable one", fontsize=9.5, pad=10)
    ax.set_xlabel("P(attempt coordination)")

    # ---- row labels ----
    lab = axes[0]
    tr = lab.get_yaxis_transform()
    for r in rows:
        y = yy[r["n"]]
        lab.text(-0.06, y - 0.16, f"Pair {r['n']}", transform=tr, fontsize=9.5,
                 fontweight="bold", va="center", ha="right")
        lab.text(-0.06, y + 0.15, f"{r['hi']} vs {r['lo']}", transform=tr,
                 fontsize=6.1, va="center", ha="right", color="0.4")
    lab.text(-0.06, -1.02, P.DISPLAY["gpt"], transform=tr, fontsize=9, va="center",
             ha="right", fontweight="bold", color="0.15")
    lab.text(-0.06, _NGPT + 0.06, P.DISPLAY["claude"], transform=tr, fontsize=9, va="center",
             ha="right", fontweight="bold", color="0.15")

    handles = [Line2D([], [], **HIGH, label="higher own-copy match"),
               Line2D([], [], **LOW, label="lower own-copy match")]
    fig.legend(handles=handles, loc="lower center", ncol=2, bbox_to_anchor=(0.57, -0.045),
               fontsize=8.5)
    _npos = sum(1 for r in rows if r["p_hi"] > r["p_lo"])
    _title = ("Models selectively bet on situations where their own copies coordinate better"
              if _npos == len(rows) else
              f"Betting follows own-copy reliability in {_npos} of {len(rows)} matched pairs")
    fig.suptitle(_title,
                 fontsize=11.5, y=1.075, x=0.57)
    fig.text(0.57, 1.028, "Matched stimuli look similarly coordinable to outsiders but "
             "differ in own-copy reliability", ha="center", fontsize=9)
    save(fig, "hero_matched_pairs", """
WHAT TO NOTICE. Read each row left to right. Column 1: the two stimuli sit almost on
top of each other on both outside-observer measures - a generic salience rating and
an external model's prediction of the focal model's own reliability. Column 2: the
same two stimuli are far apart in how well the focal model's own copies actually
coordinate (values printed). Column 3: the model attempts more often on the one its
own copies handle better, in every row.
CLAIM SUPPORTED. Willingness to enter a self-coordination game tracks the model's own
policy reliability, not how coordinable the stimulus looks from outside.
NOT ESTABLISHED. No mechanism. This does not show introspective access or privileged
self-knowledge - a learned self-model produces the same pattern. Column 1 shows that
these two particular outside measures fail to separate the pair, not that no external
route could. Pair 3's difference is small and its interval includes zero. Column 3
error bars are Wilson display intervals; the inferential quantity is the printed
permutation p from the pre-specified per-pair joint test.
""")


# ====================================================== SUPPLEMENTARY 1 ========
def supp_curves(rows):
    # Exemplars: the largest-effect pair for each model. Previously hard-coded to the
    # original 5.5/Opus-5 stimulus names, which silently produced an EMPTY figure on any
    # other pair set rather than failing.
    want = []
    for m in ("gpt", "claude"):
        sub = [r for r in rows if r["model"] == m]
        if sub:
            want.append(max(sub, key=lambda r: r["dpool"]))
    if not want:
        raise SystemExit("supp_curves: no pairs available")
    fig, axes = plt.subplots(1, 2, figsize=(6.6, 3.1), sharey=True)
    for ax, r, tag in zip(axes, want, ("A", "B")):
        for which, sty, ls in (("hi", HIGH, "-"), ("lo", LOW, "--")):
            xs, ys, lo, hi = [], [], [], []
            for s in SAFES:
                c = r["curve"][s][0 if which == "hi" else 1]
                k, n = int(c["n_attempt"]), int(c["n"])
                p = k / n; l, u = wilson(k, n)
                xs.append(s); ys.append(p); lo.append(p - l); hi.append(u - p)
            ax.errorbar(xs, ys, yerr=[lo, hi], color="black", linestyle=ls,
                        linewidth=1.2, **EB)
            ax.plot(xs, ys, **{**sty, "markersize": 6})
        ax.set_xticks(SAFES); ax.set_ylim(-0.03, 1.05); ax.set_xlim(2.4, 9.6)
        ax.set_xlabel("safe payoff (points offered to walk away)")
        ax.set_title(f"{tag}   {r['model_name']}", fontsize=9, loc="left")
        ax.text(0.03, 0.06, f"{r['hi']} vs {r['lo']}", transform=ax.transAxes,
                fontsize=6.2, color="0.35")
    axes[0].set_ylabel("P(attempt coordination)")
    handles = [Line2D([], [], color="black", linestyle="-", **{k: v for k, v in HIGH.items()
                      if k != "linestyle"}, label="higher own-copy match"),
               Line2D([], [], color="black", linestyle="--", **{k: v for k, v in LOW.items()
                      if k != "linestyle"}, label="lower own-copy match")]
    fig.legend(handles=handles, loc="upper center", ncol=2, bbox_to_anchor=(0.5, 1.005),
               fontsize=8)
    fig.suptitle("Betting diverges as the cost of attempting coordination rises",
                 fontsize=11, y=1.13)
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    save(fig, "supp_exemplar_payoff_curves", """
WHAT TO NOTICE. At a safe payoff of 3 both stimuli are always attempted - entering is
worth it either way, so behaviour is identical. The two lines separate only as the
outside option becomes competitive (7 and 9), and they separate in the direction of
own-copy reliability. One pair per model is shown (the largest effect for that model); the remaining
pairs are in the forest summary.
CLAIM SUPPORTED. The effect is a response to consequence, not a standing preference
for one stimulus: it appears exactly where choosing wrongly starts to cost points.
NOT ESTABLISHED. That the models compute expected value. Observed points only, no
smoothing or fitted curve; two exemplar pairs shown, the rest are in the forest
summary. Exemplars are the per-model maxima, so they are not representative by
construction - read the forest for the spread.
""")


# ====================================================== SUPPLEMENTARY 2 ========
def supp_forest(rows):
    fig, ax = plt.subplots(figsize=(6.3, 3.0))
    yy = {r["n"]: (r["n"] - 1) + (0.35 if r["n"] >= 4 else 0.0) for r in rows}
    for r in rows:
        y = yy[r["n"]]
        ax.errorbar([r["dpool"]], [y],
                    xerr=[[r["dpool"] - r["dlo"]], [r["dhi"] - r["dpool"]]], **EB)
        ax.plot([r["dpool"]], [y], **{**HIGH, "markersize": 7})
    ax.axvline(0, color="black", linewidth=0.9, linestyle=":")
    ax.axhline(_NGPT + 0.18, color="0.75", linewidth=0.8)
    ax.set_ylim(-0.7, 4.75); ax.invert_yaxis()
    ax.set_xlim(-0.06, 0.36)
    ax.set_yticks([yy[r["n"]] for r in rows])
    ax.set_yticklabels([f"Pair {r['n']}" for r in rows], fontsize=8.5)
    ax.set_xlabel("$\\Delta$P(attempt), higher minus lower own-copy coordination")
    tr = ax.get_yaxis_transform()
    ax.text(-0.115, -0.55, P.DISPLAY["gpt"], transform=tr, fontsize=7.5, va="center",
            ha="right", color="0.2", fontweight="bold")
    ax.text(-0.115, _NGPT + 0.32, P.DISPLAY["claude"], transform=tr, fontsize=7.5, va="center",
            ha="right", color="0.2", fontweight="bold")
    _np = sum(1 for r in rows if r["dpool"] > 0)
    fig.suptitle(f"{_np} of {len(rows)} matched pairs favour the higher-reliability stimulus",
                 fontsize=11, y=1.04)
    fig.tight_layout()
    save(fig, "supp_forest_summary", """
WHAT TO NOTICE. Where each pair's interval sits relative to zero, across both models.
Point size is not meaningful; only position and interval width are.
CLAIM SUPPORTED. Whether the direction is consistent across the approved pairs, i.e.
whether the result rests on a single favourable comparison. Count the points right of
zero rather than reading the pooled effect off this figure.
NOT ESTABLISHED. Significance. These are Newcombe display intervals, not the
pre-specified inference; the per-pair permutation test is the inferential quantity, and
the pooled cluster-bootstrap delta is the pre-specified primary. Five pairs from one
battery is also not a population estimate.
""")


def main():
    rows = load()
    print("approved pairs, in brief order:")
    for r in rows:
        print(f"  Pair {r['n']}  {r['model_name']:14}{r['hi']:15}vs {r['lo']:16}"
              f"true {r['true_hi']:.2f}/{r['true_lo']:.2f}  "
              f"P(att) {r['p_hi']:.2f}/{r['p_lo']:.2f}  [{r['kind']}]")
    hero(rows); supp_curves(rows); supp_forest(rows)


if __name__ == "__main__":
    main()
