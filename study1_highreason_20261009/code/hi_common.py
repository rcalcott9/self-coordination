"""Study 1 high-reasoning replication (1a + 1b): shared primitives. No calls happen on import.

Reuses, unmodified and by import: the 1b common module (stimuli, Latin-square orderings, REF/PRED parsers,
calibration prompt d40ea45d), the 1a prompt builder, the 1a DECISION / MATCH_PROBABILITY regexes (copied
verbatim from study1_frontier_min_20261007/code/run.py), and pc_common (slot parser, backoff, cost).

Only two things differ from the low-reasoning runs:
  1. request settings: GPT-5.5 reasoning.effort=high; Opus 5 adaptive thinking, effort high, max_tokens 16000
  2. the configuration clause that names the target model's settings inside the AUDITOR (1a) and PRED (1b)
     prompts, which must describe the configuration actually run. Every other character is unchanged.
"""
import hashlib, importlib.util, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)
SC = os.path.dirname(STUDY)
S1A = os.path.join(SC, "study1_frontier_min_20261007")
S1B = os.path.join(SC, "study1b_crossed_object_20261007")


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod


sys.path.insert(0, os.path.join(S1B, "code"))                      # 1b common imports its own siblings
C = _load("s1b_common", os.path.join(S1B, "code", "common.py"))    # 1b primitives (+ C.P = pc_common)
P = C.P
PR1A = _load("s1a_prompts", os.path.join(S1A, "code", "prompts.py"))
PR1B = _load("s1b_prompts", os.path.join(S1B, "code", "prompts.py"))

CFG_LOW = {"gpt": "reasoning effort set to low", "claude": "extended thinking turned off"}
CFG_HIGH = {"gpt": "reasoning effort set to high", "claude": "extended thinking turned on, effort set to high"}
assert PR1A.FOCAL_CFG == CFG_LOW and PR1B.CFG == CFG_LOW, "source prompt modules changed"

MODELS = {
    "gpt": {"model_id": "gpt-5.5-2026-04-23", "provider": "openai.responses",
            "settings": {"reasoning": {"effort": "high", "summary": "auto"}}, "surface": "reasoning.effort=high"},
    "claude": {"model_id": "claude-opus-5", "provider": "anthropic.messages",
               "settings": {"thinking": {"type": "adaptive", "display": "summarized"},
                            "output_config": {"effort": "high"}, "max_tokens": 16000},
               "surface": "thinking=adaptive,effort=high",
               "alias_note": "no dated snapshot exists; identity certified to the alias on the run date only",
               "display_note": "display='summarized' only controls whether a thinking summary is returned"},
}
TIMEOUT_S = 900.0

DEC = re.compile(r"DECISION:\s*[\s*_`\"'\[\(]*(PLAY|PASS)\b", re.I)            # verbatim from 1a run.py
PROB = re.compile(r"MATCH_PROBABILITY:\s*[\s*_`\"'\[\(]*(\d{1,3})(?![0-9])", re.I)


def build_prompts():
    """All prompt texts. 1a: PR1A.build with the HIGH config clause; 1b: PR1B.build_predict likewise."""
    out = {"REF": C.calib_prompt()}
    PR1A.FOCAL_CFG = dict(CFG_HIGH); PR1B.CFG = dict(CFG_HIGH)
    try:
        for f in ("gpt", "claude"):
            for t in ("PLAYPASS", "SELFPRED", "AUDITOR"):
                out[f"{t}|{f}"] = PR1A.build(t, f)
        for p in ("gpt", "claude"):
            for t in ("gpt", "claude"):
                out[f"PRED|p={p}|t={t}"] = PR1B.build_predict(p, t)
    finally:
        PR1A.FOCAL_CFG = dict(CFG_LOW); PR1B.CFG = dict(CFG_LOW)
    # proof that only the configuration clause differs from the low-reasoning wording
    low = {}
    for f in ("gpt", "claude"):
        for t in ("PLAYPASS", "SELFPRED", "AUDITOR"):
            low[f"{t}|{f}"] = PR1A.build(t, f)
    for p in ("gpt", "claude"):
        for t in ("gpt", "claude"):
            low[f"PRED|p={p}|t={t}"] = PR1B.build_predict(p, t)
    diff = {}
    for k, v in low.items():
        hv = out[k]
        for m in ("gpt", "claude"):
            v = v.replace(CFG_LOW[m], CFG_HIGH[m])
        assert v == hv, k
        diff[k] = "identical" if low[k] == hv else "config clause only"
    return out, diff


def sha256f(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def sha8(s):
    return hashlib.sha256(s.encode()).hexdigest()[:8]


# ------------------------------------------------------------------ calling ------
def ask_gpt(client, model, prompt, img):
    s = MODELS["gpt"]["settings"]
    r = client.responses.create(model=model, reasoning=s["reasoning"],
                                input=[{"role": "user", "content": [
                                    {"type": "input_text", "text": prompt},
                                    {"type": "input_image", "image_url": f"data:image/png;base64,{img}"}]}])
    summ = [getattr(x, "text", "") for it in (r.output or []) if getattr(it, "type", "") == "reasoning"
            for x in (getattr(it, "summary", None) or [])]
    u = r.usage; det = getattr(u, "output_tokens_details", None)
    eff = getattr(getattr(r, "reasoning", None), "effort", None)
    return dict(text=r.output_text or "", returned=r.model, response_id=r.id, stop_reason=getattr(r, "status", ""),
                surface=MODELS["gpt"]["surface"], settings=s, echoed_effort=eff or "", thinking_blocks=0,
                in_tok=u.input_tokens, out_tok=u.output_tokens,
                reasoning_tok=getattr(det, "reasoning_tokens", "") if det else "", summary=" ".join(summ))


def ask_claude(client, model, prompt, img):
    s = MODELS["claude"]["settings"]
    r = client.messages.create(model=model, max_tokens=s["max_tokens"], thinking=s["thinking"],
                               output_config=s["output_config"],
                               messages=[{"role": "user", "content": [
                                   {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": img}},
                                   {"type": "text", "text": prompt}]}])
    th = [b for b in r.content if getattr(b, "type", "") in ("thinking", "redacted_thinking")]
    txt = "".join(b.text for b in r.content if getattr(b, "type", "") == "text")
    return dict(text=txt, returned=r.model, response_id=r.id, stop_reason=r.stop_reason,
                surface=MODELS["claude"]["surface"], settings=s, echoed_effort="", thinking_blocks=len(th),
                in_tok=r.usage.input_tokens, out_tok=r.usage.output_tokens, reasoning_tok="",
                summary=" ".join(getattr(b, "thinking", "") or "" for b in th))


ASK = {"gpt": ask_gpt, "claude": ask_claude}


def make_clients():
    from dotenv import load_dotenv
    load_dotenv(os.path.expanduser("~/Desktop/Coordination/LLM_Coordination/.env"), override=False)
    miss = [k for k in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY") if not os.environ.get(k)]
    if miss:
        sys.exit(f"missing environment variable(s): {', '.join(miss)}")
    from openai import OpenAI
    import anthropic
    return {"gpt": OpenAI(max_retries=0, timeout=TIMEOUT_S),
            "claude": anthropic.Anthropic(max_retries=0, timeout=TIMEOUT_S)}


# ------------------------------------------------------------------ parsing ------
def parse(task, txt, order):
    """REF: CHOICE slot -> canonical (pc_common). PLAYPASS / SELFPRED / AUDITOR: 1a rules, last match.
    PRED: 1b rule (all four A-D, sum 95-105, renormalised, mapped to canonical). Never defaults."""
    if task == "REF":
        return C.parse_ref(txt, order)
    if task == "PRED":
        return C.parse_pred(txt, order)
    if task == "PLAYPASS":
        m = DEC.findall(txt or "")
        return {"decision": m[-1].upper()} if m else {}
    m = PROB.findall(txt or "")
    if not m or not 0 <= int(m[-1]) <= 100:
        return {}
    return {"match_probability": int(m[-1])}


def family(array):
    return array.rsplit("_m", 1)[0]
