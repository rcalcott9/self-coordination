"""Build the PASS=5 adapted-pilot FROZEN-PLAN CANDIDATE (2026-10-16). NOT frozen; not dispatchable until the user and
manager allocate a budget. Same jobs/permutations/items/models/settings/schema as the completed reciprocal-confidence pilot;
only incentive text changes: PASS 7 -> 5 (three game-text lines, appendix 'PASS earns', schema expected_points) and threshold
0.70 -> 0.50. User authorisation for the adaptation: "great. run the adapted pilot" (budget unresolved)."""
import hashlib, json
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
SC = Path.home() / "Desktop/Coordination/Self_Coordination"
RC = SC / "study3a_reciprocal_confidence_20261016"
sha = lambda b: hashlib.sha256(b).hexdigest(); fsha = lambda p: sha(Path(p).read_bytes())
FZ = json.loads((RC / "design/FROZEN.json").read_text())
SUBS = [("- If you choose PASS, you receive 7 points, whatever the other player does.", "- If you choose PASS, you receive 5 points, whatever the other player does.", 1),
        ("you receive 0 points and the other player receives 7 points.", "you receive 0 points and the other player receives 5 points.", 1),
        ("- If you choose PASS and the other player chooses PLAY, you receive 7 points", "- If you choose PASS and the other player chooses PLAY, you receive 5 points", 1),
        ("PASS earns 7;", "PASS earns 5;", 1),
        ("PLAY beats PASS only when that probability exceeds 0.70.", "PLAY beats PASS only when that probability exceeds 0.50.", 1),
        ('"expected_points": {"PASS": 7,', '"expected_points": {"PASS": 5,', 1)]
prompts = {}
for c in ("COPY", "DIFFERENT"):
    t = FZ["prompts"][c]["text"]
    for old, new, n in SUBS:
        assert t.count(old) == n, (c, old); t = t.replace(old, new)
    assert " 7 " not in t and "0.70" not in t and '"PASS": 7' not in t, c
    prompts[c] = dict(text=t, sha8=sha(t.encode())[:8], derived_from=FZ["prompts"][c]["sha8"])
jobs = [json.loads(l) for l in open(RC / "design/jobs.jsonl")]
for j in jobs:
    j["prompt_sha8"] = prompts[j["condition"]]["sha8"]; j["status"] = "CANDIDATE - not frozen, not dispatchable"
cand = dict(status="FROZEN-PLAN CANDIDATE (not frozen; no dispatch until budget allocated and the user/manager approve the freeze)",
            message_id="study3a-pass5-adapted-pilot-prep-01", user_authorisation_verbatim="great. run the adapted pilot",
            pass_value=5, threshold=0.5, items=FZ["items"], models=FZ["models"], prompts=prompts, substitutions=[dict(old=o, new=n) for o, n, _ in SUBS],
            design=dict(per_cell=dict(policy=24, eval=12), jobs="identical keys, roles, permutations and order to the reciprocal-confidence pilot (seed 20261017)",
                        partner_benchmark="fresh PASS=5 policies only; PASS=7 q never used for PASS=5 regret",
                        comparison="exploratory matched-item comparison with the completed PASS=7 reciprocal pilot"),
            outcomes=["regret = (max(5, 10 max_j q_j) - [5 p_PASS + 10 sum_j p_j q_j]) / 10 (same-q plug-in, >= 0)",
                      "joint payoff shortfall = (10 - mean dyadic payoff)/10, 10 = ideal coordination ceiling (not guaranteed attainable without a shared rule)",
                      "realized 10-point matching rate", "mean focal payoff and PLAY rate", "own/partner forecast accuracy (TVD), BR-consistency, EV arithmetic at explicit tolerances"],
            budget=dict(new_experiment_budget=None, note="unresolved; runner refuses dispatch while null"))
(HERE / "design").mkdir(parents=True, exist_ok=True)
(HERE / "design/CANDIDATE.json").write_text(json.dumps(cand, indent=1))
(HERE / "design/jobs_CANDIDATE.jsonl").write_text("".join(json.dumps(j) + "\n" for j in jobs))
for c, v in prompts.items(): (HERE / "design" / f"prompt_{c}_{v['sha8']}_CANDIDATE.txt").write_text(v["text"])
print({c: v["sha8"] for c, v in prompts.items()}, len(jobs), "jobs")
