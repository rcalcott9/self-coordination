"""Join the new Claude n=60 arm to the independent GPT-5.5 n=30 estimates.

Both models go through the SAME estimator (targeted_common.cell_metrics /
unbiased_match / boot_draws), recomputed from raw calls - GPT is NOT read from
a2_stimulus_level.csv, so no estimator difference can masquerade as a model
difference. Discovery and confirmation are never pooled: these are two separate
files and each stimulus gets one estimate per model.
"""
import csv, glob, json, math, os, sys
from collections import Counter, defaultdict

NG = "/Users/calypsocalcott/Desktop/Coordination/LLM_Coordination/Name_game_experiment"
BASE = "/Users/calypsocalcott/Desktop/Coordination/Self_Coordination"
ARM = f"{BASE}/study4_relational_staghunt_20260908/claude_arm_20260908"
HP = f"{BASE}/study1_hp_replication_20260905"
sys.path.insert(0, NG)
import targeted_common as tc

FC_CLEAN = 0.80          # project's position-fallback bar
STRONG, VSTRONG = 0.75, 0.90

def wilson(k, n, z=1.96):
    if n == 0: return (0.0, 1.0)
    p, d = k / n, 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))

man = {r["stimulus_id"]: r for r in csv.DictReader(open(f"{HP}/stimulus_manifest.csv"))}
keep = set(json.load(open(f"{ARM}/claude58_retained.json"))["retained"])

def load(path, want_model):
    """One valid trial per run_id; retries deduped; losses counted."""
    by_run = defaultdict(list)
    for r in csv.DictReader(open(path)):
        by_run[r["run_id"]].append(r)
    cells, lost = defaultdict(list), Counter()
    for run_id, rs in by_run.items():
        sid, model = rs[0]["stimulus"], rs[0]["actor_model"]
        if sid not in keep or model != want_model: continue
        good = [r for r in rs if r["superseded_by_retry"] != "True"
                and r["valid_response"] == "True" and r["parsed_choice_identity"]]
        if not good:
            lost[sid] += 1; continue
        r = good[-1]
        cells[sid].append(dict(choice_identity=r["parsed_choice_identity"],
                               response_side=r["parsed_choice_side"],
                               variant=r["variant"], response_raw=r["response_raw"]))
    return cells, lost

def metrics(cells, lost, model):
    out = {}
    for sid, rows in cells.items():
        m = tc.cell_metrics(rows, man[sid])
        ident = [r["choice_identity"] for r in rows]
        ic = Counter(ident); n = len(ident)
        k = ic[m["modal_identity"]]
        runner = sorted(ic.values(), reverse=True)
        m["runnerup_share"] = round((runner[1] / n) if len(runner) > 1 else 0.0, 4)
        m["modal_margin"] = round(m["modal_share"] - m["runnerup_share"], 4)
        lo, hi = wilson(k, n)
        m["modal_wilson_lo"], m["modal_wilson_hi"] = round(lo, 4), round(hi, 4)
        d = tc.boot_draws(ident, seed=f"{tc.BOOT_SEED}|{model}|{sid}")
        clo, chi = tc.pct_ci(d)
        m["match_ci_lo"], m["match_ci_hi"] = round(clo, 4), round(chi, 4)
        m["fallback"] = (m["form_consistency"] < FC_CLEAN
                         if m["form_consistency"] == m["form_consistency"] else "")
        m["near_chance"] = int(lo <= 0.5 <= hi)
        m["n_lost"] = lost.get(sid, 0)
        m["item_counts"] = json.dumps(dict(ic))
        out[sid] = m
    return out

cl_path = sorted(glob.glob(f"{ARM}/data/stageA_CLAUDE58_*.csv"))[-1]
gp_path = f"{HP}/data/stageA_A2_20260905_192538.csv"
CL = metrics(*load(cl_path, "claude"), "claude")
GP = metrics(*load(gp_path, "gpt"), "gpt")
print(f"claude cells {len(CL)}   gpt cells {len(GP)}")

rows = []
for sid in sorted(keep):
    g, c = GP.get(sid), CL.get(sid)
    if not g or not c: print("MISSING", sid, bool(g), bool(c)); continue
    same = g["modal_identity"] == c["modal_identity"]
    # cross-model match from the two independent marginals
    gi = json.loads(g["item_counts"]); ci = json.loads(c["item_counts"])
    gn, cn = sum(gi.values()), sum(ci.values())
    cross = sum(gi.get(k, 0) / gn * ci.get(k, 0) / cn for k in set(gi) | set(ci))
    def cls(th):
        gs, cs = g["modal_share"], c["modal_share"]
        if gs >= th and c["near_chance"]: return "1_GPT_strong_Claude_chance"
        if cs >= th and g["near_chance"]: return "1r_Claude_strong_GPT_chance"
        if gs >= th and cs >= th and not same: return "2_both_strong_diff_modes"
        if gs >= th and cs >= th and same: return "3_both_strong_same_mode"
        if gs >= th: return "1b_GPT_strong_Claude_intermediate"
        if cs >= th: return "1rb_Claude_strong_GPT_intermediate"
        return "0_neither_strong"
    flags = []
    if g["fallback"] is True and c["fallback"] is True: flags.append("both_positional")
    elif g["fallback"] is True or c["fallback"] is True: flags.append("one_positional")
    if g["rationale_mentions_position"] > .5 or c["rationale_mentions_position"] > .5:
        flags.append("rationale_mentions_position")
    if g["modal_share"] >= .99 and c["modal_share"] >= .99 and same:
        flags.append("option_ignored_ceiling")
    if g["n_lost"] or c["n_lost"]: flags.append("trial_loss")
    unusable = bool({"both_positional"} & set(flags))
    rows.append(dict(
        stimulus_id=sid, family=man[sid]["family"], source=man[sid]["source"],
        identity_1=man[sid]["identity_1"], identity_2=man[sid]["identity_2"],
        prompt_frame="same-model coordination game (sha8 3003ae1b)",
        gpt_n=g["n_valid"], gpt_modal=g["modal_identity"], gpt_modal_share=g["modal_share"],
        gpt_margin=g["modal_margin"], gpt_wilson_lo=g["modal_wilson_lo"],
        gpt_wilson_hi=g["modal_wilson_hi"], gpt_self_match=g["match_unbiased"],
        gpt_match_ci_lo=g["match_ci_lo"], gpt_match_ci_hi=g["match_ci_hi"],
        gpt_form_consistency=g["form_consistency"], gpt_p_left=g["p_left"],
        gpt_fallback=g["fallback"], gpt_near_chance=g["near_chance"],
        gpt_pos_lex=g["rationale_mentions_position"], gpt_n_lost=g["n_lost"],
        claude_n=c["n_valid"], claude_modal=c["modal_identity"],
        claude_modal_share=c["modal_share"], claude_margin=c["modal_margin"],
        claude_wilson_lo=c["modal_wilson_lo"], claude_wilson_hi=c["modal_wilson_hi"],
        claude_self_match=c["match_unbiased"], claude_match_ci_lo=c["match_ci_lo"],
        claude_match_ci_hi=c["match_ci_hi"], claude_form_consistency=c["form_consistency"],
        claude_p_left=c["p_left"], claude_fallback=c["fallback"],
        claude_near_chance=c["near_chance"],
        claude_pos_lex=c["rationale_mentions_position"], claude_n_lost=c["n_lost"],
        same_modal_item=int(same), cross_model_match=round(cross, 4),
        class_at_075=cls(STRONG), class_at_090=cls(VSTRONG),
        artifact_flags=";".join(flags), unusable=int(unusable),
        gpt_item_counts=g["item_counts"], claude_item_counts=c["item_counts"]))

p = f"{ARM}/current_model_inventory_58.csv"
with open(p, "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print("wrote", p, len(rows), "rows")
json.dump(rows, open(f"{ARM}/inv58.json", "w"))
