#!/usr/bin/env python3
"""Print explanation subsets for manual review (seeded samples). Usage: review_explanations.py"""
import json, re, random
from pathlib import Path
HERE = Path(__file__).resolve().parent.parent
r = [json.loads(l) for l in open(HERE / "results/run/responses.jsonl")]
print("== GPT cooperators")
for x in r:
    if x["model"] == "GPT-5.5" and x["action_canonical"] == "C": print(x["condition"], "map", x["mapping"], x["action_label"], "|", x["reason"])
mis = [x for x in r if x["model"] == "Claude Opus 5" and re.search(r"stag hunt|not a prisoner|coordination game", x["reason"], re.I)]
print("== Opus misread", len(mis), {c: sum(x["condition"] == c for x in mis) for c in ("same_model", "different_model", "fixed_response")},
      "by mapping", {m: sum(x["mapping"] == m for x in mis) for m in (0, 1)})
for x in mis[:4]: print(x["condition"], "map", x["mapping"], "|", x["reason"])
rng = random.Random(1)
for c in ("same_model", "different_model", "fixed_response"):
    print("== Opus", c)
    for x in rng.sample([x for x in r if x["model"] == "Claude Opus 5" and x["condition"] == c], 4): print("map", x["mapping"], "|", x["reason"])
print("== GPT fixed D sample")
for x in rng.sample([x for x in r if x["model"] == "GPT-5.5" and x["condition"] == "fixed_response" and x["action_canonical"] == "D"], 3): print("map", x["mapping"], "|", x["reason"])
