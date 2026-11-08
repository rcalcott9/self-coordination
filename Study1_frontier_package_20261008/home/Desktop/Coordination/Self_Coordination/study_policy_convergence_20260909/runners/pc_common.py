"""
Stage 1 collection primitives. Lead-owned. Frozen 2026-09-09.

Every design constraint that a runner could get silently wrong is enforced here as an
assertion rather than a convention:

  * Claude is ALWAYS called with thinking={"type":"disabled"}, passed explicitly. D-017.
    Omission is not equivalent: it means OFF on Opus 4.6/4.7/4.8 and adaptive-ON on Opus 5,
    which would split the panel along the very axis being measured. assert_thinking_off()
    checks the kwargs before dispatch and check_response() checks the reply for a thinking
    block afterwards. A reply carrying one is a collection FAILURE, not a datum.
  * Token usage is captured for BOTH providers. s4_common.ask_gpt discards r.usage, which
    is why GPT spend has never been measurable in this tree (D-016).
  * checkpoint_returned is recorded on every row and compared to checkpoint_requested.
  * The parser never defaults. On failure it returns None and the row carries parse_ok=0.
"""
import base64, json, os, random, re, sys, threading, time

from dotenv import load_dotenv
# Same credential source every runner in this tree uses (s4_common.py:35).
load_dotenv(os.path.expanduser("~/Desktop/Coordination/LLM_Coordination/.env"))

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
TREE = os.path.abspath(os.path.join(ROOT, ".."))

# D-016: pessimistic rate, BOTH providers, single primary number. Not a claim about price.
PRICE_IN, PRICE_OUT = 5.00, 30.00

CLAUDE_THINKING = {"type": "disabled"}          # D-017. Never change without a decision entry.
GPT_REASONING = {"effort": "low", "summary": "auto"}
GPT_NO_REASONING_TEMP = 1.0

# Panel approved at Gate 1 (GATE1_REPORT.md S6).
PANEL = [
    ("gpt",    "gpt-4-turbo-2024-04-09",     "2024-04", "G-SAMPLE"),
    ("gpt",    "gpt-4.1-2025-04-14",         "2025-04", "G-SAMPLE"),
    ("gpt",    "gpt-5-2025-08-07",           "2025-08", "G-REASON"),
    ("gpt",    "gpt-5.5-2026-04-23",         "2026-04", "G-REASON"),
    ("claude", "claude-opus-4-5-20251101",   "2025-11", "C-OFF"),
    ("claude", "claude-opus-4-6",            "2026-02", "C-OFF"),
    ("claude", "claude-opus-4-7",            "2026-04", "C-OFF"),
    ("claude", "claude-opus-4-8",            "2026-05", "C-OFF"),
    ("claude", "claude-opus-5",              "2026-07", "C-OFF"),
]
GPT_REASONING_PREFIX = ("gpt-5",)

N_FLOOR = 48            # MASTER_DESIGN S5. Never lowered.
N_PERMS = 24
PARSE_RATE_FLOOR = 0.95


# ------------------------------------------------------------------ clients ----
def make_clients():
    miss = [k for k in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY") if not os.environ.get(k)]
    if miss:
        sys.exit(f"missing environment variable(s): {', '.join(miss)}")
    from openai import OpenAI
    import anthropic
    return {"gpt": OpenAI(max_retries=0, timeout=180.0),
            "claude": anthropic.Anthropic(max_retries=0, timeout=180.0)}


# ------------------------------------------------------------- assertions -----
def assert_thinking_off(kwargs):
    """D-017. Called immediately before every Anthropic dispatch."""
    t = kwargs.get("thinking")
    if t != {"type": "disabled"}:
        raise AssertionError(
            f"D-017 violation: Claude call dispatched with thinking={t!r}. "
            "thinking={'type':'disabled'} must be passed explicitly on every call.")
    for bad in ("output_config", "budget_tokens", "temperature", "top_p", "top_k"):
        if bad in kwargs:
            raise AssertionError(f"D-017 violation: unexpected sampling parameter {bad!r}")


def check_no_thinking_block(content):
    for b in content:
        if getattr(b, "type", "") in ("thinking", "redacted_thinking"):
            raise AssertionError(
                "D-017 violation: response carried a thinking block although OFF was "
                "requested. This row is a collection failure, not a datum.")


# ----------------------------------------------------------------- calling ----
def ask_gpt(client, model, prompt, image_b64=None):
    content = [{"type": "input_text", "text": prompt}]
    if image_b64:
        content.append({"type": "input_image",
                        "image_url": f"data:image/png;base64,{image_b64}"})
    kw = dict(model=model, input=[{"role": "user", "content": content}])
    if model.startswith(GPT_REASONING_PREFIX):
        kw["reasoning"] = dict(GPT_REASONING)
        surface = "reasoning.effort=low"
    else:
        kw["temperature"] = GPT_NO_REASONING_TEMP
        surface = "temperature=1.0"
    r = client.responses.create(**kw)
    u = getattr(r, "usage", None)
    return dict(text=r.output_text or "", returned=getattr(r, "model", ""),
                surface=surface,
                in_tok=getattr(u, "input_tokens", None) if u else None,
                out_tok=getattr(u, "output_tokens", None) if u else None,
                thinking_blocks=False)


def ask_claude(client, model, prompt, image_b64=None, max_tokens=1024):
    content = []
    if image_b64:
        content.append({"type": "image", "source": {"type": "base64",
                                                    "media_type": "image/png",
                                                    "data": image_b64}})
    content.append({"type": "text", "text": prompt})
    kw = dict(model=model, max_tokens=max_tokens,
              thinking=dict(CLAUDE_THINKING),
              messages=[{"role": "user", "content": content}])
    assert_thinking_off(kw)
    r = client.messages.create(**kw)
    check_no_thinking_block(r.content)
    txt = "".join(b.text for b in r.content if getattr(b, "type", "") == "text")
    u = getattr(r, "usage", None)
    return dict(text=txt, returned=getattr(r, "model", ""),
                surface="thinking=disabled",
                in_tok=getattr(u, "input_tokens", None) if u else None,
                out_tok=getattr(u, "output_tokens", None) if u else None,
                thinking_blocks=False)


ASK = {"gpt": ask_gpt, "claude": ask_claude}


def call_with_backoff(fn, *a, tries=5, base=2.0, **kw):
    """Retry transport/rate errors only. A D-017 AssertionError is never retried."""
    last = None
    for i in range(tries):
        try:
            return fn(*a, **kw), None
        except AssertionError:
            raise
        except Exception as e:
            last = e
            msg = f"{type(e).__name__}: {e}"
            low = msg.lower()
            fatal = any(s in low for s in
                        ("does not support image", "not support image",
                         "model_not_found", "does not exist", "invalid_api_key"))
            if fatal or i == tries - 1:
                return None, msg[:400]
            time.sleep(base * (2 ** i) * (0.6 + 0.8 * random.random()))
    return None, f"{type(last).__name__}: {last}"[:400]


# ------------------------------------------------------------------ parsing ----
_CODE_RE = re.compile(r'CHOICE\s*:\s*[\s*_`"\'\[\(]*([A-Da-d])(?![A-Za-z0-9_])', re.I)
_VIS_RE = re.compile(r'CHOICE\s*:\s*[\s*_`"\'\[\(]*([1-4])(?![0-9])', re.I)


def parse_label(txt):
    """Code domain. Last match, upper-cased. NEVER defaults."""
    if not txt:
        return None
    m = _CODE_RE.findall(txt)
    return m[-1].upper() if m else None


def parse_slot(txt):
    """Visual domain. Returns 0-based display position. NEVER defaults."""
    if not txt:
        return None
    m = _VIS_RE.findall(txt)
    return int(m[-1]) - 1 if m else None


# ------------------------------------------------------- presentation order ----
def trial_perms(n, seed):
    """n trials as complete cycles of all N_PERMS permutations, order shuffled within
    each cycle by a fixed seed. Guarantees every canonical option appears in every
    display slot exactly n/N_PERMS * (N_PERMS/4) times -- 12 times at n=48."""
    if n % N_PERMS:
        raise ValueError(f"n={n} is not a whole number of {N_PERMS}-permutation cycles")
    rng = random.Random(seed)
    out = []
    for _ in range(n // N_PERMS):
        c = list(range(N_PERMS))
        rng.shuffle(c)
        out.extend(c)
    return out


def verify_slot_balance(perm_table, perms, k=4):
    """Hard check, run before any call: every canonical option in every slot equally."""
    counts = [[0] * k for _ in range(k)]
    for pid in perms:
        for slot, canon in enumerate(perm_table[pid]):
            counts[canon][slot] += 1
    want = len(perms) // k
    for canon in range(k):
        for slot in range(k):
            if counts[canon][slot] != want:
                raise AssertionError(
                    f"slot balance broken: canonical {canon} in slot {slot} "
                    f"{counts[canon][slot]}x, expected {want}x")
    return want


# ------------------------------------------------------------------- money ----
def cost(in_tok, out_tok):
    return ((in_tok or 0) * PRICE_IN + (out_tok or 0) * PRICE_OUT) / 1e6


class Budget:
    """Hard stop. Refuses to hand out permission once the cap is reached."""
    def __init__(self, cap_usd):
        self.cap = cap_usd
        self.spent = 0.0
        self.lock = threading.Lock()
        self.stopped = False

    def add(self, usd):
        with self.lock:
            self.spent += usd
            if self.spent >= self.cap:
                self.stopped = True
            return self.spent

    def ok(self):
        with self.lock:
            return not self.stopped
