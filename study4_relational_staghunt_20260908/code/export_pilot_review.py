"""Export a REVIEW copy of the pilot stimuli to ~/Downloads.

Review sheets carry labels for the human reader; the images actually shown to the
models are the unlabelled ones copied under stimuli_pilot/.
"""
import json, os, shutil
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

plt.rcParams.update({"font.family": "Arial", "font.size": 9, "text.color": "black",
                     "axes.titlesize": 9, "figure.dpi": 130})

EXP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STIM = os.path.join(EXP, "stimuli_pilot")
MAN = json.load(open(os.path.join(EXP, "pilot", "PILOT_MANIFEST_LOCKED.json")))
DL = os.path.expanduser("~/Downloads/self_coord_pilot_stimuli_20260908")

SHOW = [0, 9, 18]          # three permutations, green lands in a different slot in each


def main():
    os.makedirs(os.path.join(DL, "review_sheets"), exist_ok=True)
    recs = sorted(MAN["asymmetric"] + MAN["controls"], key=lambda r: (r["item_type"], r["array_id"]))
    lines = []
    for rec in recs:
        sid = rec["array_id"]
        gj = json.load(open(os.path.join(STIM, sid, "green.json")))
        fig, axes = plt.subplots(len(SHOW), 1, figsize=(9.0, 2.9 * len(SHOW)))
        for ax, p in zip(axes, SHOW):
            ax.imshow(mpimg.imread(os.path.join(STIM, sid, f"perm{p:02d}.png")))
            ax.set_xticks([]); ax.set_yticks([])
            for sp in ax.spines.values(): sp.set_visible(False)
            order = " | ".join(f"{i+1}:{rec['objects'][o]}" for i, o in enumerate(gj_perm(STIM, sid, p)))
            ax.set_title(f"perm{p:02d}   slots {order}   green in slot "
                         f"{gj['greened_position_by_perm'][str(p)]+1}", loc="left", pad=4)
        role = rec["item_type"].upper()
        extra = f"  [{rec['role']}]" if rec.get("role") else ""
        fig.suptitle(f"{sid}   {role}{extra}   mechanism {rec['mechanism']}\n"
                     f"Claude modal {rec['claude_modal_object']} "
                     f"({rec['claude_modal_share']:.2f})   "
                     f"GPT modal {rec['gpt_modal_object']} ({rec['gpt_modal_share']:.2f})   "
                     f"GREEN {rec['green_object']}",
                     y=0.995, va="top", ha="left", x=0.02, fontsize=9)
        fig.subplots_adjust(top=0.90, hspace=0.22, left=0.01, right=0.99, bottom=0.01)
        fig.savefig(os.path.join(DL, "review_sheets", f"{sid}.png"))
        plt.close(fig)
        lines.append(f"| {sid} | {role.lower()}{extra} | {rec['mechanism']} | "
                     f"{rec['claude_modal_object']} ({rec['claude_modal_share']:.2f}) | "
                     f"{rec['gpt_modal_object']} ({rec['gpt_modal_share']:.2f}) | "
                     f"{rec['gpt_policy_subtype']} | **{rec['green_object']}** | "
                     f"{', '.join(rec['green_eligible_objects'])} |")
        print(" ", sid)

    if os.path.isdir(os.path.join(DL, "stimuli_pilot")):
        shutil.rmtree(os.path.join(DL, "stimuli_pilot"))
    shutil.copytree(STIM, os.path.join(DL, "stimuli_pilot"))

    integ = json.load(open(os.path.join(STIM, "RENDER_INTEGRITY.json")))
    md = ["# Study 4 - Claude-focal relational pilot: stimuli for review",
          "", f"Built {MAN['built_utc']}.  Manifest sha256 "
          f"`{open(os.path.join(EXP,'pilot','PILOT_MANIFEST_LOCKED.json.sha256')).read().strip()[:16]}`"
          f"  Stimuli sha256 `{integ['stimuli_sha256'][:16]}`", "",
          "`review_sheets/` are LABELLED for you. `stimuli_pilot/` holds the actual "
          "unlabelled images the models see (24 permutations per array).", "",
          "## What green means", "",
          "The green rectangle is the **panel outline** of one object. It marks that "
          "object; it does not touch its fill, size, position or internal features. "
          "In the game the green object pays **5** if both players pick it, the three "
          "unmarked objects pay **10** if both pick the same one, any mismatch pays 0. "
          "Green follows its object across permutations - it is in a different slot in "
          "each of the three rows on every sheet.", "",
          "## Verification that ran on every array", "",
          "- The same array re-rendered **without** green is pixel-identical to the "
          "original battery5 image (max channel difference 0.000).",
          "- Every pixel that differs between the green and no-green render lies on the "
          "blend line from the original colour to the green ink, and sits inside the "
          "intended panel. Nothing else changed.",
          "- Green outline identical across all 15 arrays (8688-8704 green pixels; the "
          "spread is panel-edge antialiasing only).",
          "- Green reaches all four screen positions in every array.",
          "- 24 distinct renders per array; every object in every position exactly 6 times.",
          "- No green assignment sits on Claude's locked modal, or on any object holding "
          f"≥ {MAN['green_excl_share']} of either model's measured mass.", "",
          "## Arrays", "",
          "| array | type | mechanism | Claude modal (share) | GPT modal (share) | GPT policy | GREEN | green-eligible pool |",
          "|---|---|---|---|---|---|---|---|"] + lines
    open(os.path.join(DL, "STIMULI_REVIEW.md"), "w").write("\n".join(md) + "\n")
    print(f"\n-> {DL}")


def gj_perm(stim, sid, p):
    return json.load(open(os.path.join(stim, sid, "manifest.json")))[str(p)]


if __name__ == "__main__":
    main()
