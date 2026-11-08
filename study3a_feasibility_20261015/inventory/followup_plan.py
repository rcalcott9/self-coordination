"""Proposed smallest 3A follow-up (2026-10-15; PROPOSED, not authorised; no calls). Candidate set = every item with
existing low-effort GPT-5.5 in-game actions under the archived 3A prompts. No selection on outcomes; historical labels are
carried as provenance columns only. Writes followup_items.csv and prints exact counts and costs."""
import csv, json
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
STAG = Path.home() / "Desktop/Superrationality/Stag"
pool = list(csv.DictReader(open(HERE / "inventory_pooled.csv")))
cell = {(r["array"], r["model"], r["effort"], r["condition"]): r for r in pool}
pilot = {json.loads(l)["array"] for l in open(HERE.parent / "design/jobs.jsonl")}

# historical labels (provenance only; NOT current strength labels)
hist = {}
for a in json.loads((STAG / "two_model_staghunt_20260916/design/FROZEN.json").read_text())["selection"]["arrays"]:
    if a["model"] == "GPT-5.5": hist[a["array"]] = f"{a['bin']} (two_model selection, Stage A c_hat {a['c_hat_hist']:.3f})"
for a in json.loads((STAG / "gpt_staghunt_pilot_20260916/design/FROZEN.json").read_text())["arrays"]:
    aid = a.get("array_id") or a.get("array"); hist.setdefault(aid, f"{a.get('cls')} (gpt_staghunt_pilot, Stage A)")

POLICY, FRESH = 24, 12
COST = {"GPT-5.5": 2.47314 / 240, "Claude Opus 5": 0.949375 / 144}      # observed mean per call in the 10-15 pilot
MAXC = {"GPT-5.5": 0.0241, "Claude Opus 5": 0.0104}                       # max observed per game call (two_model)
items = sorted({k[0] for k in cell if k[1] == "GPT-5.5" and k[2] == "low" and k[3] == "COPY"})
rows, calls = [], defaultdict(int)
for a in items:
    g_copy = int(cell[(a, "GPT-5.5", "low", "COPY")]["n_ok"]); g_diff = int(cell.get((a, "GPT-5.5", "low", "DIFFERENT"), {}).get("n_ok", 0))
    o_diff = int(cell.get((a, "Claude Opus 5", "low", "DIFFERENT"), {}).get("n_ok", 0))
    if a in pilot:                                                     # already split into policy/focal/fresh by design
        need_o_pol = need_o_fresh = need_g_pol = 0; status = "complete (10-15 pilot split; archived draws extra)"
    else:
        need_o_pol = POLICY if o_diff == 0 else 0                       # existing Opus DIFFERENT draws become the policy sample
        need_o_fresh = FRESH
        need_g_pol = POLICY                                             # option (ii): new GPT COPY policy draws
        status = "needs Opus DIFFERENT policy + fresh" if o_diff == 0 else "Opus DIFFERENT policy exists (archived); needs fresh"
    calls["Opus DIFFERENT policy"] += need_o_pol; calls["Opus DIFFERENT fresh"] += need_o_fresh; calls["GPT COPY policy (option ii)"] += need_g_pol
    rows.append(dict(array=a, historical_label=hist.get(a, "none recorded"), gpt_copy_ingame_n=g_copy, gpt_diff_ingame_n=g_diff,
                     opus_diff_ingame_n=o_diff, new_opus_policy=need_o_pol, new_opus_fresh=need_o_fresh, new_gpt_copy_policy_opt_ii=need_g_pol,
                     status=status))
with open(HERE / "followup_items.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, list(rows[0])); w.writeheader(); w.writerows(rows)
for r in rows: print(r)
core = calls["Opus DIFFERENT policy"] + calls["Opus DIFFERENT fresh"]
print(dict(calls), "| core (Opus only)", core, "| with option (ii)", core + calls["GPT COPY policy (option ii)"])
for lbl, n_o, n_g in (("core", core, 0), ("core + option ii", core, calls["GPT COPY policy (option ii)"])):
    print(f"{lbl}: mean ${n_o*COST['Claude Opus 5'] + n_g*COST['GPT-5.5']:.2f}  at max per-call ${n_o*MAXC['Claude Opus 5'] + n_g*MAXC['GPT-5.5']:.2f}")
