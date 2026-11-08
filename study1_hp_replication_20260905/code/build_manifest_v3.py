"""Assemble the frozen 120-stimulus candidate battery for Study 1-HP v3.

  15  original Study 1 battery      (reused verbatim)
  30  frozen expansion battery      (reused verbatim)
  75  new v3 families               (code/make_battery_v3.py, one batch, frozen)

Writes a manifest in the SAME schema psc_common.load_manifest() expects, so the
frozen Stage A/B/C code path runs unchanged. Never touches Study 1's own tree.
"""
import csv, hashlib, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
S1 = os.path.expanduser("~/Desktop/Coordination/Self_Coordination/policy_specific_self_coordination_20260812_1401")
EXPANSION = os.path.expanduser("~/Desktop/Coordination/LLM_Coordination/Name_game_experiment/stimuli/expansion")
V3 = os.path.join(EXP, "stimuli", "v3")

COLS = ["stimulus_id","family","source","identity_1","identity_2","path_AB","path_BA",
        "local_AB","local_BA","prior_class_report","prior_note_report"]

rows = []
# --- 1. original Study 1 battery -------------------------------------------
for r in csv.DictReader(open(os.path.join(S1, "stimulus_manifest.csv"))):
    rows.append({c: r.get(c, "") for c in COLS} | {"source": "study1_original"})
n1 = len(rows)

# --- 2. frozen expansion battery -------------------------------------------
em = os.path.join(EXPANSION, "manifest.csv")
for r in csv.DictReader(open(em)):
    sid = r["stimulus_id"]
    ab, ba = os.path.join(EXPANSION, f"{sid}_AB.png"), os.path.join(EXPANSION, f"{sid}_BA.png")
    if not (os.path.exists(ab) and os.path.exists(ba)): continue
    rows.append(dict(stimulus_id=sid, family=r["family"], source="expansion_frozen",
                     identity_1=r["identity_1"], identity_2=r["identity_2"],
                     path_AB=ab, path_BA=ba, local_AB=ab, local_BA=ba,
                     prior_class_report="expansion", prior_note_report=r.get("manipulation","")))
n2 = len(rows) - n1

# --- 3. new v3 battery ------------------------------------------------------
for r in csv.DictReader(open(os.path.join(V3, "manifest.csv"))):
    sid = r["stimulus_id"]
    ab, ba = os.path.join(V3, f"{sid}_AB.png"), os.path.join(V3, f"{sid}_BA.png")
    rows.append(dict(stimulus_id=sid, family=r["family"], source="v3_new",
                     identity_1=r["identity_1"], identity_2=r["identity_2"],
                     path_AB=ab, path_BA=ba, local_AB=ab, local_BA=ba,
                     prior_class_report="v3_new", prior_note_report=r["manipulation"]))
n3 = len(rows) - n1 - n2

ids = [r["stimulus_id"] for r in rows]
assert len(set(ids)) == len(ids), "duplicate stimulus_id"
for r in rows:
    for k in ("path_AB","path_BA"):
        assert os.path.exists(r[k]), f"missing image: {r[k]}"

out = os.path.join(EXP, "stimulus_manifest.csv")
with open(out, "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=COLS); w.writeheader()
    for r in rows: w.writerow({c: r.get(c, "") for c in COLS})

h = hashlib.sha256()
for r in rows:
    for k in ("path_AB","path_BA"):
        h.update(open(r[k],"rb").read())
open(os.path.join(EXP, "BATTERY_SHA256.txt"),"w").write(h.hexdigest()+"\n")
mh = hashlib.sha256(open(out,"rb").read()).hexdigest()
print(f"battery: {len(rows)} stimuli  ({n1} study1 + {n2} expansion + {n3} v3_new)")
print(f"families: {len(set(r['family'] for r in rows))}")
print(f"images sha256:   {h.hexdigest()}")
print(f"manifest sha256: {mh}")
print(f"-> {out}")
