"""Export item-level data for the 2x3 Study 1 figure (columns GPT-5.5, Claude Opus 5, Qwen; top = reliability
curves, bottom = option-choice self advantage). Existing data only; no API calls.

Everything is recomputed from raw run files and cross-checked against each study's own item tables.
Outputs (data/):
  reliability_items.csv        top row: one row per model x setting x sample x item (x = measured agreement,
                               PLAY/PASS counts, self-prediction and auditor calibration where they exist)
  crossed_prediction_cells.csv bottom row source: model x setting x array x predictor x target Brier / log score
  self_advantage_items.csv     bottom row: per-array pooled and target-specific self-minus-cross advantage
  panel_summary.json           model-level statistics already reported, for panel annotation (copied, not refit)
"""
import csv, glob, json, os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(os.path.dirname(HERE), "data")
os.makedirs(OUT, exist_ok=True)
SC = os.path.expanduser("~/Desktop/Coordination/Self_Coordination")
STAG = os.path.expanduser("~/Desktop/Superrationality/Stag")
S1A, S1B, HI = (os.path.join(SC, d) for d in ("study1_frontier_min_20261007", "study1b_crossed_object_20261007",
                                              "study1_highreason_20261009"))
MID = {"gpt": "gpt-5.5-2026-04-23", "claude": "claude-opus-5"}
NAME = {"gpt": "GPT-5.5", "claude": "Claude Opus 5"}
SET = {("gpt", "low"): "reasoning effort low", ("claude", "low"): "thinking disabled",
       ("gpt", "high"): "reasoning effort high", ("claude", "high"): "adaptive thinking, effort high, max_tokens 16000"}
fam = lambda x: x.rsplit("_m", 1)[0]
rd = lambda p: list(csv.DictReader(open(p)))


def wmm(c):
    c = np.asarray(c, float); n = c.sum()
    return float((c * (c - 1)).sum() / (n * (n - 1)))


def sha8_of(p):
    return open(p).read().split()[0][:8]


# =========================================================================== TOP ROW
REL = []
# ---- frontier low (Study 1a minimal run; y = reused frame calibration, 48 draws/array)
F1A = json.load(open(os.path.join(S1A, "design", "FROZEN.json")))
fsha_lo = sha8_of(os.path.join(S1A, "design", "FROZEN.sha256"))
frame = {}
for r in rd(F1A["calibration_reuse"]["source"]):
    for m, mid in MID.items():
        if r["checkpoint_requested"] == mid and r["parse_ok"] == "1" and r["array_id"] in F1A["arrays"]:
            frame.setdefault((m, r["array_id"]), []).append(int(r["canonical_index"]))
lo_rows = [r for f in glob.glob(os.path.join(S1A, "runs", "main", "*.csv")) for r in rd(f) if r["frozen_sha8"] == fsha_lo]
hi_F = json.load(open(os.path.join(HI, "design", "FROZEN.json")))
fsha_hi = sha8_of(os.path.join(HI, "design", "FROZEN.sha256"))
hi_rows = [r for f in glob.glob(os.path.join(HI, "runs", "main", "*.csv")) for r in rd(f) if r["frozen_sha8"] == fsha_hi]


def task_summ(rows, m, x):
    g = lambda t: [r for r in rows if r["focal"] == m and r["array"] == x and r["task"] == t]
    pp, sp, au = g("PLAYPASS"), g("SELFPRED"), g("AUDITOR")
    ok = lambda v: [r for r in v if r["parse_ok"] == "1"]
    return dict(n_judgements_attempted=len(pp), n_judgements_parsed=len(ok(pp)),
                n_play=sum(r["decision"] == "PLAY" for r in ok(pp)),
                n_selfpred_parsed=len(ok(sp)), selfpred_mean=np.mean([int(r["match_probability"]) / 100 for r in ok(sp)]) if ok(sp) else "",
                n_auditor_parsed=len(ok(au)), auditor_mean=np.mean([int(r["match_probability"]) / 100 for r in ok(au)]) if ok(au) else "",
                auditor_model=NAME["claude" if m == "gpt" else "gpt"])


old_lab = {"gpt": {}, "claude": {}}
for m, p in (("gpt", os.path.join(SC, "study_playpass_gpt", "data", "frozen_items.json")),
             ("claude", os.path.join(STAG, "opus_playpass", "design", "FROZEN_PARALLEL.json"))):
    fz = json.load(open(p))
    for arm in ("HIGH", "LOW"):
        for it in fz[arm]:
            old_lab[m][it["array"]] = arm

for m in MID:
    for x in F1A["arrays"]:
        c = np.bincount(frame[(m, x)], minlength=4)
        REL.append(dict(model=NAME[m], column=m, setting="low", setting_detail=SET[(m, "low")],
                        sample="frontier Study 1a (all 41 VIS-FRAME arrays)", sample_type="observational",
                        item_id=x, family=fam(x), group=old_lab[m].get(x, "MID"),
                        x_agreement=wmm(c), x_estimand="unbiased independent-order copy-copy match, 4 options",
                        x_source="reused frame calibration (study_policy_convergence visual_frame_20260909), not fresh",
                        n_ref=int(c.sum()), ref_counts="/".join(map(str, c)), **task_summ(lo_rows, m, x)))
    for x in hi_F["arrays_1a"]:
        ref = [int(r["canonical_choice"]) for r in hi_rows if r["task"] == "REF" and r["answerer"] == m and r["array"] == x
               and r["parse_ok"] == "1"]
        c = np.bincount(ref, minlength=4)
        REL.append(dict(model=NAME[m], column=m, setting="high", setting_detail=SET[(m, "high")],
                        sample="frontier Study 1a (all 41 VIS-FRAME arrays)", sample_type="observational",
                        item_id=x, family=fam(x), group=old_lab[m].get(x, "MID"),
                        x_agreement=wmm(c), x_estimand="unbiased independent-order copy-copy match, 4 options",
                        x_source="fresh high-reasoning REF draws (balanced Latin orderings)",
                        n_ref=int(c.sum()), ref_counts="/".join(map(str, c)), **task_summ(hi_rows, m, x)))

# ---- Qwen observational: Study 1 (thinking off), extreme-group selected
PQ = os.path.join(STAG, "plunkett_qwen")
fz = json.load(open(os.path.join(PQ, "results", "study1_frozen.json")))
pairs = {}
for l in open(os.path.join(PQ, "results", "predict_20260911_123902", "raw", "predictability_trials.jsonl")):
    r = json.loads(l); pairs.setdefault(r["scenario"], []).append(r)
s1 = [json.loads(l) for l in open(os.path.join(PQ, "results", "s1_20260911_132831", "raw", "s1_trials.jsonl"))]
for x in fz["play"] + fz["pass_"]:
    pr = sorted(pairs[x], key=lambda r: r["pair"])
    ag = np.mean([wmm([p["nA"], p["nB"]]) for p in pr])
    assert abs(ag - fz["agree"][x]) < 1e-12
    t = [r for r in s1 if r["scenario"] == x]; ok = [r for r in t if r["decision"]]
    REL.append(dict(model="Qwen3.5-397B-A17B step-316", column="qwen", setting="thinking off",
                    setting_detail="renderer qwen3_5_disable_thinking, T=1.0, max_tokens 90",
                    sample="Qwen Study 1 (30 of 100 trained scenarios: top/bottom 15 by agreement)",
                    sample_type="observational (extreme-group selection; truth = selection data)",
                    item_id=x, family=x, group="HIGH" if x in fz["play"] else "LOW", x_agreement=ag,
                    x_estimand="unbiased same-presentation within-pair agreement, 2 options, mean of 5 fixed pairs",
                    x_source="predict_20260911_123902 (5 pairs x 40 draws, T=1, plain choice prompt); same run selected the items",
                    n_ref=sum(p["nA"] + p["nB"] for p in pr), ref_counts=";".join(f"{p['nA']}/{p['nB']}" for p in pr),
                    n_judgements_attempted=len(t), n_judgements_parsed=len(ok),
                    n_play=sum(r["decision"] == "PLAY" for r in ok), n_selfpred_parsed=0, selfpred_mean="",
                    n_auditor_parsed=0, auditor_mean="", auditor_model=""))
# ---- Qwen intervention (MAIN): counterbalanced continuation experiment (qwen_continuation_pilot_20261009)
CP = os.path.join(STAG, "qwen_continuation_pilot_20261009")
ck = {c["label"]: c for c in json.load(open(os.path.join(CP, "design", "FROZEN_CHECKPOINTS.json")))["checkpoints"]}
eitems = {e["item_id"]: e for e in json.load(open(os.path.join(CP, "data", "eval_items.json")))}
draws, pp = {}, {}
for lab in ("baseline", "V1", "V2"):
    for l in open(os.path.join(CP, "results", f"eval_{lab}", "raw.jsonl")):
        r = json.loads(l)
        draws.setdefault((lab, r["item_id"], r["orientation"]), []).append(r)
for l in open(os.path.join(CP, "playpass", "raw.jsonl")):
    r = json.loads(l); pp.setdefault((r["checkpoint"], r["item_id"], r["orientation"]), []).append(r)
for (lab, iid, o), dv in sorted(draws.items()):
    e = eitems[iid]; ok = [d for d in dv if d["status"] == "ok"]
    cnt = np.bincount([d["object"] for d in ok], minlength=2)
    state = ("pre-continuation baseline" if lab == "baseline" else
             (e[f"state_{lab}"] if e["provenance"] == "trained" else "untrained (no continuation targets)"))
    pv = pp.get((lab, iid, o), []); pok = [r for r in pv if r["status"] == "ok" and r["decision"] in ("PLAY", "PASS")]
    REL.append(dict(model="Qwen3.5-397B-A17B clean replica 12f8e1b3" + ("" if lab == "baseline" else f" + continuation {lab}"),
                    column="qwen", setting="thinking off", setting_detail="renderer qwen3_5_disable_thinking, T=1.0",
                    sample="Qwen counterbalanced continuation (clean vs 70/30 targets; V1/V2 swap scenario halves)",
                    sample_type="intervention (counterbalanced continuation)", item_id=iid, family=e["scenario"],
                    group=state, checkpoint=lab, sampler=ck[lab]["sampler"], assignment=state, order=o,
                    provenance=e["provenance"], half=e.get("half") or "",
                    x_agreement=wmm(cnt) if cnt.sum() > 1 else "",
                    x_estimand="unbiased same-order agreement over underlying options (20 draws in this order), 2 options",
                    x_source="continuation calibration draws (eval_<checkpoint>/raw.jsonl), plain [DECISION TASK] prompt",
                    n_ref=int(cnt.sum()), ref_counts="/".join(map(str, cnt)),
                    n_judgements_attempted=len(pv), n_judgements_parsed=len(pok),
                    n_play=sum(r["decision"] == "PLAY" for r in pok), n_selfpred_parsed=0, selfpred_mean="",
                    n_auditor_parsed=0, auditor_mean="", auditor_model=""))
# ---- Qwen alpha adapter scaling: EXPLORATORY, written to its own file, never in the main export
AS = os.path.join(STAG, "qwen_reliability_intervention", "adapter_scaling", "full_study")
items = {i["item_id"]: i for i in json.load(open(os.path.join(AS, "items_208.json")))["items"]}
raw = [json.loads(l) for l in open(os.path.join(AS, "raw_trials.jsonl"))]
ALPHA = []
for iid, it in items.items():
    for cond, a, key in (("alpha1", "alpha = 1 (identity)", "r_alpha1"), ("alpha050", "alpha = .5 (dW x .5)", "r_alpha050")):
        t = [r for r in raw if r["item_id"] == iid and r["condition"] == cond]; ok = [r for r in t if r["decision"]]
        ALPHA.append(dict(model="Qwen3.5-397B-A17B clean replica 12f8e1b3", column="qwen", setting="thinking off",
                          sample="Qwen alpha adapter scaling (208 fresh items)", sample_type="EXPLORATORY intervention (generic decisiveness)",
                          item_id=iid, condition=cond, condition_detail=a, family=it["scenario"], x_agreement=it[key],
                          x_estimand="analytic expected same-presentation agreement from log-probs (not sampled), 2 options",
                          n_judgements_attempted=len(t), n_judgements_parsed=len(ok),
                          n_play=sum(r["decision"] == "PLAY" for r in ok),
                          p_play=sum(r["decision"] == "PLAY" for r in ok) / len(ok) if ok else ""))
with open(os.path.join(OUT, "reliability_items_qwen_alpha_EXPLORATORY.csv"), "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(ALPHA[0])); w.writeheader()
    for r in ALPHA:
        w.writerow({k: (round(v, 6) if isinstance(v, float) else v) for k, v in r.items()})
for r in REL:
    r["p_play"] = r["n_play"] / r["n_judgements_parsed"] if r["n_judgements_parsed"] else ""
cols = ["model", "column", "setting", "setting_detail", "sample", "sample_type", "item_id", "family", "group",
        "checkpoint", "sampler", "assignment", "order", "provenance", "half",
        "x_agreement", "x_estimand", "x_source", "n_ref", "ref_counts", "n_judgements_attempted", "n_judgements_parsed",
        "n_play", "p_play", "n_selfpred_parsed", "selfpred_mean", "n_auditor_parsed", "auditor_mean", "auditor_model"]
with open(os.path.join(OUT, "reliability_items.csv"), "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=cols, restval=""); w.writeheader()
    for r in REL:
        w.writerow({k: (round(v, 6) if isinstance(v, float) else v) for k, v in r.items()})

# cross-check against the studies' own item tables
chk = {}
for setting, path in (("low", os.path.join(S1A, "analysis", "out", "item_table.csv")),
                      ("high", os.path.join(HI, "analysis", "out_1a", "item_table.csv"))):
    T = {(r["model"], r["array"]): r for r in rd(path)}
    mx = 0
    for r in REL:
        if r["setting"] == setting and r["column"] in MID:
            t = T[(r["column"], r["item_id"])]
            mx = max(mx, abs(r["x_agreement"] - float(t["y_actual"])), abs(r["p_play"] - float(t["play_rate"])),
                     abs(r["selfpred_mean"] - float(t["self_mean"])), abs(r["auditor_mean"] - float(t["auditor_mean"])))
    chk[f"1a_{setting}_max_abs_diff_vs_item_table"] = mx

# =========================================================================== BOTTOM ROW
SEL = json.load(open(os.path.join(S1B, "design", "SELECTION.json")))
strat = {x: s for s, v in SEL["selected"].items() for x in v}
fsha_b = sha8_of(os.path.join(S1B, "design", "FROZEN_MAIN.sha256"))
lo_b = [r for f in glob.glob(os.path.join(S1B, "runs", "main", "*.csv")) for r in rd(f) if r["frozen_sha8"] == fsha_b]
M = ["gpt", "claude"]
CELLS, ADV = [], []


def crossed(rows, setting, tgt_key):
    ref, pred = {}, {}
    for r in rows:
        if r["parse_ok"] != "1" or r["array"] not in strat:
            continue
        if r["task"] == "REF":
            ref.setdefault((r["answerer"], r["array"]), []).append(int(r["canonical_choice"]))
        elif r["task"] == "PRED":
            pred.setdefault((r["answerer"], r[tgt_key], r["array"]), []).append(np.array(json.loads(r["p_canonical"])))
    S = {}
    for x in SEL["selected_flat"]:
        ph = {m: np.bincount(ref[(m, x)], minlength=4) / len(ref[(m, x)]) for m in M}
        for p in M:
            for t in M:
                q = pred[(p, t, x)]
                b = [float(v @ v - 2 * v @ ph[t] + 1) for v in q]
                ls = [float(-(ph[t] * np.log(np.maximum(v, .01) / np.maximum(v, .01).sum())).sum()) for v in q]
                S[(p, t, x)] = np.mean(b)
                CELLS.append(dict(setting=setting, setting_gpt=SET[("gpt", setting)], setting_opus=SET[("claude", setting)],
                                  array=x, family=fam(x), stratum=strat[x],
                                  sample=("primary: selected for cross-model divergence under LOW reasoning"
                                          if strat[x] != "S3" else "S3 shared-policy control"),
                                  predictor=NAME[p], target=NAME[t], self_cell=int(p == t), n_pred_parsed=len(q),
                                  brier_mean=np.mean(b), brier_sd=np.std(b, ddof=1), logscore_mean=np.mean(ls),
                                  n_scoring_draws_target=len(ref[(t, x)]), target_dist_fresh="/".join(f"{v:.4f}" for v in ph[t])))
        dG = S[("claude", "gpt", x)] - S[("gpt", "gpt", x)]; dO = S[("gpt", "claude", x)] - S[("claude", "claude", x)]
        ADV.append(dict(setting=setting, array=x, family=fam(x), stratum=strat[x],
                        sample=("primary: selected for cross-model divergence under LOW reasoning" if strat[x] != "S3"
                                else "S3 shared-policy control"),
                        D_pooled=(dG + dO) / 2, D_target_gpt=dG, D_target_opus=dO,
                        tvd_fresh=0.5 * float(np.abs(ph["gpt"] - ph["claude"]).sum()),
                        gpt_modal_share=float(ph["gpt"].max()), opus_modal_share=float(ph["claude"].max()),
                        same_modal=int(ph["gpt"].argmax() == ph["claude"].argmax()),
                        n_scoring_draws_gpt=len(ref[("gpt", x)]), n_scoring_draws_opus=len(ref[("claude", x)])))


crossed(lo_b, "low", "target")
crossed([r for r in hi_rows if r["array"] in strat], "high", "focal")
for name, rows, cols_ in (("crossed_prediction_cells.csv", CELLS, None), ("self_advantage_items.csv", ADV, None)):
    with open(os.path.join(OUT, name), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader()
        for r in rows:
            w.writerow({k: (round(v, 6) if isinstance(v, float) else v) for k, v in r.items()})
for setting, path in (("low", os.path.join(S1B, "analysis", "out", "item_table.csv")),
                      ("high", os.path.join(HI, "analysis", "out_1b", "item_table.csv"))):
    T = {r["array"]: r for r in rd(path)}
    chk[f"1b_{setting}_max_abs_diff_vs_item_table"] = max(
        max(abs(a["D_pooled"] - float(T[a["array"]]["D_pooled"])), abs(a["D_target_gpt"] - float(T[a["array"]]["D_gpt"])),
            abs(a["D_target_opus"] - float(T[a["array"]]["D_opus"]))) for a in ADV if a["setting"] == setting)

# =========================================================================== annotation summary (copied)
lo1a = json.load(open(os.path.join(S1A, "analysis", "out", "results.json")))
hi1a = json.load(open(os.path.join(HI, "analysis", "out_1a", "results.json")))
lo1b = json.load(open(os.path.join(S1B, "analysis", "out", "results.json")))
hi1b = json.load(open(os.path.join(HI, "analysis", "out_1b", "results.json")))
q1 = json.load(open(os.path.join(PQ, "results", "study1_final_20261009", "summary.json")))
qa = json.load(open(os.path.join(AS, "full_result.json")))
pick = lambda r, m: dict(P1_mean_D=r[m]["P1"]["mean_D"], P1_ci=r[m]["P1"]["ci95"], P1_p=r[m]["P1"]["signflip_p"],
                         holm_P1=r["holm"][f"{m}:P1"], P2_self_slope=r[m]["P2_self"]["slope"],
                         P2_self_mse=r[m]["P2_self"]["mean_signed_error"], P2_aud_slope=r[m]["P2_auditor"]["slope"],
                         P2_aud_mse=r[m]["P2_auditor"]["mean_signed_error"])
summ = dict(
    cross_checks=chk,
    frontier_1a={s: {m: pick(r, m) for m in M} for s, r in (("low", lo1a), ("high", hi1a))},
    frontier_1a_glmm=dict(low_source=os.path.join(S1A, "analysis", "audit", "C_glm", "glmm_output.txt"),
                          low_text=open(os.path.join(S1A, "analysis", "audit", "C_glm", "glmm_output.txt")).read().strip().splitlines(),
                          high=hi1a["S1_glmm"]),
    frontier_1b={s: dict(primary_pooled=r["primary"]["pooled"], target_gpt=r["primary"]["target_gpt"],
                         target_opus=r["primary"]["target_opus"], S3_pooled=r.get("S3", {}).get("pooled"),
                         cell_mean_brier_primary=r["cell_mean_brier_primary"]) for s, r in (("low", lo1b), ("high", hi1b))},
    qwen_study1=dict(estimates=q1["estimates"], ci=q1["ci_95_scenario_bootstrap"], p=q1["p_permutation"],
                     denominators=q1["denominators"], group_agreement=q1["group_agreement"]),
    qwen_continuation_playpass=json.load(open(os.path.join(CP, "analysis", "playpass", "result.json"))),
    qwen_alpha_EXPLORATORY={k: qa[k] for k in qa if not isinstance(qa[k], (list,)) or len(str(qa[k])) < 400},
    qwen_choice_self_advantage="NOT AVAILABLE: no crossed object/option-choice predictions exist for Qwen (see QWEN_CROSSED_PROPOSAL.md)")
json.dump(summ, open(os.path.join(OUT, "panel_summary.json"), "w"), indent=1, default=float)
print(json.dumps(chk, indent=1))
import collections
print("reliability rows:", dict(collections.Counter((r["column"], r["setting"], r["sample_type"].split(" (")[0]) for r in REL)))
print("crossed cells:", len(CELLS), "| advantage rows:", dict(collections.Counter((a["setting"], a["stratum"] == "S3") for a in ADV)))
