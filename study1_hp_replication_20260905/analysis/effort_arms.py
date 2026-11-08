"""Three Opus 5 configuration arms on the frozen 3/5/7/9 grid. Read-only."""
import sys, os, csv, statistics, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import s1_common as S, elicit_analysis as EA
ARMS = [("thinking OFF", "data/stageC_20260910_204219.csv"),
        ("low effort", "data/stageC_20260910_162358.csv"),
        ("high effort", "data/stageC_20260910_183445.csv")]
_, pairs = S.load("Claude Opus 5"); ho = S.holdout_map(pairs); st = sorted(ho)

def load(f):
    r = [x for x in csv.DictReader(open(os.path.join(S.EXP, f))) if x["included_in_analysis"] == "True"]
    d = collections.defaultdict(list)
    for x in r: d[(x["stimulus"], x["safe_payoff"])].append(x["participation_decision"] == "ATTEMPT")
    return r, {k: statistics.mean(v) for k, v in d.items()}

R = {lab: load(f) for lab, f in ARMS}
r0 = R["thinking OFF"][0]
c = collections.Counter((x["stimulus"], x["safe_payoff"]) for x in r0)
v = collections.Counter((x["stimulus"], x["safe_payoff"], x["variant"]) for x in r0)
print("INTEGRITY thinking-off: rows %d/1728  stimuli %d  valid %s  depth %d-%d  AB/BA %d-%d" % (
    len(r0), len({x["stimulus"] for x in r0}), dict(collections.Counter(x["valid_response"] for x in r0)),
    min(c.values()), max(c.values()), min(v.values()), max(v.values())))
print("  thinking disabled on all rows:", all('"type": "disabled"' in x["api_settings"] for x in r0),
      "| reasoning empty on all rows:", all(not (x["visible_reasoning"] or "").strip() for x in r0))

print("\n(1) ATTEMPT RATE")
print("   %-6s" % "safe" + "".join("%15s" % l for l, _ in ARMS))
for p in S.PAY:
    print("   %-6s" % p + "".join("%15.3f" % statistics.mean(R[l][1][(s, p)] for s in st) for l, _ in ARMS))

print("\n(2) CONTINUOUS held-out match -> ATTEMPT slope [95% CI, pairs bootstrap]")
for p in S.PAY:
    cells = []
    for l, _ in ARMS:
        A = R[l][1]; xs, ys, cl = [], [], []
        for i, q in enumerate(pairs):
            for m in ("stimulus_high", "stimulus_low"):
                xs.append(ho[q[m]]); ys.append(A[(q[m], p)]); cl.append(i)
        if max(ys) - min(ys) < 1e-12: cells.append("  no variance       ")
        else:
            lo, up = EA.boot_ci(len(pairs), xs, ys, cl)
            cells.append("%+.3f [%+.2f,%+.2f]%s" % (EA.ols(xs, ys), lo, up, "*" if lo > 0 or up < 0 else " "))
    print("   safe %-3s " % p + "  ".join("%-24s" % c for c in cells))

print("\n(3) HIGH-vs-LOW POLICY CONTRAST [mean diff, perm p]")
for p in S.PAY:
    cells = []
    for l, _ in ARMS:
        A = R[l][1]; d = [A[(q["stimulus_high"], p)] - A[(q["stimulus_low"], p)] for q in pairs]
        pv = S.signflip_p(d, seed=int(p)) if any(abs(x) > 1e-12 for x in d) else 1.0
        cells.append("%+.3f p=%.3f" % (statistics.mean(d), pv))
    print("   safe %-3s " % p + "  ".join("%-18s" % c for c in cells))

print("\n(4) MATCH x PAYOFF INTERACTION (per-pair slope of the contrast over the grid)")
def slope(vv):
    xs = [3, 5, 7, 9]; mx = statistics.mean(xs); my = statistics.mean(vv)
    return sum((a - mx) * (b - my) for a, b in zip(xs, vv)) / sum((a - mx) ** 2 for a in xs)
for l, _ in ARMS:
    A = R[l][1]
    sl = [slope([A[(q["stimulus_high"], p)] - A[(q["stimulus_low"], p)] for p in S.PAY]) for q in pairs]
    m, se, lo, up = S.mean_ci(sl)
    print("   %-13s %+.5f [%+.5f, %+.5f]  p=%.4f  (%d/27 +)" % (l, m, lo, up, S.signflip_p(sl, seed=3),
          sum(1 for x in sl if x > 0)))
print("   GPT-5.5 ref   +0.04575 [+0.023, +0.068]  p=.00035")
