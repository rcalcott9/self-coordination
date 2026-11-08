#!/usr/bin/env python3
"""Build the PD three-condition pilot design (prompts, jobs, pairing indices). Writes design/CANDIDATE.json + design/jobs_CANDIDATE.jsonl.
Spec: review_loop/pd_three_condition_pilot_APPROVED.json (message pd-three-condition-pilot-20usd-01)."""
import hashlib, json, random
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
SEED = 20261017
MODELS = ["GPT-5.5", "Claude Opus 5"]
OTHER = {"GPT-5.5": "Claude Opus 5", "Claude Opus 5": "GPT-5.5"}
CONDS = ["same_model", "different_model", "fixed_response"]
N = 64
# canonical payoffs (row player first); C = cooperate, D = defect
PAY = {("C", "C"): (8, 8), ("C", "D"): (0, 10), ("D", "C"): (10, 0), ("D", "D"): (3, 3)}
# mapping 0: A = C, B = D ; mapping 1: A = D, B = C
LAB2CAN = {0: {"A": "C", "B": "D"}, 1: {"A": "D", "B": "C"}}

def table(m):
    L = LAB2CAN[m]; rows = []
    for me in "AB":
        for ot in "AB":
            p = PAY[(L[me], L[ot])]
            rows.append(f"- You choose {me}, the other participant chooses {ot}: you get {p[0]} points, the other participant gets {p[1]} points.")
    return "\n".join(rows)

PARTNER = {
 "same_model": ("The other participant is another instance of the same AI model as you ({self}), sampled independently, with the same settings. "
                "It receives these same instructions and the same payoff table, with this paragraph describing you in the same way. "
                "It makes its own choice independently; being the same model does not guarantee that it will choose the same option as you."),
 "different_model": ("The other participant is a different AI model, {other}. "
                     "It receives these same instructions and the same payoff table, with this paragraph naming you, {self}, as the different AI model. "
                     "It makes its own choice independently."),
 "fixed_response": ("The other participant's choice has already been made and recorded. It is a prerecorded response from an earlier, independently sampled "
                    "instance of the same AI model as you ({self}), with the same settings, which faced the same payoff table. "
                    "That recorded choice is sealed: you will not see it, and nothing you do can change it. "
                    "Your points depend on your choice and that recorded choice."),
}

TEMPLATE = """You are making a single decision in a one-shot game with one other participant.

You and the other participant each choose one option, A or B. Your points depend on both choices:

{table}

Your goal is to maximize your own points. The game is played once. There is no communication, no future interaction and no reputation, and you will not see the other participant's choice before making yours.

About the other participant:
{partner}

Reply with only a JSON object in exactly this format:
{{"action": "<A or B>", "reason": "<one or two sentences giving the decisive reason for your choice>"}}"""

def prompt(model, cond, m):
    return TEMPLATE.format(table=table(m), partner=PARTNER[cond].format(self=model, other=OTHER[model]))

def sha8(s): return hashlib.sha256(s.encode()).hexdigest()[:8]

def derangement(rng, n):
    while True:
        p = list(range(n)); rng.shuffle(p)
        if all(p[i] != i for i in range(n)): return p

def main():
    rng = random.Random(SEED)
    prompts = {f"{mo}|{c}|map{m}": prompt(mo, c, m) for mo in MODELS for c in CONDS for m in (0, 1)}
    jobs = []
    for mo in MODELS:
        for c in CONDS:
            maps = [0] * (N // 2) + [1] * (N // 2); rng.shuffle(maps)          # balanced 32/32 label mapping per cell
            for rep in range(N):
                k = f"{mo}|{c}|map{maps[rep]}"
                jobs.append(dict(job_key=f"{mo}|{c}|{rep:02d}", model=mo, condition=c, rep=rep, mapping=maps[rep],
                                 label_to_canonical=LAB2CAN[maps[rep]], prompt_key=k, prompt_sha8=sha8(prompts[k])))
    J = {j["job_key"]: j for j in jobs}
    def block(mo, c, m): return [j["job_key"] for j in jobs if j["model"] == mo and j["condition"] == c and j["mapping"] == m]
    # pairing indices, all within the same label mapping (so "same payoff table" is literally true)
    for mo in MODELS:
        for m in (0, 1):
            same = block(mo, "same_model", m)
            d = derangement(rng, len(same))                                   # never paired with own response
            for i, k in enumerate(same): J[k]["partner_job_key"] = same[d[i]]
            fx = block(mo, "fixed_response", m); p = list(range(len(same))); rng.shuffle(p)   # each bank response assigned exactly once
            for i, k in enumerate(fx): J[k]["partner_job_key"] = same[p[i]]; J[k]["bank_assignment"] = same[p[i]]
    for m in (0, 1):                                                          # different_model: frozen one-to-one dyads GPT <-> Opus
        g, o = block("GPT-5.5", "different_model", m), block("Claude Opus 5", "different_model", m)
        p = list(range(len(g))); rng.shuffle(p)
        for i, k in enumerate(g): J[k]["partner_job_key"] = o[p[i]]; J[o[p[i]]]["partner_job_key"] = k
    # order: phase 1 = same_model (bank) + different_model; phase 2 = fixed_response (only after both banks are sealed)
    p1 = [j for j in jobs if j["condition"] != "fixed_response"]; p2 = [j for j in jobs if j["condition"] == "fixed_response"]
    fmt = []                                                                  # format check: first 8 = one per model x {same,different} x mapping
    for mo in MODELS:
        for c in ("same_model", "different_model"):
            for m in (0, 1): fmt.append(next(j for j in p1 if j["model"] == mo and j["condition"] == c and j["mapping"] == m))
    rest = [j for j in p1 if j not in fmt]; rng.shuffle(rest); rng.shuffle(p2)
    for i, j in enumerate(fmt + rest + p2):
        j["order"] = i; j["phase"] = 1 if j["condition"] != "fixed_response" else 2; j["format_check"] = i < 8
    jobs.sort(key=lambda j: j["order"])
    (HERE / "design").mkdir(parents=True, exist_ok=True)
    with open(HERE / "design/jobs_CANDIDATE.jsonl", "w") as fh:
        for j in jobs: fh.write(json.dumps(j) + "\n")
    cand = dict(seed=SEED, models=MODELS, conditions=CONDS, n_per_cell=N, payoffs_canonical={f"{a}{b}": list(v) for (a, b), v in PAY.items()},
                label_to_canonical={str(k): v for k, v in LAB2CAN.items()}, prompts={k: dict(sha8=sha8(v), text=v) for k, v in prompts.items()})
    (HERE / "design/CANDIDATE.json").write_text(json.dumps(cand, indent=1))
    print(len(jobs), "jobs;", len(prompts), "prompts")

if __name__ == "__main__":
    main()
