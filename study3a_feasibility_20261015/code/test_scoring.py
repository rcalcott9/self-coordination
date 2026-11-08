"""Deterministic checks for scoring.py, plus a read-only cross-check against the historical estimators.
Run: /opt/anaconda3/bin/python test_scoring.py   (exits non-zero on any failure)"""
import ast, itertools, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).parent))
import scoring as S

P = lambda j: ("PLAY", j)
fails = []
def check(name, cond):
    print(("PASS " if cond else "FAIL ") + name)
    if not cond: fails.append(name)
close = lambda a, b: abs(a - b) < 1e-9

# 1. payoff table, all 25 profiles, against the prompt text (49e35910 / 8222a371)
ok = True
for a, b in itertools.product(S.ACTIONS, S.ACTIONS):
    want = 7 if a == "PASS" else (10 if (b != "PASS" and b[1] == a[1]) else 0)
    ok &= S.u(a, b) == want
check("payoff table 25/25 (PASS 7 always; PLAY j 10 iff partner PLAY j; else 0)", ok)

# 2. best response
d = lambda acts: S.dist(acts)
check("BR vs always-PASS partner = 7 (PASS)", S.best_response(d(["PASS"] * 4)) == (7.0, ["PASS"]))
check("BR vs always-PLAY(2) partner = 10 (PLAY 2)", S.best_response(d([P(2)] * 4)) == (10.0, [P(2)]))
check("BR vs 50% PASS / 50% PLAY(0) = 7: participation counts", close(S.best_response(d(["PASS", P(0)]))[0], 7.0))
check("BR vs 80% PLAY(1) = 8", close(S.best_response(d([P(1)] * 4 + ["PASS"]))[0], 8.0))
check("BR picks best object, not focal's: partner PLAY(3)x3, PLAY(0)x1 -> PLAY 3 at 7.5",
      S.best_response(d([P(3)] * 3 + [P(0)])) == (7.5, [P(3)]))
check("BR tie 70% PLAY(0) vs PASS kept as tie", set(map(str, S.best_response(d([P(0)] * 7 + ["PASS"] * 3))[1])) == {"PASS", str(P(0))})

# 3. value and regret
q = d([P(1)] * 3 + ["PASS"])
check("V(PASS, q) = 7 for any q", close(S.value(d(["PASS"]), q), 7.0))
check("regret 0 when focal plays the BR", close(S.regret_norm(d([P(1)]), q), 0.0))
check("regret (10-7)/10 = .3 when partner always PLAY(1) and focal passes", close(S.regret_norm(d(["PASS"]), d([P(1)])), 0.3))
check("regret 1.0 when partner always PLAY(1) and focal PLAY(0)", close(S.regret_norm(d([P(0)]), d([P(1)])), 1.0))
check("both always PASS -> regret 0 but realized .7 and match 0 (the known blind spot)",
      close(S.regret_norm(d(["PASS"]), d(["PASS"])), 0) and S.realized(["PASS"], ["PASS"])["match_rate"] == 0)

# 4. V equals brute-force mean over all independent cross pairs
rng = np.random.default_rng(1)
pool = list(S.ACTIONS)
F = [pool[i] for i in rng.integers(0, 5, 12)]; Q = [pool[i] for i in rng.integers(0, 5, 24)]
brute = np.mean([S.u(a, b) for a in F for b in Q])
check("V(p,q) == brute-force cross-pair mean", close(S.value(d(F), d(Q)), brute))
check("realized_cross payoff == V on the same samples", close(S.realized(F, Q, paired=False)["payoff"], S.value(d(F), d(Q))))
check("paired realized uses exactly min(n) pairs", S.realized(F, Q[:12])["n_pairs"] == 12)

# 5. cross-check: load the historical estimators read-only (function defs only, no module execution)
src_path = Path.home() / "Desktop/Superrationality/Stag/two_model_staghunt_20260916/src/analyze.py"
tree = ast.parse(src_path.read_text())
ns = {"np": np}
for node in tree.body:
    if isinstance(node, ast.FunctionDef) and node.name in ("pair_payoff", "v_hat", "c_hat_from_counts"):
        exec(compile(ast.Module([node], []), str(src_path), "exec"), ns)
H = lambda a: ("PASS", None) if a == "PASS" else ("PLAY", a[1])
ok = all(ns["pair_payoff"](H(a), H(b))[0] == S.u(a, b) for a, b in itertools.product(S.ACTIONS, S.ACTIONS))
check("historical pair_payoff agrees with u on all 25 profiles", ok)
X = [pool[i] for i in rng.integers(0, 5, 20)]
m = [sum(x == P(j) for x in X) for j in range(4)]
hist_v = ns["v_hat"](len(X), sum(x == "PASS" for x in X), m)
own = np.mean([S.u(a, b) for i, a in enumerate(X) for k, b in enumerate(X) if i != k])
check("historical v_hat == mean over distinct ordered within-sample pairs", close(hist_v, own))
# historical comparator ignores partner PASS: Stage 0 all one object (c_hat 1 -> B 10) vs partner who always passes
B_hist = max(7.0, 10.0 * ns["c_hat_from_counts"]([0, 0, 0, 20]))
check("documented discrepancy: historical B = 10 where full-action BR vs always-PASS partner = 7",
      B_hist == 10.0 and S.best_response(d(["PASS"] * 20))[0] == 7.0)

# 6. continuous strength s with Jeffreys posterior (proposal v2)
st = S.strength([P(3)] * 24)
check("s unanimous 24/24: s_hat 1, interval non-degenerate (lo < 1), P(s>.7) > .99", st["s_hat"] == 1 and st["s_lo"] < 0.999 and st["p_above"] > .99)
st = S.strength(["PASS"] * 24)
check("s all-PASS: s_hat 0, P(s>.7) ~ 0", st["s_hat"] == 0 and st["p_above"] < .001)
st = S.strength([P(2)] * 17 + ["PASS"] * 7)
check("s at 17/24 (.708, just above .7): P(s>.7) near .5", st["s_hat"] > .7 and .3 < st["p_above"] < .7)
check("s deterministic under fixed seed", S.strength([P(1)] * 15 + ["PASS"] * 9) == S.strength([P(1)] * 15 + ["PASS"] * 9))
check("10*s_hat equals BR whenever BR > 7", close(10 * S.strength([P(0)] * 20 + ["PASS"] * 4)["s_hat"], S.best_response(d([P(0)] * 20 + ["PASS"] * 4))[0]))

print(f"\n{len(fails)} failed")
sys.exit(1 if fails else 0)
