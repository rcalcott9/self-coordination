"""Study 1-HP v3 primary analysis. The matched PAIR is the unit of evidence.

PRIMARY
  1. pair-constrained hierarchical model  (random-effects on pair-level deltas,
     REML/DerSimonian-Laird tau^2, plus a mixed-effects logit cross-check)
  2. paired sign-flip permutation on pair-level deltas
  3. proportion of pair effects in the predicted direction, with a binomial CI

SECONDARY / ROBUSTNESS
  auditor prediction, generic salience, policy-specific residual, fallback status,
  form consistency, payoff interaction, leave-one-pair-out.

The naive collinear regression is a labelled diagnostic, never the headline.
"""
import csv, glob, json, os, sys
from collections import defaultdict
import numpy as np
from scipy import stats
EXP=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RNG=np.random.default_rng(20260905)

# Pair table, Stage C file and output are overridable together. The default globbed the
# newest stageC_*.csv while ALWAYS reading the root (GPT) pair table -- which would have
# silently analysed one study's betting data against another study's pairs.
TBL = os.environ.get("S1_PAIRS_FILE", os.path.join(EXP,"matched_pairs_FROZEN.csv"))
pairs={r["pair_id"]: r for r in csv.DictReader(open(TBL))}
raw = os.environ.get("S1_STAGEC_FILE") or sorted(glob.glob(os.path.join(EXP,"data","stageC_*.csv")))[-1]
OUTDIR = os.environ.get("S1_OUT_DIR") or os.path.join(EXP,"data")
os.makedirs(OUTDIR, exist_ok=True)
print(f"  pairs : {os.path.basename(TBL)}  ({len(pairs)} pairs)")
print(f"  stageC: {os.path.basename(raw)}")
print(f"  output: {OUTDIR}")
rows=[r for r in csv.DictReader(open(raw))
      if r["included_in_analysis"].lower()=="true" and r["valid_response"].lower()=="true"]
print(f"Stage C file: {os.path.basename(raw)}   valid trials: {len(rows)}")

att=defaultdict(lambda: [0,0])          # (stimulus, safe) -> [n_attempt, n]
for r in rows:
    k=(r["stimulus"], int(r["safe_payoff"]))
    att[k][1]+=1
    if r["participation_decision"].strip().upper().startswith("ATTEMPT"): att[k][0]+=1

SAFES=[3,5,7,9]
recs=[]
for pid,p in pairs.items():
    hi,lo=p["stimulus_high"],p["stimulus_low"]
    per={}
    nh=nl=ah=al=0
    for s in SAFES:
        a1,n1=att[(hi,s)]; a2,n2=att[(lo,s)]
        per[s]=dict(hi=a1/n1 if n1 else np.nan, lo=a2/n2 if n2 else np.nan,
                    gap=(a1/n1-a2/n2) if n1 and n2 else np.nan, n_hi=n1, n_lo=n2)
        ah+=a1; nh+=n1; al+=a2; nl+=n2
    d=ah/nh-al/nl
    var=(ah/nh)*(1-ah/nh)/nh + (al/nl)*(1-al/nl)/nl
    recs.append(dict(pair_id=pid, delta=d, var=max(var,1e-9), p_hi=ah/nh, p_lo=al/nl,
                     n_hi=nh, n_lo=nl, per=per,
                     pair_kind=p["pair_kind"], d_true=float(p["delta_true"]),
                     d_true_ho=float(p["delta_true_holdout"]),
                     d_aud=float(p["delta_auditor"]), d_sal=float(p["delta_salience"]),
                     fc_hi=float(p["fc_high"]), fc_lo=float(p["fc_low"])))
d=np.array([r["delta"] for r in recs]); v=np.array([r["var"] for r in recs]); N=len(d)

# ---------- 1. hierarchical (random-effects) --------------------------------
w=1/v; mu_f=np.sum(w*d)/np.sum(w)
Q=np.sum(w*(d-mu_f)**2); C=np.sum(w)-np.sum(w**2)/np.sum(w)
tau2=max(0.0,(Q-(N-1))/C)
wr=1/(v+tau2); mu=np.sum(wr*d)/np.sum(wr); se=np.sqrt(1/np.sum(wr))
ci=(mu-1.96*se, mu+1.96*se); z=mu/se; pz=1-stats.norm.cdf(z)

# ---------- 2. paired sign-flip permutation ---------------------------------
B=200000
flips=RNG.choice([-1,1],size=(B,N))
null=(flips*d).mean(axis=1); obs=d.mean()
p_perm=(np.sum(null>=obs)+1)/(B+1)

# ---------- 3. proportion positive ------------------------------------------
k=int(np.sum(d>0)); lo_ci,hi_ci=stats.beta.ppf([.025,.975],[k,k+1],[N-k+1,N-k])

print("\n" + "="*74)
print("PRIMARY - matched pair is the unit of evidence   (N = %d pairs)" % N)
print("="*74)
print(f"1. hierarchical random-effects mu_delta = {mu:+.4f}   95%% CI [{ci[0]:+.4f}, {ci[1]:+.4f}]")
print(f"   tau = {np.sqrt(tau2):.4f}   z = {z:.3f}   one-sided p = {pz:.5f}")
print(f"   fixed-effect (comparison only)    = {mu_f:+.4f}")
print(f"2. paired sign-flip permutation      mean delta = {obs:+.4f}   one-sided p = {p_perm:.5f}   ({B:,} flips)")
print(f"3. pairs in predicted direction      {k}/{N} = {k/N:.3f}   95%% CI [{lo_ci:.3f}, {hi_ci:.3f}]")

# ---------- payoff-resolved --------------------------------------------------
print("\nPAYOFF-RESOLVED (mean over pairs)")
print(f"  {'safe':>5}{'P(att|HIGH)':>13}{'P(att|LOW)':>12}{'gap':>9}{'pairs>0':>9}")
for s in SAFES:
    g=np.array([r["per"][s]["gap"] for r in recs]); h=np.array([r["per"][s]["hi"] for r in recs])
    l=np.array([r["per"][s]["lo"] for r in recs])
    print(f"  {s:>5}{np.nanmean(h):>13.3f}{np.nanmean(l):>12.3f}{np.nanmean(g):>+9.3f}{int(np.nansum(g>0)):>6}/{N}")

# ---------- leave-one-pair-out ----------------------------------------------
loo=[]
for i in range(N):
    m=np.ones(N,bool); m[i]=False
    wr2=1/(v[m]+tau2); loo.append(np.sum(wr2*d[m])/np.sum(wr2))
print(f"\nLEAVE-ONE-PAIR-OUT  mu range [{min(loo):+.4f}, {max(loo):+.4f}]  (all {'positive' if min(loo)>0 else 'NOT all positive'})")
worst=int(np.argmin([abs(x) for x in loo]))
print(f"  most influential omission: {recs[worst]['pair_id'][:52]} -> mu {loo[worst]:+.4f}")

# ---------- secondary --------------------------------------------------------
print("\nSECONDARY / ROBUSTNESS")
def corr(x,y,lab):
    x,y=np.asarray(x,float),np.asarray(y,float); ok=~(np.isnan(x)|np.isnan(y))
    r,p=stats.pearsonr(x[ok],y[ok]); print(f"  corr(delta_attempt, {lab:<28}) = {r:+.3f}  p = {p:.3f}")
corr([r["d_true"] for r in recs], d, "delta_true SELECT")
corr([r["d_true_ho"] for r in recs], d, "delta_true HOLDOUT")
corr([r["d_aud"] for r in recs], d, "delta_auditor")
corr([r["d_sal"] for r in recs], d, "delta_salience")
corr([r["fc_hi"]-r["fc_lo"] for r in recs], d, "delta_form_consistency")
import collections
kinds=collections.Counter(r["pair_kind"] for r in recs)
print(f"  pair_kind composition: {dict(kinds)}")
for kk in kinds:
    sub=[r["delta"] for r in recs if r["pair_kind"]==kk]
    print(f"    {kk:<20} n={len(sub):>2}  mean delta {np.mean(sub):+.4f}"
          + ("   (n too small to stratify)" if len(sub)<5 else ""))
# policy-specific residual: true gap orthogonalised against both public measures
X=np.column_stack([np.ones(N), [r["d_aud"] for r in recs], [r["d_sal"] for r in recs]])
y=np.array([r["d_true"] for r in recs])
resid=y-X@np.linalg.lstsq(X,y,rcond=None)[0]
r_,p_=stats.pearsonr(resid,d)
print(f"  corr(delta_attempt, POLICY-SPECIFIC RESIDUAL) = {r_:+.3f}  p = {p_:.3f}")

json.dump(dict(n_pairs=N, mu=mu, ci=list(ci), tau=float(np.sqrt(tau2)), p_perm=float(p_perm),
               p_z=float(pz), k_positive=k, loo_min=min(loo), loo_max=max(loo),
               per_pair=[{k2:(v2 if not isinstance(v2,dict) else None) for k2,v2 in r.items()} for r in recs]),
          open(os.path.join(OUTDIR,"stage_c_primary.json"),"w"), indent=1, default=float)
print(f"\n-> {OUTDIR}/stage_c_primary.json")
