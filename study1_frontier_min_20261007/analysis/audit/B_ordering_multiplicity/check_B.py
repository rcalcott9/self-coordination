import csv, glob, json, os, hashlib, collections as C, re
import numpy as np
from scipy import stats
ROOT=os.path.expanduser("~/Desktop/Coordination/Self_Coordination/study1_frontier_min_20261007")
F=json.load(open(f"{ROOT}/design/FROZEN.json"))
STIM=F["stimuli_root"]
man={a:{int(k):v for k,v in json.load(open(f"{STIM}/{a}/manifest.json")).items()} for a in F["arrays"]}
out={}
# 1. schedule / balance / manifest / sha
viol=C.Counter(); cells=0; details=[]
for stage in ("preflight","pilot","anchor","main"):
    rows=[r for f in glob.glob(f"{ROOT}/runs/{stage}/*.csv") for r in csv.DictReader(open(f))]
    sched=C.defaultdict(list)
    for j in F["schedule"]:
        if j["stage"]==stage: sched[(j["task"],j["focal"],j["array"])].append(j["perm_id"])
    got=C.defaultdict(list)
    for r in rows:
        got[(r["task"],r["focal"],r["array"])].append(int(r["perm_id"]))
        if json.loads(r["display_order"])!=man[r["array"]][int(r["perm_id"])]: viol[f"{stage}:display_order"]+=1
        if r["stimulus_sha8"]!=F["stimuli"][r["array"]]["perm_png_sha8"][r["perm_id"]]: viol[f"{stage}:stim_sha"]+=1
        if r["prompt_sha8"]!=F["prompts"][r["prompt_key"]]["sha8"]: viol[f"{stage}:prompt_sha"]+=1
        if r["frozen_sha8"]!=F_sha if False else False: pass
    if set(sched)!=set(got): viol[f"{stage}:cell_set"]+=1
    for k in sched:
        cells+=1
        if sorted(sched[k])!=sorted(got.get(k,[])): viol[f"{stage}:perm_multiset"]+=1; details.append((stage,k))
        if len(sched[k])>1:
            bal=np.zeros((4,4),int)
            for p in got[k]:
                for s,c in enumerate(man[k[2]][p]): bal[c,s]+=1
            if bal.min()!=bal.max(): viol[f"{stage}:slot_balance"]+=1
    out[f"{stage}_rows"]=len(rows); out[f"{stage}_frozen_sha"]=sorted({r["frozen_sha8"] for r in rows})
out["cells_checked"]=cells; out["violations"]=dict(viol); out["violation_examples"]=details[:5]
# balance counts per task (main)
rows=[r for f in glob.glob(f"{ROOT}/runs/main/*.csv") for r in csv.DictReader(open(f))]
per=C.defaultdict(set)
for (t,fo,a),_ in [((r["task"],r["focal"],r["array"]),0) for r in rows]: pass
g=C.defaultdict(list)
for r in rows: g[(r["task"],r["focal"],r["array"])].append(int(r["perm_id"]))
reps=C.defaultdict(set)
for (t,fo,a),ps in g.items():
    bal=np.zeros((4,4),int)
    for p in ps:
        for s,c in enumerate(man[a][p]): bal[c,s]+=1
    reps[t].add((bal.min(),bal.max()))
out["main_balance_per_task"]={t:sorted(map(lambda x:[int(x[0]),int(x[1])],v)) for t,v in reps.items()}
# 2. inclusion
src=open(f"{ROOT}/code/analyze.py").read()
out["analyze_reads_runs"]=sorted(set(re.findall(r'"runs", "(\w+)"',src)))
cal=F["calibration_reuse"]
out["calib_sha_match"]=hashlib.sha256(open(cal["source"],"rb").read()).hexdigest()==cal["source_sha256"]
out["analyze_uses_calibration_reuse_source"]='F["calibration_reuse"]["source"]' in src
out["analyze_mentions_anchor"]="anchor" in src
# 3. position effects: position of each model's frame-modal object (from frame counts)
MID={"gpt":"gpt-5.5-2026-04-23","claude":"claude-opus-5"}
cnt={m:{a:np.zeros(4) for a in F["arrays"]} for m in MID}
for r in csv.DictReader(open(cal["source"])):
    for m,mid in MID.items():
        if r["checkpoint_requested"]==mid and r["parse_ok"]=="1": cnt[m][r["array_id"]][int(r["canonical_index"])]+=1
pos={}
for task in ("PLAYPASS","SELFPRED","AUDITOR"):
    for m in MID:
        sub=[r for r in rows if r["task"]==task and r["focal"]==m and r["parse_ok"]=="1"]
        # array-demeaned outcome by slot of focal model's modal object
        byarr=C.defaultdict(list)
        for r in sub:
            modal=int(np.argmax(cnt[m][r["array"]]))
            slot=json.loads(r["display_order"]).index(modal)
            v=1.0 if r.get("decision")=="PLAY" else 0.0 if task=="PLAYPASS" else int(r["match_probability"])/100
            byarr[r["array"]].append((slot,v))
        # array-level: per array mean by slot minus array mean; then test slot effect across arrays (Friedman-like repeated measures via F on demeaned)
        M=np.full((len(byarr),4),np.nan)
        for i,(a,L) in enumerate(byarr.items()):
            am=np.mean([v for _,v in L])
            for s in range(4):
                vs=[v for sl,v in L if sl==s]
                if vs: M[i,s]=np.mean(vs)-am
        Mc=M[~np.isnan(M).any(1)]
        slot_means=np.nanmean(M,0)
        fr=stats.friedmanchisquare(*[Mc[:,s] for s in range(4)]) if len(Mc)>2 and np.ptp(Mc)>0 else None
        # array-clustered permutation: shuffle slot labels within array
        rng=np.random.default_rng(1)
        def stat(Mx): return np.var(np.nanmean(Mx,0))
        obs=stat(Mc); null=[stat(np.array([rng.permutation(row) for row in Mc])) for _ in range(5000)]
        p=(np.sum(np.array(null)>=obs)+1)/(5000+1)
        pos[f"{task}|focal={m}"]=dict(n_arrays=int(len(Mc)),slot_effect_demeaned=[round(float(x),4) for x in slot_means],
            friedman_p=None if fr is None else round(float(fr.pvalue),4), within_array_perm_p=round(float(p),4))
out["position_effects"]=pos
json.dump(out,open(f"{ROOT}/analysis/audit/B_ordering_multiplicity/B_checks.json","w"),indent=1,default=str)
print(json.dumps(out,indent=1,default=str))
