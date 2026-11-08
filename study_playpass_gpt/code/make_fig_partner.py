#!/usr/bin/env python3
"""Partner x reasoning interaction, matching the structure of fig_2x2_policy_v2.

GPT cells are computed from the raw CSVs. Opus cells are the values reported by the
Opus session (claudine-8d); they are point estimates only, so intervals for BOTH models
are Wilson binomial on (p, n) to keep one method across the figure.
"""
import csv, glob, math
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

try: plt.style.use("academic")
except Exception: pass
plt.rcParams.update({
    "font.family":"sans-serif","font.sans-serif":["Arial","Helvetica","DejaVu Sans"],
    "font.size":9,"axes.labelsize":9,"axes.titlesize":9,"xtick.labelsize":9,
    "ytick.labelsize":9,"legend.fontsize":8,"axes.linewidth":0.8,
    "axes.spines.top":False,"axes.spines.right":False,
    "xtick.direction":"out","ytick.direction":"out","axes.grid":False,
    "figure.facecolor":"white","axes.facecolor":"white","text.color":"black",
    "axes.labelcolor":"black","xtick.color":"black","ytick.color":"black"})

D="/Users/calypsocalcott/Desktop/Coordination/Self_Coordination/study_playpass_gpt/data/"
G={("copy","low"):D+"playpass_full_20260912_191607.csv",
   ("copy","high"):D+"playpass_full_high_20260912_194050.csv",
   ("different","low"):D+"playpass_full_different_low_20260912_195055.csv",
   ("different","high"):sorted(glob.glob(D+"playpass_full_different_high_*.csv"))[-1]}
def cell(f):
    r=[x for x in csv.DictReader(open(f)) if x["parse_ok"]=="1" and x["transport_ok"]=="1"]
    k=sum(1 for x in r if x["decision"].upper()=="PLAY")
    return k/len(r), len(r)
GPT={k:cell(v) for k,v in G.items()}
# Opus, reported by claudine-8d; 600 decisions per cell
OPUS={("copy","low"):(.8717,600),("copy","high"):(.7500,600),
      ("different","low"):(.7167,600),("different","high"):(.6167,600)}

def wilson(p,n,z=1.96):
    d=1+z*z/n; c=(p+z*z/(2*n))/d
    h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return c-h, c+h

fig,axes=plt.subplots(1,2,figsize=(5.5,3.2),sharey=True)
X=[0,1]
STYLE={"low":dict(marker="s",mfc="white",mec="black",ls="--",color="0.45"),
       "high":dict(marker="o",mfc="black",mec="black",ls="-",color="black")}
for ax,(name,data) in zip(axes,(("Claude Opus 5",OPUS),("GPT-5.5",GPT))):
    for eff in ("low","high"):
        ys=[data[("copy",eff)][0], data[("different",eff)][0]]
        los,his=[],[]
        for part in ("copy","different"):
            p,n=data[(part,eff)]; a,b=wilson(p,n); los.append(p-a); his.append(b-p)
        ax.errorbar(X,ys,yerr=[los,his],capsize=2.5,elinewidth=0.8,capthick=0.8,
                    lw=1.0,ms=4.5,**STYLE[eff])
    ax.set_xticks(X); ax.set_xticklabels(["Copy","Different"])
    ax.set_xlim(-0.35,1.35); ax.set_ylim(0,1.0)
    ax.set_title(name)
axes[0].set_ylabel("P(PLAY)")
axes[0].legend(handles=[Line2D([],[],ls="--",color="0.45",marker="s",mfc="white",
                               mec="black",ms=4.5,lw=1.0,label="Low reasoning"),
                        Line2D([],[],ls="-",color="black",marker="o",mfc="black",
                               ms=4.5,lw=1.0,label="High reasoning")],
               loc="lower left",frameon=False,handlelength=2.4)
fig.tight_layout()
for ext in ("pdf","png"):
    fig.savefig(f"/Users/calypsocalcott/Downloads/fig_2x2_partner_v2.{ext}",
                dpi=300,bbox_inches="tight")
print("GPT cells (p, n):")
for k,v in GPT.items(): print(f"  {k[0]:10s}/{k[1]:5s} p={v[0]:.4f} n={v[1]}")
print("saved -> ~/Downloads/fig_2x2_partner_v2.pdf/.png")
