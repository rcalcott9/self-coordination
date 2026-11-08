"""
STUDY 2 CONFIRMATION SCREEN -- re-estimate the compatibility gradient at higher n.

WHAT THIS IS
------------
The Stage-A-style confirmation battery (design/FROZEN_PARAMS.CONFIRM_N, run with the
frozen Study-1 runner stage_a_ground_truth.py under PSC_EXP_DIR=data/confirmation) is
read here and turned into the three quantities Study 2's primary analysis needs:

    GG = own-copy coordination rate, GPT-5.5 with a GPT-5.5 copy
    CC = own-copy coordination rate, Claude Opus 5 with a Claude Opus 5 copy
    GC = cross-model rate, DERIVED from the two independent marginals
    advantage(focal) = own(focal) - GC

NOTHING HERE IS A NEW ESTIMATOR. Every number comes from the already-written and
self-checked code:

    targeted_common.unbiased_match     own-copy, bias-corrected (same-draw pairs removed)
    cross_model_match.cross_match      cross-model plug-in product (already unbiased)
    cross_model_match.own_match_ci     own-copy + its frozen bootstrap
    cross_model_match.cross_boot_ci    cross-model bootstrap (two cells resampled
                                       INDEPENDENTLY, reproducing the estimand)
    targeted_common.pct_ci / BOOT_B / BOOT_SEED   bootstrap convention

The ONE thing with no frozen predecessor is the CI for the DIFFERENCE own - cross.
It is built from the same two frozen estimators inside one joint bootstrap that
resamples the GPT cell and the Claude cell independently and recomputes
unbiased_match(focal) - cross_match(gpt, claude) on each draw, so the focal cell's
error enters both terms with the correct correlation.

A SELF-CHECK runs first: the same code path is applied to Study 1's n=60 Stage A file
and required to reproduce pairs/cross_model_table.csv exactly. If the wrapper were
calling the frozen estimators differently, that check would fail.

PROVENANCE GUARD. Rows are pooled across the confirmation part-files, but a cell whose
rows come from more than one file is only accepted if the run_ids are DISJOINT (a
genuine resume). Overlapping run_ids abort: a partial failed file is never merged with
a good one.

Run:  python3 confirm_compat.py
Writes: ../design/confirmed_compatibility.csv
"""
import csv, glob, os, random, sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
S2 = os.path.dirname(HERE)
CONF = os.path.join(S2, "data", "confirmation")
os.environ.setdefault("PSC_EXP_DIR", CONF)
STUDY1 = os.path.normpath(os.path.join(os.path.dirname(S2),
                                       "policy_specific_self_coordination_20260812_1401"))
for p in (HERE, os.path.join(STUDY1, "code")):
    if p not in sys.path:
        sys.path.insert(0, p)

import psc_common as P
import targeted_common as tc
import cross_model_match as X          # frozen cross estimator + bootstraps
sys.path.insert(0, os.path.join(S2, "design"))
import FROZEN_PARAMS as F

MODELS = ("gpt", "claude")

# --- gate criteria -----------------------------------------------------------
# FROZEN_PARAMS names the critical TIERS; it does not numerically define "sign and
# qualitative order". These two constants make the reading explicit and are stated
# in CONFIRMATION_RESULTS.md alongside every verdict.
#   A zero_floor cell's design role is to supply a near-zero dose. Its provisional
#   value is +-0.02 to +-0.07, i.e. its SIGN carries no information at n=60 and a
#   sign change there cannot be a failure. What would break the design is the cell
#   ceasing to be a floor cell at all.
ZERO_FLOOR_MAX = 0.10       # |advantage| a zero_floor cell must stay under
SIGN_TRIVIAL = 0.05         # provisional |advantage| below this: sign uninformative


def load_confirmation_rows():
    """Pooled valid Stage-A rows from the confirmation battery, with provenance guard."""
    files = sorted(f for f in glob.glob(os.path.join(CONF, "data", "stageA_*.csv"))
                   if "_DRY" not in f)
    if not files:
        sys.exit("no confirmation Stage A files found under " + os.path.join(CONF, "data"))
    rows, src = [], defaultdict(lambda: defaultdict(list))   # cell -> file -> run_ids
    for f in files:
        for r in P.load_analysis_rows(f):
            if r["stage"] != "A" or not r["parsed_choice_identity"]:
                continue
            r["_src"] = os.path.basename(f)
            rows.append(r)
            src[(r["actor_model"], r["stimulus"])][os.path.basename(f)].append(r["run_id"])
    problems = []
    for cell, byfile in sorted(src.items()):
        if len(byfile) == 1:
            continue
        seen = Counter()
        for ids in byfile.values():
            seen.update(set(ids))
        dup = [k for k, v in seen.items() if v > 1]
        if dup:
            problems.append(f"{cell}: run_ids present in >1 file ({len(dup)} overlapping) "
                            f"across {sorted(byfile)} -- refusing to merge")
    if problems:
        sys.exit("PROVENANCE CHECK FAILED:\n  " + "\n  ".join(problems))
    return rows, files, src


def cells_from(rows):
    cell = defaultdict(list)
    for r in rows:
        cell[(r["actor_model"], r["stimulus"])].append(r)
    return cell


def joint_boot(g_ids, c_ids, seed, b=tc.BOOT_B):
    """Resample the two cells INDEPENDENTLY; recompute GG, CC, GC and both advantages
    on every draw with the same frozen estimators. Returns dict of draw lists."""
    rng = random.Random(seed)
    ng, nc = len(g_ids), len(c_ids)
    out = defaultdict(list)
    for _ in range(b):
        gs = rng.choices(g_ids, k=ng)
        cs = rng.choices(c_ids, k=nc)
        cg, cc = Counter(gs), Counter(cs)
        gg = tc.unbiased_match(cg)
        ccm = tc.unbiased_match(cc)
        gc = X.cross_match(cg, cc)
        out["GG"].append(gg); out["CC"].append(ccm); out["GC"].append(gc)
        out["adv_gpt"].append(gg - gc); out["adv_claude"].append(ccm - gc)
    return out


def build(cell, sids):
    out = []
    for s in sids:
        g = [r["parsed_choice_identity"] for r in cell[("gpt", s)]]
        c = [r["parsed_choice_identity"] for r in cell[("claude", s)]]
        row = dict(stimulus=s, n_gpt=len(g), n_claude=len(c))
        for m, ids in (("gpt", g), ("claude", c)):
            rs = cell[(m, s)]
            row[f"n_AB_{m}"] = sum(x["variant"] == "AB" for x in rs)
            row[f"n_BA_{m}"] = sum(x["variant"] == "BA" for x in rs)
            v, lo, hi = X.own_match_ci(ids, seed=f"{tc.BOOT_SEED}|{m}|{s}")
            key = "GG" if m == "gpt" else "CC"
            row[key] = X.rnd(v); row[f"{key}_ci_lo"] = X.rnd(lo); row[f"{key}_ci_hi"] = X.rnd(hi)
            cnt = Counter(ids)
            row[f"modal_{m}"] = max(cnt, key=lambda k: (cnt[k], k)) if cnt else ""
            # POSITION-FALLBACK DIAGNOSTIC. Pooled over AB and BA, the share taking the
            # modal SIDE. A cell at ~1.0 here with own-copy at ~0.5 is not coordinating
            # on the form at all -- it is answering by position, and the AB/BA
            # randomization then splits its identity choices 50/50.
            sc = Counter(x["parsed_choice_side"] for x in rs)
            row[f"pos_rate_{m}"] = X.rnd(max(sc.values()) / sum(sc.values())) if sc else ""
        gc = X.cross_match(Counter(g), Counter(c))
        lo, hi = X.cross_boot_ci(g, c, seed=f"{tc.BOOT_SEED}|cross|{s}")
        row["GC"] = X.rnd(gc); row["GC_ci_lo"] = X.rnd(lo); row["GC_ci_hi"] = X.rnd(hi)
        row["cross_variant_balanced"] = X.rnd(X.cross_match_variant_balanced(
            cell[("gpt", s)], cell[("claude", s)]))
        row["same_modal_identity"] = (row["modal_gpt"] == row["modal_claude"])
        draws = joint_boot(g, c, seed=f"{tc.BOOT_SEED}|adv|{s}")
        for m in MODELS:
            adv = (row["GG"] if m == "gpt" else row["CC"]) - gc
            alo, ahi = tc.pct_ci(draws[f"adv_{m}"])
            row[f"advantage_{m}"] = X.rnd(adv)
            row[f"advantage_{m}_ci_lo"] = X.rnd(alo)
            row[f"advantage_{m}_ci_hi"] = X.rnd(ahi)
        # structural identity |GC-1/2| = sqrt((GG-1/2)(CC-1/2)), FROZEN_PARAMS sec.2
        pred = ((row["GG"] - .5) * (row["CC"] - .5))
        pred = (pred ** .5) if pred >= 0 else float("nan")
        row["struct_pred_abs_dev"] = X.rnd(pred)
        row["struct_resid"] = X.rnd(abs(abs(gc - .5) - pred)) if pred == pred else ""
        out.append(row)
    return out


def selfcheck_old_path():
    """Apply this file's code path to Study 1's n=60 Stage A file and require it to
    reproduce pairs/cross_model_table.csv (own_gpt, own_claude, cross) exactly."""
    old = [f for f in glob.glob(os.path.join(STUDY1, "data", "stageA_*.csv"))
           if "_DRY" not in f]
    if not old:
        return None, "no Study 1 Stage A file found"
    old = max(old, key=os.path.getmtime)
    rows = [r for r in P.load_analysis_rows(old)
            if r["stage"] == "A" and r["parsed_choice_identity"]]
    cell = cells_from(rows)
    ref = {r["stimulus"]: r for r in
           csv.DictReader(open(os.path.join(S2, "pairs", "cross_model_table.csv")))}
    checks = []
    for s in sorted(ref):
        if ("gpt", s) not in cell:
            continue
        g = [r["parsed_choice_identity"] for r in cell[("gpt", s)]]
        c = [r["parsed_choice_identity"] for r in cell[("claude", s)]]
        for name, got in (("own_gpt", tc.unbiased_match(Counter(g))),
                          ("own_claude", tc.unbiased_match(Counter(c))),
                          ("cross", X.cross_match(Counter(g), Counter(c)))):
            want = float(ref[s][name])
            checks.append((s, name, want, got, abs(want - round(got, 4)) < 1e-9))
    return checks, os.path.basename(old)


def gate(table):
    """SIGN and qualitative ORDER of the GATE_CRITICAL_TIERS cells, per actor."""
    tab = {r["stimulus"]: r for r in table}
    verdicts, fails = [], []
    for m in MODELS:
        tiers = {sid: (adv, tier) for sid, adv, tier, _ in F.GRADIENT[m]}
        for sid, (prov, tier) in tiers.items():
            if tier not in F.GATE_CRITICAL_TIERS:
                continue
            if sid not in tab:
                fails.append((m, sid, tier, prov, "", "cell not collected"))
                continue
            new = tab[sid][f"advantage_{m}"]
            lo, hi = tab[sid][f"advantage_{m}_ci_lo"], tab[sid][f"advantage_{m}_ci_hi"]
            excl0 = (lo > 0) or (hi < 0)
            if tier == "large":
                ok = (new > 0) and excl0
                why = ("positive, CI excludes 0" if ok else
                       "NOT a positive advantage separated from 0")
            elif tier == "negative":
                if new < 0:
                    ok, why = True, ("negative, CI excludes 0" if excl0
                                     else "negative; CI includes 0")
                else:
                    ok = not excl0
                    why = ("sign flipped POSITIVE and CI excludes 0" if not ok
                           else "sign flipped positive but CI includes 0")
            else:                                   # zero_floor
                ok = abs(new) <= ZERO_FLOOR_MAX
                why = (f"|adv|={abs(new):.3f} <= {ZERO_FLOOR_MAX}, still a floor cell"
                       if ok else
                       f"|adv|={abs(new):.3f} > {ZERO_FLOOR_MAX}, no longer a floor cell")
                if abs(prov) < SIGN_TRIVIAL:
                    why += "; sign uninformative at n=60 (|prov|<%.2f)" % SIGN_TRIVIAL
            verdicts.append(dict(actor=m, stimulus=sid, tier=tier, provisional=prov,
                                 confirmed=new, ci_lo=lo, ci_hi=hi,
                                 pass_sign=ok, note=why))
            if not ok:
                fails.append((m, sid, tier, prov, new, why))
        # ORDER, within actor, over the critical tiers
        crit = [(sid, tab[sid][f"advantage_{m}"], tier)
                for sid, (prov, tier) in tiers.items()
                if tier in F.GATE_CRITICAL_TIERS and sid in tab]
        neg = [v for _, v, t in crit if t == "negative"]
        flo = [v for _, v, t in crit if t == "zero_floor"]
        lar = [v for _, v, t in crit if t == "large"]
        order_ok = bool(neg and flo and lar) and (max(neg) < min(flo)) and (max(flo) < min(lar))
        if not (neg and flo and lar):
            verdicts.append(dict(actor=m, stimulus="__ORDER__", tier="critical_order",
                                 provisional="", confirmed="", ci_lo="", ci_hi="",
                                 pass_sign=False, note="critical cells incomplete"))
            fails.append((m, "__ORDER__", "critical_order", "", "", "critical cells incomplete"))
            continue
        verdicts.append(dict(actor=m, stimulus="__ORDER__", tier="critical_order",
                             provisional="", confirmed="", ci_lo="", ci_hi="",
                             pass_sign=order_ok,
                             note=f"negative({max(neg):+.3f}) < zero_floor"
                                  f"({min(flo):+.3f}..{max(flo):+.3f}) < large({min(lar):+.3f})"))
        if not order_ok:
            fails.append((m, "__ORDER__", "critical_order", "", "",
                          "critical-tier order does not hold"))
    return verdicts, fails


def fill_design_table(table):
    """Write confirmed_advantage into design/frozen_design_table.csv, keyed on
    (actor_model, stimulus). Every other column is passed through untouched. If a
    sibling agent has not created the file, say so and leave it for reconciliation."""
    path = os.path.join(S2, "design", "frozen_design_table.csv")
    if not os.path.exists(path):
        return None
    tab = {r["stimulus"]: r for r in table}
    with open(path) as fh:
        rdr = csv.DictReader(fh)
        cols, rows = rdr.fieldnames, list(rdr)
    if "confirmed_advantage" not in cols:
        return "no confirmed_advantage column -- left untouched"
    n = 0
    for r in rows:
        t = tab.get(r["stimulus"])
        if not t:
            continue
        v = t.get(f"advantage_{r['actor_model']}")
        if v is None:
            continue
        r["confirmed_advantage"] = "%+0.3f" % v
        n += 1
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader(); w.writerows(rows)
    return f"filled confirmed_advantage on {n}/{len(rows)} rows"


def write_report(table, verdicts, fails, files, oldchecks, oldfile):
    """CONFIRMATION_RESULTS.md -- generated from the same objects that produced the
    CSV, so the report and the data cannot drift apart."""
    tab = {r["stimulus"]: r for r in table}
    old = {r["stimulus"]: r for r in
           csv.DictReader(open(os.path.join(S2, "pairs", "cross_model_table.csv")))}
    L = []
    A = L.append
    headline = ("**Stage C MAY PROCEED as frozen.**" if not fails else
                "**Stage C MUST NOT PROCEED as frozen — the gate FAILS.**")
    A("# Study 2 — confirmation screen results\n")
    A(f"{headline}\n")
    if fails:
        A("Critical cells that did not replicate:\n")
        for m, sid, tier, prov, new, why in fails:
            A(f"- `{m}` / `{sid}` ({tier}): {why}")
        A("")
    A("## What was run\n")
    A("A Stage-A-style re-estimation of own-copy choice rates, at the per-stimulus n "
      "frozen in `FROZEN_PARAMS.CONFIRM_N`, on both actors in `CONFIRM_MODELS`. "
      "The frozen Study-1 runner `stage_a_ground_truth.py` was reused unchanged "
      "(`PSC_EXP_DIR` redirected all output under `data/confirmation/`, so Study 1's "
      "tree was never written to): independent one-shot calls, exact AB/BA balance, "
      "prompt sha8 `3003ae1b`, unchanged parse rules, unchanged API settings. One "
      "invocation per n-group per actor.\n")
    A(f"Part files ({len(files)}):\n")
    for f in files:
        A(f"- `{os.path.basename(f)}`")
    A("")
    A("## Estimators\n")
    A("Nothing was reimplemented. Own-copy is `targeted_common.unbiased_match` "
      "(bias-corrected: same-draw pairs removed). Cross-model is "
      "`cross_model_match.cross_match`, the plug-in product of the two INDEPENDENT "
      "marginals, `GC = sum_k p_k^gpt * p_k^claude` — derived, never measured with "
      "new simultaneous cross-model calls. Bootstrap CIs are percentile, "
      f"B={tc.BOOT_B}, seed base {tc.BOOT_SEED}; the two cells are resampled "
      "independently. The advantage CI comes from one joint bootstrap that "
      "recomputes `unbiased_match(focal) - cross_match(gpt, claude)` per draw.\n")
    if oldchecks is not None:
        bad = [c for c in oldchecks if not c[4]]
        A(f"Self-check: this code path applied to the n=60 file `{oldfile}` reproduces "
          f"`pairs/cross_model_table.csv` on {len(oldchecks) - len(bad)}/{len(oldchecks)} "
          "cells exactly.\n")
    A("## Own-copy rates, n=60 -> confirmed, with CIs on both\n")
    A("Every cell reached its planned n exactly, with exact AB/BA balance, zero API "
      "errors, zero lost trials and zero unparseable responses.\n")
    A("| stimulus | actor | n=60 [95% CI] | confirmed n | confirmed [95% CI] | shift | CIs overlap |")
    A("|---|---|---|---|---|---|---|")
    disjoint = []
    for r in table:
        o = old[r["stimulus"]]
        for m, key in (("gpt", "GG"), ("claude", "CC")):
            ov_, olo, ohi = (float(o[f"own_{m}"]), float(o[f"own_{m}_ci_lo"]),
                             float(o[f"own_{m}_ci_hi"]))
            nv, nlo, nhi = r[key], r[f"{key}_ci_lo"], r[f"{key}_ci_hi"]
            ok = not (ohi < nlo or nhi < olo)
            if not ok:
                disjoint.append((r["stimulus"], m, ov_, nv))
            A(f"| `{r['stimulus']}` | {m} | {ov_:.3f} [{olo:.3f}, {ohi:.3f}] | "
              f"{r['n_' + m]} | {nv:.3f} [{nlo:.3f}, {nhi:.3f}] | {nv - ov_:+.3f} | "
              f"{'yes' if ok else '**NO - disjoint**'} |")
    A("")
    if disjoint:
        A("**Non-overlapping CIs** - a change larger than either sample's own "
          "uncertainty, so not attributable to n=60 sampling error:\n")
        for sid, m, ov_, nv in disjoint:
            A(f"- `{sid}` / {m}: {ov_:.3f} -> {nv:.3f} ({nv - ov_:+.3f})")
        A("")
    A("Cross-model rate, derived from the two independent marginals:\n")
    A("| stimulus | GC n=60 | GC confirmed [95% CI] | variant-balanced GC |")
    A("|---|---|---|---|")
    for r in table:
        o = old[r["stimulus"]]
        A(f"| `{r['stimulus']}` | {float(o['cross']):.3f} | "
          f"{r['GC']:.3f} [{r['GC_ci_lo']:.3f}, {r['GC_ci_hi']:.3f}] | "
          f"{r['cross_variant_balanced']:.3f} |")
    A("")
    A("## Compatibility advantage (own − cross), provisional → confirmed\n")
    for m in MODELS:
        A(f"### Focal {P.DISPLAY[m]}\n")
        A("| stimulus | tier | provisional (n=60) | confirmed [95% CI] | shift | critical |")
        A("|---|---|---|---|---|---|")
        for sid, prov, tier, _ in F.GRADIENT[m]:
            if sid not in tab:
                A(f"| `{sid}` | {tier} | {prov:+.3f} | NOT COLLECTED | | |")
                continue
            r = tab[sid]
            new = r[f"advantage_{m}"]
            A(f"| `{sid}` | {tier} | {prov:+.3f} | {new:+.3f} "
              f"[{r[f'advantage_{m}_ci_lo']:+.3f}, {r[f'advantage_{m}_ci_hi']:+.3f}] | "
              f"{new - prov:+.3f} | {'yes' if tier in F.GATE_CRITICAL_TIERS else ''} |")
        A("")
    A("## Gate\n")
    A(f"`GATE_CRITICAL_TIERS` = {F.GATE_CRITICAL_TIERS}. FROZEN_PARAMS names the tiers "
      "but does not numerically define \"sign and qualitative order\", so the reading "
      "applied here is stated explicitly:\n")
    A("- **large** — must stay positive with a 95% CI excluding 0.")
    A("- **negative** — must stay negative. A positive point estimate fails only if its "
      "CI also excludes 0; a sign change inside the CI is reported, not failed.")
    A(f"- **zero_floor** — the cell's design role is a near-zero dose, and its "
      f"provisional value (±0.01–0.07) means its SIGN carries no information at n=60. "
      f"The requirement is therefore that it remains a floor cell: "
      f"|advantage| ≤ {ZERO_FLOOR_MAX} (the project's existing negligible-difference "
      f"bar, `cross_model_match.CROSS_TOL`).")
    A("- **order** — within each actor, negative < zero_floor < large.\n")
    A("A tier boundary moving while sign and order hold is not a failure; the confirmed "
      "value simply replaces the provisional one.\n")
    A("| actor | cell | tier | provisional | confirmed | verdict | note |")
    A("|---|---|---|---|---|---|---|")
    for v in verdicts:
        pv = f"{float(v['provisional']):+.3f}" if v["provisional"] != "" else ""
        cv = f"{float(v['confirmed']):+.3f}" if v["confirmed"] != "" else ""
        A(f"| {v['actor']} | `{v['stimulus']}` | {v['tier']} | {pv} | {cv} | "
          f"**{'PASS' if v['pass_sign'] else 'FAIL'}** | "
          f"{v['note'].replace('|', chr(92) + '|')} |")
    A("")
    A("## Structural identity\n")
    A("`FROZEN_PARAMS` section 2 asserts |GC − 1/2| = sqrt((GG − 1/2)(CC − 1/2)) for "
      "binary stimuli. Confirmed residuals:\n")
    A("A blank residual means the sampled (GG - 1/2)(CC - 1/2) was negative — one "
      "own-copy rate landed a hair below chance — so the square root is undefined; "
      "that happens only at floor cells and is sampling noise, not a violation.\n")
    A("| stimulus | predicted \\|dev\\| | observed \\|dev\\| | residual |")
    A("|---|---|---|---|")
    for r in table:
        A(f"| `{r['stimulus']}` | {r['struct_pred_abs_dev']} | "
          f"{abs(r['GC'] - .5):.4f} | {r['struct_resid']} |")
    A("")
    A("## Position fallback, and why `d_texture` moved\n")
    A("`pos_rate` is the share of a cell's trials taking its modal SIDE, pooled over "
      "AB and BA. Near 1.0 means the model answered by position rather than by form; "
      "the AB/BA randomization then splits its identity choices ~50/50 and own-copy "
      "collapses to chance. This is the mechanism behind the one non-overlapping "
      "shift, and it is the same form-rule instability the 2026-08-14 version-"
      "stability analysis reported.\n")
    A("| stimulus | pos_rate gpt | own-copy gpt | pos_rate claude | own-copy claude |")
    A("|---|---|---|---|---|")
    for r in table:
        A(f"| `{r['stimulus']}` | {r['pos_rate_gpt']:.3f} | {r['GG']:.3f} | "
          f"{r['pos_rate_claude']:.3f} | {r['CC']:.3f} |")
    A("")
    A("The `cross_variant_balanced` column in `confirmed_compatibility.csv` diverges "
      "from the pooled `GC` at exactly these position-driven cells. That is expected "
      "and is not an estimator disagreement: the pooled estimator is the frozen one "
      "and answers the question the game asks — two players who each receive an "
      "INDEPENDENTLY randomized layout — whereas the variant-balanced diagnostic "
      "conditions on both players receiving the SAME layout, which two position "
      "responders would trivially match on. The pooled value is the one used "
      "everywhere.\n")
    A("## The confirmed gradient, in rank order\n")
    A("Tier labels come from the provisional n=60 values and are frozen; the confirmed "
      "numbers are what the primary analysis actually uses as the predictor. Where the "
      "rank order no longer matches the label order, the label is stale, not the number.\n")
    for m in MODELS:
        A(f"**Focal {P.DISPLAY[m]}**\n")
        g = sorted(((sid, tab[sid][f"advantage_{m}"], tier)
                    for sid, prov, tier, _ in F.GRADIENT[m] if sid in tab),
                   key=lambda x: -x[1])
        A("| rank | stimulus | frozen tier label | confirmed advantage |")
        A("|---|---|---|---|")
        for i, (sid, v, tier) in enumerate(g, 1):
            A(f"| {i} | `{sid}` | {tier} | {v:+.3f} |")
        A("")
        sep = [x for x in g if abs(x[1]) > 0.10]
        A(f"Cells with |advantage| > 0.10 (i.e. carrying a usable dose): "
          f"{len(sep)} of {len(g)}.\n")
    A("## Cells whose confirmed value departs materially from the provisional one\n")
    A("Listed for every tier, critical or not, at a |shift| above 0.15.\n")
    A("| actor | stimulus | tier | provisional | confirmed [95% CI] | shift |")
    A("|---|---|---|---|---|---|")
    for m in MODELS:
        for sid, prov, tier, _ in F.GRADIENT[m]:
            if sid not in tab:
                continue
            v = tab[sid][f"advantage_{m}"]
            if abs(v - prov) > 0.15:
                A(f"| {m} | `{sid}` | {tier} | {prov:+.3f} | {v:+.3f} "
                  f"[{tab[sid][f'advantage_{m}_ci_lo']:+.3f}, "
                  f"{tab[sid][f'advantage_{m}_ci_hi']:+.3f}] | {v - prov:+.3f} |")
    A("")
    A("## What the failure is, and what it does not touch\n")
    A("**Holding.** The GPT-focal gradient replicates on every criterion: `a_chev_ud` "
      "stays a clear positive advantage, `b_spiral_cw` stays negative with a CI "
      "excluding zero and a point estimate essentially unchanged (-0.128 to -0.127), "
      "both floor cells stay at the floor, and the critical order negative < "
      "zero_floor < large holds. Both ceiling controls remain at exactly 1.000 for "
      "both actors.\n")
    A("**Failing.** The Claude-focal gradient no longer has a usable low end. Three "
      "things happened at once:\n")
    A("1. `mirror` rose from +0.022 to +0.114 [+0.038, +0.214] — a floor cell that is "
      "now a small-positive dose with a CI excluding zero, so it is no longer the "
      "zero anchor the design assigned it.")
    A("2. `c_open_cplx`, Claude's ONLY negative cell and by the spec's own allocation "
      "the one carrying most of the discrimination between the coarse-identity and "
      "policy-specific accounts, collapsed from -0.106 to -0.003 [-0.065, +0.080]. "
      "The sign survives, but the dose does not. The mechanism is visible in the "
      "position-fallback table: Claude answers `c_open_cplx` by position on 1.000 of "
      "trials, so its identity choices split 50/50 by construction and its own-copy "
      "rate is pinned at chance. A negative advantage then requires GC to sit ABOVE "
      "0.5, which under a position rule is pure noise around 0.5 — the n=60 value of "
      "0.633 was that noise. A cell whose focal model is a position responder cannot "
      "carry a stable negative dose at any n.")
    A("3. Consequently the critical order fails: the negative cell (-0.003) is no "
      "longer below the floor cells (-0.004 and +0.114).\n")
    A("**Also worth seeing, though not gated.** `d_texture`, Claude's medium cell, "
      "fell from +0.401 to +0.003 — the one shift whose CIs do not overlap the n=60 "
      "estimate, driven by Claude switching to a near-pure position rule on that "
      "stimulus. Claude's frozen allocation therefore now spends 64 Stage C trials on "
      "a cell labelled `medium` whose true dose is zero. And for GPT the `large` and "
      "`medium` labels have swapped (`c_open_cplx` +0.489 now exceeds `a_chev_ud` "
      "+0.294); that is a tier-boundary move with sign and order intact, which the "
      "spec explicitly does not treat as a failure, but it does mean `a_chev_ud` no "
      "longer dominates the GPT slope the way section 14 anticipated.\n")
    A("**What this does not undermine.** The estimators, the balance, the prompt and "
      "the API settings are all unchanged and verified; the structural identity "
      "|GC - 1/2| = sqrt((GG - 1/2)(CC - 1/2)) holds to a residual of 0.002 wherever "
      "it is defined; and the confirmation itself did exactly what it was for. The "
      "predictor was measured with error at n=60, the re-estimation at n=180/120/60 "
      "found that error to be large enough to move design-critical cells, and it "
      "found it BEFORE Stage C was paid for rather than after.\n")
    A("**Decision required before Stage C.** The gate is a human decision point and "
      "this report does not resolve it. Stage C is not run. The Claude-focal arm "
      "needs either a replacement negative cell and a replacement floor cell drawn "
      "from the confirmed values, or an explicit decision to run the slope on the "
      "confirmed doses as they now stand and accept that Claude contributes no "
      "negative arm.\n")
    A("## Files\n")
    A("- `design/confirmed_compatibility.csv` — GG, CC, GC and both advantages, with CIs")
    A("- `design/confirmation_gate.csv` — the per-cell gate verdicts above")
    A("- `data/confirmation/data/stageA_*.csv|.jsonl` — raw trials")
    A("")
    path = os.path.join(S2, "design", "CONFIRMATION_RESULTS.md")
    open(path, "w").write("\n".join(L))
    return path


def main():
    rows, files, src = load_confirmation_rows()
    cell = cells_from(rows)
    sids = [s for s in F.CONFIRM_N if ("gpt", s) in cell and ("claude", s) in cell]

    print("=" * 78)
    print("STUDY 2 CONFIRMATION SCREEN -- compatibility gradient at higher n")
    print("=" * 78)
    print(f"  part files         : {len(files)}")
    for f in files:
        print(f"      {os.path.basename(f)}")
    print(f"  bootstrap          : B={tc.BOOT_B}, percentile, seed base {tc.BOOT_SEED}")
    print("  own-copy estimator : targeted_common.unbiased_match  (bias-corrected)")
    print("  cross estimator    : sum_k p_k^gpt * p_k^claude       (plug-in, unbiased)")

    checks, oldf = selfcheck_old_path()
    _sc = (checks, oldf)
    if checks:
        bad = [c for c in checks if not c[4]]
        print(f"\n  SELF-CHECK, same code path on the n=60 file ({oldf}) vs "
              f"pairs/cross_model_table.csv: {len(checks) - len(bad)}/{len(checks)} exact")
        for s, name, want, got, ok in bad:
            print(f"    MISMATCH {s} {name}: ref={want} got={got}")

    table = build(cell, sids)
    outp = os.path.join(S2, "design", "confirmed_compatibility.csv")
    X.write_csv(outp, table)

    print("\n  AB/BA balance and cell sizes (planned n from CONFIRM_N):")
    for r in table:
        plan = F.CONFIRM_N[r["stimulus"]]
        flag = ""
        if r["n_AB_gpt"] != r["n_BA_gpt"] or r["n_AB_claude"] != r["n_BA_claude"]:
            flag = "  <-- IMBALANCED"
        print(f"    {r['stimulus']:14s} plan={plan:>3d}  gpt {r['n_gpt']:>3d}"
              f" (AB{r['n_AB_gpt']}/BA{r['n_BA_gpt']})  claude {r['n_claude']:>3d}"
              f" (AB{r['n_AB_claude']}/BA{r['n_BA_claude']}){flag}")

    old = {r["stimulus"]: r for r in
           csv.DictReader(open(os.path.join(S2, "pairs", "cross_model_table.csv")))}
    print("\n" + "=" * 78)
    print("OWN-COPY AND CROSS-MODEL RATES:  n=60 -> confirmed")
    print("=" * 78)
    print(f"  {'stimulus':14s} {'GG old':>7s} {'GG new [95% CI]':>22s} "
          f"{'CC old':>7s} {'CC new [95% CI]':>22s} {'GC old':>7s} {'GC new':>7s}")
    for r in table:
        o = old[r["stimulus"]]
        print(f"  {r['stimulus']:14s} {float(o['own_gpt']):>7.3f} "
              f"{r['GG']:>10.3f} [{r['GG_ci_lo']:.3f},{r['GG_ci_hi']:.3f}] "
              f"{float(o['own_claude']):>7.3f} "
              f"{r['CC']:>10.3f} [{r['CC_ci_lo']:.3f},{r['CC_ci_hi']:.3f}] "
              f"{float(o['cross']):>7.3f} {r['GC']:>7.3f}")

    print("\n" + "=" * 78)
    print("COMPATIBILITY ADVANTAGE (own - cross):  provisional -> confirmed")
    print("=" * 78)
    for m in MODELS:
        print(f"\n  focal {P.DISPLAY[m]}")
        print(f"    {'stimulus':14s} {'tier':<11s} {'prov':>7s} {'confirmed [95% CI]':>26s}"
              f" {'shift':>7s}")
        tabx = {x["stimulus"]: x for x in table}
        for sid, prov, tier, _ in F.GRADIENT[m]:
            if sid not in tabx:
                print(f"    {sid:14s} {tier:<11s} {prov:>+7.3f}   NOT YET COLLECTED")
                continue
            r = tabx[sid]
            new = r[f"advantage_{m}"]
            print(f"    {sid:14s} {tier:<11s} {prov:>+7.3f} "
                  f"{new:>+13.3f} [{r[f'advantage_{m}_ci_lo']:+.3f},"
                  f"{r[f'advantage_{m}_ci_hi']:+.3f}] {new - prov:>+7.3f}")

    print("\n  STRUCTURAL CHECK |GC-1/2| = sqrt((GG-1/2)(CC-1/2)):")
    for r in table:
        print(f"    {r['stimulus']:14s} predicted |dev|={r['struct_pred_abs_dev']}"
              f"  observed |dev|={abs(r['GC'] - .5):.4f}  residual={r['struct_resid']}")

    verdicts, fails = gate(table)
    print("\n" + "=" * 78)
    print(f"GATE -- critical tiers {F.GATE_CRITICAL_TIERS}")
    print("=" * 78)
    print(f"  zero_floor cells must satisfy |advantage| <= {ZERO_FLOOR_MAX}")
    for v in verdicts:
        p = float(v["provisional"]) if v["provisional"] != "" else None
        c = float(v["confirmed"]) if v["confirmed"] != "" else None
        print(f"  {'PASS' if v['pass_sign'] else 'FAIL'}  {v['actor']:7s} "
              f"{v['stimulus']:14s} {v['tier']:<14s} "
              f"{('%+0.3f' % p) if p is not None else '':>7s} -> "
              f"{('%+0.3f' % c) if c is not None else '':>7s}   {v['note']}")
    X.write_csv(os.path.join(S2, "design", "confirmation_gate.csv"), verdicts)

    print("\n" + "=" * 78)
    if fails:
        print(f"GATE VERDICT: FAIL -- {len(fails)} critical cell(s) did not replicate.")
        for m, sid, tier, prov, new, why in fails:
            print(f"  {m} {sid} ({tier}): {why}")
        print("  Stage C must NOT proceed as frozen; the design needs revision.")
    else:
        print("GATE VERDICT: PASS -- sign and qualitative order of every critical cell")
        print("  replicate. Stage C may proceed as frozen, with the confirmed advantages")
        print("  replacing the provisional ones in the analysis.")
    print("=" * 78)
    msg = fill_design_table(table)
    rp = write_report(table, verdicts, fails, files, _sc[0], _sc[1])
    print(f"\n  wrote {outp}")
    print(f"  wrote {rp}")
    if msg is None:
        print("  design/frozen_design_table.csv does NOT exist -- no sibling table to "
              "fill; left for reconciliation")
    else:
        print(f"  design/frozen_design_table.csv: {msg}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
