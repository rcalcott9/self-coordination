"""Study 3A inventory (2026-10-15, local, no calls): every existing IN-GAME action in the guaranteed-PASS Stag Hunt
(PASS 7 always; PLAY j 10 iff partner PLAYs j; else 0), by item x model/settings x partner condition x prompt.
Reference-task (Stage 0 / Stage A) choices are excluded by construction: only rows whose prompt is a game prompt."""
import csv, glob, hashlib, json
from collections import Counter, defaultdict
from pathlib import Path

STAG = Path.home() / "Desktop/Superrationality/Stag"
SC = Path.home() / "Desktop/Coordination/Self_Coordination"
STIM = SC / "study2_4opt_20260830/stimuli"
GAME_PROMPTS = {"49e35910": "COPY", "8222a371": "DIFFERENT"}       # archived visual 3A game prompts
OUT = Path(__file__).resolve().parent

stim_hash = {}
def canon_image(array, h):
    if array not in stim_hash:
        stim_hash[array] = {hashlib.sha256((STIM / array / f"perm{p:02d}.png").read_bytes()).hexdigest(): p for p in range(24)} \
            if (STIM / array).is_dir() else {}
    return h in stim_hash[array]

sources = [  # (run label, glob of responses, default model if the row lacks one)
    ("two_model_staghunt_20260916", str(STAG / "two_model_staghunt_20260916/results/*/responses.jsonl"), None),
    ("gpt_staghunt_pilot_20260916", str(STAG / "gpt_staghunt_pilot_20260916/results/*/responses.jsonl"), "GPT-5.5"),
    ("fable_staghunt_20261008", str(STAG / "fable_staghunt_20261008/results/*/responses.jsonl"), "Claude Fable 5.1"),
    ("study3a_feasibility_20261015", str(SC / "study3a_feasibility_20261015/results/pilot/responses.jsonl"), None),
]
PILOT_IMG = {json.loads(l)["job_key"]: json.loads(l)["image_sha256"] for l in open(SC / "study3a_feasibility_20261015/design/jobs.jsonl")}
cells = defaultdict(lambda: dict(n_sent=0, n_ok=0, acts=Counter(), perms=set(), img_ok=0, returned=set(), effort=set()))
skipped = Counter()
for run, pat, default_model in sources:
    for f in sorted(glob.glob(pat)):
        sub = Path(f).parent.name
        for line in open(f):
            r = json.loads(line)
            if r.get("mock"): skipped["mock"] += 1; continue
            s8 = r.get("prompt_sha8") or ("49e35910" if r["condition"] == "COPY" else "8222a371" if run == "study3a_feasibility_20261015" else None)
            if s8 not in GAME_PROMPTS: skipped[f"non-game prompt ({run})"] += 1; continue
            model = r.get("model") or default_model
            effort = r.get("effort") or ("high" if "high" in sub else "low")
            role = r.get("role", "game")
            key = (r["array"], model, effort, r["condition"], s8, run, sub, role)
            c = cells[key]; c["n_sent"] += 1
            c["returned"].add(str(r.get("model_returned")))
            if r["status"] != "ok": continue
            c["n_ok"] += 1
            c["acts"]["PASS" if r["decision"] == "PASS" else f"PLAY{r['object_canonical']}"] += 1
            c["perms"].add(r.get("perm")); c["img_ok"] += canon_image(r["array"], r.get("image_sha256") or PILOT_IMG.get(r["job_key"]))

rows = []
for (array, model, effort, cond, s8, run, sub, role), c in sorted(cells.items()):
    rows.append(dict(array=array, model=model, effort=effort, condition=cond, prompt_sha8=s8, run=run, subrun=sub, role=role,
                     model_returned="|".join(sorted(c["returned"])), n_sent=c["n_sent"], n_ok=c["n_ok"],
                     PASS=c["acts"]["PASS"], **{f"PLAY{j}": c["acts"][f"PLAY{j}"] for j in range(4)},
                     distinct_perms=len(c["perms"]), images_match_canonical_stimuli=c["img_ok"] == c["n_ok"]))
with open(OUT / "inventory_cells.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, list(rows[0])); w.writeheader(); w.writerows(rows)

# pooled view per (array, model, effort, condition): independent draws from one frozen prompt + settings
pool = defaultdict(lambda: Counter())
for r in rows:
    k = (r["array"], r["model"], r["effort"], r["condition"])
    for a in ("n_ok", "PASS", "PLAY0", "PLAY1", "PLAY2", "PLAY3"): pool[k][a] += r[a]
    pool[k]["runs"] = pool[k].get("runs", 0) + 1
with open(OUT / "inventory_pooled.csv", "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["array", "model", "effort", "condition", "n_ok", "PASS", "PLAY0", "PLAY1", "PLAY2", "PLAY3", "n_source_cells"])
    for k, v in sorted(pool.items()):
        w.writerow([*k, v["n_ok"], v["PASS"], v["PLAY0"], v["PLAY1"], v["PLAY2"], v["PLAY3"], v["runs"]])
print("skipped:", dict(skipped))
print(f"{len(rows)} source cells; {len(pool)} pooled item x model x effort x condition cells")
for k, v in sorted(pool.items()):
    print(f"{k[0]:18s} {k[1]:16s} {k[2]:4s} {k[3]:9s} n={v['n_ok']:3d}  PASS {v['PASS']:2d} | P0 {v['PLAY0']:2d} P1 {v['PLAY1']:2d} P2 {v['PLAY2']:2d} P3 {v['PLAY3']:2d}")
