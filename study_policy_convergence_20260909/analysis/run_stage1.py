"""
Stage 1 policy-convergence pipeline: raw trials -> cells -> pairs -> convergence.

MAKES NO API CALLS. Reads existing frozen data strictly READ-ONLY and writes only into
this analysis/ directory.

    python3 run_stage1.py --sources sources_worked_run.json --out out/worked_run
    python3 run_stage1.py --selftest

Stages
  0  LOAD + INTEGRITY GATES   one row per (model, item, presentation); prompt_hash,
                              checkpoint_requested vs checkpoint_returned, parse_ok,
                              duplicates, per-cell n. A gate failure is recorded and
                              the affected cells are excluded, never silently repaired.
  1  CELL METRICS             per model x item (DATA_DICTIONARY S "Per model x item")
  2  PAIR METRICS             per model-pair x item (DATA_DICTIONARY S "Per model-pair")
  3  CONVERGENCE              vintage slopes on the whole estimator ladder, within- and
                              cross-family, domain and mechanism interactions,
                              determinism-adjusted test, item-level exceptions and
                              reversals, leave-one-family-out / leave-one-mechanism-out.

Outputs (all under --out):
  integrity.json          every gate result and every excluded cell, with the reason
  cell_metrics.csv        one row per model x item
  pair_metrics.csv        one row per model-pair x item
  convergence.json        every convergence analysis
  SUMMARY.md              human-readable report
"""
from __future__ import annotations

import argparse
import csv
import glob
import json
import os
import sys
from collections import Counter, defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import convergence_metrics as cm  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))


# ------------------------------------------------------------------------------ load


def _read_rows(spec, k):
    """Normalise a source file to rows of
    (item_id, presentation_id, canonical_choice, display_position, prompt_hash,
     checkpoint_returned, parse_ok)."""
    out, raw_n = [], 0
    for path in spec["files"]:
        for f in sorted(glob.glob(path)):
            for r in csv.DictReader(open(f)):
                raw_n += 1
                if spec["schema"] == "stagea":
                    if r.get("model") != spec.get("model_col_value"):
                        continue
                    item, perm = r["array_id"], r["perm_id"]
                elif spec["schema"] == "aid_perm":
                    item, perm = r["aid"], r["perm"]
                else:
                    raise ValueError(spec["schema"])
                ok = (r.get("parse_ok") == "True") and (r.get("ok", "True") == "True")
                choice = r.get("chosen_item", "")
                pos = r.get("chosen_position", "")
                out.append(dict(
                    item_id=item, presentation_id=str(perm),
                    trial=str(r.get("trial", "")),
                    canonical_choice=int(choice) if ok and choice not in ("", "None") else None,
                    display_position=int(pos) if ok and pos not in ("", "None") else None,
                    prompt_hash=r.get("prompt_sha8", ""),
                    checkpoint_returned=r.get("api_model", ""),
                    parse_ok=ok, source_file=os.path.basename(f)))
    return out, raw_n


def load(sources, k):
    """Stage 0. Returns (cells, integrity). cells[(model_id, item_id)] = list of rows."""
    integ = dict(gates=[], excluded_cells=[], per_model={}, prompt_hashes={},
                 checkpoint_mismatches=[], duplicates=[], parse_failures={})
    cells = defaultdict(list)
    for spec in sources["models"]:
        mid = spec["model_id"]
        rows, raw_n = _read_rows(spec, k)
        shas = Counter(r["prompt_hash"] for r in rows)
        integ["prompt_hashes"][mid] = dict(shas)
        bad_ckpt = [r for r in rows
                    if spec["api_model_contains"] not in (r["checkpoint_returned"] or "")]
        if bad_ckpt:
            integ["checkpoint_mismatches"].append(
                dict(model=mid, n=len(bad_ckpt),
                     seen=sorted({r["checkpoint_returned"] for r in bad_ckpt})[:5]))
        seen = set()
        n_dup = n_bad = 0
        for r in rows:
            if spec["api_model_contains"] not in (r["checkpoint_returned"] or ""):
                continue                               # GATE: requested != returned
            # The trial index, NOT the presentation index, is the unique trial key.
            # n=48 is TWO complete cycles of the 24 permutations (MASTER_DESIGN S5), so
            # each presentation_id legitimately appears twice and keying on it would
            # silently halve every such cell.
            key = (r["item_id"], r["trial"] or r["presentation_id"], r["source_file"])
            if key in seen:
                n_dup += 1
                continue                               # GATE: duplicate trial
            seen.add(key)
            if not r["parse_ok"] or r["canonical_choice"] is None:
                n_bad += 1
                continue                               # GATE: unparseable
            cells[(mid, r["item_id"])].append(r)
        integ["duplicates"].append(dict(model=mid, n=n_dup))
        integ["parse_failures"][mid] = n_bad
        integ["per_model"][mid] = dict(raw_rows=raw_n, usable=sum(
            len(v) for (m, _), v in cells.items() if m == mid))

    # GATE: a single prompt generation across the whole analysis set
    all_shas = sorted({s for d in integ["prompt_hashes"].values() for s in d})
    integ["gates"].append(dict(
        gate="single_prompt_generation", pass_=len(all_shas) == 1, value=all_shas,
        note="MASTER_DESIGN threat 6: never combine incompatible prompt generations."))
    exp = sources.get("expect_prompt_sha8")
    if exp:
        integ["gates"].append(dict(gate="expected_prompt_hash",
                                   pass_=all_shas == [exp], value=all_shas, expected=exp))
    integ["gates"].append(dict(gate="checkpoint_requested_eq_returned",
                               pass_=not integ["checkpoint_mismatches"],
                               value=integ["checkpoint_mismatches"]))
    return cells, integ


# --------------------------------------------------------------------- cells and pairs


def build_cells(cells, items, k, n_floor, integ, stimuli_root):
    """Stage 1."""
    out = {}
    for (mid, item), rows in sorted(cells.items()):
        if item not in items:
            integ["excluded_cells"].append(dict(model=mid, item=item,
                                                reason="item not in battery manifest"))
            continue
        counts = cm.as_counts([r["canonical_choice"] for r in rows], k)
        rec = dict(model_id=mid, item_id=item, **items[item])
        rec.update(cm.cell_metrics(counts))
        if int(counts.sum()) < n_floor:
            rec["below_n_floor"] = True
            integ["excluded_cells"].append(
                dict(model=mid, item=item, reason=f"n={int(counts.sum())} < floor {n_floor}",
                     action="RETAINED and flagged; a real Stage 1 cell would be recollected"))
        else:
            rec["below_n_floor"] = False
        # position diagnostics (visual domain only)
        man_path = os.path.join(stimuli_root, item, "manifest.json")
        if rec.get("domain") == "visual" and os.path.exists(man_path):
            perm = json.load(open(man_path))
            rec.update(cm.position_metrics(
                [dict(item=r["canonical_choice"], perm_id=r["presentation_id"])
                 for r in rows], perm, rec["modal_identity"], k))
        out[(mid, item)] = rec
    return out


VINTAGE_ORIGIN = (2025, 1)          # years since 2025-01, so slopes read "per year"


def vintage_value(spec):
    """The vintage coordinate for a checkpoint.

    PREFER the calendar release date (`vintage_date`, "YYYY-MM"), expressed in years since
    2025-01. T4's `checkpoint_panel_verified.csv` also carries `release_order`, but that
    counter RESTARTS WITHIN EACH FAMILY (GPT 1..10, Claude 1..7), so averaging it across a
    cross-family pair compares two different scales and is meaningless. `vintage_rank` is
    retained only as a fallback for a single-family analysis or a worked run.
    """
    if spec.get("vintage_date"):
        y, m = (int(x) for x in str(spec["vintage_date"]).split("-")[:2])
        return (y - VINTAGE_ORIGIN[0]) + (m - VINTAGE_ORIGIN[1]) / 12.0
    return float(spec["vintage_rank"])


def build_pairs(cell_recs, models, k):
    """Stage 2. One row per unordered model pair x item."""
    ids = [m["model_id"] for m in models]
    meta = {m["model_id"]: m for m in models}
    vv = {m["model_id"]: vintage_value(m) for m in models}
    rows = []
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            a, b = ids[i], ids[j]
            for (m, item) in cell_recs:
                if m != a or (b, item) not in cell_recs:
                    continue
                ca = np.array(cell_recs[(a, item)]["choice_distribution"])
                cb = np.array(cell_recs[(b, item)]["choice_distribution"])
                r = dict(
                    model_a=a, model_b=b, item_id=item,
                    domain=cell_recs[(a, item)].get("domain"),
                    family_item=cell_recs[(a, item)].get("family"),
                    mechanism=cell_recs[(a, item)].get("mechanism"),
                    family_a=meta[a]["family"], family_b=meta[b]["family"],
                    pair_type=("within_family"
                               if meta[a]["family"] == meta[b]["family"]
                               else "cross_family"),
                    vintage=0.5 * (vv[a] + vv[b]),
                    vintage_min=min(vv[a], vv[b]),
                    vintage_a=vv[a], vintage_b=vv[b],
                    stratum_a=meta[a].get("stratum", ""),
                    stratum_b=meta[b].get("stratum", ""),
                    same_stratum=int(meta[a].get("stratum", "") == meta[b].get("stratum", "")),
                    n_a=int(ca.sum()), n_b=int(cb.sum()),
                    effective_support_a=cell_recs[(a, item)]["effective_support"],
                    effective_support_b=cell_recs[(b, item)]["effective_support"],
                    support_target_a=float(cm.support_targets(ca[None, :], k)[0]),
                    support_target_b=float(cm.support_targets(cb[None, :], k)[0]),
                )
                r.update(cm.pair_metrics(ca, cb))
                r["counts_a"] = ca.tolist()
                r["counts_b"] = cb.tolist()
                rows.append(r)
    return rows


# ------------------------------------------------------------------------ convergence


LADDER = ["cross_model_match", "cos_raw", "das", "dajs", "rank_similarity",
          "distribution_distance", "hellinger", "modal_agreement",
          "determinism_channel", "alignment_channel", "log_cross_match"]


def convergence(pairs, k, boot_b, null_b, target_support, seed=20260909):
    """Stage 3. Every analysis named in DATA_DICTIONARY 'Convergence analyses'."""
    x = np.array([p["vintage"] for p in pairs], float)
    it = np.array([p["item_id"] for p in pairs])
    res = {}

    # -- similarity by checkpoint vintage, on every rung of the ladder
    res["by_vintage"] = {}
    for kk in LADDER:
        y = np.array([p[kk] for p in pairs], float)
        pt, lo, hi = cm.cluster_bootstrap_slope(x, y, it, b=boot_b, seed=seed)
        res["by_vintage"][kk] = dict(slope=pt, lo=lo, hi=hi,
                                     mean=float(np.nanmean(y)))

    # -- the EXACT decomposition of the raw-match trend into its two channels
    d = res["by_vintage"]
    res["decomposition_of_raw_trend"] = dict(
        log_cross_match_slope=d["log_cross_match"]["slope"],
        determinism_channel_slope=d["determinism_channel"]["slope"],
        alignment_channel_slope=d["alignment_channel"]["slope"],
        residual=d["log_cross_match"]["slope"] - d["determinism_channel"]["slope"]
        - d["alignment_channel"]["slope"],
        share_from_determinism=(
            d["determinism_channel"]["slope"] / d["log_cross_match"]["slope"]
            if abs(d["log_cross_match"]["slope"]) > 1e-12 else float("nan")),
        note="log M_AB = .5 log M_AA + .5 log M_BB + log cos_raw, exactly. "
             "The residual is 0 by construction and is printed as a check.")

    # -- within-family, cross-family, domain, mechanism
    for gk, name in (("pair_type", "by_pair_type"), ("domain", "by_domain"),
                     ("mechanism", "by_mechanism"), ("family_item", "by_item_family"),
                     ("same_stratum", "by_stratum_match")):
        res[name] = {kk: cm.group_slopes(pairs, "vintage", kk, gk, "item_id",
                                         b=boot_b, seed=seed)
                     for kk in ("cross_model_match", "das")}

    # -- interaction: does the vintage slope differ between groups?
    def contrast(groupdict):
        gs = {g: v["slope"] for g, v in groupdict.items() if v["slope"] == v["slope"]}
        if len(gs) < 2:
            return None
        lo_g, hi_g = min(gs, key=gs.get), max(gs, key=gs.get)
        return dict(min_group=lo_g, min_slope=gs[lo_g],
                    max_group=hi_g, max_slope=gs[hi_g], spread=gs[hi_g] - gs[lo_g])
    res["interactions"] = {
        name: {kk: contrast(res[name][kk]) for kk in res[name]}
        for name in ("by_pair_type", "by_domain", "by_mechanism", "by_item_family",
                     "by_stratum_match")}

    # -- DETERMINISM-ADJUSTED test: the primary inference (ANALYSIS_SPEC S4.5)
    nrows = [dict(item_id=p["item_id"], vintage=p["vintage"],
                  n_a=p["n_a"], n_b=p["n_b"],
                  counts_a=p["counts_a"], counts_b=p["counts_b"]) for p in pairs]
    res["determinism_adjusted_test"] = cm.determinism_matched_null_band(
        nrows, b=null_b, target_support=target_support, seed=seed)

    # -- SECONDARY confirmation on the estimable subset, where DAS is nearly unbiased
    #    and an ordinary item-clustered bootstrap CI is valid (ANALYSIS_SPEC S4.6).
    est = [p for p in pairs
           if min(p["support_target_a"], p["support_target_b"]) >= 0.75 * target_support]
    if len(est) >= 6 and len({p["vintage"] for p in est}) >= 2:
        pt, lo, hi = cm.cluster_bootstrap_slope(
            [p["vintage"] for p in est], [p["das"] for p in est],
            [p["item_id"] for p in est], b=boot_b, seed=seed)
        res["estimable_subset"] = dict(
            n=len(est), n_total=len(pairs), threshold=0.75 * target_support,
            slope=pt, lo=lo, hi=hi,
            mean_das=float(np.mean([p["das"] for p in est])))
    else:
        res["estimable_subset"] = dict(
            n=len(est), n_total=len(pairs), threshold=0.75 * target_support,
            slope=float("nan"), lo=float("nan"), hi=float("nan"),
            note="too few pairs above the support threshold to refit; the panel is "
                 "too deterministic for an unadjusted-bias estimate of the DAS trend")

    # -- S* sensitivity: is the conclusion an artefact of the reference level?
    res["target_support_sensitivity"] = {}
    for s_star in (1.5, 2.0, 2.5, 3.0):
        y = np.array([cm.das(np.array(p["counts_a"]), np.array(p["counts_b"]),
                             s_star)[0] for p in pairs], float)
        pt, lo, hi = cm.cluster_bootstrap_slope(x, y, it, b=max(200, boot_b // 2),
                                                seed=seed)
        res["target_support_sensitivity"][str(s_star)] = dict(
            slope=pt, lo=lo, hi=hi, mean=float(np.nanmean(y)))

    # -- alpha sensitivity
    res["alpha_sensitivity"] = {}
    for al in (0.25, 0.5, 1.0):
        y = np.array([cm.das(np.array(p["counts_a"]), np.array(p["counts_b"]),
                             target_support, al)[0] for p in pairs], float)
        pt, lo, hi = cm.cluster_bootstrap_slope(x, y, it, b=max(200, boot_b // 2),
                                                seed=seed)
        res["alpha_sensitivity"][str(al)] = dict(slope=pt, lo=lo, hi=hi)

    # -- item-level exceptions and reversals
    pooled = res["by_vintage"]["das"]["slope"]
    per_item = {}
    for item in sorted(set(it)):
        sub = [p for p in pairs if p["item_id"] == item]
        if len({p["vintage"] for p in sub}) < 2:
            continue
        s_das, _ = cm.ols_slope([p["vintage"] for p in sub], [p["das"] for p in sub])
        s_raw, _ = cm.ols_slope([p["vintage"] for p in sub],
                                [p["cross_model_match"] for p in sub])
        ma = sorted(((p["vintage"], p["modal_agreement"]) for p in sub))
        reversal = bool(ma and ma[0][1] == 1 and ma[-1][1] == 0)
        per_item[item] = dict(
            das_slope=s_das, raw_slope=s_raw,
            opposes_pooled=bool(s_das == s_das and pooled == pooled
                                and s_das * pooled < 0),
            modal_agreement_reversal=reversal,
            mean_modal_agreement=float(np.mean([p["modal_agreement"] for p in sub])),
            min_support=float(min(min(p["support_target_a"], p["support_target_b"])
                                  for p in sub)))
    res["item_level"] = per_item
    res["exceptions"] = dict(
        pooled_das_slope=pooled,
        n_items=len(per_item),
        n_opposing=sum(v["opposes_pooled"] for v in per_item.values()),
        opposing_items=[i for i, v in per_item.items() if v["opposes_pooled"]],
        n_modal_reversals=sum(v["modal_agreement_reversal"] for v in per_item.values()),
        reversal_items=[i for i, v in per_item.items() if v["modal_agreement_reversal"]])

    # -- leave-one-family-out / leave-one-mechanism-out
    res["leave_one_family_out"] = {
        kk: cm.leave_one_out_slopes(pairs, "vintage", kk, "family_item", "item_id",
                                    b=boot_b, seed=seed)
        for kk in ("cross_model_match", "das")}
    res["leave_one_mechanism_out"] = {
        kk: cm.leave_one_out_slopes(pairs, "vintage", kk, "mechanism", "item_id",
                                    b=boot_b, seed=seed)
        for kk in ("cross_model_match", "das")}
    return res


# ------------------------------------------------------------------------------ io


def write_csv(path, rows, drop=()):
    if not rows:
        return
    keys = [k for k in rows[0] if k not in drop]
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: (json.dumps(v) if isinstance(v, (list, dict)) else v)
                        for k, v in r.items() if k in keys})


def summary_md(sources, integ, cell_recs, pairs, conv, out):
    L = []
    A = L.append
    A("# Stage 1 pipeline — worked run\n")
    A("Generated by `analysis/run_stage1.py`. **No API calls.** Existing frozen data "
      "read strictly read-only.\n")
    A(f"Source config: `{os.path.basename(sources.get('_path', ''))}`  |  "
      f"domain `{sources['domain']}`  |  K = {sources['k_options']}\n")
    A("\n## 0. Integrity gates\n")
    A("| gate | pass | value |")
    A("|---|---|---|")
    for g in integ["gates"]:
        A(f"| {g['gate']} | {'PASS' if g['pass_'] else 'FAIL'} | `{g.get('value')}` |")
    A("\n| model | raw rows | usable trials | parse failures | duplicates |")
    A("|---|---|---|---|---|")
    dup = {d["model"]: d["n"] for d in integ["duplicates"]}
    for m, v in integ["per_model"].items():
        A(f"| `{m}` | {v['raw_rows']} | {v['usable']} | "
          f"{integ['parse_failures'].get(m, 0)} | {dup.get(m, 0)} |")
    if integ["excluded_cells"]:
        A(f"\n{len(integ['excluded_cells'])} cell notices "
          f"(see `integrity.json`); first 5:\n")
        for e in integ["excluded_cells"][:5]:
            A(f"- `{e['model']}` x `{e['item']}` — {e['reason']}")

    A("\n## 1. Cells\n")
    sup = [c["effective_support"] for c in cell_recs.values()]
    ms = [c["modal_share"] for c in cell_recs.values()]
    fc = [c.get("form_consistency") for c in cell_recs.values()
          if c.get("form_consistency") == c.get("form_consistency")]
    A(f"{len(cell_recs)} model x item cells.\n")
    A(f"- effective_support: median {np.median(sup):.3f}, "
      f"IQR [{np.percentile(sup, 25):.3f}, {np.percentile(sup, 75):.3f}], "
      f"min {min(sup):.3f}, max {max(sup):.3f}")
    A(f"- modal_share: median {np.median(ms):.3f}; "
      f"{sum(m >= 0.99 for m in ms)}/{len(ms)} cells at modal_share >= 0.99 "
      f"(behavioural collapse; MASTER_DESIGN threat 3)")
    if fc:
        A(f"- form_consistency (visual): median {np.median(fc):.3f}, "
          f"min {min(fc):.3f}, n={len(fc)}")
    A("\n### effective_support by model")
    A("\n| model | n cells | median support | median modal_share | median form_consistency |")
    A("|---|---|---|---|---|")
    for mid in sorted({c["model_id"] for c in cell_recs.values()}):
        cs = [c for c in cell_recs.values() if c["model_id"] == mid]
        f2 = [c.get("form_consistency") for c in cs
              if c.get("form_consistency") == c.get("form_consistency")]
        A(f"| `{mid}` | {len(cs)} | {np.median([c['effective_support'] for c in cs]):.3f} "
          f"| {np.median([c['modal_share'] for c in cs]):.3f} | "
          f"{(f'{np.median(f2):.3f}' if f2 else 'n/a')} |")

    A("\n## 2. Pairs\n")
    A(f"{len(pairs)} model-pair x item rows over "
      f"{len({(p['model_a'], p['model_b']) for p in pairs})} pairs.\n")
    A("| pair | type | vintage | n items | modal_agree | cross_match | JS dist | cos_raw | DAS |")
    A("|---|---|---|---|---|---|---|---|---|")
    for (a, b) in sorted({(p["model_a"], p["model_b"]) for p in pairs}):
        sub = [p for p in pairs if p["model_a"] == a and p["model_b"] == b]
        A(f"| `{a}` vs `{b}` | {sub[0]['pair_type']} | {sub[0]['vintage']:.1f} | {len(sub)} "
          f"| {np.mean([p['modal_agreement'] for p in sub]):.3f} "
          f"| {np.mean([p['cross_model_match'] for p in sub]):.3f} "
          f"| {np.mean([p['distribution_distance'] for p in sub]):.3f} "
          f"| {np.mean([p['cos_raw'] for p in sub]):.3f} "
          f"| {np.mean([p['das'] for p in sub]):.3f} |")

    A("\n## 3. Convergence\n")
    A("### Similarity by checkpoint vintage (item-clustered bootstrap)\n")
    A("| metric | mean | slope / vintage | 95% CI |")
    A("|---|---|---|---|")
    for kk, v in conv["by_vintage"].items():
        A(f"| {kk} | {v['mean']:+.4f} | {v['slope']:+.4f} | "
          f"[{v['lo']:+.4f}, {v['hi']:+.4f}] |")

    d = conv["decomposition_of_raw_trend"]
    A("\n### Exact decomposition of the raw-match trend\n")
    A("`log M_AB = .5 log M_AA + .5 log M_BB + log cos_raw`\n")
    A(f"- total (log cross_model_match) slope: {d['log_cross_match_slope']:+.4f}")
    A(f"- **determinism channel**: {d['determinism_channel_slope']:+.4f} "
      f"({100 * d['share_from_determinism']:.0f}% of the total)")
    A(f"- **alignment channel**: {d['alignment_channel_slope']:+.4f}")
    A(f"- residual (must be 0): {d['residual']:+.2e}")

    t = conv["determinism_adjusted_test"]
    A("\n### DETERMINISM-ADJUSTED test (primary inference)\n")
    # LEAD GUARD 2026-09-09: a degenerate panel returns None for every band field
    # (see convergence_metrics.determinism_matched_null_band). Report that, do not format it.
    if t.get("degenerate"):
        A(f"- **DEGENERATE PANEL — no test performed.** {t.get('degenerate_reason','')}")
        A(f"- observed DAS slope: {t['observed_slope'] if t['observed_slope'] is None else format(t['observed_slope'], '+.4f')}")
        A("- determinism-matched null band: not computable")
        A("- verdict: **NO VERDICT.** This is a statement about the panel, not the models.")
    else:
        A(f"- observed DAS slope: **{t['observed_slope']:+.4f}**")
        A(f"- determinism-matched null band: [{t['null_lo']:+.4f}, {t['null_hi']:+.4f}] "
          f"(null mean {t['null_mean']:+.4f})")
        A(f"- excess over null: **{t['excess_slope']:+.4f}**, two-sided p = {t['p_two_sided']:.3f}")
        A(f"- verdict: **{'REJECT H0 (similarity change beyond determinism)' if t['reject'] else 'DO NOT REJECT H0 (no similarity change beyond determinism)'}**")
    A(f"- identifiable: **{t['identifiable']}** — {t['n_reference_rows_strict']} rows meet "
      f"the strict reference threshold (both cells at effective support >= "
      f"{t['reference_threshold']:.2f}); the band shown uses {t['n_reference_rows']} rows. "
      f"Mean support A {t['mean_support_a']:.3f}, B {t['mean_support_b']:.3f}.")
    if not t["identifiable"]:
        A("\n> **Not identifiable.** Too few pairs retain effective support near the "
          "reference level, so this panel cannot separate determinism from similarity "
          "at all. That is a reportable outcome about the battery, not a result about "
          "the models.")

    es = conv["estimable_subset"]
    A("\n### Secondary: estimable subset (both cells above the support threshold)\n")
    A(f"- {es['n']} of {es['n_total']} pair x item rows have both cells at "
      f"effective support >= {es['threshold']:.2f}")
    if es["slope"] == es["slope"]:
        A(f"- DAS slope on that subset: {es['slope']:+.4f} "
          f"[{es['lo']:+.4f}, {es['hi']:+.4f}] (mean DAS {es['mean_das']:.4f})")
    else:
        A(f"- {es['note']}")

    A("\n### Within- vs cross-family\n")
    A("| metric | group | n | slope | 95% CI |")
    A("|---|---|---|---|---|")
    for kk in conv["by_pair_type"]:
        for g, v in conv["by_pair_type"][kk].items():
            A(f"| {kk} | {g} | {v['n']} | {v['slope']:+.4f} | "
              f"[{v['lo']:+.4f}, {v['hi']:+.4f}] |")

    A("\n### Compatibility-stratum check (DAS slope)\n")
    A("A trend carried only by cross-stratum pairs is a request-surface artefact "
      "(MASTER_DESIGN S4.1), not convergence.\n")
    A("| same_stratum | n | slope | 95% CI |")
    A("|---|---|---|---|")
    for g, v in sorted(conv["by_stratum_match"]["das"].items()):
        A(f"| {g} | {v['n']} | {v['slope']:+.4f} | [{v['lo']:+.4f}, {v['hi']:+.4f}] |")

    A("\n### Mechanism interaction (DAS slope)\n")
    A("| mechanism | n | slope | 95% CI |")
    A("|---|---|---|---|")
    for g, v in sorted(conv["by_mechanism"]["das"].items()):
        A(f"| {g} | {v['n']} | {v['slope']:+.4f} | [{v['lo']:+.4f}, {v['hi']:+.4f}] |")

    A("\n### Interactions (spread of the DAS vintage slope across group levels)\n")
    A("| grouping | min level | min slope | max level | max slope | spread |")
    A("|---|---|---|---|---|---|")
    for name in ("by_domain", "by_mechanism", "by_item_family", "by_pair_type",
                 "by_stratum_match"):
        c = conv["interactions"][name]["das"]
        if not c:
            A(f"| {name[3:]} | (single level) | | | | |")
            continue
        A(f"| {name[3:]} | {c['min_group']} | {c['min_slope']:+.4f} | {c['max_group']} "
          f"| {c['max_slope']:+.4f} | {c['spread']:.4f} |")

    e = conv["exceptions"]
    A("\n### Item-level exceptions and reversals\n")
    A(f"- pooled DAS slope {e['pooled_das_slope']:+.4f} over {e['n_items']} items")
    A(f"- items whose DAS slope OPPOSES the pooled sign: {e['n_opposing']} "
      f"{e['opposing_items'][:10]}")
    A(f"- items with a modal-agreement reversal (agree at low vintage, disagree at "
      f"high): {e['n_modal_reversals']} {e['reversal_items'][:10]}")

    A("\n### Leave-one-out sensitivity (DAS slope)\n")
    A("| dropped | n | slope | 95% CI |")
    A("|---|---|---|---|")
    for name in ("leave_one_family_out", "leave_one_mechanism_out"):
        for g, v in conv[name]["das"].items():
            A(f"| {name.split('_')[2]}: {g} | {v['n']} | {v['slope']:+.4f} | "
              f"[{v['lo']:+.4f}, {v['hi']:+.4f}] |")

    A("\n### Sensitivity to the reference determinism S* and the smoothing alpha\n")
    A("| S* | mean DAS | slope | 95% CI |")
    A("|---|---|---|---|")
    for s, v in conv["target_support_sensitivity"].items():
        A(f"| {s} | {v['mean']:+.4f} | {v['slope']:+.4f} | [{v['lo']:+.4f}, {v['hi']:+.4f}] |")
    A("\n| alpha | slope | 95% CI |")
    A("|---|---|---|")
    for s, v in conv["alpha_sensitivity"].items():
        A(f"| {s} | {v['slope']:+.4f} | [{v['lo']:+.4f}, {v['hi']:+.4f}] |")

    A("\n---\n")
    A("Required language (MASTER_DESIGN S2): these are *policy similarity* results on "
      "*this fixed battery*, *associated with* checkpoint vintage, and the historical "
      "checkpoint comparison is a *descriptive historical pattern*, not a causal time "
      "trend. The panel used here is a worked-run convenience sample, not the Stage 1 "
      "panel (T4, TBD), and the vintage ranks are analyst-supplied.\n")
    open(out, "w").write("\n".join(L) + "\n")


# -------------------------------------------------------------------------- selftest


def selftest():
    """Assert the properties the spec claims. Exits non-zero on failure."""
    rng = np.random.default_rng(7)
    k = 4
    ok = True

    def check(name, cond, extra=""):
        nonlocal ok
        print(f"  {'PASS' if cond else 'FAIL'}  {name} {extra}")
        ok = ok and bool(cond)

    print("selftest")
    # 1. exact tempering invariance of standardisation, in the population
    q = cm.standardize_probs_batch(rng.dirichlet(np.ones(k), size=50), 2.0)
    worst = 0.0
    for beta in (0.3, 1.0, 2.0, 7.0, 25.0):
        p = cm.temper_batch(q, np.full(len(q), beta))
        back = cm.standardize_probs_batch(p, 2.0)
        worst = max(worst, float(np.abs(back - q).max()))
    check("standardize(temper(q, beta)) == q for all beta", worst < 1e-8,
          f"(max abs dev {worst:.2e})")

    # 2. DAS is invariant to per-model tempering, in the population
    qa, qb = q[:25], q[25:]
    base = 2.0 * (qa * qb).sum(axis=1)
    worst = 0.0
    for ba, bb in ((1, 1), (0.5, 4.0), (9.0, 2.0), (30.0, 30.0)):
        pa = cm.temper_batch(qa, np.full(25, ba))
        pb = cm.temper_batch(qb, np.full(25, bb))
        got = 2.0 * (cm.standardize_probs_batch(pa, 2.0)
                     * cm.standardize_probs_batch(pb, 2.0)).sum(axis=1)
        worst = max(worst, float(np.abs(got - base).max()))
    check("DAS invariant to per-model tempering", worst < 1e-8, f"(max dev {worst:.2e})")

    # 3. the match decomposition is exact
    ca = rng.multinomial(48, rng.dirichlet(np.ones(k)), size=30)
    cb = rng.multinomial(48, rng.dirichlet(np.ones(k)), size=30)
    r = max(abs(cm.match_decomposition(ca[i], cb[i], 0.5)["residual"]) for i in range(30))
    check("log M_AB = .5 log M_AA + .5 log M_BB + log cos_raw", r < 1e-12,
          f"(max residual {r:.2e})")

    # 4. cross_model_match is unbiased for independent samples
    pa, pb = np.array([.5, .25, .15, .10]), np.array([.4, .3, .2, .1])
    truth = float((pa * pb).sum())
    est = np.mean([cm.cross_model_match(rng.multinomial(48, pa), rng.multinomial(48, pb))
                   for _ in range(4000)])
    check("cross_model_match unbiased", abs(est - truth) < 0.004,
          f"(truth {truth:.4f}, mean estimate {est:.4f})")

    # 5. within_model_match is unbiased, plug-in is not
    tw = float((pa * pa).sum())
    draws = [rng.multinomial(48, pa) for _ in range(4000)]
    eu = np.mean([cm.within_model_match(c) for c in draws])
    ep = np.mean([cm.plugin_match(c) for c in draws])
    check("within_model_match unbiased, plug-in biased up", abs(eu - tw) < 0.004 and ep > eu,
          f"(truth {tw:.4f}, unbiased {eu:.4f}, plug-in {ep:.4f})")

    # 6. distances are metrics with the right endpoints
    u = np.array([12, 12, 12, 12])
    d1 = cm.js_distance(u, u, 0.5, False)
    d2 = cm.js_distance(np.array([48, 0, 0, 0]), np.array([0, 0, 0, 48]), 0.0, False)
    check("JS distance 0 on identical, 1 on disjoint", d1 < 1e-9 and d2 > 0.999,
          f"({d1:.2e}, {d2:.4f})")

    # 7. Miller-Madow reduces the small-sample bias of plug-in JS distance
    pa2, pb2 = np.array([.5, .25, .15, .10]), np.array([.4, .3, .2, .1])
    tj = float(np.sqrt(cm.js_divergence_bits(pa2, pb2)))
    pl, mm = [], []
    for _ in range(1500):
        c1, c2 = rng.multinomial(48, pa2), rng.multinomial(48, pb2)
        pl.append(cm.js_distance(c1, c2, 0.5, False))
        mm.append(cm.js_distance(c1, c2, 0.5, True))
    bp, bm = abs(np.mean(pl) - tj), abs(np.mean(mm) - tj)
    check("Miller-Madow reduces JS distance bias", bm < bp / 2,
          f"(truth {tj:.4f}, plug-in bias {np.mean(pl) - tj:+.4f}, MM bias {np.mean(mm) - tj:+.4f})")

    # 8. batch == scalar
    Pt, tau, _ = cm.standardize_batch(ca.astype(float))
    worst = max(float(np.abs(cm.standardize(ca[i])[0] - Pt[i]).max()) for i in range(30))
    check("batch standardise == scalar standardise", worst < 1e-9, f"({worst:.2e})")

    print("selftest", "PASSED" if ok else "FAILED")
    return 0 if ok else 1


# ------------------------------------------------------------------------------ main


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sources", default=os.path.join(HERE, "sources_worked_run.json"))
    ap.add_argument("--out", default=os.path.join(HERE, "out", "worked_run"))
    ap.add_argument("--n-floor", type=int, default=48)
    ap.add_argument("--boot-b", type=int, default=2000)
    ap.add_argument("--null-b", type=int, default=400)
    ap.add_argument("--target-support", type=float, default=cm.DEFAULT_TARGET_SUPPORT)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(selftest())

    sources = json.load(open(a.sources))
    sources["_path"] = a.sources
    k = sources["k_options"]
    os.makedirs(a.out, exist_ok=True)

    items = {}
    for r in csv.DictReader(open(sources["battery_manifest"])):
        items[r["array_id"]] = dict(domain=sources["domain"], family=r["family"],
                                    mechanism=r["mechanism"])

    print("stage 0: load + integrity")
    cells, integ = load(sources, k)
    print("stage 1: cell metrics")
    cell_recs = build_cells(cells, items, k, a.n_floor, integ, sources["stimuli_root"])
    print(f"  {len(cell_recs)} cells")
    print("stage 2: pair metrics")
    pairs = build_pairs(cell_recs, sources["models"], k)
    print(f"  {len(pairs)} pair x item rows")
    print("stage 3: convergence")
    conv = convergence(pairs, k, a.boot_b, a.null_b, a.target_support)

    json.dump(integ, open(os.path.join(a.out, "integrity.json"), "w"), indent=1)
    write_csv(os.path.join(a.out, "cell_metrics.csv"), list(cell_recs.values()))
    write_csv(os.path.join(a.out, "pair_metrics.csv"), pairs)
    json.dump(conv, open(os.path.join(a.out, "convergence.json"), "w"), indent=1,
              default=float)
    summary_md(sources, integ, cell_recs, pairs, conv,
               os.path.join(a.out, "SUMMARY.md"))
    print("wrote", a.out)


if __name__ == "__main__":
    main()
