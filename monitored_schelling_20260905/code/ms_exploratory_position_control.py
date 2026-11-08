"""EXPLORATORY -- not part of the frozen confirmatory analysis.

Specified 2026-09-05, while Stage A2 was at 1000/2000 rows, BEFORE the final
monitor accuracy or content gap could be observed. Recorded here so the form of
the adjustment cannot have been chosen to suit the result.

MOTIVATION
    Stage A2 shows claude-opus-5 selecting the first DISPLAYED option at
    p ~= 0.104 against a 0.083 uniform baseline (z ~= 2.3 at n=992). The focal
    stage is clean (0.083 exactly, chi2(11)=13.4). Because the monitor's option
    order is shuffled INDEPENDENTLY of the focal model's, any position-driven
    monitor choice is uncorrelated with focal content -- it is noise that makes
    the monitor look WORSE at prediction and so INFLATES the content gap this
    study is designed to detect. The bias therefore favours the study hypothesis
    and must be adjusted for rather than noted.

ESTIMATOR
    For item i let f_i be the focal modal option. The monitor's realised order
    places f_i at displayed position q in {1..12}, and q is uniform by
    construction. Define

        a_i(q) = P(monitor chooses f_i | f_i displayed at position q)

    The naive monitor accuracy pooled over q is a consistent estimate of
    position-free accuracy ONLY if a_i(q) is flat in q. If the monitor over-picks
    position 1, then a_i(1) > a_i(q>1) and pooling is fine in expectation -- but
    the VARIANCE attributable to position is real, and more importantly the
    monitor is spending choice mass on position rather than content.

    Two quantities are reported:

    (1) STRATIFIED accuracy: mean over q of a_i(q), each position weighted 1/12
        equally. Equals the naive estimate when position is uninformative;
        diverges when it is not. This is the primary adjusted number.

    (2) POSITION-1-EXCLUDED accuracy: a_i computed on monitor calls where f_i
        did NOT land in position 1, rescaled. This discards the contaminated
        stratum entirely -- a conservative bound in the direction AGAINST the
        study hypothesis (it removes the trials where the monitor gets a free
        hit, but also removes its position-driven misses).

    The confirmatory gap is recomputed under each. If the GO verdict flips under
    either, the Phase 1 result is reported as position-contingent, not as a
    clean content effect.

Reads only the frozen raw files; writes nothing the confirmatory pipeline reads.
"""
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
F = ROOT / "data"
NOPT = 12


def load(p):
    return [r for r in json.loads((F / p).read_text()) if r.get("choice")]


def main():
    foc, mon = load("ms_raw_focal.json"), load("ms_raw_monitor.json")
    fby, mby = defaultdict(list), defaultdict(list)
    for r in foc: fby[r["item_id"]].append(r)
    for r in mon: mby[r["item_id"]].append(r)

    print("=" * 78)
    print("EXPLORATORY POSITION CONTROL  (specified at A2 n=1000, pre-result)")
    print("=" * 78)

    rows, naive_all, strat_all, excl_all, pcopy_all = [], [], [], [], []
    for iid in sorted(fby):
        fc = Counter(r["choice"] for r in fby[iid])
        f_i, fn = fc.most_common(1)[0]
        p_copy = fn / len(fby[iid])

        ms = mby.get(iid, [])
        if not ms:
            continue
        # naive: monitor mass on the focal modal option
        naive = sum(1 for r in ms if r["choice"] == f_i) / len(ms)

        # stratify by the position at which f_i was DISPLAYED to the monitor
        by_q = defaultdict(lambda: [0, 0])   # q -> [hits, n]
        for r in ms:
            q = r["order"].index(f_i) + 1 if f_i in r["order"] else None
            if q is None:
                continue
            by_q[q][1] += 1
            by_q[q][0] += (r["choice"] == f_i)
        seen = [q for q in by_q if by_q[q][1] > 0]
        strat = sum(by_q[q][0] / by_q[q][1] for q in seen) / len(seen) if seen else float("nan")

        ex_h = sum(by_q[q][0] for q in by_q if q != 1)
        ex_n = sum(by_q[q][1] for q in by_q if q != 1)
        excl = ex_h / ex_n if ex_n else float("nan")

        rows.append((iid, p_copy, naive, strat, excl, by_q.get(1, [0, 0])))
        naive_all.append(naive); strat_all.append(strat); excl_all.append(excl)
        pcopy_all.append(p_copy)

    print(f"\n{'item':5s} {'p_copy':>7s} {'mon_naive':>10s} {'mon_strat':>10s} "
          f"{'mon_excl1':>10s} {'gap_naive':>10s} {'gap_strat':>10s} {'gap_excl':>9s}")
    for iid, pc, na, st, ex, q1 in rows:
        print(f"{iid:5s} {pc:7.3f} {na:10.3f} {st:10.3f} {ex:10.3f} "
              f"{pc-na:10.3f} {pc-st:10.3f} {pc-ex:9.3f}")

    n = len(rows)
    mp = sum(pcopy_all) / n
    mn_, ms_, me_ = (sum(v) / n for v in (naive_all, strat_all, excl_all))
    print("\n" + "-" * 78)
    print(f"  mean p_copy                    {mp:.4f}")
    print(f"  mean monitor accuracy  naive   {mn_:.4f}   gap {mp-mn_:+.4f}")
    print(f"                         strat   {ms_:.4f}   gap {mp-ms_:+.4f}")
    print(f"                         excl-1  {me_:.4f}   gap {mp-me_:+.4f}")
    print(f"\n  gap shift from position control: strat {(mp-ms_)-(mp-mn_):+.4f}   "
          f"excl-1 {(mp-me_)-(mp-mn_):+.4f}")
    print("  (negative shift = naive gap was INFLATED by monitor position bias)")
    print("-" * 78)

    # per-item robustness under each accuracy definition, frozen thresholds
    for lab, acc in (("naive", naive_all), ("strat", strat_all), ("excl-1", excl_all)):
        k = sum(1 for i in range(n) if pcopy_all[i] >= 0.15 and pcopy_all[i] - acc[i] > 0)
        print(f"  items with p_copy>=.15 and positive gap, {lab:6s}: {k}/{n}")
    print("\n  NOTE: null-model p-values are NOT recomputed here. This script only")
    print("  asks whether the position bias moves the gap; the frozen ms_analyze.py")
    print("  remains the confirmatory test.")


if __name__ == "__main__":
    main()
