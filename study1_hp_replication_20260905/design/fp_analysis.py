import sys, numpy as np
sys.path.insert(0,"design")
from adaptive_simulation import *

def decompose(n_stim, nA2, nB2, n_rep, rng):
    tot=fail_true=fail_aud=fail_sal=0; gaps=[]; augaps=[]
    for _ in range(n_rep):
        B = make_battery(n_stim, rng)
        for m in MODELS:
            idx=np.arange(n_stim)
            s2,_ = measure(B,m,idx,nA2,nB2,rng)
            for h,l in pair_up(s2, idx):
                tot+=1
                dt=B[m]["true"][h]-B[m]["true"][l]
                da=abs(B[m]["aud"][h]-B[m]["aud"][l]); ds=abs(B[m]["sal"][h]-B[m]["sal"][l])
                gaps.append(dt); augaps.append(da)
                if dt < THR_TRUE: fail_true+=1
                if da > THR_AUD:  fail_aud+=1
                if ds > THR_SAL:  fail_sal+=1
    return dict(n=tot, true=fail_true/tot, aud=fail_aud/tot, sal=fail_sal/tot,
                mean_gap=float(np.mean(gaps)), q10_gap=float(np.percentile(gaps,10)),
                mean_augap=float(np.mean(augaps)))

rng=np.random.default_rng(99)
print("Decomposition of 'false positive' confirmed pairs, by WHICH criterion the")
print("pair actually violates on its true values (Stage A depth 30):\n")
print(f"{'nB2':>5}{'pairs':>8}{'fails |d_true|':>16}{'fails |d_aud|':>15}{'fails |d_sal|':>15}{'mean true gap':>15}{'p10 gap':>9}")
for nB2 in (10, 15, 20, 30, 45, 60):
    d = decompose(72, 30, nB2, 25, rng)
    print(f"{nB2:>5}{d['n']:>8}{d['true']:>16.3f}{d['aud']:>15.3f}{d['sal']:>15.3f}{d['mean_gap']:>15.3f}{d['q10_gap']:>9.3f}")
print(f"\nThreshold reference: |d_true| >= {THR_TRUE:.4f}, |d_aud| <= {THR_AUD:.4f}, |d_sal| <= {THR_SAL:.4f}")
print("\nStage A depth sensitivity (nB2 = 20 fixed):")
print(f"{'nA2':>5}{'pairs':>8}{'fails |d_true|':>16}{'mean true gap':>15}")
for nA2 in (15, 20, 30, 45, 60):
    d = decompose(72, nA2, 20, 25, rng)
    print(f"{nA2:>5}{d['n']:>8}{d['true']:>16.3f}{d['mean_gap']:>15.3f}")
