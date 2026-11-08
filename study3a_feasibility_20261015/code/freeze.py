"""Freeze the Study 3A feasibility pilot (2026-10-15) before any call: items (recorded labels only), prompts
(archived, sha8-verified), model settings, permutations, the 384-job list, caps and stop rules."""
import hashlib, json, random
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
STAG = Path.home() / "Desktop/Superrationality/Stag/two_model_staghunt_20260916"
STIM = Path.home() / "Desktop/Coordination/Self_Coordination/study2_4opt_20260830/stimuli"
sha = lambda b: hashlib.sha256(b).hexdigest()
SEED = 20261015

# ---- items: recorded GPT-5.5 Stage A labels in the approved selection (no in-game outcomes consulted)
src = json.loads((STAG / "design/FROZEN.json").read_text())
assert src["selection"]["sha256"] == "bdee575f76ad020f52989548788de1877dd4181f5952266803b0f80238ea26ad"
gpt = [a for a in src["selection"]["arrays"] if a["model"] == "GPT-5.5"]
strong = sorted([a for a in gpt if a["bin"] == "HIGH"], key=lambda a: (-a["c_hat_hist"], a["array"]))[:2]
weak = sorted([a for a in gpt if a["bin"] == "LOW"], key=lambda a: (a["c_hat_hist"], a["array"]))[:2]
items = [dict(array=a["array"], historical_label="strong" if a in strong else "weak", historical_bin=a["bin"],
              c_hat_hist=a["c_hat_hist"], counts_hist=a["counts"]) for a in strong + weak]

# ---- prompts: the exact archived text that was sent (data/jobs.jsonl); the design/*.txt copies differ only by a trailing newline
prompts = {}
sent = {}
for line in open(STAG / "data/jobs.jsonl"):
    j = json.loads(line)
    if j["phase"] == "game": sent.setdefault(j["condition"], set()).add(j["prompt"])
for cond, fn, s8 in (("COPY", "prompt_game_COPY_49e35910.txt", "49e35910"), ("DIFFERENT", "prompt_game_DIFFERENT_8222a371.txt", "8222a371")):
    assert len(sent[cond]) == 1, cond
    t = next(iter(sent[cond]))
    assert sha(t.encode())[:8] == s8 and t == (STAG / "design" / fn).read_text().rstrip("\n"), cond
    prompts[cond] = dict(text=t, sha8=s8, source=f"{STAG}/data/jobs.jsonl (== design/{fn} without trailing newline)")

GPT = dict(label="GPT-5.5", api="openai.responses", model="gpt-5.5-2026-04-23", reasoning={"effort": "low", "summary": "auto"},
           max_output_tokens=None, temperature=None, content_order="text,image", price_per_mtok={"input": 5.0, "output": 30.0},
           note="recorded settings of two_model_staghunt_20260916 (requested alias gpt-5.5, returned gpt-5.5-2026-04-23); pinned to the returned snapshot")
OPUS = dict(label="Claude Opus 5", api="anthropic.messages", model="claude-opus-5", thinking={"type": "adaptive", "display": "summarized"},
            output_config={"effort": "low"}, max_tokens=4000, temperature=None, content_order="text,image",
            price_per_mtok={"input": 5.0, "output": 25.0}, note="recorded settings of two_model_staghunt_20260916; claude-opus-5 has no dated id")
PARTNER = {"COPY": GPT, "DIFFERENT": OPUS}

rng = random.Random(SEED)
jobs = []
for it in items:
    man = json.loads((STIM / it["array"] / "manifest.json").read_text())
    it["images_sha256"] = {p: sha((STIM / it["array"] / f"perm{p:02d}.png").read_bytes()) for p in range(24)}
    for cond in ("COPY", "DIFFERENT"):
        roles = [("policy", PARTNER[cond], rng.sample(range(24), 24)),   # each permutation exactly once
                 ("focal", GPT, rng.sample(range(24), 12)),
                 ("fresh", PARTNER[cond], rng.sample(range(24), 12))]
        for role, M, perms in roles:
            for k, p in enumerate(perms):
                jobs.append(dict(job_key=f"{it['array']}|{cond}|{role}|{k:02d}", array=it["array"], label=it["historical_label"],
                                 condition=cond, role=role, rep=k, model=M["label"], perm=p,
                                 slot_to_canonical=man[str(p)], image_path=str(STIM / it["array"] / f"perm{p:02d}.png"),
                                 image_sha256=it["images_sha256"][p], prompt_sha8=prompts[cond]["sha8"]))
rng.shuffle(jobs)                                                           # interleave cells in dispatch order
for i, j in enumerate(jobs): j["order"] = i
assert len(jobs) == 384 and len({j["job_key"] for j in jobs}) == 384

frozen = dict(
    study="Study 3A feasibility pilot (pipeline and measurement pilot, not a hypothesis test)", frozen_utc="2026-10-15",
    authorization=["This prompt authorizes at most $3 of new spend, including retries, and never overrides the recorded $20 cumulative cap. (user, 2026-10-15)",
                   "we can go up to $50 if needed (user, 2026-10-15, mid-run)"],
    caps=dict(run_hard_cap_usd=10.0, cumulative_cap_usd=20.0, cumulative_prior_usd=1.32999,
              note="scope unchanged (<= 384 calls); $10 run cap covers the max-cost estimate $7.17 plus retries"),
    focal_model="GPT-5.5", partner_models={"COPY": "GPT-5.5", "DIFFERENT": "Claude Opus 5"},
    item_rule="strong = recorded bin HIGH, highest c_hat_hist then array id, first 2; weak = recorded bin LOW, lowest c_hat_hist then array id, first 2. "
              "Labels from historical Stage A (prompt d40ea45d, 24 draws) via selection_proposal.csv sha256 bdee575f. Items are never replaced or relabelled.",
    items=items, prompts=prompts, models={"GPT-5.5": GPT, "Claude Opus 5": OPUS},
    design=dict(per_cell=dict(policy=24, focal=12, fresh=12), cells="4 items x {COPY, DIFFERENT}", seed=SEED,
                policy_perms="each of 24 once", focal_fresh_perms="12 distinct of 24, independent draws",
                no_prediction_calls=True),
    parsing="historical parse_game (two_model_staghunt_20260916/src/analyze.py), unchanged; invalid replies are recorded, never resampled",
    retries="API exceptions only, up to 3 attempts per job (SDK auto-retry off); every attempt logged",
    stop_rules=["projected spend (spent + reserved) would exceed the run hard cap or cumulative cap",
                "3 refusals in total", "5 consecutive API failures", "any non-retryable 4xx (model/settings unresolved)"],
    scoring="code/scoring.py: BR from policy sample; regret from focal vs policy; realized payoff + match from focal x fresh pairs",
)
(HERE / "design").mkdir(exist_ok=True)
(HERE / "design/FROZEN.json").write_text(json.dumps(frozen, indent=1))
(HERE / "design/jobs.jsonl").write_text("".join(json.dumps(j) + "\n" for j in jobs))
for f in ("FROZEN.json", "jobs.jsonl"):
    (HERE / "design" / (f + ".sha256")).write_text(sha((HERE / "design" / f).read_bytes()) + "  " + f + "\n")
print("items:", [(i["array"], i["historical_label"], round(i["c_hat_hist"], 3)) for i in items])
print("jobs:", len(jobs), {m: sum(j["model"] == m for j in jobs) for m in ("GPT-5.5", "Claude Opus 5")})
