"""Gate 2A scoring. FT reports are largely non-existent, so quantity A is reported as
NOT ESTIMABLE rather than computed on a biased remnant."""
import json, sys
from collections import Counter
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
from gate2a_elicit import parse_strict, parse_lenient
from gate1_score import fit_context, normalise, z, boot_ci
ROOT=Path(__file__).resolve().parent.parent; F=ROOT/'data'/'gate2a'; G=ROOT/'data'/'gate1'

trials={(r['scenario'],r['idx']):r for r in json.loads((F/'gate2a_report_trials.json').read_text())}
true_w=json.loads((G/'gate1_true_weights.json').read_text())

# learned behavioural weights, refit from Gate 1 held-out choices (same estimator)
heldout=json.loads((G/'gate1_heldout_5000.json').read_text())
by_key={(r['scenario'],r['idx']):r for r in heldout}
ev=json.loads((G/'gate1_eval_ft.json').read_text())
byc={}
for r in ev:
    if r.get('choice') not in ('A','B'): continue
    s=by_key[(r['scenario'],r['idx'])]; rng=[s[f'range_{i}'] for i in range(1,6)]
    d=byc.setdefault(r['scenario'],{'X':[],'y':[]})
    d['X'].append([(s[f'A_attribute_{i}']-s[f'B_attribute_{i}'])/rng[i-1] for i in range(1,6)])
    d['y'].append(1 if r['choice']=='A' else 0)
learned={}
for s,d in byc.items():
    c,_=fit_context(np.array(d['X']),np.array(d['y']))
    if c is not None:
        n=normalise(c)
        if n is not None: learned[s]=n

def summarize(path,label):
    rep=json.loads(Path(path).read_text())
    strict={}; lenient={}; reasons=Counter(); rescued=0
    for r in rep:
        names=trials[(r['scenario'],r['idx'])]['attr_names']
        v,st=parse_strict(r.get('reply'),names); reasons[st]+=1
        if v is not None: strict.setdefault(r['scenario'],[]).append(v)
        lv=parse_lenient(r.get('reply'),names)
        if lv is not None:
            lenient.setdefault(r['scenario'],[]).append(lv)
            if v is None: rescued+=1
    print(f"\n=== {label} ===")
    print(f"  replies={len(rep)}  strict OK={reasons['ok']} ({reasons['ok']/len(rep):.1%})"
          f"  contexts with >=1 strict report={len(strict)}/100")
    print(f"  lenient rescued (beyond strict): {rescued}   contexts lenient={len(lenient)}/100")
    print(f"  parse outcomes: {dict(reasons.most_common(6))}")
    return strict,lenient,reasons

def correlate(reports,target,name):
    ctx=sorted(set(reports)&set(target))
    if len(ctx)<3: print(f"  {name}: NOT ESTIMABLE (only {len(ctx)} contexts)"); return None
    R=np.array([np.mean(reports[s],axis=0) for s in ctx]).ravel()
    T=np.concatenate([np.asarray(target[s],float) for s in ctx])
    cl=[s for s in ctx for _ in range(5)]
    r=float(np.corrcoef(z(R),z(T))[0,1]); lo,hi=boot_ci(R,T,cl)
    within=[float(np.corrcoef(np.mean(reports[s],axis=0),np.asarray(target[s],float))[0,1])
            for s in ctx if np.std(np.mean(reports[s],axis=0))>0 and np.std(target[s])>0]
    slope=float(np.polyfit(z(R),z(T),1)[0])
    print(f"  {name}: r={r:+.4f} [{lo:+.4f},{hi:+.4f}] contexts={len(ctx)} "
          f"within-ctx mean={np.mean(within):+.3f} neg={sum(1 for w in within if w<0)}/{len(within)}")
    return {"r":r,"ci95":[lo,hi],"n_contexts":len(ctx),
            "within_context_mean":float(np.mean(within)),
            "within_context_negative":int(sum(1 for w in within if w<0)),
            "standardised_slope":slope}

out={}
fs,fl,fr=summarize(F/'gate2a_reports_ft.json','FINE-TUNED (Gate 1 model)')
bs,bl,br=summarize(F/'gate2a_reports_base.json','BASE gpt-4.1-mini (control)')
print("\n--- correlations ---")
out['ft_report_vs_learned']=correlate(fs,learned,'FT report vs LEARNED behavioural (A)')
out['ft_report_vs_true']=correlate(fs,true_w and {k:[v[f'attr{i+1}'] for i in range(5)] for k,v in true_w.items()},'FT report vs TRUE (B)')
tw={k:[v[f'attr{i+1}'] for i in range(5)] for k,v in true_w.items()}
out['base_report_vs_true']=correlate(bs,tw,'BASE report vs TRUE')
out['base_report_vs_ft_learned']=correlate(bs,learned,'BASE report vs FT LEARNED')
out['parse']={'ft_strict_ok':fr['ok'],'ft_total':sum(fr.values()),'ft_contexts':len(fs),
              'base_strict_ok':br['ok'],'base_total':sum(br.values()),'base_contexts':len(bs)}
(F/'gate2a_scores.json').write_text(json.dumps(out,indent=2,default=str))
print(f"\nscores -> {F/'gate2a_scores.json'}")
