"""
§12.C CROSS-GENERATION TRANSPORT ANALYSIS - deliberately separate from the primary.

Compares the ORIGINAL 5.5/Opus-5 reliability map with the FRESH 5.4/4.8 map, both
measured by the identical Stage A procedure (same prompt sha8 3003ae1b, same 15 stimuli,
same n=60, same identity coding).

HARD CONSTRAINTS (spec §12.C)
  - must NOT redefine HIGH/LOW for the primary replication
  - must NOT be pooled into the replication claim
  - ZERO SELECTED-PAIR OVERLAP IS DESCRIPTIVE, NOT A TEST. Set overlap depends on the
    selection rule and the candidate pool, not only on instability. The statistical
    evidence for version instability is the measured per-stimulus change and sign
    reversals below, not the overlap count.

Run:  . replication_5_4_4_8/env.sh && python3 analyze_transport.py
"""
import csv, json, os
import psc_common as P

ORIG = os.path.expanduser("~/Desktop/Coordination/Self_Coordination/"
                          "policy_specific_self_coordination_20260812_1401")
OUT = os.path.join(P.EXP, "analysis", "transport")
FC = P.FC_CLEAN


def spearman(a, b):
    def rank(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(order):                       # average ties
            j = i
            while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
                j += 1
            avg = (i + j) / 2.0 + 1
            for k in range(i, j + 1):
                r[order[k]] = avg
            i = j + 1
        return r
    ra, rb = rank(a), rank(b)
    n = len(a)
    ma, mb = sum(ra) / n, sum(rb) / n
    num = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    den = (sum((x - ma) ** 2 for x in ra) * sum((y - mb) ** 2 for y in rb)) ** 0.5
    return num / den if den else float("nan")


def main():
    os.makedirs(OUT, exist_ok=True)
    new = {(r["model"], r["stimulus"]): r for r in
           csv.DictReader(open(os.path.join(P.DATA, "fresh_self_match.csv")))}
    old = {(r["model"], r["stimulus"]): r for r in
           csv.DictReader(open(os.path.join(ORIG, "data", "fresh_self_match.csv")))}

    rows = []
    for k in sorted(set(new) & set(old)):
        o, n = old[k], new[k]
        om, nm = float(o["self_match_unbiased"]), float(n["self_match_unbiased"])
        ofc, nfc = float(o["form_consistency"]), float(n["form_consistency"])
        ocl, och = float(o["self_match_ci_lo"]), float(o["self_match_ci_hi"])
        ncl, nch = float(n["self_match_ci_lo"]), float(n["self_match_ci_hi"])
        rows.append(dict(model=k[0], stimulus=k[1],
                         match_5_5=om, match_5_4=nm, delta=nm - om,
                         fc_5_5=ofc, fc_5_4=nfc,
                         rule_5_5=ofc >= FC, rule_5_4=nfc >= FC,
                         rule_flip=(ofc >= FC) != (nfc >= FC),
                         disjoint_ci=bool(och < ncl or nch < ocl)))

    print("\n=== §12.C CROSS-GENERATION TRANSPORT (descriptive) ===")
    print(f"\n  {'model':7} {'stimulus':16}{'5.5/O5':>8}{'5.4/O4.8':>10}{'delta':>8}"
          f"  rule 5.5->5.4   CIs")
    for r in sorted(rows, key=lambda x: (x["model"], -abs(x["delta"]))):
        print(f"  {r['model']:7} {r['stimulus']:16}{r['match_5_5']:8.3f}{r['match_5_4']:10.3f}"
              f"{r['delta']:+8.3f}   {str(r['rule_5_5'])[0]} -> {str(r['rule_5_4'])[0]}"
              f"{'  FLIP' if r['rule_flip'] else '      '}"
              f"{'  disjoint' if r['disjoint_ci'] else ''}")

    rho = spearman([r["match_5_5"] for r in rows], [r["match_5_4"] for r in rows])
    nflip = sum(r["rule_flip"] for r in rows)
    ndis = sum(r["disjoint_ci"] for r in rows)
    mean_abs = sum(abs(r["delta"]) for r in rows) / len(rows)

    # direction reversals relative to chance (0.5): convention -> chance or the reverse
    rev = [r for r in rows if (r["match_5_5"] > 0.6) != (r["match_5_4"] > 0.6)]

    print(f"\n  cells compared             : {len(rows)}")
    print(f"  Spearman rank correlation  : rho = {rho:+.3f}")
    print(f"  mean |change| in self-match: {mean_abs:.3f}")
    print(f"  form-rule status flips     : {nflip} of {len(rows)}")
    print(f"  disjoint bootstrap CIs     : {ndis} of {len(rows)}")
    print(f"  convention<->chance crosses: {len(rev)} of {len(rows)}")

    # pair overlap - DESCRIPTIVE ONLY
    o_ap = {(r["focal_model"], r["stimulus_high"], r["stimulus_low"])
            for r in csv.DictReader(open(os.path.join(ORIG, "matched_pairs.csv")))
            if str(r.get("approved", "")).lower() == "true"}
    n_ap = {(r["focal_model"], r["stimulus_high"], r["stimulus_low"])
            for r in csv.DictReader(open(os.path.join(P.EXP, "pairs", "approved_pairs.csv")))}
    print(f"\n  selected-pair overlap      : {len(o_ap & n_ap)} of {len(n_ap)}"
          f"   [DESCRIPTIVE - not a statistical test]")

    json.dump(dict(cells=rows, spearman_rho=rho, mean_abs_delta=mean_abs,
                   rule_flips=nflip, disjoint_cis=ndis,
                   convention_chance_crosses=len(rev),
                   pair_overlap=len(o_ap & n_ap), n_pairs_new=len(n_ap),
                   note="Pair overlap is descriptive, not a test of version instability."),
              open(os.path.join(OUT, "transport_results.json"), "w"), indent=2)
    print(f"\n  -> {OUT}/transport_results.json")


if __name__ == "__main__":
    main()
