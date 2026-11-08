"""Full-action scoring with a configurable PASS payoff (new module; the historical scoring.py with PASS=7 is unchanged).
Actions: 'PASS' or ('PLAY', j), j canonical 0..3. PASS -> pass_value always; PLAY j -> 10 iff partner PLAY j, else 0."""
ACTIONS = ["PASS", ("PLAY", 0), ("PLAY", 1), ("PLAY", 2), ("PLAY", 3)]

def u(a, b, pass_value):
    if a == "PASS": return float(pass_value)
    return 10.0 if (b != "PASS" and b[1] == a[1]) else 0.0

def dist(xs):
    n = len(xs); return {a: (sum(x == a for x in xs) / n if n else float("nan")) for a in ACTIONS}

def best_response(q, pass_value):
    vals = {a: sum(q[b] * u(a, b, pass_value) for b in ACTIONS) for a in ACTIONS}; m = max(vals.values())
    return m, [a for a, v in vals.items() if abs(v - m) < 1e-12]

def value(p, q, pass_value):
    return sum(p[a] * q[b] * u(a, b, pass_value) for a in ACTIONS for b in ACTIONS)

def regret_norm(p, q, pass_value):
    """(max(PASS, 10 max_j q_j) - [PASS p_PASS + 10 sum_j p_j q_j]) / 10 ; same-q plug-in, >= 0."""
    return (best_response(q, pass_value)[0] - value(p, q, pass_value)) / 10.0

def pairs_stats(pairs, pass_value):
    """pairs of (focal action, partner action): focal payoff, dyadic mean payoff, joint shortfall vs 10, match rate."""
    if not pairs: return None
    f = [u(a, b, pass_value) for a, b in pairs]; g = [u(b, a, pass_value) for a, b in pairs]
    dy = [(x + y) / 2 for x, y in zip(f, g)]
    match = [a != "PASS" and b != "PASS" and a[1] == b[1] for a, b in pairs]
    return dict(focal_payoff_norm=sum(f) / len(f) / 10, dyadic_payoff_norm=sum(dy) / len(dy) / 10,
                joint_shortfall=(10 - sum(dy) / len(dy)) / 10, match_rate=sum(match) / len(match), n_pairs=len(pairs))

if __name__ == "__main__":
    import itertools, random
    P = lambda j: ("PLAY", j); ok = []
    ok.append(("payoff table PASS=5", all(u(a, b, 5) == (5 if a == "PASS" else 10 if (b != "PASS" and b[1] == a[1]) else 0) for a, b in itertools.product(ACTIONS, ACTIONS))))
    ok.append(("BR vs always PLAY0 = 10", best_response(dist([P(0)] * 4), 5)[0] == 10))
    ok.append(("BR vs 60% PLAY0 (> .5) = 6 PLAY", best_response(dist([P(0)] * 3 + ["PASS"] * 2), 5) == (6.0, [P(0)])))
    ok.append(("BR at exactly .5 is a tie", set(map(str, best_response(dist([P(0)] * 2 + ["PASS"] * 2), 5)[1])) == {"PASS", str(P(0))}))
    ok.append(("PASS=7 reproduces historical regret", abs(regret_norm(dist(["PASS"]), dist([P(1)]), 7) - .3) < 1e-12))
    rng = random.Random(1)
    ok.append(("same-q regret >= 0 (5,000 random)", min(regret_norm(dist([rng.choice(ACTIONS) for _ in range(12)]), dist([rng.choice(ACTIONS) for _ in range(24)]), 5) for _ in range(5000)) >= 0))
    st = pairs_stats([(P(1), P(1)), ("PASS", P(1)), (P(2), "PASS")], 5)
    ok.append(("dyadic shortfall: (10 - mean[(10+10)/2,(5+0)/2,(0+5)/2])/10", abs(st["joint_shortfall"] - (10 - (10 + 2.5 + 2.5) / 3) / 10) < 1e-12 and abs(st["match_rate"] - 1 / 3) < 1e-12))
    ok.append(("all PASS: regret 0 vs PASS partner, shortfall .5, match 0", regret_norm(dist(["PASS"]), dist(["PASS"]), 5) == 0 and pairs_stats([("PASS", "PASS")], 5)["joint_shortfall"] == .5))
    for n, t in ok: print(("PASS " if t else "FAIL ") + n)
    assert all(t for _, t in ok)
