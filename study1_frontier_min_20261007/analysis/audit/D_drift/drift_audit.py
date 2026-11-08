import csv, glob, json, os
import numpy as np
ROOT=os.path.expanduser("~/Desktop/Coordination/Self_Coordination/study1_frontier_min_20261007")
OUT=os.path.join(ROOT,"analysis","audit","D_drift")
F=json.load(open(os.path.join(ROOT,"design","FROZEN.json"))); A=F["arrays"]; K=len(A)
MODEL={"gpt":"gpt-5.5-2026-04-23","claude":"claude-opus-5"}; AL=.5
fr={m:{a:np.zeros(4) for a in A} for m in MODEL}
for r in csv.DictReader(open(F["calibration_reuse"]["source"])):
    for m,mid in MODEL.items():
        if r["checkpoint_requested"]==mid and r["parse_ok"]=="1": fr[m][r["array_id"]][int(r["canonical_index"])]+=1
an={m:{a:[] for a in A} for m in MODEL}
for f in glob.glob(os.path.join(ROOT,"runs","anchor","*.csv")):
    for r in csv.DictReader(open(f)):
        if r["parse_ok"]=="1": an[r["answerer"]][r["array"]].append(int(r["canonical_choice"]))
rng=np.random.default_rng(7)
def wmm(c): c=np.asarray(c,float); n=c.sum(-1); return (c*(c-1)).sum(-1)/(n*(n-1))
res={}
def null_pp(C,lp,B):   # posterior-predictive null, vectorized: B x 41
    a=C+AL
    g=rng.gamma(np.broadcast_to(a,(B,)+a.shape)); P=g/g.sum(-1,keepdims=True)
    tot=np.zeros(B)
    for i in range(K):
        k=np.array([rng.multinomial(4,P[b,i]) for b in range(B)]); tot+=k@lp[i]
    return tot
def null_plug(ph,lp,B):
    tot=np.zeros(B)
    for i in range(K): tot+=rng.multinomial(4,ph[i],size=B)@lp[i]
    return tot
for m in MODEL:
    C=np.array([fr[m][a] for a in A]); ph=(C+AL)/(C+AL).sum(1,keepdims=True); lp=np.log(ph)
    obs_k=np.array([np.bincount(an[m][a],minlength=4) for a in A]); obs=float((obs_k*lp).sum())
    unseen_hits=int(sum(obs_k[i][C[i]==0].sum() for i in range(K)))
    exp_unseen=float(sum(4*ph[i][C[i]==0].sum() for i in range(K)))
    # null components: share of null draws hitting unseen
    np_=null_pp(C,lp,10000); npl=null_plug(ph,lp,10000)
    p_pp=float(np.mean(np_<=obs)); p_pl=float(np.mean(npl<=obs))
    # descriptive
    modal=C.argmax(1); hits=np.concatenate([obs_k[i][modal[i]]*[1]+0 for i in range(K)]) if False else None
    h=np.array([obs_k[i][modal[i]] for i in range(K)]); n=obs_k.sum(1)
    hit=h.sum()/n.sum(); exp=float((ph[np.arange(K),modal]*n).sum()/n.sum())
    bh=[]
    for _ in range(4000):
        idx=rng.integers(0,K,K); bh.append(h[idx].sum()/n[idx].sum())
    pa=obs_k/4; pf=C/48
    cross=float((pa*pf).sum(1).mean()); within=float(wmm(C).mean())
    bc=[]
    for _ in range(4000):
        idx=rng.integers(0,K,K); bc.append(((pa*pf).sum(1)[idx].mean()-wmm(C)[idx].mean()))
    res[m]=dict(obs_loglik=round(obs,2),null_pp_median=round(float(np.median(np_)),2),null_pp_1pct=round(float(np.quantile(np_,.01)),2),
        p_posterior_predictive=p_pp,p_plugin=p_pl,null_plugin_median=round(float(np.median(npl)),2),
        unseen_option_hits_obs=unseen_hits,unseen_option_hits_expected_under_smoothed_model=round(exp_unseen,2),
        share_null_plugin_reps_with_any_unseen_hit=None,
        modal_hit=round(float(hit),3),modal_hit_ci=[round(float(np.quantile(bh,.025)),3),round(float(np.quantile(bh,.975)),3)],modal_hit_expected=round(exp,3),
        anchor_frame_crossmatch=round(cross,3),frame_within_match=round(within,3),cross_minus_within_ci=[round(float(np.quantile(bc,.025)),3),round(float(np.quantile(bc,.975)),3)])
    # critical value from posterior-predictive null for power (B=10000 already)
    crit=np.quantile(np_,.01)
    # also per-array: how many arrays have zero-count options
    res[m]["arrays_with_unseen_options"]=int(sum((C[i]==0).any() for i in range(K)))
    # power
    pw={}
    def sim(P,S=500):
        rej=0
        for _ in range(S):
            tot=0.0
            for i in range(K): tot+=rng.multinomial(4,P[i])@lp[i]
            rej+=tot<=crit
        return rej/S
    P0=C/48
    pw["none (size check)"]=sim(P0)
    for e in (.1,.2,.3,.5): pw[f"mixture uniform eps={e}"]=sim((1-e)*P0+e/4)
    for f in (.1,.25,.5):
        rr=[]
        for _ in range(500):
            P=P0.copy(); sel=rng.choice(K,int(round(f*K)),replace=False)
            for i in sel:
                mo=P[i].argmax(); o=rng.choice([j for j in range(4) if j!=mo]); P[i,o]+=P[i,mo]; P[i,mo]=0
            tot=sum(rng.multinomial(4,P[i])@lp[i] for i in range(K)); rr.append(tot<=crit)
        pw[f"favourite swap f={f}"]=float(np.mean(rr))
    for t in (.5,2):
        Pt=np.where(P0>0,P0,1e-12)**t; Pt=Pt/Pt.sum(1,keepdims=True); pw[f"temper tau={t}"]=sim(Pt)
    res[m]["power_at_p01"]=pw; res[m]["crit_loglik_1pct"]=round(float(crit),2)
json.dump(res,open(os.path.join(OUT,"drift_audit.json"),"w"),indent=1)
print(json.dumps(res,indent=1))
