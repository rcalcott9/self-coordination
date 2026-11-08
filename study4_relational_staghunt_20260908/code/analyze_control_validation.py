"""STAGE 1 analysis - pass/fail each control against the FROZEN thresholds, then
apply the predeclared selection rule. Nothing here is re-derived from the data:
the tested identity is the locked prediction, and unconstrained modes are reported
separately, never substituted.
"""
import csv, json, math, os, sys
from collections import Counter, defaultdict

EXP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, "/Users/calypsocalcott/Desktop/Coordination/Self_Coordination/study2_4opt_20260830/code")
import s4_common as S

LOCK = json.load(open(os.path.join(EXP, "pilot", "CONTROL_VALIDATION_LOCKED.json")))
STIM = os.path.join(EXP, "stimuli5")
TH = LOCK["thresholds"]


def cell(rows, manifest, locked_idx):
    n = len(rows)
    ic = Counter(r["item"] for r in rows)
    pc = Counter(r["pos"] for r in rows)
    k = ic.get(locked_idx, 0)
    lo, hi = S.wilson_ci(k, n)
    byslot = defaultdict(list)
    for r in rows:
        byslot[manifest[str(r["perm"])].index(locked_idx)].append(int(r["item"] == locked_idx))
    hit = {p: sum(v) / len(v) for p, v in byslot.items() if v}
    fc = 1 - (max(hit.values()) - min(hit.values())) if len(hit) == 4 else float("nan")
    unc = max(ic, key=lambda i: (ic[i], -i))
    pmod = max(pc, key=lambda p: (pc[p], -p))
    return dict(n=n, locked_share=k / n, locked_wilson_lo=lo, locked_wilson_hi=hi,
                form_consistency=fc, fc_by_slot={str(p): round(v, 3) for p, v in sorted(hit.items())},
                pos_modal=pmod, pos_modal_share=pc[pmod] / n,
                unconstrained_modal=unc, unconstrained_share=ic[unc] / n,
                identity_match=S.unbiased_match(ic),
                eff_identity_support=sum(v * v for v in ic.values()) / (n * n) and
                                     sum((v / n) ** 2 for v in ic.values()),
                item_counts={str(i): ic.get(i, 0) for i in range(4)})


def main(run_dir):
    p = os.path.join(run_dir, "data", "stageA_ctrlval_parsed.csv")
    raw = list(csv.DictReader(open(p)))
    assert len(raw) == 336, len(raw)
    by = defaultdict(list)
    for r in raw:
        assert r["ok"] == "True", r
        assert r["chosen_item"] != "", r
        by[(r["sid"], r["actor"])].append(dict(item=int(r["chosen_item"]),
                                               pos=int(r["chosen_position"]),
                                               perm=int(r["perm_id"])))
    api = Counter(r["api_model"] for r in raw)

    out, results = [], {}
    for c in LOCK["candidates"]:
        sid, li = c["array_id"], c["predicted_modal_index"]
        manifest = json.load(open(os.path.join(STIM, sid, "manifest.json")))
        rec = dict(array_id=sid, mechanism=c["mechanism"], family=c["family"],
                   role=c["role"], predicted=c["predicted_modal_object"],
                   predicted_index=li)
        fails = []
        for m in ("claude", "gpt"):
            rows = by[(sid, m)]
            assert len(rows) == 24, (sid, m, len(rows))
            assert sorted(r["perm"] for r in rows) == list(range(24)), (sid, m)
            d = cell(rows, manifest, li)
            for k, v in d.items():
                rec[f"{m}_{k}"] = v
            if d["unconstrained_modal"] != li:
                fails.append(f"{m}:modal_moved_to_{c['objects'][d['unconstrained_modal']]}")
            if d["locked_share"] < TH["min_modal_share"]:
                fails.append(f"{m}:share_{d['locked_share']:.3f}<{TH['min_modal_share']}")
            if not (d["form_consistency"] >= TH["min_form_consistency"]):
                fails.append(f"{m}:fc_{d['form_consistency']:.3f}<{TH['min_form_consistency']}")
            if d["pos_modal_share"] >= TH["max_position_modal_share"]:
                fails.append(f"{m}:position_driven_{d['pos_modal_share']:.3f}")
        rec["same_modal_both_models"] = (rec["claude_unconstrained_modal"] ==
                                         rec["gpt_unconstrained_modal"] == li)
        rec["fails"] = "; ".join(fails)
        rec["PASS"] = int(not fails)
        results[sid] = rec
        out.append(rec)

    # ---------------------- predeclared selection: mechanism coverage ------------
    ref = LOCK["asymmetric_reference"]
    target = ref["mechanism_counts"]                      # nesting1 noise1 mirror3 contour1 numer2
    want = {"nesting": 1, "noise_texture": 1, "mirror": 2, "line_contour": 1, "numerosity": 1}
    passing = [r for r in out if r["PASS"]]
    chosen, spare, shortfall = [], [], []
    for mech, k in sorted(want.items()):
        pool = sorted([r for r in passing if r["mechanism"] == mech],
                      key=lambda r: (abs(r["claude_locked_share"] - ref["mean_claude_modal_share"]),
                                     r["array_id"]))
        if len(pool) < k:
            shortfall.append(f"{mech}: {len(pool)} passing, wanted {k}")
        chosen += pool[:k]
        spare += pool[k:]
    spare.sort(key=lambda r: (abs(r["claude_locked_share"] - ref["mean_claude_modal_share"]),
                              r["array_id"]))
    while len(chosen) < 6 and spare:
        promoted = spare.pop(0)
        chosen.append(promoted)
        shortfall.append(f"slot filled off-mechanism by {promoted['array_id']} "
                         f"({promoted['mechanism']})")
    fam = Counter(r["family"] for r in chosen)
    fam_violation = [f for f, n in fam.items() if n > 2]

    ok = len(chosen) >= 6 and not fam_violation
    res = dict(run_dir=run_dir, locked_sha=open(os.path.join(
                   EXP, "pilot", "CONTROL_VALIDATION_LOCKED.json.sha256")).read().strip(),
               api_models=dict(api), n_rows=len(raw), transport_fail=0, parse_fail=0,
               n_pass=len(passing), n_fail=len(out) - len(passing),
               selected=[r["array_id"] for r in chosen],
               spare=[r["array_id"] for r in spare],
               failed=[r["array_id"] for r in out if not r["PASS"]],
               shortfall=shortfall, family_violation=fam_violation,
               STAGE1_OK=bool(ok), arrays=out)
    json.dump(res, open(os.path.join(run_dir, "control_validation_results.json"), "w"),
              indent=1, default=str)
    cols = ["array_id", "mechanism", "role", "predicted", "claude_locked_share",
            "claude_form_consistency", "claude_pos_modal_share", "claude_unconstrained_modal",
            "gpt_locked_share", "gpt_form_consistency", "gpt_pos_modal_share",
            "gpt_unconstrained_modal", "same_modal_both_models", "PASS", "fails"]
    with open(os.path.join(run_dir, "control_validation_results.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader(); w.writerows(out)

    print(f"api models: {dict(api)}   rows {len(raw)}  transport_fail 0  parse_fail 0\n")
    hdr = f"{'array':17s} {'mech':13s} {'C share':>8s} {'C fc':>6s} {'C pos':>6s} " \
          f"{'G share':>8s} {'G fc':>6s} {'G pos':>6s}  PASS  notes"
    print(hdr); print("-" * len(hdr))
    for r in out:
        print(f"{r['array_id']:17s} {r['mechanism']:13s} "
              f"{r['claude_locked_share']:8.3f} {r['claude_form_consistency']:6.2f} "
              f"{r['claude_pos_modal_share']:6.2f} {r['gpt_locked_share']:8.3f} "
              f"{r['gpt_form_consistency']:6.2f} {r['gpt_pos_modal_share']:6.2f}  "
              f"{'PASS' if r['PASS'] else 'FAIL'}  {r['fails']}")
    print(f"\npass {len(passing)}/7   selected 6: {[r['array_id'] for r in chosen]}")
    print(f"spare: {[r['array_id'] for r in spare]}   failed: {res['failed']}")
    if shortfall:
        print(f"SHORTFALL: {shortfall}")
    print(f"\nSTAGE 1 {'OK - proceed to Stage 2' if ok else 'FAILED - do not launch Stage 2'}")


if __name__ == "__main__":
    main(sys.argv[1])
