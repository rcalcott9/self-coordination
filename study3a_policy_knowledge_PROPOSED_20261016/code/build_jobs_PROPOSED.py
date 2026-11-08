"""PROPOSED job list and cost model for the Study 3A policy-knowledge pilot (2026-10-16). Writes jobs_PROPOSED.jsonl and
COST_PROPOSED.json. Not frozen; there is no dispatch code here. Items are a candidate set for user review, picked from
archived/descriptive in-game data (not from any evaluation outcome); historical labels are kept as provenance."""
import hashlib, json, random
from pathlib import Path
from prompts_PROPOSED import PROMPTS, sha8

HERE = Path(__file__).resolve().parent.parent
STIM = Path.home() / "Desktop/Coordination/Self_Coordination/study2_4opt_20260830/stimuli"
SEED = 20261016
ITEMS = [  # candidate (in-game, descriptive): archived/independent COPY counts PASS/P0/P1/P2/P3 from diagnostic_20261016
    dict(array="F27_linecount_m1", candidate="strong-PLAY", evidence="independent pilot policy 0/0/0/0/24 (also archived 54/54); historical LOW (Stage A) - preserved", reuse_opus_policy=True),
    dict(array="F14_bars_m1", candidate="strong-PLAY", evidence="archived 1/0/0/29/0 (n=30); historical NEAR_ABOVE", reuse_opus_policy=False),
    dict(array="F05_orient_m5", candidate="diffuse", evidence="archived 9/2/3/3/2 (n=19), P(h<.6)=.93; historical WEAK", reuse_opus_policy=False),
    dict(array="F12_mirror_m3", candidate="diffuse", evidence="archived 9/5/1/1/3 (n=19), P(h<.6)=.93; historical WEAK", reuse_opus_policy=False),
]
# arm: (prompt key, model, n per item, role)
ARMS = [("P_GPT_COPY", "ACT_COPY", "GPT-5.5", 24, "own policy = COPY partner policy (independent)"),
        ("P_OPUS_DIFF", "ACT_DIFFERENT", "Claude Opus 5", 24, "DIFFERENT partner policy (independent)"),
        ("F_COPY", "F_COPY", "GPT-5.5", 12, "spontaneous forecast of copy (= own policy)"),
        ("F_DIFF", "F_DIFFERENT", "GPT-5.5", 12, "spontaneous forecast of DIFFERENT partner"),
        ("AU_COPY", "AUDITOR_COPY", "Claude Opus 5", 12, "external auditor forecast of GPT COPY policy"),
        ("E0_COPY", "ACT_COPY", "GPT-5.5", 12, "focal act-only, COPY"), ("E0_DIFF", "ACT_DIFFERENT", "GPT-5.5", 12, "focal act-only, DIFFERENT"),
        ("E1_COPY", "FA_COPY", "GPT-5.5", 12, "focal forecast-then-act, COPY"), ("E1_DIFF", "FA_DIFFERENT", "GPT-5.5", 12, "focal forecast-then-act, DIFFERENT")]

# expected per-call cost (USD): act calls = observed means in the 10-15 pilot; forecast calls = estimates from added prompt
# length and the SHAPES prediction/action output ratio (GPT 1.66x, Opus 1.53x). Bounds = token limits (GPT needs max_output_tokens 4000).
TOK = lambda chars: int(818 + (chars - 1380) / 4)                       # GPT input tokens scale from the 818-token act prompt
EXP = {"ACT_COPY|GPT-5.5": 0.01030, "ACT_DIFFERENT|GPT-5.5": 0.01030, "ACT_DIFFERENT|Claude Opus 5": 0.00659,
       "F_COPY|GPT-5.5": TOK(len(PROMPTS["F_COPY"])) * 5e-6 + 395 * 30e-6, "F_DIFFERENT|GPT-5.5": TOK(len(PROMPTS["F_DIFFERENT"])) * 5e-6 + 395 * 30e-6,
       "FA_COPY|GPT-5.5": TOK(len(PROMPTS["FA_COPY"])) * 5e-6 + 630 * 30e-6, "FA_DIFFERENT|GPT-5.5": TOK(len(PROMPTS["FA_DIFFERENT"])) * 5e-6 + 630 * 30e-6,
       "AUDITOR_COPY|Claude Opus 5": (1022 + (len(PROMPTS["AUDITOR_COPY"]) - 1351) / 4) * 5e-6 + 98 * 25e-6}
BOUND = lambda key: (TOK(len(PROMPTS[key.split("|")[0]])) * 5e-6 + 4000 * 30e-6) if "GPT" in key else \
                    ((1022 + max(0, len(PROMPTS[key.split("|")[0]]) - 1351) / 4) * 5e-6 + 4000 * 25e-6)

rng = random.Random(SEED); jobs = []
for it in ITEMS:
    man = json.loads((STIM / it["array"] / "manifest.json").read_text())
    for arm, pk, model, n, role in ARMS:
        if arm == "P_OPUS_DIFF" and it["reuse_opus_policy"]: continue        # Design decision: reuse 10-15 pilot Opus policy (same prompt/settings)
        perms = rng.sample(range(24), 24) if n == 24 else rng.sample(range(24), n)
        for k, p in enumerate(perms):
            img = STIM / it["array"] / f"perm{p:02d}.png"
            jobs.append(dict(job_key=f"{it['array']}|{arm}|{k:02d}", array=it["array"], arm=arm, role=role, model=model, prompt_key=pk,
                             prompt_sha8=sha8(PROMPTS[pk]), perm=p, slot_to_canonical=man[str(p)], image_path=str(img),
                             image_sha256=hashlib.sha256(img.read_bytes()).hexdigest(), status="PROPOSED - not frozen, not dispatchable"))
rng.shuffle(jobs)
for i, j in enumerate(jobs): j["order"] = i
(HERE / "jobs_PROPOSED.jsonl").write_text("".join(json.dumps(j) + "\n" for j in jobs))
by = {}
for j in jobs:
    k = f"{j['prompt_key']}|{j['model']}"; b = by.setdefault(k, dict(n=0, expected=EXP[k], bound=BOUND(k))); b["n"] += 1
tot_e = sum(v["n"] * v["expected"] for v in by.values()); tot_b = sum(v["n"] * v["bound"] for v in by.values())
prior = 4.7525; R = 20 - prior
cost = dict(calls=len(jobs), by_type={k: dict(n=v["n"], expected_per_call=round(v["expected"], 5), bound_per_call=round(v["bound"], 4)) for k, v in by.items()},
            expected_total=round(tot_e, 2), expected_range_forecast_costs_x0_5_to_x1_5=[round(tot_e - .5 * sum(v["n"] * v["expected"] for k, v in by.items() if not k.startswith("ACT")), 2),
                                                                                          round(tot_e + .5 * sum(v["n"] * v["expected"] for k, v in by.items() if not k.startswith("ACT")), 2)],
            hard_bound_total=round(tot_b, 2), proposed_pilot_cap=8.0, prior_cumulative=prior, remaining_under_20=round(R, 4),
            reserve_after_cap=round(R - 8.0, 4), note="Expected costs are estimates from recorded rates, not launch-verified prices. Hard bounds use token limits and require GPT max_output_tokens=4000. The run would reserve each call's bound before dispatch against min(pilot cap, $20 - recomputed cumulative), so it may stop incomplete.")
(HERE / "COST_PROPOSED.json").write_text(json.dumps(cost, indent=1))
print(json.dumps(cost, indent=1))
