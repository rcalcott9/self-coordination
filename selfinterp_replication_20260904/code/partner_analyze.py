"""Analyses for the partner-conditional deviation pilot. Local only.

Contrast hierarchy is fixed in advance:
  PRIMARY   SAME vs UNKNOWN                 -- does same-model identity increase
                                               reliance on the focal model's own policy?
  CONTROL   DIFF_INFORMED vs DIFF_UNINFORMED -- does EXPLICIT partner information move
                                               behaviour at all? (instruction-following;
                                               not evidence of partner modelling)
  SECONDARY SAME vs DIFF_UNINFORMED          -- identity only; no directional info in DU
  DESCRIPTIVE DIFF_INFORMED vs SAME          -- different implied partner policies

Partner-preference wording is deliberately "predicted"/"model-based" throughout.
"""

import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression

ROOT = Path(__file__).resolve().parent.parent
F = ROOT / "data" / "partner_pilot"
RNG = np.random.default_rng(20260907)
NB = 4000
CONDS = ["SAME", "UNKNOWN", "DIFF_UNINFORMED", "DIFF_INFORMED"]


def boot(units, fn, n=NB):
    out = []
    for _ in range(n):
        pick = [units[i] for i in RNG.integers(0, len(units), len(units))]
        v = fn(pick)
        if v is not None and np.isfinite(v):
            out.append(v)
    a = np.array(out)
    return float(np.percentile(a, 2.5)), float(np.percentile(a, 97.5)), a


def main():
    items = {x["item"]: x for x in json.loads((F / "partner_items.json").read_text())}
    res = json.loads((F / "partner_results.json").read_text())
    ctx_of = {k: v["scenario"] for k, v in items.items()}
    contexts = sorted(set(ctx_of.values()))

    ch = defaultdict(lambda: defaultdict(list))
    bad = Counter()
    for r in res:
        if r.get("choice") in ("A", "B"):
            ch[r["cond"]][r["item"]].append(r["choice"])
        else:
            bad[r["cond"]] += 1
    print("=" * 78)
    print("PARTNER-CONDITIONAL DEVIATION PILOT")
    print("=" * 78)
    for c in CONDS:
        n = sum(len(v) for v in ch[c].values())
        print(f"  {c:17s} valid={n:5d}  parse failures={bad[c]}")

    def rate(cs, cond, key="focal_favoured", subset=None):
        hit = tot = 0
        for it in (subset or items):
            if ctx_of[it] not in cs:
                continue
            fav = items[it][key]
            for x in ch[cond].get(it, []):
                tot += 1; hit += (x == fav)
        return hit / tot if tot else None

    print("\n" + "=" * 78)
    print("P(focal chooses its OWN higher-learned-weight option), by condition")
    print("=" * 78)
    summary = {}
    for c in CONDS:
        p = rate(set(contexts), c)
        lo, hi, _ = boot(contexts, lambda cs, c=c: rate(set(cs), c))
        summary[c] = p
        print(f"  {c:17s} {p:.4f}   95% CI [{lo:.4f}, {hi:.4f}]")

    print("\n  by focal-gap tertile:")
    print(f"  {'condition':17s} " + " ".join(f"{t:>10s}" for t in ("low", "medium", "high")))
    for c in CONDS:
        row = []
        for t in ("low", "medium", "high"):
            sub = [it for it in items if items[it]["tertile"] == t]
            row.append(rate(set(contexts), c, subset=sub))
        print(f"  {c:17s} " + " ".join(f"{v:10.4f}" for v in row))

    print("\n  P(choose PREDICTED partner-favoured option)  [= 1 - own, by construction]")
    for c in CONDS:
        p = rate(set(contexts), c, key="partner_predicted_favoured")
        print(f"  {c:17s} {p:.4f}")

    # ---------------- contrasts -------------------------------------------
    def contrast(a, b, subset=None, label=""):
        d = rate(set(contexts), a, subset=subset) - rate(set(contexts), b, subset=subset)
        lo, hi, dist = boot(contexts, lambda cs: (
            None if rate(set(cs), a, subset=subset) is None or rate(set(cs), b, subset=subset) is None
            else rate(set(cs), a, subset=subset) - rate(set(cs), b, subset=subset)))
        print(f"  {label:34s} {d:+.4f}  95% CI [{lo:+.4f}, {hi:+.4f}]  "
              f"P(<=0)={float((dist <= 0).mean()):.4f}")
        return {"diff": d, "ci": [lo, hi], "p_le_0": float((dist <= 0).mean())}

    print("\n" + "=" * 78)
    print("CONTRASTS on P(choose own-policy option)")
    print("=" * 78)
    out = {}
    print("\n PRIMARY")
    out["same_vs_unknown"] = contrast("SAME", "UNKNOWN", label="SAME - UNKNOWN")
    print("\n POSITIVE CONTROL (capability; instruction-following suffices)")
    out["informed_vs_uninformed"] = contrast("DIFF_INFORMED", "DIFF_UNINFORMED",
                                             label="DIFF_INFORMED - DIFF_UNINFORMED")
    print("\n SECONDARY (DIFF_UNINFORMED carries no directional partner info)")
    out["same_vs_diffunin"] = contrast("SAME", "DIFF_UNINFORMED", label="SAME - DIFF_UNINFORMED")
    print("\n DESCRIPTIVE (different implied partner policies; not ordinal)")
    out["informed_vs_same"] = contrast("DIFF_INFORMED", "SAME", label="DIFF_INFORMED - SAME")

    print("\n  primary + control contrasts within tertile:")
    for t in ("low", "medium", "high"):
        sub = [it for it in items if items[it]["tertile"] == t]
        print(f"   [{t}]")
        contrast("SAME", "UNKNOWN", subset=sub, label="  SAME - UNKNOWN")
        contrast("DIFF_INFORMED", "DIFF_UNINFORMED", subset=sub,
                 label="  DIFF_INFORMED - DIFF_UNINFORMED")

    # ---------------- logistic with interaction ---------------------------
    print("\n" + "=" * 78)
    print("TRIAL-LEVEL LOGISTIC: choice_own ~ |d_focal| * condition (ref = UNKNOWN)")
    print("=" * 78)
    rows = []
    for c in CONDS:
        for it in items:
            g = abs(items[it]["d_focal"])
            for x in ch[c].get(it, []):
                rows.append((g, c, 1 if x == items[it]["focal_favoured"] else 0, ctx_of[it]))
    g = np.array([r[0] for r in rows], float)
    cond = np.array([r[1] for r in rows])
    y = np.array([r[2] for r in rows])
    cl = np.array([r[3] for r in rows])
    gz = (g - g.mean()) / g.std()

    def design(mask):
        cols = [gz[mask]]
        for c in CONDS[:1] + CONDS[2:]:      # dummies for SAME, DIFF_UNIN, DIFF_INF
            d = (cond[mask] == c).astype(float)
            cols.append(d); cols.append(d * gz[mask])
        return np.column_stack(cols)
    names = ["|dw|"] + sum([[f"{c}", f"{c}x|dw|"] for c in CONDS[:1] + CONDS[2:]], [])

    def fit(cs):
        m = np.isin(cl, list(cs))
        if len(np.unique(y[m])) < 2:
            return None
        return LogisticRegression(max_iter=3000, C=1e6).fit(design(m), y[m]).coef_[0]
    base = fit(set(contexts))
    bl = []
    for _ in range(1500):
        pick = [contexts[i] for i in RNG.integers(0, len(contexts), len(contexts))]
        v = fit(set(pick))
        if v is not None:
            bl.append(v)
    bl = np.array(bl)
    for i, nm in enumerate(names):
        lo, hi = np.percentile(bl[:, i], [2.5, 97.5])
        star = "  *" if (lo > 0 or hi < 0) else ""
        print(f"  {nm:22s} {base[i]:+.4f}  95% CI [{lo:+.4f}, {hi:+.4f}]{star}")
    print("  (interaction terms are the partner-conditional moderation of own-policy reliance)")

    json.dump({"summary": summary, "contrasts": out,
               "logistic": {n: [float(base[i]), *np.percentile(bl[:, i], [2.5, 97.5]).tolist()]
                            for i, n in enumerate(names)},
               "parse_failures": dict(bad)},
              open(F / "partner_analysis.json", "w"), indent=2)
    print(f"\n-> {F/'partner_analysis.json'}")


if __name__ == "__main__":
    main()
