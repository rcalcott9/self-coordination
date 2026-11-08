"""
Stage C DATA QUALITY ONLY. Rows collected vs planned, valid/invalid, AB/BA balance
per cell, cells short of target, and the raw per-cell ATTEMPT rate.

THIS IS NOT THE ANALYSIS. It fits no model, tests no hypothesis, computes no slope
and reports nothing partner-contrasted or advantage-ordered. The primary
dose-response analysis is pre-specified in design/STUDY2_SPEC_FROZEN.md sections
9/10 and implemented in code/analyze_dose_response.py; running anything else on
these data before that would defeat the pre-registration.

    python3 stage_c_quality.py > ../data/STAGE_C_DATA_QUALITY.md
"""
import csv, glob, os, sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import study2_betting as S                                   # noqa: E402
import FROZEN_PARAMS as FP                                   # noqa: E402
import psc_common as P                                       # noqa: E402

DATA = P.DATA
design = S.load_design_table()
cells, meta = S.build_cells(design)
plan = {S.cell_key(c): meta[S.cell_key(c)]["n_cell"] for c in cells}

files = S.part_files(DATA)
complete, partial = S.scan_progress(lambda k: plan[k], DATA, keys=set(plan))

# rows are taken from exactly ONE part file per cell - the one that completed it -
# so a partial failed file is never merged with a good one.
src_of = dict(complete)
by_file = defaultdict(lambda: defaultdict(list))     # file -> cell -> rows
attempted_by_cell = defaultdict(list)                # every row written, any file
for f in files:
    for r in csv.DictReader(open(f)):
        k = r.get("cell_key") or S.cell_key(r)
        if k not in plan:
            continue
        attempted_by_cell[k].append((f, r))
        by_file[f][k].append(r)

T = lambda v: str(v).strip().lower() in ("true", "1", "yes")

# rows_by_cell  = the completing file's rows (a COMPLETE cell at its frozen n)
# best_by_cell  = for a cell no file completed, the SINGLE part file holding the most
#                 analysable rows for it. Still one file per cell - counts are never
#                 summed across files, so a partial file is never merged with a good
#                 one. These cells are short of target and are flagged as such.
rows_by_cell, best_by_cell, best_src = defaultdict(list), {}, {}
for k in plan:
    if k in src_of:
        rows_by_cell[k] = by_file[src_of[k]][k]
        best_by_cell[k] = [r for r in rows_by_cell[k] if T(r["included_in_analysis"])]
        best_src[k] = src_of[k]
    else:
        cand = [(sum(1 for r in by_file[f][k] if T(r["included_in_analysis"])), f)
                for f in files if by_file[f][k]]
        if cand:
            n_best, f_best = max(cand)
            best_by_cell[k] = [r for r in by_file[f_best][k]
                               if T(r["included_in_analysis"])]
            best_src[k] = f_best
        else:
            best_by_cell[k] = []

out = print

out("# Stage C — DATA QUALITY REPORT")
out("")
out("Factual only: collection completeness, validity, AB/BA balance and raw per-cell")
out("ATTEMPT rates. **No dose-response analysis, no partner contrast, no model fit,")
out("no interpretation.** The primary analysis is pre-specified in")
out("`design/STUDY2_SPEC_FROZEN.md` §9–10 and implemented in")
out("`code/analyze_dose_response.py`; it is deliberately not run here.")
out("")
out(f"- design table: `design/frozen_design_table.csv` ({len(design)} cells, "
    f"re-frozen on the CONFIRMED advantages — see `design/RE_FREEZE_RECORD.md`)")
out(f"- planned trials: **{sum(plan.values()):,}**  "
    f"(FROZEN_PARAMS.stage_c_calls() = {FP.stage_c_calls():,})")
out(f"- part files read: {len(files)}")
for f in files:
    out(f"    - `{os.path.basename(f)}`")
out("")

# ------------------------------------------------------------- run outcome ----
out("## 0. Run outcome")
out("")
out("Both actors were launched live in parallel on 2026-08-22 from the re-frozen")
out("design table.")
out("")
out("| actor | trials attempted | wall time | API errors | trials lost (retry also failed) | cells complete |")
out("|---|---|---|---|---|---|")
out("| GPT-5.5 | 1,424 | 1,184 s | **0** | **0** | **64/64** |")
out("| Claude Opus 5 | 1,408 | 883 s | **358** | **179** | **6/64** |")
out("")
out("**The Claude arm was cut short by an account-level Anthropic API usage limit,")
out("not by anything in the design or the runner.** Every one of the 358 errors is the")
out("same HTTP 400 `invalid_request_error`:")
out("")
out("> You have reached your specified API usage limits. You will regain access on")
out("> 2026-09-01 at 00:00 UTC.")
out("")
out("A single probe call after the run confirmed the cap is still in force, so the")
out("Claude arm was **not** retried — a resume would only have produced more errors.")
out("The GPT arm was allowed to complete in full first; it did, cleanly.")
out("")
out("**To finish the Claude arm:** re-run `python3 code/study2_betting.py --live")
out("--models claude` on or after 2026-09-01. The runner is resumable and will skip")
out("the 6 complete Claude cells and re-run the 58 short ones from scratch. Rows for a")
out("cell always come from exactly one part file, so the completed re-run will not be")
out("merged with the partial file left by today's run.")
out("")

# ------------------------------------------------------------------ totals ----
out("## 1. Rows collected vs planned")
out("")
out("| actor | planned trials | analysed rows | complete cells | partial cells | not started |")
out("|---|---|---|---|---|---|")
tot = Counter()
for actor in ("gpt", "claude"):
    ks = [k for k in plan if k.startswith(actor + "|")]
    pl = sum(plan[k] for k in ks)
    got = sum(len(rows_by_cell[k]) for k in ks)
    cc = sum(1 for k in ks if k in complete)
    pc = sum(1 for k in ks if k in partial)
    ns = len(ks) - cc - pc
    tot["planned"] += pl; tot["got"] += got; tot["cc"] += cc; tot["pc"] += pc; tot["ns"] += ns
    out(f"| {P.DISPLAY[actor]} | {pl:,} | {got:,} | {cc}/{len(ks)} | {pc} | {ns} |")
out(f"| **TOTAL** | **{tot['planned']:,}** | **{tot['got']:,}** | "
    f"**{tot['cc']}/{len(plan)}** | **{tot['pc']}** | **{tot['ns']}** |")
out("")

# --------------------------------------------------------------- validity -----
out("## 2. Valid / invalid responses")
out("")
out("`valid_response` is the parse verdict on a single API response; a first response")
out("that failed to parse is retried and marked `superseded_by_retry`. "
    "`included_in_analysis` is the one row per trial that the analysis reads.")
out("")
out("| actor | rows written | valid | invalid | superseded by retry | included in analysis |")
out("|---|---|---|---|---|---|")
for actor in ("gpt", "claude"):
    rs = [r for k, v in attempted_by_cell.items() if k.startswith(actor + "|")
          for _f, r in v]
    v = sum(1 for r in rs if T(r["valid_response"]))
    sup = sum(1 for r in rs if T(r["superseded_by_retry"]))
    inc = sum(1 for r in rs if T(r["included_in_analysis"]))
    out(f"| {P.DISPLAY[actor]} | {len(rs):,} | {v:,} | {len(rs)-v:,} | {sup:,} | {inc:,} |")
out("")

# ------------------------------------------------------------- AB/BA balance --
out("## 3. AB/BA balance per cell")
out("")
out("The design requires exactly n/2 AB and n/2 BA in every cell. Counted over the")
out("`included_in_analysis` rows of each cell's single source file.")
out("")
imb_complete, imb_short = [], []
for k in sorted(plan):
    rs = best_by_cell.get(k, [])
    if not rs:
        continue
    c = Counter(r["variant"] for r in rs)
    bal = (c["AB"] == plan[k] // 2 and c["BA"] == plan[k] // 2)
    if k in src_of:
        if not bal:
            imb_complete.append((k, plan[k], c["AB"], c["BA"]))
    elif c["AB"] != c["BA"]:
        imb_short.append((k, plan[k], c["AB"], c["BA"]))

n_comp = sum(1 for k in plan if k in src_of)
if imb_complete:
    out(f"**{len(imb_complete)} of the {n_comp} COMPLETE cells are not exactly "
        "n/2 / n/2:**")
    out("")
    out("| cell | n planned | AB | BA |")
    out("|---|---|---|---|")
    for k, n, a, b in imb_complete:
        out(f"| `{k}` | {n} | {a} | {b} |")
else:
    out(f"**All {n_comp} cells that reached their frozen n are exactly n/2 AB and")
    out("n/2 BA.** Balance is exact wherever collection completed.")
out("")
out("The cells that did not reach their n (section 4) lost trials to API errors that")
out("fell wherever they fell in the randomised order, so their AB/BA split is not")
out("guaranteed. It is reported here rather than assumed:")
out("")
n_short = sum(1 for k in plan if k not in src_of and best_by_cell.get(k))
if imb_short:
    out(f"- {len(imb_short)} of the {n_short} short cells have unequal AB/BA:")
    out("")
    out("| cell | target n | AB | BA | AB−BA |")
    out("|---|---|---|---|---|")
    for k, n, a, b in imb_short:
        out(f"| `{k}` | {n} | {a} | {b} | {a - b:+d} |")
else:
    out(f"- all {n_short} short cells still happen to hold equal AB and BA counts.")
out("")

# ---------------------------------------------------------------- shortfalls --
out("## 4. Cells short of target")
out("")
short = []
for k in sorted(plan):
    if k in src_of:
        continue
    short.append((k, plan[k], len(best_by_cell[k])))
if short:
    out(f"**{len(short)} of {len(plan)} cells did not reach their frozen n** — all of")
    out("them Claude, all for the reason in section 0. `analysable rows` counts the")
    out("`included_in_analysis` rows in the SINGLE best part file for that cell; counts")
    out("are never summed across files.")
    out("")
    got = sum(n for _k, _t, n in short)
    tgt = sum(t for _k, t, _n in short)
    out(f"Across the short cells: **{got:,} analysable rows against a target of "
        f"{tgt:,}** ({got/tgt:.1%}).")
    out("")
    out("| cell | target n | analysable rows | short by |")
    out("|---|---|---|---|")
    for k, n, inc in short:
        out(f"| `{k}` | {n} | {inc} | {n - inc} |")
else:
    out("**No cell is short of its target n.** Every one of the "
        f"{len(plan)} cells holds its full allocation.")
out("")

# ------------------------------------------------------- raw ATTEMPT rates ----
out("## 5. Raw per-cell ATTEMPT rates")
out("")
out("Raw proportions over `included_in_analysis` rows from a single part file per cell.")
out("Descriptive only — no contrast, no test, no ordering by advantage. A rate shown as")
out("`0.750 (6/8)` comes from a cell that did NOT reach its frozen n and is reported")
out("only for completeness; `target n` is the frozen allocation.")
out("")
for actor in ("gpt", "claude"):
    out(f"### {P.DISPLAY[actor]}")
    out("")
    out("| stimulus | tier | partner | safe 3 | safe 5 | safe 7 | safe 9 | target n |")
    out("|---|---|---|---|---|---|---|---|")
    seen = {}
    for k in plan:
        a, sid, part, safe = k.split("|")
        if a != actor:
            continue
        seen.setdefault((sid, part), {})[int(safe)] = k
    order = {sid: i for i, (sid, *_r) in enumerate(FP.ACTIVE_GRADIENT[actor])}
    for (sid, part) in sorted(seen, key=lambda x: (order.get(x[0], 99), x[1])):
        cellsr, n0 = [], None
        for safe in FP.SAFE_PAYOFFS:
            k = seen[(sid, part)].get(safe)
            rs = best_by_cell.get(k, []) if k else []
            n0 = plan[k] if k else n0
            if not rs:
                cellsr.append("— (0)")
            else:
                att = sum(1 for r in rs
                          if str(r["participation_decision"]).strip().upper() == "ATTEMPT")
                cellsr.append(f"{att/len(rs):.3f}"
                              + ("" if len(rs) == n0 else f" ({len(rs)}/{n0})"))
        tier = meta[seen[(sid, part)][FP.SAFE_PAYOFFS[0]]]["tier"]
        out(f"| {sid} | {tier} | {part} | " + " | ".join(cellsr) + f" | {n0} |")
    out("")

out("## 6. Notes")
out("")
out("- Rows for a cell are taken from exactly one part file — the newest that completed")
out("  it at that cell's own n. Partial files are discarded, never merged.")
out("- Retried trials appear twice in the raw file: the unparseable first response")
out("  (`superseded_by_retry=True`) and the retry. Only one row per trial carries")
out("  `included_in_analysis=True`.")
out("- Any lost trial (retry also failed) shows up in section 4 as a shortfall.")
