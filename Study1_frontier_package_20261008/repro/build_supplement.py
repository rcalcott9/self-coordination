"""Build supplementary tables (docs/supplement/*.csv + SUPPLEMENT.md) from packaged frozen designs, runs and reported outputs."""
import csv, json, os, glob, collections as C
PKG = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
H = os.path.join(PKG, "home", "Desktop/Coordination/Self_Coordination"); R = os.path.join(PKG, "reported")
S1 = os.path.join(H, "study1_frontier_min_20261007"); S1B = os.path.join(H, "study1b_crossed_object_20261007")
OUT = os.path.join(PKG, "docs", "supplement"); os.makedirs(OUT, exist_ok=True)
def w(name, header, rows):
    with open(os.path.join(OUT, name), "w", newline="") as fh:
        x = csv.writer(fh); x.writerow(header); x.writerows(rows)
    return name, len(rows)
made = []
# S1 integrity by stage (Study 1 and 1b)
rows = []
for study, root, stages in (("Study 1", S1, ["preflight", "pilot", "anchor", "main"]), ("Study 1b", S1B, ["screen", "preflight", "pilot", "main"])):
    for st in stages:
        rs = [r for f in glob.glob(os.path.join(root, "runs", st, "*.csv")) for r in csv.DictReader(open(f))]
        rows.append([study, st, len(rs), sum(r["transport_ok"] == "1" for r in rs), sum(r["parse_ok"] == "1" for r in rs),
                     sum(r["transport_ok"] == "1" and r["model_match"] != "1" for r in rs), round(sum(float(r["cost_usd"] or 0) for r in rs), 4)])
made.append(w("TableS1_integrity_cost.csv", ["study", "stage", "calls", "transport_ok", "parsed", "model_mismatch", "cost_usd"], rows))
# S2 prompts
rows = []
F = json.load(open(os.path.join(S1, "design", "FROZEN.json"))); FM = json.load(open(os.path.join(S1B, "design", "FROZEN_MAIN.json")))
for k, v in F["prompts"].items(): rows.append(["Study 1", k, v["sha8"], v["text"]])
for k, v in FM["prompts"].items(): rows.append(["Study 1b", k, v["sha8"], v["text"]])
made.append(w("TableS2_prompts.csv", ["study", "prompt_key", "sha8", "text"], rows))
# S3 Study 1 per-array
made.append(w("TableS3_study1_items.csv", *(lambda a: (a[0], a[1:]))(list(csv.reader(open(os.path.join(R, "study1", "item_table.csv")))))))
# S4 Study 1 divergence items
made.append(w("TableS4_study1_divergence_items.csv", *(lambda a: (a[0], a[1:]))(list(csv.reader(open(os.path.join(R, "study1", "divergence_items.csv")))))))
# S5 drift power
D = json.load(open(os.path.join(R, "study1", "audit", "D_drift", "drift_audit.json")))
def flat(d, pre=""):
    for k, v in d.items():
        if isinstance(v, dict): yield from flat(v, f"{pre}{k}.")
        else: yield (f"{pre}{k}", json.dumps(v) if isinstance(v, list) else v)
made.append(w("TableS5_drift_audit.csv", ["quantity", "value"], list(flat(D))))
# S6 Study 1b selection table
SEL = json.load(open(os.path.join(S1B, "design", "SELECTION.json"))); rows = []
sel = {x: s for s, v in SEL["selected"].items() for x in v}
for x, t in SEL["per_array"].items():
    if "gpt" not in t: rows.append([x, "", "", "", "", "", "", t.get("reason", "")]); continue
    rows.append([x, t["stratum"] or "", sel.get(x, ""), json.dumps(t["gpt"]["counts"]), round(t["gpt"]["modal_share"], 3),
                 json.dumps(t["claude"]["counts"]), round(t["claude"]["modal_share"], 3), "S1 fallback" if t.get("s1_fallback") else ""])
made.append(w("TableS6_study1b_screen_selection.csv", ["array", "eligible_stratum", "selected_stratum", "gpt_screen_counts", "gpt_modal_share",
                                                        "opus_screen_counts", "opus_modal_share", "note"], rows))
# S7 Study 1b per-array
made.append(w("TableS7_study1b_items.csv", *(lambda a: (a[0], a[1:]))(list(csv.reader(open(os.path.join(R, "study1b", "item_table.csv")))))))
# S8 family table
FS = json.load(open(os.path.join(R, "study1b", "family_sensitivity.json"))); rows = []
for f, info in FS["families"].items():
    rows.append([f, ";".join(info["arrays"]), ";".join(info["strata"])] + [FS[k]["family_means"][f] for k in ("D_pooled", "D_gpt", "D_opus")]
                + [round(FS["D_pooled"]["lofo_family_mean"][f], 4)])
made.append(w("TableS8_study1b_families.csv", ["family", "arrays", "strata", "D_pooled", "D_gpt", "D_opus", "LOFO_pooled_family_mean"], rows))
# S9 cell means and contrasts
RB = json.load(open(os.path.join(R, "study1b", "results.json"))); rows = [[k, round(v, 4)] for k, v in RB["cell_mean_brier_primary"].items()]
for k, v in RB["primary"].items(): rows.append([f"primary.{k}.mean [CI] p", f"{v['mean']:.4f} [{v['ci95'][0]:.4f}, {v['ci95'][1]:.4f}] p={v['signflip_p']:.4f}"])
made.append(w("TableS9_study1b_cells_contrasts.csv", ["quantity", "value"], rows))
with open(os.path.join(PKG, "docs", "SUPPLEMENT.md"), "w") as fh:
    fh.write("# Supplementary tables\n\nCSV files in `docs/supplement/`, built by `repro/build_supplement.py` from the frozen designs, raw runs and reported outputs.\n\n| Table | File | Rows |\n|---|---|---|\n")
    desc = {"TableS1": "Integrity and cost by stage", "TableS2": "All frozen prompts with sha8 and full text", "TableS3": "Study 1 per-array: y, self, auditor, D, PLAY, old PLAY, same-order match",
            "TableS4": "Study 1 per-array cross-model divergence (exploratory)", "TableS5": "Calibration drift gate audit and power", "TableS6": "Study 1b screening counts, eligibility, selection",
            "TableS7": "Study 1b per-array cell Brier scores and contrasts", "TableS8": "Study 1b family-level means and leave-one-family-out (post hoc)", "TableS9": "Study 1b cell means and primary contrasts"}
    for n, k in made: fh.write(f"| {desc[n.split('_')[0]]} | `{n}` | {k} |\n")
print(made)
