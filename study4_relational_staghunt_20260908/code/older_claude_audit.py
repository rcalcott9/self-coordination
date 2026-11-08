"""Audit: can an older Claude checkpoint supply the OTHER model for a GPT-5.5-focal arm?

Both models re-estimated from RAW through targeted_common, the same path used for every
Study 4 number. Checkpoints are never pooled.
"""
import csv, glob, json, math, os, sys
from collections import Counter, defaultdict

CO = "/Users/calypsocalcott/Desktop/Coordination"
GL = f"{CO}/Self_Coordination/generation_ladder_20260814"
PSC = f"{CO}/Self_Coordination/policy_specific_self_coordination_20260812_1401"
sys.path.insert(0, f"{CO}/LLM_Coordination/Name_game_experiment")
import targeted_common as tc

FC_CLEAN, SHARE, ADV, POS_MIN, WEAK = 0.80, 0.75, 0.25, 0.75, 0.55


def load_chooser(path, want_model_substr=None):
    """One valid trial per run_id from a stageA-style binary file."""
    by = defaultdict(list)
    for r in csv.DictReader(open(path)):
        if r.get("stage") not in (None, "", "A"): continue
        if not r.get("parsed_choice_identity"): continue
        if r.get("superseded_by_retry") == "True": continue
        if r.get("valid_response") == "False": continue
        mid = (r.get("actor_model_id_returned") or r.get("actor_model_id_requested")
               or r.get("api_model") or "")
        if want_model_substr and want_model_substr not in mid: continue
        r["_ckpt"] = mid
        by[r["stimulus"]].append(r)
    return by


def cell(rows, entry):
    ident = [r["parsed_choice_identity"] for r in rows]
    sides = [r["parsed_choice_side"] for r in rows]
    n = len(ident); ic, sc = Counter(ident), Counter(sides)
    modal, k = ic.most_common(1)[0]
    on_l = [r for r in rows if tc.slot_identities(entry, r["variant"])[0] == modal]
    on_r = [r for r in rows if tc.slot_identities(entry, r["variant"])[1] == modal]
    pl = sum(r["parsed_choice_identity"] == modal for r in on_l)/len(on_l) if on_l else float("nan")
    pr = sum(r["parsed_choice_identity"] == modal for r in on_r)/len(on_r) if on_r else float("nan")
    fc = 1 - abs(pl - pr) if on_l and on_r else float("nan")
    return dict(n=n, modal=modal, share=round(k/n, 4),
                identity_match=round(tc.unbiased_match(ic), 4),
                fc=round(fc, 4) if fc == fc else None,
                eff=round(1/sum((v/n)**2 for v in ic.values()), 3),
                pos_share=round(sc.most_common(1)[0][1]/n, 4),
                counts=dict(ic))


def main():
    man = {r["stimulus_id"]: r for r in csv.DictReader(open(f"{PSC}/stimulus_manifest.csv"))}
    # --- GPT-5.5 chooser reference (policy_specific, n=60, prompt 3003ae1b) ---
    gpt = {s: cell(v, man[s]) for s, v in
           load_chooser(f"{PSC}/data/stageA_20260812_150823.csv", "gpt-5.5").items() if s in man}
    # --- older Claude chooser files ---
    SRC = {
        "claude-opus-4-5-20251101": f"{GL}/models/opus45/data/stageA_20260814_222620.csv",
        "claude-opus-4-6":          f"{GL}/models/opus46_expanded/data/stageA_MERGED_20260818_110230.csv",
        "claude-opus-4-7":          f"{GL}/models/opus47/data/stageA_20260815_130823.csv",
        "claude-opus-4-8":          f"{GL}/models/opus48_expanded/data/orig15_stageA_claude.csv",
    }
    overlap, asym, ctrl = [], [], []
    for ck, path in SRC.items():
        if not os.path.exists(path):
            print("MISSING", path); continue
        raw = load_chooser(path)
        cl = {s: cell(v, man[s]) for s, v in raw.items() if s in man}
        ckpts = Counter(r["_ckpt"] for v in raw.values() for r in v)
        assert len(ckpts) == 1, (path, ckpts)          # never pool checkpoints
        ck_actual = next(iter(ckpts))
        assert ck_actual == ck, f"folder says {ck}, rows say {ck_actual}"
        shared = sorted(set(gpt) & set(cl))
        pr = list(csv.DictReader(open(path)))
        sha = Counter(r.get("prompt_sha8", "") for r in pr)
        gsha = Counter(r.get("prompt_sha8", "") for r in
                       csv.DictReader(open(f"{PSC}/data/stageA_20260812_150823.csv")))
        overlap.append(dict(checkpoint=ck, source_file=os.path.relpath(path, CO), arity=2,
                            n_overlapping_arrays=len(shared), overlapping_ids="|".join(shared),
                            claude_n_per_cell=(cl[shared[0]]["n"] if shared else 0),
                            gpt_n_per_cell=(gpt[shared[0]]["n"] if shared else 0),
                            checkpoint_verified_from_rows=ck_actual,
                            claude_prompt_sha8="|".join(sorted(sha)),
                            gpt_prompt_sha8="|".join(sorted(gsha)),
                            prompts_equivalent=int(set(sha) == set(gsha)),
                            raw_available=1, parser="parse_side LEFT/RIGHT",
                            position_scheme="AB/BA balanced n/2 each"))
        for s in shared:
            g, c = gpt[s], cl[s]
            gn, cn = sum(g["counts"].values()), sum(c["counts"].values())
            keys = set(g["counts"]) | set(c["counts"])
            cross = sum(g["counts"].get(k, 0)/gn * c["counts"].get(k, 0)/cn for k in keys)
            adv = round(g["identity_match"] - cross, 4)
            same = g["modal"] == c["modal"]
            sub = ("strong_competing_identity" if c["share"] >= SHARE and (c["fc"] or 0) >= FC_CLEAN
                   else "position_policy" if (c["fc"] or 1) < FC_CLEAN and c["pos_share"] >= POS_MIN
                   else "weak_competing_identity" if c["share"] >= WEAK else "diffuse_identity")
            row = dict(checkpoint=ck, array_id=s, family=man[s]["family"], arity=2,
                       gpt_modal=g["modal"], gpt_share=g["share"], gpt_fc=g["fc"],
                       gpt_identity_match=g["identity_match"], gpt_n=g["n"],
                       claude_modal=c["modal"], claude_share=c["share"], claude_fc=c["fc"],
                       claude_eff=c["eff"], claude_pos_share=c["pos_share"], claude_n=c["n"],
                       same_modal=int(same), cross_model_match=round(cross, 4),
                       gpt_copy_minus_cross=adv, claude_policy_subtype=sub)
            gpt_ok = g["share"] >= SHARE and (g["fc"] or 0) >= FC_CLEAN
            shares_strong = same and c["share"] >= SHARE and (c["fc"] or 0) >= FC_CLEAN
            if gpt_ok and not shares_strong and adv >= ADV:
                asym.append(row)
            if (same and g["share"] >= SHARE and c["share"] >= SHARE
                    and (g["fc"] or 0) >= FC_CLEAN and (c["fc"] or 0) >= FC_CLEAN
                    and g["pos_share"] < POS_MIN and c["pos_share"] < POS_MIN):
                ctrl.append(row)
    for fn, data in (("older_claude_overlap.csv", overlap),
                     ("older_claude_gpt_focal_candidates.csv", asym),
                     ("older_claude_shared_controls.csv", ctrl)):
        p = os.path.join("design", fn)
        if data:
            with open(p, "w", newline="") as fh:
                w = csv.DictWriter(fh, fieldnames=list(data[0].keys())); w.writeheader(); w.writerows(data)
        else:
            open(p, "w").write("(none)\n")
        print("wrote", p, len(data), "rows")
    print()
    for r in overlap:
        print(f"  {r['checkpoint']:26} overlap={r['n_overlapping_arrays']:3} arrays  "
              f"claude n/cell={r['claude_n_per_cell']}  gpt n/cell={r['gpt_n_per_cell']}  "
              f"prompts_equivalent={r['prompts_equivalent']}")
    print()
    print("GPT-focal asymmetric candidates (BINARY) by checkpoint:",
          dict(Counter(r["checkpoint"] for r in asym)))
    print("shared controls (BINARY) by checkpoint:", dict(Counter(r["checkpoint"] for r in ctrl)))
    print("Claude policy subtypes:", dict(Counter(r["claude_policy_subtype"] for r in asym)))


if __name__ == "__main__":
    main()
