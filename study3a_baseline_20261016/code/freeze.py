"""Freeze the Study 3A BASELINE (2026-10-16) before any new outcome. Authorisation (user, relayed by the ChatGPT manager,
message study3a-baseline-execution-30usd-01): "no we first want to test baseline performance on the stag hunt with the relevant
stimuli ..." / "yes. this is good. run exactly this experiment. i want a resulting plot that shows regret for each model, relative to
an optimal (low regret) benchmark" / "your budget is $30".

Design: 19 retained items x model {GPT-5.5, Claude Opus 5} x archived game prompt {COPY 49e35910, DIFFERENT 8222a371}.
Each (item, model, prompt) cell gets 36 independent action draws: 24 'policy' (each of the 24 permutations once) and
12 'eval' (12 distinct seeded permutations). Roles are disjoint. Scoring (not here): focal M in COPY uses q = M's COPY policy
draws; focal M in DIFFERENT uses q = the OTHER model's DIFFERENT policy draws. No intervention."""
import csv, hashlib, json, random
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
SC = Path.home() / "Desktop/Coordination/Self_Coordination"
STIM = SC / "study2_4opt_20260830/stimuli"
SEED = 20261016
sha = lambda b: hashlib.sha256(b).hexdigest()
fsha = lambda p: sha(Path(p).read_bytes())

items = [r["array"] for r in csv.DictReader(open(SC / "study3a_feasibility_20261015/inventory/diagnostic_20261016/diagnostic_items.csv"))]
assert len(items) == 19
hist = {r["array"]: r["historical_label_provenance"] for r in csv.DictReader(open(SC / "study3a_feasibility_20261015/inventory/diagnostic_20261016/diagnostic_items.csv"))}

FP = json.loads((SC / "study3a_feasibility_20261015/design/FROZEN.json").read_text())
PROMPTS = {c: dict(text=FP["prompts"][c]["text"], sha8=FP["prompts"][c]["sha8"]) for c in ("COPY", "DIFFERENT")}
for c, v in PROMPTS.items(): assert sha(v["text"].encode())[:8] == v["sha8"]

MODELS = {
 "GPT-5.5": dict(api="openai.responses", model="gpt-5.5-2026-04-23", reasoning={"effort": "low", "summary": "auto"}, max_output_tokens=4000,
                 temperature=None, content_order="text,image", price_per_mtok={"input": 5.0, "output": 30.0},
                 input_tokens_observed={"COPY": 818, "DIFFERENT": 813},
                 note="archived settings plus max_output_tokens=4000 (required for a finite reservation bound; archived GPT runs had no cap, so no GPT draw is reused)"),
 "Claude Opus 5": dict(api="anthropic.messages", model="claude-opus-5", thinking={"type": "adaptive", "display": "summarized"},
                       output_config={"effort": "low"}, max_tokens=4000, temperature=None, content_order="text,image",
                       price_per_mtok={"input": 5.0, "output": 25.0}, input_tokens_observed={"COPY": 1022, "DIFFERENT": 1015},
                       note="identical to the archived and 2026-10-15 settings"),
}
def bound(model, cond):
    m = MODELS[model]; cap = m.get("max_output_tokens") or m.get("max_tokens")
    return round((m["input_tokens_observed"][cond] * 1.10 * m["price_per_mtok"]["input"] + cap * m["price_per_mtok"]["output"]) / 1e6, 6)

# reuse: only exact matches (model id + settings + prompt + stimuli), roles kept disjoint and unchanged
pilot_jobs = {json.loads(l)["job_key"]: json.loads(l) for l in open(SC / "study3a_feasibility_20261015/design/jobs.jsonl")}
pilot_rows = [json.loads(l) for l in open(SC / "study3a_feasibility_20261015/results/pilot/responses.jsonl")]
reuse = []
for r in pilot_rows:
    if r["model"] == "Claude Opus 5" and r["condition"] == "DIFFERENT" and r["role"] in ("policy", "fresh"):
        j = pilot_jobs[r["job_key"]]
        reuse.append(dict(job_key=f"{r['array']}|Claude Opus 5|DIFFERENT|{'policy' if r['role']=='policy' else 'eval'}|R{r['rep']:02d}", array=r["array"],
                          model="Claude Opus 5", condition="DIFFERENT", role="policy" if r["role"] == "policy" else "eval", perm=r["perm"],
                          source="historical: study3a_feasibility_20261015 pilot (2026-10-15), exact model id/settings/prompt/stimuli; role " + r["role"] + " -> " + ("policy" if r["role"] == "policy" else "eval"),
                          source_job_key=r["job_key"], image_sha256=j["image_sha256"], prompt_sha8=j["prompt_sha8"], status=r["status"]))
reused_cells = {(x["array"], x["model"], x["condition"]) for x in reuse}
assert len(reuse) == 144 and len(reused_cells) == 4

rng = random.Random(SEED); cells = {}
for it in items:
    man = json.loads((STIM / it / "manifest.json").read_text())
    for model in MODELS:
        for cond in ("COPY", "DIFFERENT"):
            if (it, model, cond) in reused_cells: continue
            roles = ["policy"] * 24 + ["eval"] * 12; rng.shuffle(roles)               # roles interleaved within the cell
            pol_perms = rng.sample(range(24), 24); ev_perms = rng.sample(range(24), 12)
            jl, pi, ei = [], 0, 0
            for k, role in enumerate(roles):
                if role == "policy": p = pol_perms[pi]; pi += 1
                else: p = ev_perms[ei]; ei += 1
                img = STIM / it / f"perm{p:02d}.png"
                jl.append(dict(job_key=f"{it}|{model}|{cond}|{role}|{k:02d}", array=it, model=model, condition=cond, role=role, rep=k, perm=p,
                               slot_to_canonical=man[str(p)], image_path=str(img), image_sha256=fsha(img), prompt_sha8=PROMPTS[cond]["sha8"],
                               bound_usd=bound(model, cond)))
            cells[(it, model, cond)] = jl
# balanced order: round k takes the k-th job of every cell, cells shuffled within the round; the first 8 jobs cover
# all four model x prompt types twice (format check inside the frozen sample)
order = []
for k in range(36):
    rnd = [cells[c][k] for c in cells]; rng.shuffle(rnd)
    if k == 0:
        types = [("GPT-5.5", "COPY"), ("GPT-5.5", "DIFFERENT"), ("Claude Opus 5", "COPY"), ("Claude Opus 5", "DIFFERENT")]
        head = []
        for _ in range(2):
            for t in types:
                j = next(x for x in rnd if (x["model"], x["condition"]) == t and x not in head); head.append(j)
        rnd = head + [x for x in rnd if x not in head]
    order += rnd
for i, j in enumerate(order): j["order"] = i
n_new = len(order); assert n_new == 2736 - 144
prior = 4.75248
exp_cost = {("GPT-5.5", "COPY"): 0.010305, ("GPT-5.5", "DIFFERENT"): 0.010305, ("Claude Opus 5", "COPY"): 0.006593, ("Claude Opus 5", "DIFFERENT"): 0.006593}
expected = sum(exp_cost[(j["model"], j["condition"])] for j in order)
frozen = dict(
  study="Study 3A BASELINE (no intervention): normalized full-action best-response regret, focal GPT-5.5 and Claude Opus 5, COPY vs DIFFERENT",
  frozen_utc="2026-10-16", message_id="study3a-baseline-execution-30usd-01",
  authorisation_verbatim=["no we first want to test baseline performance on the stag hunt with the relevant stimuli (test in stag hunt to avoid the thing we found previously that weak policies in study 1 are strong here)",
                          "yes. this is good. run exactly this experiment. i want a resulting plot that shows regret for each model, relative to an optimal (low regret) benchmark",
                          "your budget is $30"],
  budget=dict(cumulative_cap_usd=30.0, prior_cumulative_usd_recomputed=prior, remaining_usd=round(30 - prior, 5),
              rule="dispatch only if prior + run actual + outstanding reservations (each at its token-limit bound) + next bound <= 30; a call with missing usage keeps its full bound charged; each retry is a new reservation",
              expected_new_usd_at_pilot_means=round(expected, 2), hard_bound_all_new_usd=round(sum(j["bound_usd"] for j in order), 2),
              prices_verified="2026-10-16: GPT-5.5 $5/$30, Claude Opus 5 $5/$25 per MTok (developers.openai.com model page; platform.claude.com pricing)"),
  items=[dict(array=i, historical_label_provenance=hist[i]) for i in items],
  prompts=PROMPTS, models=MODELS,
  design=dict(cell="(item, model, prompt)", per_cell=dict(policy=24, eval=12), seed=SEED,
              scoring={"focal M, COPY": "p = M COPY eval; q = M COPY policy", "focal M, DIFFERENT": "p = M DIFFERENT eval; q = OTHER model DIFFERENT policy"},
              realized={"COPY": "all distinct ordered pairs within M's COPY eval draws (never self-paired)", "DIFFERENT": "all GPT x Opus DIFFERENT eval cross pairs, each model scored with its own payoff"},
              regret="[max(7, 10*max_j q(PLAY j)) - (7 p(PASS) + 10 sum_j p(PLAY j) q(PLAY j))]/10 (same-q plug-in; >= 0)",
              reuse=f"{len(reuse)} historical Opus DIFFERENT draws on 4 items (exact match); no GPT or September Opus reuse"),
  stop_rules=["budget rule above", "3 refusals in total", "5 consecutive API failures", "any non-retryable 4xx"],
  retries="API exceptions only (429/5xx/timeout/connection), up to 3 attempts per job, each a new reservation; invalid replies are recorded, never resampled",
  parsing="historical parse_game (two_model_staghunt_20260916/src/analyze.py), unchanged",
  format_check="the first 8 frozen jobs (2 per model x prompt) run first, are inspected, and count toward the sample",
  n_new_jobs=n_new, n_reused=len(reuse))
(HERE / "design").mkdir(parents=True, exist_ok=True)
for name, obj in (("FROZEN.json", frozen),):
    (HERE / "design" / name).write_text(json.dumps(obj, indent=1))
(HERE / "design/jobs.jsonl").write_text("".join(json.dumps(j) + "\n" for j in order))
(HERE / "design/reuse.jsonl").write_text("".join(json.dumps(j) + "\n" for j in reuse))
for f in ("FROZEN.json", "jobs.jsonl", "reuse.jsonl"):
    (HERE / "design" / (f + ".sha256")).write_text(fsha(HERE / "design" / f) + "  " + f + "\n")
print(f"new jobs {n_new}, reused {len(reuse)}; expected ${expected:.2f}; hard bound ${frozen['budget']['hard_bound_all_new_usd']}; remaining ${30-prior:.4f}")
print("first 8:", [(j["model"], j["condition"], j["array"]) for j in order[:8]])
