"""Pair yield for a SINGLE focal model (GPT-5.5 parameters)."""
import sys, numpy as np
sys.path.insert(0,"design")
import adaptive_simulation as A

SD_TRUE_G, SD_AUD_G = 0.2298, 0.0724          # GPT-5.5 measured battery SDs
THR_T, THR_A, THR_S = 0.75*SD_TRUE_G, 0.35*SD_AUD_G, 0.35*A.SD_SAL

def battery(n, rng, fam=3, fs_sal=0.18, fs_aud=0.02):
    nf=int(np.ceil(n/fam)); f=np.repeat(np.arange(nf),fam)[:n]
    sal=np.clip(0.404+rng.normal(0,fs_sal,nf)[f]+rng.normal(0,A.SD_SAL*0.5,n),.02,.98)
    u=rng.random(n)
    p=np.where(u<.50, rng.beta(30,1.2,n), np.where(u<.60, rng.beta(6,2.5,n),
        np.clip(rng.normal(.5,.08,n),.05,.95)))
    p=np.where(rng.random(n)<.5,p,1-p)
    true=p**2+(1-p)**2
    aud=np.clip(0.713+0.41*(true-0.773)/SD_TRUE_G*SD_AUD_G+rng.normal(0,fs_aud,nf)[f]
                +0.5*(sal-.404)/A.SD_SAL*SD_AUD_G+rng.normal(0,SD_AUD_G*.45,n),.3,.95)
    return true, aud, sal, p

def yield_pairs(n_stim, nA2, nB2, rng, n_rep=200):
    ind=[]; elig=[]
    for _ in range(n_rep):
        true,aud,sal,p = battery(n_stim,rng)
        ph = rng.binomial(nA2,p)/nA2; est_t = ph**2+(1-ph)**2
        est_a = aud + rng.normal(0,A.W_AUD/np.sqrt(nB2),n_stim)
        est_s = sal + rng.normal(0,A.W_SAL/np.sqrt(nB2),n_stim)
        c=[]
        for i in range(n_stim):
            for j in range(i+1,n_stim):
                a,b=(i,j) if est_t[i]>=est_t[j] else (j,i)
                if est_t[a]-est_t[b] < THR_T: continue
                if abs(est_a[a]-est_a[b]) > THR_A: continue
                if abs(est_s[a]-est_s[b]) > THR_S: continue
                c.append((est_t[a]-est_t[b],a,b))
        c.sort(key=lambda x:-x[0]); used=set(); k=0
        for d,h,l in c:
            if h in used or l in used: continue
            used|={h,l}; k+=1
        ind.append(k); elig.append(len(c))
    return np.array(ind), np.array(elig)

rng=np.random.default_rng(2026)
print("SINGLE FOCAL MODEL (GPT-5.5), A2 depth 30 / Stage B depth 20\n")
print(f"{'stimuli':>8}{'eligible':>10}{'independent pairs':>20}{'P(>=20)':>9}{'P(>=24)':>9}{'sim/stim':>10}")
res={}
for n in (72, 90, 110, 130, 150):
    ind,el = yield_pairs(n,30,20,rng)
    res[n]=ind
    print(f"{n:>8}{el.mean():>10.0f}{f'{ind.mean():.0f} ({np.percentile(ind,10):.0f}-{np.percentile(ind,90):.0f})':>20}"
          f"{np.mean(ind>=20):>9.2f}{np.mean(ind>=24):>9.2f}{ind.mean()/n:>10.3f}")
print("\nCONSERVATIVE EMPIRICAL ANCHOR")
print("  Opus 4.6, 45 stimuli, 1 focal model, observed: 8 independent pairs = 0.178 per stimulus.")
print("  GPT's auditor window is 47% wider than Claude-family, so this UNDERSTATES GPT yield.")
for n in (90,110,130,150):
    print(f"    n={n:>4}: conservative {n*0.178:>5.1f} pairs   simulated {res[n].mean():>5.1f}")
print("\n  Battery needed for >=20 pairs on the conservative anchor: %d stimuli" % int(np.ceil(20/0.178)))
print("  Battery needed for >=24 pairs on the conservative anchor: %d stimuli" % int(np.ceil(24/0.178)))
