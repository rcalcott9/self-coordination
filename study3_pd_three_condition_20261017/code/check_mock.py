#!/usr/bin/env python3
"""Offline checks of runner output. Usage: check_mock.py <results dir> [cap]"""
import json, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent.parent
d = Path(sys.argv[1]); cap = float(sys.argv[2]) if len(sys.argv) > 2 else None
r = {x["job_key"]: x for x in map(json.loads, open(d / "responses.jsonl"))}
J = {j["job_key"]: j for j in map(json.loads, open(HERE / "design/jobs.jsonl"))}
req = [json.loads(l) for l in open(d / "requests.jsonl")]
spent = sum(x["cost_usd"] for x in r.values())
print("records", len(r), "requests", len(req), "spent", round(spent, 5))
print("by condition", {c: sum(x["condition"] == c for x in r.values()) for c in ("same_model", "different_model", "fixed_response")})
print("status", {s: sum(x["status"] == s for x in r.values()) for s in ("ok", "invalid_response", "refusal", "api_failure")})
print("canonical mapping ok", all(x["action_canonical"] == J[k]["label_to_canonical"][x["action_label"]] for k, x in r.items() if x["status"] == "ok"))
if cap is not None:
    print("spent + max single bound <= cap", spent <= cap)
    print("no fixed_response while bank incomplete", not any(x["condition"] == "fixed_response" for x in r.values()) or (d / "bank_sealed.json").exists())
if (d / "assignments.jsonl").exists():
    A = [json.loads(l) for l in open(d / "assignments.jsonl")]
    bank = json.load(open(d / "bank_sealed.json"))
    print("assignments", len(A), "unique bank responses", len({a["bank_job_key"] for a in A}))
    print("assignments match frozen", all(J[a["job_key"]]["bank_assignment"] == a["bank_job_key"] for a in A))
    print("assigned action matches bank record", all(r[a["bank_job_key"]]["action_canonical"] == a["bank_action_canonical"] for a in A))
    seal = min(v["sealed_at"] for v in bank.values())
    print("all fixed records after bank seal", all(x["ts"] >= seal for x in r.values() if x["condition"] == "fixed_response"))
    print("all bank records before seal", all(x["ts"] <= seal for x in r.values() if x["condition"] == "same_model"))
