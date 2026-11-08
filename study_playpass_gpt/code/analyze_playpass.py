#!/usr/bin/env python3
"""Behavioural analysis of the GPT PLAY/PASS arm.

Reads ONLY the decision columns. The `reasoning` / `raw` columns are not
touched: trace coding is a separate, later step by design.
"""
import csv, json, math, sys, collections
import numpy as np
from scipy import stats

HERE = "/Users/calypsocalcott/Desktop/Coordination/Self_Coordination/study_playpass_gpt"
CSV  = sys.argv[1] if len(sys.argv) > 1 else HERE + "/data/playpass_full_20260912_191607.csv"
ITEMS = json.load(open(HERE + "/data/frozen_items.json"))
RNG = np.random.default_rng(20260912)
import os
TAG = os.path.basename(CSV).replace("playpass_","").replace(".csv","")
OUT = HERE + "/results/" + TAG

# Qwen reference (run_study1_playpass.py arm)
QWEN = dict(dprime=0.492, auc=0.776, c=-0.442)

DROP = {"raw", "reasoning"}
rows = []
with open(CSV) as f:
    for r in csv.DictReader(f):
        rows.append({k: v for k, v in r.items() if k not in DROP})

# ---------- 1. integrity ----------
n_total = len(rows)
parse_ok = sum(int(r["parse_ok"]) for r in rows)
tx_ok    = sum(int(r["transport_ok"]) for r in rows)
cost     = sum(float(r["cost_usd"]) for r in rows)
models   = collections.Counter(r["model_returned"] for r in rows)
shas     = collections.Counter((r["prompt_sha8"], r["frozen_sha8"]) for r in rows)

use = [r for r in rows if int(r["parse_ok"]) and int(r["transport_ok"])]
for r in use:
    r["play"] = 1 if r["decision"].upper() == "PLAY" else 0
    r["agreement"] = float(r["agreement"])
    r["perm_id"] = int(r["perm_id"])

HI = [r for r in use if r["arm"] == "HIGH"]
LO = [r for r in use if r["arm"] == "LOW"]

def rate(rs): return sum(x["play"] for x in rs) / len(rs)

p_hi, p_lo = rate(HI), rate(LO)

def wilson(k, n, z=1.96):
    if n == 0: return (float("nan"),) * 2
    p = k / n; d = 1 + z*z/n
    ctr = (p + z*z/(2*n)) / d
    hw = z*math.sqrt(p*(1-p)/n + z*z/(4*n*n)) / d
    return (ctr - hw, ctr + hw)

# ---------- item-level aggregation ----------
def item_table(rs):
    d = collections.OrderedDict()
    for r in rs:
        d.setdefault(r["array"], []).append(r)
    out = []
    for arr, g in d.items():
        out.append(dict(array=arr, arm=g[0]["arm"], agreement=g[0]["agreement"],
                        n=len(g), k=sum(x["play"] for x in g),
                        p=sum(x["play"] for x in g)/len(g)))
    return out

items_hi, items_lo = item_table(HI), item_table(LO)
all_items = items_hi + items_lo

# ---------- 5. difference, item-clustered bootstrap ----------
def diff_stat(ih, il):
    return np.mean([i["p"] for i in ih]) - np.mean([i["p"] for i in il])

obs_diff = diff_stat(items_hi, items_lo)
B = 20000
boot = np.empty(B)
ah = np.array([i["p"] for i in items_hi]); al = np.array([i["p"] for i in items_lo])
for b in range(B):
    boot[b] = RNG.choice(ah, ah.size, replace=True).mean() - RNG.choice(al, al.size, replace=True).mean()
ci_lo, ci_hi = np.percentile(boot, [2.5, 97.5])

# item-level permutation test on the arm label
pool = np.concatenate([ah, al]); nperm = 20000
perm = np.empty(nperm)
for b in range(nperm):
    s = RNG.permutation(pool)
    perm[b] = s[:ah.size].mean() - s[ah.size:].mean()
p_perm = (np.sum(np.abs(perm) >= abs(obs_diff)) + 1) / (nperm + 1)

# ---------- 6/8. SDT ----------
def z(p, n):
    p = min(max(p, 0.5/n), 1 - 0.5/n)   # log-linear style clamp at 1/(2n)
    return stats.norm.ppf(p)
zH, zF = z(p_hi, len(HI)), z(p_lo, len(LO))
dprime = zH - zF
crit   = -0.5 * (zH + zF)
sens, spec = p_hi, 1 - p_lo

# ---------- 7. AUC ----------
u, p_mw = stats.mannwhitneyu(ah, al, alternative="two-sided")
auc_item = u / (ah.size * al.size)
yt = np.array([r["play"] for r in HI] + [r["play"] for r in LO])
xt = np.array([1]*len(HI) + [0]*len(LO))
# trial-level AUC of the binary decision as a classifier of arm
tp = np.sum((yt == 1) & (xt == 1)); fp = np.sum((yt == 1) & (xt == 0))
auc_trial = 0.5 * (p_hi + (1 - p_lo))   # = balanced accuracy for a binary rule

# ---------- 9. continuous agreement vs item P(PLAY) ----------
ag = np.array([i["agreement"] for i in all_items]); pp = np.array([i["p"] for i in all_items])
rho, p_rho = stats.spearmanr(ag, pp)
rpear, p_pear = stats.pearsonr(ag, pp)
# within-arm (removes the binary split)
rho_hi, p_rho_hi = stats.spearmanr([i["agreement"] for i in items_hi], ah)
rho_lo, p_rho_lo = stats.spearmanr([i["agreement"] for i in items_lo], al)

# ---------- 10. leave-one-item-out ----------
loo = []
for drop in all_items:
    ih = [i for i in items_hi if i is not drop]
    il = [i for i in items_lo if i is not drop]
    d = diff_stat(ih, il)
    a = stats.mannwhitneyu([i["p"] for i in ih], [i["p"] for i in il],
                           alternative="two-sided")[0] / (len(ih)*len(il))
    loo.append((drop["array"], d, a))

# ---------- 11. permutation / position effects ----------
perm_tab = collections.OrderedDict()
for r in use:
    perm_tab.setdefault(r["perm_id"], []).append(r)
perm_rows = [(k, len(v), rate(v)) for k, v in sorted(perm_tab.items())]
obs = np.array([[sum(1 for r in v if r["play"] == 1), sum(1 for r in v if r["play"] == 0)]
                for k, v in sorted(perm_tab.items())])
chi2, p_chi, dof, _ = stats.chi2_contingency(obs)
# within-arm
perm_by_arm = {}
for arm, rs in (("HIGH", HI), ("LOW", LO)):
    t = collections.OrderedDict()
    for r in rs: t.setdefault(r["perm_id"], []).append(r)
    o = np.array([[sum(1 for r in v if r["play"]), sum(1 for r in v if not r["play"])]
                  for k, v in sorted(t.items())])
    keep = o.sum(axis=1) > 0
    try: pa = stats.chi2_contingency(o[keep])[1]
    except ValueError: pa = float("nan")
    perm_by_arm[arm] = (sorted(t), [rate(v) for k, v in sorted(t.items())], pa)
# rep (order within run) effect
reps = collections.OrderedDict()
for r in use: reps.setdefault(int(r["rep"]), []).append(r)
rho_rep, p_rep = stats.spearmanr([k for k in sorted(reps)],
                                 [rate(reps[k]) for k in sorted(reps)])

# ---------- report ----------
L = []
A = L.append
A("="*72); A("GPT PLAY/PASS — Study 1 arm, behavioural analysis"); A("="*72)
A(f"file            {CSV.split('/')[-1]}")
A(f"model returned  {dict(models)}")
A(f"prompt/frozen   {[f'{a}/{b}: {n}' for (a,b),n in shas.items()]}")
A("")
A("[1] INTEGRITY")
A(f"  decisions attempted {n_total}   parsed {parse_ok}   parse failures {n_total-parse_ok}")
A(f"  transport ok {tx_ok}            transport failures {n_total-tx_ok}")
A(f"  usable rows {len(use)}  (HIGH {len(HI)}, LOW {len(LO)})")
A("[2] COST")
A(f"  total ${cost:.4f}   ${cost/n_total:.5f}/call")
A("")
A("[3-4] PLAY RATES")
lo_h, hi_h = wilson(sum(r['play'] for r in HI), len(HI))
lo_l, hi_l = wilson(sum(r['play'] for r in LO), len(LO))
A(f"  P(PLAY | HIGH) = {p_hi:.4f}  [{lo_h:.3f}, {hi_h:.3f}]  ({sum(r['play'] for r in HI)}/{len(HI)})")
A(f"  P(PLAY | LOW ) = {p_lo:.4f}  [{lo_l:.3f}, {hi_l:.3f}]  ({sum(r['play'] for r in LO)}/{len(LO)})")
A(f"  overall P(PLAY) = {rate(use):.4f}")
A("")
A("[5] HIGH - LOW DIFFERENCE (item-clustered)")
A(f"  difference {obs_diff:+.4f}   95% CI [{ci_lo:+.4f}, {ci_hi:+.4f}]  (item bootstrap, B={B})")
A(f"  item-level permutation test of arm label: p = {p_perm:.4f}")
A("")
A("[6] d'"); A(f"  d' = {dprime:.4f}   (zH {zH:+.4f}, zFA {zF:+.4f}; rates clamped at 1/2n)")
A("[7] AUC")
A(f"  item-level (15 vs 15, Mann-Whitney) AUC = {auc_item:.4f}, p = {p_mw:.4f}")
A(f"  trial-level balanced accuracy of the PLAY rule = {auc_trial:.4f}")
A("[8] CRITERION / OPERATING POINT")
A(f"  sensitivity (hit, PLAY|HIGH) = {sens:.4f}")
A(f"  specificity (PASS|LOW)       = {spec:.4f}")
A(f"  criterion c = {crit:+.4f}   (negative = bias toward PLAY)")
A("")
A("[9] CONTINUOUS AGREEMENT vs ITEM P(PLAY)   (n=30 items)")
A(f"  Spearman rho = {rho:+.4f}, p = {p_rho:.4f}")
A(f"  Pearson  r   = {rpear:+.4f}, p = {p_pear:.4f}")
A(f"  within HIGH: rho = {rho_hi:+.4f}, p = {p_rho_hi:.4f}")
A(f"  within LOW : rho = {rho_lo:+.4f}, p = {p_rho_lo:.4f}")
A("")
A("[10] ITEM-LEVEL DETAIL  (array, arm, agreement, PLAY/20)")
for i in sorted(all_items, key=lambda x: -x["agreement"]):
    A(f"  {i['array']:22s} {i['arm']:5s} agr {i['agreement']:.4f}  PLAY {i['k']:2d}/{i['n']:2d} = {i['p']:.3f}")
ds = [d for _, d, _ in loo]; asx = [a for _, _, a in loo]
A(f"  leave-one-item-out: difference range [{min(ds):+.4f}, {max(ds):+.4f}]"
  f"   AUC range [{min(asx):.4f}, {max(asx):.4f}]")
worst_d = min(loo, key=lambda t: t[1]); worst_a = min(loo, key=lambda t: t[2])
A(f"  most influential for difference: drop {worst_d[0]} -> {worst_d[1]:+.4f}")
A(f"  most influential for AUC:        drop {worst_a[0]} -> {worst_a[2]:.4f}")
A("")
A("[11] PERMUTATION / POSITION EFFECTS")
for k, n, p in perm_rows:
    A(f"  perm {k:2d}  n={n:3d}  P(PLAY)={p:.3f}")
A(f"  chi2 across permutations (pooled): chi2={chi2:.3f}, df={dof}, p={p_chi:.4f}")
for arm in ("HIGH", "LOW"):
    ids, rs, pa = perm_by_arm[arm]
    A(f"  within {arm}: P(PLAY) by perm {[round(x,3) for x in rs]}  chi2 p = {pa:.4f}")
A(f"  rep-order trend: Spearman rho = {rho_rep:+.4f}, p = {p_rep:.4f}")
A("")
A("[12] COMPARISON WITH QWEN")
A(f"  {'':10s} {'GPT-5.5':>10s} {'Qwen':>10s}")
A(f"  {'d-prime':10s} {dprime:10.3f} {QWEN['dprime']:10.3f}")
A(f"  {'AUC':10s} {auc_item:10.3f} {QWEN['auc']:10.3f}")
A(f"  {'c':10s} {crit:10.3f} {QWEN['c']:10.3f}")
A("="*72)

txt = "\n".join(L)
print(txt)
open(OUT + "_REPORT.txt", "w").write(txt + "\n")
json.dump(dict(n=n_total, parse_fail=n_total-parse_ok, tx_fail=n_total-tx_ok, cost=cost,
               p_high=p_hi, p_low=p_lo, diff=obs_diff, diff_ci=[ci_lo, ci_hi], p_perm=p_perm,
               dprime=dprime, auc_item=auc_item, auc_p=p_mw, c=crit, sens=sens, spec=spec,
               spearman=rho, spearman_p=p_rho, pearson=rpear,
               rho_high=rho_hi, rho_low=rho_lo,
               loo_diff=[min(ds), max(ds)], loo_auc=[min(asx), max(asx)],
               perm_chi2_p=p_chi, rep_rho=rho_rep,
               items=all_items),
          open(OUT + "_summary.json", "w"), indent=1)
