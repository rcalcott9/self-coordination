"""Call and cost model. One trial = one API call. Input-token counts are the
MEASURED Study 1 values (README 'Cost and runtime'); Study 1's realised
4,800 calls at $75-110 all-in anchors the per-call rate."""
N_STIM, N_PAIRS = 72, 24
NA, NB, NC, PAYOFFS = 60, 30, 30, 4
S1_CALLS, S1_LO, S1_HI = 4800, 75.0, 110.0
RATE_LO, RATE_HI = S1_LO/S1_CALLS, S1_HI/S1_CALLS

phases = [
 ("Stage A  own-copy ground truth", f"{N_STIM} stim x 2 models x {NA}", N_STIM*2*NA, 1),
 ("Stage B  auditor_prediction",    f"{N_STIM} stim x 2 focal x {NB}",  N_STIM*2*NB, 1),
 ("Stage B  generic_salience",      f"{N_STIM} stim x 2 raters x {NB}", N_STIM*2*NB, 1),
 ("Stage B  self_stated_confidence",f"{N_STIM} stim x 2 focal x {NB}",  N_STIM*2*NB, 1),
 ("Stage C  ATTEMPT vs SAFE",       f"{N_PAIRS} pairs x 2 x {PAYOFFS} x {NC}", N_PAIRS*2*PAYOFFS*NC, 2),
]
print(f"{'phase':<34}{'shape':<34}{'calls':>8}{'$ all-in':>15}")
p1=p2=0
for name, shape, calls, ph in phases:
    print(f"{name:<34}{shape:<34}{calls:>8,}{f'${calls*RATE_LO:,.0f}-{calls*RATE_HI:,.0f}':>15}")
    if ph==1: p1+=calls
    else: p2+=calls
tot=p1+p2
print("-"*91)
print(f"{'PHASE 1 (A + B) — gated':<68}{p1:>8,}{f'${p1*RATE_LO:,.0f}-{p1*RATE_HI:,.0f}':>15}")
print(f"{'PHASE 2 (C) — only if Phase 1 yields >=20 pairs':<68}{p2:>8,}{f'${p2*RATE_LO:,.0f}-{p2*RATE_HI:,.0f}':>15}")
print(f"{'TOTAL':<68}{tot:>8,}{f'${tot*RATE_LO:,.0f}-{tot*RATE_HI:,.0f}':>15}")
print(f"\nStudy 1: {S1_CALLS:,} calls, ${S1_LO:.0f}-{S1_HI:.0f}.  This design = {tot/S1_CALLS:.1f}x the calls.")
print("\nLevers, if the total needs to come down:")
for label, saved in [
    ("drop safe=3 (observed gap exactly 0.000 - pure ceiling)", N_PAIRS*2*1*NC),
    ("self-confidence on paired stimuli only (~48 cells, not 144)", (N_STIM*2-48)*NB),
    ("battery 72 -> 60 stimuli (yield ~20 pairs, not ~25)", (72-60)*2*(NA+3*NB)),
    ("single focal model instead of two", tot//2)]:
    print(f"  -{saved:>6,} calls  (${saved*RATE_LO:,.0f}-{saved*RATE_HI:,.0f})   {label}")
