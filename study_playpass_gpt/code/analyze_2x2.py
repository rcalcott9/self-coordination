#!/usr/bin/env python3
"""GPT PLAY/PASS: partner x reasoning-effort, with the policy split inside each cell.

Cell identity comes from an EXPLICIT map. Two files predate the effort/partner
flags (copy/low has neither, copy/high has no partner), so neither column nor
filename inference is safe across all four.

No d'/AUC/sensitivity on any DIFFERENT cell: within_model_match is copy-copy
agreement and is not ground truth for a differently-trained partner.
"""
import csv, collections, glob
import numpy as np
from scipy import stats

HERE="/Users/calypsocalcott/Desktop/Coordination/Self_Coordination/study_playpass_gpt"
# different/high is globbed: its stamp changed after the spend-limit run was voided.
CELLS={("copy","low"):      "playpass_full_20260912_191607.csv",
       ("copy","high"):     "playpass_full_high_20260912_194050.csv",
       ("different","low"): "playpass_full_different_low_20260912_195055.csv",
       ("different","high"):sorted(
           f.split("/")[-1] for f in glob.glob(
               HERE+"/data/playpass_full_different_high_*.csv"))[-1]}
RNG=np.random.default_rng(20260912)

def load(fn):
    rows=[r for r in csv.DictReader(open(HERE+"/data/"+fn))
          if r["parse_ok"]=="1" and r["transport_ok"]=="1"]
    for r in rows: r["play"]=1 if r["decision"].upper()=="PLAY" else 0
    return rows

def items(rows):
    d=collections.OrderedDict()
    for r in rows: d.setdefault(r["array"],[]).append(r)
    return {k:dict(arm=v[0]["arm"],agr=float(v[0]["agreement"]),n=len(v),
                   p=sum(x["play"] for x in v)/len(v)) for k,v in d.items()}

C={k:load(v) for k,v in CELLS.items()}
I={k:items(v) for k,v in C.items()}
keys=sorted(set.intersection(*[set(v) for v in I.values()]))
hi=[k for k in keys if I[("copy","low")][k]["arm"]=="HIGH"]
lo=[k for k in keys if I[("copy","low")][k]["arm"]=="LOW"]
assert len(keys)==30 and len(hi)==15 and len(lo)==15, (len(keys),len(hi),len(lo))

def rate(rows,arm=None):
    s=[r for r in rows if arm is None or r["arm"]==arm]
    return sum(x["play"] for x in s)/len(s) if s else float("nan")
def boot(x,B=20000):
    b=np.array([RNG.choice(x,x.size,replace=True).mean() for _ in range(B)])
    return np.percentile(b,[2.5,97.5])
def ivec(cell,ks): return np.array([I[cell][k]["p"] for k in ks])

L=[];A=L.append
A("="*74); A("GPT-5.5 PLAY/PASS — partner x reasoning effort"); A("="*74)
for k,v in CELLS.items(): A(f"  {k[0]:10s} {k[1]:5s}  n={len(C[k]):4d}  {v}")
A("")
A("[1] P(PLAY) — 2x2")
A(f"  {'':12s}{'COPY':>10s}{'DIFFERENT':>12s}{'partner eff':>13s}")
for e in ("low","high"):
    a,b=rate(C[("copy",e)]),rate(C[("different",e)])
    A(f"  {e+' effort':12s}{a:10.4f}{b:12.4f}{b-a:+13.4f}")
A(f"  {'effort eff':12s}{rate(C[('copy','high')])-rate(C[('copy','low')]):+10.4f}"
  f"{rate(C[('different','high')])-rate(C[('different','low')]):+12.4f}")
A("")
A("[2] POLICY SPLIT INSIDE EACH CELL  (clear vs no policy)")
A(f"  {'cell':20s}{'clear':>8s}{'none':>8s}{'diff':>9s}")
for k in CELLS:
    a,b=rate(C[k],"HIGH"),rate(C[k],"LOW")
    A(f"  {k[0]+'/'+k[1]:20s}{a:8.4f}{b:8.4f}{a-b:+9.4f}")
A("")
A("[3] PARTNER EFFECT, paired by item (COPY minus DIFFERENT)")
for e in ("low","high"):
    d=ivec(("copy",e),keys)-ivec(("different",e),keys)
    ci=boot(d)
    A(f"  {e:5s} effort  all30 {d.mean():+.4f} [{ci[0]:+.4f},{ci[1]:+.4f}]  "
      f"Wilcoxon p={stats.wilcoxon(d).pvalue:.4f}")
    for lab,ks in (("clear",hi),("none",lo)):
        dd=ivec(("copy",e),ks)-ivec(("different",e),ks); c2=boot(dd)
        A(f"           {lab:6s} {dd.mean():+.4f} [{c2[0]:+.4f},{c2[1]:+.4f}]  "
          f"p={stats.wilcoxon(dd).pvalue:.4f}")
A("")
A("[4] PARTNER x EFFORT INTERACTION  (item-clustered bootstrap)")
dlo=ivec(("copy","low"),keys)-ivec(("different","low"),keys)
dhi=ivec(("copy","high"),keys)-ivec(("different","high"),keys)
diff=dhi-dlo; ci=boot(diff)
A(f"  partner effect at high minus at low = {diff.mean():+.4f}  95% CI [{ci[0]:+.4f}, {ci[1]:+.4f}]")
A(f"  Wilcoxon on paired item differences: p = {stats.wilcoxon(diff).pvalue:.4f}")
A("  NOTE widest intervals in the study: the high row is n=300 per cell vs 600 at low.")
A("")
A("[5] ACCURACY — COPY CELLS ONLY (ground truth exists only against copies)")
for e in ("low","high"):
    k=("copy",e); ph,pl=rate(C[k],"HIGH"),rate(C[k],"LOW")
    n_h=len([r for r in C[k] if r["arm"]=="HIGH"]); n_l=len(C[k])-n_h
    def z(p,n): return stats.norm.ppf(min(max(p,0.5/n),1-0.5/n))
    dpr=z(ph,n_h)-z(pl,n_l); crit=-0.5*(z(ph,n_h)+z(pl,n_l))
    auc=stats.mannwhitneyu(ivec(k,hi),ivec(k,lo))[0]/225
    A(f"  copy/{e:5s}  d'={dpr:.3f}  AUC={auc:.4f}  c={crit:+.4f}  spec={1-pl:.4f}")
A("  DIFFERENT cells: no accuracy statistics by design.")
A("="*74)
t="\n".join(L); print(t)
open(HERE+"/results/partner_x_effort_REPORT.txt","w").write(t+"\n")
