#!/usr/bin/env python3
"""Follow-ups: is the hedge caused by the PICTURE or by the PRICE?"""
import csv, os, random
from collections import Counter, defaultdict
EXP=("/Users/calypsocalcott/Desktop/Coordination/Self_Coordination/"
     "policy_specific_self_coordination_20260812_1401")
random.seed(20260825)
corpus=list(csv.DictReader(open(os.path.join(EXP,"reasoning_traces/trace_corpus.csv"))))
truth={}
for r in csv.DictReader(open(os.path.join(EXP,"data/attempt_rates.csv"))):
    truth[(r["model"],r["stimulus"])]=dict(sm=float(r["true_self_match"]),fc=float(r["form_consistency"]))
H="hedge_no_rule"; hit=lambda r,k: r[k] in ("1","True","true","1.0")
LBL={"gpt":"GPT-5.5","claude":"Claude Opus 5"}
def pearson(x,y):
    n=len(x);mx=sum(x)/n;my=sum(y)/n
    num=sum((a-mx)*(b-my) for a,b in zip(x,y))
    den=(sum((a-mx)**2 for a in x)*sum((b-my)**2 for b in y))**.5
    return num/den if den else float('nan')

print("="*100)
print("A.  HOW MANY TRIALS EVER SAY 'NO CLEAR RULE' WHILE PLAYING?")
print("="*100)
c=Counter((r["participation_decision"],hit(r,H)) for r in corpus)
att_h=c[("ATTEMPT",True)]; att_n=c[("ATTEMPT",False)]
saf_h=c[("SAFE",True)];    saf_n=c[("SAFE",False)]
print(f"  ATTEMPT  hedged {att_h:4d} / {att_h+att_n:4d}  = {att_h/(att_h+att_n):.4f}")
print(f"  SAFE     hedged {saf_h:4d} / {saf_h+saf_n:4d}  = {saf_h/(saf_h+saf_n):.4f}")

print()
print("="*100)
print("B.  IS THE SAFE-SIDE HEDGE CALIBRATED TO THE TRUE RULE?")
print("="*100)
xs=[];ys=[]
print(f"{'actor':14s}{'stimulus':17s}{'self_match':>11}{'form_cons':>11}{'hedge|SAFE':>12}{'n':>6}")
for (a,st),t in sorted(truth.items(), key=lambda kv:-kv[1]['sm']):
    saf=[r for r in corpus if r["actor_model"]==a and r["stimulus"]==st and r["participation_decision"]=="SAFE"]
    if len(saf)<10: continue
    h=sum(hit(r,H) for r in saf)/len(saf)
    xs.append(t['sm']); ys.append(h)
    flag="   <-- perfect convention, still says 'no rule'" if t['sm']>=0.99 and h>0.2 else ""
    print(f"{LBL[a]:14s}{st:17s}{t['sm']:>11.3f}{t['fc']:>11.3f}{h:>12.3f}{len(saf):>6}{flag}")
print(f"\n  corr(hedge|SAFE, true self-match) = {pearson(ys,xs):+.3f}   (negative would mean calibrated)")

print()
print("="*100)
print("C.  DECISIVE: WITHIN ONE STIMULUS, DOES THE HEDGE RISE WITH THE SAFE PAYOFF?")
print("="*100)
print("  The image is byte-identical across payoff levels. If 'there is no clear rule'")
print("  is a reading of the picture, it cannot move with the price.\n")
print(f"{'actor':14s}{'stimulus':17s}" + "".join(f"{'k='+k:>9}" for k in ("3","5","7","9")) + f"{'slope':>9}")
slopes=[]
for (a,st),t in sorted(truth.items()):
    row=[];ks=[]
    for k in ("3","5","7","9"):
        sub=[r for r in corpus if r["actor_model"]==a and r["stimulus"]==st and r["safe_payoff"]==k]
        row.append(sum(hit(r,H) for r in sub)/len(sub) if sub else float('nan')); ks.append(float(k))
    if any(v!=v for v in row): continue
    sl=pearson(ks,row)*(max(row)-min(row))
    slopes.append(row[3]-row[0])
    print(f"{LBL[a]:14s}{st:17s}" + "".join(f"{v:>9.3f}" for v in row) + f"{row[3]-row[0]:>+9.3f}")
print(f"\n  mean rise from safe=3 to safe=9 : {sum(slopes)/len(slopes):+.3f}  over {len(slopes)} cells")
print(f"  cells rising: {sum(1 for s in slopes if s>0.02)} / {len(slopes)}")
