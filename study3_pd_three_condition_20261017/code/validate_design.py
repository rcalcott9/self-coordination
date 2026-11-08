#!/usr/bin/env python3
"""Offline checks of the PD pilot design. Usage: validate_design.py [CANDIDATE|FROZEN]"""
import json, re, sys, hashlib
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
tag = sys.argv[1] if len(sys.argv) > 1 else "CANDIDATE"
D = json.loads((HERE / f"design/{tag}.json").read_text())
jobs = [json.loads(l) for l in open(HERE / ("design/jobs_CANDIDATE.jsonl" if tag == "CANDIDATE" else "design/jobs.jsonl"))]
J = {j["job_key"]: j for j in jobs}
P = D["payoffs_canonical"]; res = []
def check(name, ok): res.append((name, bool(ok)))

# payoff matrix
check("PD: D strictly dominates vs partner C (10 > 8)", P["DC"][0] > P["CC"][0])
check("PD: D strictly dominates vs partner D (3 > 0)", P["DD"][0] > P["CD"][0])
check("PD: CC > DD for both players", P["CC"][0] > P["DD"][0] and P["CC"][1] > P["DD"][1])
check("PD: symmetric (row CD = col DC)", all(P[a + b][0] == P[b + a][1] for a in "CD" for b in "CD"))
check("PD: T > R > P > S and 2R > T + S", P["DC"][0] > P["CC"][0] > P["DD"][0] > P["CD"][0] and 2 * P["CC"][0] > P["DC"][0] + P["CD"][0])

# prompt text: re-parse each table and check against canonical payoffs via the stated mapping
row = re.compile(r"- You choose ([AB]), the other participant chooses ([AB]): you get (\d+) points, the other participant gets (\d+) points\.")
ok_map = True; partner_par = {}
for k, v in D["prompts"].items():
    t = v["text"]; m = int(k[-1]); L = D["label_to_canonical"][str(m)]
    rows = row.findall(t); ok_map &= len(rows) == 4
    for me, ot, a, b in rows: ok_map &= P[L[me] + L[ot]] == [int(a), int(b)]
    ok_map &= hashlib.sha256(t.encode()).hexdigest()[:8] == v["sha8"]
    for w in ("cooperat", "defect", "betray", "trust", "prisoner", "dilemma", "superrational", "joint", "together", "shared rule"):
        ok_map &= w not in t.lower()
    partner_par[k] = t.split("About the other participant:\n")[1].split("\n\nReply with")[0]
check("prompt tables re-parse to canonical payoffs under stated A/B mapping; hashes match; no loaded words", ok_map)
strip = {k: v["text"].replace(partner_par[k], "<PARTNER>") for k, v in D["prompts"].items()}
check("non-condition text identical across conditions and models (per mapping)",
      all(len({s for k, s in strip.items() if k.endswith(f"map{m}")}) == 1 for m in (0, 1)))
check("same-model and fixed paragraphs name the focal model; different-model names the other model",
      all((k.split("|")[0] in partner_par[k]) and ((k.split("|")[1] != "different_model") or
          ({"GPT-5.5": "Claude Opus 5", "Claude Opus 5": "GPT-5.5"}[k.split("|")[0]] in partner_par[k])) for k in partner_par))
check("fixed paragraph does not disclose bank action or rate", all(not re.search(r"\b(A|B)\b|%|rate|percent", partner_par[k]) for k in partner_par if "fixed" in k))

# jobs
check("384 jobs, 64 per model x condition", len(jobs) == 384 and set(Counter((j["model"], j["condition"]) for j in jobs).values()) == {64})
check("label mapping balanced 32/32 within every cell", set(Counter((j["model"], j["condition"], j["mapping"]) for j in jobs).values()) == {32})
check("job prompt hash matches its prompt", all(D["prompts"][j["prompt_key"]]["sha8"] == j["prompt_sha8"] for j in jobs))
check("unique job keys and order 0..383", len(J) == 384 and sorted(j["order"] for j in jobs) == list(range(384)))
same = [j for j in jobs if j["condition"] == "same_model"]; fx = [j for j in jobs if j["condition"] == "fixed_response"]; dif = [j for j in jobs if j["condition"] == "different_model"]
check("same_model: partner is a distinct same-model same_model response (no self-pairing)",
      all(j["partner_job_key"] != j["job_key"] and J[j["partner_job_key"]]["model"] == j["model"] and J[j["partner_job_key"]]["condition"] == "same_model" for j in same))
check("same_model: pairing is a permutation (each response is a partner once)", len({j["partner_job_key"] for j in same}) == 128)
check("fixed: each bank response assigned exactly once, same model", all(J[j["bank_assignment"]]["condition"] == "same_model" and J[j["bank_assignment"]]["model"] == j["model"] for j in fx) and len({j["bank_assignment"] for j in fx}) == 128)
check("different: partner is the other model's different_model response, reciprocal dyads",
      all(J[j["partner_job_key"]]["model"] != j["model"] and J[j["partner_job_key"]]["condition"] == "different_model" and J[J[j["partner_job_key"]]["partner_job_key"]]["job_key"] == j["job_key"] for j in dif))
check("all pairs share the label mapping (same payoff table)", all(J[j["partner_job_key"]]["mapping"] == j["mapping"] for j in jobs))
mx1 = max(j["order"] for j in jobs if j["phase"] == 1); mn2 = min(j["order"] for j in jobs if j["phase"] == 2)
check("phase order: every fixed_response job after every same_model/different_model job", mx1 < mn2 and all((j["phase"] == 2) == (j["condition"] == "fixed_response") for j in jobs))
fc = [j for j in jobs if j["format_check"]]
check("format check = first 8 frozen jobs, one per model x {same,different} x mapping",
      len(fc) == 8 and {j["order"] for j in fc} == set(range(8)) and len({(j["model"], j["condition"], j["mapping"]) for j in fc}) == 8)

for n, t in res: print(("PASS " if t else "FAIL ") + n)
print(f"{sum(t for _, t in res)}/{len(res)} checks passed")
sys.exit(0 if all(t for _, t in res) else 1)
