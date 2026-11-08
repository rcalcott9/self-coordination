"""Final power for Study 1b (Brier). Per-array pooled self-minus-cross contrast
c_j = delta + beta*(d_j - mean d) + u_j + e_rep + e_fresh.
tau (between-array SD of true contrast): .085 from the 2026-09-12 relational pilot (11 arrays, pooled SD .090
incl. noise; unmatched wording, Opus adaptive -> treated as an upper bound) and .05 (optimistic).
Rep noise: Brier SD per response .105 (pilot) -> pooled contrast var = .105^2/r.
Fresh-draw noise for n=48 target draws: var ~ .0017 (pooled), from 4*Var(dq.1[choice])/n with |dq| ~ .2.
Tests: primary sign-flip (2-sided, 2000 flips); moderation = OLS slope permutation (2000)."""
import numpy as np, json
rng = np.random.default_rng(1)
def tvd_sample(comp):
    # divergence by stratum from inventory-like ranges (selection draws)
    lo_hi = {"S1": (.6, .95), "S2G": (.35, .7), "S2O": (.35, .7), "S3": (0, .2)}
    return np.concatenate([rng.uniform(*lo_hi[s], n) for s, n in comp.items()])
def sim(comp, delta, beta, tau, r, nsim=1000, B=1000):
    N = sum(comp.values()); hp = hm = 0
    for _ in range(nsim):
        d = tvd_sample(comp)
        c = delta + beta*(d-d.mean()) + rng.normal(0, tau, N) + rng.normal(0, .105/np.sqrt(r), N) + rng.normal(0, np.sqrt(.0017), N)
        flips = rng.choice([-1, 1], (B, N))
        p = (np.sum(np.abs((flips*c).mean(1)) >= abs(c.mean()))+1)/(B+1); hp += p < .05
        sl = np.polyfit(d, c, 1)[0]
        perm = np.array([np.polyfit(rng.permutation(d), c, 1)[0] for _ in range(300)])
        hm += (np.sum(np.abs(perm) >= abs(sl))+1)/301 < .05
    return hp/nsim, hm/nsim
out = []
for comp_name, comp in (("expected N=28 (S1 5/S2G 5/S2O 8/S3 10)", {"S1":5,"S2G":5,"S2O":8,"S3":10}),
                        ("pessimistic N=22 (3/3/6/10)", {"S1":3,"S2G":3,"S2O":6,"S3":10})):
    for tau in (.085, .05):
        for r in (8,):
            for delta, beta in ((0,0),(.03,0),(.05,0),(.08,0),(.05,.10),(.05,.20)):
                pp, pm = sim(comp, delta, beta, tau, r, nsim=600)
                out.append(dict(design=comp_name, tau=tau, reps=r, delta=delta, beta=beta, power_pooled=pp, power_moderation=pm))
                print(out[-1], flush=True)
for r in (4, 12):
    pp, pm = sim({"S1":5,"S2G":5,"S2O":8,"S3":10}, .05, 0, .085, r, nsim=600)
    out.append(dict(design="expected N=28", tau=.085, reps=r, delta=.05, beta=0, power_pooled=pp, power_moderation=pm)); print(out[-1])
json.dump(out, open("power_final.json","w"), indent=1)
