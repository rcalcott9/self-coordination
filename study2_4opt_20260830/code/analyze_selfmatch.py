"""Per-cell metrics for a Stage A run -> cell_metrics_<mode>.csv.

One row per (stimulus, model): unbiased self-match + bootstrap CI, modal item and
share, entropy, position bias, and a fallback CLASSIFICATION.

On classification: at 4 options a position responder scores .25, which is exactly
chance, so positional behaviour is a genuine floor and not an artefact that
inflates anything. It is therefore recorded as a covariate and reported as a
robustness split, NOT used to exclude stimuli. (At 2 options it had to be excluded,
because there .50 was simultaneously the floor and the entire 'low' band.)

Also emits the cross-model match, computed directly by pairing each model's
independent draws - not inferred from marginals.
"""
import os, csv, glob, json, argparse, math
from collections import Counter
import s4_common as S


def cells(rows):
    out = {}
    for r in rows:
        if r["parse_ok"] != "True":
            continue
        k = (r["stimulus_id"], r["model"])
        out.setdefault(k, {"items": [], "pos": []})
        out[k]["items"].append(int(r["chosen_item"]))
        out[k]["pos"].append(int(r["chosen_position"]) - 1)
    return out


def classify(match, posbias, ent):
    """Coarse, reported alongside the raw numbers - never used as a filter."""
    if posbias >= 0.30:
        return "position_fallback"
    if match >= 0.75:
        return "strong_convention"
    if match <= 0.45:
        return "weak_or_none"
    return "intermediate"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=("discovery", "validation"), default="discovery")
    ap.add_argument("--file", default=None)
    a = ap.parse_args()

    f = a.file or sorted(glob.glob(os.path.join(S.DATA,
                                                f"stageA_{a.mode}_*.csv")))[-1]
    rows = list(csv.DictReader(open(f)))
    print(f"source: {f}   rows={len(rows)}")
    n_parse_fail = sum(1 for r in rows if r["ok"] == "True" and r["parse_ok"] != "True")
    n_transport = sum(1 for r in rows if r["ok"] != "True")
    print(f"  transport failures: {n_transport}   parse failures: {n_parse_fail}")

    C = cells(rows)
    recs = []
    for (sid, model), d in sorted(C.items()):
        items, pos = d["items"], d["pos"]
        ic, pc = Counter(items), Counter(pos)
        m = S.unbiased_match(ic)
        lo, hi = S.boot_match_ci(items)
        pb = S.position_bias(pc)
        ent = S.entropy_bits(ic)
        modal, modal_n = ic.most_common(1)[0]
        recs.append(dict(
            mode=a.mode, stimulus_id=sid, family=sid.rsplit("_m", 1)[0],
            member=sid.rsplit("_m", 1)[1], model=model, n=len(items),
            self_match=round(m, 4), ci_lo=round(lo, 4), ci_hi=round(hi, 4),
            plugin=round(S.plugin_match(ic), 4),
            modal_item=modal, modal_share=round(modal_n / len(items), 4),
            entropy_bits=round(ent, 4), position_bias=round(pb, 4),
            item_counts=json.dumps({str(k): v for k, v in sorted(ic.items())}),
            pos_counts=json.dumps({str(k): v for k, v in sorted(pc.items())}),
            classification=classify(m, pb, ent)))

    # ---- cross-model match from the independent draws themselves --------------
    by = {(r["stimulus_id"], r["model"]): r for r in recs}
    raw = {}
    for r in rows:
        if r["parse_ok"] == "True":
            raw.setdefault((r["stimulus_id"], r["model"]), []).append(int(r["chosen_item"]))
    for r in recs:
        g = raw.get((r["stimulus_id"], "gpt"), [])
        c = raw.get((r["stimulus_id"], "claude"), [])
        if g and c:
            gc, cc = Counter(g), Counter(c)
            # P(match) between one independent GPT draw and one independent Claude
            # draw = sum_k p_k q_k. Estimated from the two empirical distributions,
            # which ARE independent samples - no marginal-inference shortcut.
            cross = sum((gc[k] / len(g)) * (cc[k] / len(c)) for k in range(4))
            r["cross_match"] = round(cross, 4)
            other = "claude" if r["model"] == "gpt" else "gpt"
            r["own_minus_cross"] = round(r["self_match"] - cross, 4)
            o = by.get((r["stimulus_id"], other))
            r["other_self_match"] = o["self_match"] if o else ""
        else:
            r["cross_match"] = r["own_minus_cross"] = r["other_self_match"] = ""

    out = os.path.join(S.DATA, f"cell_metrics_{a.mode}.csv")
    with open(out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(recs[0].keys()))
        w.writeheader(); w.writerows(recs)
    print(f"wrote {out}  ({len(recs)} cells)\n")

    # ---- summary --------------------------------------------------------------
    for model in ("gpt", "claude"):
        s = [r for r in recs if r["model"] == model]
        if not s:
            continue
        cl = Counter(r["classification"] for r in s)
        print(f"{S.DISPLAY[model]}  ({len(s)} stimuli)")
        for k in ("strong_convention", "intermediate", "weak_or_none",
                  "position_fallback"):
            print(f"    {k:20} {cl.get(k,0):4d}")
        hi = [r for r in s if r["self_match"] >= 0.75]
        lo = [r for r in s if r["self_match"] <= 0.45]
        print(f"    self_match >= .75    {len(hi):4d}")
        print(f"    self_match <= .45    {len(lo):4d}")
        spec = [r for r in hi if r["own_minus_cross"] != "" and
                r["own_minus_cross"] >= 0.15]
        print(f"    of the >=.75, policy-SPECIFIC (own-cross >= .15): {len(spec)}")
        print()


if __name__ == "__main__":
    main()
