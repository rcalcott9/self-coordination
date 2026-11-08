"""Apply the FROZEN A1 retention rule.

Rule (fixed before any call, DESIGN_v3_ONEFOCAL.md S4):
  retain cells whose screened self-match falls in the TOP 40% or BOTTOM 40% of the
  focal model's screened distribution; drop the middle 20%.

A1 data is used for NOTHING ELSE. It never enters a pair estimate.
Self-match uses the frozen estimator targeted_common.unbiased_match.
"""
import csv, glob, json, os, sys
from collections import Counter
HERE=os.path.dirname(os.path.abspath(__file__)); EXP=os.path.dirname(HERE)
os.environ.setdefault("PSC_EXP_DIR", EXP)
sys.path.insert(0, os.path.expanduser(
  "~/Desktop/Coordination/Self_Coordination/policy_specific_self_coordination_20260812_1401/code"))
import psc_common as P, targeted_common as tc

# Explicit input and output beat glob-and-clobber: the default glob would also have
# been happy to overwrite the 2026-09-05 GPT-5.5 run's a1_screen.csv / a1_retained.json.
raw = os.environ.get("S1_A1_FILE") or \
      sorted(glob.glob(os.path.join(EXP,"data","stageA_A1_*.csv")))[-1]
OUTDIR = os.environ.get("S1_OUT_DIR") or os.path.join(EXP,"data")
os.makedirs(OUTDIR, exist_ok=True)
print(f"  input : {os.path.basename(raw)}")
print(f"  output: {OUTDIR}")
rows=[r for r in csv.DictReader(open(raw))
      if r["included_in_analysis"].lower()=="true" and r["valid_response"].lower()=="true"]
by={}
for r in rows: by.setdefault(r["stimulus"],[]).append(r)
man={m["stimulus_id"]:m for m in P.load_manifest()}

recs=[]
for sid,rs in by.items():
    idents=[r["parsed_choice_identity"] for r in rs if r["parsed_choice_identity"]]
    c=Counter(idents)
    sm=tc.unbiased_match(c)
    n=len(idents)
    i1=man[sid]["identity_1"]
    p1=c.get(i1,0)/n if n else float("nan")
    pl=sum(1 for r in rs if r["variant"]=="AB" and r["parsed_choice_side"]=="LEFT") \
      +sum(1 for r in rs if r["variant"]=="BA" and r["parsed_choice_side"]=="LEFT")
    recs.append(dict(stimulus_id=sid, family=man[sid]["family"], source=man[sid]["source"],
                     n_valid=n, self_match_screen=round(sm,4),
                     p_identity_1=round(p1,4), p_left=round(pl/n,4) if n else "",
                     form_consistency_screen=round(abs(2*p1-1),4)))
recs.sort(key=lambda r:-r["self_match_screen"])
N=len(recs); k=int(round(N*0.40))
top={r["stimulus_id"] for r in recs[:k]}; bot={r["stimulus_id"] for r in recs[-k:]}
for r in recs:
    r["retained"] = r["stimulus_id"] in top or r["stimulus_id"] in bot
    r["band"] = "top40" if r["stimulus_id"] in top else ("bottom40" if r["stimulus_id"] in bot else "middle_dropped")
out=os.path.join(OUTDIR,"a1_screen.csv")
with open(out,"w",newline="") as fh:
    w=csv.DictWriter(fh,fieldnames=list(recs[0].keys())); w.writeheader(); w.writerows(recs)
ret=[r for r in recs if r["retained"]]
print(f"A1 screen: {N} stimuli, {len(rows)} valid trials")
print(f"  self-match screen: min {recs[-1]['self_match_screen']:.3f}  median {recs[N//2]['self_match_screen']:.3f}  max {recs[0]['self_match_screen']:.3f}")
print(f"  RETAINED {len(ret)} (top40 {len(top)} + bottom40 {len(bot)}), dropped {N-len(ret)}")
import collections
print("  retained by source:", dict(collections.Counter(r['source'] for r in ret)))
print("  dropped  by source:", dict(collections.Counter(r['source'] for r in recs if not r['retained'])))
print(f"  top-band self-match range   {min(r['self_match_screen'] for r in recs[:k]):.3f}-{recs[0]['self_match_screen']:.3f}")
print(f"  bottom-band self-match range {recs[-1]['self_match_screen']:.3f}-{max(r['self_match_screen'] for r in recs[-k:]):.3f}")
json.dump({"n_screened":N,"n_retained":len(ret),"retained":[r["stimulus_id"] for r in ret]},
          open(os.path.join(OUTDIR,"a1_retained.json"),"w"), indent=1)
print(f"-> {out}")
