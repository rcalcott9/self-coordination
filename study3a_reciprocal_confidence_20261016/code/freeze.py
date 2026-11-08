"""Freeze the Study 3A reciprocal-confidence pilot (2026-10-16) before any new outcome.
Authorisation (user, relayed by the ChatGPT manager, message study3a-reciprocal-confidence-pilot-20usd-01):
"yes and new cap for this experiment: $20". Approved spec: review_loop/reciprocal_confidence_pilot_APPROVED.json.

Every call (both roles, both partners) receives the same prompt for its condition: archived baseline game text +
the approved appendix (verbatim) + a response schema. 4 items x {GPT-5.5, Claude Opus 5} x {COPY, DIFFERENT} x
(24 policy + 12 eval) = 576 calls. Scoring: focal M in COPY uses q = M's COPY policy draws; in DIFFERENT, q = the OTHER
model's DIFFERENT policy draws (all under the appendix). Baseline data are exploratory comparison only."""
import hashlib, json, random
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
SC = Path.home() / "Desktop/Coordination/Self_Coordination"
RL = Path.home() / ".codex/.chatgpt-projects/g-p-6aa069d23ae08191a861f83470dbc913/review_loop"
STIM = SC / "study2_4opt_20260830/stimuli"
SEED = 20261017
sha = lambda b: hashlib.sha256(b).hexdigest(); fsha = lambda p: sha(Path(p).read_bytes())

SPEC = json.loads((RL / "reciprocal_confidence_pilot_APPROVED.json").read_text())
APPENDIX = SPEC["prompt_appendix"]
ITEMS = SPEC["recommended_pilot"]["items"]
assert ITEMS == ["F01_oddone_m0", "F27_linecount_m1", "F05_orient_m5", "F12_mirror_m3"]
BASE = json.loads((SC / "study3a_baseline_20261016/design/FROZEN.json").read_text())
CUT = "Answer with exactly one JSON object and nothing else"
GAME = {c: BASE["prompts"][c]["text"][: BASE["prompts"][c]["text"].index(CUT)] for c in ("COPY", "DIFFERENT")}
DIST = '{"PASS": <p>, "1": <p>, "2": <p>, "3": <p>, "4": <p>}'
SCHEMA = ("Response schema. Objects are identified by their position (1, 2, 3 or 4) in YOUR image. \"own_distribution\" is your "
          "estimate of how independent instances of your model, each given this complete prompt including these instructions, "
          "would act; it is a forecast, not a commitment. \"partner_distribution\" is your estimate of the other player's action. "
          "Each distribution's values are probabilities between 0 and 1 that sum to 1.\n\n"
          "Answer with exactly one JSON object and nothing else, in this form:\n"
          '{"own_distribution": ' + DIST + ', "partner_distribution": ' + DIST + ', '
          '"expected_points": {"PASS": 7, "1": <number>, "2": <number>, "3": <number>, "4": <number>}, '
          '"decision": "PASS" or "PLAY", "object": null or "<1, 2, 3 or 4 - the position in YOUR image of the object you choose>", '
          '"explanation": "<one or two sentences on the decisive uncertainty>"}')
PROMPTS = {c: GAME[c] + APPENDIX + "\n\n" + SCHEMA for c in ("COPY", "DIFFERENT")}

MODELS = {k: dict(v) for k, v in BASE["models"].items()}       # identical settings to the baseline
in_tok_est = {}
for m, v in MODELS.items():
    for c in ("COPY", "DIFFERENT"):
        extra_chars = len(PROMPTS[c]) - len(BASE["prompts"][c]["text"])
        in_tok_est[(m, c)] = int(v["input_tokens_observed"][c] + extra_chars / 3.5)    # conservative chars->tokens
def bound(m, c):
    v = MODELS[m]; cap = v.get("max_output_tokens") or v.get("max_tokens")
    return round((in_tok_est[(m, c)] * 1.15 * v["price_per_mtok"]["input"] + cap * v["price_per_mtok"]["output"]) / 1e6, 6)

rng = random.Random(SEED); cells = {}
for it in ITEMS:
    man = json.loads((STIM / it / "manifest.json").read_text())
    for m in MODELS:
        for c in ("COPY", "DIFFERENT"):
            roles = ["policy"] * 24 + ["eval"] * 12; rng.shuffle(roles)
            pol, ev = rng.sample(range(24), 24), rng.sample(range(24), 12); jl = []; pi = ei = 0
            for k, role in enumerate(roles):
                if role == "policy": p = pol[pi]; pi += 1
                else: p = ev[ei]; ei += 1
                img = STIM / it / f"perm{p:02d}.png"
                jl.append(dict(job_key=f"{it}|{m}|{c}|{role}|{k:02d}", array=it, model=m, condition=c, role=role, rep=k, perm=p,
                               slot_to_canonical=man[str(p)], image_path=str(img), image_sha256=fsha(img),
                               prompt_sha8=sha(PROMPTS[c].encode())[:8], bound_usd=bound(m, c)))
            cells[(it, m, c)] = jl
order = []
for k in range(36):
    rnd = [cells[c][k] for c in cells]; rng.shuffle(rnd)
    if k == 0:
        head = []
        for _ in range(2):
            for t in (("GPT-5.5", "COPY"), ("GPT-5.5", "DIFFERENT"), ("Claude Opus 5", "COPY"), ("Claude Opus 5", "DIFFERENT")):
                head.append(next(x for x in rnd if (x["model"], x["condition"]) == t and x not in head))
        rnd = head + [x for x in rnd if x not in head]
    order += rnd
for i, j in enumerate(order): j["order"] = i
assert len(order) == 576
frozen = dict(
    study="Study 3A reciprocal-confidence pilot (symmetric two-step appendix to both players)", frozen_utc="2026-10-16",
    message_id="study3a-reciprocal-confidence-pilot-20usd-01", authorisation_verbatim="yes and new cap for this experiment: $20",
    approved_spec=str(RL / "reciprocal_confidence_pilot_APPROVED.json"), approved_spec_sha256=fsha(RL / "reciprocal_confidence_pilot_APPROVED.json"),
    budget=dict(pilot_cap_usd=20.0, cumulative_ceiling_usd=50.0, prior_cumulative_usd_recomputed=29.76738,
                rule="dispatch only if pilot actual + outstanding reservations (token-limit bound each) + next bound <= 20 AND prior + pilot actual + outstanding + next <= 50; missing usage keeps the full bound charged; retries are new reservations",
                prices="GPT-5.5 $5/$30, Claude Opus 5 $5/$25 per MTok (verified 2026-10-16)"),
    items=ITEMS, prompts={c: dict(text=t, sha8=sha(t.encode())[:8]) for c, t in PROMPTS.items()},
    appendix_sha256=sha(APPENDIX.encode()), schema=SCHEMA, models=MODELS,
    input_tokens_estimate={f"{m}|{c}": v for (m, c), v in in_tok_est.items()},
    design=dict(per_cell=dict(policy=24, eval=12), seed=SEED,
                scoring={"focal M COPY": "p = M COPY eval decisions; q = M COPY policy decisions",
                         "focal M DIFFERENT": "p = M DIFFERENT eval decisions; q = OTHER model DIFFERENT policy decisions"},
                forecasts="eval draws' own_distribution scored against the same cell's policy decisions; eval draws' partner_distribution scored against the actual partner's policy decisions (independent samples)",
                ev_consistency="decision is a best response (ties kept) to the call's own partner_distribution; stated expected_points vs 10 x partner probability",
                baseline_comparison="study3a_baseline_20261016 per-item regret on the same 4 items (exploratory; never a partner benchmark)"),
    parsing="strict JSON with exactly the schema keys; distributions accepted if the sum is within 0.97-1.03 (renormalised); a reply whose sum is 97-103 is read as percent and rescaled (documented routine repair); decision/object as in the baseline parser; otherwise invalid (recorded, never resampled)",
    stop_rules=["budget rule above", "3 refusals", "5 consecutive API failures", "any non-retryable 4xx"],
    format_check="first 8 frozen jobs (2 per model x condition) run first and count toward the sample",
    no_other_arms=True)
(HERE / "design").mkdir(parents=True, exist_ok=True)
(HERE / "design/FROZEN.json").write_text(json.dumps(frozen, indent=1))
(HERE / "design/jobs.jsonl").write_text("".join(json.dumps(j) + "\n" for j in order))
for c, t in PROMPTS.items(): (HERE / "design" / f"prompt_{c}_{sha(t.encode())[:8]}.txt").write_text(t)
for f in ("FROZEN.json", "jobs.jsonl"):
    (HERE / "design" / (f + ".sha256")).write_text(fsha(HERE / "design" / f) + "  " + f + "\n")
print({k: v["sha8"] for k, v in frozen["prompts"].items()}, "bounds:", {f"{j['model']}|{j['condition']}": j["bound_usd"] for j in order[:4]})
print("in-token estimates:", frozen["input_tokens_estimate"], "hard bound all:", round(sum(j["bound_usd"] for j in order), 2))
