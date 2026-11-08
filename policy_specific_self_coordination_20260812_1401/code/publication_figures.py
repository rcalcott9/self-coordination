"""
Publication figures for the Stage C policy-specific self-coordination result.

VISUALISATION ONLY. No API calls, no analysis changes. Every number plotted is read
from the existing Stage A/B/C outputs; the only computation performed here is
(a) pooling attempt counts across payoffs, which is a sum of numbers already in
attempt_rates.csv, and (b) closed-form Wilson / Newcombe DISPLAY intervals.

Why Wilson rather than the stored bootstrap ci_lo/ci_hi: several Stage C cells sit
at 0/30 or 30/30, where a nonparametric bootstrap of a proportion is degenerate and
returns a zero-width interval. Plotting those would draw points with no visible
uncertainty exactly where uncertainty is least well determined. Wilson is closed
form and behaves correctly at the boundary. The inferential result is unchanged and
untouched: it remains the pre-specified per-pair permutation test.

Pair descriptions use FRESH Stage A classifications. The old manifest labels are not
used - 12 of 15 stimuli classify differently on GPT-5.5 / Claude Opus 5.

Run:  python3 publication_figures.py
"""
import csv, math, os
from collections import defaultdict
import psc_common as P

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Rectangle, Patch

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
    "font.size": 9, "axes.labelsize": 9, "axes.titlesize": 9,
    "xtick.labelsize": 8, "ytick.labelsize": 8, "legend.fontsize": 8,
    "axes.linewidth": 0.8, "axes.edgecolor": "black", "text.color": "black",
    "axes.spines.top": False, "axes.spines.right": False,
    "xtick.direction": "out", "ytick.direction": "out",
    "xtick.major.width": 0.8, "ytick.major.width": 0.8,
    "axes.grid": False, "legend.frameon": False,
    "figure.facecolor": "white", "axes.facecolor": "white",
    "figure.dpi": 300, "savefig.dpi": 300, "savefig.bbox": "tight",
})

VIZ = P.VIZ
HI_STY = dict(marker="o", markerfacecolor="black", markeredgecolor="black",
              linestyle="-", color="black", markersize=4, linewidth=1.1)
LO_STY = dict(marker="s", markerfacecolor="white", markeredgecolor="black",
              linestyle="--", color="black", markersize=4, linewidth=1.1)
EB = dict(elinewidth=0.7, capsize=2, capthick=0.7, ecolor="black")
HI_FILL = dict(facecolor="0.25", edgecolor="black", linewidth=0.8)
LO_FILL = dict(facecolor="white", edgecolor="black", linewidth=0.8, hatch="////")

SAFES = [3, 5, 7, 9]
NOTES = []


# ----------------------------------------------------------------- intervals --
def wilson(k, n, z=1.959964):
    if not n:
        return float("nan"), float("nan")
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = (z / d) * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return max(0.0, c - h), min(1.0, c + h)


def newcombe(k1, n1, k2, n2):
    """Newcombe hybrid-score CI for a difference of proportions (display only)."""
    p1, p2 = k1 / n1, k2 / n2
    l1, u1 = wilson(k1, n1)
    l2, u2 = wilson(k2, n2)
    d = p1 - p2
    lo = d - math.sqrt((p1 - l1) ** 2 + (u2 - p2) ** 2)
    hi = d + math.sqrt((u1 - p1) ** 2 + (p2 - l2) ** 2)
    return d, lo, hi


# --------------------------------------------------------------------- data ---
def load():
    D = P.DATA
    approved = [r for r in csv.DictReader(open(os.path.join(P.EXP, "matched_pairs.csv")))
                if str(r.get("approved", "")).lower() in ("true", "1", "yes")]
    joint = {r["pair_id"]: r for r in
             csv.DictReader(open(os.path.join(D, "matched_pair_joint.csv")))}
    cand = {r["pair_id"]: r for r in
            csv.DictReader(open(os.path.join(D, "stage_c_candidates.csv")))}
    rates = list(csv.DictReader(open(os.path.join(D, "attempt_rates.csv"))))
    cell = {(r["model"], r["stimulus"], int(r["safe_payoff"])): r for r in rates}
    fresh = {(r["model"], r["stimulus"]): r for r in
             csv.DictReader(open(os.path.join(D, "fresh_self_match.csv")))}

    pairs = []
    for r in approved:
        pid, m = r["pair_id"], r["focal_model"]
        hi, lo = r["stimulus_high"], r["stimulus_low"]
        j, c = joint.get(pid, {}), cand.get(pid, {})
        # pooled across payoffs = sum of counts already in attempt_rates.csv
        def pool(sid):
            k = sum(int(cell[(m, sid, s)]["n_attempt"]) for s in SAFES if (m, sid, s) in cell)
            n = sum(int(cell[(m, sid, s)]["n"]) for s in SAFES if (m, sid, s) in cell)
            return k, n
        kh, nh = pool(hi)
        kl, nl = pool(lo)
        d, dlo, dhi = newcombe(kh, nh, kl, nl)
        ch = c.get("fresh_classification_high", "")
        cl = c.get("fresh_classification_low", "")
        both_form = ch.startswith("form_rule") and cl.startswith("form_rule")
        pairs.append(dict(
            pair_id=pid, model=m, model_name=P.DISPLAY[m], hi=hi, lo=lo,
            label=f"{hi}\nvs {lo}",
            k_hi=kh, n_hi=nh, k_lo=kl, n_lo=nl,
            p_hi=kh / nh, p_lo=kl / nl,
            p_hi_ci=wilson(kh, nh), p_lo_ci=wilson(kl, nl),
            dpool=d, dpool_lo=dlo, dpool_hi=dhi,
            beta=float(j["beta_is_high"]) if j else float("nan"),
            perm_p=float(j["perm_p_one_sided"]) if j else float("nan"),
            dT=float(r["delta_true_holdout"]), dS=float(r["delta_salience_holdout"]),
            dA=float(r["delta_auditor_holdout"]),
            fresh_hi=ch, fresh_lo=cl, both_form=both_form,
            pair_type="both form-based" if both_form else "form-rule vs fallback",
            true_hi=float(fresh[(m, hi)]["self_match_unbiased"]),
            true_lo=float(fresh[(m, lo)]["self_match_unbiased"]),
            curve={s: (cell[(m, hi, s)], cell[(m, lo, s)]) for s in SAFES
                   if (m, hi, s) in cell and (m, lo, s) in cell},
        ))
    order = {"gpt": 0, "claude": 1}
    pairs.sort(key=lambda x: (order[x["model"]], -x["dpool"]))
    return pairs


def save(fig, stem, note):
    os.makedirs(VIZ, exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(VIZ, f"{stem}.{ext}"), facecolor="white")
    plt.close(fig)
    print(f"\n-> {stem}.png / .pdf")
    print(note.strip())
    NOTES.append((stem, note.strip()))


def curve_pts(pr, which):
    xs, ys, lo, hi = [], [], [], []
    for s in SAFES:
        if s not in pr["curve"]:
            continue
        r = pr["curve"][s][0 if which == "hi" else 1]
        k, n = int(r["n_attempt"]), int(r["n"])
        p = k / n
        l, u = wilson(k, n)
        xs.append(s); ys.append(p); lo.append(p - l); hi.append(u - p)
    return xs, ys, [lo, hi]


# ------------------------------------------------------------------ FIGURE 1 --
def figure1(pairs):
    fig, axes = plt.subplots(1, 2, figsize=(7.1, 3.6), sharey=True,
                             gridspec_kw={"width_ratios": [3, 2]})
    for ax, m in zip(axes, ("gpt", "claude")):
        ps = [p for p in pairs if p["model"] == m]
        w = 0.34
        for i, pr in enumerate(ps):
            for off, key, sty in ((-w / 2 - 0.02, "hi", HI_FILL), (w / 2 + 0.02, "lo", LO_FILL)):
                val = pr["p_hi"] if key == "hi" else pr["p_lo"]
                cilo, cihi = pr["p_hi_ci"] if key == "hi" else pr["p_lo_ci"]
                ax.bar(i + off, val, width=w, **sty, zorder=2)
                ax.errorbar(i + off, val, yerr=[[val - cilo], [cihi - val]], **EB, zorder=3)
            pv = f"p = {pr['perm_p']:.4f}" if pr["perm_p"] >= 0.0005 else "p < 0.001"
            ax.text(i, 1.09, f"$\\Delta$ = {pr['dpool']:+.3f}\n{pv}",
                    ha="center", va="bottom", fontsize=6.8, clip_on=False)
            if pr["both_form"]:
                ax.add_patch(Rectangle((i - 0.47, 0.0), 0.94, 1.06, fill=False,
                                       edgecolor="black", linewidth=0.9,
                                       linestyle=(0, (3, 2)), zorder=1, clip_on=False))
        ax.set_xticks(range(len(ps)))
        ax.set_xticklabels([p["label"] + ("\n(both form-based)" if p["both_form"] else "")
                            for p in ps], fontsize=6.6)
        ax.set_xlim(-0.62, len(ps) - 0.38)
        ax.set_ylim(0, 1.06)
        ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
        ax.set_xlabel(P.DISPLAY[m], labelpad=8)
    axes[0].set_ylabel("P(ATTEMPT), pooled across safe payoffs")
    handles = [Patch(**HI_FILL, label="high true self-match"),
               Patch(**LO_FILL, label="matched low")]
    fig.legend(handles=handles, loc="upper center", ncol=2, bbox_to_anchor=(0.5, 0.945),
               fontsize=8)
    fig.suptitle("Models bet more on stimuli where their own copies coordinate better",
                 fontsize=10.5, y=1.075)
    fig.text(0.5, 1.015, "Matched pairs are similar in generic salience and "
             "external-model prediction", ha="center", fontsize=8.2)
    fig.tight_layout(rect=[0, 0, 1, 0.92])
    save(fig, "figure1_core_matched_pair", """
FIGURE 1. For each of the five approved matched pairs, P(ATTEMPT) pooled across the
four safe payoffs, for the high- and low-true-self-match stimulus, with Wilson 95%
display intervals. Annotations give the pooled difference and the p-value from the
PRE-SPECIFIED per-pair joint permutation test (attempt ~ is_high + safe_payoff,
labels permuted within payoff strata) - one test per pair, not one per bar. The
dashed box marks the GPT pair whose two stimuli are BOTH form-based.
SUPPORTS: all five pairs show greater willingness to bet on the higher-reliability
stimulus. DOES NOT ESTABLISH: any mechanism. Pooling across payoffs is a summary;
the payoff-resolved behaviour is Figure 2. Bar heights are descriptive - the
inferential quantity is the annotated permutation p-value.
""")


# ------------------------------------------------------------------ FIGURE 2 --
def figure2(pairs):
    fig, axes = plt.subplots(1, 5, figsize=(7.3, 2.7), sharey=True)
    for ax, pr in zip(axes, pairs):
        for which, sty in (("hi", HI_STY), ("lo", LO_STY)):
            xs, ys, err = curve_pts(pr, which)
            ax.errorbar(xs, ys, yerr=err, **sty, **EB)
        # EV-neutral safe payoff = 10 * p*, drawn as a caret on the axis floor.
        for which, mk in (("hi", "^"), ("lo", "v")):
            pstar = pr["true_hi"] if which == "hi" else pr["true_lo"]
            ax.plot([10 * pstar], [-0.055], marker=mk, color="black", markersize=3.4,
                    clip_on=False, linestyle="none")
        ax.set_xticks(SAFES)
        ax.set_ylim(0, 1.02)
        ax.set_xlim(2.3, 9.7)
        ax.set_title(f"{pr['model_name']}\n{pr['hi']}\nvs {pr['lo']}", fontsize=6.4)
    axes[0].set_ylabel("P(ATTEMPT)")
    for ax in axes:
        ax.set_xlabel("safe payoff")
    axes[0].plot([], [], **HI_STY, label="high true self-match")
    axes[0].plot([], [], **LO_STY, label="matched low")
    axes[0].plot([], [], marker="^", color="black", linestyle="none", markersize=3.4,
                 label="EV-neutral payoff (normative)")
    axes[0].legend(loc="lower left", fontsize=5.8)
    fig.suptitle("Willingness to attempt separates as coordination becomes consequential",
                 fontsize=10.5, y=1.13)
    fig.tight_layout()
    save(fig, "figure2_attempt_curves", """
FIGURE 2. P(ATTEMPT) at each safe payoff, per approved pair, with Wilson 95% display
intervals. Observed values only - no smoothing and no fitted curve. Carets on the
axis floor mark each stimulus's EV-neutral safe payoff (10 x empirical self-match):
a NORMATIVE benchmark for where entry stops maximising expected value, not a claim
about any computation the model performs.
SUPPORTS: the separation emerges where the outside option becomes competitive
(safe = 7 and 9) and is absent at safe = 3-5 where attempting is optimal for both
stimuli - i.e. the effect tracks consequence, not a constant preference. DOES NOT
ESTABLISH: that models compute expected value, nor that behaviour matches the
benchmark; several cells depart from it in both directions.
""")


# ------------------------------------------------------------------ FIGURE 3 --
def figure3(pairs):
    fig, ax = plt.subplots(figsize=(6.6, 3.4))
    ys = range(len(pairs))
    off, ms = 0.24, 5
    series = (("dT", "True self-match gap", "o", "black"),
              ("dS", "Generic salience gap", "s", "white"),
              ("dA", "External-model prediction gap", "^", "0.55"))
    for j, (key, lab, mk, fc) in enumerate(series):
        for i, pr in enumerate(pairs):
            ax.plot([pr[key]], [i + (1 - j) * off], marker=mk, markerfacecolor=fc,
                    markeredgecolor="black", markersize=ms, linestyle="none",
                    markeredgewidth=0.8, zorder=3)
        ax.plot([], [], marker=mk, markerfacecolor=fc, markeredgecolor="black",
                markersize=ms, linestyle="none", label=lab)
    for i in ys:
        ax.axhline(i, color="0.9", linewidth=0.5, zorder=0)
    ax.axvline(0, color="black", linewidth=0.9, linestyle=":", zorder=1)
    ax.set_yticks(list(ys))
    ax.set_yticklabels([f"{p['model_name']}\n{p['hi']} vs {p['lo']}" for p in pairs],
                       fontsize=6.6)
    ax.set_xlabel("held-out difference, high stimulus minus low")
    ax.set_xlim(-0.12, 0.66)
    ax.invert_yaxis()
    ax.legend(loc="center", bbox_to_anchor=(0.47, 0.52), fontsize=7)
    fig.suptitle("True self-coordination differs where public measures do not",
                 fontsize=10.5, y=1.02)
    fig.tight_layout()
    save(fig, "figure3_public_dissociation", """
FIGURE 3. High-minus-low differences for each approved pair on three measures, all
from the HELD-OUT half of Stages A and B (the half not used to order or select the
pairs). The true self-match gap is 0.40-0.52 while both public gaps sit within
+/-0.09 of zero.
SUPPORTS: the direct answer to "maybe the high stimulus just looked easier" - on
these pairs it does not look easier, either to a generic-player salience rating or
to an external model predicting the focal model's own reliability. DOES NOT
ESTABLISH: that the auditor prediction is a pure public baseline. The auditor is a
different model and may hold model-specific information about the focal model, so a
small auditor gap is evidence that this particular external predictor cannot
separate the pair, not proof that no external route exists.
""")


# ------------------------------------------------------------------ FIGURE 4 --
def figure4(pairs):
    fig, ax = plt.subplots(figsize=(6.6, 3.2))
    for i, pr in enumerate(pairs):
        sty = HI_STY if pr["both_form"] else LO_STY
        ax.errorbar([pr["dpool"]], [i],
                    xerr=[[pr["dpool"] - pr["dpool_lo"]], [pr["dpool_hi"] - pr["dpool"]]],
                    marker=sty["marker"], markerfacecolor=sty["markerfacecolor"],
                    markeredgecolor="black", markersize=5.5, linestyle="none", **EB)
    ax.axvline(0, color="black", linewidth=0.9, linestyle=":")
    ax.set_yticks(range(len(pairs)))
    ax.set_yticklabels([f"{p['model_name']}   {p['hi']} vs {p['lo']}" for p in pairs],
                       fontsize=6.8)
    ax.set_xlabel("pooled $\\Delta$P(ATTEMPT), high minus low")
    ax.invert_yaxis()
    ax.set_xlim(-0.05, 0.50)
    for i, pr in enumerate(pairs):
        ax.text(0.495, i, pr["pair_type"], fontsize=6.2, va="center", ha="right",
                style="italic")
    # No legend: the italic right-hand labels already name each pair type, and
    # marker fill (filled = both form-based) is redundant with them.
    fig.suptitle("All five matched pairs show greater willingness to bet on the\n"
                 "higher-reliability stimulus", fontsize=10.5, y=1.06)
    fig.tight_layout()
    save(fig, "figure4_forest_summary", """
FIGURE 4. Pooled difference in P(ATTEMPT), high minus low, for each approved pair,
with Newcombe 95% display intervals; dotted line at zero. Pairs are grouped by focal
model then ordered by effect size, and marker style distinguishes the two pair types
under the FRESH Stage A classification.
SUPPORTS: the direction is consistent - 5/5 pairs positive, spanning both models and
both pair types. DOES NOT ESTABLISH: significance. These display intervals are not
the pre-specified inference; the inferential result is the per-pair permutation test
(4 of 5 pairs at p < 0.05), and one interval here overlaps zero. Significance is
deliberately not the primary visual encoding.
""")


# ------------------------------------------------------------------ FIGURE 5 --
def figure5(pairs):
    pr = next((p for p in pairs if p["both_form"]), None)
    if not pr:
        print("\n(no both-form-based pair among approved - figure 5 skipped)")
        return
    D = P.DATA
    aud = {(r["focal_model"], r["stimulus"]): r for r in
           csv.DictReader(open(os.path.join(D, "auditor_predictions.csv")))}
    sal = {r["stimulus"]: r for r in
           csv.DictReader(open(os.path.join(D, "salience_ratings.csv")))
           if r["rater_model"] == "pooled"}
    m, hi, lo = pr["model"], pr["hi"], pr["lo"]
    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.8),
                             gridspec_kw={"width_ratios": [1, 1.35, 1.35]})

    ax = axes[0]
    ax.bar([0], [pr["true_hi"]], width=0.55, **HI_FILL)
    ax.bar([1], [pr["true_lo"]], width=0.55, **LO_FILL)
    ax.set_xticks([0, 1]); ax.set_xticklabels([hi, lo], fontsize=6.4)
    ax.set_ylim(0, 1.05); ax.set_ylabel("empirical self-match")
    ax.set_title("A  own-copy coordination", fontsize=7.5, loc="left")

    ax = axes[1]
    w = 0.34
    for i, (sid, sty) in enumerate(((hi, HI_FILL), (lo, LO_FILL))):
        s = float(sal[sid]["salience"]); a = float(aud[(m, sid)]["auditor_predicted_match"])
        ax.bar(0 + (i - 0.5) * (w + 0.03), s, width=w, **sty)
        ax.bar(1 + (i - 0.5) * (w + 0.03), a, width=w, **sty)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["generic\nsalience", "external-model\nprediction"], fontsize=6.6)
    ax.set_ylim(0, 1.05)
    ax.set_title("B  public measures", fontsize=7.5, loc="left")

    ax = axes[2]
    for which, sty in (("hi", HI_STY), ("lo", LO_STY)):
        xs, ys, err = curve_pts(pr, which)
        ax.errorbar(xs, ys, yerr=err, **sty, **EB)
    ax.set_xticks(SAFES); ax.set_ylim(0, 1.02); ax.set_xlabel("safe payoff")
    ax.set_ylabel("P(ATTEMPT)")
    ax.set_title("C  betting behaviour", fontsize=7.5, loc="left")
    ax.plot([], [], **HI_STY, label=hi)
    ax.plot([], [], **LO_STY, label=lo)
    ax.legend(loc="lower left", fontsize=6)

    fig.suptitle("Policy-specific betting extends beyond fallback detection",
                 fontsize=10.5, y=1.06)
    fig.tight_layout()
    save(fig, "figure5_both_form_based", f"""
FIGURE 5. The one approved pair whose stimuli are BOTH form-based under the fresh
Stage A classification ({P.DISPLAY[m]}, {hi} form consistency
{pr['fresh_hi'].replace('_', ' ')} vs {lo} {pr['fresh_lo'].replace('_', ' ')}).
(A) own-copy coordination differs; (B) generic salience and external-model
prediction do not; (C) betting separates as the safe payoff rises.
SUPPORTS: the effect is not reducible to detecting position fallback - here the low
stimulus has a genuine form rule, merely a less concentrated one, and this pair
shows the LARGEST joint-model coefficient of the five. DOES NOT ESTABLISH: a graded
relationship across reliability levels. This is a single pair at one contrast; the
battery contains no intermediate cases, so the shape of the relationship between
reliability and willingness to bet is not measured here.
""")


# ---------------------------------------------------------------- COMPOSITE ---
def composite(pairs):
    """Three clean rows: A schematic | B held-out diffs + D forest | C attempt curves."""
    fig = plt.figure(figsize=(7.2, 6.2))
    gs = fig.add_gridspec(3, 5, height_ratios=[0.24, 1.0, 0.95],
                          hspace=0.88, wspace=0.55)

    # -- A schematic --
    axa = fig.add_subplot(gs[0, :])
    axa.set_xlim(0, 10); axa.set_ylim(0, 1.6); axa.axis("off")
    for cx, txt in ((1.45, "matched on\npublic appearance"),
                    (5.0, "differ in TRUE\nown-copy coordination"),
                    (8.55, "does betting\nfollow?")):
        axa.add_patch(Rectangle((cx - 1.35, 0.28), 2.7, 1.0, fill=False,
                                edgecolor="black", linewidth=0.9))
        axa.text(cx, 0.78, txt, ha="center", va="center", fontsize=7.2)
    for x0, x1 in ((2.85, 3.62), (6.4, 7.17)):
        axa.add_patch(FancyArrowPatch((x0, 0.78), (x1, 0.78), arrowstyle="-|>",
                                      mutation_scale=9, linewidth=0.9, color="black"))
    axa.text(0.0, 1.02, "A", fontsize=9, fontweight="bold", transform=axa.transAxes)

    short = lambda pr: f"{pr['model_name'][:6]} {pr['hi'][:10]}/{pr['lo'][:10]}"

    # -- B held-out differences --
    axb = fig.add_subplot(gs[1, 0:2])
    for j, (key, lab, mk, fc) in enumerate((("dT", "true self-match", "o", "black"),
                                            ("dS", "generic salience", "s", "white"),
                                            ("dA", "external-model", "^", "0.55"))):
        for i, pr in enumerate(pairs):
            axb.plot([pr[key]], [i + (1 - j) * 0.25], marker=mk, markerfacecolor=fc,
                     markeredgecolor="black", markersize=4.2, linestyle="none",
                     markeredgewidth=0.7)
        axb.plot([], [], marker=mk, markerfacecolor=fc, markeredgecolor="black",
                 markersize=4.2, linestyle="none", label=lab)
    axb.axvline(0, color="black", linewidth=0.8, linestyle=":")
    axb.set_yticks(range(len(pairs)))
    axb.set_yticklabels([short(p) for p in pairs], fontsize=5.8)
    axb.set_xlabel("held-out difference, high - low", fontsize=7.5)
    axb.invert_yaxis(); axb.set_xlim(-0.14, 0.68)
    axb.tick_params(labelsize=6.5)
    axb.legend(loc="lower center", bbox_to_anchor=(0.5, 1.02), ncol=3,
               fontsize=5.8, columnspacing=1.0, handletextpad=0.4)
    axb.text(-0.50, 1.13, "B", fontsize=9, fontweight="bold", transform=axb.transAxes)

    # -- D forest --
    axd = fig.add_subplot(gs[1, 2:])
    for i, pr in enumerate(pairs):
        sty = HI_STY if pr["both_form"] else LO_STY
        axd.errorbar([pr["dpool"]], [i],
                     xerr=[[pr["dpool"] - pr["dpool_lo"]], [pr["dpool_hi"] - pr["dpool"]]],
                     marker=sty["marker"], markerfacecolor=sty["markerfacecolor"],
                     markeredgecolor="black", markersize=4.8, linestyle="none", **EB)

    axd.axvline(0, color="black", linewidth=0.8, linestyle=":")
    axd.set_yticks(range(len(pairs)))
    axd.set_yticklabels([])          # same rows, same order as panel B
    axd.set_xlabel("pooled $\\Delta$P(ATTEMPT), high - low", fontsize=7.5)
    axd.plot([], [], **{**HI_STY, "linestyle": "none"}, label="both form-based")
    axd.plot([], [], **{**LO_STY, "linestyle": "none"}, label="form-rule vs fallback")
    axd.legend(loc="lower center", bbox_to_anchor=(0.5, 1.02), ncol=2, fontsize=5.8,
               columnspacing=1.0, handletextpad=0.4)
    axd.invert_yaxis(); axd.set_xlim(-0.05, 0.42)
    axd.tick_params(labelsize=6.5)
    axd.text(-0.04, 1.13, "D", fontsize=9, fontweight="bold", transform=axd.transAxes)

    # -- C attempt curves, one full row --
    for k, pr in enumerate(pairs):
        axc = fig.add_subplot(gs[2, k])
        for which, sty in (("hi", HI_STY), ("lo", LO_STY)):
            xs, ys, err = curve_pts(pr, which)
            axc.errorbar(xs, ys, yerr=err, **{**sty, "markersize": 3.0,
                                              "linewidth": 0.9}, **EB)
        axc.set_xticks(SAFES); axc.set_ylim(0, 1.04); axc.set_xlim(2.4, 9.6)
        axc.tick_params(labelsize=6)
        axc.set_title(f"{pr['model_name'][:6]}\n{pr['hi'][:11]}\nvs {pr['lo'][:11]}",
                      fontsize=5.6)
        axc.set_xlabel("safe payoff", fontsize=6.5)
        if k == 0:
            axc.set_ylabel("P(ATTEMPT)", fontsize=7.5)
            axc.text(-0.62, 1.30, "C", fontsize=9, fontweight="bold",
                     transform=axc.transAxes)
        else:
            axc.set_yticklabels([])

    fig.suptitle("Policy-specific information predicts willingness to enter\n"
                 "self-coordination games", fontsize=10.5, y=1.045)
    save(fig, "figure_main_composite", """
COMPOSITE. (A) the design logic; (B) held-out high-minus-low differences on the true
and the two public measures; (C) payoff-resolved attempt curves for all five approved
pairs; (D) pooled effect with Newcombe display intervals.
SUPPORTS: the full argument in one view - pairs matched on public measures, separated
on own-copy coordination, and betting that follows the own-copy measure. DOES NOT
ESTABLISH: mechanism, introspective access, or generality beyond this battery. Panel
A is a schematic of the design, not a causal diagram.
""")


def main():
    pairs = load()
    print(f"approved pairs plotted: {len(pairs)}")
    for p in pairs:
        print(f"  {p['model_name']:16}{p['hi']:16}vs {p['lo']:16}"
              f"pooled hi {p['p_hi']:.3f} lo {p['p_lo']:.3f}  d {p['dpool']:+.3f}"
              f"  perm p {p['perm_p']:.4f}  [{p['pair_type']}]")
    figure1(pairs); figure2(pairs); figure3(pairs); figure4(pairs); figure5(pairs)
    composite(pairs)
    print(f"\nall figures written to {VIZ}")


if __name__ == "__main__":
    main()
