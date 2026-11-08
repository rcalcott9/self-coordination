"""Study 4 CUE-CONFLICT battery5 discovery analysis - 42 arrays x 2 models x 24 perms.

Same one-path structure as analyze_discovery4.py, widened for battery5:

  * battery manifest is stimuli5/battery5_manifest.csv, keyed on `array_id`
    (not `stimulus_id`), and carries `mechanism` and `variant` as their own
    columns - kept SEPARATE from `family` everywhere downstream.
  * the discovery run is SHARDED, so every data/stageA_discovery5*.csv is read
    and concatenated before any cell is formed.
  * per model x array the cell adds effective identity support 1/sum(p_i^2) and
    the full conditional choice distribution by display slot, on top of the
    battery4 identity / position / form-consistency metrics.
  * per array each focal direction carries an explicit classification of what
    the OTHER model is doing: diffuse_identity / position /
    weak_competing_identity / strong_competing_identity.

Form-policy and position-policy metrics stay separate; coordination is scored on
canonical object identity only. Four-option chance floors: identity modal share
.25, dyadic identity match .25.
"""
import csv, glob, json, math, os, sys
from collections import Counter, defaultdict

EXP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STIM = os.path.join(EXP, "stimuli5")
sys.path.insert(0, "/Users/calypsocalcott/Desktop/Coordination/LLM_Coordination/Name_game_experiment")
import targeted_common as tc          # unbiased_match, boot_draws, pct_ci, BOOT_SEED

CHANCE = 0.25
FC_CLEAN, POS_MIN, LIVE_MIN = 0.80, 0.75, 0.05
N_PER_CELL, N_ARRAYS, MODELS = 24, 42, ("gpt", "claude")

# OTHER-policy subtype thresholds (used by lock_candidates5.py too)
OTH_STRONG, OTH_WEAK = 0.75, 0.55
EXPECTED_API = {"gpt": "gpt-5.5", "claude": "claude-opus-5"}


def wilson(k, n, z=1.96):
    if n == 0: return (0.0, 1.0)
    p, d = k / n, 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def chi2_uniform(counts, k=4):
    n = sum(counts.values()); e = n / k
    return sum((counts.get(i, 0) - e) ** 2 / e for i in range(k)) if e else float("nan")


def modal_of(counts):
    """Deterministic modal key: highest count, lowest key on a tie.

    battery4 used Counter.most_common, whose tie order follows insertion. With 42
    arrays and locked predictions a tie must not depend on row order.
    """
    return min(counts, key=lambda k: (-counts[k], k))


def eff_support(counts):
    """Effective identity support = 1/sum(p_i^2): 1 = deterministic, 4 = uniform."""
    n = sum(counts.values())
    if not n: return float("nan")
    s = sum((v / n) ** 2 for v in counts.values())
    return 1.0 / s if s else float("nan")


def cell(rows, manifest, model, aid):
    """rows: dicts with item (int 0-3), pos (chosen screen position 1-4), perm_id."""
    n = len(rows)
    ident = [r["item"] for r in rows]
    pos = [r["pos"] for r in rows]
    ic, pc = Counter(ident), Counter(pos)

    modal = modal_of(ic); k = ic[modal]
    ranked = sorted(ic.values(), reverse=True)
    lo, hi = wilson(k, n)
    d = tc.boot_draws(ident, seed=f"{tc.BOOT_SEED}|4opt|b5|{model}|{aid}")
    clo, chi = tc.pct_ci(d)

    pmod = modal_of(pc); pk = pc[pmod]
    plo, phi = wilson(pk, n)

    # form consistency generalised to 4 positions:
    # P(choose modal object | modal object displayed at slot p), spread across p.
    # The full conditional distribution over ALL four objects is kept alongside it.
    byslot = defaultdict(list)
    condslot = defaultdict(Counter)
    for r in rows:
        slot = manifest[str(r["perm_id"])].index(modal)      # where the modal object sat
        byslot[slot].append(int(r["item"] == modal))
        condslot[slot][r["item"]] += 1
    hit = {p: sum(v) / len(v) for p, v in byslot.items() if v}
    fc = 1 - (max(hit.values()) - min(hit.values())) if len(hit) == 4 else float("nan")
    cond = {str(p): {str(i): condslot[p].get(i, 0) for i in range(4)}
            for p in sorted(condslot)}
    condp = {p: {i: (c / sum(d.values()) if sum(d.values()) else 0.0)
                 for i, c in d.items()} for p, d in cond.items()}

    live = sum(1 for v in ic.values() if v / n >= LIVE_MIN)
    return dict(
        n=n, obj_modal=modal, obj_modal_share=round(k / n, 4),
        obj_margin=round((k - (ranked[1] if len(ranked) > 1 else 0)) / n, 4),
        obj_wilson_lo=round(lo, 4), obj_wilson_hi=round(hi, 4),
        identity_match=round(tc.unbiased_match(ic), 4),
        identity_match_ci_lo=round(clo, 4), identity_match_ci_hi=round(chi, 4),
        eff_identity_support=round(eff_support(ic), 4),
        pos_modal=pmod, pos_modal_share=round(pk / n, 4),
        pos_wilson_lo=round(plo, 4), pos_wilson_hi=round(phi, 4),
        position_match=round(tc.unbiased_match(pc), 4),
        position_chi2=round(chi2_uniform(pc), 3),
        form_consistency=round(fc, 4) if fc == fc else "",
        form_consistency_by_slot=json.dumps({str(p): round(v, 3) for p, v in sorted(hit.items())}),
        cond_choice_by_slot=json.dumps(cond),
        cond_choice_by_slot_p=json.dumps({p: {i: round(v, 3) for i, v in d.items()}
                                          for p, d in condp.items()}),
        n_live_objects=live,
        entropy_bits=round(-sum((v / n) * math.log2(v / n) for v in ic.values()), 4),
        item_counts=json.dumps({str(i): ic.get(i, 0) for i in range(4)}),
        item_shares=json.dumps({str(i): round(ic.get(i, 0) / n, 4) for i in range(4)}),
        pos_counts=json.dumps({str(i): pc.get(i, 0) for i in range(1, 5)}),
        policy_type=("form" if fc == fc and fc >= FC_CLEAN
                     else "position" if pk / n >= POS_MIN else "mixed"),
    )


def other_policy(D):
    """What the OTHER model is doing, as exactly one subtype.

    Order matters: a strong form-driven competing convention outranks a position
    policy, which outranks a merely leaning identity, which outranks diffuse.
    """
    fc = float(D["form_consistency"]) if D["form_consistency"] != "" else float("nan")
    if D["obj_modal_share"] >= OTH_STRONG and fc >= FC_CLEAN:
        return "strong_competing_identity"
    if D["pos_modal_share"] >= POS_MIN:
        return "position"
    if D["obj_modal_share"] >= OTH_WEAK:
        return "weak_competing_identity"
    return "diffuse_identity"


def read_raw(run_dir):
    """Every shard of the discovery run, concatenated in filename order."""
    paths = sorted(glob.glob(os.path.join(run_dir, "data", "stageA_discovery5*.csv")))
    if not paths:
        raise SystemExit(f"no stageA_discovery5*.csv under {run_dir}/data")
    raw = []
    for p in paths:
        raw.extend(csv.DictReader(open(p)))
    return paths, raw


def main(run_dir):
    battery = {r["array_id"]: r for r in
               csv.DictReader(open(os.path.join(STIM, "battery5_manifest.csv")))}
    if len(battery) != N_ARRAYS:
        print(f"WARNING: battery5_manifest.csv has {len(battery)} arrays, expected {N_ARRAYS}")
    paths, raw = read_raw(run_dir)

    cells = defaultdict(list)
    integ = dict(rows=len(raw), transport_ok=0, parse_ok=0, bad_model=[], dupes=[],
                 missing=[], shards=[os.path.basename(p) for p in paths],
                 n_arrays=len(battery), expected_rows=len(battery) * 2 * N_PER_CELL)
    seen, shas = set(), Counter()
    for r in raw:
        aid = r.get("array_id") or r.get("stimulus_id")
        integ["transport_ok"] += r["ok"] == "True"
        integ["parse_ok"] += r["parse_ok"] == "True"
        shas[r.get("prompt_sha8", "")] += 1
        key = (aid, r["model"], r["perm_id"])
        if key in seen: integ["dupes"].append(key)
        seen.add(key)
        if EXPECTED_API.get(r["model"], "\x00") not in (r["api_model"] or ""):
            integ["bad_model"].append((key, r["api_model"]))
        if r["parse_ok"] == "True":
            cells[(r["model"], aid)].append(
                dict(item=int(r["chosen_item"]), pos=int(r["chosen_position"]),
                     perm_id=int(r["perm_id"])))
    for aid in battery:
        for m in MODELS:
            got = len(cells.get((m, aid), []))
            if got != N_PER_CELL: integ["missing"].append((m, aid, got))
    integ["prompt_sha8"] = sorted(shas)
    prompt_sha8 = shas.most_common(1)[0][0] if shas else ""

    M = {}
    for (m, aid), rs in cells.items():
        if aid not in battery or not rs: continue
        man = json.load(open(os.path.join(STIM, aid, "manifest.json")))
        M[(m, aid)] = cell(rs, man, m, aid)

    out = []
    for aid, b in battery.items():
        if any((m, aid) not in M for m in MODELS):
            continue                                    # nothing to score for this array
        g, c = M[("gpt", aid)], M[("claude", aid)]
        gi, ci = json.loads(g["item_counts"]), json.loads(c["item_counts"])
        gn, cn = sum(gi.values()), sum(ci.values())
        cross = sum(gi[k] / gn * ci[k] / cn for k in gi)
        names = b["objects"].split("|")
        rec = dict(array_id=aid, family=b["family"], mechanism=b["mechanism"],
                   variant=b["variant"], objects=b["objects"], n_options=4,
                   chance_identity_match=CHANCE, prompt_sha8=prompt_sha8,
                   note=b.get("note", ""),
                   gpt_modal_name=names[g["obj_modal"]], claude_modal_name=names[c["obj_modal"]],
                   same_obj_modal=int(g["obj_modal"] == c["obj_modal"]),
                   cross_model_identity_match=round(cross, 4),
                   copy_match_gpt=g["identity_match"], copy_match_claude=c["identity_match"],
                   gpt_copy_minus_other=round(g["identity_match"] - cross, 4),
                   claude_copy_minus_other=round(c["identity_match"] - cross, 4),
                   other_policy_for_focal_gpt=other_policy(c),
                   other_policy_for_focal_claude=other_policy(g))
        for tag, D in (("gpt", g), ("claude", c)):
            for k, v in D.items(): rec[f"{tag}_{k}"] = v
        out.append(rec)

    if not out:
        raise SystemExit("no array had both model cells; nothing written")

    p = os.path.join(run_dir, "discovery5_inventory.csv")
    with open(p, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
    json.dump(out, open(os.path.join(run_dir, "discovery5_inventory.json"), "w"))
    json.dump(integ, open(os.path.join(run_dir, "trial_integrity.json"), "w"), indent=1)
    print(f"read {len(paths)} shard(s), {len(raw)} rows "
          f"(expected {integ['expected_rows']} = {len(battery)} x 2 x {N_PER_CELL})")
    print("wrote", p, len(out), "arrays")
    print("integrity:", {k: (len(v) if isinstance(v, list) else v) for k, v in integ.items()})
    return out


if __name__ == "__main__":
    main(sys.argv[1])
