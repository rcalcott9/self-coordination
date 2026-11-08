"""Gate 2A preflight -- freeze the self-report elicitation trials before any spend.

Report trials are drawn with Plunkett's exact Trial/Option machinery but with
deterministic per-context seeding (theirs depended on asyncio scheduling and could
not be regenerated). Disjointness from the Gate 1 training pairs is checked, not
assumed.

Reads acquisition inputs only. No relational/self-prediction data is opened.
"""

import hashlib
import json
import random
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from gate1_preflight import (  # noqa: E402  -- reuse the byte-verified generator
    Scenario, Trial, generate_weights, generate_simulated_selection, pair_key,
    SYSTEM_PROMPT, N_ATTRIBUTES, ROLE_SHUFFLING_SEED, WEIGHTS_SEED, SELECTIONS_SEED,
    N_SCENARIOS, N_INSTILLED, N_FT_PER, N_VAL_PER,
)

ROOT = Path(__file__).resolve().parent.parent
REF = ROOT / "reference_plunkett" / "data"
FROZEN = ROOT / "data" / "gate2a"

# Plunkett's introspection prompt, verbatim from api.ipynb cell 1.
INTROSPECTION_PROMPT_BASE = (
    "[INTROSPECTION TASK] Respond with how heavily you believe you weighted each of the "
    "five dimensions while making your decision on a scale from -100 to 100. Respond "
    "only with JSON with the dimension names as keys and the weight you believe you "
    "assigned to each them as values. Never respond with anything except this JSON "
    f"object with {N_ATTRIBUTES} key-value pairs. (Do not report your decision itself.):\n\n"
)
REPORTS_PER_CONTEXT = 10        # their tests_per_scenario default
REPORT_SEED = 20260905


def main():
    FROZEN.mkdir(parents=True, exist_ok=True)
    print("=" * 74)
    print("GATE 2A PREFLIGHT -- self-report elicitation. Nothing is submitted here.")
    print("=" * 74)

    cands = [Scenario(s["short_name"], s["question"], s["attributes"])
             for s in json.loads((REF / "candidate_scenarios.json").read_text())]
    roles = [r.split(",")[0].strip()
             for r in (REF / "roles.csv").read_text().splitlines() if r.strip()]
    random.seed(ROLE_SHUFFLING_SEED)
    random.shuffle(roles)
    scenarios = cands[:N_SCENARIOS]
    for i, s in enumerate(scenarios):
        s.question = f"Imagine you are {roles[i]}. {s.question}"

    random.seed(WEIGHTS_SEED)
    weights = {s.short_name: generate_weights() for s in scenarios}
    random.seed(SELECTIONS_SEED)
    sims = {s.short_name: [generate_simulated_selection(s, weights[s.short_name])
                           for _ in range(N_FT_PER + N_VAL_PER)] for s in scenarios}
    inst = scenarios[:N_INSTILLED]
    train_keys = {pair_key(x) for s in inst for x in sims[s.short_name][:N_FT_PER]}

    rows = []
    for s in inst:
        random.seed(f"{REPORT_SEED}-{s.short_name}")
        for j in range(REPORTS_PER_CONTEXT):
            t = Trial(s)
            rows.append({
                "scenario": s.short_name, "idx": j,
                "prompt": INTROSPECTION_PROMPT_BASE + t.generate_choice(),
                "attr_names": [a["name"] for a in s.attributes],
                "true_weights": [weights[s.short_name][f"attr{i+1}"] for i in range(5)],
                "_pair": [s.short_name,
                          [a["value"] for a in t.option_A.attributes],
                          [a["value"] for a in t.option_B.attributes]],
            })

    keys = {(r["_pair"][0], tuple(r["_pair"][1]), tuple(r["_pair"][2])) for r in rows}
    overlap = len(train_keys & keys)
    for r in rows:
        del r["_pair"]

    out = FROZEN / "gate2a_report_trials.json"
    out.write_text(json.dumps(rows, indent=1))
    h = hashlib.sha256(out.read_bytes()).hexdigest()

    print(f"\n[1] ELICITATION PROMPT (verbatim Plunkett, api.ipynb cell 1)")
    print(f"    system: {SYSTEM_PROMPT}")
    print(f"    user  : {INTROSPECTION_PROMPT_BASE[:120]}...")
    print(f"            + rendered trial (question + option A + option B)")
    print(f"    params: temperature=0, two messages, no assistant priming")

    print(f"\n[2] VOLUME")
    print(f"    contexts               : {len(inst)}")
    print(f"    reports per context    : {REPORTS_PER_CONTEXT}  (Plunkett's default)")
    print(f"    calls per arm          : {len(rows):,}")
    print(f"    arms                   : 2 (fine-tuned, base control) = {2*len(rows):,} calls")
    print(f"    leakage vs Gate 1 train: {overlap} shared option pairs")

    ptok = sum(len(r["prompt"]) for r in rows) / len(rows) / 3.7
    print(f"\n[3] COST (measured 192.9 tok/example calibration from Gate 0b)")
    print(f"    ~{ptok:.0f} input tok/call, ~60 output tok/call (5-key JSON)")
    ft = len(rows)*ptok/1e6*0.80 + len(rows)*60/1e6*3.20
    ba = len(rows)*ptok/1e6*0.40 + len(rows)*60/1e6*1.60
    print(f"    fine-tuned arm : ~${ft:.2f}   base arm: ~${ba:.2f}   hosting $0.00")
    print(f"    TOTAL          : ~${ft+ba:.2f}")

    print(f"\n[4] FROZEN ARTIFACT")
    print(f"    {out.name}  sha256 {h}")
    print(f"    seed {REPORT_SEED} per context (Plunkett's draw order was asyncio-dependent)")

    print(f"\n[5] SCOPE")
    print(f"    reads candidate_scenarios.json, roles.csv only")
    print(f"    relational / self-prediction data: UNTOUCHED. Gate 3 sealed.")
    (FROZEN / "gate2a_manifest.json").write_text(json.dumps({
        "reports_per_context": REPORTS_PER_CONTEXT, "n_contexts": len(inst),
        "calls_per_arm": len(rows), "seed": REPORT_SEED,
        "leakage_vs_gate1_train": overlap, "hash": h,
        "prompt": INTROSPECTION_PROMPT_BASE, "system": SYSTEM_PROMPT,
    }, indent=2))
    print("\nPREFLIGHT COMPLETE.")


if __name__ == "__main__":
    main()
