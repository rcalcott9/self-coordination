"""Study 1b, high reasoning: existing primary analysis (study1b_crossed_object_20261007/code/analyze.py) on the
ORIGINAL selected arrays (no reselection), scored on fresh high-reasoning REF draws (48/model/array).

Primary: pooled self-minus-cross Brier advantage on the original 10 divergent arrays (S1, S2_G, S2_O)
  D_j = 0.5*[(B_O->G + B_G->O) - (B_G->G + B_O->O)], two-sided array sign-flip (10,000 simulated flips,
  p=(k+1)/(B+1)) + exact enumeration; array bootstrap CI. Target-specific (Holm over 2).
Secondary: S3 controls; strata; log score; family-level aggregation; CURRENT divergence of the original arrays
  under high reasoning (TVD, modal shares, whether each array still meets its original stratum definition) -
  descriptive only, arrays are not reselected. Exclusion rule unchanged: any cell < 6/8 parsed.

  python code/analyze_1b.py [--runs runs|runs_mock]
"""
import argparse, csv, glob, itertools, json, os
import numpy as np

ap = argparse.ArgumentParser(); ap.add_argument("--runs", default="runs"); a = ap.parse_args()
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "analysis", "out_1b" + ("_mock" if a.runs != "runs" else "")); os.makedirs(OUT, exist_ok=True)
F = json.load(open(os.path.join(ROOT, "design", "FROZEN.json")))
FSHA = open(os.path.join(ROOT, "design", "FROZEN.sha256")).read().split()[0][:8]
M = ["gpt", "claude"]; G, O = "gpt", "claude"
B_FLIP, B_BOOT = 10000, 10000
rng = np.random.default_rng(20261009)
ARR = F["arrays_1b"]; strat = {x: s for s, v in F["strata_1b"].items() for x in v}
SEL = json.load(open(os.path.join(os.path.dirname(ROOT), "study1b_crossed_object_20261007", "design", "SELECTION.json")))
cfg = SEL["config"]

rows = [r for f in glob.glob(os.path.join(ROOT, a.runs, "main", "*.csv")) for r in csv.DictReader(open(f))
        if r["frozen_sha8"] == FSHA]
ref = {(m, x): [] for m in M for x in ARR}
pred = {(p, t, x): [] for p in M for t in M for x in ARR}
integ = {}
for r in rows:
    if r["array"] not in ARR or r["task"] not in ("REF", "PRED"):
        continue
    k = f"{r['task']}|{r['answerer']}->{r['focal']}"
    d = integ.setdefault(k, dict(rows=0, transport_ok=0, parsed=0, mismatch=0, cost=0.0))
    d["rows"] += 1; d["transport_ok"] += r["transport_ok"] == "1"; d["parsed"] += r["parse_ok"] == "1"
    d["mismatch"] += r["transport_ok"] == "1" and r["model_match"] != "1"; d["cost"] += float(r["cost_usd"] or 0)
    if r["parse_ok"] != "1":
        continue
    if r["task"] == "REF":
        ref[(r["answerer"], r["array"])].append(int(r["canonical_choice"]))
    else:
        pred[(r["answerer"], r["focal"], r["array"])].append(np.array(json.loads(r["p_canonical"])))

excluded = [x for x in ARR if any(len(pred[(p, t, x)]) < 6 for p in M for t in M) or any(len(ref[(m, x)]) < 24 for m in M)]
arrays = [x for x in ARR if x not in excluded]
PH = {(m, x): np.bincount(ref[(m, x)], minlength=4) / len(ref[(m, x)]) for m in M for x in arrays}
brier = lambda q, ph: float(q @ q - 2 * q @ ph + 1)
logscore = lambda q, ph: float(-(ph * np.log(np.maximum(q, .01) / np.maximum(q, .01).sum())).sum())


def cells(score, P):
    return {(p, t, x): np.mean([score(q, PH[(t, x)]) for q in P[(p, t, x)]]) for p in M for t in M for x in arrays}


def contrasts(S, xs):
    dG = np.array([S[(O, G, x)] - S[(G, G, x)] for x in xs]); dO = np.array([S[(G, O, x)] - S[(O, O, x)] for x in xs])
    return dict(pooled=(dG + dO) / 2, target_gpt=dG, target_opus=dO,
                predictor_effect=np.array([.5 * ((S[(G, G, x)] + S[(G, O, x)]) - (S[(O, G, x)] + S[(O, O, x)])) for x in xs]),
                target_effect=np.array([.5 * ((S[(G, G, x)] + S[(O, G, x)]) - (S[(G, O, x)] + S[(O, O, x)])) for x in xs]))


def signflip(v):
    v = np.asarray(v); fl = rng.choice([-1, 1], size=(B_FLIP, len(v)))
    k = int(np.sum(np.abs((fl * v).mean(1)) >= abs(v.mean()) - 1e-12)); return (k + 1) / (B_FLIP + 1), k


def exact(v):
    v = np.asarray(v); obs = abs(v.mean()) - 1e-12
    if len(v) > 16:
        return None
    pats = np.array(list(itertools.product([-1, 1], repeat=len(v))))
    return float(np.mean(np.abs((pats * v).mean(1)) >= obs))


def boot_ci(v):
    v = np.asarray(v); m = v[rng.integers(0, len(v), size=(B_BOOT, len(v)))].mean(1)
    return [float(np.quantile(m, .025)), float(np.quantile(m, .975))]


def summarize(v):
    p, k = signflip(v)
    return dict(n=len(v), mean=float(np.mean(v)), ci95=boot_ci(v), signflip_p=p, exact_p=exact(v), k_exceed=k,
                n_pos=int((np.asarray(v) > 0).sum()), n_neg=int((np.asarray(v) < 0).sum()))


S = cells(brier, pred)
prim = [x for x in arrays if x in F["primary_1b"]]; s3 = [x for x in arrays if strat[x] == "S3"]
R = dict(frozen_sha8=FSHA, integrity=integ, excluded=excluded, n_primary=len(prim), n_S3=len(s3),
         n_ref={f"{m}|{x}": len(ref[(m, x)]) for m in M for x in ARR})
C1 = contrasts(S, prim)
R["primary"] = {k: summarize(v) for k, v in C1.items()}
ps = [R["primary"]["target_gpt"]["signflip_p"], R["primary"]["target_opus"]["signflip_p"]]
o = np.argsort(ps); holm = [0, 0]
holm[o[0]] = min(1, 2 * ps[o[0]]); holm[o[1]] = min(1, max(holm[o[0]], ps[o[1]]))
R["primary"]["target_gpt"]["holm_p"], R["primary"]["target_opus"]["holm_p"] = holm
R["cell_mean_brier_primary"] = {f"{p}->{t}": float(np.mean([S[(p, t, x)] for x in prim])) for p in M for t in M}
if s3:
    C3 = contrasts(S, s3); R["S3"] = {k: summarize(C3[k]) for k in ("pooled", "target_gpt", "target_opus")}
R["by_stratum"] = {s: {k: dict(n=len(xs), mean=float(contrasts(S, xs)[k].mean())) for k in ("pooled", "target_gpt", "target_opus")}
                   for s in ("S1", "S2_G", "S2_O", "S3") for xs in [[x for x in arrays if strat[x] == s]] if xs}
SL = cells(logscore, pred); R["sensitivity_logscore_pooled"] = summarize(contrasts(SL, prim)["pooled"])
fam = {}
for i, x in enumerate(prim):
    fam.setdefault(x.rsplit("_m", 1)[0], []).append(C1["pooled"][i])
fv = np.array([np.mean(v) for v in fam.values()])
R["sensitivity_family_level"] = dict(n_families=len(fv), **summarize(fv))

# current divergence of the ORIGINAL arrays under high reasoning (descriptive; no reselection)
div = {}
for x in arrays:
    pg, po = PH[(G, x)], PH[(O, x)]
    mg, mo = int(pg.argmax()), int(po.argmax())
    conc = lambda p: p.max() >= cfg["conc_min_modal_share"]; diff = lambda p: p.max() <= cfg["diffuse_max_modal_share"]
    now = ("S1" if conc(pg) and conc(po) and mg != mo else "S2_G" if conc(pg) and diff(po) else
           "S2_O" if conc(po) and diff(pg) else "S3" if conc(pg) and conc(po) and mg == mo else "other")
    orig = SEL["per_array"] if isinstance(SEL["per_array"], dict) else None
    div[x] = dict(stratum_original=strat[x], stratum_now_strict=now, tvd=float(.5 * np.abs(pg - po).sum()),
                  gpt_modal_share=float(pg.max()), opus_modal_share=float(po.max()), same_modal=mg == mo,
                  gpt_dist=np.round(pg, 3).tolist(), opus_dist=np.round(po, 3).tolist())
R["current_divergence"] = div
R["current_divergence_summary"] = dict(
    primary_mean_tvd=float(np.mean([div[x]["tvd"] for x in prim])), s3_mean_tvd=float(np.mean([div[x]["tvd"] for x in s3])) if s3 else None,
    primary_still_meeting_original_stratum=int(sum(div[x]["stratum_now_strict"] == div[x]["stratum_original"] for x in prim)),
    primary_same_modal=int(sum(div[x]["same_modal"] for x in prim)))
with open(os.path.join(OUT, "item_table.csv"), "w", newline="") as fh:
    w = csv.writer(fh)
    call = contrasts(S, arrays)
    w.writerow(["array", "family", "stratum", "stratum_now_strict", "tvd_high", "gpt_high", "opus_high"] +
               [f"B_{p}->{t}" for p in M for t in M] + ["D_pooled", "D_gpt", "D_opus"])
    for i, x in enumerate(arrays):
        w.writerow([x, x.rsplit("_m", 1)[0], strat[x], div[x]["stratum_now_strict"], round(div[x]["tvd"], 4),
                    div[x]["gpt_dist"], div[x]["opus_dist"]] + [round(S[(p, t, x)], 4) for p in M for t in M] +
                   [round(call["pooled"][i], 4), round(call["target_gpt"][i], 4), round(call["target_opus"][i], 4)])
json.dump(R, open(os.path.join(OUT, "results.json"), "w"), indent=1, default=float)
print(json.dumps({k: R[k] for k in ("primary", "cell_mean_brier_primary", "current_divergence_summary")}, indent=1, default=float))
print("excluded:", excluded, "| out:", OUT)
