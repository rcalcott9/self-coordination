"""Unified current-model candidate inventory with SEPARATE form- and position-policy metrics.

Two batteries, both GPT-5.5 + Claude Opus 5, both prompt sha8 3003ae1b, both recomputed
from raw calls through targeted_common:
  hp58   study1_hp 58-stimulus pool   GPT n=30 (A2)   Claude n=60 (this run)
  psc15  policy_specific 15-stimulus  GPT n=60        Claude n=60

Never pooled across batteries; `battery` is a column.
"""
import csv, glob, json, math, os, sys
from collections import Counter, defaultdict

NG = "/Users/calypsocalcott/Desktop/Coordination/LLM_Coordination/Name_game_experiment"
B = "/Users/calypsocalcott/Desktop/Coordination/Self_Coordination"
ARM = f"{B}/study4_relational_staghunt_20260908/claude_arm_20260908"
HP, PSC = f"{B}/study1_hp_replication_20260905", f"{B}/policy_specific_self_coordination_20260812_1401"
sys.path.insert(0, NG)
import targeted_common as tc

FC_CLEAN = 0.80
BIN_FLOOR = 0.50          # binary identity-match floor under independent layouts
PROJ_4OPT_FLOOR = 0.25    # projected 4-option floor - HYPOTHESIS, needs measurement

def wilson(k, n, z=1.96):
    if n == 0: return (0.0, 1.0)
    p, d = k / n, 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))

def load(paths, man, keep=None):
    by_run = defaultdict(list)
    for p in paths:
        for r in csv.DictReader(open(p)):
            by_run[(p, r["run_id"])].append(r)
    cells, lost = defaultdict(list), Counter()
    for (_, rid), rs in by_run.items():
        sid, model = rs[0]["stimulus"], rs[0]["actor_model"]
        if sid not in man or (keep and sid not in keep): continue
        good = [r for r in rs if r["superseded_by_retry"] != "True"
                and r["valid_response"] == "True" and r["parsed_choice_identity"]]
        if not good: lost[(model, sid)] += 1; continue
        r = good[-1]
        cells[(model, sid)].append(dict(choice_identity=r["parsed_choice_identity"],
            response_side=r["parsed_choice_side"], variant=r["variant"],
            response_raw=r["response_raw"]))
    return cells, lost

def cell(rows, entry, model, sid, lost):
    m = tc.cell_metrics(rows, entry)
    ident = [r["choice_identity"] for r in rows]
    sides = [r["response_side"] for r in rows]
    n = len(ident)
    ic, sc = Counter(ident), Counter(sides)
    # --- form (canonical-object) policy ---
    k = ic[m["modal_identity"]]
    ilo, ihi = wilson(k, n)
    d = tc.boot_draws(ident, seed=f"{tc.BOOT_SEED}|{model}|{sid}")
    clo, chi = tc.pct_ci(d)
    # --- position (screen-coordinate) policy ---
    pmod, pk = sc.most_common(1)[0]
    plo, phi = wilson(pk, n)
    pos_match = sum(v * (v - 1) for v in sc.values()) / (n * (n - 1))
    runner = sorted(ic.values(), reverse=True)
    return dict(
        n=n, n_lost=lost.get((model, sid), 0),
        obj_modal=m["modal_identity"], obj_modal_share=m["modal_share"],
        obj_modal_wilson_lo=round(ilo, 4), obj_modal_wilson_hi=round(ihi, 4),
        obj_margin=round(m["modal_share"] - ((runner[1] / n) if len(runner) > 1 else 0.0), 4),
        identity_match=m["match_unbiased"],
        identity_match_ci_lo=round(clo, 4), identity_match_ci_hi=round(chi, 4),
        pos_modal=pmod, pos_modal_share=round(pk / n, 4),
        pos_modal_wilson_lo=round(plo, 4), pos_modal_wilson_hi=round(phi, 4),
        position_match=round(pos_match, 4),
        form_consistency=m["form_consistency"], p_left=m["p_left"],
        rationale_mentions_position=m["rationale_mentions_position"],
        n_AB=m["n_AB"], n_BA=m["n_BA"],
        form_driven=int(m["form_consistency"] >= FC_CLEAN),
        position_driven=int(m["form_consistency"] < FC_CLEAN),
        item_counts=json.dumps(dict(ic)), side_counts=json.dumps(dict(sc)))

BATT = {}
hp_man = {r["stimulus_id"]: r for r in csv.DictReader(open(f"{HP}/stimulus_manifest.csv"))}
keep = set(json.load(open(f"{ARM}/claude58_retained.json"))["retained"])
c1, l1 = load([sorted(glob.glob(f"{ARM}/data/stageA_CLAUDE58_*.csv"))[-1],
               f"{HP}/data/stageA_A2_20260905_192538.csv"], hp_man, keep)
BATT["hp58"] = (c1, l1, hp_man)
psc_man = {r["stimulus_id"]: r for r in csv.DictReader(open(f"{PSC}/stimulus_manifest.csv"))}
c2, l2 = load([f"{PSC}/data/stageA_20260812_150823.csv"], psc_man)
BATT["psc15"] = (c2, l2, psc_man)

rows = []
for batt, (cells, lost, man) in BATT.items():
    sids = sorted({s for (_, s) in cells})
    for sid in sids:
        M = {}
        for model in ("gpt", "claude"):
            rs = cells.get((model, sid))
            if not rs: break
            M[model] = cell(rs, man[sid], model, sid, lost)
        if len(M) != 2: continue
        g, c = M["gpt"], M["claude"]
        gi, ci_ = json.loads(g["item_counts"]), json.loads(c["item_counts"])
        gn, cn = sum(gi.values()), sum(ci_.values())
        cross = sum(gi.get(k, 0) / gn * ci_.get(k, 0) / cn for k in set(gi) | set(ci_))
        rec = dict(battery=batt, stimulus_id=sid, family=man[sid]["family"],
                   source=man[sid]["source"], identity_1=man[sid]["identity_1"],
                   identity_2=man[sid]["identity_2"], n_options=2,
                   prompt_frame="same-model coordination game (sha8 3003ae1b)",
                   cross_model_identity_match=round(cross, 4),
                   same_obj_modal=int(g["obj_modal"] == c["obj_modal"]),
                   binary_identity_floor=BIN_FLOOR,
                   projected_4opt_identity_floor=PROJ_4OPT_FLOOR,
                   projected_floor_status="HYPOTHESIS - requires 4-option premeasurement")
        for tag, d in (("gpt", g), ("claude", c)):
            for k, v in d.items(): rec[f"{tag}_{k}"] = v
        rec["gpt_selfmatch_minus_cross"] = round(g["identity_match"] - cross, 4)
        rec["claude_selfmatch_minus_cross"] = round(c["identity_match"] - cross, 4)
        rows.append(rec)

json.dump(rows, open(f"{ARM}/tiers_raw.json", "w"))
print(f"built {len(rows)} stimulus rows across {len({r['battery'] for r in rows})} batteries")
for b in BATT: print(f"   {b}: {sum(1 for r in rows if r['battery']==b)}")
