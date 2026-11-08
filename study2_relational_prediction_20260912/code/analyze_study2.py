"""Study 2 analysis: relational gating G, plus the secondaries in ANALYSIS_PLAN.md."""
import glob, json, os, random, statistics as st, sys
from collections import defaultdict

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def tvd(p, q):
    return 0.5 * sum(abs(a - b) for a, b in zip(p, q))


def brier(p, q):
    return sum((a - b) ** 2 for a, b in zip(p, q))


def main(run=None):
    run = run or sorted(glob.glob(os.path.join(HERE, "results", "run_*")))[-1]
    rs = [json.loads(l) for l in open(os.path.join(run, "raw", "parsed.jsonl"))]
    emp = {r["stimulus_id"]: r for r in json.load(
        open(os.path.join(HERE, "data", "frozen_items.json")))}
    cell = defaultdict(list)
    for r in rs:
        cell[(r["stimulus_id"], r["focal"], r["condition"])].append(r["p_canonical"])
    mean = {k: [st.mean(x[i] for x in v) for i in range(4)] for k, v in cell.items()}

    rows = []
    for focal in ("gpt", "claude"):
        other = "claude" if focal == "gpt" else "gpt"
        for sid, e in emp.items():
            SELF = e[f"p_{'gpt' if focal=='gpt' else 'claude'}"]
            OTHER = e[f"p_{'claude' if focal=='gpt' else 'gpt'}"]
            c = mean.get((sid, focal, "COPY")); d = mean.get((sid, focal, "DIFFERENT"))
            if not c or not d:
                continue
            G = ((tvd(c, OTHER) - tvd(c, SELF)) - (tvd(d, OTHER) - tvd(d, SELF)))
            rows.append(dict(stimulus_id=sid, focal=focal, G=G,
                             shift=tvd(c, d),
                             copy_to_self=tvd(c, SELF), copy_to_other=tvd(c, OTHER),
                             diff_to_self=tvd(d, SELF), diff_to_other=tvd(d, OTHER),
                             brier_copy=brier(c, SELF), brier_diff=brier(d, OTHER)))
    print(f"{'focal':<8}{'n':>4}{'G':>9}{'95% CI':>22}{'shift':>8}"
          f"{'copy->SELF':>12}{'diff->OTHER':>13}")
    for focal in ("gpt", "claude"):
        g = [r for r in rows if r["focal"] == focal]
        if not g:
            continue
        G = st.mean(r["G"] for r in g)
        rng = random.Random(20260912); dr = []
        for _ in range(4000):
            bs = [g[rng.randrange(len(g))] for _ in range(len(g))]
            dr.append(st.mean(r["G"] for r in bs))
        dr.sort()
        print(f"{focal:<8}{len(g):>4}{G:>+9.4f}   [{dr[100]:+.4f}, {dr[3899]:+.4f}]"
              f"{st.mean(r['shift'] for r in g):>8.3f}"
              f"{st.mean(r['copy_to_self'] for r in g):>12.3f}"
              f"{st.mean(r['diff_to_other'] for r in g):>13.3f}")
    json.dump(rows, open(os.path.join(run, "item_level.json"), "w"), indent=1)
    print(f"\nitem-level -> {run}/item_level.json")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
