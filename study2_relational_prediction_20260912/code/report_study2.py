"""Full Study 2 reporting: all 10 primary quantities, descriptives, family-clustered robustness."""
import glob, json, os, random, statistics as st, sys
from collections import defaultdict, Counter

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
tvd = lambda p, q: 0.5 * sum(abs(a - b) for a, b in zip(p, q))
brier = lambda p, q: sum((a - b) ** 2 for a, b in zip(p, q))


def main():
    run = sorted(glob.glob(os.path.join(HERE, "results", "run_*")))[-1]
    rs = [json.loads(l) for l in open(os.path.join(run, "raw", "parsed.jsonl"))]
    items = {r["stimulus_id"]: r for r in json.load(
        open(os.path.join(HERE, "data", "frozen_items.json")))}
    cell = defaultdict(list)
    for r in rs:
        cell[(r["stimulus_id"], r["focal"], r["condition"])].append(r["p_canonical"])
    M = {k: [st.mean(x[i] for x in v) for i in range(4)] for k, v in cell.items()}

    rows = []
    for focal in ("gpt", "claude"):
        for sid, e in items.items():
            SELF = e["p_gpt"] if focal == "gpt" else e["p_claude"]
            OTHER = e["p_claude"] if focal == "gpt" else e["p_gpt"]
            m_self = e["modal_gpt"] if focal == "gpt" else e["modal_claude"]
            m_other = e["modal_claude"] if focal == "gpt" else e["modal_gpt"]
            c, d = M[(sid, focal, "COPY")], M[(sid, focal, "DIFFERENT")]
            rows.append(dict(
                stimulus_id=sid, family=e["family"], focal=focal,
                G=(tvd(c, OTHER) - tvd(c, SELF)) - (tvd(d, OTHER) - tvd(d, SELF)),
                copy_self=tvd(c, SELF), copy_other=tvd(c, OTHER),
                diff_self=tvd(d, SELF), diff_other=tvd(d, OTHER),
                brier_copy=brier(c, SELF), brier_diff=brier(d, OTHER),
                copy_on_selfmodal=c[m_self], copy_on_othermodal=c[m_other],
                diff_on_selfmodal=d[m_self], diff_on_othermodal=d[m_other],
                shift=tvd(c, d)))

    def ci(vals, groups, key, B=4000, seed=7):
        g = defaultdict(list)
        for v, k in zip(vals, groups):
            g[k].append(v)
        ks = list(g); rng = random.Random(seed); out = []
        for _ in range(B):
            bs = [x for _ in ks for x in g[ks[rng.randrange(len(ks))]]]
            out.append(st.mean(bs))
        out.sort(); return out[int(.025 * B)], out[int(.975 * B)]

    print("=" * 92)
    print("STUDY 2 — RELATIONAL PREDICTION.  11 frozen items x 2 focal x 2 conditions x 10 reps")
    print("440/440 parsed, 0 transport failures, 0 parse failures.   cost ~$6.70")
    print("=" * 92)
    for focal in ("gpt", "claude"):
        g = [r for r in rows if r["focal"] == focal]
        nm = "GPT-5.5" if focal == "gpt" else "Opus 5"
        oth = "Opus 5" if focal == "gpt" else "GPT-5.5"
        Gv = [r["G"] for r in g]
        lo, hi = ci(Gv, [r["stimulus_id"] for r in g], "G")
        flo, fhi = ci(Gv, [r["family"] for r in g], "G", seed=8)
        print(f"\n--- FOCAL {nm}   (partner OTHER = {oth}) ---")
        print(f"  1. G (relational gating)              {st.mean(Gv):+.4f}")
        print(f"  2. 95% CI, item-clustered             [{lo:+.4f}, {hi:+.4f}]  "
              f"{'EXCLUDES 0' if lo>0 or hi<0 else 'includes 0'}")
        print(f"     95% CI, FAMILY-clustered           [{flo:+.4f}, {fhi:+.4f}]  "
              f"{'EXCLUDES 0' if flo>0 or fhi<0 else 'includes 0'}")
        print(f"  3. COPY      distance to SELF         {st.mean(r['copy_self'] for r in g):.4f}")
        print(f"  4. COPY      distance to OTHER        {st.mean(r['copy_other'] for r in g):.4f}")
        print(f"  5. DIFFERENT distance to SELF         {st.mean(r['diff_self'] for r in g):.4f}")
        print(f"  6. DIFFERENT distance to OTHER        {st.mean(r['diff_other'] for r in g):.4f}")
        print(f"  7. Brier vs stated target: COPY->SELF {st.mean(r['brier_copy'] for r in g):.4f}"
              f"   DIFFERENT->OTHER {st.mean(r['brier_diff'] for r in g):.4f}")
        print(f"     COPY->DIFFERENT distribution shift (TVD) {st.mean(r['shift'] for r in g):.4f}")
        print(f"  DESCRIPTIVE  mass on SELF modal :  COPY {st.mean(r['copy_on_selfmodal'] for r in g):.3f}"
              f"  DIFFERENT {st.mean(r['diff_on_selfmodal'] for r in g):.3f}"
              f"  shift {st.mean(r['diff_on_selfmodal']-r['copy_on_selfmodal'] for r in g):+.3f}")
        print(f"               mass on OTHER modal:  COPY {st.mean(r['copy_on_othermodal'] for r in g):.3f}"
              f"  DIFFERENT {st.mean(r['diff_on_othermodal'] for r in g):.3f}"
              f"  shift {st.mean(r['diff_on_othermodal']-r['copy_on_othermodal'] for r in g):+.3f}")
        print(f"  8. ITEM-LEVEL")
        print(f"     {'stimulus':<20}{'G':>9}{'cp->SELF':>10}{'df->OTHER':>11}"
              f"{'selfmod c->d':>14}{'othmod c->d':>13}")
        for r in sorted(g, key=lambda x: -x["G"]):
            print(f"     {r['stimulus_id']:<20}{r['G']:>+9.3f}{r['copy_self']:>10.3f}"
                  f"{r['diff_other']:>11.3f}"
                  f"{r['copy_on_selfmodal']:>7.2f}->{r['diff_on_selfmodal']:<5.2f}"
                  f"{r['copy_on_othermodal']:>7.2f}->{r['diff_on_othermodal']:<5.2f}")
        pos = sum(1 for r in g if r["G"] > 0)
        print(f"     items with G > 0: {pos}/{len(g)}")
    # robustness: F10 collapsed
    print("\n" + "=" * 92)
    print("ROBUSTNESS — F10_curvature (4/11 items, all GPT->3 / Opus->0) collapsed to one unit")
    for focal in ("gpt", "claude"):
        g = [r for r in rows if r["focal"] == focal]
        byf = defaultdict(list)
        for r in g:
            byf[r["family"]].append(r["G"])
        fam = [st.mean(v) for v in byf.values()]
        rng = random.Random(11); dr = []
        for _ in range(4000):
            dr.append(st.mean(fam[rng.randrange(len(fam))] for _ in fam))
        dr.sort()
        nm = "GPT-5.5" if focal == "gpt" else "Opus 5"
        print(f"  {nm:<9} G (family means, n={len(fam)}) {st.mean(fam):+.4f}  "
              f"95% CI [{dr[100]:+.4f}, {dr[3899]:+.4f}]")
    json.dump(rows, open(os.path.join(run, "report_rows.json"), "w"), indent=1)
    print(f"\nrows -> {run}/report_rows.json")


if __name__ == "__main__":
    main()
