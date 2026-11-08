"""Elicitation arm vs frozen unprompted arm. Read-only."""
import sys, os, csv, math, random, statistics, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import s1_common as S
PAY = ["3", "5", "7", "9"]


def ols(x, y):
    mx, my = statistics.mean(x), statistics.mean(y); d = sum((a-mx)**2 for a in x)
    return sum((a-mx)*(b-my) for a, b in zip(x, y))/d if d else float("nan")


def pear(x, y):
    mx, my = statistics.mean(x), statistics.mean(y)
    d = math.sqrt(sum((a-mx)**2 for a in x)*sum((b-my)**2 for b in y))
    return sum((a-mx)*(b-my) for a, b in zip(x, y))/d if d else float("nan")


def boot_ci(pairs, xs, ys, cl, stat=ols, B=4000, seed=9):
    rng = random.Random(seed)
    idx = {i: [k for k, c in enumerate(cl) if c == i] for i in range(pairs)}
    out = []
    for _ in range(B):
        pick = [rng.randrange(pairs) for _ in range(pairs)]
        sel = [k for i in pick for k in idx[i]]
        v = stat([xs[k] for k in sel], [ys[k] for k in sel])
        if v == v: out.append(v)
    out.sort()
    return out[int(.025*len(out))], out[int(.975*len(out))]


def load_arm(path, need_prob):
    rows = [r for r in csv.DictReader(open(path)) if r["included_in_analysis"] == "True"]
    if need_prob:
        rows = [r for r in rows if r["predicted_match_probability"] not in ("", "None")]
    return rows
