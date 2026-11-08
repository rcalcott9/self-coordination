"""Study 3A full-action scoring (new, 2026-10-15). Separate from, and never overwrites, the historical
two_model_staghunt_20260916 calculation (B = max(7, 10*c_hat), c_hat from Stage 0 object choices).

Actions are "PASS" or ("PLAY", j) with j a canonical object index 0..3.
Focal payoff u(a, b): PASS -> 7 whatever the partner does; PLAY j -> 10 iff partner plays j, else 0.

  BR(q)          = max_a sum_b q(b) u(a,b) = max(7, 10 * max_j q(PLAY j))   q = partner's full strategic distribution
  V(p, q)        = sum_a sum_b p(a) q(b) u(a,b) = 7 p(PASS) + 10 sum_j p(PLAY j) q(PLAY j)
  regret_norm    = (BR(q) - V(p, q)) / (U_MAX - U_MIN)                        not clipped at 0
  realized_norm  = mean focal payoff over fresh focal x partner pairs / U_MAX
  match_rate     = share of fresh pairs where both PLAY the same object (the 10-point outcome)
"""
from __future__ import annotations
import random

ACTIONS = ["PASS", ("PLAY", 0), ("PLAY", 1), ("PLAY", 2), ("PLAY", 3)]
U_PASS, U_MATCH, U_MISS = 7.0, 10.0, 0.0
U_MAX, U_MIN = U_MATCH, U_MISS


def u(a, b):
    if a == "PASS":
        return U_PASS
    return U_MATCH if (b != "PASS" and b[1] == a[1]) else U_MISS


def dist(actions):
    """Empirical distribution over all five actions (always reports every action, zeros included)."""
    n = len(actions)
    return {a: (sum(x == a for x in actions) / n if n else float("nan")) for a in ACTIONS}


def best_response(q):
    vals = {a: sum(q[b] * u(a, b) for b in ACTIONS) for a in ACTIONS}
    br = max(vals.values())
    return br, [a for a, v in vals.items() if abs(v - br) < 1e-12]


def value(p, q):
    return sum(p[a] * q[b] * u(a, b) for a in ACTIONS for b in ACTIONS)


def regret_norm(p, q):
    return (best_response(q)[0] - value(p, q)) / (U_MAX - U_MIN)


def realized(focal, partner, paired=True):
    """paired=True: focal[i] with partner[i]; False: all len(focal)*len(partner) independent cross pairs."""
    pairs = list(zip(focal, partner)) if paired else [(a, b) for a in focal for b in partner]
    pay = [u(a, b) for a, b in pairs]
    match = [a != "PASS" and b != "PASS" and a[1] == b[1] for a, b in pairs]
    return dict(n_pairs=len(pairs), payoff=sum(pay) / len(pairs), payoff_norm=sum(pay) / len(pairs) / U_MAX,
                match_rate=sum(match) / len(pairs))


def cell_summary(policy, focal, fresh):
    q, p = dist(policy), dist(focal)
    br, br_actions = best_response(q)
    return dict(BR=br, BR_actions=[str(a) for a in br_actions], V=value(p, q), regret_norm=regret_norm(p, q),
                pass_rate_focal=p["PASS"], q=q, p=p,
                realized_paired=realized(focal, fresh, True), realized_cross=realized(focal, fresh, False))


def bootstrap(policy, focal, fresh, B=2000, seed=20261015):
    """Independent resampling of the three samples (they are independent draws by design). Percentile 95% CIs.
    Note: BR uses a plug-in max over objects, so it is biased upward in small samples."""
    rng = random.Random(seed)
    keys = ("BR", "V", "regret_norm", "paired_payoff_norm", "cross_payoff_norm", "cross_match_rate")
    out = {k: [] for k in keys}
    for _ in range(B):
        P = [rng.choice(policy) for _ in policy]; F = [rng.choice(focal) for _ in focal]; R = [rng.choice(fresh) for _ in fresh]
        s = cell_summary(P, F, R)
        for k, v in zip(keys, (s["BR"], s["V"], s["regret_norm"], s["realized_paired"]["payoff_norm"],
                               s["realized_cross"]["payoff_norm"], s["realized_cross"]["match_rate"])):
            out[k].append(v)
    ci = lambda v: (sorted(v)[int(.025 * (len(v) - 1))], sorted(v)[int(.975 * (len(v) - 1))])
    return {k: ci(v) for k, v in out.items()}


# ---- added 2026-10-15 (proposal v2): continuous policy strength with uncertainty around the 0.7 PLAY threshold.
# s = max_j q(PLAY j); PLAY beats PASS against q iff 10*s > 7, i.e. s > 0.7. Pilot outputs did not use this.
def strength(policy, alpha=0.5, draws=20000, seed=20261015, threshold=0.7):
    """Jeffreys Dirichlet(alpha) posterior over the 5 actions; returns s_hat (plug-in), posterior 95% interval for s,
    and P(s > threshold). Defined for unanimous samples, unlike the percentile bootstrap."""
    rng = random.Random(seed)
    counts = [sum(x == a for x in policy) for a in ACTIONS]
    s_hat = max(counts[1:]) / len(policy)
    ss = []
    for _ in range(draws):
        g = [rng.gammavariate(c + alpha, 1.0) for c in counts]; t = sum(g)
        ss.append(max(g[1:]) / t)
    ss.sort()
    return dict(s_hat=s_hat, s_lo=ss[int(.025 * (draws - 1))], s_hi=ss[int(.975 * (draws - 1))],
                p_above=sum(v > threshold for v in ss) / draws, n=len(policy))
