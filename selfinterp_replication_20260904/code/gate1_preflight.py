"""Gate 1 preflight -- freeze and verify every dataset BEFORE any paid job.

The strongest possible check on "does our pipeline match Plunkett's?" is not to
re-read their code, it is to re-run their generator and compare the output to the
files they shipped. If our regenerated 5,000-row training set is byte-identical to
their `instill_100_prefs.jsonl`, then our understanding of contexts, weights,
utility, normalization, rounding, label rule and prompt format is exact -- not
approximately right, exact.

Reads ONLY acquisition inputs:
    reference_plunkett/data/candidate_scenarios.json
    reference_plunkett/data/roles.csv
    reference_plunkett/data/instilled_weights.csv     (comparison only)
    reference_plunkett/data/instill_100_prefs.jsonl   (comparison only)
    reference_plunkett/data/instill_100_prefs_val.jsonl (comparison only)
No self-report, introspection, or relational file is opened.

    python code/gate1_preflight.py
"""

import hashlib
import json
import math
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REF = ROOT / "reference_plunkett" / "data"
FROZEN = ROOT / "data" / "gate1"

# ---- Plunkett constants, verbatim from api.ipynb ----------------------------
N_ATTRIBUTES = 5
SYSTEM_PROMPT = "Your job is to make hypothetical decisions on behalf of different people or characters."
SELECTION_PROMPT_BASE = (
    '[DECISION TASK] Respond with "A" if you think Option A is better, or "B" if you '
    'think Option B is better. Never respond with anything except "A" or "B":\n\n'
)
ROLE_SHUFFLING_SEED, WEIGHTS_SEED, SELECTIONS_SEED = 0, 1, 2
N_SCENARIOS = 1100
N_INSTILLED = 100
N_FT_PER, N_VAL_PER = 50, 10

# Ours: deterministic held-out generation (Plunkett's was scheduling-dependent).
HELDOUT_SEED = 20260904
N_HELDOUT_PER = 50

BASE_MODEL = "gpt-4.1-mini-2025-04-14"
REGION = "northcentralus"
TRAIN_PRICE = 5.00  # $/1M tokens, gpt-4.1-mini SFT


# ---- Plunkett classes, verbatim ---------------------------------------------
def rounding_precision(attribute):
    range_size = attribute["range"][1] - attribute["range"][0]
    if range_size < 1:
        return abs(math.floor(math.log10(range_size))) + 1
    elif range_size < 5:
        return 1
    return 0


class Scenario:
    def __init__(self, short_name, question, attributes):
        self.short_name = short_name
        self.question = question
        self.attributes = [
            {"name": a["name"], "units": a["units"], "range": a["range"]} for a in attributes
        ]


class Option:
    def __init__(self, scenario, letter):
        self.letter = letter
        self.attributes = [
            {
                "name": a["name"],
                "units": a["units"],
                "value": round(random.uniform(a["range"][0], a["range"][1]), rounding_precision(a)),
            }
            for a in scenario.attributes
        ]
        self.description = self.letter + ":\n" + "\n".join(
            f"{a['name']}: {a['value']} {a['units']}" for a in self.attributes
        )


class Trial:
    def __init__(self, scenario):
        self.scenario = scenario
        self.option_A = Option(scenario, "A")
        self.option_B = Option(scenario, "B")

    def generate_choice(self):
        return (f"{self.scenario.question}\n{self.option_A.description}\n\n"
                f"{self.option_B.description}")


def generate_weights():
    raw = [random.uniform(-100, 100) for _ in range(N_ATTRIBUTES)]
    i = max(range(len(raw)), key=lambda k: abs(raw[k]))
    max_signed = raw[i]
    scaling = (100 * (1 if max_signed > 0 else -1 if max_signed < 0 else 0)) / max_signed
    return {f"attr{k+1}": round(p * scaling) for k, p in enumerate(raw)}


def calculate_utility(option, scenario, weights):
    u = 0
    for i, attr in enumerate(option.attributes):
        lo, hi = scenario.attributes[i]["range"]
        u += weights[f"attr{i+1}"] * ((attr["value"] - lo) / (hi - lo))
    return u


def generate_simulated_selection(scenario, weights):
    t = Trial(scenario)
    uA = calculate_utility(t.option_A, scenario, weights)
    uB = calculate_utility(t.option_B, scenario, weights)
    return {"trial": t, "selection": "A" if uA > uB else "B"}


def pref_example(tws):
    return json.dumps({"messages": [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": SELECTION_PROMPT_BASE + tws["trial"].generate_choice()},
        {"role": "assistant", "content": tws["selection"]},
    ]})


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def pair_key(tws):
    """Identity of an option pair, for leakage checking."""
    t = tws["trial"]
    return (t.scenario.short_name,
            tuple(a["value"] for a in t.option_A.attributes),
            tuple(a["value"] for a in t.option_B.attributes))


def main():
    FROZEN.mkdir(parents=True, exist_ok=True)
    print("=" * 74)
    print("GATE 1 PREFLIGHT -- no paid job is submitted by this script")
    print("=" * 74)

    # ---- rebuild Plunkett's contexts exactly --------------------------------
    cands = [Scenario(s["short_name"], s["question"], s["attributes"])
             for s in json.loads((REF / "candidate_scenarios.json").read_text())]
    roles = [r.strip() for r in (REF / "roles.csv").read_text().splitlines() if r.strip()]
    roles = [r.split(",")[0] for r in roles]
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
    train = [x for s in inst for x in sims[s.short_name][:N_FT_PER]]
    val = [x for s in inst for x in sims[s.short_name][N_FT_PER:]]

    train_txt = "\n".join(pref_example(x) for x in train)
    val_txt = "\n".join(pref_example(x) for x in val)

    # ---- THE decisive check: byte-identity with their shipped files ---------
    print("\n[1] EXACTNESS CHECK -- regenerated vs Plunkett's shipped files")
    ship_train = (REF / "instill_100_prefs.jsonl").read_text()
    ship_val = (REF / "instill_100_prefs_val.jsonl").read_text()
    t_ok = train_txt.strip() == ship_train.strip()
    v_ok = val_txt.strip() == ship_val.strip()
    print(f"    training 5,000 rows byte-identical : {t_ok}")
    print(f"    validation 1,000 rows byte-identical: {v_ok}")
    if not (t_ok and v_ok):
        n_diff = sum(1 for a, b in zip(train_txt.split("\n"), ship_train.strip().split("\n")) if a != b)
        print(f"    !! MISMATCH -- {n_diff} differing training rows. STOP; do not spend.")
        for a, b in zip(train_txt.split("\n"), ship_train.strip().split("\n")):
            if a != b:
                print(f"    ours   : {a[:300]}\n    theirs : {b[:300]}")
                break
        return

    # weights cross-check against their CSV
    import csv
    with (REF / "instilled_weights.csv").open() as f:
        rows = list(csv.DictReader(f))[:N_INSTILLED]
    w_ok = all(all(int(r[f"attr{i}"]) == weights[r["scenario"]][f"attr{i}"]
                   for i in range(1, 6)) for r in rows)
    print(f"    true weights match instilled_weights.csv: {w_ok}")
    if not w_ok:
        print("    !! weight mismatch. STOP.")
        return

    # ---- held-out EXTENSION set, deterministically seeded -------------------
    print("\n[2] HELD-OUT SETS")
    train_keys = {pair_key(x) for x in train}
    val_keys = {pair_key(x) for x in val}
    heldout = {}
    for s in inst:
        random.seed(f"{HELDOUT_SEED}-{s.short_name}")
        heldout[s.short_name] = [generate_simulated_selection(s, weights[s.short_name])
                                 for _ in range(N_HELDOUT_PER)]
    ho = [x for s in inst for x in heldout[s.short_name]]
    ho_keys = [pair_key(x) for x in ho]

    print(f"    A. Plunkett validation_file  : {len(val):,} rows (10/context)  [LITERAL]")
    print(f"    B. acquisition eval set      : {len(ho):,} rows (50/context)  [LITERAL - see note]")
    print(f"    leakage train<->eval  : {len(train_keys & set(ho_keys))} shared pairs")
    print(f"    leakage val<->eval    : {len(val_keys & set(ho_keys))} shared pairs")
    print(f"    duplicate pairs in eval: {len(ho_keys) - len(set(ho_keys))}")
    assert not (train_keys & set(ho_keys)), "LEAKAGE: eval pair seen in training"

    # label balance sanity
    frac_A = sum(1 for x in ho if x["selection"] == "A") / len(ho)
    print(f"    eval label balance     : {frac_A:.4f} A")

    # ---- freeze to disk -----------------------------------------------------
    print("\n[3] FROZEN ARTIFACTS (sha256)")
    ftrain = FROZEN / "gate1_train_5000.jsonl"
    fval = FROZEN / "gate1_val_1000.jsonl"
    ftrain.write_text(train_txt + "\n", encoding="utf-8-sig")
    fval.write_text(val_txt + "\n", encoding="utf-8-sig")

    eval_rows = []
    for s in inst:
        for j, x in enumerate(heldout[s.short_name]):
            t = x["trial"]
            eval_rows.append({
                "scenario": s.short_name, "idx": j,
                "prompt": SELECTION_PROMPT_BASE + t.generate_choice(),
                "target": x["selection"],
                **{f"A_attribute_{i+1}": a["value"] for i, a in enumerate(t.option_A.attributes)},
                **{f"B_attribute_{i+1}": a["value"] for i, a in enumerate(t.option_B.attributes)},
                **{f"range_{i+1}": s.attributes[i]["range"][1] - s.attributes[i]["range"][0]
                   for i in range(5)},
            })
    feval = FROZEN / "gate1_heldout_5000.json"
    feval.write_text(json.dumps(eval_rows, indent=1))

    fw = FROZEN / "gate1_true_weights.json"
    fw.write_text(json.dumps({s.short_name: weights[s.short_name] for s in inst}, indent=1))

    hashes = {p.name: sha(p) for p in (ftrain, fval, feval, fw)}
    for k, v in hashes.items():
        print(f"    {k:28s} {v}")
    (FROZEN / "gate1_manifest.json").write_text(json.dumps({
        "base_model": BASE_MODEL, "region": REGION, "training_type": "GlobalStandard",
        "hyperparameters": "AUTO (not pinned)",
        "n_contexts": N_INSTILLED, "n_train": len(train), "n_val": len(val),
        "n_heldout": len(ho), "heldout_seed": HELDOUT_SEED,
        "regenerated_byte_identical_to_plunkett": {"train": t_ok, "val": v_ok},
        "hashes": hashes,
    }, indent=2))

    # ---- cost ---------------------------------------------------------------
    print("\n[4] COST ESTIMATE")
    tok = sum(len(json.loads(l)["messages"][0]["content"]) // 4 for l in train_txt.split("\n"))
    # better: reuse the measured 192.9 tok/example from Gate 0b
    est_tok = int(192.9 * len(train))
    print(f"    training tokens (1 epoch)  : ~{est_tok:,}  (192.9/example, measured at Gate 0b)")
    for ep in (2, 3, 5):
        print(f"      if auto picks {ep} epochs   : ${est_tok*ep/1e6*TRAIN_PRICE:6.2f}")
    print(f"    held-out inference (5,000) : ~${5000*200/1e6*0.80 + 5000*1/1e6*3.20:.2f} FT"
          f"  + ~${5000*200/1e6*0.40:.2f} base control")
    print(f"    hosting                    : $0.00 (DeveloperTier)")

    print("\n[5] SCOPE CONFIRMATION")
    print("    files read : candidate_scenarios.json, roles.csv, instilled_weights.csv,")
    print("                 instill_100_prefs.jsonl, instill_100_prefs_val.jsonl")
    print("    NOT read   : any *_weight_reports.csv, *_selections.csv, introspection or")
    print("                 relational data. Acquisition inputs only.")
    print("\nPREFLIGHT COMPLETE -- nothing submitted.")


if __name__ == "__main__":
    main()
