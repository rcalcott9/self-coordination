"""Stage A2 + B analysis and PAIR CONSTRUCTION for Study 1-HP v3.

Selector is Study 1's, unchanged:
  eligible iff |z_true| >= 0.75 and |z_salience| <= 0.35 and |z_auditor| <= 0.35
  z = difference / that model's own battery SD.  No |t| cutoff anywhere.
  Stimuli are never reused (independence). Fallback stimuli stay eligible.

Winner's curse is handled exactly as in Study 1: A2's draws are split
deterministically into SELECT and HOLDOUT halves; SELECT orders high/low, drives
the score and the ranking; HOLDOUT gives an independent estimate of the same gaps.
A1 is never used here - it only ever dropped stimuli.

Writes matched_pairs.csv with approved=False on every row. Nothing is selected.
"""
import csv, glob, json, os, statistics, sys
from collections import Counter, defaultdict
HERE=os.path.dirname(os.path.abspath(__file__)); EXP=os.path.dirname(HERE)
os.environ.setdefault("PSC_EXP_DIR", EXP)
S1=os.path.expanduser("~/Desktop/Coordination/Self_Coordination/policy_specific_self_coordination_20260812_1401/code")
sys.path.insert(0, S1)
import psc_common as P, targeted_common as tc
sys.path.insert(0, os.path.join(S1))
from analyze_stage_ab import assign_halves, _match_on, _sd, diagnose, LARGE_TRUE_Z, SMALL_PUBLIC_Z

FOCAL = os.environ.get("S1_FOCAL", "gpt")   # default unchanged: the 2026-09-05 GPT-5.5 run reproduces exactly

def newest(pat):
    f=sorted(glob.glob(os.path.join(EXP,"data",pat)))
    if not f: sys.exit(f"no file matching {pat}")
    return f[-1]

def valid(path, extra=None):
    out=[]
    for r in csv.DictReader(open(path)):
        if r["included_in_analysis"].lower()!="true": continue
        if r["valid_response"].lower()!="true": continue
        if extra and not extra(r): continue
        out.append(r)
    return out

man={m["stimulus_id"]:m for m in P.load_manifest()}

# ---------- Stage A2: own-copy reliability, select/holdout split --------------
a2=valid(newest("stageA_A2_*.csv"))
assign_halves(a2, lambda r: r["stimulus"])
byS=defaultdict(list)
for r in a2: byS[r["stimulus"]].append(r)
truth={}
for sid,rs in byS.items():
    idents=[r["parsed_choice_identity"] for r in rs]
    c=Counter(idents); n=len(idents)
    p1=c.get(man[sid]["identity_1"],0)/n
    rec=dict(stimulus_id=sid, family=man[sid]["family"], source=man[sid]["source"],
             n_valid=n, self_match=round(tc.unbiased_match(c),4),
             form_consistency=round(abs(2*p1-1),4), p_identity_1=round(p1,4))
    rec["fresh_classification"]=("form_rule_ceiling" if rec["form_consistency"]>=0.80
        else "form_rule_partial" if rec["form_consistency"]>=0.50 else "position_fallback")
    for tag in ("select","holdout"):
        rec.update(_match_on([r for r in rs if r["_half"]==tag], man[sid], FOCAL, sid, tag))
    truth[sid]=rec

# ---------- Stage B ------------------------------------------------------------
def arm_means(pat, field, parse):
    rows=valid(newest(pat))
    assign_halves(rows, lambda r: r["stimulus"])
    out=defaultdict(dict)
    g=defaultdict(list)
    for r in rows:
        v=parse(r)
        if v is None: continue
        g[r["stimulus"]].append((r["_half"], v))
    for sid,vs in g.items():
        allv=[v for _,v in vs]
        out[sid]["all"]=statistics.fmean(allv); out[sid]["n"]=len(allv)
        for tag in ("select","holdout"):
            h=[v for t,v in vs if t==tag]
            out[sid][tag]=statistics.fmean(h) if h else float("nan")
    return out

aud=arm_means("stageB_auditor_*.csv","predicted_match_probability",
              lambda r: float(r["predicted_match_probability"]) if r["predicted_match_probability"] else None)
sal=arm_means("stageB_salience_*.csv","salience_rating",
              lambda r: float(r["salience_rating"]) if r["salience_rating"] else None)

sids=sorted(s for s in truth if s in aud and s in sal)
print(f"stimuli with all three measures: {len(sids)}")

# ---------- battery SDs (SELECT half, focal model's own battery) ---------------
sd_true=_sd([truth[s]["self_match_select"] for s in sids if truth[s]["self_match_select"]!=""])
sd_aud =_sd([aud[s]["select"] for s in sids])
sd_sal =_sd([sal[s]["select"] for s in sids])
print(f"battery SDs (select): true {sd_true:.4f}  auditor {sd_aud:.4f}  salience {sd_sal:.4f}")
print(f"windows: |d_true| >= {LARGE_TRUE_Z*sd_true:.4f}   |d_aud| <= {SMALL_PUBLIC_Z*sd_aud:.4f}"
      f"   |d_sal| <= {SMALL_PUBLIC_Z*sd_sal:.4f}")

# ---------- enumerate every within-model pair ----------------------------------
rows=[]
for i in range(len(sids)):
    for j in range(i+1,len(sids)):
        a,b=sids[i],sids[j]
        hi,lo=(a,b) if truth[a]["self_match_select"]>=truth[b]["self_match_select"] else (b,a)
        d_true=truth[hi]["self_match_select"]-truth[lo]["self_match_select"]
        d_aud =aud[hi]["select"]-aud[lo]["select"]
        d_sal =sal[hi]["select"]-sal[lo]["select"]
        dt_ho =truth[hi]["self_match_holdout"]-truth[lo]["self_match_holdout"]
        z_t,z_a,z_s = d_true/sd_true, d_aud/sd_aud, d_sal/sd_sal
        kind=("clean_disparity" if truth[hi]["fresh_classification"]=="form_rule_ceiling"
              and truth[lo]["fresh_classification"]!="position_fallback"
              else "fallback_disparity" if truth[lo]["fresh_classification"]=="position_fallback"
              else "mixed")
        rows.append(dict(focal_model=FOCAL, pair_id=f"{FOCAL}__{hi}__vs__{lo}",
            stimulus_high=hi, stimulus_low=lo,
            family_high=truth[hi]["family"], family_low=truth[lo]["family"],
            same_family=truth[hi]["family"]==truth[lo]["family"],
            true_high_select=truth[hi]["self_match_select"], true_low_select=truth[lo]["self_match_select"],
            true_high_holdout=truth[hi]["self_match_holdout"], true_low_holdout=truth[lo]["self_match_holdout"],
            auditor_high=round(aud[hi]["select"],4), auditor_low=round(aud[lo]["select"],4),
            salience_high=round(sal[hi]["select"],4), salience_low=round(sal[lo]["select"],4),
            delta_true=round(d_true,4), delta_true_holdout=round(dt_ho,4),
            delta_auditor=round(d_aud,4), delta_salience=round(d_sal,4),
            z_true=round(z_t,4), z_auditor=round(z_a,4), z_salience=round(z_s,4),
            pair_diagnostic=diagnose(z_t,z_s,z_a),
            fc_high=truth[hi]["form_consistency"], fc_low=truth[lo]["form_consistency"],
            class_high=truth[hi]["fresh_classification"], class_low=truth[lo]["fresh_classification"],
            pair_kind=kind,
            eligible=bool(abs(z_t)>=LARGE_TRUE_Z and abs(z_s)<=SMALL_PUBLIC_Z and abs(z_a)<=SMALL_PUBLIC_Z),
            matching_score_public=round(z_t-abs(z_s)-abs(z_a),4), approved=False))

elig=[r for r in rows if r["eligible"]]
elig.sort(key=lambda r:-r["matching_score_public"])
used=set(); indep=[]
for r in elig:
    if r["stimulus_high"] in used or r["stimulus_low"] in used: continue
    used|={r["stimulus_high"],r["stimulus_low"]}; indep.append(r)
for r in rows: r["independent_selected"]=r["pair_id"] in {x["pair_id"] for x in indep}

out=os.path.join(EXP,"matched_pairs.csv")
with open(out,"w",newline="") as fh:
    w=csv.DictWriter(fh,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
tout=os.path.join(EXP,"data","a2_stimulus_level.csv")
with open(tout,"w",newline="") as fh:
    ks=sorted({k for v in truth.values() for k in v})
    w=csv.DictWriter(fh,fieldnames=ks); w.writeheader()
    for s in sids: w.writerow({k:truth[s].get(k,"") for k in ks})
print(f"\ncandidate pairs {len(rows)}   eligible {len(elig)}   INDEPENDENT {len(indep)}")
import collections
print("  independent by pair_kind:", dict(collections.Counter(r['pair_kind'] for r in indep)))
print("  independent by diagnostic:", dict(collections.Counter(r['pair_diagnostic'] for r in indep)))
print("  same-family pairs among independent:", sum(r['same_family'] for r in indep))
print(f"-> {out}")
