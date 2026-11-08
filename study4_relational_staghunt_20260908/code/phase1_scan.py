"""PHASE 1 - scan the already-measured 203-array four-option battery for the target
asymmetry: focal strong + position-invariant, OTHER identity-unpredictable.

Same estimator path as the Study 4 discovery analysis. Nothing is modified.
"""
import csv, glob, json, math, os, sys
from collections import Counter, defaultdict

S4 = "/Users/calypsocalcott/Desktop/Coordination/Self_Coordination/study2_4opt_20260830"
sys.path.insert(0, "/Users/calypsocalcott/Desktop/Coordination/LLM_Coordination/Name_game_experiment")
import targeted_common as tc

CHANCE = 0.25


def eff_support(c):
    n = sum(c.values())
    return round(1.0 / sum((v / n) ** 2 for v in c.values()), 3)


def cell(rows, man):
    n = len(rows)
    ident = [r["item"] for r in rows]
    pos = [r["pos"] for r in rows]
    ic, pc = Counter(ident), Counter(pos)
    modal, k = ic.most_common(1)[0]
    ranked = [v for _, v in ic.most_common()]
    byslot = defaultdict(list)
    for r in rows:
        slot = man[str(r["perm"])].index(modal)
        byslot[slot].append(int(r["item"] == modal))
    hit = {p: sum(v) / len(v) for p, v in byslot.items() if v}
    fc = 1 - (max(hit.values()) - min(hit.values())) if len(hit) == 4 else float("nan")
    return dict(n=n, modal=modal, share=round(k / n, 4),
                margin=round((k - (ranked[1] if len(ranked) > 1 else 0)) / n, 4),
                identity_match=round(tc.unbiased_match(ic), 4),
                fc=round(fc, 4) if fc == fc else None,
                eff_support=eff_support(ic),
                pos_modal_share=round(pc.most_common(1)[0][1] / n, 4),
                counts={str(i): ic.get(i, 0) for i in range(4)})


def main():
    bat = {r["stimulus_id"]: r for r in
           csv.DictReader(open(os.path.join(S4, "stimuli", "battery_manifest.csv")))}
    cells = defaultdict(list)
    for f in glob.glob(os.path.join(S4, "data", "stageA_discovery_*.csv")):
        for r in csv.DictReader(open(f)):
            if r["parse_ok"] != "True" or r["chosen_item"] == "": continue
            cells[(r["model"], r["stimulus_id"])].append(
                dict(item=int(r["chosen_item"]), pos=int(r["chosen_position"]),
                     perm=int(r["perm_id"])))
    mans = {}
    out = []
    for sid in sorted(bat):
        g, c = cells.get(("gpt", sid)), cells.get(("claude", sid))
        if not g or not c: continue
        if sid not in mans:
            mans[sid] = json.load(open(os.path.join(S4, "stimuli", sid, "manifest.json")))
        G, C = cell(g, mans[sid]), cell(c, mans[sid])
        gn, cn = sum(G["counts"].values()), sum(C["counts"].values())
        cross = sum(G["counts"][k] / gn * C["counts"][k] / cn for k in G["counts"])
        out.append(dict(stimulus_id=sid, family=bat[sid]["family"], gpt=G, claude=C,
                        cross=round(cross, 4),
                        gpt_adv=round(G["identity_match"] - cross, 4),
                        claude_adv=round(C["identity_match"] - cross, 4),
                        same_modal=int(G["modal"] == C["modal"])))
    json.dump(out, open(os.path.dirname(os.path.abspath(__file__)) + "/../phase1_4opt_scan.json", "w"))
    print(f"scanned {len(out)} arrays with both models\n")

    def qual(F, O, adv):
        return (F["share"] >= .75 and F["fc"] is not None and F["fc"] >= .667
                and F["identity_match"] > CHANCE + .10 and adv >= .25
                and not (O["share"] >= .75 and O["fc"] is not None and O["fc"] >= .80))
    hits = []
    for r in out:
        for foc, oth, fn, adv in (("gpt", "claude", "gpt", r["gpt_adv"]),
                                  ("claude", "gpt", "claude", r["claude_adv"])):
            F, O = r[foc], r[oth]
            if qual(F, O, adv):
                sub = ("strong_competing" if O["share"] >= .75 else
                       "weak_competing" if O["share"] >= .55 else
                       "position" if O["pos_modal_share"] >= .60 else "diffuse")
                hits.append(dict(sid=r["stimulus_id"], family=r["family"], focal=fn,
                                 focal_share=F["share"], focal_fc=F["fc"],
                                 focal_match=F["identity_match"], other_share=O["share"],
                                 other_fc=O["fc"], other_eff=O["eff_support"],
                                 other_pos=O["pos_modal_share"], cross=r["cross"],
                                 adv=adv, other_subtype=sub, same_modal=r["same_modal"]))
    hits.sort(key=lambda h: -h["adv"])
    print(f"=== EXISTING four-option arrays meeting the Study-4 asymmetry bar: {len(hits)} ===")
    print(f"    (focal share>=.75, focal FC>=.667, focal match>.35, COPY-OTHER>=.25,")
    print(f"     OTHER not also strong+form-consistent)\n")
    byfoc = Counter(h["focal"] for h in hits)
    byfam = Counter(h["family"] for h in hits)
    print(f"  by focal model: {dict(byfoc)}")
    print(f"  distinct families: {len(byfam)}")
    print()
    hdr = f"{'stimulus':22}{'family':18}{'focal':7}{'fshare':>7}{'fFC':>6}{'fmatch':>7}{'oshare':>7}{'oeff':>6}{'opos':>6}{'cross':>7}{'ADV':>7}  subtype"
    print(hdr); print("-" * len(hdr))
    for h in hits:
        print(f"{h['sid']:22}{h['family'][:17]:18}{h['focal']:7}{h['focal_share']:>7.3f}"
              f"{h['focal_fc']:>6.2f}{h['focal_match']:>7.3f}{h['other_share']:>7.3f}"
              f"{h['other_eff']:>6.2f}{h['other_pos']:>6.2f}{h['cross']:>7.3f}{h['adv']:>+7.3f}  {h['other_subtype']}")
    json.dump(hits, open(os.path.dirname(os.path.abspath(__file__)) + "/../phase1_hits.json", "w"))


if __name__ == "__main__":
    from collections import Counter
    main()
