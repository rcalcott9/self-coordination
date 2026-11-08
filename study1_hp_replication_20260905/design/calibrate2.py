"""Calibrate against BOTH observed funnels:
   15 stimuli, 2 models -> ~3 eligible, ~2 independent per model  (Study 1)
   45 stimuli, 1 model  -> 52 eligible, 8 independent             (Opus 4.6 ladder)
Real batteries are built in CUE FAMILIES; members share structure, so eligible
pairs cluster and non-reuse bites hard. Family random effects reproduce that."""
import sys, numpy as np
sys.path.insert(0,"design")
import adaptive_simulation as A

def battery(n_stim, fam_size, fam_sd_sal, fam_sd_aud, rng):
    nf = int(np.ceil(n_stim/fam_size))
    fam = np.repeat(np.arange(nf), fam_size)[:n_stim]
    f_sal = rng.normal(0, fam_sd_sal, nf)[fam]
    f_aud = rng.normal(0, fam_sd_aud, nf)[fam]
    sal = np.clip(0.404 + f_sal + rng.normal(0, A.SD_SAL*0.5, n_stim), .02, .98)
    u = rng.random(n_stim)
    p = np.where(u<0.50, rng.beta(30,1.2,n_stim),
        np.where(u<0.60, rng.beta(6,2.5,n_stim), np.clip(rng.normal(.5,.08,n_stim),.05,.95)))
    p = np.where(rng.random(n_stim)<0.5, p, 1-p)
    true = p**2+(1-p)**2
    aud = np.clip(0.718 + 0.39*(true-0.777)/A.SD_TRUE*A.SD_AUD + f_aud
                  + 0.5*(sal-0.404)/A.SD_SAL*A.SD_AUD
                  + rng.normal(0, A.SD_AUD*0.45, n_stim), .3, .95)
    return true, aud, sal

def funnel(n_stim, fam_size, fs_sal, fs_aud, n_rep, seed):
    rng = np.random.default_rng(seed); E=[]; I=[]
    for _ in range(n_rep):
        true, aud, sal = battery(n_stim, fam_size, fs_sal, fs_aud, rng)
        elig=[]
        for i in range(n_stim):
            for j in range(i+1,n_stim):
                a,b=(i,j) if true[i]>=true[j] else (j,i)
                if true[a]-true[b] < A.THR_TRUE: continue
                if abs(aud[a]-aud[b]) > A.THR_AUD: continue
                if abs(sal[a]-sal[b]) > A.THR_SAL: continue
                elig.append((true[a]-true[b],a,b))
        elig.sort(key=lambda x:-x[0]); used=set(); ind=0
        for d,h,l in elig:
            if h in used or l in used: continue
            used|={h,l}; ind+=1
        E.append(len(elig)); I.append(ind)
    return np.mean(E), np.mean(I)

print(f"{'fam_sd_sal':>11}{'fam_sd_aud':>11} | {'n=15: elig':>11}{'ind':>6} | {'n=45: elig':>11}{'ind':>6}")
print(f"{'target':>11}{'':>11} | {3.0:>11.1f}{2.0:>6.1f} | {52.0:>11.1f}{8.0:>6.1f}")
best=None
for fs_sal in (0.10, 0.14, 0.18):
    for fs_aud in (0.020, 0.035, 0.050):
        e15,i15 = funnel(15,3,fs_sal,fs_aud,300,11)
        e45,i45 = funnel(45,3,fs_sal,fs_aud,150,12)
        err = abs(e15-3)/3 + abs(i15-2)/2 + abs(e45-52)/52 + abs(i45-8)/8
        flag=""
        if best is None or err<best[0]: best=(err,fs_sal,fs_aud,e15,i15,e45,i45); flag=" <-"
        print(f"{fs_sal:>11.3f}{fs_aud:>11.3f} | {e15:>11.2f}{i15:>6.2f} | {e45:>11.2f}{i45:>6.2f}{flag}")
print(f"\nBEST fam_sd_sal={best[1]}, fam_sd_aud={best[2]}")
print(f"  n=15 -> {best[3]:.2f} eligible / {best[4]:.2f} independent   (target 3 / 2)")
print(f"  n=45 -> {best[5]:.2f} eligible / {best[6]:.2f} independent   (target 52 / 8)")
for n in (60,72,90,110):
    e,i = funnel(n,3,best[1],best[2],120,13)
    print(f"  PROJECTION n={n:>3} -> {e:>6.1f} eligible / {i:>5.1f} independent per model  => {2*i:.0f} pairs across 2 models")
