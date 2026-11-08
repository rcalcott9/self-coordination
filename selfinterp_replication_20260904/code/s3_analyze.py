"""Study 3 analysis. Local only.

Primary: the within-item partner-induced reversal on confirmed divergent items,
oriented so 1 = Focal complemented the FT modal, 0 = complemented the Claude modal.

    P(FT-complement | COPY) - P(FT-complement | CLAUDE)      expected POSITIVE

Confirmatory: Focal choice ~ Partner Identity x Partner-Policy Divergence, with a
context-clustered bootstrap and a paired-by-item bootstrap as robustness.

COPY-appropriate + CLAUDE-chance is reported as strategic self-policy use, NOT as
relational adaptation.
"""

import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from scipy import stats

ROOT = Path(__file__).resolve().parent.parent
F = ROOT / "data" / "study3"
RNG = np.random.default_rng(20260909)
NB = 4000


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
    conf = {r["item"]: r for r in json.loads((F / "s3_confirmed.json").read_text())}
    focal = json.loads((F / "s3_focal.json").read_text())

    div = [k for k, r in conf.items() if r["stable_C"] and r["cls_C"] == "DIVERGENT"]
    agr = [k for k, r in conf.items() if r["stable_C"] and r["cls_C"] == "AGREEMENT"]
    ctx = {k: conf[k]["scenario"] for k in conf}
    print("=" * 72)
    print("STUDY 3 — partner-sensitive complementary coordination")
    print("=" * 72)
    print(f"confirmed DIVERGENT={len(div)}  AGREEMENT={len(agr)}  "
          f"demoted/unstable={len(conf)-len(div)-len(agr)}")

    by = defaultdict(lambda: defaultdict(list))
    bad = Counter()
    for r in focal:
        if r.get("choice") in ("A", "B"):
            by[r["cond"]][r["item"]].append(r)
        else:
            bad[r["cond"]] += 1
    print(f"parse failures by condition: {dict(bad) or 'none'}")
    for c in ("COPY", "CLAUDE", "INFORMED", "ORDINARY"):
        print(f"  {c:9s} trials={sum(len(v) for v in by[c].values()):5d} "
              f"items={len(by[c])}")

    # ---------- primary: FT-complement rate on divergent items ------------
    def ftcomp(cond, items, contexts=None):
        hit = tot = 0
        for it in items:
            if contexts is not None and ctx[it] not in contexts:
                continue
            fm = conf[it]["ft_modal_C"]
            comp_ft = "B" if fm == "A" else "A"      # complement of the FT modal
            for r in by[cond].get(it, []):
                tot += 1; hit += (r["choice"] == comp_ft)
        return hit / tot if tot else None

    contexts = sorted({ctx[k] for k in div})
    pc, pl = ftcomp("COPY", div), ftcomp("CLAUDE", div)
    lo, hi, dist = boot(contexts, lambda cs: (
        None if ftcomp("COPY", div, set(cs)) is None or ftcomp("CLAUDE", div, set(cs)) is None
        else ftcomp("COPY", div, set(cs)) - ftcomp("CLAUDE", div, set(cs))))
    print("\n" + "=" * 72)
    print("PRIMARY — within-item reversal on DIVERGENT items")
    print("  (1 = complement FT modal, 0 = complement Claude modal)")
    print("=" * 72)
    print(f"  P(FT-complement | COPY)   = {pc:.4f}")
    print(f"  P(FT-complement | CLAUDE) = {pl:.4f}")
    print(f"  DIFFERENCE                = {pc-pl:+.4f}   95% CI [{lo:+.4f}, {hi:+.4f}]")
    print(f"  P(difference <= 0)        = {float((dist<=0).mean()):.4f}")

    # paired-by-item bootstrap as robustness
    per_item = []
    for it in div:
        a = by["COPY"].get(it, []); b = by["CLAUDE"].get(it, [])
        if not a or not b:
            continue
        fm = conf[it]["ft_modal_C"]; cf = "B" if fm == "A" else "A"
        per_item.append((np.mean([r["choice"] == cf for r in a]),
                         np.mean([r["choice"] == cf for r in b])))
    d = np.array([x[0] - x[1] for x in per_item])
    plo, phi, _ = boot(list(range(len(d))), lambda idx: float(np.mean(d[list(idx)])))
    print(f"  paired-by-item mean diff  = {d.mean():+.4f}  95% CI [{plo:+.4f}, {phi:+.4f}]")
    print(f"  items shifting in predicted direction: {int((d>0).sum())}/{len(d)}  "
          f"(sign test p={stats.binomtest(int((d>0).sum()), len(d), 0.5).pvalue:.4g})")

    # ---------- agreement-item control ------------------------------------
    print("\n" + "=" * 72)
    print("CONTROL — identity effect on AGREEMENT items (should be ~0)")
    print("=" * 72)
    ac, al = ftcomp("COPY", agr), ftcomp("CLAUDE", agr)
    actx = sorted({ctx[k] for k in agr})
    alo, ahi, adist = boot(actx, lambda cs: (
        None if ftcomp("COPY", agr, set(cs)) is None or ftcomp("CLAUDE", agr, set(cs)) is None
        else ftcomp("COPY", agr, set(cs)) - ftcomp("CLAUDE", agr, set(cs))))
    print(f"  P(FT-complement | COPY)   = {ac:.4f}")
    print(f"  P(FT-complement | CLAUDE) = {al:.4f}")
    print(f"  DIFFERENCE                = {ac-al:+.4f}   95% CI [{alo:+.4f}, {ahi:+.4f}]")

    # ---------- interaction ------------------------------------------------
    allctx = sorted(set(contexts) | set(actx))
    def inter(cs):
        s = set(cs)
        a = ftcomp("COPY", div, s); b = ftcomp("CLAUDE", div, s)
        cc = ftcomp("COPY", agr, s); dd = ftcomp("CLAUDE", agr, s)
        if None in (a, b, cc, dd):
            return None
        return (a - b) - (cc - dd)
    ilo, ihi, idist = boot(allctx, inter)
    iv = inter(allctx)
    print("\n" + "=" * 72)
    print("CONFIRMATORY — Partner Identity x Divergence interaction")
    print("=" * 72)
    print(f"  (COPY-CLAUDE | divergent) - (COPY-CLAUDE | agreement) = {iv:+.4f}")
    print(f"  95% CI [{ilo:+.4f}, {ihi:+.4f}]   P(<=0) = {float((idist<=0).mean()):.4f}")

    # ---------- partner-appropriate accuracy & realized success ------------
    print("\n" + "=" * 72)
    print("SECONDARY")
    print("=" * 72)
    for lab, items in (("divergent", div), ("agreement", agr)):
        for cond, key in (("COPY", "ft_modal_C"), ("CLAUDE", "cl_modal_C")):
            hit = tot = 0
            for it in items:
                m = conf[it][key]; comp = "B" if m == "A" else "A"
                for r in by[cond].get(it, []):
                    tot += 1; hit += (r["choice"] == comp)
            print(f"  partner-appropriate | {cond:6s} {lab:9s} = {hit/tot:.4f}" if tot else "")
    for cond in ("COPY", "CLAUDE"):
        for lab, items in (("divergent", div), ("agreement", agr)):
            hit = tot = 0
            for it in items:
                for r in by[cond].get(it, []):
                    if r.get("worker_choice"):
                        tot += 1; hit += (r["choice"] != r["worker_choice"])
            if tot:
                print(f"  realized success    | {cond:6s} {lab:9s} = {hit/tot:.4f}")

    # ---------- INFORMED positive control ----------------------------------
    hit = tot = 0
    for it, rows in by["INFORMED"].items():
        for r in rows:
            told = r.get("told") or r.get("worker_choice")
            if told:
                tot += 1; hit += (r["choice"] != told)
    print(f"\n  INFORMED positive control (correct = complement told) = "
          f"{hit/tot:.4f}  n={tot}" if tot else "\n  INFORMED: no data")

    # ---------- ordinary baseline / anti-heuristic --------------------------
    ordm = {}
    for it, rows in by["ORDINARY"].items():
        a = sum(1 for r in rows if r["choice"] == "A")
        ordm[it] = "A" if a >= len(rows) / 2 else "B"
    for cond in ("COPY", "CLAUDE"):
        flips = tot = 0
        for it in div:
            if it not in ordm:
                continue
            for r in by[cond].get(it, []):
                tot += 1; flips += (r["choice"] != ordm[it])
        if tot:
            print(f"  flip vs own ordinary modal | {cond:6s} divergent = {flips/tot:.4f}")

    json.dump({"n_divergent": len(div), "n_agreement": len(agr),
               "primary": {"copy": pc, "claude": pl, "diff": pc - pl, "ci": [lo, hi],
                           "p_le_0": float((dist <= 0).mean()),
                           "paired_mean": float(d.mean()), "paired_ci": [plo, phi],
                           "items_predicted_direction": int((d > 0).sum()), "n_items": len(d)},
               "agreement_control": {"copy": ac, "claude": al, "diff": ac - al,
                                     "ci": [alo, ahi]},
               "interaction": {"value": iv, "ci": [ilo, ihi],
                               "p_le_0": float((idist <= 0).mean())},
               "parse_failures": dict(bad)},
              open(F / "s3_results.json", "w"), indent=2)
    print(f"\n-> {F/'s3_results.json'}")


if __name__ == "__main__":
    main()
