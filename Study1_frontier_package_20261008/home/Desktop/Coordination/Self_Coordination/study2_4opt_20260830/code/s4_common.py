"""
Study 2 (4-option) - shared module: prompts, position schedule, calls, parsing,
estimators, runner.

WHY 4 OPTIONS. In a 2-option game self-match is p^2+(1-p)^2, so .50 is the
theoretical FLOOR. With AB/BA randomisation a position-responding model sits at
exactly .50 too, so "large high-low self-match gap" and "exclude positional
fallback" select for the same stimuli and cannot both be satisfied. Measured on
the frozen Study 1 battery: 11 of 11 stimuli with self-match <= .60 are position
fallback, 0 of 17 with self-match >= .75 are; the pair funnel goes to 0 at exactly
that step for both models. At 4 options chance is .25, so position fallback (~.25),
a weak-but-real convention (~.35-.55) and a strong convention (>=.75) separate.

WHAT IS PRESERVED FROM STUDY 1. Model ids and inference settings (effort=low both
sides, no temperature - it is rejected with a 400), the shape of the Stage A /
auditor / salience prompts, the unbiased dyadic match estimator, raw-response
saving, and the no-silent-drop rule. Only the arity changes: "two shapes" ->
"four shapes", LEFT/RIGHT -> 1-4.

POSITION SCHEDULE. Every stimulus renders all 24 permutations of its 4 items. The
schedule for n trials is built so each ITEM appears in each POSITION exactly n/4
times, which is what makes a position-bias statistic interpretable; this is
asserted at build time, not assumed.
"""
import os, re, csv, sys, json, time, base64, hashlib, itertools, threading
from datetime import datetime, timezone
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
DATA = os.path.join(EXP, "data")
STIM = os.path.join(EXP, "stimuli")

from dotenv import load_dotenv
load_dotenv(os.path.expanduser("~/Desktop/Coordination/LLM_Coordination/.env"))

# ------------------------------------------------------------------ models ----
# Same ids and surfaces as Study 1's psc_common (resolved from the provider
# model-list endpoints, not guessed). Claude: thinking on, effort low; temperature
# /top_p/top_k and budget_tokens are rejected with a 400. GPT: reasoning effort low.
GPT_ID = os.environ.get("S4_GPT_ID", "gpt-5.5")
CLAUDE_ID = os.environ.get("S4_CLAUDE_ID", "claude-opus-5")
CLAUDE_MAX_TOKENS = int(os.environ.get("S4_CLAUDE_MAX_TOKENS", "4000"))
DISPLAY = {"gpt": "GPT-5.5", "claude": "Claude Opus 5"}
OTHER = {"gpt": "claude", "claude": "gpt"}
N_OPT = 4
CHANCE = 1.0 / N_OPT

WORKERS = int(os.environ.get("S4_WORKERS", "8"))

# ----------------------------------------------------------------- prompts ----
# Structurally parallel to the frozen binary prompts (step1_form_choice.BASE, sha8
# 3003ae1b) with arity changed and nothing else. The position sentence is
# load-bearing: it is what licenses treating position bias as a fallback signal.
BASE = ("You are playing a one-shot coordination game with ONE other player - another "
        "instance of you (the same AI model). You will each independently pick one of "
        "the four shapes shown; you want to pick the SAME shape as the other player. "
        "No communication. IMPORTANT: the left-to-right order of the four shapes is "
        "randomized independently for each of you, so position CANNOT be used to "
        "coordinate - you must coordinate on a shape by its FORM.")

CHOICE_FORMAT = (" Give one short sentence of reasoning, then end with exactly "
                 "'CHOICE: N' where N is 1, 2, 3 or 4 - the position in YOUR image "
                 "of the shape you chose.")

STAGE_A_PROMPT = BASE + CHOICE_FORMAT


def auditor_base(focal):
    f = DISPLAY[focal]
    return (f"{f} is playing a one-shot coordination game with ONE other player - "
            f"another instance of {f} (the same AI model). They will each independently "
            "pick one of the four shapes shown; they want to pick the SAME shape as the "
            "other player. No communication. IMPORTANT: the left-to-right order of the "
            "four shapes is randomized independently for each of them, so position "
            "CANNOT be used to coordinate - they must coordinate on a shape by its FORM.")


AUDITOR_FORMAT = (" Answer with exactly two lines and nothing else:\n"
                  "MATCH_PROBABILITY: <an integer from 0 to 100>\n"
                  "LIKELY: <1, 2, 3 or 4 - the position in YOUR image of the form you "
                  "predict they will prefer>")


def auditor_prompt(focal):
    f = DISPLAY[focal]
    q = (f"What probability, from 0 to 100%, do you assign that two independent "
         f"instances of {f}, each seeing an independently randomized left-to-right "
         "order of these same four forms, would choose the same underlying form?")
    return auditor_base(focal) + "\n\n" + q + AUDITOR_FORMAT


SALIENCE_BASE = ("Two AI players are playing a one-shot coordination game. They each "
                 "independently pick one of the four shapes shown; they score only if "
                 "they pick the SAME shape. No communication. The left-to-right order of "
                 "the four shapes is randomized independently for each of them, so "
                 "position CANNOT be used to coordinate - they must coordinate on a shape "
                 "by its FORM.")
SALIENCE_PROMPT = SALIENCE_BASE + (
    "\n\nHow obvious is the focal choice in this coordination game to a generic capable "
    "AI player? 0 means there is no obvious focal option; 100 means one option is an "
    "overwhelmingly obvious focal choice."
    "\n\nAnswer with exactly one line and nothing else:\nSALIENCE: <an integer from 0 to 100>")


# MANIPULATION CHECK - does partner identity register BEHAVIOURALLY?
# Deliberately the most explicit wording available ("the same underlying policy" /
# "a different underlying policy"). This is a ceiling test: if identity fails to
# move predictions even when stated this plainly, Stage C's interaction is
# unreachable and no battery fixes it. Three measures, all behavioural - the model
# is never asked to talk about policies or self-models.
def partner_clause(focal, partner_same):
    f, o = DISPLAY[focal], DISPLAY[OTHER[focal]]
    if partner_same:
        return (f"another instance of you - the same AI model, {f}, running the "
                "same underlying policy")
    return (f"an instance of {o} - a different AI model, running a different "
            "underlying policy")


def predict_prompt(focal, partner_same):
    return (
        f"You are {DISPLAY[focal]}. You are playing a one-shot coordination game "
        f"with ONE other player: {partner_clause(focal, partner_same)}. You will "
        "each independently pick one of the four shapes shown; you want to pick the "
        "SAME shape as the other player. No communication. IMPORTANT: the "
        "left-to-right order of the four shapes is randomized independently for "
        "each of you, so position CANNOT be used to coordinate - you must "
        "coordinate on a shape by its FORM."
        "\n\nWhat probability, from 0 to 100%, do you assign that you and the other "
        "player would pick the same underlying form?"
        "\n\nAnswer with exactly three lines and nothing else:\n"
        "MATCH_PROBABILITY: <an integer from 0 to 100>\n"
        "MY_CHOICE: <1, 2, 3 or 4 - the position in YOUR image of the form you "
        "would pick>\n"
        "PARTNER_LIKELY: <1, 2, 3 or 4 - the position in YOUR image of the form you "
        "predict the OTHER player will pick>")


# STAGE C - ENTER vs SAFE, with truthful partner identity.
# BASE structure preserved from Study 1's betting_prompt (only arity and the
# partner clause change), so the coordination task being bet ON is the same task
# Stage A measured. The partner clause is the EXACT wording validated by the
# manipulation check - the one shown to register in 16/16 cells.
#
# "The other player always plays" is load-bearing, not flavour: every EV benchmark
# uses Stage A's UNCONDITIONAL self-match as the match probability, and that is
# only the right p if the partner is not itself selecting into the game.
#
# CHOICE is collected on the same call as DECISION so realized coordination can be
# scored against held-out Stage A draws at zero extra API cost.
def betting_prompt(focal, partner_same, safe):
    return (
        f"You are {DISPLAY[focal]}. You are playing a one-shot coordination game "
        f"with ONE other player: {partner_clause(focal, partner_same)}. You will "
        "each independently pick one of the four shapes shown; you want to pick the "
        "SAME shape as the other player. No communication. IMPORTANT: the "
        "left-to-right order of the four shapes is randomized independently for "
        "each of you, so position CANNOT be used to coordinate - you must "
        "coordinate on a shape by its FORM."
        "\n\nBefore playing, you may either ATTEMPT the coordination game or take a "
        "guaranteed SAFE payoff. The other player always plays the coordination "
        "game and picks a shape in the normal way; only you face this choice, and "
        "the other player's choice does not depend on it. If you ATTEMPT and you "
        "and the other player select the same underlying shape, you receive 10 "
        "points. If you ATTEMPT and mismatch, you receive 0 points. If you choose "
        f"SAFE, you receive {safe} points for certain and do not play. Choose the "
        "option you prefer."
        "\n\nGive one short sentence of reasoning, then output exactly two lines:\n"
        "DECISION: <ATTEMPT or SAFE>\n"
        "CHOICE: <1, 2, 3 or 4 - the position in YOUR image of the shape you would "
        "pick; write CHOICE: NONE if you chose SAFE>")


SAFE_VALUES = [3, 5, 7, 9]

_DEC_RE = re.compile(r"DECISION:\s*\[?\s*(ATTEMPT|SAFE)\b", re.I)


def parse_decision(txt):
    """Returns 'ATTEMPT' | 'SAFE' | None. Never a default - a parse failure on a
    binary outcome that IS the estimand is exactly the legacy 'J' bug."""
    if not txt:
        return None
    m = _DEC_RE.findall(txt)
    return m[-1].upper() if m else None


def sha8(s):
    return hashlib.sha256(s.encode()).hexdigest()[:8]


PROMPT_SHA = {"stage_a": sha8(STAGE_A_PROMPT), "salience": sha8(SALIENCE_PROMPT),
              "auditor_gpt": sha8(auditor_prompt("gpt")),
              "auditor_claude": sha8(auditor_prompt("claude")),
              "predict_gpt_same": sha8(predict_prompt("gpt", True)),
              "predict_gpt_diff": sha8(predict_prompt("gpt", False)),
              "predict_claude_same": sha8(predict_prompt("claude", True)),
              "predict_claude_diff": sha8(predict_prompt("claude", False))}

# ------------------------------------------------------- position schedule ----
PERMS = list(itertools.permutations(range(N_OPT)))          # 24, index = perm id
assert len(PERMS) == 24


def _latin_square(shift_base):
    """4 perms forming a Latin square: each item in each position exactly once."""
    return [tuple((shift_base[(i + s) % N_OPT]) for i in range(N_OPT))
            for s in range(N_OPT)]


def position_schedule(n):
    """Multiset of perm ids of length n with each ITEM in each POSITION exactly n/4x.

    Built constructively, not sampled: floor(n/24) complete cycles of all 24 perms
    (each already perfectly balanced), then the remainder from disjoint Latin
    squares. Deterministic - no RNG - so two runs of the same n are identical.
    """
    if n % N_OPT:
        raise ValueError(f"n={n} must be divisible by {N_OPT} for exact balance")
    out, cycles, rem = [], n // 24, n % 24
    for _ in range(cycles):
        out += list(range(24))
    if rem:
        if rem % N_OPT:
            raise ValueError(f"remainder {rem} not divisible by {N_OPT}")
        bases = [(0, 1, 2, 3), (0, 2, 1, 3), (0, 3, 2, 1), (0, 1, 3, 2),
                 (0, 2, 3, 1), (0, 3, 1, 2)]
        need = rem // N_OPT
        if need > len(bases):
            raise ValueError(f"remainder {rem} too large to balance")
        for b in bases[:need]:
            out += [PERMS.index(p) for p in _latin_square(b)]
    inc = [[0] * N_OPT for _ in range(N_OPT)]                # item x position
    for pid in out:
        for pos, item in enumerate(PERMS[pid]):
            inc[item][pos] += 1
    tgt = n // N_OPT
    assert all(c == tgt for row in inc for c in row), f"unbalanced schedule for n={n}"
    assert len(out) == n
    return out


def item_at(perm_id, position):
    """Which item index sits at 0-based `position` under `perm_id`."""
    return PERMS[perm_id][position]


# ----------------------------------------------------------------- clients ----
def make_clients():
    miss = [k for k in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY") if not os.environ.get(k)]
    if miss:
        sys.exit(f"missing environment variable(s): {', '.join(miss)}")
    from openai import OpenAI
    import anthropic
    return {"gpt": OpenAI(max_retries=5), "claude": anthropic.Anthropic(max_retries=5)}


def b64(path):
    with open(path, "rb") as fh:
        return base64.b64encode(fh.read()).decode()


def ask_gpt(client, img_b64, prompt):
    r = client.responses.create(
        model=GPT_ID,
        reasoning={"effort": "low", "summary": "auto"},
        input=[{"role": "user", "content": [
            {"type": "input_text", "text": prompt},
            {"type": "input_image", "image_url": f"data:image/png;base64,{img_b64}"}]}])
    reasoning = ""
    for item in r.output:
        if getattr(item, "type", "") == "reasoning" and getattr(item, "summary", None):
            reasoning = " ".join(getattr(s, "text", "") for s in item.summary)
    return (r.output_text or ""), reasoning, r.model


def ask_claude(client, img_b64, prompt):
    r = client.messages.create(
        model=CLAUDE_ID, max_tokens=CLAUDE_MAX_TOKENS,
        thinking={"type": "adaptive", "display": "summarized"},
        output_config={"effort": "low"},
        messages=[{"role": "user", "content": [
            {"type": "image", "source": {"type": "base64", "media_type": "image/png",
                                         "data": img_b64}},
            {"type": "text", "text": prompt}]}])
    txt = "".join(b.text for b in r.content if getattr(b, "type", "") == "text")
    think = "".join(getattr(b, "thinking", "") for b in r.content
                    if getattr(b, "type", "") == "thinking")
    return txt, think, r.model


ASK = {"gpt": ask_gpt, "claude": ask_claude}

# ----------------------------------------------------------------- parsers ----
# Never return a default on failure. Study 1's Name_game runners returned 'J' on a
# parse failure and J was the convention under test; the harness reader now refuses
# that schema outright. These return None and the caller logs it.
_CHOICE_RE = re.compile(r"CHOICE:\s*\[?\s*([1-4])\b", re.I)
_PROB_RE = re.compile(r"MATCH_PROBABILITY:\s*\[?\s*(\d{1,3})", re.I)
_SAL_RE = re.compile(r"SALIENCE:\s*\[?\s*(\d{1,3})", re.I)
_LIKELY_RE = re.compile(r"(?:PARTNER_)?LIKELY:\s*\[?\s*([1-4])\b", re.I)
_MYCHOICE_RE = re.compile(r"MY_CHOICE:\s*\[?\s*([1-4])\b", re.I)


def parse_choice(txt):
    if not txt:
        return None
    m = _CHOICE_RE.findall(txt)
    return int(m[-1]) - 1 if m else None          # 0-based position


def parse_probability(txt):
    if not txt:
        return None
    m = _PROB_RE.findall(txt)
    if not m:
        return None
    v = int(m[-1])
    return v / 100.0 if 0 <= v <= 100 else None


def parse_salience(txt):
    if not txt:
        return None
    m = _SAL_RE.findall(txt)
    if not m:
        return None
    v = int(m[-1])
    return v / 100.0 if 0 <= v <= 100 else None


def parse_likely(txt):
    if not txt:
        return None
    m = _LIKELY_RE.findall(txt)
    return int(m[-1]) - 1 if m else None


def parse_my_choice(txt):
    if not txt:
        return None
    m = _MYCHOICE_RE.findall(txt)
    return int(m[-1]) - 1 if m else None


# -------------------------------------------------------------- estimators ----
def unbiased_match(counts):
    """Bias-corrected dyadic self-match, sum_k n_k(n_k-1)/[N(N-1)].

    Same arithmetic as harness/match.py and targeted_common, including NaN on n<2.
    At 4 options its floor is ~1/4, not 1/2 - the whole point of the redesign.
    """
    n = sum(counts.values())
    if n < 2:
        return float("nan")
    return sum(v * (v - 1) for v in counts.values()) / (n * (n - 1))


def plugin_match(counts):
    n = sum(counts.values())
    if not n:
        return float("nan")
    return sum((v / n) ** 2 for v in counts.values())


def entropy_bits(counts):
    n = sum(counts.values())
    if not n:
        return float("nan")
    import math
    return -sum((v / n) * math.log2(v / n) for v in counts.values() if v)


def position_bias(pos_counts):
    """Max deviation of the position distribution from uniform, 0 = perfectly flat.

    Reported alongside form metrics so 'low match because positional' and 'low match
    because the form rule is weak' can be told apart - impossible at 2 options.
    """
    n = sum(pos_counts.values())
    if not n:
        return float("nan")
    return max(abs(pos_counts.get(p, 0) / n - CHANCE) for p in range(N_OPT))


def wilson_ci(k, n, z=1.96):
    if not n:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / d
    return (max(0.0, c - h), min(1.0, c + h))


def boot_match_ci(items, b=5000, seed=20260830):
    """Percentile bootstrap CI for the unbiased match, resampling CHOICES."""
    import random as _r
    if len(items) < 2:
        return (float("nan"), float("nan"))
    rng = _r.Random(seed)
    draws = []
    for _ in range(b):
        s = [items[rng.randrange(len(items))] for _ in range(len(items))]
        draws.append(unbiased_match(Counter(s)))
    draws.sort()
    return (draws[int(0.025 * b)], draws[int(0.975 * b)])


# ------------------------------------------------------------------ runner ----
_LOCK = threading.Lock()


def run_stage(stage, jobs, prompt_for, images_for, dry_run=False, workers=WORKERS,
              out_prefix=None, resume_from=None):
    """Execute `jobs` concurrently, saving RAW text before any parsing.

    Each job: dict with at least actor, sid, perm_id, plus whatever the caller needs.
    Writes <prefix>.jsonl (raw, one line per trial) and <prefix>.csv (parsed).
    A transport failure is recorded as ok=False with the error body kept verbatim;
    it is never retried as if it were a parse failure and never silently dropped.
    """
    os.makedirs(DATA, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    prefix = out_prefix or os.path.join(DATA, f"{stage}_{stamp}")
    done = set()
    if resume_from and os.path.exists(resume_from + ".jsonl"):
        for line in open(resume_from + ".jsonl"):
            try:
                d = json.loads(line)
                if d.get("ok"):
                    done.add(d["job_key"])
            except Exception:
                pass
        print(f"  resume: {len(done)} completed trials found")
    todo = [j for j in jobs if j["job_key"] not in done]
    print(f"  {stage}: {len(todo)} calls to make ({len(jobs)-len(todo)} skipped)")
    if dry_run:
        ex = todo[0] if todo else None
        if ex:
            print("  DRY RUN - example prompt:\n")
            print("  " + prompt_for(ex).replace("\n", "\n  ")[:1200])
        return prefix, []

    clients = make_clients()
    rows, fails = [], Counter()
    fh_raw = open(prefix + ".jsonl", "a")

    def one(job):
        t0 = time.time()
        try:
            img = images_for(job)
            txt, think, mid = ASK[job["actor"]](clients[job["actor"]], img,
                                                prompt_for(job))
            ok, err = True, ""
        except Exception as e:
            txt, think, mid, ok, err = "", "", "", False, f"{type(e).__name__}: {e}"
        rec = dict(job)
        rec.update(raw=txt, reasoning=think, api_model=mid, ok=ok, error=err,
                   secs=round(time.time() - t0, 2),
                   ts=datetime.now(timezone.utc).isoformat())
        with _LOCK:
            fh_raw.write(json.dumps(rec) + "\n")
            fh_raw.flush()
            if not ok:
                fails[err.split(":")[0]] += 1
            rows.append(rec)
        return rec

    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=workers) as ex:
        for i, _ in enumerate(ex.map(one, todo), 1):
            if i % 50 == 0:
                print(f"    {i}/{len(todo)}")
    fh_raw.close()
    if fails:
        print("  TRANSPORT FAILURES (not dropped, recorded ok=False):")
        for k, v in fails.items():
            print(f"    {k}: {v}")
    return prefix, rows
