"""Study 2 item selection — reads Stage A 4-option data READ-ONLY, writes only into this dir.

Selection metric, fixed before any Study 2 data exists:

  stability_m  = max_k p_m(k)              modal share within model m (n=24)
  divergence   = TVD(p_gpt, p_claude)      total variation distance between the two
                                           empirical action distributions
  score        = min(stability_gpt, stability_claude) * divergence

min() rather than mean(): an item is only usable if BOTH models are individually predictable.
TVD rather than JS/KL: bounded [0,1], linear in probability mass, and directly interpretable
as "fraction of probability mass that would have to move".
"""
import csv, json, os
from collections import defaultdict

SRC = ("/Users/calypsocalcott/Desktop/Coordination/Self_Coordination/"
       "study2_4opt_20260830/data")
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
K = 4


def dist(counts_json):
    c = {int(k): v for k, v in json.loads(counts_json).items()}
    n = sum(c.values())
    return [c.get(i, 0) / n for i in range(K)], n


def main():
    rows = []
    for f in ("cell_metrics_discovery_batch1.csv", "cell_metrics_discovery_batch2.csv"):
        rows += list(csv.DictReader(open(os.path.join(SRC, f))))
    by = defaultdict(dict)
    for r in rows:
        by[r["stimulus_id"]][r["model"]] = r

    out = []
    for sid, d in by.items():
        if len(d) != 2:
            continue
        pg, ng = dist(d["gpt"]["item_counts"])
        pc, nc = dist(d["claude"]["item_counts"])
        tvd = 0.5 * sum(abs(a - b) for a, b in zip(pg, pc))
        sg, sc = max(pg), max(pc)
        out.append(dict(stimulus_id=sid, family=d["gpt"]["family"],
                        p_gpt=[round(x, 4) for x in pg], p_claude=[round(x, 4) for x in pc],
                        modal_gpt=pg.index(max(pg)), modal_claude=pc.index(max(pc)),
                        stability_gpt=round(sg, 4), stability_claude=round(sc, 4),
                        min_stability=round(min(sg, sc), 4), tvd=round(tvd, 4),
                        score=round(min(sg, sc) * tvd, 4),
                        pos_bias_gpt=float(d["gpt"]["position_bias"]),
                        pos_bias_claude=float(d["claude"]["position_bias"]),
                        n_gpt=ng, n_claude=nc))
    out.sort(key=lambda r: -r["score"])
    os.makedirs(os.path.join(HERE, "data"), exist_ok=True)
    with open(os.path.join(HERE, "data", "candidates_ranked.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=[k for k in out[0] if k not in ("p_gpt", "p_claude")])
        w.writeheader()
        for r in out:
            w.writerow({k: v for k, v in r.items() if k not in ("p_gpt", "p_claude")})
    json.dump(out, open(os.path.join(HERE, "data", "candidates_ranked.json"), "w"), indent=1)
    print(f"{len(out)} stimuli with both models (n=24 each)")
    print(f"\n{'rank':>4} {'stimulus':<22}{'stab_gpt':>9}{'stab_cla':>9}{'TVD':>7}{'score':>7}"
          f"{'modal g/c':>11}")
    for i, r in enumerate(out[:25], 1):
        print(f"{i:>4} {r['stimulus_id']:<22}{r['stability_gpt']:>9.2f}"
              f"{r['stability_claude']:>9.2f}{r['tvd']:>7.2f}{r['score']:>7.2f}"
              f"{str(r['modal_gpt'])+'/'+str(r['modal_claude']):>11}")
    for t in (0.60, 0.70, 0.75, 0.80):
        n = sum(1 for r in out if r["min_stability"] >= t and r["tvd"] >= 0.50)
        print(f"  min_stability >= {t:.2f} AND TVD >= 0.50 : {n:>3} items")
    for t in (0.50, 0.60, 0.70):
        n = sum(1 for r in out if r["min_stability"] >= 0.70 and r["tvd"] >= t)
        print(f"  min_stability >= 0.70 AND TVD >= {t:.2f} : {n:>3} items")


if __name__ == "__main__":
    main()
