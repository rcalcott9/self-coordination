"""Study 4 four-object discovery analysis.

Both models re-estimated through ONE path. Form-policy and position-policy metrics are
computed separately; coordination is scored on canonical object identity only.

Four-option chance floors: identity modal share .25, dyadic identity match .25.
"""
import csv, glob, json, math, os, sys
from collections import Counter, defaultdict

EXP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, "/Users/calypsocalcott/Desktop/Coordination/LLM_Coordination/Name_game_experiment")
import targeted_common as tc          # unbiased_match, boot_draws, pct_ci, BOOT_SEED

CHANCE = 0.25
FC_CLEAN, POS_MIN, GAP_MIN, LIVE_MIN = 0.80, 0.75, 0.20, 0.05


def wilson(k, n, z=1.96):
    if n == 0: return (0.0, 1.0)
    p, d = k / n, 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def chi2_uniform(counts, k=4):
    n = sum(counts.values()); e = n / k
    return sum((counts.get(i, 0) - e) ** 2 / e for i in range(k)) if e else float("nan")


def cell(rows, manifest, model, sid):
    """rows: dicts with chosen_item (int), chosen_position (1-4), perm_id."""
    n = len(rows)
    ident = [r["item"] for r in rows]
    pos = [r["pos"] for r in rows]
    ic, pc = Counter(ident), Counter(pos)

    modal, k = ic.most_common(1)[0]
    ranked = [v for _, v in ic.most_common()]
    lo, hi = wilson(k, n)
    d = tc.boot_draws(ident, seed=f"{tc.BOOT_SEED}|4opt|{model}|{sid}")
    clo, chi = tc.pct_ci(d)

    pmod, pk = pc.most_common(1)[0]
    plo, phi = wilson(pk, n)

    # form consistency generalised to 4 positions:
    # P(choose modal object | modal object displayed at position p), spread across p
    byslot = defaultdict(list)
    for r in rows:
        slot = manifest[str(r["perm_id"])].index(modal)      # where the modal object sat
        byslot[slot].append(int(r["item"] == modal))
    hit = {p: sum(v) / len(v) for p, v in byslot.items() if v}
    fc = 1 - (max(hit.values()) - min(hit.values())) if len(hit) == 4 else float("nan")

    live = sum(1 for v in ic.values() if v / n >= LIVE_MIN)
    return dict(
        n=n, obj_modal=modal, obj_modal_share=round(k / n, 4),
        obj_margin=round((k - (ranked[1] if len(ranked) > 1 else 0)) / n, 4),
        obj_wilson_lo=round(lo, 4), obj_wilson_hi=round(hi, 4),
        identity_match=round(tc.unbiased_match(ic), 4),
        identity_match_ci_lo=round(clo, 4), identity_match_ci_hi=round(chi, 4),
        pos_modal=pmod, pos_modal_share=round(pk / n, 4),
        pos_wilson_lo=round(plo, 4), pos_wilson_hi=round(phi, 4),
        position_match=round(tc.unbiased_match(pc), 4),
        position_chi2=round(chi2_uniform(pc), 3),
        form_consistency=round(fc, 4) if fc == fc else "",
        form_consistency_by_slot=json.dumps({str(p): round(v, 3) for p, v in sorted(hit.items())}),
        n_live_objects=live,
        entropy_bits=round(-sum((v / n) * math.log2(v / n) for v in ic.values()), 4),
        item_counts=json.dumps({str(i): ic.get(i, 0) for i in range(4)}),
        pos_counts=json.dumps({str(i): pc.get(i, 0) for i in range(1, 5)}),
        policy_type=("form" if fc == fc and fc >= FC_CLEAN
                     else "position" if pk / n >= POS_MIN else "mixed"),
    )


def main(run_dir):
    battery = {r["stimulus_id"]: r for r in
               csv.DictReader(open(os.path.join(EXP, "stimuli4", "battery4_manifest.csv")))}
    path = sorted(glob.glob(os.path.join(run_dir, "data", "stageA_discovery4*.csv")))[-1]
    raw = list(csv.DictReader(open(path)))

    cells = defaultdict(list)
    integ = dict(rows=len(raw), transport_ok=0, parse_ok=0, bad_model=[], dupes=[], missing=[])
    seen = set()
    for r in raw:
        integ["transport_ok"] += r["ok"] == "True"
        integ["parse_ok"] += r["parse_ok"] == "True"
        key = (r["stimulus_id"], r["model"], r["perm_id"])
        if key in seen: integ["dupes"].append(key)
        seen.add(key)
        exp = "gpt-5.5" if r["model"] == "gpt" else "claude-opus-5"
        if exp not in (r["api_model"] or ""): integ["bad_model"].append((key, r["api_model"]))
        if r["parse_ok"] == "True":
            cells[(r["model"], r["stimulus_id"])].append(
                dict(item=int(r["chosen_item"]), pos=int(r["chosen_position"]),
                     perm_id=int(r["perm_id"])))
    for sid in battery:
        for m in ("gpt", "claude"):
            got = len(cells[(m, sid)])
            if got != 24: integ["missing"].append((m, sid, got))

    M = {}
    for (m, sid), rs in cells.items():
        man = json.load(open(os.path.join(EXP, "stimuli4", sid, "manifest.json")))
        M[(m, sid)] = cell(rs, man, m, sid)

    out = []
    for sid, b in battery.items():
        g, c = M[("gpt", sid)], M[("claude", sid)]
        gi, ci = json.loads(g["item_counts"]), json.loads(c["item_counts"])
        gn, cn = sum(gi.values()), sum(ci.values())
        cross = sum(gi[k] / gn * ci[k] / cn for k in gi)
        names = b["objects"].split("|")
        rec = dict(stimulus_id=sid, family=b["family"], track_hypothesis=b["track"],
                   mechanism=b["mechanism"], source_binary=b["source_binary"],
                   objects=b["objects"], n_options=4, chance_identity_match=CHANCE,
                   prompt_sha8="d40ea45d",
                   gpt_modal_name=names[g["obj_modal"]], claude_modal_name=names[c["obj_modal"]],
                   same_obj_modal=int(g["obj_modal"] == c["obj_modal"]),
                   cross_model_identity_match=round(cross, 4),
                   copy_match_gpt=g["identity_match"], copy_match_claude=c["identity_match"],
                   gpt_copy_minus_other=round(g["identity_match"] - cross, 4),
                   claude_copy_minus_other=round(c["identity_match"] - cross, 4))
        for tag, D in (("gpt", g), ("claude", c)):
            for k, v in D.items(): rec[f"{tag}_{k}"] = v
        out.append(rec)

    p = os.path.join(run_dir, "discovery4_inventory.csv")
    with open(p, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
    json.dump(out, open(os.path.join(run_dir, "discovery4_inventory.json"), "w"))
    json.dump(integ, open(os.path.join(run_dir, "trial_integrity.json"), "w"), indent=1)
    print("wrote", p, len(out), "arrays")
    print("integrity:", {k: (v if not isinstance(v, list) else len(v)) for k, v in integ.items()})
    return out


if __name__ == "__main__":
    main(sys.argv[1])
