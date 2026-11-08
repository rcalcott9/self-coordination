"""Apply the PRE-SPECIFIED freezing rule to the re-measured candidates.

Rule (fixed before the re-measurement was run):
  retain if  stability_gpt >= .60  AND  stability_claude >= .60  AND  TVD >= .40
  if >= 8 survive -> freeze all survivors
  else            -> freeze the top 8 of the original 13 by min(stab_g, stab_c) x TVD,
                     using ONLY the fresh estimates
No new criteria are introduced after seeing results.
"""
import csv, glob, hashlib, json, os, sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
K = 4


def tvd(p, q):
    return 0.5 * sum(abs(a - b) for a, b in zip(p, q))


def main(run=None):
    run = run or sorted(glob.glob(os.path.join(HERE, "results", "remeasure_*")))[-1]
    rows = list(csv.DictReader(open(os.path.join(run, "data", "parsed.csv"))))
    ok = [r for r in rows if r["chosen_item"] not in ("", "None")]
    print(f"rows {len(rows)}   parsed {len(ok)}   failures {len(rows)-len(ok)}")

    cnt = defaultdict(Counter)
    for r in ok:
        cnt[(r["sid"], r["actor"])][int(r["chosen_item"])] += 1
    old = {r["stimulus_id"]: r for r in
           csv.DictReader(open(os.path.join(HERE, "data", "candidates_ranked.csv")))}
    oldp = {r["stimulus_id"]: r for r in
            json.load(open(os.path.join(HERE, "data", "candidates_ranked.json")))}

    out = []
    for sid in sorted({r["sid"] for r in ok}):
        d = {}
        for a in ("gpt", "claude"):
            c = cnt[(sid, a)]; n = sum(c.values())
            d[a] = ([c.get(i, 0) / n for i in range(K)], n)
        pg, ng = d["gpt"]; pc, nc = d["claude"]
        sg, sc = max(pg), max(pc)
        t = tvd(pg, pc)
        out.append(dict(stimulus_id=sid, family=old[sid]["family"],
                        n_gpt=ng, n_claude=nc,
                        p_gpt=[round(x, 4) for x in pg], p_claude=[round(x, 4) for x in pc],
                        modal_gpt=pg.index(max(pg)), modal_claude=pc.index(max(pc)),
                        stability_gpt=round(sg, 4), stability_claude=round(sc, 4),
                        min_stability=round(min(sg, sc), 4), tvd=round(t, 4),
                        score=round(min(sg, sc) * t, 4),
                        old_stab_gpt=float(old[sid]["stability_gpt"]),
                        old_stab_claude=float(old[sid]["stability_claude"]),
                        old_tvd=float(old[sid]["tvd"]),
                        old_p_gpt=oldp[sid]["p_gpt"], old_p_claude=oldp[sid]["p_claude"]))
    out.sort(key=lambda r: -r["score"])

    print(f"\n{'stimulus':<20}{'stab_gpt':>18}{'stab_cla':>18}{'TVD':>16}")
    print(f"{'':<20}{'n24 -> n100':>18}{'n24 -> n100':>18}{'n24 -> n100':>16}")
    print("-" * 74)
    for r in out:
        print(f"{r['stimulus_id']:<20}"
              f"{r['old_stab_gpt']:>8.2f} ->{r['stability_gpt']:>7.2f}"
              f"{r['old_stab_claude']:>8.2f} ->{r['stability_claude']:>7.2f}"
              f"{r['old_tvd']:>7.2f} ->{r['tvd']:>7.2f}")

    import statistics as st
    dg = [r["stability_gpt"] - r["old_stab_gpt"] for r in out]
    dc = [r["stability_claude"] - r["old_stab_claude"] for r in out]
    dt = [r["tvd"] - r["old_tvd"] for r in out]
    print(f"\nREGRESSION TO THE MEAN")
    print(f"  stability GPT    mean change {st.mean(dg):+.3f}  ({sum(1 for x in dg if x<0)}/13 down)")
    print(f"  stability Opus   mean change {st.mean(dc):+.3f}  ({sum(1 for x in dc if x<0)}/13 down)")
    print(f"  TVD              mean change {st.mean(dt):+.3f}  ({sum(1 for x in dt if x<0)}/13 down)")
    print(f"  mean TVD         {st.mean(r['old_tvd'] for r in out):.3f} -> {st.mean(r['tvd'] for r in out):.3f}")

    passed = [r for r in out if r["stability_gpt"] >= .60 and r["stability_claude"] >= .60
              and r["tvd"] >= .40]
    print(f"\nTHRESHOLDS (stab_gpt>=.60, stab_opus>=.60, TVD>=.40): {len(passed)}/13 pass")
    for r in out:
        why = []
        if r["stability_gpt"] < .60: why.append(f"stab_gpt {r['stability_gpt']:.2f}")
        if r["stability_claude"] < .60: why.append(f"stab_opus {r['stability_claude']:.2f}")
        if r["tvd"] < .40: why.append(f"TVD {r['tvd']:.2f}")
        print(f"  {r['stimulus_id']:<20} {'PASS' if not why else 'fail: ' + ', '.join(why)}")

    if len(passed) >= 8:
        frozen, rule = passed, f"all {len(passed)} survivors (>=8 passed)"
    else:
        frozen, rule = out[:8], "top 8 of 13 by fresh min(stab)xTVD (<8 passed)"
    print(f"\nFREEZING RULE APPLIED: {rule}")
    print(f"FINAL SET: {len(frozen)} items")
    fam = Counter(r["family"] for r in frozen)
    print(f"  families: {dict(fam)}")
    top = fam.most_common(1)[0]
    print(f"  largest family: {top[0]} = {top[1]}/{len(frozen)} ({top[1]/len(frozen):.0%})")
    for r in frozen:
        print(f"   {r['stimulus_id']:<20} stab {r['stability_gpt']:.2f}/{r['stability_claude']:.2f}"
              f"  TVD {r['tvd']:.2f}  modal {r['modal_gpt']}/{r['modal_claude']}")

    p = os.path.join(HERE, "data", "frozen_items.json")
    json.dump(frozen, open(p, "w"), indent=1)
    h = hashlib.sha256(open(p, "rb").read()).hexdigest()
    open(p + ".sha256", "w").write(h + "\n")
    json.dump(out, open(os.path.join(HERE, "data", "remeasured_all13.json"), "w"), indent=1)
    print(f"\nfrozen -> {p}")
    print(f"sha256  {h}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
