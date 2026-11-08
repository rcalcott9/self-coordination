"""
Reasoning traces from the Stage C pilot.

THE QUESTION THIS CAN NOW SETTLE. The previous Study 2 found 0 of 1,424 Stage C
rationales containing policy talk, and that was (wrongly) read as evidence the
partner manipulation had been ignored. Here the manipulation demonstrably moved
behaviour by +0.40 (GPT) and +0.12 (Claude). So if the rationales still do not
mention the partner, that is a clean DISSOCIATION between behavioural sensitivity
and verbal report - not evidence of no effect.

METHOD. The Aug-13 frozen lexicons are reused VERBATIM. No new lexicon, no
tuning. This project has twice seen a regex tweak move a headline number
(assert-and-decline 24% -> 3%; 0.268 -> 0.079), so the lexicon is treated as
fixed and rates are reported as approximate.

The rationale is the one sentence the prompt requested, extracted by stripping the
DECISION/CHOICE lines. Mean length 118 characters, so these are short - a low
mention rate is partly a length artifact and is flagged as such.
"""
import os, csv, json, re, glob
import numpy as np
import s4_common as S

SEED = 20260831
rng = np.random.default_rng(SEED)
LEX = json.load(open(os.path.join(
    os.path.dirname(S.EXP), "policy_specific_self_coordination_20260812_1401",
    "reasoning_traces", "lexicons.json")))["lexicons"]
PAT = {k: re.compile(v, re.I) for k, v in LEX.items()}
OUT = os.path.join(S.DATA, "trace_analysis.md")
L = []


def p(s=""):
    print(s); L.append(s)


def rationale(raw):
    """The requested one sentence, with the two output lines removed."""
    t = re.split(r"\bDECISION\s*:", raw, flags=re.I)[0]
    return re.sub(r"\s+", " ", t).strip()


f = sorted(glob.glob(os.path.join(S.DATA, "stageC_pilot_*.jsonl")))[-1]
rows = []
for line in open(f):
    d = json.loads(line)
    if not d["ok"]:
        continue
    dec = S.parse_decision(d["raw"])
    if dec is None:
        continue
    r = rationale(d["raw"])
    rows.append(dict(focal=d["focal"], sid=d["sid"], family=d["family"],
                     level=d["level"], same=int(d["partner_same"]),
                     safe=d["safe"], decision=dec, attempt=int(dec == "ATTEMPT"),
                     text=r, nchar=len(r),
                     **{k: int(bool(PAT[k].search(r))) for k in PAT}))

p("# Stage C pilot - reasoning traces")
p()
p(f"`{len(rows):,}` rationales. Aug-13 frozen lexicons reused verbatim; no new "
  "lexicon, no tuning. Mean rationale length "
  f"**{np.mean([r['nchar'] for r in rows]):.0f} characters** - these are one "
  "sentence by instruction, so low mention rates are partly a length artifact.")
p()


def rate(sel, key):
    v = [r[key] for r in rows if sel(r)]
    return (np.mean(v) if v else np.nan), len(v)


# ------------------------------------------------- 1. does the partner appear -
p("## 1. Does the partner reach the rationale at all?")
p()
p("Behaviour moved by +0.40 (GPT) / +0.12 (Claude). Does the language?")
p()
p("| focal | partner | n | partner_self_ref | asserts_salient | hedge_no_rule | "
  "payoff_reasoning |")
p("|---|---|---|---|---|---|---|")
for focal in ("gpt", "claude"):
    for sm, lab in ((1, "SAME"), (0, "DIFF")):
        sel = lambda r, f=focal, s=sm: r["focal"] == f and r["same"] == s
        n = rate(sel, "partner_self_ref")[1]
        cells = [f"{rate(sel, k)[0]:.3f}" for k in
                 ("partner_self_ref", "asserts_salient", "hedge_no_rule",
                  "payoff_reasoning")]
        p(f"| {S.DISPLAY[focal]} | {lab} | {n} | " + " | ".join(cells) + " |")
p()
for focal in ("gpt", "claude"):
    a = [r["partner_self_ref"] for r in rows if r["focal"] == focal and r["same"] == 1]
    b = [r["partner_self_ref"] for r in rows if r["focal"] == focal and r["same"] == 0]
    d = np.mean(a) - np.mean(b)
    pool = np.array(a + b)
    n = len(a)
    null = [pool[rng.permutation(len(pool))][:n].mean()
            - pool[rng.permutation(len(pool))][n:].mean() for _ in range(4000)]
    pv = float(np.mean(np.abs(null) >= abs(d)))
    p(f"- **{S.DISPLAY[focal]}** partner mentioned {np.mean(a)*100:.1f}% (SAME) vs "
      f"{np.mean(b)*100:.1f}% (DIFF), difference {d*100:+.1f} pp, perm p = {pv:.3f}")
p()

# ------------------------------------------- 2. the dissociation, quantified --
p("## 2. Behaviour moves; does language move with it?")
p()
p("Stimulus-level: does the rationale's partner-mention rate predict the "
  "behavioural same-vs-different entry gap on that stimulus?")
p()


def corr(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    dx, dy = x - x.mean(), y - y.mean()
    d = np.sqrt((dx ** 2).sum() * (dy ** 2).sum())
    return float((dx * dy).sum() / d) if d else np.nan


p("| focal | n stimuli | mean entry gap | mean mention rate | corr(gap, mention) |")
p("|---|---|---|---|---|")
for focal in ("gpt", "claude"):
    sids = sorted({r["sid"] for r in rows if r["focal"] == focal})
    gaps, ment = [], []
    for s in sids:
        sub = [r for r in rows if r["focal"] == focal and r["sid"] == s]
        gaps.append(np.mean([r["attempt"] for r in sub if r["same"] == 1])
                    - np.mean([r["attempt"] for r in sub if r["same"] == 0]))
        ment.append(np.mean([r["partner_self_ref"] for r in sub]))
    p(f"| {S.DISPLAY[focal]} | {len(sids)} | {np.mean(gaps):+.3f} | "
      f"{np.mean(ment):.3f} | {corr(gaps, ment):+.3f} |")
p()

# ------------------------------- 3. does language track stimulus or decision --
p("## 3. Does the rationale track the picture or the decision?")
p()
p("The Aug-25 result was that hedging tracks the DECISION, not the image. Tested "
  "here on byte-identical stimuli: holding the stimulus fixed, does hedge "
  "language rise with the safe payoff (which changes only the decision)?")
p()
p("| focal | safe | hedge rate | asserts_salient | attempt rate |")
p("|---|---|---|---|---|")
for focal in ("gpt", "claude"):
    for s in (3, 5, 7, 9):
        sel = lambda r, f=focal, sv=s: r["focal"] == f and r["safe"] == sv
        p(f"| {S.DISPLAY[focal]} | {s} | {rate(sel,'hedge_no_rule')[0]:.3f} | "
          f"{rate(sel,'asserts_salient')[0]:.3f} | {rate(sel,'attempt')[0]:.3f} |")
p()
for focal in ("gpt", "claude"):
    h = [rate(lambda r, f=focal, sv=s: r["focal"] == f and r["safe"] == sv,
              "hedge_no_rule")[0] for s in (3, 5, 7, 9)]
    p(f"- **{S.DISPLAY[focal]}** hedge rate {h[0]:.3f} -> {h[-1]:.3f} "
      f"across safe 3 -> 9 (same images throughout), change {h[-1]-h[0]:+.3f}")
p()
p("Conditional on the decision, to separate 'the payoff changed the decision' "
  "from 'the payoff changed the story':")
p()
p("| focal | safe | hedge \\| ATTEMPT | hedge \\| SAFE |")
p("|---|---|---|---|")
for focal in ("gpt", "claude"):
    for s in (3, 5, 7, 9):
        a = rate(lambda r, f=focal, sv=s: r["focal"] == f and r["safe"] == sv
                 and r["attempt"] == 1, "hedge_no_rule")
        b = rate(lambda r, f=focal, sv=s: r["focal"] == f and r["safe"] == sv
                 and r["attempt"] == 0, "hedge_no_rule")
        fa = f"{a[0]:.3f} (n={a[1]})" if a[1] else "-"
        fb = f"{b[0]:.3f} (n={b[1]})" if b[1] else "-"
        p(f"| {S.DISPLAY[focal]} | {s} | {fa} | {fb} |")
p()

# ------------------------------------------- 4. convention strength language --
p("## 4. Does language track measured convention strength?")
p()
p("| focal | level | asserts_salient | hedge_no_rule | explicit_chance | "
  "position_word |")
p("|---|---|---|---|---|---|")
for focal in ("gpt", "claude"):
    for lev in ("HIGH", "LOW"):
        sel = lambda r, f=focal, l=lev: r["focal"] == f and r["level"] == l
        cells = [f"{rate(sel,k)[0]:.3f}" for k in
                 ("asserts_salient", "hedge_no_rule", "explicit_chance",
                  "position_word")]
        p(f"| {S.DISPLAY[focal]} | {lev} | " + " | ".join(cells) + " |")
p()

# ----------------------------------------------------------- 5. examples -----
p("## 5. Sample rationales")
p()
for focal in ("gpt", "claude"):
    for lev, sm in (("HIGH", 1), ("LOW", 1), ("HIGH", 0), ("LOW", 0)):
        ex = [r for r in rows if r["focal"] == focal and r["level"] == lev
              and r["same"] == sm]
        if ex:
            e = ex[len(ex) // 3]
            p(f"- **{S.DISPLAY[focal]} {lev} "
              f"{'SAME' if sm else 'DIFF'}** ({e['decision']}, safe={e['safe']}): "
              f"\"{e['text'][:170]}\"")
p()
open(OUT, "w").write("\n".join(L) + "\n")
with open(os.path.join(S.DATA, "trace_corpus.csv"), "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
    w.writeheader(); w.writerows(rows)
print(f"\nwrote {OUT}")
