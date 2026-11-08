"""Stage 0 - MINIMUM probe that claude-opus-4-7 is served and parses through the pipeline.

ONE API call. Uses the established path end to end: the real four-option prompt (d40ea45d),
a real rendered array, s4_common.ask_claude's exact request surface, and s4_common.parse_choice.
That verifies availability, alias resolution, image handling and parser compatibility together.
"""
import json, os, sys, time
from datetime import datetime, timezone

S4 = "/Users/calypsocalcott/Desktop/Coordination/Self_Coordination/study2_4opt_20260830/code"
EXP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, S4)
import s4_common as S

REQUESTED = "claude-opus-4-7"
ARRAY, PERM = "m4_contour_v4", 0

img = S.b64(os.path.join(EXP, "stimuli5", ARRAY, f"perm{PERM:02d}.png"))
cl = S.make_clients()["claude"]
t0 = time.time()
rec = dict(requested_checkpoint=REQUESTED, array=ARRAY, perm=PERM,
           prompt_sha8=S.PROMPT_SHA["stage_a"],
           ts_utc=datetime.now(timezone.utc).isoformat())
try:
    r = cl.messages.create(
        model=REQUESTED, max_tokens=S.CLAUDE_MAX_TOKENS,
        thinking={"type": "adaptive", "display": "summarized"},
        output_config={"effort": "low"},
        messages=[{"role": "user", "content": [
            {"type": "image", "source": {"type": "base64", "media_type": "image/png",
                                         "data": img}},
            {"type": "text", "text": S.STAGE_A_PROMPT}]}])
    txt = "".join(b.text for b in r.content if getattr(b, "type", "") == "text")
    rec.update(ok=True, returned_checkpoint=r.model, raw_response=txt,
               stop_reason=getattr(r, "stop_reason", None),
               usage=dict(input_tokens=getattr(r.usage, "input_tokens", None),
                          output_tokens=getattr(r.usage, "output_tokens", None)),
               secs=round(time.time() - t0, 2))
    pos = S.parse_choice(txt)
    rec.update(parsed_position=(None if pos is None else pos + 1), parse_ok=pos is not None)
    man = json.load(open(os.path.join(EXP, "stimuli5", ARRAY, "manifest.json")))
    rec["parsed_canonical_item"] = None if pos is None else man[str(PERM)][pos]
except Exception as e:
    rec.update(ok=False, error=f"{type(e).__name__}: {e}", secs=round(time.time() - t0, 2))

rec["alias_resolved_cleanly"] = bool(rec.get("ok") and
                                     REQUESTED in (rec.get("returned_checkpoint") or ""))
out = os.path.join(EXP, "probe_opus47", "probe_result.json")
json.dump(rec, open(out, "w"), indent=1)
print(json.dumps({k: v for k, v in rec.items() if k != "raw_response"}, indent=1))
print("\nraw_response:", repr(rec.get("raw_response"))[:400])
print("\nwrote", out)
