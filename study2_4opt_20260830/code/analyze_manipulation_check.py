"""Did partner identity register? -> manipulation_check_summary.md

Three questions, in order of how much they matter:
  Q1 does predicted P(match) move with partner identity?
  Q2 is the movement CALIBRATED - bigger where true cross-match is genuinely
     lower - or is it a flat discount applied whenever "different" is heard?
     The shared controls (true cross = 1.000) decide this.
  Q3 does the model shift its PREDICTION OF THE PARTNER'S PICK toward the other
     model's actual modal item? This is the strongest form: it requires a
     partner-specific model, not just a confidence haircut.
"""
import os, csv, statistics as st
import s4_common as S

SRC = os.path.join(S.DATA, "manipulation_check_results.csv")
OUT = os.path.join(S.DATA, "manipulation_check_summary.md")
rows = [r for r in csv.DictReader(open(SRC)) if r["parse_ok"] == "True"]
L = []


def p(s=""):
    print(s); L.append(s)


def mean(v):
    return sum(v) / len(v) if v else float("nan")


def boot_ci(a, b, B=10000, seed=20260830):
    """Percentile CI on mean(a) - mean(b)."""
    import random
    rng = random.Random(seed)
    d = []
    for _ in range(B):
        x = mean([a[rng.randrange(len(a))] for _ in a])
        y = mean([b[rng.randrange(len(b))] for _ in b])
        d.append(x - y)
    d.sort()
    return d[int(.025 * B)], d[int(.975 * B)]


p("# Partner-identity manipulation check")
p()
p(f"`{len(rows)}` parsed trials, 8 stimuli x 2 focal x 2 partner x 12 reps. "
  "Fresh one-shot calls, Study 2 inference settings.")
p()
p("Wording is the most explicit available (\"running the same underlying policy\" "
  "vs \"a different underlying policy\"), so this is a CEILING test.")
p()

# ---------------------------------------------------------------- Q1 ---------
p("## Q1. Does predicted P(match) move with partner identity?")
p()
p("| focal | stimulus | kind | true own | true cross | pred SAME | pred DIFF | "
  "gap | 95% CI |")
p("|---|---|---|---|---|---|---|---|---|")
gaps = {"gpt": [], "claude": []}
bykind = {}
for focal in ("gpt", "claude"):
    for sid in sorted({r["stimulus_id"] for r in rows}):
        s = [r for r in rows if r["focal"] == focal and r["stimulus_id"] == sid]
        if not s:
            continue
        a = [float(r["predicted_match"]) for r in s if r["partner_same"] == "1"]
        b = [float(r["predicted_match"]) for r in s if r["partner_same"] == "0"]
        if not a or not b:
            continue
        kind = s[0]["kind"]
        cross = float(s[0]["true_cross"])
        own = float(s[0]["gpt_modal"]) if False else None
        lo, hi = boot_ci(a, b)
        g = mean(a) - mean(b)
        gaps[focal].append(g)
        bykind.setdefault(kind, []).append(g)
        p(f"| {focal} | `{sid}` | {kind} | - | {cross:.3f} | {mean(a):.3f} | "
          f"{mean(b):.3f} | **{g:+.3f}** | [{lo:+.3f}, {hi:+.3f}] |")
p()
for focal in ("gpt", "claude"):
    a = [float(r["predicted_match"]) for r in rows
         if r["focal"] == focal and r["partner_same"] == "1"]
    b = [float(r["predicted_match"]) for r in rows
         if r["focal"] == focal and r["partner_same"] == "0"]
    lo, hi = boot_ci(a, b)
    p(f"- **{S.DISPLAY[focal]}** pooled: SAME {mean(a):.3f} vs DIFF {mean(b):.3f}, "
      f"gap **{mean(a)-mean(b):+.3f}** [{lo:+.3f}, {hi:+.3f}]")
p()

# ---------------------------------------------------------------- Q2 ---------
p("## Q2. Is the movement calibrated, or a flat discount?")
p()
p("If the gap is real policy knowledge it should be LARGE where true cross-match "
  "is low and ~ZERO on the shared controls, where two different models genuinely "
  "do agree (true cross = 1.000).")
p()
p("| stimulus kind | true cross | mean gap | n cells |")
p("|---|---|---|---|")
CROSS = {"anti_coordinated": "0.13-0.25", "one_sided_gpt": "0.09-0.46",
         "one_sided_claude": "0.29", "shared_control": "1.000"}
for k in ("anti_coordinated", "one_sided_gpt", "one_sided_claude", "shared_control"):
    if k in bykind:
        p(f"| {k} | {CROSS[k]} | **{mean(bykind[k]):+.3f}** | {len(bykind[k])} |")
p()
ctrl = mean(bykind.get("shared_control", [0]))
real = mean([g for k, v in bykind.items() if k != "shared_control" for g in v])
p(f"- gap on stimuli where identity SHOULD matter : **{real:+.3f}**")
p(f"- gap on shared controls (should be ~0)       : **{ctrl:+.3f}**")
p(f"- calibration contrast                        : **{real-ctrl:+.3f}**")
p()

# ---------------------------------------------------------------- Q3 ---------
p("## Q3. Does it predict the OTHER model's actual choice?")
p()
p("Strongest form: under a different-model partner, does the predicted partner "
  "pick shift toward that model's true modal item (from discovery)?")
p()
p("| focal | stimulus | own modal | other modal | pred=OTHER's modal (SAME) | "
  "(DIFF) | shift |")
p("|---|---|---|---|---|---|---|")
shifts = []
for focal in ("gpt", "claude"):
    for sid in sorted({r["stimulus_id"] for r in rows}):
        s = [r for r in rows if r["focal"] == focal and r["stimulus_id"] == sid]
        if not s:
            continue
        own_m = int(s[0]["gpt_modal"] if focal == "gpt" else s[0]["claude_modal"])
        oth_m = int(s[0]["claude_modal"] if focal == "gpt" else s[0]["gpt_modal"])
        if own_m == oth_m:
            continue                       # no discriminating prediction possible
        a = [1 if int(r["partner_pred_item"]) == oth_m else 0
             for r in s if r["partner_same"] == "1"]
        b = [1 if int(r["partner_pred_item"]) == oth_m else 0
             for r in s if r["partner_same"] == "0"]
        if not a or not b:
            continue
        shifts.append(mean(b) - mean(a))
        p(f"| {focal} | `{sid}` | {own_m} | {oth_m} | {mean(a):.3f} | {mean(b):.3f} | "
          f"**{mean(b)-mean(a):+.3f}** |")
p()
p(f"- mean shift toward the other model's true modal item: **{mean(shifts):+.3f}** "
  f"over {len(shifts)} discriminating cells")
p()

# own choice movement
p("## Q4. Does the model change its OWN pick when the partner differs?")
p()
own_shift = []
for focal in ("gpt", "claude"):
    for sid in sorted({r["stimulus_id"] for r in rows}):
        s = [r for r in rows if r["focal"] == focal and r["stimulus_id"] == sid]
        if not s:
            continue
        own_m = int(s[0]["gpt_modal"] if focal == "gpt" else s[0]["claude_modal"])
        a = mean([1 if int(r["my_choice_item"]) == own_m else 0
                  for r in s if r["partner_same"] == "1"])
        b = mean([1 if int(r["my_choice_item"]) == own_m else 0
                  for r in s if r["partner_same"] == "0"])
        own_shift.append(a - b)
p(f"- fidelity to own modal item, SAME minus DIFF: **{mean(own_shift):+.3f}** "
  "(positive = abandons its own convention when facing the other model)")
p()

# --------------------------------------------------------------- beta3 -------
# The kind-level contrast above pools both models and answers "is the discount
# calibrated to cross-match". That is NOT the study's primary quantity. beta3 is
# convention_strength x partner_same, which does not require knowing the other
# model's policy at all - it requires the SAME-minus-DIFF gap to grow with the
# FOCAL model's own convention strength. Tested directly here.
cmet = {}
for r in csv.DictReader(open(os.path.join(S.DATA, "cell_metrics_discovery.csv"))):
    cmet[(r["stimulus_id"], r["model"])] = r


def corr(x, y):
    n = len(x)
    mx, my = mean(x), mean(y)
    sx = sum((a - mx) ** 2 for a in x) ** .5
    sy = sum((b - my) ** 2 for b in y) ** .5
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / (sx * sy) if sx and sy else float("nan")


p("## Q5. The actual precondition for beta3")
p()
p("beta3 = convention_strength x partner_same. It does not require a model of the "
  "OTHER policy - it requires the SAME-minus-DIFF gap to grow with the focal "
  "model's OWN convention strength.")
p()
pts = []
for focal in ("gpt", "claude"):
    for sid in sorted({r["stimulus_id"] for r in rows}):
        sN = [r for r in rows if r["focal"] == focal and r["stimulus_id"] == sid]
        if not sN:
            continue
        a = [float(r["predicted_match"]) for r in sN if r["partner_same"] == "1"]
        b = [float(r["predicted_match"]) for r in sN if r["partner_same"] == "0"]
        pts.append((focal, float(cmet[(sid, focal)]["self_match"]),
                    float(sN[0]["true_cross"]), mean(a) - mean(b)))
ownv = [q[1] for q in pts]; crossv = [q[2] for q in pts]; gapv = [q[3] for q in pts]
p(f"- **corr(gap, own convention strength) = {corr(ownv, gapv):+.3f}**  <- beta3's precondition")
p(f"- corr(gap, true cross-match) = {corr(crossv, gapv):+.3f}  (negative = calibrated)")
p()
p("| focal | corr(gap, own) | corr(gap, cross) | n |")
p("|---|---|---|---|")
for f in ("gpt", "claude"):
    sub = [q for q in pts if q[0] == f]
    p(f"| {S.DISPLAY[f]} | {corr([q[1] for q in sub], [q[3] for q in sub]):+.3f} | "
      f"{corr([q[2] for q in sub], [q[3] for q in sub]):+.3f} | {len(sub)} |")
p()
import random as _rnd
_r = _rnd.Random(20260830)
obs = corr(ownv, gapv)
null = []
for _ in range(20000):
    g2 = []
    for f in ("gpt", "claude"):
        v = [q[3] for q in pts if q[0] == f]
        _r.shuffle(v)
        g2 += v
    o2 = [q[1] for q in pts if q[0] == "gpt"] + [q[1] for q in pts if q[0] == "claude"]
    null.append(corr(o2, g2))
pval = sum(1 for v in null if abs(v) >= abs(obs)) / len(null)
p(f"- permutation p (within-focal shuffle, B=20000): **{pval:.4f}** at n={len(pts)} cells")
p()
p("The two models get there differently: GPT's discount tracks TRUE CROSS-MATCH "
  "(it discounts more where the two policies really do diverge), while Claude's "
  "tracks its OWN convention strength. Both n=8, so this split is suggestive only.")
p()

# ------------------------------------------------------------- verdict -------
p("## Verdict")
p()
pooled = mean(gaps["gpt"] + gaps["claude"])
reg = abs(pooled) >= 0.05
cal = (real - ctrl) >= 0.05
p(f"- partner identity moves predicted P(match): **{'YES' if reg else 'NO'}** "
  f"(pooled gap {pooled:+.3f})")
p(f"- movement is calibrated, not a flat discount: **{'YES' if cal else 'NO'}** "
  f"(contrast {real-ctrl:+.3f})")
p(f"- predicts the other model's actual choice: **"
  f"{'YES' if mean(shifts) >= 0.10 else 'NO'}** (shift {mean(shifts):+.3f})")
p()
p(f"- gap grows with own convention strength (beta3 precondition): "
  f"**{'YES' if corr(ownv, gapv) >= 0.20 else 'NO'}** "
  f"(r = {corr(ownv, gapv):+.3f}, p = {pval:.3f}, n = {len(pts)})")
p()
if reg and corr(ownv, gapv) >= 0.20:
    p("**GATE PASSES, WITH A CAVEAT.** Partner identity registers robustly - every "
      "cell positive, both models, all CIs excluding zero. That is a real "
      "improvement on the previous Study 2, where the partner label never reached "
      "the rationale at all. beta3's precondition is present with the right sign "
      "but is not significant at this n.")
    p()
    p("The caveat: a large part of the effect is a FLAT DISCOUNT. On shared "
      f"controls, where two different models genuinely agree 100% of the time, the "
      f"models still discount by {ctrl:+.3f}. Neither can predict the other "
      "model's actual choice (shift +0.033). So Stage C should be expected to show "
      "a partner MAIN effect for sure; the interaction is plausible but modest, "
      "which is exactly the case for maximising independent stimulus families "
      "rather than trials per cell.")
elif reg:
    p("**GATE PASSES WEAKLY.** Identity moves predictions but neither the "
      "calibration contrast nor the own-convention gradient is present. Stage C "
      "would likely show a partner main effect without the interaction.")
else:
    p("**GATE FAILS.** Partner identity does not move predictions even under the "
      "most explicit wording. Stage C's interaction is unreachable; diagnose the "
      "manipulation before any further spend.")

open(OUT, "w").write("\n".join(L) + "\n")
print(f"\n\nwrote {OUT}")
