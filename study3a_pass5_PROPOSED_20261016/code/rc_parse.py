"""Parser for the reciprocal-confidence response schema (frozen rules in design/FROZEN.json 'parsing')."""
import json, re
_JSON = re.compile(r"\{.*\}", re.S)
KEYS = {"own_distribution", "partner_distribution", "expected_points", "decision", "object", "explanation"}
POS = ("PASS", "1", "2", "3", "4")

def _dist(d):
    if not isinstance(d, dict) or set(d) != set(POS): return None, "distribution keys"
    try: v = {k: float(d[k]) for k in POS}
    except (TypeError, ValueError): return None, "distribution values"
    if any(x < 0 for x in v.values()): return None, "negative probability"
    s = sum(v.values())
    if 0.97 <= s <= 1.03: return {k: x / s for k, x in v.items()}, "ok"
    if 97 <= s <= 103: return {k: x / s for k, x in v.items()}, "ok (percent rescaled)"
    return None, f"distribution sum {s:g}"

def parse(text):
    """-> (parsed dict or None, note). parsed: own, partner (position-keyed, sum 1), ev (dict or None), decision, slot, explanation."""
    m = _JSON.search(text or "")
    if not m: return None, "no JSON object"
    try: d = json.loads(m.group(0))
    except Exception as e: return None, f"invalid JSON ({type(e).__name__})"
    if not isinstance(d, dict) or set(d) != KEYS: return None, "unexpected keys"
    own, n1 = _dist(d["own_distribution"]); part, n2 = _dist(d["partner_distribution"])
    if own is None: return None, "own " + n1
    if part is None: return None, "partner " + n2
    ev = d["expected_points"]
    try: ev = {k: float(ev[k]) for k in POS} if isinstance(ev, dict) and set(ev) == set(POS) else None
    except (TypeError, ValueError): ev = None
    if d["decision"] == "PASS":
        if d["object"] not in (None, "null", ""): return None, "PASS with an object"
        slot = None
    elif d["decision"] == "PLAY":
        o = str(d["object"]).strip() if d["object"] is not None else ""
        if o not in ("1", "2", "3", "4"): return None, f"object {d['object']!r} not 1-4"
        slot = int(o)
    else: return None, f"decision {d['decision']!r}"
    notes = "; ".join(x for x in (n1, n2) if x != "ok") or "ok"
    return dict(own=own, partner=part, ev=ev, ev_note=("ok" if ev else "expected_points missing/malformed"), decision=d["decision"], slot=slot,
                explanation=str(d["explanation"])[:600]), notes

def to_canon(dist_pos, slot_to_canonical):
    """position-keyed distribution -> {'PASS': p, ('PLAY', canonical j): p}"""
    out = {"PASS": dist_pos["PASS"], ("PLAY", 0): 0.0, ("PLAY", 1): 0.0, ("PLAY", 2): 0.0, ("PLAY", 3): 0.0}
    for pos in range(1, 5): out[("PLAY", slot_to_canonical[pos - 1])] += dist_pos[str(pos)]
    return out

if __name__ == "__main__":
    ok = '{"own_distribution": {"PASS": 0.1, "1": 0, "2": 0.9, "3": 0, "4": 0}, "partner_distribution": {"PASS": 0.2, "1": 0, "2": 0.8, "3": 0, "4": 0}, "expected_points": {"PASS": 7, "1": 0, "2": 8, "3": 0, "4": 0}, "decision": "PLAY", "object": "2", "explanation": "x"}'
    tests = [
      ("valid PLAY", parse(ok)[0] is not None and parse(ok)[0]["slot"] == 2),
      ("percent rescaled", parse(ok.replace('"PASS": 0.1, "1": 0, "2": 0.9', '"PASS": 10, "1": 0, "2": 90').replace('"PASS": 0.2, "1": 0, "2": 0.8', '"PASS": 20, "1": 0, "2": 80'))[0] is not None),
      ("bad sum rejected", parse(ok.replace('"2": 0.9', '"2": 0.5'))[0] is None),
      ("PASS with object rejected", parse(ok.replace('"decision": "PLAY"', '"decision": "PASS"'))[0] is None),
      ("missing key rejected", parse(ok.replace(', "explanation": "x"', ''))[0] is None),
      ("prose around JSON tolerated", parse("Sure.\n" + ok)[0] is not None),
      ("mapping", abs(to_canon(parse(ok)[0]["partner"], [3, 0, 2, 1])[("PLAY", 0)] - 0.8) < 1e-12),
      ("malformed EV kept as None, not invalid", parse(ok.replace('"expected_points": {"PASS": 7, "1": 0, "2": 8, "3": 0, "4": 0}', '"expected_points": "n/a"'))[0]["ev"] is None),
    ]
    for n, t in tests: print(("PASS " if t else "FAIL ") + n)
    assert all(t for _, t in tests)
