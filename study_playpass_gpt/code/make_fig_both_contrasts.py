#!/usr/bin/env python3
"""Two contrasts side by side, both models, both reasoning levels.

LEFT  partner effect: Copy - Different. PAIRED - same 30 items in both cells.
      bootstrap over item-level paired differences; Wilcoxon signed-rank.
RIGHT policy effect: Clear - No policy, under the COPY partner. UNPAIRED -
      15 clear items vs 15 different no-policy items; independent bootstrap of
      each band; Mann-Whitney. A paired test would be invalid here.

Opus trials read READ-ONLY from opus_2x2_clean.csv (effort axis, verified against
its reported cell means). Nothing in that tree is written.
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

def gpt_cell(f):
    d=collections.defaultdict(list); arm={}
    for x in csv.DictReader(open(f)):
        if x["parse_ok"]=="1" and x["transport_ok"]=="1":
            d[x["array"]].append(1 if x["decision"].upper()=="PLAY" else 0)
            arm[x["array"]]=x["arm"]
    return {k:sum(v)/len(v) for k,v in d.items()}, arm
GI={};GARM={}
for k,v in G.items(): GI[k],GARM[k]=gpt_cell(v)

op=collections.defaultdict(lambda: collections.defaultdict(list)); oarm={}
for x in csv.DictReader(open(OP)):
    key=(x["partner"].lower(),x["effort"])
    op[key][x["item"]].append(int(x["play"])); oarm.setdefault(key,{})[x["item"]]=x["group"]
OI={k:{i:sum(v)/len(v) for i,v in d.items()} for k,d in op.items()}

def boot1(x,B=20000):
    b=np.array([RNG.choice(x,x.size,replace=True).mean() for _ in range(B)])
    return np.percentile(b,[2.5,97.5])
def boot2(a,b,B=20000):
    d=np.array([RNG.choice(a,a.size,replace=True).mean()-RNG.choice(b,b.size,replace=True).mean()
                for _ in range(B)])
    return np.percentile(d,[2.5,97.5])

PART={};POL={}
for name,I,ARM in (("Claude Opus 5",OI,oarm),("GPT-5.5",GI,GARM)):
    for eff in ("low","high"):
        ks=sorted(set(I[("copy",eff)]) & set(I[("different",eff)]))
        d=np.array([I[("copy",eff)][k]-I[("different",eff)][k] for k in ks])
        ci=boot1(d); PART[(name,eff)]=(d.mean(),ci[0],ci[1],stats.wilcoxon(d).pvalue,d.size)
        a=ARM[("copy",eff)]
        hi=np.array([v for k,v in I[("copy",eff)].items() if a[k]=="HIGH"])
        lo=np.array([v for k,v in I[("copy",eff)].items() if a[k]=="LOW"])
        ci2=boot2(hi,lo)
        POL[(name,eff)]=(hi.mean()-lo.mean(),ci2[0],ci2[1],
                         stats.mannwhitneyu(hi,lo).pvalue,(hi.size,lo.size))

print("PARTNER  Copy - Different (paired, 30 items, Wilcoxon)")
for k,v in PART.items(): print(f"  {k[0]:14s} {k[1]:5s} {v[0]:+.4f} [{v[1]:+.4f},{v[2]:+.4f}] p={v[3]:.4f} n_items={v[4]}")
print("POLICY   Clear - No policy under COPY (unpaired 15v15, Mann-Whitney)")
for k,v in POL.items(): print(f"  {k[0]:14s} {k[1]:5s} {v[0]:+.4f} [{v[1]:+.4f},{v[2]:+.4f}] p={v[3]:.4f} n={v[4]}")

try: plt.style.use("academic")
except Exception: pass
plt.rcParams.update({"font.family":"sans-serif",
    "font.sans-serif":["Arial","Helvetica","DejaVu Sans"],"font.size":9,
    "axes.labelsize":9,"axes.titlesize":9,"xtick.labelsize":9,"ytick.labelsize":9,
    "legend.fontsize":8,"axes.linewidth":0.8,"axes.spines.top":False,
    "axes.spines.right":False,"xtick.direction":"out","ytick.direction":"out",
    "axes.grid":False,"figure.facecolor":"white","axes.facecolor":"white"})
fig,axes=plt.subplots(1,2,figsize=(5.5,3.2))
S={"Claude Opus 5":dict(marker="s",mfc="white",mec="black",ls="--",color="0.45",dx=-0.07),
   "GPT-5.5":      dict(marker="o",mfc="black",mec="black",ls="-", color="black",dx=+0.07)}
for ax,(RES,ttl,ylab) in zip(axes,
        ((PART,"Partner","P(PLAY): Copy − Different"),
         (POL, "Policy", "P(PLAY): Clear − No policy"))):
    ax.axhline(0,color="0.6",lw=0.8,ls=":")
    for name in ("Claude Opus 5","GPT-5.5"):
        st=dict(S[name]); dx=st.pop("dx")
        ys=[RES[(name,e)][0] for e in ("low","high")]
        lo=[ys[i]-RES[(name,e)][1] for i,e in enumerate(("low","high"))]
        hi=[RES[(name,e)][2]-ys[i] for i,e in enumerate(("low","high"))]
        ax.errorbar([0+dx,1+dx],ys,yerr=[lo,hi],capsize=2.5,elinewidth=0.8,
                    capthick=0.8,lw=1.0,ms=4.5,**st)
    ax.set_xticks([0,1]); ax.set_xticklabels(["Low","High"])
    ax.set_xlim(-0.4,1.4); ax.set_xlabel("Reasoning"); ax.set_ylabel(ylab)
    ax.set_title(ttl); ax.set_ylim(bottom=min(0,ax.get_ylim()[0]))
axes[1].legend(handles=[Line2D([],[],ls="--",color="0.45",marker="s",mfc="white",
                               mec="black",ms=4.5,lw=1.0,label="Claude Opus 5"),
                        Line2D([],[],ls="-",color="black",marker="o",mfc="black",
                               ms=4.5,lw=1.0,label="GPT-5.5")],
               loc="lower right",frameon=False,handlelength=2.4)
fig.tight_layout()
for ext in ("pdf","png"):
    fig.savefig(f"/Users/calypsocalcott/Downloads/fig_both_contrasts.{ext}",dpi=300,bbox_inches="tight")
print("saved -> ~/Downloads/fig_both_contrasts.pdf/.png")
