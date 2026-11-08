"""Calibrate the synthetic battery so a 15-stimulus / full-depth run reproduces
Study 1's OBSERVED funnel: 105 candidate pairs per model -> ~3 eligible -> 2 independent."""
import sys, numpy as np
sys.path.insert(0,"design")
import adaptive_simulation as A

TARGET_ELIG, TARGET_IND = 3.0, 2.0     # per model, Study 1 observed

def funnel(res_frac, sal_load, n_rep=400, n_stim=15, seed=1):
    rng = np.random.default_rng(seed)
    E=[]; I=[]
    for _ in range(n_rep):
        A_res, A_load = A.SD_AUD*res_frac, sal_load
        # rebuild battery with the trial parameters
        sal = np.clip(rng.normal(0.404, A.SD_SAL, n_stim), .02, .98)
        u = rng.random(n_stim)
        p = np.where(u<0.50, rng.beta(30,1.2,n_stim),
            np.where(u<0.60, rng.beta(6,2.5,n_stim), np.clip(rng.normal(.5,.08,n_stim),.05,.95)))
        p = np.where(rng.random(n_stim)<0.5, p, 1-p)
        true = p**2+(1-p)**2
        aud = np.clip(0.718 + 0.39*(true-0.777)/A.SD_TRUE*A.SD_AUD
                      + A_load*(sal-0.404)/A.SD_SAL*A.SD_AUD
                      + rng.normal(0, A_res, n_stim), .3, .95)
        elig=[]
        for i in range(n_stim):
            for j in range(i+1,n_stim):
                a,b = (i,j) if true[i]>=true[j] else (j,i)
                if true[a]-true[b] < A.THR_TRUE: continue
                if abs(aud[a]-aud[b]) > A.THR_AUD: continue
                if abs(sal[a]-sal[b]) > A.THR_SAL: continue
                elig.append((true[a]-true[b], a, b))
        elig.sort(key=lambda x:-x[0]); used=set(); ind=0
        for d,h,l in elig:
            if h in used or l in used: continue
            used|={h,l}; ind+=1
        E.append(len(elig)); I.append(ind)
    return np.mean(E), np.mean(I)

print(f"{'res_frac':>9}{'sal_load':>10}{'eligible':>10}{'independent':>13}   target 3.0 / 2.0")
best=None
for rf in (0.45, 0.7, 1.0, 1.3, 1.6, 2.0):
    for sl in (0.75, 0.5, 0.3):
        e,i = funnel(rf, sl)
        err = abs(e-TARGET_ELIG)/TARGET_ELIG + abs(i-TARGET_IND)/TARGET_IND
        flag = ""
        if best is None or err < best[0]: best=(err, rf, sl, e, i); flag=" <-"
        print(f"{rf:>9.2f}{sl:>10.2f}{e:>10.2f}{i:>13.2f}{flag}")
print(f"\nBEST: residual_frac={best[1]}, salience_loading={best[2]}  -> eligible {best[3]:.2f}, independent {best[4]:.2f}")
