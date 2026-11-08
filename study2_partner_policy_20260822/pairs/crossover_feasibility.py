"""
Can the battery support a PARTNER-SPECIFIC COMPATIBILITY design?

The revised Study 2 wants matched stimuli whose compatibility REVERSES across
partners, so the focal model must track which convention works with a particular
partner policy rather than applying a generic "same model = safer" heuristic.

For focal GPT that means one stimulus with GG > GC and another with GC > GG;
for focal Claude, one with CC > CG and another with CG > CC.

A HARD ALGEBRAIC CONSTRAINT GOVERNS WHAT IS POSSIBLE. Every stimulus is a binary
choice between two identities. Write p and q for P(identity_1) under GPT and
Claude, and let a = |2p-1|, b = |2q-1| be how decisive each model is. Then

    GG = 1/2 + a^2/2      CC = 1/2 + b^2/2      GC = 1/2 +/- ab/2

so that, exactly,

    |GC - 1/2| = sqrt( (GG - 1/2) * (CC - 1/2) )                          (*)

The cross-model rate is pinned to the GEOMETRIC MEAN of the two own-copy rates'
deviations from chance. Only the SIGN is free — it records whether the two models
land on the same identity or opposite ones. Three consequences decide the design:

  1. "own-copy LOW but cross HIGH" is IMPOSSIBLE. If a model is near chance it
     matches every partner at almost exactly 1/2, itself included. So the
     literal Stimulus B in the brief (GPT-GPT low, GPT-Claude high) cannot exist
     for any binary stimulus, at any sample size. It is ruled out by algebra, not
     by this battery.
  2. What CAN give GC > GG is the partner being MORE decisive while agreeing:
     GC > GG exactly when CC > GG (and same modal identity). The reversal is real
     but its size is bounded by how much more decisive the partner is.
  3. The strongest incompatibility is not a low cross rate but a BELOW-CHANCE one:
     both models decisive on OPPOSITE identities drives GC toward 0. That is
     anti-coordination, and it is a much bigger lever than mere ambiguity.

This script verifies (*) against the data, classifies every stimulus, and
enumerates the reversal pairs actually available. NO API CALLS.

Run:  python3 crossover_feasibility.py
"""
import csv, math, os

HERE = os.path.dirname(os.path.abspath(__file__))
TBL = os.path.join(HERE, "cross_model_table.csv")

# Descriptive bars, printed at runtime, used only to surface candidates.
DECISIVE = 0.70    # own-copy at or above this = the model has a real convention
CHANCE_BAND = 0.10 # within this of 0.50 = indistinguishable from chance
SAL_TOL = 0.10     # Study 1's public-matching bar, carried over

rows = list(csv.DictReader(open(TBL)))
def g(r, k): return float(r[k])

print(f"""
{'='*100}
PARTNER-SPECIFIC COMPATIBILITY — is the crossover design constructible on this battery?
{'='*100}
bars in force: decisive >= {DECISIVE}, chance band +/-{CHANCE_BAND} around 0.50, salience tol {SAL_TOL}
n = 60 per model per stimulus (Stage A, GPT-5.5 / Claude Opus 5, 2026-08-12)
""")

# ---------------------------------------------------------------- verify (*)
print(f"{'-'*100}\nCHECK: does |GC - 1/2| = sqrt((GG-1/2)(CC-1/2)) hold in the data?\n{'-'*100}")
print(f"{'stimulus':<16}{'GG':>8}{'CC':>8}{'GC obs':>9}{'GC pred':>9}{'resid':>8}   agree?")
resid = []
for r in rows:
    GG, CC, GC = g(r, "own_gpt"), g(r, "own_claude"), g(r, "cross")
    pred_dev = math.sqrt(max(GG - .5, 0) * max(CC - .5, 0))
    same = r["same_modal_identity"] == "True"
    pred = .5 + pred_dev if same else .5 - pred_dev
    resid.append(abs(GC - pred))
    print(f"{r['stimulus']:<16}{GG:>8.3f}{CC:>8.3f}{GC:>9.3f}{pred:>9.3f}{GC-pred:>+8.3f}"
          f"   {'same' if same else 'OPPOSITE'}")
print(f"\nmean |residual| = {sum(resid)/len(resid):.4f}, max = {max(resid):.4f}"
      "  (sampling noise only; the identity is exact in the limit)")

# ------------------------------------------------------- classify + reversals
print(f"\n{'-'*100}\nPER-STIMULUS COMPATIBILITY, from each focal model's point of view\n{'-'*100}")
print(f"{'stimulus':<16}{'GG':>7}{'CC':>7}{'GC':>7}{'GC-GG':>8}{'GC-CC':>8}{'sal':>7}   class")
cls = {}
for r in rows:
    GG, CC, GC = g(r, "own_gpt"), g(r, "own_claude"), g(r, "cross")
    dec_g, dec_c = GG >= DECISIVE, CC >= DECISIVE
    if not dec_g and not dec_c:
        k = "neither decisive (dead)"
    elif GC < .5 - CHANCE_BAND:
        k = "ANTI-COORDINATED"
    elif dec_g and dec_c and GC >= DECISIVE:
        k = "shared convention"
    elif dec_g and not dec_c:
        k = "GPT-only convention"
    elif dec_c and not dec_g:
        k = "Claude-only convention"
    else:
        k = "mixed"
    cls[r["stimulus"]] = k
    print(f"{r['stimulus']:<16}{GG:>7.3f}{CC:>7.3f}{GC:>7.3f}{GC-GG:>+8.3f}{GC-CC:>+8.3f}"
          f"{g(r,'generic_salience'):>7.3f}   {k}")

for focal, own_k, part_lbl in (("GPT", "own_gpt", "Claude"), ("Claude", "own_claude", "GPT")):
    print(f"\n{'-'*100}\nFOCAL {focal}: reversal pairs (one stimulus favours the SELF partner, "
          f"the other favours {part_lbl})\n{'-'*100}")
    selfish = [r for r in rows if g(r, own_k) - g(r, "cross") > 0.20]
    partnerish = [r for r in rows if g(r, "cross") - g(r, own_k) > 0.05]
    print(f"  favours SELF partner (own - cross > 0.20): "
          f"{', '.join(x['stimulus'] for x in selfish) or 'NONE'}")
    print(f"  favours {part_lbl} partner (cross - own > 0.05): "
          f"{', '.join(x['stimulus'] for x in partnerish) or 'NONE'}")
    if not selfish or not partnerish:
        print("  -> no reversal pair available")
        continue
    print(f"\n  {'A (self-compatible)':<22}{'B (partner-compatible)':<24}"
          f"{'gap|self':>10}{'gap|part':>10}{'interaction':>13}{'d_sal':>8}")
    best = []
    for A in selfish:
        for B in partnerish:
            gap_self = g(A, own_k) - g(B, own_k)          # A minus B, self partner
            gap_part = g(A, "cross") - g(B, "cross")      # A minus B, other partner
            inter = gap_self - gap_part
            dsal = abs(g(A, "generic_salience") - g(B, "generic_salience"))
            best.append((inter, A["stimulus"], B["stimulus"], gap_self, gap_part, dsal))
    for inter, a, b, gs, gp, ds in sorted(best, reverse=True):
        flag = "" if ds <= SAL_TOL else f"  <- fails salience bar ({SAL_TOL})"
        print(f"  {a:<22}{b:<24}{gs:>+10.3f}{gp:>+10.3f}{inter:>+13.3f}{ds:>8.3f}{flag}")
