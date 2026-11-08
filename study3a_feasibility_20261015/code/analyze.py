"""Analysis for the Study 3A feasibility pilot. Descriptive; pipeline and measurement pilot, not a hypothesis test.
Label check (stated before results were inspected, 2026-10-15): a historical label is "consistent in this game" if
  strong -> PLAY is advantageous against the COPY partner policy (10 * max_j q(PLAY j) > 7), and
  weak   -> it is not (10 * max_j q(PLAY j) <= 7).
Items are never relabelled or replaced on this basis."""
import csv, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import scoring as S

HERE = Path(__file__).resolve().parent.parent
run = sys.argv[1] if len(sys.argv) > 1 else "pilot"
rows = [json.loads(l) for l in open(HERE / "results" / run / "responses.jsonl")]
FZ = json.loads((HERE / "design/FROZEN.json").read_text())
out = HERE / "results" / run / "analysis"; out.mkdir(exist_ok=True)
act = lambda r: "PASS" if r["decision"] == "PASS" else ("PLAY", r["object_canonical"])
name = lambda a: "PASS" if a == "PASS" else f"PLAY_obj{a[1]}"

cells, dists = [], []
for it in FZ["items"]:
    for cond in ("COPY", "DIFFERENT"):
        sel = lambda role: [r for r in rows if r["array"] == it["array"] and r["condition"] == cond and r["role"] == role]
        allr = {k: sel(k) for k in ("policy", "focal", "fresh")}
        ok = {k: [act(r) for r in v if r["status"] == "ok"] for k, v in allr.items()}
        c = dict(array=it["array"], label=it["historical_label"], condition=cond, partner=FZ["partner_models"][cond],
                 **{f"n_{k}_ok": len(v) for k, v in ok.items()}, **{f"n_{k}_sent": len(v) for k, v in allr.items()},
                 **{f"n_{k}_{s}": sum(r["status"] == s for r in allr[k]) for k in allr for s in ("invalid_response", "refusal", "api_failure")})
        if min(len(v) for v in ok.values()) >= 2:
            s = S.cell_summary(ok["policy"], ok["focal"], ok["fresh"])
            ci = S.bootstrap(ok["policy"], ok["focal"], ok["fresh"])
            c.update(BR=s["BR"], BR_actions="|".join(s["BR_actions"]), V=s["V"], regret_norm=s["regret_norm"],
                     focal_pass=s["p"]["PASS"], partner_pass=s["q"]["PASS"], max_partner_play_obj=max(s["q"][a] for a in S.ACTIONS[1:]),
                     paired_payoff_norm=s["realized_paired"]["payoff_norm"], paired_match=s["realized_paired"]["match_rate"],
                     n_pairs=s["realized_paired"]["n_pairs"], cross_payoff_norm=s["realized_cross"]["payoff_norm"],
                     cross_match=s["realized_cross"]["match_rate"],
                     **{f"{k}_lo": v[0] for k, v in ci.items()}, **{f"{k}_hi": v[1] for k, v in ci.items()})
            if cond == "COPY":
                adv = 10 * c["max_partner_play_obj"] > 7
                c["label_consistent"] = adv if it["historical_label"] == "strong" else (not adv)
            for role in ("policy", "focal", "fresh"):
                d = S.dist(ok[role])
                dists.append(dict(array=it["array"], label=it["historical_label"], condition=cond, role=role,
                                  model=FZ["partner_models"][cond] if role != "focal" else "GPT-5.5", n=len(ok[role]),
                                  **{name(a): round(d[a] * len(ok[role])) for a in S.ACTIONS}))
        cells.append(c)

for fn, data in (("cells.csv", cells), ("distributions.csv", dists)):
    keys = list(dict.fromkeys(k for d in data for k in d))
    with open(out / fn, "w", newline="") as fh:
        w = csv.DictWriter(fh, keys); w.writeheader(); w.writerows(data)
spend = sum(r["cost_usd"] for r in rows)
summ = dict(records=len(rows), by_status={s: sum(r["status"] == s for r in rows) for s in ("ok", "invalid_response", "refusal", "api_failure")},
            retries=sum(max(0, r["attempts"] - 1) for r in rows), spend_usd=spend,
            spend_by_model={m: sum(r["cost_usd"] for r in rows if r["model"] == m) for m in ("GPT-5.5", "Claude Opus 5")},
            stops=sorted({str(r["stop"]) for r in rows}), models_returned=sorted({str(r["model_returned"]) for r in rows}))
(out / "summary.json").write_text(json.dumps(dict(summary=summ, cells=cells), indent=1, default=str))
print(json.dumps(summ, indent=1))
for c in cells:
    print(f"{c['array']:17s} {c['label']:6s} {c['condition']:9s} ok {c['n_policy_ok']}/{c['n_focal_ok']}/{c['n_fresh_ok']} "
          + (f"BR {c['BR']:.2f} [{c['BR_lo']:.2f},{c['BR_hi']:.2f}] regret {c['regret_norm']:+.3f} [{c['regret_norm_lo']:+.3f},{c['regret_norm_hi']:+.3f}] "
             f"payoff {c['paired_payoff_norm']:.2f} (cross {c['cross_payoff_norm']:.2f} [{c['cross_payoff_norm_lo']:.2f},{c['cross_payoff_norm_hi']:.2f}]) "
             f"match {c['cross_match']:.2f} focalPASS {c['focal_pass']:.2f} partnerPASS {c['partner_pass']:.2f}"
             + (f" label_consistent {c['label_consistent']}" if 'label_consistent' in c else "") if "BR" in c else "insufficient"))
for d in dists: print(d)
