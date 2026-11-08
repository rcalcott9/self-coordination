"""PROPOSED analysis for the Study 3A policy-knowledge pilot (2026-10-16). New module; imports the existing
study3a scoring.py read-only and never edits it. Actions/forecasts are over 5 canonical actions:
PASS, PLAY0..PLAY3 (object identity, mapped from screen position by each call's slot_to_canonical).

Policy descriptors of a distribution q (participation-inclusive):
  pi = 1 - q(PASS)                 participation
  c  = max_j q(PLAY j) / pi        conditional object concentration (undefined if pi = 0)
  h  = max_a q(a)                  overall action concentration (consistent PASS gives h = 1, s = 0)
  s  = max_j q(PLAY j) = pi * c    PLAY opportunity against a partner with policy q (PLAY beats PASS iff s > .7)
Screening (to be applied to NEW independent COPY policy draws; Jeffreys Dirichlet(1/2) posterior):
  strong-PLAY if P(s > .7) >= .9;  diffuse if P(h < .6) >= .9;  concentrated-PASS if P(q(PASS) > .7) >= .9;  else intermediate.
  All items are kept and reported whatever their class; no replacement or relabelling."""
import json, random, re, sys
from pathlib import Path
sys.path.insert(0, str(Path.home() / "Desktop/Coordination/Self_Coordination/study3a_feasibility_20261015/code"))
import scoring as S                                    # historical/feasibility scoring, read-only

A = S.ACTIONS                                         # ["PASS", ("PLAY",0..3)]
_JSON = re.compile(r"\{.*\}", re.S)

def to_canon(slot_probs, slot_to_canonical):
    """{'PASS': x, '1'..'4': y} in percent -> dict over canonical actions (sums to 1)."""
    out = {a: 0.0 for a in A}; out["PASS"] = slot_probs["PASS"] / 100
    for pos in range(1, 5): out[("PLAY", slot_to_canonical[pos - 1])] += slot_probs[str(pos)] / 100
    return out

def parse_forecast_obj(d):
    if not isinstance(d, dict) or set(d) != {"PASS", "1", "2", "3", "4"}: return None, "forecast keys"
    try: v = {k: float(d[k]) for k in d}
    except (TypeError, ValueError): return None, "forecast values"
    if any(x < 0 or x > 100 for x in v.values()): return None, "forecast range"
    tot = sum(v.values())
    if not 95 <= tot <= 105: return None, f"forecast sum {tot:g}"
    return {k: x * 100 / tot for k, x in v.items()}, "ok"          # renormalise small rounding error only

def parse_forecast(text):
    m = _JSON.search(text or "")
    if not m: return None, "no JSON"
    try: d = json.loads(m.group(0))
    except Exception as e: return None, f"invalid JSON ({type(e).__name__})"
    return parse_forecast_obj(d)

def parse_forecast_then_act(text):
    m = _JSON.search(text or "")
    if not m: return None, None, "no JSON"
    try: d = json.loads(m.group(0))
    except Exception as e: return None, None, f"invalid JSON ({type(e).__name__})"
    if not isinstance(d, dict) or set(d) != {"forecast", "decision", "object"}: return None, None, "keys"
    f, note = parse_forecast_obj(d["forecast"])
    if f is None: return None, None, note
    if d["decision"] == "PASS" and d["object"] in (None, "null", ""): return f, ("PASS", None), "ok"
    if d["decision"] == "PLAY" and str(d["object"]).strip() in ("1", "2", "3", "4"): return f, ("PLAY", int(str(d["object"]).strip())), "ok"
    return None, None, "decision/object"

def descriptors(q):
    pi = 1 - q["PASS"]; s = max(q[a] for a in A[1:])
    return dict(pi=pi, c=(s / pi if pi > 0 else None), h=max(q.values()), s=s)

def posterior_class(actions, draws=20000, seed=20261016):
    counts = [sum(x == a for x in actions) for a in A]; rng = random.Random(seed)
    ps = ph = pp = 0
    for _ in range(draws):
        g = [rng.gammavariate(c + .5, 1.0) for c in counts]; t = sum(g); q = [x / t for x in g]
        ps += max(q[1:]) > .7; ph += max(q) < .6; pp += q[0] > .7
    P = dict(P_s_gt_07=ps / draws, P_h_lt_06=ph / draws, P_pass_gt_07=pp / draws)
    cls = ("strong-PLAY" if P["P_s_gt_07"] >= .9 else "concentrated-PASS" if P["P_pass_gt_07"] >= .9
           else "diffuse" if P["P_h_lt_06"] >= .9 else "intermediate")
    return cls, P

def mean_forecast(fs):
    return {a: sum(f[a] for f in fs) / len(fs) for a in A}

def tvd(f, q): return 0.5 * sum(abs(f[a] - q[a]) for a in A)
def brier(f, q): return sum(q[b] * sum((f[a] - (a == b)) ** 2 for a in A) for b in A)   # expected multiclass Brier vs draws from q

def implied_br(f):
    """Best response to a forecast f of the partner: PASS (7) vs PLAY j (10 f(PLAY j)); ties kept."""
    v = {a: (7.0 if a == "PASS" else 10.0 * f[a]) for a in A}; m = max(v.values())
    return [a for a in A if abs(v[a] - m) < 1e-12]

def regret(actions, q_actions):
    """Same-q plug-in normalized regret (>= 0 by construction). q from the INDEPENDENT partner-policy sample."""
    return S.regret_norm(S.dist(actions), S.dist(q_actions))

def realized_shortfall(actions, q_actions, fresh_actions):
    """Independent shortfall: BR from the policy sample minus realized payoff vs fresh partners (can be negative)."""
    return (S.best_response(S.dist(q_actions))[0] - S.realized(actions, fresh_actions, paired=False)["payoff"]) / 10

def item_bootstrap(values, B=4000, seed=20261016):
    rng = random.Random(seed); n = len(values)
    if n < 2: return (None, None)
    m = sorted(sum(rng.choice(values) for _ in range(n)) / n for _ in range(B))
    return (m[int(.025 * (B - 1))], m[int(.975 * (B - 1))])
