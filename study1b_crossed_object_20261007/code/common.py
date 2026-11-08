"""Study 1b (crossed object-level prediction): shared primitives. No calls happen on import.

Request kwargs mirror the frame calibration run exactly (pc_common.ask_gpt / ask_claude); the
D-017 thinking-off assertions are reused from pc_common. Orderings are balanced Latin squares
from str-seeded RNGs, which are deterministic across processes.
"""
import hashlib, json, os, random, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)
SC = os.path.dirname(STUDY)
SPC = os.path.join(SC, "study_policy_convergence_20260909")
STIM = os.path.join(SC, "study2_4opt_20260830", "stimuli")
FRAME_CSV = os.path.join(SPC, "runs", "visual_frame", "visual_frame_20260909_204609.csv")
sys.path.insert(0, os.path.join(SPC, "runners"))
sys.path.insert(0, HERE)
import pc_common as P                                                  # noqa: E402

PY = "/opt/anaconda3/bin/python"
MODELS = {
    "gpt": {"model_id": "gpt-5.5-2026-04-23", "provider": "openai.responses",
            "settings": {"reasoning": {"effort": "low", "summary": "auto"}}, "surface": "reasoning.effort=low"},
    "claude": {"model_id": "claude-opus-5", "provider": "anthropic.messages",
               "settings": {"thinking": {"type": "disabled"}, "max_tokens": 1024}, "surface": "thinking=disabled",
               "alias_note": "no dated snapshot; identity certified to the alias on the run date only"},
}
RATE = {("gpt", "REF"): 0.0082, ("gpt", "PRED"): 0.0115,
        ("claude", "REF"): 0.0056, ("claude", "PRED"): 0.0063}
CALIB_SHA8 = "d40ea45d"
CODE_FILES = ["common.py", "prompts.py", "freeze_screen.py", "select_arrays.py", "freeze_main.py", "run.py"]


def sha256f(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def sha8(s):
    return hashlib.sha256(s.encode()).hexdigest()[:8]


def code_sha8():
    d = {f: sha256f(os.path.join(HERE, f))[:8] for f in CODE_FILES if os.path.exists(os.path.join(HERE, f))}
    d["pc_common.py"] = sha256f(os.path.join(SPC, "runners", "pc_common.py"))[:8]
    return d


def verify_code(frozen_code):
    live = code_sha8()
    bad = {k: (live.get(k), v) for k, v in frozen_code.items() if live.get(k) != v}
    if bad:
        sys.exit(f"ABORT: code changed since freeze: {bad}")


def write_frozen(path, obj):
    json.dump(obj, open(path, "w"), indent=1)
    h = sha256f(path)
    open(path.replace(".json", ".sha256"), "w").write(f"{h}  {os.path.basename(path)}\n")
    return h


def load_frozen(path):
    want = open(path.replace(".json", ".sha256")).read().split()[0]
    got = sha256f(path)
    if got != want:
        sys.exit(f"ABORT: {os.path.basename(path)} sha256 {got[:16]} != frozen {want[:16]}")
    return json.load(open(path)), got[:8]


def calib_prompt():
    """STAGE_A_PROMPT rendered from s4_common source without importing it (import loads credentials)."""
    import ast
    s4 = os.path.join(SC, "study2_4opt_20260830", "code", "s4_common.py")
    env = {}
    for n in ast.parse(open(s4).read()).body:
        if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") in ("BASE", "CHOICE_FORMAT", "STAGE_A_PROMPT"):
            exec(compile(ast.Module([n], []), s4, "exec"), env)
    p = env["STAGE_A_PROMPT"]
    assert sha8(p) == CALIB_SHA8, sha8(p)
    return p


def all_candidate_arrays():
    return sorted(d for d in os.listdir(STIM) if os.path.isdir(os.path.join(STIM, d)))


def perm_table(a):
    return {int(k): v for k, v in json.load(open(os.path.join(STIM, a, "manifest.json"))).items()}


def stim_hashes(a):
    return {"manifest_sha256": sha256f(os.path.join(STIM, a, "manifest.json")),
            "perm_png_sha8": {str(p): sha256f(os.path.join(STIM, a, f"perm{p:02d}.png"))[:8] for p in range(24)}}


def latin_squares(table, n, seed):
    """n (multiple of 4) perm ids: k Latin squares; each shape in each display slot n/4 times."""
    assert n % 4 == 0, n
    rng = random.Random(seed)
    inv = {tuple(v): pid for pid, v in table.items()}
    out = []
    for _ in range(n // 4):
        base = list(range(4)); rng.shuffle(base)
        sq = [tuple(base[(i + s) % 4] for i in range(4)) for s in range(4)]
        rng.shuffle(sq)
        out += [inv[p] for p in sq]
    c = [[0] * 4 for _ in range(4)]
    for p in out:
        for slot, canon in enumerate(table[p]):
            c[canon][slot] += 1
    flat = [x for r in c for x in r]
    assert max(flat) == min(flat) == n // 4, c
    return out


# ------------------------------------------------------------------ calling ------
def ask_gpt(client, model, prompt, img):
    r = client.responses.create(model=model, reasoning={"effort": "low", "summary": "auto"},
                                input=[{"role": "user", "content": [
                                    {"type": "input_text", "text": prompt},
                                    {"type": "input_image", "image_url": f"data:image/png;base64,{img}"}]}])
    summ = [getattr(s, "text", "") for it in (r.output or []) if getattr(it, "type", "") == "reasoning"
            for s in (getattr(it, "summary", None) or [])]
    u = r.usage; det = getattr(u, "output_tokens_details", None)
    return dict(text=r.output_text or "", returned=r.model, response_id=r.id, stop_reason=getattr(r, "status", ""),
                surface="reasoning.effort=low", settings=MODELS["gpt"]["settings"],
                in_tok=u.input_tokens, out_tok=u.output_tokens,
                reasoning_tok=getattr(det, "reasoning_tokens", "") if det else "", summary=" ".join(summ))


def ask_claude(client, model, prompt, img):
    kw = dict(model=model, max_tokens=1024, thinking={"type": "disabled"},
              messages=[{"role": "user", "content": [
                  {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": img}},
                  {"type": "text", "text": prompt}]}])
    P.assert_thinking_off(kw)
    r = client.messages.create(**kw)
    P.check_no_thinking_block(r.content)
    txt = "".join(b.text for b in r.content if getattr(b, "type", "") == "text")
    return dict(text=txt, returned=r.model, response_id=r.id, stop_reason=r.stop_reason,
                surface="thinking=disabled", settings=MODELS["claude"]["settings"],
                in_tok=r.usage.input_tokens, out_tok=r.usage.output_tokens, reasoning_tok="", summary="")


ASK = {"gpt": ask_gpt, "claude": ask_claude}

# ------------------------------------------------------------------ parsing ------
_PROB = re.compile(r"^[\s*_`>-]*([A-D])\s*[:=)\]]\s*[\s*_`]*(\d{1,3}(?:\.\d+)?)\s*%?", re.I | re.M)


def parse_ref(txt, order):
    s = P.parse_slot(txt)
    return {} if s is None else {"slot_returned": s, "canonical_choice": order[s]}


def parse_pred(txt, order):
    """Four probabilities A-D = display positions 1-4 in the PREDICTOR's image. Last value per
    letter wins. Requires all four, sum in [95, 105]; then renormalised and mapped to canonical
    shape ids via the perm's display order. Never defaults."""
    found = {}
    for letter, v in _PROB.findall(txt or ""):
        found[letter.upper()] = float(v)
    if set(found) != set("ABCD"):
        return {}
    vals = [found[k] for k in "ABCD"]
    tot = sum(vals)
    if not 95 <= tot <= 105 or any(v < 0 or v > 100 for v in vals):
        return {}
    canon = [0.0] * 4
    for slot, v in enumerate(vals):
        canon[order[slot]] = v / tot
    return {"p_slots_raw": json.dumps(vals), "p_sum_raw": tot, "p_canonical": json.dumps([round(x, 6) for x in canon])}
