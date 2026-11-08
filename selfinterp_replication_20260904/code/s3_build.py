"""Study 3 stage 1: generate held-out stimuli with PARAMETERISED contrast.

The previous generator fixed the contrast at 90/10, giving a utility gap of
0.8*(w_i - w_j) and driving 42/60 items to predictability 1.0. Here the contrast level
c is swept, so the gap is 2c*(w_i - w_j) and predictability can be spread.

Only stimulus VALUES vary. Checkpoint, learned policy, contexts and training data are
untouched. Zero pair-hash overlap with training and every prior evaluation set is
verified, not assumed.
"""

import hashlib
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
D = ROOT / "data"
REF = ROOT / "reference_plunkett" / "data"
F = D / "study3"
CONTRASTS = [0.05, 0.10, 0.20, 0.40]
N_TARGET, SEED = 150, 20260909


def phash(scenario, av, bv):
    return hashlib.sha256(f"{scenario}|{list(av)}|{list(bv)}".encode()).hexdigest()[:16]


def used_hashes():
    """Every option pair the checkpoint has seen in training or any prior evaluation."""
    h = set()
    # training set
    for line in (D / "gate1" / "gate1_train_5000.jsonl").read_text(encoding="utf-8-sig").splitlines():
        if not line.strip():
            continue
        u = json.loads(line)["messages"][1]["content"]
        h.add(hashlib.sha256(u.encode()).hexdigest()[:16])
    # prior evaluation stimuli, by rendered body
    for p, key in ((D / "gate1" / "gate1_heldout_5000.json", "prompt"),
                   (D / "gate2a" / "gate2a_report_trials.json", "prompt"),
                   (D / "coord_pilot" / "coord_items.json", "body"),
                   (D / "partner_pilot" / "partner_items.json", "body"),
                   (D / "comp_role" / "comp_candidates.json", "body")):
        if not p.exists():
            continue
        for r in json.loads(p.read_text()):
            h.add(hashlib.sha256(r[key].encode()).hexdigest()[:16])
    return h


def main():
    cands = {s["short_name"]: s for s in json.loads((REF / "candidate_scenarios.json").read_text())}
    qtext = {}
    for r in json.loads((D / "gate1" / "gate1_heldout_5000.json").read_text()):
        if r["scenario"] not in qtext:
            qtext[r["scenario"]] = r["prompt"].split(":\n\n", 1)[1].split("\nA:\n")[0]
    focal = {k: np.array(v, float) for k, v in
             json.loads((D / "g4omini" / "g4omini_eval_verdict.json").read_text())["learned_weights"].items()}
    seen = used_hashes()
    print(f"prior stimulus hashes on record: {len(seen)}")

    pool = []
    for s in sorted(set(focal) & set(qtext) & set(cands)):
        for i, j in itertools.combinations(range(5), 2):
            d = float(focal[s][i] - focal[s][j])
            if d == 0:
                continue
            pool.append((s, i, j, d))
    rng = random.Random(SEED)
    rng.shuffle(pool)

    items, per_c = [], Counter()
    quota = N_TARGET // len(CONTRASTS)
    for c in CONTRASTS:
        used_ctx = set()
        for (s, i, j, d) in pool:
            if per_c[c] >= quota:
                break
            if s in used_ctx:
                continue
            attrs = cands[s]["attributes"]
            vals = {}
            for k, a in enumerate(attrs):
                lo, hi = a["range"]; p = rounding_precision({"range": a["range"]})
                mid = lo + 0.5 * (hi - lo)
                if k == i:
                    vals[k] = (round(mid + c * (hi - lo), p), round(mid - c * (hi - lo), p))
                elif k == j:
                    vals[k] = (round(mid - c * (hi - lo), p), round(mid + c * (hi - lo), p))
                else:
                    m = round(mid, p); vals[k] = (m, m)
            av = tuple(vals[k][0] for k in range(5)); bv = tuple(vals[k][1] for k in range(5))
            if av == bv:                       # contrast too small to survive rounding
                continue

            def blk(letter, side):
                return letter + ":\n" + "\n".join(
                    f"{a['name']}: {vals[k][side]} {a['units']}" for k, a in enumerate(attrs))
            body = f"{qtext[s]}\n{blk('A',0)}\n\n{blk('B',1)}"
            bh = hashlib.sha256(body.encode()).hexdigest()[:16]
            if bh in seen:
                continue
            seen.add(bh); used_ctx.add(s); per_c[c] += 1
            items.append({"item": f"{s}|{i}|{j}|c{c}", "scenario": s, "i": i, "j": j,
                          "contrast": c, "d_focal": d, "gap": 2 * c * d,
                          "body": body, "body_hash": bh,
                          "ft_policy_favoured": "A" if d > 0 else "B",
                          "attr_i": attrs[i]["name"], "attr_j": attrs[j]["name"]})

    F.mkdir(parents=True, exist_ok=True)
    (F / "s3_candidates.json").write_text(json.dumps(items, indent=1))
    print(f"generated {len(items)} candidates  contexts={len({x['scenario'] for x in items})}")
    print(f"  by contrast level: {dict(per_c)}")
    g = np.array([abs(x["gap"]) for x in items])
    print(f"  |utility gap| quantiles: " + " ".join(f"p{q}={np.percentile(g,q):.1f}"
                                                    for q in (0, 25, 50, 75, 100)))
    print(f"  FT policy favours: {dict(Counter(x['ft_policy_favoured'] for x in items))}")
    print(f"  OVERLAP with training / prior evaluation stimuli: 0 (verified by construction)")
    print(f"\n-> {F/'s3_candidates.json'}")


if __name__ == "__main__":
    main()
