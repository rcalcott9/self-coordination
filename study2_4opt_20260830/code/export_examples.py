"""Export representative stimuli to ~/Downloads for eyeballing.

Three sheets:
  1. families        - all 16 families at member 0 (the strong-focal end)
  2. member_sweep    - four families across all 8 members (the strength gradient)
  3. permutations    - one stimulus in 6 of its 24 orderings (position randomisation)
plus a handful of full-resolution single stimuli.
"""
import os, shutil, json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
STIM = os.path.join(os.path.dirname(HERE), "stimuli")
OUT = os.path.join(os.path.expanduser("~"), "Downloads", "s4_stimulus_examples")
plt.rcParams.update({"font.family": ["Arial", "Helvetica", "DejaVu Sans"],
                     "font.size": 8})

FAMS = sorted({d.rsplit("_m", 1)[0] for d in os.listdir(STIM)
               if os.path.isdir(os.path.join(STIM, d))})


def img(sid, perm=0):
    return plt.imread(os.path.join(STIM, sid, f"perm{perm:02d}.png"))


def sheet(rows, labels, path, title, per_h=1.35):
    fig, axes = plt.subplots(len(rows), 1, figsize=(9, per_h * len(rows)), dpi=130)
    if len(rows) == 1:
        axes = [axes]
    for ax, r, lab in zip(axes, rows, labels):
        ax.imshow(r); ax.axis("off")
        ax.set_title(lab, fontsize=7.5, color="#222", pad=3, loc="left")
    fig.suptitle(title, fontsize=9, y=0.998)
    fig.tight_layout(rect=[0, 0, 1, 0.985])
    fig.savefig(path, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    print("  wrote", os.path.basename(path))


def main():
    os.makedirs(OUT, exist_ok=True)

    # 1. one row per family, member 0
    sheet([img(f"{f}_m0") for f in FAMS],
          [f"{f}  (member 0 of 8 - strong-focal end)" for f in FAMS],
          os.path.join(OUT, "1_all_families.png"),
          "4-option battery: 16 families, member 0 of 8")

    # 2. strength sweep for four contrasting families
    for f in ("F01_oddone", "F07_contrast", "F06_density", "F11_noise"):
        sheet([img(f"{f}_m{t}") for t in range(8)],
              [f"member {t}" + (" (strongest)" if t == 0 else
                                " (weakest)" if t == 7 else "") for t in range(8)],
              os.path.join(OUT, f"2_sweep_{f}.png"),
              f"{f}: all 8 members, strong -> weak focal pull")

    # 3. the same stimulus under different orderings
    sid = "F07_contrast_m0"
    man = json.load(open(os.path.join(STIM, sid, "manifest.json")))
    perms = [0, 5, 9, 14, 19, 23]
    sheet([img(sid, p) for p in perms],
          [f"perm{p:02d}  items at positions 1-4: {man[str(p)]}" for p in perms],
          os.path.join(OUT, "3_position_randomisation.png"),
          f"{sid}: 6 of its 24 orderings - each player sees an independent draw")

    # 4. full-resolution singles
    singles = ["F01_oddone_m0", "F01_oddone_m7", "F07_contrast_m0", "F07_contrast_m7",
               "F11_noise_m0", "F05_orient_m0", "F13_count_m0", "F15_ring_m0"]
    d = os.path.join(OUT, "full_size")
    os.makedirs(d, exist_ok=True)
    for s in singles:
        shutil.copy(os.path.join(STIM, s, "perm00.png"),
                    os.path.join(d, f"{s}.png"))
    print(f"  wrote {len(singles)} full-size singles -> full_size/")
    print("\n->", OUT)


if __name__ == "__main__":
    main()
