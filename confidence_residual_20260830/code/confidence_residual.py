"""
Does own-copy reliability predict betting ABOVE AND BEYOND stated confidence?

DATA PROVENANCE (important - this is NOT Study 1).
Study 1 (policy_specific_..._20260812_1401) has NO self-directed confidence: its
Stage B "auditor" arm is CROSS-model by construction (stage_b_perception.py:41,
actor = P.OTHER[focal]). The only explicit self-stated coordination probability in
the project is arm 2 of the 2026-08-01 confidence_calibration experiment, which is
self-contained: arms 1 (choice -> true self-match), 2 (stated P), and 3 (safe-payoff
sweep -> betting) all run on the SAME models and SAME 6 stimuli.

Models here are gpt-5.4 / claude-opus-4-8, NOT Study 1's GPT-5.5 / Opus 5.

ESTIMATORS
  true self-match : unbiased dyadic sum_k n_k(n_k-1)/[N(N-1)]  (harness/match.py)
  stated P        : mean of arm-2 stated_p, rescaled to [0,1]
  betting         : arm-3 attempt rate, pooled and per safe payoff

No API calls. Deterministic seed for the bootstrap/permutation.
"""
import csv, os, collections, math
import numpy as np

SEED = 20260830
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
SRC = os.path.join(ROOT, "experiments", "2026-08-01_confidence_calibration",
                   "data", "confidence_calib_20260801_160108.csv")
OUT = os.path.join(HERE, "..", "data")


def unbiased_match(counts):
    n = sum(counts.values())
    if n < 2:
        return float("nan")
    return sum(v * (v - 1) for v in counts.values()) / (n * (n - 1))


rows = list(csv.DictReader(open(SRC)))
parse_fail = collections.Counter()

# ---------------------------------------------------------------- arm 1 ------
a1 = collections.defaultdict(collections.Counter)
for r in rows:
    if r["arm"] != "1":
        continue
    s = r["chosen_shape"].strip()
    if not s:
        parse_fail[("arm1", r["model"], r["pair"])] += 1
        continue
    a1[(r["model"], r["pair"])][s] += 1

# ---------------------------------------------------------------- arm 2 ------
a2 = collections.defaultdict(list)
for r in rows:
    if r["arm"] != "2":
        continue
    v = r["stated_p"].strip()
    try:
        p = float(v)
    except ValueError:
        parse_fail[("arm2", r["model"], r["pair"])] += 1
        continue
    a2[(r["model"], r["pair"])].append(p / 100.0 if p > 1.0 else p)

# ---------------------------------------------------------------- arm 3 ------
a3 = collections.defaultdict(list)          # pooled over safe
a3s = collections.defaultdict(list)         # per safe payoff
for r in rows:
    if r["arm"] != "3":
        continue
    d = r["decision"].strip()
    if d not in ("attempt", "opt_out"):
        parse_fail[("arm3", r["model"], r["pair"])] += 1
        continue
    y = 1 if d == "attempt" else 0
    a3[(r["model"], r["pair"])].append(y)
    a3s[(r["model"], r["pair"], int(r["safe"]))].append(y)

cells = sorted(set(a1) & set(a2) & set(a3))

recs = []
for m, p in cells:
    c = a1[(m, p)]
    recs.append(dict(
        model=m, stimulus=p,
        n_a1=sum(c.values()), true_match=unbiased_match(c),
        modal=max(c, key=c.get), modal_share=max(c.values()) / sum(c.values()),
        n_a2=len(a2[(m, p)]), stated_p=float(np.mean(a2[(m, p)])),
        stated_sd=float(np.std(a2[(m, p)], ddof=1)),
        n_a3=len(a3[(m, p)]), attempt=float(np.mean(a3[(m, p)])),
    ))
    for s in (3, 5, 7, 9):
        v = a3s.get((m, p, s), [])
        recs[-1][f"attempt_safe{s}"] = float(np.mean(v)) if v else float("nan")

recs.sort(key=lambda r: (r["model"], r["stimulus"]))

# ------------------------------------------------------------- reporting -----
print("=" * 96)
print("PER-CELL TABLE  (arm1 true self-match / arm2 stated P / arm3 attempt rate)")
print("=" * 96)
print(f"{'model':18}{'stimulus':10}{'trueP':>8}{'statedP':>9}{'gap':>8}"
      f"{'attempt':>9}{'a@3':>7}{'a@5':>7}{'a@7':>7}{'a@9':>7}{'n1':>5}{'n2':>5}{'n3':>5}")
print("-" * 96)
for r in recs:
    gap = r["stated_p"] - r["true_match"]
    print(f"{r['model']:18}{r['stimulus']:10}{r['true_match']:8.3f}{r['stated_p']:9.3f}"
          f"{gap:+8.3f}{r['attempt']:9.3f}"
          f"{r['attempt_safe3']:7.2f}{r['attempt_safe5']:7.2f}"
          f"{r['attempt_safe7']:7.2f}{r['attempt_safe9']:7.2f}"
          f"{r['n_a1']:5d}{r['n_a2']:5d}{r['n_a3']:5d}")

print()
print("MISCALIBRATION EXTREMES (stated - true), sorted")
print("-" * 60)
for r in sorted(recs, key=lambda r: r["stated_p"] - r["true_match"]):
    gap = r["stated_p"] - r["true_match"]
    tag = ("UNDERconfident: reliable but doubted" if gap < -0.15 else
           "OVERconfident: unreliable but trusted" if gap > 0.15 else "")
    print(f"  {r['model']:18}{r['stimulus']:10} true {r['true_match']:.3f}"
          f"  stated {r['stated_p']:.3f}  gap {gap:+.3f}  {tag}")

# ------------------------------------------------- correlations + residual ---
tm = np.array([r["true_match"] for r in recs])
sp = np.array([r["stated_p"] for r in recs])
at = np.array([r["attempt"] for r in recs])
mo = np.array([r["model"] for r in recs])


def corr(a, b):
    return float(np.corrcoef(a, b)[0, 1])


print()
print("=" * 96)
print("CELL-LEVEL CORRELATIONS  (n = %d cells)" % len(recs))
print("=" * 96)
print(f"  corr(stated P, true match)   = {corr(sp, tm):+.3f}   <- is confidence calibrated?")
print(f"  corr(attempt,  true match)   = {corr(at, tm):+.3f}   <- does betting track reality?")
print(f"  corr(attempt,  stated P)     = {corr(at, sp):+.3f}   <- does betting track the story?")


def partial(x, y, z):
    """corr(x, y | z) via residuals of OLS on [1, z]."""
    Z = np.c_[np.ones_like(z), z]
    rx = x - Z @ np.linalg.lstsq(Z, x, rcond=None)[0]
    ry = y - Z @ np.linalg.lstsq(Z, y, rcond=None)[0]
    return corr(rx, ry)


print()
print("PARTIAL CORRELATIONS  (the question asked)")
print("-" * 96)
pa_t = partial(at, tm, sp)
pa_s = partial(at, sp, tm)
print(f"  corr(attempt, true match | stated P) = {pa_t:+.3f}"
      "   <- reliability's value ABOVE stated confidence")
print(f"  corr(attempt, stated P | true match) = {pa_s:+.3f}"
      "   <- confidence's value ABOVE reliability")

# permutation test on the partial correlations, cells shuffled within model
rng = np.random.default_rng(SEED)
B = 20000


def perm_p(stat, target, other):
    obs = partial(at, target, other)
    null = np.empty(B)
    idx = np.arange(len(recs))
    for b in range(B):
        pi = idx.copy()
        for m in np.unique(mo):
            sel = np.where(mo == m)[0]
            pi[sel] = rng.permutation(sel)
        null[b] = partial(at, target[pi], other[pi])
    return obs, float(np.mean(np.abs(null) >= abs(obs)))


o1, p1 = perm_p(None, tm, sp)
o2, p2 = perm_p(None, sp, tm)
print(f"    permutation p (within-model shuffle, B={B}):  true|stated {p1:.4f}"
      f"   stated|true {p2:.4f}")

# ---------------------------------------------- trial-level logistic model ---
print()
print("=" * 96)
print("TRIAL-LEVEL LOGISTIC:  attempt ~ true_match + stated_p + safe_payoff + model")
print("=" * 96)
lut = {(r["model"], r["stimulus"]): r for r in recs}
X, y = [], []
for r in rows:
    if r["arm"] != "3":
        continue
    d = r["decision"].strip()
    if d not in ("attempt", "opt_out"):
        continue
    k = (r["model"], r["pair"])
    if k not in lut:
        continue
    c = lut[k]
    X.append([1.0, c["true_match"], c["stated_p"], float(r["safe"]),
              1.0 if r["model"] == "gpt-5.4" else 0.0])
    y.append(1.0 if d == "attempt" else 0.0)
X, y = np.array(X), np.array(y)


def irls(X, y, ridge=1e-6, iters=100):
    b = np.zeros(X.shape[1])
    for _ in range(iters):
        eta = np.clip(X @ b, -30, 30)
        mu = 1 / (1 + np.exp(-eta))
        W = np.clip(mu * (1 - mu), 1e-9, None)
        H = X.T @ (X * W[:, None]) + ridge * np.eye(X.shape[1])
        g = X.T @ (y - mu) - ridge * b
        step = np.linalg.solve(H, g)
        b += step
        if np.max(np.abs(step)) < 1e-10:
            break
    eta = np.clip(X @ b, -30, 30)
    mu = 1 / (1 + np.exp(-eta))
    W = np.clip(mu * (1 - mu), 1e-9, None)
    cov = np.linalg.inv(X.T @ (X * W[:, None]) + ridge * np.eye(X.shape[1]))
    return b, np.sqrt(np.diag(cov))


names = ["intercept", "true_match", "stated_p", "safe_payoff", "is_gpt"]
b, se = irls(X, y)
print(f"  n trials = {len(y)}, attempt rate = {y.mean():.3f}")
print(f"  {'term':14}{'beta':>10}{'naive SE':>10}{'z':>8}")
for nm, bb, ss in zip(names, b, se):
    print(f"  {nm:14}{bb:+10.3f}{ss:10.3f}{bb/ss:8.2f}")

# cluster-robust by (model, stimulus) -- 12 clusters, so read as indicative
clusters = [(r["model"], r["pair"]) for r in rows
            if r["arm"] == "3" and r["decision"].strip() in ("attempt", "opt_out")
            and (r["model"], r["pair"]) in lut]
uc = sorted(set(clusters))
ca = np.array([uc.index(c) for c in clusters])
eta = np.clip(X @ b, -30, 30)
mu = 1 / (1 + np.exp(-eta))
W = np.clip(mu * (1 - mu), 1e-9, None)
bread = np.linalg.inv(X.T @ (X * W[:, None]) + 1e-6 * np.eye(X.shape[1]))
meat = np.zeros((X.shape[1], X.shape[1]))
for j in range(len(uc)):
    s = ca == j
    u = (X[s] * (y[s] - mu[s])[:, None]).sum(0)
    meat += np.outer(u, u)
crse = np.sqrt(np.diag(bread @ meat @ bread))
print()
print(f"  cluster-robust by (model x stimulus), {len(uc)} clusters:")
print(f"  {'term':14}{'beta':>10}{'clust SE':>10}{'z':>8}")
for nm, bb, ss in zip(names, b, crse):
    print(f"  {nm:14}{bb:+10.3f}{ss:10.3f}{bb/ss:8.2f}")

# ------------------------------------------------------------------ save -----
os.makedirs(OUT, exist_ok=True)
fp = os.path.join(OUT, "cell_table.csv")
with open(fp, "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(recs[0].keys()))
    w.writeheader()
    w.writerows(recs)
print()
print("wrote", fp)
if parse_fail:
    print("PARSE FAILURES (not silently dropped):")
    for k, v in parse_fail.items():
        print("   ", k, v)
else:
    print("parse failures: none")
