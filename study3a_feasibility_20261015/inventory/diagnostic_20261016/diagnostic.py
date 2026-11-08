"""Study 3A read-only design diagnostic (2026-10-16). Authorisation: "okay. send CC to do the read-only diagnostic"
(user, relayed by the ChatGPT research manager, message study3a-readonly-design-diagnostic-01). Local analysis only.

For each of the 19 retained GPT-5.5 candidate items (focal GPT-5.5, low effort, archived 3A prompts):
  q includes participation: q(PASS) + sum_j q(PLAY j) = 1, never conditioned on PLAY.
  Sources are kept separate:
    COPY_POLICY      independent GPT COPY partner-policy sample (10-15 pilot policy role)        -> held-out policy
    COPY_ARCHIVED    archived GPT COPY game draws (two_model, gpt_staghunt_pilot) + pilot focal/fresh
                     = designated focal evaluation draws in plan v2 -> any use as q is EXPLORATORY reuse
    DIFF_POLICY      independent Opus DIFFERENT partner-policy sample (pilot policy role)        -> held-out policy
    DIFF_FRESH       independent Opus DIFFERENT fresh-partner sample (pilot fresh role)
    DIFF_OPUS_SEP    archived Opus DIFFERENT game draws (two_model, Sep; Opus's own game) - actual partner behaviour,
                     independent of GPT draws; Sep/Oct pooling NOT established
    GPT_DIFF_FOCAL   GPT focal actions under DIFFERENT framing - NOT an Opus partner-policy sample (context only)
Excluded by construction: Stage 0 / Stage A rows (non-game prompt), high effort, GREEN, SHAPES, M07."""
import csv, glob, json, sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
SC = Path.home() / "Desktop/Coordination/Self_Coordination"
STAG = Path.home() / "Desktop/Superrationality/Stag"
sys.path.insert(0, str(SC / "study3a_feasibility_20261015/code"))
import scoring as S

GAME = {"49e35910": "COPY", "8222a371": "DIFFERENT"}
CATS = ["PASS", "PLAY0", "PLAY1", "PLAY2", "PLAY3"]
STAT = ["ok", "invalid_response", "refusal", "api_failure"]
pilot_jobs = {json.loads(l)["job_key"]: json.loads(l) for l in open(SC / "study3a_feasibility_20261015/design/jobs.jsonl")}

def records():
    for f in sorted(glob.glob(str(STAG / "two_model_staghunt_20260916/results/*/responses.jsonl"))):
        sub = Path(f).parent.name
        for l in open(f):
            r = json.loads(l)
            if r["phase"] != "game" or r.get("prompt_sha8") not in GAME or "high" in sub: continue
            yield r, f"two_model_staghunt_20260916/{sub}", "2026-09", r["model"], GAME[r["prompt_sha8"]], "game"
    for l in open(STAG / "gpt_staghunt_pilot_20260916/results/pilot/responses.jsonl"):
        r = json.loads(l)
        if r.get("prompt_sha8") not in GAME: continue
        yield r, "gpt_staghunt_pilot_20260916/pilot", "2026-09", "GPT-5.5", GAME[r["prompt_sha8"]], "game"
    for l in open(SC / "study3a_feasibility_20261015/results/pilot/responses.jsonl"):
        r = json.loads(l); j = pilot_jobs[r["job_key"]]
        assert j["prompt_sha8"] in GAME and GAME[j["prompt_sha8"]] == r["condition"]
        yield r, "study3a_feasibility_20261015/pilot", "2026-10", r["model"], r["condition"], r["role"]

def source_of(run, model, cond, role):
    if model == "GPT-5.5" and cond == "COPY": return "COPY_POLICY" if role == "policy" else "COPY_ARCHIVED"
    if model == "GPT-5.5" and cond == "DIFFERENT": return "GPT_DIFF_FOCAL"
    if model == "Claude Opus 5" and cond == "DIFFERENT":
        return {"policy": "DIFF_POLICY", "fresh": "DIFF_FRESH"}.get(role, "DIFF_OPUS_SEP")
    return None                                        # Opus COPY / Fable: not partners of focal GPT

acts = defaultdict(list); status = defaultdict(Counter); runs = defaultdict(set); mapping_errors = 0; n_rows = 0
for r, run, month, model, cond, role in records():
    src = source_of(run, model, cond, role)
    if src is None: continue
    key = (r["array"], src); n_rows += 1
    status[key][r["status"]] += 1; runs[key].add(f"{run} ({month})")
    if r["status"] != "ok": continue
    if r["decision"] == "PLAY":
        if r["object_canonical"] != r["slot_to_canonical"][r["object_slot"] - 1]: mapping_errors += 1
        acts[key].append(("PLAY", r["object_canonical"]))
    else:
        acts[key].append("PASS")

items = sorted({a for (a, s) in acts if s in ("COPY_POLICY", "COPY_ARCHIVED")})
assert len(items) == 19, items
hist = {}
for a in json.loads((STAG / "two_model_staghunt_20260916/design/FROZEN.json").read_text())["selection"]["arrays"]:
    if a["model"] == "GPT-5.5": hist[a["array"]] = f"{a['bin']} (two_model Stage A)"
for a in json.loads((STAG / "gpt_staghunt_pilot_20260916/design/FROZEN.json").read_text())["arrays"]:
    hist.setdefault(a.get("array_id") or a.get("array"), f"{a.get('cls')} (gpt_staghunt_pilot Stage A)")

def dist_str(x):
    c = Counter("PASS" if a == "PASS" else f"PLAY{a[1]}" for a in x)
    return "/".join(str(c[k]) for k in CATS)

def q(x, a):  # participation-inclusive probability of action a
    return sum(y == a for y in x) / len(x) if x else None

rows = []
for it in items:
    row = dict(array=it, historical_label_provenance=hist.get(it, "none recorded"),
               focal="GPT-5.5 gpt-5.5-2026-04-23, effort low, summary auto, no output cap, text then image",
               copy_partner="GPT-5.5 (same settings), prompt 49e35910", diff_partner="Claude Opus 5 (claude-opus-5, adaptive summarized, effort low, max_tokens 4000), prompt 8222a371")
    for src in ("COPY_POLICY", "COPY_ARCHIVED", "DIFF_POLICY", "DIFF_FRESH", "DIFF_OPUS_SEP", "GPT_DIFF_FOCAL"):
        x = acts.get((it, src), []); st = status.get((it, src), Counter())
        row[f"{src}_sources"] = "; ".join(sorted(runs.get((it, src), []))) or "NOT MEASURED"
        row[f"{src}_n_valid"] = st["ok"]; row[f"{src}_n_invalid_refused_failed"] = f"{st['invalid_response']}/{st['refusal']}/{st['api_failure']}"
        row[f"{src}_PASS_P0_P1_P2_P3"] = dist_str(x) if x else ""
        row[f"{src}_pass_rate"] = round(q(x, "PASS"), 3) if x else ""
    # s and modal COPY PLAY object: independent policy sample if it exists, otherwise archived draws (exploratory)
    s_src = "COPY_POLICY" if acts.get((it, "COPY_POLICY")) else "COPY_ARCHIVED"
    xc = acts[(it, s_src)]
    row["s_source"] = "independent policy sample" if s_src == "COPY_POLICY" else "EXPLORATORY reuse of archived evaluation draws"
    stn = S.strength(xc)
    row.update(s=round(stn["s_hat"], 3), s_lo=round(stn["s_lo"], 3), s_hi=round(stn["s_hi"], 3), P_s_gt_0_7=round(stn["p_above"], 3), s_n=stn["n"])
    if s_src == "COPY_POLICY":   # also report the archived estimate for comparison
        sa = S.strength(acts[(it, "COPY_ARCHIVED")]); row["s_archived_exploratory"] = round(sa["s_hat"], 3)
    play_counts = {j: sum(a == ("PLAY", j) for a in xc) for j in range(4)}
    top = max(play_counts.values())
    if top == 0:
        row["modal_copy_play_objects"] = "NO PLAY observed (j* undefined)"; modal = []
    else:
        modal = [j for j, c in play_counts.items() if c == top]; row["modal_copy_play_objects"] = "|".join(map(str, modal))
    # payoffs of PLAY(j*) vs PASS = 7, only where the actual partner distribution is measured
    pay_copy, pay_diff = [], []
    for j in modal:
        pay_copy.append(f"j{j}: {10 * q(xc, ('PLAY', j)):.2f}")
        for dsrc, tag in (("DIFF_POLICY", "Opus policy Oct"), ("DIFF_OPUS_SEP", "Opus archived Sep")):
            xd = acts.get((it, dsrc))
            if xd: pay_diff.append(f"j{j} [{tag}, n={len(xd)}]: {10 * q(xd, ('PLAY', j)):.2f}")
    row["PASS_payoff"] = 7
    row["10q_COPY_PLAY_jstar"] = "; ".join(pay_copy) if modal else "n/a (no PLAY)"
    row["10q_DIFF_PLAY_jstar"] = "; ".join(pay_diff) if (modal and pay_diff) else ("n/a (no PLAY)" if not modal else "MISSING: no Opus DIFFERENT partner measurement")
    tie_diff = len(modal) > 1 and len({p.split(': ')[1] for p in pay_diff if 'Oct' in p or 'Sep' in p}) > 1
    row["tie_note"] = "tied modal objects differ in DIFFERENT payoff; alternatives shown" if tie_diff else ("tied modal objects" if len(modal) > 1 else "")
    rows.append(row)

with open(HERE / "diagnostic_items.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, list(dict.fromkeys(k for r in rows for k in r))); w.writeheader(); w.writerows(rows)
val = dict(rows_read=n_rows, items=len(items), canonical_mapping_errors=mapping_errors,
           invalid_refused_failed_total=sum(status[k]["invalid_response"] + status[k]["refusal"] + status[k]["api_failure"] for k in status))
(HERE / "validation.json").write_text(json.dumps(val, indent=1))
print(json.dumps(val))
for r in rows:
    print(f"{r['array']:17s} s={r['s']:.3f} [{r['s_lo']:.2f},{r['s_hi']:.2f}] P>.7={r['P_s_gt_0_7']:.2f} ({'POL' if r['s_source'].startswith('indep') else 'arch'} n={r['s_n']}) "
          f"COPYpass={r['COPY_ARCHIVED_pass_rate']} j*={r['modal_copy_play_objects']} | COPY {r['10q_COPY_PLAY_jstar']} | DIFF {r['10q_DIFF_PLAY_jstar']} | OpusPASS pol={r['DIFF_POLICY_pass_rate']} sep={r['DIFF_OPUS_SEP_pass_rate']}")
