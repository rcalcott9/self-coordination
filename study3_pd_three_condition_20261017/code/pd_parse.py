"""Parser for the PD pilot response schema {"action": "A"|"B", "reason": str}. Invalid replies are recorded, never resampled."""
import json, re
_JSON = re.compile(r"\{.*\}", re.S)

def parse(text):
    """-> (dict(action, reason) or None, note)"""
    m = _JSON.search(text or "")
    if not m: return None, "no JSON object"
    try: d = json.loads(m.group(0))
    except Exception as e: return None, f"invalid JSON ({type(e).__name__})"
    if not isinstance(d, dict) or set(d) != {"action", "reason"}: return None, "unexpected keys"
    a = d["action"].strip().upper() if isinstance(d["action"], str) else None
    if a not in ("A", "B"): return None, f"action {d['action']!r} not A/B"
    return dict(action=a, reason=str(d["reason"])[:600]), "ok"

if __name__ == "__main__":
    tests = [
        ("valid A", parse('{"action": "A", "reason": "x"}')[0] == {"action": "A", "reason": "x"}),
        ("lowercase / spaces", parse('{"action": " b ", "reason": "x"}')[0]["action"] == "B"),
        ("code fence tolerated", parse('```json\n{"action": "B", "reason": "x"}\n```')[0]["action"] == "B"),
        ("extra key rejected", parse('{"action": "A", "reason": "x", "p": 1}')[0] is None),
        ("missing reason rejected", parse('{"action": "A"}')[0] is None),
        ("C rejected", parse('{"action": "C", "reason": "x"}')[0] is None),
        ("non-string rejected", parse('{"action": 1, "reason": "x"}')[0] is None),
        ("no JSON rejected", parse("I choose A")[0] is None),
        ("empty rejected", parse("")[0] is None and parse(None)[0] is None),
    ]
    for n, t in tests: print(("PASS " if t else "FAIL ") + n)
    assert all(t for _, t in tests)
