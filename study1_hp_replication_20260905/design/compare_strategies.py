import sys, json
import numpy as np
sys.path.insert(0, "design")
from adaptive_simulation import *

RATE_LO, RATE_HI = 75/4800, 110/4800
N_REP = 200

STRATS = [
 # name,                       n_stim, nA1, nB1, nA2, nB2, adaptive, conf_arm,     nC
 ("1 current fixed-depth",         72,  60,  30,   0,   0, False, "all_battery",   30),
 ("2 reduced fixed-depth",         72,  30,  20,   0,   0, False, "survivors",     24),
 ("3 two-stage adaptive",          72,  20,  12,  30,  20, True,  "final_pairs",   24),
 ("4 aggressive breadth-first",   110,  12,   8,  30,  20, True,  "final_pairs",   24),
]

rng = np.random.default_rng(20260905)
rows = []
for name, ns, a1, b1, a2, b2, ad, ca, nC in STRATS:
    reps = [run_strategy(name, ns, a1, b1, a2 or a1, b2 or b1, ad, rng, ca) for _ in range(N_REP)]
    npairs = np.array([r["n_pairs"] for r in reps])
    fp = np.array([r["false_pos"] for r in reps])
    gap = np.array([r["mean_true_gap"] for r in reps])
    surv = np.array([r["n_surv"] for r in reps])
    comp = {k: float(np.mean([r["calls"][k] for r in reps])) for k in reps[0]["calls"]}
    n_use = int(np.median(npairs))
    comp["stageC"] = min(n_use, 30) * 2 * 4 * nC
    tot = sum(comp.values())
    rows.append(dict(name=name, n_stim=ns, nC=nC, pairs_med=n_use,
                     pairs_lo=int(np.percentile(npairs,10)), pairs_hi=int(np.percentile(npairs,90)),
                     p_ge20=float(np.mean(npairs>=20)), fp_rate=float(np.mean(fp/np.maximum(npairs,1))),
                     mean_true_gap=float(np.mean(gap)), surv=float(np.mean(surv)),
                     calls=comp, total=tot, lo=tot*RATE_LO, hi=tot*RATE_HI))

hdr = "%-28s%5s%18s%9s%6s%7s%9s%14s" % ("strategy","stim","pairs (p10-p90)","P(>=20)","FP","gap","calls","$ all-in")
print(hdr)
for r in rows:
    pr = "%d (%d-%d)" % (r["pairs_med"], r["pairs_lo"], r["pairs_hi"])
    money = "$%,.0f-%,.0f".replace("%,","%,")  # placeholder
    money = "${:,.0f}-{:,.0f}".format(r["lo"], r["hi"])
    print("%-28s%5d%18s%9.2f%6.2f%7.3f%9s%14s" % (
        r["name"], r["n_stim"], pr, r["p_ge20"], r["fp_rate"], r["mean_true_gap"],
        format(r["total"], ",.0f"), money))

print(f"\n{'COST BY COMPONENT (calls)':<28}{'stageA':>9}{'auditor':>9}{'salience':>10}{'confid':>9}{'stageC':>9}")
for r in rows:
    c=r["calls"]
    print(f"{r['name']:<28}{c['stageA']:>9,.0f}{c['auditor']:>9,.0f}{c['salience']:>10,.0f}{c['confidence']:>9,.0f}{c['stageC']:>9,.0f}")

print(f"\n{'POWER at the realised pair count':<28}{'nC':>4}{'mu=.145':>9}{'mu=.10':>8}{'mu=.07':>8}")
prng = np.random.default_rng(7)
for r in rows:
    n = min(r["pairs_med"], 30)
    ps = [power_pairs(n, mu, 0.0903, r["nC"], prng, 300) for mu in (0.145, 0.10, 0.07)]
    r["power"] = dict(zip(("0.145","0.10","0.07"), ps))
    print(f"{r['name']:<28}{r['nC']:>4}{ps[0]:>9.3f}{ps[1]:>8.3f}{ps[2]:>8.3f}")

print(f"\n{'STAGE C DEPTH at 24 pairs':<28}{'20/cell':>9}{'24/cell':>9}{'30/cell':>9}")
for mu in (0.145, 0.10, 0.07):
    ps = [power_pairs(24, mu, 0.0903, nc, prng, 400) for nc in (20, 24, 30)]
    print(f"{f'  mu = {mu}':<28}{ps[0]:>9.3f}{ps[1]:>9.3f}{ps[2]:>9.3f}")

json.dump(rows, open("design/strategy_comparison.json","w"), indent=1, default=float)
print("\nwritten -> design/strategy_comparison.json")
