#!/usr/bin/env python3
"""Paired Copy-minus-DIFFERENT partner effect, both models, both reasoning levels.

Pairing is by item: every cell contains the same 30 arrays within a model, so the
item-level difference removes between-item variance. Opus trials are read READ-ONLY
from ~/Desktop/Stag/opus_playpass/results/opus_2x2_clean.csv (effort axis; verified
against its reported cell means). Nothing in that tree is written.
"""
import csv, glob, collections
import numpy as np
from scipy import stats
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

RNG=np.random.default_rng(20260912)
D="/Users/calypsocalcott/Desktop/Coordination/Self_Coordination/study_playpass_gpt/data/"
OP="/Users/calypsocalcott/Desktop/Stag/opus_playpass/results/opus_2x2_clean.csv"
G={("copy","low"):D+"playpass_full_20260912_191607.csv",
   ("copy","high"):D+"playpass_full_high_20260912_194050.csv",
   ("different","low"):D+"playpass_full_different_low_20260912_195055.csv",
   ("different","high"):sorted(glob.glob(D+"playpass_full_different_high_*.csv"))[-1]}

def gpt_items(f):
    d=collections.defaultdict(list)
    for x in csv.DictReader(open(f)):
        if x["parse_ok"]=="1" and x["transport_ok"]=="1":
            d[x["array"]].append(1 if x["decision"].upper()=="PLAY" else 0)
    return {k:sum(v)/len(v) for k,v in d.items()}
GI={k:gpt_items(v) for k,v in G.items()}

op=collections.defaultdict(lambda: collections.defaultdict(list))
for x in csv.DictReader(open(OP)):
    op[(x["partner"].lower(),x["effort"])][x["item"]].append(int(x["play"]))
OI={k:{i:sum(v)/len(v) for i,v in d.items()} for k,d in op.items()}

def paired(I,eff):
    ks=sorted(set(I[("copy",eff)]) & set(I[("different",eff)]))
    return np.array([I[("copy",eff)][k]-I[("different",eff)][k] for k in ks])
def boot(x,B=20000):
    b=np.array([RNG.choice(x,x.size,replace=True).mean() for _ in range(B)])
    return np.percentile(b,[2.5,97.5])

RES={}
for name,I in (("Claude Opus 5",OI),("GPT-5.5",GI)):
    for eff in ("low","high"):
        d=paired(I,eff); ci=boot(d)
        RES[(name,eff)]=(d.mean(),ci[0],ci[1],stats.wilcoxon(d).pvalue,d.size)
        print(f"{name:14s} {eff:5s}  n_items={d.size}  diff={d.mean():+.4f}  "
              f"95% CI [{ci[0]:+.4f}, {ci[1]:+.4f}]  Wilcoxon p={stats.wilcoxon(d).pvalue:.4f}")

try: plt.style.use("academic")
except Exception: pass
plt.rcParams.update({"font.family":"sans-serif",
    "font.sans-serif":["Arial","Helvetica","DejaVu Sans"],"font.size":9,
    "axes.labelsize":9,"xtick.labelsize":9,"ytick.labelsize":9,"legend.fontsize":8,
    "axes.linewidth":0.8,"axes.spines.top":False,"axes.spines.right":False,
    "xtick.direction":"out","ytick.direction":"out","axes.grid":False,
    "figure.facecolor":"white","axes.facecolor":"white"})
fig,ax=plt.subplots(figsize=(5.5,3.2))
ax.axhline(0,color="0.6",lw=0.8,ls=":")
S={"Claude Opus 5":dict(marker="s",mfc="white",mec="black",ls="--",color="0.45",dx=-0.07),
   "GPT-5.5":      dict(marker="o",mfc="black",mec="black",ls="-", color="black",dx=+0.07)}
for name in ("Claude Opus 5","GPT-5.5"):
    st=dict(S[name]); dx=st.pop("dx")
    xs=[0+dx,1+dx]; ys=[RES[(name,e)][0] for e in ("low","high")]
    lo=[ys[i]-RES[(name,e)][1] for i,e in enumerate(("low","high"))]
    hi=[RES[(name,e)][2]-ys[i] for i,e in enumerate(("low","high"))]
    ax.errorbar(xs,ys,yerr=[lo,hi],capsize=2.5,elinewidth=0.8,capthick=0.8,lw=1.0,ms=4.5,**st)
ax.set_xticks([0,1]); ax.set_xticklabels(["Low reasoning","High reasoning"])
ax.set_xlim(-0.4,1.4)
ax.set_ylabel("P(PLAY): Copy − Different")
ax.legend(handles=[Line2D([],[],ls="--",color="0.45",marker="s",mfc="white",mec="black",
                          ms=4.5,lw=1.0,label="Claude Opus 5"),
                   Line2D([],[],ls="-",color="black",marker="o",mfc="black",
                          ms=4.5,lw=1.0,label="GPT-5.5")],
          loc="upper right",frameon=False,handlelength=2.4)
fig.tight_layout()
for ext in ("pdf","png"):
    fig.savefig(f"/Users/calypsocalcott/Downloads/fig_partner_difference.{ext}",
                dpi=300,bbox_inches="tight")
print("saved -> ~/Downloads/fig_partner_difference.pdf/.png")
