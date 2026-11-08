#!/usr/bin/env python3
"""Partner-sensitivity contrast: COPY vs DIFFERENT, both at reasoning effort low.

Deliberately reports NO d'/AUC/sensitivity. Those require ground truth, and our
labels (within_model_match) are agreement among GPT COPIES - they are not the
truth for a differently-trained partner. This cell measures willingness to bet.
Items are identical across arms, so everything is paired by item.
"""
import csv, glob, json, collections
import numpy as np
from scipy import stats

HERE="/Users/calypsocalcott/Desktop/Coordination/Self_Coordination/study_playpass_gpt"
COPY=HERE+"/data/playpass_full_20260912_191607.csv"
DIFF=sorted(glob.glob(HERE+"/data/playpass_full_different_low_*.csv"))[-1]
RNG=np.random.default_rng(20260912)

def load(f):
    rows=[r for r in csv.DictReader(open(f)) if r["parse_ok"]=="1" and r["transport_ok"]=="1"]
    for r in rows: r["play"]=1 if r["decision"].upper()=="PLAY" else 0
    return rows

def items(rows):
    d=collections.OrderedDict()
    for r in rows: d.setdefault(r["array"],[]).append(r)
    return {k:dict(arm=v[0]["arm"],agr=float(v[0]["agreement"]),
                   n=len(v),p=sum(x["play"] for x in v)/len(v)) for k,v in d.items()}

C,D=load(COPY),load(DIFF)
ic,idf=items(C),items(D)
keys=[k for k in ic if k in idf]
assert len(keys)==30, len(keys)
hi=[k for k in keys if ic[k]["arm"]=="HIGH"]; lo=[k for k in keys if ic[k]["arm"]=="LOW"]

def rate(rows,arm=None):
    s=[r for r in rows if arm is None or r["arm"]==arm]
    return sum(x["play"] for x in s)/len(s)

L=[];A=L.append
A("="*70); A("PARTNER SENSITIVITY — COPY vs DIFFERENT (both effort low)"); A("="*70)
A(f"COPY      {COPY.split('/')[-1]}  n={len(C)}")
A(f"DIFFERENT {DIFF.split('/')[-1]}  n={len(D)}")
A(f"prompt sha8: copy cbc2592c | different {D[0]['prompt_sha8']}")
A("")
A("[A] P(PLAY) BY PARTNER")
A(f"  {'':10s}{'COPY':>9s}{'DIFFERENT':>11s}{'change':>10s}")
for lab,arm in (("overall",None),("HIGH",("HIGH")),("LOW",("LOW"))):
    a,b=rate(C,arm),rate(D,arm)
    A(f"  {lab:10s}{a:9.4f}{b:11.4f}{b-a:+10.4f}")
A("")

# paired by item
dc=np.array([ic[k]["p"]-idf[k]["p"] for k in keys])
dh=np.array([ic[k]["p"]-idf[k]["p"] for k in hi])
dl=np.array([ic[k]["p"]-idf[k]["p"] for k in lo])
def boot_ci(x,B=20000):
    b=np.array([RNG.choice(x,x.size,replace=True).mean() for _ in range(B)])
    return np.percentile(b,[2.5,97.5])
A("[B] PAIRED BY ITEM  (COPY minus DIFFERENT, positive = partner identity matters)")
for lab,x in (("all 30",dc),("HIGH 15",dh),("LOW 15",dl)):
    ci=boot_ci(x); t=stats.wilcoxon(x) if np.any(x!=0) else None
    A(f"  {lab:8s} mean drop {x.mean():+.4f}  95% CI [{ci[0]:+.4f}, {ci[1]:+.4f}]"
      f"  Wilcoxon p={t.pvalue:.4f}" if t else f"  {lab:8s} all zero")
A("")
A("[C] INTERACTION  (does the partner effect depend on policy stability?)")
inter=dl.mean()-dh.mean()
B=20000
bi=np.array([RNG.choice(dl,dl.size,replace=True).mean()-RNG.choice(dh,dh.size,replace=True).mean()
             for _ in range(B)])
ci=np.percentile(bi,[2.5,97.5])
A(f"  LOW drop - HIGH drop = {inter:+.4f}   95% CI [{ci[0]:+.4f}, {ci[1]:+.4f}]")
A(f"  Mann-Whitney on item drops (HIGH vs LOW): p = {stats.mannwhitneyu(dh,dl).pvalue:.4f}")
A("")
A("[D] WITHIN-DIFFERENT: does the stimulus split still move behaviour?")
a,b=rate(D,"HIGH"),rate(D,"LOW")
ph=np.array([idf[k]["p"] for k in hi]); pl=np.array([idf[k]["p"] for k in lo])
A(f"  P(PLAY|HIGH items) {a:.4f}   P(PLAY|LOW items) {b:.4f}   difference {a-b:+.4f}")
A(f"  item-level Mann-Whitney p = {stats.mannwhitneyu(ph,pl).pvalue:.4f}")
rho,prho=stats.spearmanr([idf[k]['agr'] for k in keys],[idf[k]['p'] for k in keys])
A(f"  Spearman(copy-agreement, item P(PLAY)) = {rho:+.4f}, p = {prho:.4f}")
A("  NOTE: agreement here is COPY-copy agreement. It is NOT ground truth for a")
A("  differently-trained partner, so this is a stimulus effect, not accuracy.")
A("")
A("[E] ITEMS WITH THE LARGEST PARTNER EFFECT")
for k in sorted(keys,key=lambda k:-(ic[k]["p"]-idf[k]["p"]))[:6]:
    A(f"  {k:22s} {ic[k]['arm']:5s} agr {ic[k]['agr']:.3f}  COPY {ic[k]['p']:.2f} -> DIFF {idf[k]['p']:.2f}")
A("="*70)
t="\n".join(L); print(t)
open(HERE+"/results/partner_contrast_REPORT.txt","w").write(t+"\n")
