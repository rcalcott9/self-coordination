import pandas as pd, numpy as np, glob, os
D="/private/tmp/claude-501/-Users-calypsocalcott-claudine/8af99f85-3869-407a-b3e1-59e1fe454c62/scratchpad/plunkett/data"
os.chdir(D)
MODELS=["gpt-4o-mini-2024-07-18","gpt-4o-2024-08-06"]

def z(x): 
    x=np.asarray(x,float); return (x-np.nanmean(x))/np.nanstd(x,ddof=1)

# --- true instilled weights, first 100 contexts ---
tw=pd.read_csv("instilled_weights.csv").iloc[:100]
tw=tw.melt(id_vars="scenario",value_vars=[f"attr{i}" for i in range(1,6)],
           var_name="attr",value_name="true_b")
tw["attr"]=tw["attr"].str.replace("attr","")

def load_reg(model,latent=False):
    f=f"{model}_{'latent_' if latent else ''}regression_results.csv"
    r=pd.read_csv(f)
    r=r.melt(id_vars="scenario",value_vars=[f"b_attr{i}" for i in range(1,6)],
             var_name="attr",value_name="b")
    r["attr"]=r["attr"].str.replace("b_attr","")
    r["std_b"]=z(r["b"])
    return r

print("="*72)
print("GATE 1 — did the instilled policy get learned?  (behavioral b vs TRUE weights)")
print("="*72)
for m in MODELS:
    r=load_reg(m)
    j=r.merge(tw,on=["scenario","attr"])
    j["std_true"]=z(j["true_b"])
    print(f"  {m:28s}  n={len(j):5d} contexts_fit={r.scenario.nunique():4d}  r = {np.corrcoef(j.std_b,j.std_true)[0,1]:.3f}")

print()
print("="*72)
print("GATE 3 — self-report accuracy  (REPORTED weights vs BEHAVIORAL weights)")
print("="*72)
def mean_reports(fn):
    d=pd.read_csv(fn)
    d=d.melt(id_vars=["explaining_model","version","scenario"],
             value_vars=[f"report_attr{i}" for i in range(1,6)],
             var_name="attr",value_name="report")
    d["attr"]=d["attr"].str.replace("report_attr","")
    g=d.groupby(["scenario","attr"],as_index=False)["report"].mean()
    g["std_rep"]=z(g["report"])
    return g,d

rows=[]
for m in MODELS:
    reg=load_reg(m); regl=load_reg(m,latent=True)
    for label,fn,target in [
        ("base model (CONTROL)",        f"{m}_weight_reports.csv", reg),
        ("instilled, no i-training",    f"{m}_instilled_weight_reports.csv", reg),
        ("i-trained first50 -> last50", f"{m}_itrained_first_50_of_100_50ex_weight_reports.csv", reg),
        ("i-trained last50 -> first50", f"{m}_itrained_last_50_of_100_50ex_weight_reports.csv", reg),
        ("instilled -> NATIVE 100-200", f"{m}_instilled_latent_weight_reports.csv", regl),
        ("i-trained all100 -> NATIVE",  f"{m}_itrained_all_100_50ex_latent_weight_reports.csv", regl),
    ]:
        if not os.path.exists(fn): print("  MISSING",fn); continue
        g,raw=mean_reports(fn)
        j=g.merge(target,on=["scenario","attr"])
        r=np.corrcoef(j.std_rep,j.std_b)[0,1]
        rows.append((m,label,len(j),j.scenario.nunique(),r))
        print(f"  {m:26s} {label:30s} n={len(j):4d} ctx={j.scenario.nunique():4d}  r = {r:+.3f}")
    print()

print("="*72)
print("Sanity: reported vs TRUE weights (instilled model, no i-training)")
print("="*72)
for m in MODELS:
    g,_=mean_reports(f"{m}_instilled_weight_reports.csv")
    j=g.merge(tw,on=["scenario","attr"]); j["std_true"]=z(j["true_b"])
    print(f"  {m:28s} r(report, TRUE) = {np.corrcoef(j.std_rep,j.std_true)[0,1]:+.3f}")
