"""Analyses A-F for the coordination pilot. Local only, no API calls.

All inference is cluster-bootstrapped on CONTEXT, because the 10 attribute pairs
within a context share the same weight vector and are not independent.
"""

import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from scipy import stats
from sklearn.linear_model import LogisticRegression

ROOT = Path(__file__).resolve().parent.parent
F = ROOT / "data" / "coord_pilot"
RNG = np.random.default_rng(20260906)
NB = 4000

items = {x["item"]: x for x in json.loads((F / "coord_items.json").read_text())}
res = json.loads((F / "coord_results.json").read_text())


def cluster_boot(units, fn, n=NB):
    """units: list of context ids. fn(list_of_contexts) -> scalar or None."""
    out = []
    for _ in range(n):
        pick = [units[i] for i in RNG.integers(0, len(units), len(units))]
        v = fn(pick)
        if v is not None and np.isfinite(v):
            out.append(v)
    a = np.array(out)
    return float(np.percentile(a, 2.5)), float(np.percentile(a, 97.5)), a


def main():
    by = defaultdict(lambda: defaultdict(list))
    invalid = Counter()
    for r in res:
        if r.get("choice") in ("A", "B"):
            by[r["arm"]][r["item"]].append(r["choice"])
        else:
            invalid[r["arm"]] += 1
    print("=" * 74)
    print("COORDINATION PILOT -- behavioural bridge (temperature 1.0)")
    print("=" * 74)
    for arm in ("coord", "control"):
        n = sum(len(v) for v in by[arm].values())
        print(f"  {arm:8s} valid={n:5d}  invalid={invalid[arm]:3d}  items={len(by[arm])}")

    ctx_of = {it: items[it]["scenario"] for it in items}
    contexts = sorted({v for v in ctx_of.values()})

    # exclude exact ties (d_learned == 0): no prediction is defined
    usable = [it for it in items if items[it]["favoured_by_learned"] is not None]
    ties = len(items) - len(usable)
    print(f"  items with a defined learned-favoured option: {len(usable)}/{len(items)} "
          f"(ties excluded: {ties})")

    for arm in ("coord", "control"):
        print("\n" + "=" * 74)
        print(f"ARM: {arm}")
        print("=" * 74)
        ch = by[arm]

        # ---- A. policy preference ---------------------------------------
        def rate(cs, subset=None, key="favoured_by_learned"):
            hit = tot = 0
            for it in (subset or usable):
                if ctx_of[it] not in cs:
                    continue
                fav = items[it][key]
                if fav is None:
                    continue
                for c in ch.get(it, []):
                    tot += 1; hit += (c == fav)
            return hit / tot if tot else None
        p = rate(set(contexts))
        lo, hi, _ = cluster_boot(contexts, lambda cs: rate(set(cs)))
        print(f"[A] P(choose higher-LEARNED-weight option) = {p:.4f}  95% CI [{lo:.4f},{hi:.4f}]")
        pt = rate(set(contexts), key="favoured_by_true")
        lot, hit_, _ = cluster_boot(contexts, lambda cs: rate(set(cs), key="favoured_by_true"))
        print(f"    (same for TRUE-weight option)          = {pt:.4f}  95% CI [{lot:.4f},{hit_:.4f}]")

        # ---- B. weight gap gradient --------------------------------------
        X, y, cl = [], [], []
        for it in usable:
            g = abs(items[it]["d_learned"])
            for c in ch.get(it, []):
                X.append([g]); y.append(1 if c == items[it]["favoured_by_learned"] else 0)
                cl.append(ctx_of[it])
        X = np.array(X); y = np.array(y); cl = np.array(cl)
        def slope(cs):
            m = np.isin(cl, list(cs))
            if len(np.unique(y[m])) < 2:
                return None
            return LogisticRegression(max_iter=2000).fit(X[m], y[m]).coef_[0][0]
        b = slope(set(contexts))
        blo, bhi, bd = cluster_boot(contexts, lambda cs: slope(set(cs)))
        print(f"[B] logistic slope on |d_learned| = {b:+.5f} per unit  95% CI [{blo:+.5f},{bhi:+.5f}]"
              f"  P(slope<=0)={float((bd<=0).mean()):.4f}")
        # rate by gap tertile
        gaps = np.array([abs(items[it]["d_learned"]) for it in usable])
        t1, t2 = np.percentile(gaps, [33.3, 66.7])
        for lab, sel in (("low", gaps <= t1), ("mid", (gaps > t1) & (gaps <= t2)), ("high", gaps > t2)):
            ss = [it for it, k in zip(usable, sel) if k]
            print(f"      |d_learned| {lab:4s} (n={len(ss):3d} items): "
                  f"P(favoured)={rate(set(contexts), subset=ss):.4f}")

        # ---- C/D. agreement vs independence null -------------------------
        obs_pairs = pred = tot_pairs = 0
        per_item = []
        for it in usable:
            cs = ch.get(it, [])
            if len(cs) < 2:
                continue
            k = len(cs) // 2
            a1, a2 = cs[:k], cs[k:2*k]
            ag = sum(1 for x, yv in zip(a1, a2) if x == yv)
            obs_pairs += ag; tot_pairs += k
            pA = sum(1 for c in cs if c == "A") / len(cs)
            pred += (pA**2 + (1-pA)**2) * k
            per_item.append((it, ag/k if k else np.nan, pA**2 + (1-pA)**2))
        print(f"[C] observed pairwise agreement = {obs_pairs/tot_pairs:.4f}  ({tot_pairs} pairs)")
        print(f"[D] predicted under independence (mean p^2+(1-p)^2) = {pred/tot_pairs:.4f}")
        print(f"    difference (obs - predicted) = {(obs_pairs-pred)/tot_pairs:+.4f}")

        # ---- F. agreement vs |d_learned| ---------------------------------
        g = np.array([abs(items[it]["d_learned"]) for it, _, _ in per_item])
        a = np.array([x[1] for x in per_item])
        rr = stats.spearmanr(g, a)
        print(f"[F] Spearman(agreement, |d_learned|) = {rr.statistic:+.4f} (p={rr.pvalue:.4g}, "
              f"n={len(g)} items)")

        # ---- E. learned vs true, on sign-disagreement items --------------
        dis = [it for it in usable if items[it]["sign_disagree"]]
        pl = rate(set(contexts), subset=dis, key="favoured_by_learned")
        dlo, dhi, dd = cluster_boot(contexts,
                                    lambda cs: rate(set(cs), subset=dis, key="favoured_by_learned"))
        print(f"[E] SIGN-DISAGREEMENT items only (n={len(dis)}):")
        print(f"    P(choose LEARNED-favoured) = {pl:.4f}  95% CI [{dlo:.4f},{dhi:.4f}]")
        print(f"    (= 1 - P(choose TRUE-favoured), these are opposite by construction)")
        print(f"    P(<=0.5) under bootstrap = {float((dd<=0.5).mean()):.4f}")

    json.dump({"note": "see stdout"}, open(F / "coord_analysis.json", "w"))


if __name__ == "__main__":
    main()
