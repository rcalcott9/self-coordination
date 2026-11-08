"""Follow-ups: resolve the cell-level vs trial-level conflict, and test the
within-stimulus crossover, which controls generic stimulus ambiguity exactly."""
import csv, os, numpy as np

SEED = 20260830
HERE = os.path.dirname(os.path.abspath(__file__))
recs = list(csv.DictReader(open(os.path.join(HERE, "..", "data", "cell_table.csv"))))
for r in recs:
    for k in r:
        if k not in ("model", "stimulus", "modal"):
            r[k] = float(r[k])

tm = np.array([r["true_match"] for r in recs])
sp = np.array([r["stated_p"] for r in recs])
at = np.array([r["attempt"] for r in recs])
a9 = np.array([r["attempt_safe9"] for r in recs])
mo = np.array([r["model"] for r in recs])


def corr(a, b):
    return float(np.corrcoef(a, b)[0, 1])


def partial(x, y, z):
    Z = np.c_[np.ones_like(z), z]
    rx = x - Z @ np.linalg.lstsq(Z, x, rcond=None)[0]
    ry = y - Z @ np.linalg.lstsq(Z, y, rcond=None)[0]
    return corr(rx, ry)


print("=" * 90)
print("1. CENSORING CHECK - how much dynamic range does the betting measure have?")
print("=" * 90)
print(f"  cells with pooled attempt >= 0.97 : {int((at >= 0.97).sum())} of {len(at)}")
print(f"  cells with attempt@safe=9 >= 0.95 : {int((a9 >= 0.95).sum())} of {len(a9)}")
print(f"  cells with attempt@safe=9 <= 0.05 : {int((a9 <= 0.05).sum())} of {len(a9)}")
print("  -> only the middle cells carry information; this is the known arm-3 censoring.")

print()
print("=" * 90)
print("2. SAME ANALYSIS AT safe=9 ONLY (the one payoff with real variance)")
print("=" * 90)
print(f"  corr(attempt@9, true match)              = {corr(a9, tm):+.3f}")
print(f"  corr(attempt@9, stated P)                = {corr(a9, sp):+.3f}")
print(f"  corr(attempt@9, true match | stated P)   = {partial(a9, tm, sp):+.3f}")
print(f"  corr(attempt@9, stated P | true match)   = {partial(a9, sp, tm):+.3f}")

print()
print("=" * 90)
print("3. WITHIN-STIMULUS CROSSOVER  (GPT minus Claude on the SAME image, n=6)")
print("   Differencing removes every stimulus-level generic property exactly.")
print("=" * 90)
stims = sorted(set(r["stimulus"] for r in recs))
dt, ds, da, d9 = [], [], [], []
print(f"  {'stimulus':10}{'d_true':>9}{'d_stated':>10}{'d_attempt':>11}{'d_att@9':>10}")
print("  " + "-" * 50)
for s in stims:
    g = [r for r in recs if r["stimulus"] == s and r["model"] == "gpt-5.4"][0]
    c = [r for r in recs if r["stimulus"] == s and r["model"] == "claude-opus-4-8"][0]
    a, b, cc, dd = (g["true_match"] - c["true_match"], g["stated_p"] - c["stated_p"],
                    g["attempt"] - c["attempt"], g["attempt_safe9"] - c["attempt_safe9"])
    dt.append(a); ds.append(b); da.append(cc); d9.append(dd)
    print(f"  {s:10}{a:+9.3f}{b:+10.3f}{cc:+11.3f}{dd:+10.3f}")
dt, ds, da, d9 = map(np.array, (dt, ds, da, d9))
print()
print(f"  corr(d_attempt,   d_true)   = {corr(da, dt):+.3f}")
print(f"  corr(d_attempt,   d_stated) = {corr(da, ds):+.3f}")
print(f"  corr(d_att@9,     d_true)   = {corr(d9, dt):+.3f}")
print(f"  corr(d_att@9,     d_stated) = {corr(d9, ds):+.3f}")
print(f"  corr(d_stated,    d_true)   = {corr(ds, dt):+.3f}"
      "   <- does stated confidence move with reliability across models?")

print()
print("=" * 90)
print("4. LEAVE-ONE-CELL-OUT on the two partial correlations (stability, n=12)")
print("=" * 90)
print(f"  {'dropped':28}{'true|stated':>13}{'stated|true':>13}")
print("  " + "-" * 54)
pt, ps = [], []
for i in range(len(recs)):
    k = np.arange(len(recs)) != i
    a = partial(at[k], tm[k], sp[k]); b = partial(at[k], sp[k], tm[k])
    pt.append(a); ps.append(b)
    print(f"  {recs[i]['model'] + '/' + recs[i]['stimulus']:28}{a:+13.3f}{b:+13.3f}")
print("  " + "-" * 54)
print(f"  {'range':28}{min(pt):+6.3f}..{max(pt):+.3f}   {min(ps):+6.3f}..{max(ps):+.3f}")

print()
print("=" * 90)
print("5. WHY THE TRIAL-LEVEL LOGISTIC DISAGREED: separation diagnostic")
print("=" * 90)
sat = [f"{r['model']}/{r['stimulus']}" for r in recs
       if r["attempt"] >= 0.99 or r["attempt"] <= 0.01]
print(f"  saturated cells (attempt 0 or 1): {len(sat)} of 12")
for s in sat:
    print("    ", s)
print("  A logit fit on cell-level predictors with saturated cells is quasi-separated:")
print("  the huge betas (stated_p +60.9, intercept -34.7) are the signature.")
print("  Effective n is 12 cells, not 1200 trials. The cell-level numbers are the honest ones.")

print()
print("=" * 90)
print("6. COLLINEARITY of the two predictors")
print("=" * 90)
print(f"  corr(stated P, true match) = {corr(sp, tm):+.3f}  ->  R^2 = {corr(sp, tm)**2:.3f}")
print(f"  variance inflation factor  = {1/(1-corr(sp,tm)**2):.2f}")
