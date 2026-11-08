"""Candidate inventory for the crossed object-level follow-up. Existing data only, no API calls.

Sources (plain reference choice, prompt d40ea45d, canonical object ids):
  FRAME   VIS-FRAME-41 frame run       GPT effort low | Opus thinking DISABLED | n=48   (41 arrays)
  PREFL   liveness preflight            GPT effort low | Opus thinking DISABLED | n~24   (~24 arrays)
  STAGEA  study2_4opt stage-A discovery GPT effort low | Opus thinking ADAPTIVE | n=24   (203 arrays)
  REMEAS  relational remeasure          GPT effort low | Opus thinking ADAPTIVE | n=100  (13 arrays)
Writes inventory.json + per_array.csv here.
"""
import glob, json, os
import numpy as np, pandas as pd

SC = os.path.expanduser("~/Desktop/Coordination/Self_Coordination")
SPC = f"{SC}/study_policy_convergence_20260909"
OUT = os.path.dirname(os.path.abspath(__file__))
rng = np.random.default_rng(20261009)
MID = {"gpt": "gpt-5.5-2026-04-23", "claude": "claude-opus-5"}

rows = []
fr = pd.read_csv(f"{SPC}/runs/visual_frame/visual_frame_20260909_204609.csv", low_memory=False)
fr = fr[(fr.parse_ok == 1) & fr.checkpoint_requested.isin(MID.values())]
for _, r in fr.iterrows():
    rows.append(("FRAME", "gpt" if r.checkpoint_requested.startswith("gpt") else "claude", r.array_id, int(r.canonical_index)))
for f in glob.glob(f"{SPC}/runs/liveness_preflight/visual_preflight_*.csv"):
    d = pd.read_csv(f)
    d = d[(d.parse_ok == 1) & d.checkpoint_requested.isin(MID.values())]
    for _, r in d.iterrows():
        rows.append(("PREFL", "gpt" if r.checkpoint_requested.startswith("gpt") else "claude", r.array_id, int(r.canonical_index)))
for f in glob.glob(f"{SC}/study2_4opt_20260830/data/stageA_discovery_*.csv"):
    d = pd.read_csv(f)
    d = d[(d.parse_ok == True) & d.chosen_item.notna()]
    for _, r in d.iterrows():
        rows.append(("STAGEA", r.model, r.stimulus_id, int(r.chosen_item)))
d = pd.read_csv(f"{SC}/study2_relational_prediction_20260912/results/remeasure_20260912_151751/data/parsed.csv")
d = d[(d.ok == True) & d.chosen_item.notna()]
for _, r in d.iterrows():
    rows.append(("REMEAS", r.actor, r.sid, int(r.chosen_item)))
D = pd.DataFrame(rows, columns=["src", "model", "array", "item"])
CONFIG = {("FRAME", "claude"): "disabled", ("PREFL", "claude"): "disabled",
          ("STAGEA", "claude"): "adaptive", ("REMEAS", "claude"): "adaptive"}
D["config"] = [CONFIG.get((s, m), "effort_low") for s, m in zip(D.src, D.model)]
stim = sorted(os.listdir(f"{SC}/study2_4opt_20260830/stimuli"))
stim = [s for s in stim if os.path.isdir(f"{SC}/study2_4opt_20260830/stimuli/{s}")]
F41 = set(pd.read_csv(f"{SPC}/audits/visual/recommended_frame_arrays.csv").query("frame_id=='VIS-FRAME-41'").array_id)


def counts(sub):
    return np.bincount(sub.item.values, minlength=4)


def wmm(c):
    c = np.asarray(c, float); n = c.sum()
    return float((c * (c - 1)).sum() / (n * (n - 1))) if n > 1 else np.nan


def summ(c):
    n = c.sum()
    return dict(n=int(n), counts=c.tolist(), modal=int(c.argmax()), modal_share=float(c.max() / n),
                tie=bool((c == c.max()).sum() > 1), wmm=wmm(c))


# per array x model x config-pool distributions
tab = {}
for (a, m, cfg), g in D.groupby(["array", "model", "config"]):
    tab[(a, m, cfg)] = summ(counts(g))
# also per source (for test-retest)
src_tab = {}
for (a, m, s), g in D.groupby(["array", "model", "src"]):
    src_tab[(a, m, s)] = summ(counts(g))

# ---------- 2. config transfer (Opus adaptive vs disabled) and GPT test-retest -----------
def compare(pairs):
    if not pairs:
        return {}
    A = [p[0] for p in pairs]; B = [p[1] for p in pairs]
    same = np.mean([a["modal"] == b["modal"] for a, b in pairs])
    ms_a = np.array([a["modal_share"] for a in A]); ms_b = np.array([b["modal_share"] for b in B])
    w_a = np.array([a["wmm"] for a in A]); w_b = np.array([b["wmm"] for b in B])
    # share the disabled distribution gives to the adaptive modal object
    p_x = np.mean([b["counts"][a["modal"]] / b["n"] for a, b in pairs])
    return dict(n_arrays=len(pairs), same_modal=float(same), r_modal_share=float(np.corrcoef(ms_a, ms_b)[0, 1]),
                r_wmm=float(np.corrcoef(w_a, w_b)[0, 1]), mean_abs_diff_wmm=float(np.abs(w_a - w_b).mean()),
                mean_signed_wmm_second_minus_first=float((w_b - w_a).mean()),
                mean_share_on_first_modal=float(p_x))


arrays = sorted(set(D.array))
opus_pairs = [(tab[(a, "claude", "adaptive")], tab[(a, "claude", "disabled")]) for a in arrays
              if (a, "claude", "adaptive") in tab and (a, "claude", "disabled") in tab]
gpt_pairs = [(src_tab[(a, "gpt", "STAGEA")], tab_ := src_tab.get((a, "gpt", "FRAME")) or src_tab.get((a, "gpt", "PREFL")))
             for a in arrays if (a, "gpt", "STAGEA") in src_tab and ((a, "gpt", "FRAME") in src_tab or (a, "gpt", "PREFL") in src_tab)]
# Opus disabled test-retest (FRAME vs PREFL on overlap)
opus_dd = [(src_tab[(a, "claude", "PREFL")], src_tab[(a, "claude", "FRAME")]) for a in arrays
           if (a, "claude", "PREFL") in src_tab and (a, "claude", "FRAME") in src_tab]
transfer = dict(opus_adaptive_vs_disabled=compare(opus_pairs), gpt_stageA_vs_frame_or_prefl=compare(gpt_pairs),
                opus_disabled_prefl_vs_frame=compare(opus_dd))

# null for same-modal/abs-diff expected from sampling alone (Opus disabled distribution resampled at n=24 vs itself)
def sampling_null(pairs, n1=24, B=500):
    sm, ad = [], []
    for _ in range(B):
        s, a_ = [], []
        for _, b in pairs:
            p = (np.array(b["counts"]) + .5) / (b["n"] + 2)
            c1 = rng.multinomial(n1, p); c2 = rng.multinomial(b["n"], p)
            s.append(c1.argmax() == c2.argmax()); a_.append(abs(wmm(c1) - wmm(c2)))
        sm.append(np.mean(s)); ad.append(np.mean(a_))
    return {"same_modal_null_mean": float(np.mean(sm)), "same_modal_null_2.5pct": float(np.quantile(sm, .025)),
            "abs_diff_wmm_null_mean": float(np.mean(ad)), "abs_diff_wmm_null_97.5pct": float(np.quantile(ad, .975))}


transfer["opus_sampling_null_if_no_config_effect"] = sampling_null(opus_pairs) if opus_pairs else {}
transfer["gpt_sampling_null"] = sampling_null(gpt_pairs) if gpt_pairs else {}


# ---------- 3. stratum counts --------------------------------------------------------
def best(a, m, allow_adaptive):
    """Best available distribution: GPT pools all (same config); Opus disabled, else adaptive if allowed."""
    if m == "gpt":
        sub = D[(D.array == a) & (D.model == "gpt")]
        return (summ(counts(sub)), "effort_low") if len(sub) else (None, None)
    if (a, "claude", "disabled") in tab:
        return tab[(a, "claude", "disabled")], "disabled"
    if allow_adaptive and (a, "claude", "adaptive") in tab:
        return tab[(a, "claude", "adaptive")], "adaptive"
    return None, None


THRESH = {"T75_ms50": dict(conc=("modal_share", .75), diff=("modal_share", .50)),
          "T80_ms50": dict(conc=("modal_share", .80), diff=("modal_share", .50)),
          "T80_w45": dict(conc=("modal_share", .80), diff=("wmm", .45)),
          "T90_ms55": dict(conc=("modal_share", .90), diff=("modal_share", .55))}


def label(s, th):
    k, v = th["conc"]; kd, vd = th["diff"]
    if s[k] >= v and not s["tie"]:
        return "C"
    if s[kd] <= vd:
        return "D"
    return "M"


def stratum(g, o, th):
    lg, lo = label(g, th), label(o, th)
    if lg == "C" and lo == "C":
        return "S1_opposing" if g["modal"] != o["modal"] else "S3_shared"
    if lg == "C" and lo == "D":
        return "S2_gptC_opusD"
    if lg == "D" and lo == "C":
        return "S2_opusC_gptD"
    return None


per = []
for a in stim:
    for allow in (False, True):
        g, _ = best(a, "gpt", allow); o, ocfg = best(a, "claude", allow)
        if g is None or o is None:
            continue
        rec = dict(array=a, family=a.rsplit("_m", 1)[0], in_F41=a in F41, nominate_with_adaptive=allow,
                   opus_config=ocfg, gpt_n=g["n"], opus_n=o["n"], gpt_modal=g["modal"], opus_modal=o["modal"],
                   gpt_ms=round(g["modal_share"], 3), opus_ms=round(o["modal_share"], 3),
                   gpt_wmm=round(g["wmm"], 3), opus_wmm=round(o["wmm"], 3),
                   gpt_counts=g["counts"], opus_counts=o["counts"])
        for tn, th in THRESH.items():
            rec[tn] = stratum(g, o, th)
        per.append(rec)
P = pd.DataFrame(per)
P.to_csv(f"{OUT}/per_array.csv", index=False)
strata_counts = {}
for allow in (False, True):
    sub = P[P.nominate_with_adaptive == allow]
    key = "adaptive_nomination" if allow else "frame_config_only"
    strata_counts[key] = {"n_arrays_with_both_models": int(len(sub))}
    for tn in THRESH:
        vc = sub[tn].value_counts().to_dict()
        fam = sub.dropna(subset=[tn]).groupby(tn).family.nunique().to_dict()
        f41 = sub[sub.in_F41].dropna(subset=[tn]).groupby(tn).size().to_dict()
        maxfam = sub.dropna(subset=[tn]).groupby([tn, "family"]).size().groupby(level=0).max().to_dict()
        strata_counts[key][tn] = {s: dict(n=int(vc.get(s, 0)), families=int(fam.get(s, 0)),
                                          from_F41=int(f41.get(s, 0)), max_per_family=int(maxfam.get(s, 0)))
                                  for s in ["S1_opposing", "S2_gptC_opusD", "S2_opusC_gptD", "S3_shared"]}


# ---------- 4. misclassification / regression to the mean ------------------------------
def flip_prob(c, th, n_new, B=400, who=None):
    """P(label on fresh n_new draws != label on current) under Dirichlet(c+.5) posterior."""
    s = summ(np.array(c)); lab = label(s, th)
    flips = 0
    for _ in range(B):
        p = rng.dirichlet(np.array(c) + .5)
        c2 = rng.multinomial(n_new, p); s2 = summ(c2)
        flips += label(s2, th) != lab or (lab == "C" and s2["modal"] != s["modal"])
    return flips / B


th = THRESH["T80_ms50"]
nom = P[P.nominate_with_adaptive == True].dropna(subset=["T80_ms50"])
flip = []
for _, r in nom.iterrows():
    fg = flip_prob(r.gpt_counts, th, 48); fo = flip_prob(r.opus_counts, th, 48)
    flip.append(dict(array=r.array, stratum=r.T80_ms50, opus_config=r.opus_config, gpt_n=r.gpt_n, opus_n=r.opus_n,
                     p_flip_gpt=fg, p_flip_opus=fo, p_keep_both=(1 - fg) * (1 - fo)))
FL = pd.DataFrame(flip)
FL.to_csv(f"{OUT}/flip_risk_T80_ms50.csv", index=False)
flip_summary = FL.groupby(["stratum", "opus_config"]).agg(n=("array", "size"), mean_p_keep_both=("p_keep_both", "mean"),
                                                          n_keep_ge_80=("p_keep_both", lambda x: int((x >= .8).sum()))).reset_index()

# regression to the mean: arrays with BOTH stage-A (n=24) and frame (n=48) GPT data; select extremes on stage-A
rtm = {}
for m, cfg_first, cfg_second in (("gpt", "STAGEA", "FRAME"), ("claude", "PREFL", "FRAME")):
    xs, ys = [], []
    for a in arrays:
        if (a, m, cfg_first) in src_tab and (a, m, cfg_second) in src_tab:
            xs.append(src_tab[(a, m, cfg_first)]["modal_share"]); ys.append(src_tab[(a, m, cfg_second)]["modal_share"])
    xs, ys = np.array(xs), np.array(ys)
    if len(xs) > 5:
        hi, lo = xs >= .80, xs <= .50
        rtm[f"{m}_{cfg_first}_to_{cfg_second}"] = dict(n=len(xs), sel_conc_n=int(hi.sum()),
                                                       conc_first=float(xs[hi].mean()) if hi.any() else None,
                                                       conc_second=float(ys[hi].mean()) if hi.any() else None,
                                                       sel_diff_n=int(lo.sum()),
                                                       diff_first=float(xs[lo].mean()) if lo.any() else None,
                                                       diff_second=float(ys[lo].mean()) if lo.any() else None)
# simulated RTM at n=24 selection, n=48 fresh, using frame distributions as truth
sim = []
for m in MID:
    truth = [np.array(tab[(a, m, "disabled" if m == "claude" else "effort_low")]["counts"]) for a in F41
             if (a, m, "disabled" if m == "claude" else "effort_low") in tab]
    sel_c, fresh_c, sel_d, fresh_d = [], [], [], []
    for _ in range(300):
        for c in truth:
            p = rng.dirichlet(c + .5)
            a1 = rng.multinomial(24, p); a2 = rng.multinomial(48, p)
            if a1.max() / 24 >= .8:
                sel_c.append(a1.max() / 24); fresh_c.append(a2[a1.argmax()] / 48)
            if a1.max() / 24 <= .5:
                sel_d.append(a1.max() / 24); fresh_d.append(a2.max() / 48)
    sim.append(dict(model=m, conc_sel=float(np.mean(sel_c)), conc_fresh_same_object=float(np.mean(fresh_c)),
                    diff_sel=float(np.mean(sel_d)), diff_fresh=float(np.mean(fresh_d))))

out = dict(sources={s: {m: int(((D.src == s) & (D.model == m)).sum()) for m in MID} for s in D.src.unique()},
           arrays_per_source={s: {m: int(D[(D.src == s) & (D.model == m)].array.nunique()) for m in MID} for s in D.src.unique()},
           n_stimuli=len(stim), transfer=transfer, strata_counts=strata_counts,
           flip_summary_T80_ms50=flip_summary.to_dict("records"), rtm_observed=rtm, rtm_simulated=sim)
json.dump(out, open(f"{OUT}/inventory.json", "w"), indent=1, default=float)
print(json.dumps(out, indent=1, default=float))
