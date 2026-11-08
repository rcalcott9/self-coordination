"""STAGE 2 pre-freeze: the realized-partner draw for UNKNOWN, and the COPY pairing seed.

Both are predeclared here, BEFORE any strategic call, so neither can be chosen after
seeing outcomes. The UNKNOWN draw is balanced 12/12 within every array so each array
carries the same number of Claude-partner and GPT-partner realizations.
"""
import hashlib, json, os, random, sys

EXP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(EXP, "pilot")
DRAW_SEED = 20260908102
PAIR_SEED = 20260908103


def main(approval):
    man = json.load(open(os.path.join(P, "PILOT_MANIFEST_FINAL.json")))
    arrays = [a["array_id"] for a in man["asymmetric"]] + \
             [c["array_id"] for c in man["controls"]]
    assert len(arrays) == 14, len(arrays)
    rng = random.Random(DRAW_SEED)
    draw = {}
    for sid in sorted(arrays):
        who = ["claude"] * 12 + ["gpt"] * 12          # exact 50/50 within array
        rng.shuffle(who)
        draw[sid] = {str(p): who[p] for p in range(24)}
    spec = dict(
        stage="strategic_pilot",
        arrays=sorted(arrays),
        n_asymmetric=len(man["asymmetric"]), n_control=len(man["controls"]),
        conditions=["copy", "other", "unknown"], arms=["action", "predict"],
        perms="all 24, each exactly once, per array x condition x arm x role",
        unknown_draw_seed=DRAW_SEED,
        unknown_realized_partner=draw,
        unknown_balance="exactly 12 claude / 12 gpt realizations per array",
        copy_pairing=dict(
            seed=PAIR_SEED,
            primary="unbiased dyadic match sum_k n_k(n_k-1)/[N(N-1)] over the 24 COPY "
                    "action responses per array - all pairs, bias-corrected, uncertainty "
                    "by bootstrap over the 24 RESPONSES (never over pairs)",
            realized="12 disjoint pairs per array from a seeded shuffle, used for realized "
                     "payoff; no response is ever paired with itself and no response "
                     "appears in two pairs",
            sampling_units="responses within array; arrays across the item-type contrast"),
        partner_sources=dict(
            copy="focal Claude COPY action responses (symmetric prompt), paired as above",
            other="independent GPT-5.5 action calls, prompt gpt|other|action",
            unknown="independent action calls from the realized partner, prompt "
                    "{claude,gpt}|unknown_partner|action - never recycled from COPY"),
        green="locked in PILOT_MANIFEST_LOCKED.json, unchanged; green payoff 5, "
              "unmarked payoff 10, mismatch 0",
        review_sheet_approval=approval,
        prompt_sha=json.load(open(os.path.join(P, "prompt_sha.json")))
        if os.path.exists(os.path.join(P, "prompt_sha.json")) else None)
    sys.path.insert(0, os.path.join(EXP, "code"))
    import pilot_prompts as PP
    spec["prompt_sha"] = PP.PROMPT_SHA
    p = os.path.join(P, "STRATEGIC_RUN_LOCKED.json")
    json.dump(spec, open(p, "w"), indent=1)
    h = hashlib.sha256(open(p, "rb").read()).hexdigest()
    open(p + ".sha256", "w").write(h + "\n")
    n_focal = 14 * 3 * 2 * 24
    print(f"arrays {len(arrays)}  ({spec['n_asymmetric']} asym + {spec['n_control']} control)")
    print(f"focal claude calls : {n_focal}")
    print(f"other partner (gpt): {14*24}")
    print(f"unknown partner    : {14*24}  (12 claude / 12 gpt per array)")
    print(f"TOTAL stage 2      : {n_focal + 14*24*2}")
    print(f"approval recorded  : {approval}")
    print(f"sha256: {h}")


if __name__ == "__main__":
    main(json.loads(sys.argv[1]) if len(sys.argv) > 1 else None)
