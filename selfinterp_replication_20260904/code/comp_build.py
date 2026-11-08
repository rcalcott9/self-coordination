"""Complementary-role experiment, stage 1: build the candidate item pool. Local, free.

120 two-attribute contrast items spread across contexts and spanning |d_focal|, which is
the best available a-priori proxy for how determinate the fine-tuned policy will be.
Actual predictability is measured, not assumed, in stage 2.
"""

import itertools
import json
import random
from collections import Counter
from pathlib import Path

import numpy as np

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from gate1_preflight import rounding_precision

ROOT = Path(__file__).resolve().parent.parent
G1, O = ROOT / "data" / "gate1", ROOT / "data" / "g4omini"
REF = ROOT / "reference_plunkett" / "data"
F = ROOT / "data" / "comp_role"
N_ITEMS, SEED = 120, 20260908


def main():
    cands = {s["short_name"]: s for s in json.loads((REF / "candidate_scenarios.json").read_text())}
    qtext = {}
    for r in json.loads((G1 / "gate1_heldout_5000.json").read_text()):
        if r["scenario"] not in qtext:
            qtext[r["scenario"]] = r["prompt"].split(":\n\n", 1)[1].split("\nA:\n")[0]
    focal = {k: np.array(v, float) for k, v in
             json.loads((O / "g4omini_eval_verdict.json").read_text())["learned_weights"].items()}

    pool = []
    for s in sorted(set(focal) & set(qtext) & set(cands)):
        for i, j in itertools.combinations(range(5), 2):
            d = float(focal[s][i] - focal[s][j])
            if d == 0:
                continue
            pool.append({"scenario": s, "i": i, "j": j, "d_focal": d})

    g = np.array([abs(x["d_focal"]) for x in pool])
    cuts = np.percentile(g, [33.3, 66.7])
    for x, v in zip(pool, g):
        x["gap_stratum"] = "low" if v <= cuts[0] else ("medium" if v <= cuts[1] else "high")

    # spread across contexts, balance the side the learned policy favours
    rng = random.Random(SEED)
    chosen, per = [], N_ITEMS // 3
    for strat in ("low", "medium", "high"):
        cand = [x for x in pool if x["gap_stratum"] == strat]
        rng.shuffle(cand)
        used, sideA, picked = set(), 0, []
        for second in (False, True):
            for c in cand:
                if len(picked) >= per:
                    break
                if not second and c["scenario"] in used:
                    continue
                fav = "A" if c["d_focal"] > 0 else "B"
                if fav == "A" and sideA >= per // 2:
                    continue
                if fav == "B" and (len(picked) - sideA) >= per // 2:
                    continue
                picked.append(c); used.add(c["scenario"]); sideA += (fav == "A")
        chosen += picked

    items = []
    for c in chosen:
        s, i, j = c["scenario"], c["i"], c["j"]
        attrs = cands[s]["attributes"]
        vals = {}
        for k, a in enumerate(attrs):
            lo, hi = a["range"]; p = rounding_precision({"range": a["range"]})
            mid = round(lo + 0.5 * (hi - lo), p)
            if k == i:
                vals[k] = (round(lo + 0.9 * (hi - lo), p), round(lo + 0.1 * (hi - lo), p))
            elif k == j:
                vals[k] = (round(lo + 0.1 * (hi - lo), p), round(lo + 0.9 * (hi - lo), p))
            else:
                vals[k] = (mid, mid)

        def blk(letter, side):
            return letter + ":\n" + "\n".join(
                f"{a['name']}: {vals[k][side]} {a['units']}" for k, a in enumerate(attrs))
        items.append({**c, "item": f"{s}|{i}|{j}",
                      "body": f"{qtext[s]}\n{blk('A',0)}\n\n{blk('B',1)}",
                      "focal_policy_favoured": "A" if c["d_focal"] > 0 else "B",
                      "attr_i_name": attrs[i]["name"], "attr_j_name": attrs[j]["name"]})

    F.mkdir(parents=True, exist_ok=True)
    (F / "comp_candidates.json").write_text(json.dumps(items, indent=1))
    print(f"candidate pool from {len(pool)} possible -> selected {len(items)}")
    print(f"  contexts spanned : {len({x['scenario'] for x in items})}")
    print(f"  by |d_focal|     : {dict(Counter(x['gap_stratum'] for x in items))}")
    print(f"  policy favours   : {dict(Counter(x['focal_policy_favoured'] for x in items))}")
    cc = Counter(x["scenario"] for x in items)
    print(f"  items per context: max={max(cc.values())}, >1 in {sum(1 for v in cc.values() if v>1)}")
    print(f"  |d_focal| tertile cuts: {cuts[0]:.0f}, {cuts[1]:.0f}")
    print(f"\n-> {F/'comp_candidates.json'}")


if __name__ == "__main__":
    main()
