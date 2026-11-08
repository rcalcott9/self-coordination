"""
Family-level battery report -> family_report.md + candidate_pairs.csv

WHAT THE LOW MEMBER IS FOR. Not to manufacture a large contrast. It tests whether
the focal model BACKS OFF when its own policy is unreliable *even when told the
partner is another instance of itself*. That is what rules out the trivial
heuristic "partner is my model, therefore coordinate". So a usable pair needs, for
ONE focal model:

  HIGH  self-match >= .75 AND model-specific (own - cross >= .15)
        - model-specific because on a shared convention a same-model partner buys
          nothing, so no interaction is predicted there
  LOW   self-match <= .45 AND non-positional
        - non-positional because "the model gave up and read position" is a
          different construct from "the model's own convention is unreliable"
  PAIR  gap >= .30, and preferably DIFFERENT families on the two sides

FAMILY IS THE UNIT OF INDEPENDENCE. Variants within a family are three settings of
one structural manipulation, not three observations. So each family contributes at
most one high and at most one low to the reported pair set, and the headline number
is pairs with distinct families on both sides.

A family is NOT required to supply both sides - that would over-constrain
discovery. Highs and lows are matched across the whole battery.
"""
import os, csv, glob, argparse
from collections import Counter, defaultdict
import s4_common as S

HI, LO, SPEC, GAP = 0.75, 0.45, 0.15, 0.30


def load():
    """Merge every discovery cell-metrics file; later files win on collision."""
    rows = {}
    for f in sorted(glob.glob(os.path.join(S.DATA, "cell_metrics_discovery*.csv"))):
        for r in csv.DictReader(open(f)):
            rows[(r["stimulus_id"], r["model"])] = r
    return rows


def F(r, k):
    v = r.get(k, "")
    return float(v) if v not in ("", "nan", None) else float("nan")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    cm = load()
    stimuli = sorted({s for s, _ in cm})
    fam_of = {s: s.rsplit("_m", 1)[0] for s in stimuli}
    L = []

    def p(s=""):
        print(s); L.append(s)

    p("# 4-option battery - family-level report")
    p()
    p(f"`{len(stimuli)}` stimuli across `{len(set(fam_of.values()))}` families, "
      f"discovery n=24/model/stimulus.")
    p()
    p(f"Criteria: HIGH self-match >= {HI} and own-cross >= {SPEC}; "
      f"LOW self-match <= {LO} and non-positional; pair gap >= {GAP}; "
      "family is the unit of independence.")
    p()

    allpairs = []
    for focal in ("gpt", "claude"):
        p(f"## {S.DISPLAY[focal]} as focal model")
        p()
        highs, lows = [], []
        for s in stimuli:
            r = cm.get((s, focal))
            if not r:
                continue
            sm, adv = F(r, "self_match"), F(r, "own_minus_cross")
            pos = r["classification"] == "position_fallback"
            if sm >= HI and adv >= SPEC:
                highs.append((s, sm, adv))
            if sm <= LO and not pos:
                lows.append((s, sm, F(r, "position_bias")))

        hf = {f for f, _ in ((fam_of[s], s) for s, _, _ in highs)}
        lf = {fam_of[s] for s, _, _ in lows}
        p(f"- qualifying HIGH stimuli (>= {HI}, model-specific): **{len(highs)}** "
          f"across **{len(hf)}** families")
        p(f"- qualifying LOW stimuli (<= {LO}, non-positional) : **{len(lows)}** "
          f"across **{len(lf)}** families")
        p(f"- families supplying BOTH a high and a low          : "
          f"**{len(hf & lf)}**")
        p()

        # one best high and one best low per family -> maximises family diversity
        best_h, best_l = {}, {}
        for s, sm, adv in sorted(highs, key=lambda x: -x[2]):
            best_h.setdefault(fam_of[s], (s, sm, adv))
        for s, sm, pb in sorted(lows, key=lambda x: x[1]):
            best_l.setdefault(fam_of[s], (s, sm, pb))

        used_h, used_l, pairs = set(), set(), []
        cand = []
        for fh, (sh, smh, adv) in best_h.items():
            for fl, (sl, sml, pb) in best_l.items():
                if fh == fl:
                    continue                       # distinct families required
                gap = smh - sml
                if gap < GAP:
                    continue
                # transparent composite: both properties must be present, and the
                # scarcer one (model-specificity) is not allowed to be traded away
                score = min(adv / 0.50, 1.0) * 0.6 + min(gap / 0.60, 1.0) * 0.4
                cand.append((score, gap, adv, sh, sl, fh, fl, smh, sml, pb))
        for c in sorted(cand, key=lambda x: -x[0]):
            _, gap, adv, sh, sl, fh, fl, smh, sml, pb = c
            if fh in used_h or fl in used_l:
                continue
            used_h.add(fh); used_l.add(fl)
            pairs.append(c)

        p(f"- **high/low pairs with DISTINCT families on both sides: "
          f"{len(pairs)}**")
        p(f"- distinct families represented across those pairs: "
          f"{len(used_h | used_l)}")
        p()
        if pairs:
            p("| # | HIGH stimulus | self | own-cross | LOW stimulus | self | "
              "pos.bias | gap |")
            p("|---|---|---|---|---|---|---|---|")
            for i, (_, gap, adv, sh, sl, fh, fl, smh, sml, pb) in enumerate(pairs, 1):
                p(f"| {i} | `{sh}` | {smh:.3f} | **{adv:+.3f}** | `{sl}` | "
                  f"{sml:.3f} | {pb:.3f} | {gap:.3f} |")
            p()
        for c in pairs:
            _, gap, adv, sh, sl, fh, fl, smh, sml, pb = c
            allpairs.append(dict(
                focal=focal, high_stimulus=sh, high_family=fh, high_self=round(smh, 4),
                high_own_minus_cross=round(adv, 4), low_stimulus=sl, low_family=fl,
                low_self=round(sml, 4), low_position_bias=round(pb, 4),
                gap=round(gap, 4), distinct_families=True))

    # ------------------------------------------------------------- families ---
    p("## Family-level yield")
    p()
    p("| family | GPT high | GPT low | Claude high | Claude low |")
    p("|---|---|---|---|---|")
    fams = sorted(set(fam_of.values()))
    for f in fams:
        cells = []
        for focal in ("gpt", "claude"):
            h = sum(1 for s in stimuli if fam_of[s] == f and (s, focal) in cm
                    and F(cm[(s, focal)], "self_match") >= HI
                    and F(cm[(s, focal)], "own_minus_cross") >= SPEC)
            l = sum(1 for s in stimuli if fam_of[s] == f and (s, focal) in cm
                    and F(cm[(s, focal)], "self_match") <= LO
                    and cm[(s, focal)]["classification"] != "position_fallback")
            cells += [h, l]
        if any(cells):
            p(f"| `{f}` | {cells[0]} | {cells[1]} | {cells[2]} | {cells[3]} |")
    p()

    out = a.out or os.path.join(S.DATA, "family_report.md")
    open(out, "w").write("\n".join(L) + "\n")
    if allpairs:
        cp = os.path.join(S.DATA, "candidate_pairs.csv")
        with open(cp, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(allpairs[0].keys()))
            w.writeheader(); w.writerows(allpairs)
        print(f"\nwrote {cp}  ({len(allpairs)} pairs)")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
