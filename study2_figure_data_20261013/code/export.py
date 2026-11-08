#!/usr/bin/env python3
"""Study 2 figure inputs (primary configurations only), rebuilt from the raw run files. No API calls.

Primary: GPT-5.5 effort low; Claude Opus 5 adaptive thinking, effort low; Qwen step-316 thinking off, run B
(plunkett_qwen/results/s2_20260912_181428). Relational G: GPT-5.5 effort low and Opus 5 adaptive low focal.

Writes data/:
  playpass_items_long.csv     model x item x partner: attempted / parsed / PLAY counts, agreement, group, config
  playpass_items_paired.csv   model x item, COPY and DIFFERENT side by side (pairing preserved)
  playpass_qwen_option_pairs.csv  Qwen run B scenario x option pair x partner (the within-scenario sampling unit)
  playpass_cells.csv          figure cell means + CIs (copied from paper_assembly study2_freeze.py output)
  playpass_contrasts_harmonised.csv  same source, primary configurations
  playpass_contrasts_frozen.csv      frozen-report contrasts, with their original resampling methods
  relational_G_items.csv      11 items x 2 focal models
  relational_G_summary.csv    G with item-clustered and family-clustered CIs (frozen code, reproduced), plus
                              the F10-collapsed family-means sensitivity and the figure's harmonised recomputation
  model_configs.csv
Every table is checked against the frozen or figure values before anything is written.
"""
import json, random, shutil, statistics as st
from collections import defaultdict
from pathlib import Path
import numpy as np, pandas as pd

OUT = Path(__file__).resolve().parent.parent / "data"; OUT.mkdir(exist_ok=True)
SC = Path.home() / "Desktop/Coordination/Self_Coordination"; ST = Path.home() / "Desktop/Superrationality/Stag"
PA = SC / "paper_assembly_20261010"
CFG = {"GPT-5.5": "effort low", "Claude Opus 5": "adaptive, effort low", "Qwen step-316": "thinking off"}

# ------------------------------------------------------------------ PLAY/PASS trials (all attempted rows)
rows = []
G = SC / "study_playpass_gpt/data"
for part, fn in (("COPY", "playpass_full_20260912_191607.csv"), ("DIFFERENT", "playpass_full_different_low_20260912_195055.csv")):
    t = pd.read_csv(G / fn)
    assert set(t.model_returned.dropna()) == {"gpt-5.5-2026-04-23"}
    for r in t.itertuples():
        rows.append(dict(model="GPT-5.5", item=r.array, family=r.family, agreement=r.agreement, group=r.arm,
                         partner=part, attempted=1, transport_ok=int(r.transport_ok), parsed=int(r.parse_ok == 1),
                         play=int(r.parse_ok == 1 and r.decision == "PLAY"), source=f"study_playpass_gpt/data/{fn}",
                         prompt_sha8=r.prompt_sha8))
OP = ST / "opus_playpass/results"
for part, d in (("COPY", "parallel_20260912_191415"), ("DIFFERENT", "pp_different_adaptive_efflow_20260912_200226")):
    assert not (OP / d / "CONTAMINATED_BUGGY_REFERENT.txt").exists()
    for r in json.load(open(OP / d / "raw_rows.json")):
        ok = bool(r["decision"])
        rows.append(dict(model="Claude Opus 5", item=r["item"], family=r["family"], agreement=r["agreement"],
                         group=r["group"], partner=part, attempted=1, transport_ok=1, parsed=int(ok),
                         play=int(ok and r["decision"] == "PLAY"), source=f"Stag/opus_playpass/results/{d}/raw_rows.json",
                         prompt_sha8=""))
QB = ST / "plunkett_qwen/results/s2_20260912_181428"
q = [json.loads(l) for l in open(QB / "raw/s2_trials.jsonl")]
for r in q:
    ok = r["decision"] in ("PLAY", "PASS")
    rows.append(dict(model="Qwen step-316", item=r["scenario"], family=r["scenario"], agreement=r["agreement"],
                     group="HIGH" if r["arm"] == "PLAY_correct" else "LOW", partner=r["partner"], attempted=1, transport_ok=1,
                     parsed=int(ok), play=int(ok and r["decision"] == "PLAY"),
                     source="Stag/plunkett_qwen/results/s2_20260912_181428/raw/s2_trials.jsonl", prompt_sha8="",
                     option_pair_index=r["option_pair_index"]))
T = pd.DataFrame(rows)
T["config"] = T.model.map(CFG)
T["group_label"] = np.where(T.model == "Qwen step-316", T.group.map({"HIGH": "CLEAR", "LOW": "WEAK"}), T.group)

key = ["model", "config", "item", "family", "group", "group_label", "agreement", "partner"]
L = T.groupby(key, sort=False).agg(n_attempted=("attempted", "sum"), n_transport_ok=("transport_ok", "sum"),
                                   n_parsed=("parsed", "sum"), n_play=("play", "sum"), source=("source", "first"),
                                   prompt_sha8=("prompt_sha8", "first")).reset_index()
L["p_play"] = L.n_play / L.n_parsed
assert L.groupby(["model", "item", "partner"]).size().max() == 1, "agreement or group not constant within item"

# ---- checks against the figure's trial table (parsed rows only) and frozen collection counts
FT = pd.read_csv(PA / "tables/study2_playpass_trials.csv")
FT = FT[FT.status == "frozen primary"].groupby(["model", "item", "partner"]).play.agg(["sum", "size"])
mine = L.set_index(["model", "item", "partner"])[["n_play", "n_parsed"]]
assert (FT.reindex(mine.index).values == mine.values).all(), "item counts differ from paper_assembly trials table"
cnt = L.groupby(["model", "group", "partner"])[["n_attempted", "n_parsed"]].sum()
assert (cnt.loc["GPT-5.5"].values == 300).all() and (cnt.loc["Claude Opus 5"].values == 300).all()
assert cnt.loc["Qwen step-316"].n_attempted.eq(300).all()
assert list(cnt.loc["Qwen step-316"].n_parsed) == [298, 295, 296, 297]  # HIGH-COPY, HIGH-DIFF, LOW-COPY, LOW-DIFF
assert L.groupby("model").item.nunique().eq(30).all()

L.drop(columns=["prompt_sha8"]).to_csv(OUT / "playpass_items_long.csv", index=False)

W = L.pivot_table(index=["model", "config", "item", "family", "group", "group_label", "agreement"], columns="partner",
                  values=["n_attempted", "n_parsed", "n_play", "p_play"], aggfunc="first")
W.columns = [f"{v}_{p.lower()}" for v, p in W.columns]
W = W.reset_index()
W["partner_shift"] = W.p_play_copy - W.p_play_different
assert W.notna().all().all() and len(W) == 90

# paired item-level check: pooled partner shift equals the figure contrast
FC = pd.read_csv(PA / "tables/study2_playpass_contrasts.csv")
for m in CFG:
    w = W[W.model == m]
    est = w.n_play_copy.sum() / w.n_parsed_copy.sum() - w.n_play_different.sum() / w.n_parsed_different.sum()
    ref = FC[(FC.model == m) & (FC.config == CFG[m]) & (FC.contrast == "partner shift, all items")].estimate.iloc[0]
    assert abs(est - ref) < 1e-12, (m, est, ref)
W.to_csv(OUT / "playpass_items_paired.csv", index=False)

Qp = T[T.model == "Qwen step-316"].groupby(["item", "group_label", "agreement", "option_pair_index", "partner"]).agg(
    n_attempted=("attempted", "sum"), n_parsed=("parsed", "sum"), n_play=("play", "sum")).reset_index()
Qp.rename(columns={"item": "scenario"}).to_csv(OUT / "playpass_qwen_option_pairs.csv", index=False)

# ------------------------------------------------------------------ cell means + contrasts
cells = pd.read_csv(PA / "tables/study2_playpass_cells.csv")
cells = cells[cells.status == "frozen primary"].copy()
for r in cells.itertuples():
    s = L[(L.model == r.model) & (L.group == r.cls) & (L.partner == r.partner)]
    assert abs(s.n_play.sum() / s.n_parsed.sum() - r.p_play) < 1e-12 and s.n_parsed.sum() == r.n_trials
cells["group_label"] = np.where(cells.model == "Qwen step-316", cells.cls.map({"HIGH": "CLEAR", "LOW": "WEAK"}), cells.cls)
cells["ci_method"] = ("item-cluster percentile bootstrap within class x partner, 10,000 resamples, seed 20261010 "
                      "(Qwen: scenario = item); P(PLAY) pools parsed trials")
cells["source"] = "paper_assembly_20261010/code/study2_freeze.py -> tables/study2_playpass_cells.csv (plotted in fig_study2 a-c)"
cells.to_csv(OUT / "playpass_cells.csv", index=False)

hc = FC[FC.status == "frozen primary"].copy()
hc["ci_method"] = ("paired item-cluster percentile bootstrap (items resampled within class, both partner cells kept "
                   "together), 10,000, seed 20261010")
hc["status"] = "sensitivity (harmonised re-analysis, 2026-10-13); point estimates reproduce the frozen reports"
hc.to_csv(OUT / "playpass_contrasts_harmonised.csv", index=False)

# frozen contrasts, transcribed from METHODS_RESULTS_DRAFT.md Table S2 (sources G1, O1, Q1)
FZ = [
    ("GPT-5.5", "partner (COPY - DIFFERENT), all items", .140, .093, .188, "item-paired bootstrap, 20,000; Wilcoxon p", "G1"),
    ("GPT-5.5", "policy (HIGH - LOW), COPY", .380, .220, .543, "item bootstrap", "G1"),
    ("GPT-5.5", "policy (HIGH - LOW), DIFFERENT", .453, .290, .613, "item bootstrap", "G1"),
    ("GPT-5.5", "interaction (LOW shift - HIGH shift)", .0733, -.020, .167, "item drops resampled within class; Mann-Whitney p .157", "G1"),
    ("Claude Opus 5", "partner (COPY - DIFFERENT), all items", .155, .025, .292,
     "unpaired item bootstrap (separate item draw per partner), 20,000", "O1"),
    ("Claude Opus 5", "policy (HIGH - LOW), COPY", .190, .080, .310, "item bootstrap; point frozen (O1), CI from S", "O1, S"),
    ("Claude Opus 5", "policy (HIGH - LOW), DIFFERENT", .453, .283, .620, "item bootstrap; point frozen (O1), CI from S", "O1, S"),
    ("Claude Opus 5", "interaction (LOW shift - HIGH shift)", .263, .057, .463, "unpaired item bootstrap, 20,000", "O1"),
    ("Qwen step-316", "partner (COPY - DIFFERENT), all items", .155, .103, .206, "scenario-cluster bootstrap; scenario sign-flip p", "Q1"),
    ("Qwen step-316", "policy (CLEAR - WEAK), COPY", .133, .029, .247, "scenario-cluster bootstrap", "Q1"),
    ("Qwen step-316", "policy (CLEAR - WEAK), DIFFERENT", .193, .075, .309, "scenario-cluster bootstrap", "Q1"),
    ("Qwen step-316", "interaction (LOW shift - HIGH shift), sign converted from frozen -.059", .059, -.044, .157,
     "scenario-cluster bootstrap; class-label permutation p .26", "Q1"),
]
SRC = {"G1": "study_playpass_gpt/results/{RESULT.md, partner_x_effort_REPORT.txt}",
       "O1": "Stag/opus_playpass/results/REPORT_2x2.txt", "Q1": "Stag/plunkett_qwen/QWEN_STUDY2_RESULT.md",
       "O1, S": "Stag/opus_playpass/results/REPORT_2x2.txt; paper_assembly_20261010/tables/study2_sensitivity.json"}
fz = pd.DataFrame(FZ, columns=["model", "contrast", "estimate", "ci_lo", "ci_hi", "ci_method", "source_key"])
fz.insert(1, "config", fz.model.map(CFG)); fz["source"] = fz.source_key.map(SRC)
fz["planning_status"] = np.where(fz.model == "Qwen step-316", "planned: PI instruction", "not planned in advance")
# point estimates must match the harmonised recomputation from the raw trials
hmap = {"partner (COPY": "partner shift, all items", "policy (HIGH - LOW), COPY": "policy effect (HIGH-LOW), COPY",
        "policy (HIGH - LOW), DIFFERENT": "policy effect (HIGH-LOW), DIFFERENT",
        "policy (CLEAR - WEAK), COPY": "policy effect (HIGH-LOW), COPY",
        "policy (CLEAR - WEAK), DIFFERENT": "policy effect (HIGH-LOW), DIFFERENT",
        "interaction": "interaction (LOW shift - HIGH shift)"}
for r in fz.itertuples():
    k = next(v for p, v in hmap.items() if r.contrast.startswith(p))
    e = hc[(hc.model == r.model) & (hc.contrast == k)].estimate.iloc[0]
    assert abs(e - r.estimate) < .0015, (r.model, r.contrast, e)
fz.to_csv(OUT / "playpass_contrasts_frozen.csv", index=False)

# ------------------------------------------------------------------ relational G
RP = SC / "study2_relational_prediction_20260912"
R = json.load(open(RP / "results/run_20260912_154308/report_rows.json"))


def ci(vals, groups, B=4000, seed=7):  # verbatim logic of report_study2.py ci(): cluster bootstrap, pooled item mean
    g = defaultdict(list)
    for v, k in zip(vals, groups):
        g[k].append(v)
    ks = list(g); rng = random.Random(seed); out = []
    for _ in range(B):
        out.append(st.mean([x for _ in ks for x in g[ks[rng.randrange(len(ks))]]]))
    out.sort(); return out[int(.025 * B)], out[int(.975 * B)]


FROZ = {"gpt": dict(G=.0206, item=(-.015, .046), fam=(-.037, .043), f10=(.002, -.056, .040)),
        "claude": dict(G=-.0004, item=(-.056, .064), fam=(-.026, .039), f10=(.002, -.020, .031))}
NAME = {"gpt": "GPT-5.5", "claude": "Claude Opus 5"}
RCFG = {"gpt": "effort low", "claude": "adaptive, effort low"}
harm = pd.read_csv(PA / "tables/study2_relational_G_summary.csv")
summ = []
for foc in ("gpt", "claude"):
    g = [r for r in R if r["focal"] == foc]; Gv = [r["G"] for r in g]; f = FROZ[foc]
    lo, hi = ci(Gv, [r["stimulus_id"] for r in g]); flo, fhi = ci(Gv, [r["family"] for r in g], seed=8)
    byf = defaultdict(list)
    for r in g:
        byf[r["family"]].append(r["G"])
    fam = [st.mean(v) for v in byf.values()]; rng = random.Random(11); dr = sorted(
        st.mean(fam[rng.randrange(len(fam))] for _ in fam) for _ in range(4000))
    got = dict(G=st.mean(Gv), item=(lo, hi), fam=(flo, fhi), f10=(st.mean(fam), dr[100], dr[3899]))
    assert abs(got["G"] - f["G"]) < 5e-5
    for k in ("item", "fam"):
        assert all(abs(a - b) < 5e-4 for a, b in zip(got[k], f[k])), (foc, k, got[k])
    assert all(abs(a - b) <= 5e-4 + 1e-9 for a, b in zip(got["f10"], f["f10"])), (foc, got["f10"])
    base = dict(focal=NAME[foc], config=RCFG[foc], n_pos=sum(v > 0 for v in Gv))
    summ += [dict(base, estimate="G, mean over 11 items", n_units=11, units="items", G=got["G"], ci_lo=lo, ci_hi=hi,
                  ci_method="item-cluster percentile bootstrap, 4,000, Python random seed 7 (report_study2.py)",
                  status="frozen primary", source="study2_relational_prediction_20260912/RESULTS.md (R1)"),
             dict(base, estimate="G, mean over 11 items", n_units=6, units="families (items pooled within drawn families)",
                  G=got["G"], ci_lo=flo, ci_hi=fhi,
                  ci_method="family-cluster percentile bootstrap: resample the 6 families, pool their items, take the item mean; "
                            "4,000, seed 8 (report_study2.py)",
                  status="frozen (reported in R1); METHODS draft lists it as a sensitivity, not planned in advance",
                  source="study2_relational_prediction_20260912/RESULTS.md (R1)"),
             dict(base, estimate="G, mean over 6 family means (F10 collapsed)", n_units=6, units="family means",
                  G=got["f10"][0], ci_lo=got["f10"][1], ci_hi=got["f10"][2], n_pos=sum(v > 0 for v in fam),
                  ci_method="percentile bootstrap of family means, 4,000, seed 11 (report_study2.py)",
                  status="sensitivity, not planned in advance", source="study2_relational_prediction_20260912/RESULTS.md (R1)")]
    for u, lab in (("items", "item-cluster"), ("families (F10 collapsed)", "family means")):
        h = harm[(harm.focal == NAME[foc]) & (harm.unit == u)].iloc[0]
        summ.append(dict(base, estimate=f"G, figure panel d ({u})", n_units=int(h.n), units=u, G=h.G, ci_lo=h.ci_lo,
                         ci_hi=h.ci_hi, n_pos=int(h.n_pos),
                         ci_method=f"{lab} percentile bootstrap, 10,000, numpy seed 20261010 (study2_freeze.py)",
                         status="harmonised recomputation; plotted in current fig_study2 (d)",
                         source="paper_assembly_20261010/tables/study2_relational_G_summary.csv"))
pd.DataFrame(summ).to_csv(OUT / "relational_G_summary.csv", index=False)
Ri = pd.DataFrame(R); Ri.insert(2, "focal_model", Ri.focal.map(NAME)); Ri.insert(3, "config", Ri.focal.map(RCFG))
Ri.to_csv(OUT / "relational_G_items.csv", index=False)

# ------------------------------------------------------------------ configurations
MC = [
    dict(model="GPT-5.5", config="effort low", role="PLAY/PASS 2x2 primary; relational focal",
         model_requested="gpt-5.5", model_returned="gpt-5.5-2026-04-23 (every call)", api="OpenAI Responses",
         reasoning="reasoning={effort: low, summary: auto}", temperature="not sent", max_tokens="not set",
         system_prompt="none", input="text + PNG of four-shape array, option order permuted per trial",
         prompt_sha8_copy="cbc2592c", prompt_sha8_different="60d134c1",
         runs="COPY playpass_full_20260912_191607; DIFFERENT playpass_full_different_low_20260912_195055",
         trials_per_item_per_cell=20, items="30 VIS-FRAME arrays, top/bottom 15 by own independent-order copy agreement",
         agreement_source="study_policy_convergence_20260909 stage1_frame, 48 draws, effort low (frozen items sha8 8ee3a56e)"),
    dict(model="Claude Opus 5", config="adaptive, effort low", role="PLAY/PASS 2x2 primary; relational focal",
         model_requested="claude-opus-5", model_returned="claude-opus-5", api="Anthropic Messages",
         reasoning="thinking={type: adaptive}, output_config={effort: low} (requested; API does not echo it)",
         temperature="not sent", max_tokens="4000 (runner source)", system_prompt="none",
         input="PNG + text, option order permuted per trial", prompt_sha8_copy="", prompt_sha8_different="",
         runs="COPY parallel_20260912_191415; DIFFERENT pp_different_adaptive_efflow_20260912_200226",
         trials_per_item_per_cell=20, items="30 VIS-FRAME arrays, top/bottom 15 by own independent-order copy agreement",
         agreement_source="frame calibration with thinking disabled, 48 draws (opus_playpass/design/FROZEN_ITEMS.json)"),
    dict(model="Qwen step-316", config="thinking off", role="PLAY/PASS 2x2 primary (run B)",
         model_requested="tinker://2d50363f-2bc8-5eed-af24-c4587089a565:train:0/sampler_weights/step316",
         model_returned="same", api="Tinker sampling", reasoning="renderer qwen3_5_disable_thinking",
         temperature="1.0", max_tokens="90",
         system_prompt="Your job is to make hypothetical decisions on behalf of different people or characters.",
         input="text; 5 fixed option pairs per scenario x 4 samples", prompt_sha8_copy="6b8026f5 (template sha16 prefix)",
         prompt_sha8_different="a86a2da2 (template sha16 prefix)", runs="s2_20260912_181428 (run B, 22:14 UTC)",
         trials_per_item_per_cell=20, items="Study 1 frozen 15 CLEAR / 15 WEAK scenarios",
         agreement_source="Study 1 selection draws, 40 per option pair (results/study1_frozen.json); same draws define the classes"),
]
pd.DataFrame(MC).to_csv(OUT / "model_configs.csv", index=False)

shutil.copy2(PA / "code/study2_freeze.py", OUT.parent / "code/plot_study2_CURRENT_study2_freeze.py")
print(cnt.to_string()); print(pd.DataFrame(summ)[["focal", "units", "G", "ci_lo", "ci_hi", "status"]].round(4).to_string())
print("all checks passed")
