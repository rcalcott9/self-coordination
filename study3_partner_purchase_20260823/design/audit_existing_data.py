#!/usr/bin/env python3
"""
DESIGN AUDIT for the revealed-preference redesign ("Study 3").

No API calls. Reads only what already exists:

  design/confirmed_compatibility.csv   partner-BLIND policies at n=180/120/60
                                       (the Aug-22 confirmation battery)
  data/study2C_*.csv                   partner-AWARE form choices from the failed
                                       Study 2 (ATTEMPT trials only -> selected)

and reports, per focal model x stimulus:

  p_same, p_cross      under each information context
  advantage            p_same - p_cross
  k_star               indifference cost = 10 - 10*p_cross/p_same
  DeltaEV(k)           (10-k)*p_same - 10*p_cross

The point of running both contexts is to answer the one question that decides
whether the calibration phase can be skipped: does telling the model who its
partner is move its choice policy at all?
"""
import csv, glob, os, collections, math

EXP = ("/Users/calypsocalcott/Desktop/Coordination/Self_Coordination/"
       "study2_partner_policy_20260822")

# ---------------------------------------------------------------- helpers ---
def self_match_unbiased(counts):
    """P(two independent draws from this policy agree), same-draw pairs removed."""
    n = sum(counts.values())
    if n < 2:
        return None, n
    num = sum(c * (c - 1) for c in counts.values())
    return num / (n * (n - 1)), n


def cross_match(c1, c2):
    """P(a draw from policy 1 agrees with an independent draw from policy 2)."""
    n1, n2 = sum(c1.values()), sum(c2.values())
    if n1 == 0 or n2 == 0:
        return None, min(n1, n2)
    keys = set(c1) | set(c2)
    return sum((c1.get(k, 0) / n1) * (c2.get(k, 0) / n2) for k in keys), min(n1, n2)


def kstar(p_same, p_cross):
    """Cost at which (10-k)*p_same == 10*p_cross. <0 means the copy never pays."""
    if not p_same:
        return None
    return 10.0 - 10.0 * p_cross / p_same


def dev(p_same, p_cross, k):
    return (10.0 - k) * p_same - 10.0 * p_cross


# ------------------------------------------- 1. partner-BLIND confirmation ---
conf = {r["stimulus"]: r for r in
        csv.DictReader(open(os.path.join(EXP, "design/confirmed_compatibility.csv")))}

print("=" * 108)
print("1.  PARTNER-BLIND POLICIES  (confirmation battery, Stage A prompt, no partner named)")
print("=" * 108)
print(f"{'stimulus':16s}{'n/model':>9}{'p_same(G)':>11}{'p_same(C)':>11}{'p_cross':>10}"
      f"{'adv_G':>9}{'adv_C':>9}{'k*_G':>8}{'k*_C':>8}")
blind = {}
for s, r in conf.items():
    GG, CC, GC = float(r["GG"]), float(r["CC"]), float(r["GC"])
    n = int(r["n_gpt"])
    blind[s] = dict(GG=GG, CC=CC, GC=GC, n=n)
    ksg, ksc = kstar(GG, GC), kstar(CC, GC)
    print(f"{s:16s}{n:>9}{GG:>11.3f}{CC:>11.3f}{GC:>10.3f}"
          f"{GG-GC:>+9.3f}{CC-GC:>+9.3f}{ksg:>8.2f}{ksc:>8.2f}")

# ------------------------------------------- 2. partner-AWARE from Study 2 ---
rows = []
for f in glob.glob(os.path.join(EXP, "data/study2C_2026*.csv")):
    if "DRY" in f or "MERGED" in f:
        continue
    rows += [r for r in csv.DictReader(open(f))]
inc = [r for r in rows
       if r.get("included_in_analysis") in ("True", "1", "true")
       and r.get("parsed_choice_identity") not in (None, "", "NONE")]

# policy[(actor, stimulus, partner_condition)] -> Counter(identity)
pol = collections.defaultdict(collections.Counter)
att = collections.Counter()
tot = collections.Counter()
for r in rows:
    if r.get("included_in_analysis") not in ("True", "1", "true"):
        continue
    key = (r["actor_model"], r["stimulus"], r["partner_condition"])
    tot[key] += 1
    if r.get("participation_decision") == "ATTEMPT":
        att[key] += 1
        ident = r.get("parsed_choice_identity")
        if ident and ident != "NONE":
            pol[key][ident] += 1

print()
print("=" * 108)
print("2.  PARTNER-AWARE POLICIES  (Study 2 Stage C; ATTEMPT trials only -> SELECTED SAMPLE)")
print("=" * 108)
stims = sorted({k[1] for k in pol})
print(f"{'stimulus':16s}{'p_same(G)':>11}{'p_same(C)':>11}{'p_cross':>10}"
      f"{'adv_G':>9}{'adv_C':>9}{'n_G':>7}{'n_C':>7}   selection (attempt rate)")
aware = {}
for s in stims:
    # focal GPT playing a GPT copy  -> GPT's policy when told partner = same
    g_same = pol.get(("gpt", s, "same"), collections.Counter())
    g_diff = pol.get(("gpt", s, "different"), collections.Counter())
    c_same = pol.get(("claude", s, "same"), collections.Counter())
    c_diff = pol.get(("claude", s, "different"), collections.Counter())
    ps_g, ng = self_match_unbiased(g_same)
    ps_c, nc = self_match_unbiased(c_same)
    # cross: GPT told "partner is Claude"  x  Claude told "partner is GPT"
    pc, npc = cross_match(g_diff, c_diff)
    if None in (ps_g, ps_c, pc):
        continue
    aware[s] = dict(GG=ps_g, CC=ps_c, GC=pc, n_g=ng, n_c=nc)
    ar_g = att[("gpt", s, "same")] / max(1, tot[("gpt", s, "same")])
    ar_c = att[("claude", s, "same")] / max(1, tot[("claude", s, "same")])
    print(f"{s:16s}{ps_g:>11.3f}{ps_c:>11.3f}{pc:>10.3f}"
          f"{ps_g-pc:>+9.3f}{ps_c-pc:>+9.3f}{ng:>7}{nc:>7}   G {ar_g:.2f} / C {ar_c:.2f}")

# ------------------------------------------------ 3. does the frame move it? --
print()
print("=" * 108)
print("3.  DOES NAMING THE PARTNER MOVE THE POLICY?   blind -> aware, same stimulus")
print("=" * 108)
print(f"{'stimulus':16s}{'p_same(G)':>22}{'p_same(C)':>22}{'p_cross':>22}")
print(f"{'':16s}{'blind   aware   d':>22}{'blind   aware   d':>22}{'blind   aware   d':>22}")
deltas = []
for s in sorted(set(blind) & set(aware)):
    b, a = blind[s], aware[s]
    row = f"{s:16s}"
    for key in ("GG", "CC", "GC"):
        d = a[key] - b[key]
        deltas.append(abs(d))
        row += f"{b[key]:>8.3f}{a[key]:>8.3f}{d:>+7.3f}"
    print(row)
print(f"\nmean |change| across {len(deltas)} cells = {sum(deltas)/len(deltas):.3f}")

# ------------------------------------------------------- 4. the algebra bar --
print()
print("=" * 108)
print("4.  STRUCTURAL BOUND ON THE DESIGN")
print("=" * 108)
print("""For a two-alternative stimulus, p_same is the collision probability of the focal
policy with itself, so p_same = 1/2 + a^2/2 with a = |2p-1|.  THEREFORE p_same >= 0.50
ALWAYS: a model can never match a copy of itself below chance.  p_cross = 1/2 +/- a*b/2
is free in sign.  A NEGATIVE-ADVANTAGE cell (p_cross > p_same) therefore requires the
OTHER model to be more decisive than the focal model AND to agree with it -- it cannot
be manufactured by making the focal model erratic.""")

print()
print("Negative-advantage cells available (advantage < -0.02), partner-blind:")
found = False
for s, b in blind.items():
    for focal, own in (("gpt", b["GG"]), ("claude", b["CC"])):
        adv = own - b["GC"]
        if adv < -0.02:
            print(f"    focal {focal:7s} {s:16s} p_same={own:.3f} p_cross={b['GC']:.3f} "
                  f"adv={adv:+.3f}  k*={kstar(own, b['GC']):+.2f}")
            found = True
if not found:
    print("    NONE")

# ------------------------------------------------------- 5. DeltaEV surface --
print()
print("=" * 108)
print("5.  DeltaEV(k) SURFACE, partner-blind estimates  [(10-k)*p_same - 10*p_cross]")
print("=" * 108)
GRID = [0, 1, 2, 3, 4, 5]
print(f"{'focal':7s}{'stimulus':16s}{'p_same':>8}{'p_cross':>9}{'k*':>7}   " +
      "".join(f"k={k:<6}" for k in GRID))
cells = []
for s, b in sorted(blind.items()):
    for focal, own in (("gpt", b["GG"]), ("claude", b["CC"])):
        ks = kstar(own, b["GC"])
        cells.append((focal, s, own, b["GC"], ks))
        line = f"{focal:7s}{s:16s}{own:>8.3f}{b['GC']:>9.3f}{ks:>7.2f}   "
        line += "".join(f"{dev(own, b['GC'], k):>+7.2f}" for k in GRID)
        print(line)

print()
print("k* distribution across the 16 focal x stimulus cells:")
kk = sorted(c[4] for c in cells)
print("   ", " ".join(f"{v:+.2f}" for v in kk))
print(f"    min {min(kk):+.2f}  median {kk[len(kk)//2]:+.2f}  max {max(kk):+.2f}")
