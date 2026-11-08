#!/usr/bin/env python3
"""Study 2 labelled sensitivity checks (no API calls). Frozen primaries untouched.
(a) Legacy PLAY/PASS prompts describe a same-presentation game; labels used independent-order agreement.
    Recompute same-presentation agreement from the frame calibration (2 draws per ordering, 24 orderings).
(b) Opus 2x2 cells are thinking-adaptive but labels came from the thinking-disabled frame calibration.
    Recompute labels from adaptive Stage A agreement (n=24)."""
import json
from pathlib import Path
import numpy as np, pandas as pd
from scipy.stats import spearmanr
HERE = Path(__file__).resolve().parent.parent
SC = Path.home() / "Desktop/Coordination/Self_Coordination"; ST = Path.home() / "Desktop/Superrationality/Stag"
rng = np.random.default_rng(20261010)
F = pd.read_csv(SC / "study_policy_convergence_20260909/runs/visual_frame/visual_frame_20260909_204609.csv", low_memory=False)
F = F[F.parse_ok == 1]
CK = {"GPT-5.5": "gpt-5.5-2026-04-23", "Claude Opus 5": "claude-opus-5"}


def agreements(model):
    d = F[F.checkpoint_requested == CK[model]]
    rows = []
    for a, g in d.groupby("array_id"):
        k = g.canonical_index.value_counts().values; n = k.sum()
        ind = float((k * (k - 1)).sum() / (n * (n - 1)))
        same = g.groupby("presentation_id").canonical_index.agg(lambda s: float(s.iloc[0] == s.iloc[1]) if len(s) == 2 else np.nan)
        rows.append(dict(array=a, n=int(n), agree_indep=ind, agree_same=float(same.mean()), n_orderings=int(same.notna().sum())))
    return pd.DataFrame(rows).set_index("array")


def cluster_diff(t, lab):
    """HIGH-LOW P(PLAY) with item-cluster bootstrap CI."""
    it = t.groupby("item").agg(p=("play", "mean"), n=("play", "size")).join(lab)
    h, l = it[it.lab == "HIGH"], it[it.lab == "LOW"]
    def est(h, l): return np.average(h.p, weights=h.n) - np.average(l.p, weights=l.n)
    bs = [est(h.sample(len(h), replace=True, random_state=rng.integers(1e9)), l.sample(len(l), replace=True, random_state=rng.integers(1e9))) for _ in range(5000)]
    return dict(n_high=len(h), n_low=len(l), diff=float(est(h, l)), ci95=[float(np.quantile(bs, .025)), float(np.quantile(bs, .975))])


out, item_rows = {}, []
# ---------- load legacy cells ----------
cells = {}
G = SC / "study_playpass_gpt/data"
for eff, part, fn in (("low", "COPY", "playpass_full_20260912_191607.csv"), ("high", "COPY", "playpass_full_high_20260912_194050.csv"),
                      ("low", "DIFFERENT", "playpass_full_different_low_20260912_195055.csv"), ("high", "DIFFERENT", "playpass_full_different_high_20260912_210001.csv")):
    t = pd.read_csv(G / fn); t = t[t.parse_ok == 1].rename(columns={"array": "item", "arm": "group"})
    t["play"] = (t.decision == "PLAY").astype(int); cells[("GPT-5.5", eff, part)] = t
O = pd.read_csv(ST / "opus_playpass/results/opus_2x2_clean.csv")
for (eff, part), t in O.groupby(["effort", "partner"]): cells[("Claude Opus 5", eff, part)] = t
D = pd.read_csv(ST / "opus_playpass/results/parallel_disabled_20260912_191726/trials.csv")
cells[("Claude Opus 5", "disabled", "COPY")] = D

for model in CK:
    A = agreements(model)
    lab0 = {k: v for (m, *_), t in cells.items() if m == model for k, v in t.groupby("item").group.first().items()}
    items = sorted(lab0); A = A.loc[items]
    frozen = {k: v for (m, *_), t in cells.items() if m == model for k, v in t.groupby("item").agreement.first().items()}
    A["agree_frozen_label_source"] = pd.Series(frozen)
    A["label_frozen"] = pd.Series(lab0)
    # (a) relabel by same-presentation agreement: top/bottom 15 of the same 30 items
    # relabel only if the top-15 boundary is not inside a tie (else undefined; reported)
    srt = A.agree_same.sort_values(ascending=False).values
    same_defined = bool(srt[14] != srt[15])
    A["label_same"] = np.where(A.agree_same >= srt[14], "HIGH", "LOW") if same_defined else "UNDEFINED_TIE"
    res = dict(check_indep_reproduces_frozen_max_abs=float((A.agree_indep - A.agree_frozen_label_source).abs().max()),
               mean_agree_indep=A.groupby("label_frozen").agree_indep.mean().to_dict(),
               mean_agree_same=A.groupby("label_frozen").agree_same.mean().to_dict(),
               relabel_by_same_defined=same_defined, n_tied_at_boundary_same=int((A.agree_same == srt[14]).sum()),
               n_relabelled_by_same=int((A.label_same != A.label_frozen).sum()) if same_defined else None, cells={})
    if model == "Claude Opus 5":
        c = pd.read_csv(ST / "rational_agent_collection/audit/opus_thinking_check.csv")
        c = c[c.model == model].set_index("item")
        A["agree_adaptive_stageA"] = c.self_match_unbiased_stageA
        r2 = A.agree_adaptive_stageA.rank(method="first", ascending=False)
        A["label_adaptive"] = np.where(r2 <= 15, "HIGH", "LOW")
        res["n_relabelled_by_adaptive"] = int((A.label_adaptive != A.label_frozen).sum())
        res["mean_agree_adaptive"] = A.groupby("label_frozen").agree_adaptive_stageA.mean().to_dict()
        res["n_ties_at_1_adaptive"] = int((A.agree_adaptive_stageA == 1).sum())
    for (m, eff, part), t in cells.items():
        if m != model: continue
        ip = t.groupby("item").play.mean()
        cr = dict(n=int(len(t)), P_play=float(t.play.mean()),
                  frozen=cluster_diff(t, A.label_frozen.rename("lab")),
                  same_presentation=cluster_diff(t, A.label_same.rename("lab")) if same_defined else "undefined (tie at top-15 boundary)",
                  spearman_indep=float(spearmanr(A.agree_indep, ip[A.index]).statistic),
                  spearman_same=float(spearmanr(A.agree_same, ip[A.index]).statistic))
        if model == "Claude Opus 5":
            cr["adaptive_labels"] = cluster_diff(t, A.label_adaptive.rename("lab"))
            cr["spearman_adaptive"] = float(spearmanr(A.agree_adaptive_stageA, ip[A.index]).statistic)
        res["cells"][f"{eff}|{part}"] = cr
    out[model] = res
    item_rows.append(A.reset_index().assign(model=model))
pd.concat(item_rows).to_csv(HERE / "tables/study2_sensitivity_items.csv", index=False)
json.dump(out, open(HERE / "tables/study2_sensitivity.json", "w"), indent=1)
print(json.dumps(out, indent=1))
