#!/usr/bin/env python3
"""Freeze CANDIDATE design -> design/FROZEN.json + design/jobs.jsonl (+ .sha256). Refuses to overwrite an existing freeze."""
import hashlib, json, shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
SC = Path.home() / "Desktop/Coordination/Self_Coordination"
assert not (HERE / "design/FROZEN.json").exists(), "already frozen"
C = json.loads((HERE / "design/CANDIDATE.json").read_text())
P5 = json.loads((SC / "study3a_pass5_PROPOSED_20261016/design/FROZEN.json").read_text())["models"]
models = {}
for mo, M in P5.items():
    M = {k: v for k, v in M.items() if k not in ("input_tokens_observed", "content_order", "note")}
    M["max_out"] = M.get("max_output_tokens", M.get("max_tokens"))
    M["content"] = "text only (single user message)"
    M["note"] = "settings identical to the PASS=5 pilot (study3a_pass5_PROPOSED_20261016 FROZEN.json); no image"
    models[mo] = M
F = dict(
    status="FROZEN 2026-10-17 before any PD call",
    message_id="pd-three-condition-pilot-20usd-01",
    user_authorisation_verbatim="okay run a small pilot based on that. budget = $20. im going to go away, so provide me with a plot of the three conditions by the time i get back",
    approved_spec="review_loop/pd_three_condition_pilot_APPROVED.json",
    seed=C["seed"], models=models, conditions=C["conditions"], n_per_cell=C["n_per_cell"], planned_calls=384,
    payoffs_canonical=C["payoffs_canonical"], label_to_canonical=C["label_to_canonical"], prompts=C["prompts"],
    schema='{"action": "A"|"B", "reason": str}; parser code/pd_parse.py; invalid recorded, never resampled',
    pairing=dict(
        same_model="derangement within model x mapping block (never own response); directed pairs",
        different_model="frozen one-to-one GPT<->Opus dyads within mapping",
        fixed_response="each same_model bank response assigned to exactly one fixed_response job of the same model and mapping; recorded in assignments.jsonl before the call; never disclosed",
        all="partners always share the label mapping, so 'the same payoff table' is literally true"),
    order="phase 1 = same_model + different_model (first 8 = format check, one per model x condition x mapping); phase 2 = fixed_response after the bank is sealed",
    budget=dict(pilot_cap_usd=20.0, cumulative_ceiling_usd=71.31619, prior_cumulative_usd_recomputed=51.31619,
                rule="dispatch only if pilot actual + outstanding reservations + next bound <= 20 AND prior + same <= 71.31619; bound = prompt characters x input price + max output tokens x output price; unknown usage keeps the full bound; API-error retries are new reservations",
                prices="GPT-5.5 $5/$30, Claude Opus 5 $5/$25 per MTok (re-verified 2026-10-17 ~20:30Z: platform.claude.com pricing page; developers.openai.com pricing page)"),
    stop_rules=["budget rule", "3 refusals", "5 consecutive API failures", "non-retryable 4xx"],
    primary_outcome="canonical cooperation rate of focal actions per model x condition, Wilson 95% CI over valid responses",
    frozen_utc="2026-10-17",
)
(HERE / "design/FROZEN.json").write_text(json.dumps(F, indent=1))
shutil.copy(HERE / "design/jobs_CANDIDATE.jsonl", HERE / "design/jobs.jsonl")
for f in ("FROZEN.json", "jobs.jsonl"):
    (HERE / "design" / (f + ".sha256")).write_text(hashlib.sha256((HERE / "design" / f).read_bytes()).hexdigest() + "  " + f + "\n")
print(open(HERE / "design/FROZEN.json.sha256").read(), open(HERE / "design/jobs.jsonl.sha256").read())
