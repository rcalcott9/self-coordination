"""Export the battery to ~/Downloads with each stimulus labelled by measured
GPT / Claude coordination ability.

Sheets, in the order that matters for the design:
  0_summary.png        scatter of GPT vs Claude self-match, all stimuli
  1_gpt_favoured       GPT coordinates, Claude does not   (delta > 0)
  2_claude_favoured    Claude coordinates, GPT does not   (delta < 0)
  3_shared_strong      both coordinate - NOT usable as high members (own = cross)
  4_both_low           neither coordinates
  labels.csv           the numbers behind every panel

`delta` here is GPT self-match minus Claude self-match. The design's usable HIGH
members are the asymmetric ones: on a shared convention a same-model partner buys
nothing, so no partner effect is predicted there.
"""
import os, csv, glob, shutil, argparse
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import s4_common as S

OUT = os.path.join(os.path.expanduser("~"), "Downloads", "s4_stimulus_examples")
plt.rcParams.update({"font.family": ["Arial", "Helvetica", "DejaVu Sans"],
                     "font.size": 8})
MAXROWS = 22


def load(mode):
    p = os.path.join(S.DATA, f"cell_metrics_{mode}.csv")
    rows = list(csv.DictReader(open(p)))
    by = {}
    for r in rows:
        by.setdefault(r["stimulus_id"], {})[r["model"]] = r
    out = []
    for sid, d in by.items():
        if "gpt" not in d or "claude" not in d:
            continue
        g, c = float(d["gpt"]["self_match"]), float(d["claude"]["self_match"])
        out.append(dict(
            sid=sid, gpt=g, claude=c, delta=g - c,
            gpt_cls=d["gpt"]["classification"], claude_cls=d["claude"]["classification"],
            gpt_pb=float(d["gpt"]["position_bias"]),
            claude_pb=float(d["claude"]["position_bias"]),
            cross=float(d["gpt"]["cross_match"]) if d["gpt"]["cross_match"] else float("nan"),
            gpt_modal=d["gpt"]["modal_item"], claude_modal=d["claude"]["modal_item"],
            n=int(d["gpt"]["n"])))
    return out


def lab(r):
    return (f"{r['sid']}   GPT {r['gpt']:.2f} / Claude {r['claude']:.2f}"
            f"   delta {r['delta']:+.2f}   cross {r['cross']:.2f}"
            f"   modal G{r['gpt_modal']} C{r['claude_modal']}"
            f"   posbias G{r['gpt_pb']:.2f} C{r['claude_pb']:.2f}")


def sheet(recs, path, title):
    if not recs:
        print(f"  (skip {os.path.basename(path)} - no stimuli)")
        return
    recs = recs[:MAXROWS]
    fig, axes = plt.subplots(len(recs), 1, figsize=(9, 1.30 * len(recs)), dpi=125)
    if len(recs) == 1:
        axes = [axes]
    for ax, r in zip(axes, recs):
        ax.imshow(plt.imread(os.path.join(S.STIM, r["sid"], "perm00.png")))
        ax.axis("off")
        ax.set_title(lab(r), fontsize=7, color="#222", pad=3, loc="left")
    fig.suptitle(title, fontsize=9.5, y=0.999)
    fig.tight_layout(rect=[0, 0, 1, 0.986])
    fig.savefig(path, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    print(f"  wrote {os.path.basename(path)}  ({len(recs)} stimuli)")


def scatter(recs, path, n):
    fig, ax = plt.subplots(figsize=(5.5, 3.2))
    ax.axhline(S.CHANCE, color="0.7", lw=0.8, ls=(0, (4, 3)))
    ax.axvline(S.CHANCE, color="0.7", lw=0.8, ls=(0, (4, 3)))
    ax.plot([0.2, 1.02], [0.2, 1.02], color="0.6", lw=0.8, ls=(0, (1, 2)))
    sym = [r for r in recs if abs(r["delta"]) < 0.30]
    asym = [r for r in recs if abs(r["delta"]) >= 0.30]
    ax.plot([r["gpt"] for r in sym], [r["claude"] for r in sym], "o",
            mfc="none", mec="k", mew=0.7, ms=4, lw=0, label="symmetric")
    ax.plot([r["gpt"] for r in asym], [r["claude"] for r in asym], "s",
            mfc="k", mec="k", ms=4.5, lw=0, label="asymmetric (|delta| >= .30)")
    ax.set_xlabel("GPT-5.5 own-copy match")
    ax.set_ylabel("Claude Opus 5 own-copy match")
    ax.set_xlim(0.15, 1.05); ax.set_ylim(0.15, 1.05)
    ax.legend(frameon=False, fontsize=7.5, loc="lower right")
    fig.tight_layout()
    fig.savefig(path, facecolor="white", dpi=300)
    plt.close(fig)
    print(f"  wrote {os.path.basename(path)}  (n={n} stimuli)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", default="discovery")
    a = ap.parse_args()
    recs = load(a.mode)
    os.makedirs(OUT, exist_ok=True)

    with open(os.path.join(OUT, "labels.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(recs[0].keys()))
        w.writeheader(); w.writerows(sorted(recs, key=lambda r: -r["delta"]))

    scatter(recs, os.path.join(OUT, "0_summary_scatter.png"), len(recs))

    HI, LO = 0.75, 0.45
    gptfav = sorted([r for r in recs if r["gpt"] >= HI and r["claude"] <= LO],
                    key=lambda r: -r["delta"])
    clafav = sorted([r for r in recs if r["claude"] >= HI and r["gpt"] <= LO],
                    key=lambda r: r["delta"])
    shared = sorted([r for r in recs if r["gpt"] >= HI and r["claude"] >= HI],
                    key=lambda r: -(r["gpt"] + r["claude"]))
    both_lo = sorted([r for r in recs if r["gpt"] <= LO and r["claude"] <= LO],
                     key=lambda r: r["gpt"] + r["claude"])

    sheet(gptfav, os.path.join(OUT, "1_gpt_favoured.png"),
          f"GPT coordinates (>= {HI}), Claude does not (<= {LO})  -  "
          f"{len(gptfav)} stimuli, n={recs[0]['n']}/model")
    sheet(clafav, os.path.join(OUT, "2_claude_favoured.png"),
          f"Claude coordinates (>= {HI}), GPT does not (<= {LO})  -  "
          f"{len(clafav)} stimuli, n={recs[0]['n']}/model")
    sheet(shared, os.path.join(OUT, "3_shared_strong.png"),
          f"BOTH coordinate - shared conventions, own = cross, no partner effect "
          f"predicted  -  {len(shared)} stimuli")
    sheet(both_lo, os.path.join(OUT, "4_both_low.png"),
          f"Neither coordinates  -  {len(both_lo)} stimuli")

    d = os.path.join(OUT, "full_size")
    os.makedirs(d, exist_ok=True)
    for r in (gptfav[:4] + clafav[:4]):
        shutil.copy(os.path.join(S.STIM, r["sid"], "perm00.png"),
                    os.path.join(d, f"{r['sid']}_G{r['gpt']:.2f}_C{r['claude']:.2f}.png"))

    print(f"\n  GPT-favoured    {len(gptfav):4d}")
    print(f"  Claude-favoured {len(clafav):4d}")
    print(f"  shared strong   {len(shared):4d}")
    print(f"  both low        {len(both_lo):4d}")
    print(f"\n-> {OUT}")


if __name__ == "__main__":
    main()
