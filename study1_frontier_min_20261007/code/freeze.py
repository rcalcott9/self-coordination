"""Build design/FROZEN.json (+ .sha256) and design/LEGACY_MANIFEST.json. No API calls.

Freezes: models + inference settings, all prompt texts and sha8s, the 41 arrays with
stimulus hashes, and every presentation schedule for every stage. Schedules are balanced
Latin squares (each canonical shape in each display slot equally often), drawn with
str-seeded RNGs, which are deterministic across processes (unlike the frame runner's
hash() seed). Old PLAY/PASS data and the reused calibration are recorded by sha256 only.
"""
import csv, glob, hashlib, json, os, random, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SC = os.path.dirname(ROOT)
sys.path.insert(0, HERE)
import prompts as PR                                                   # noqa: E402

SPC = os.path.join(SC, "study_policy_convergence_20260909")
STIM = os.path.join(SC, "study2_4opt_20260830", "stimuli")
STAG = os.path.expanduser("~/Desktop/Superrationality/Stag")
SEED = "S1FMIN-20261007"


def sha256f(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def sha8(s):
    return hashlib.sha256(s.encode()).hexdigest()[:8]


MODELS = {
    "gpt": {"model_id": "gpt-5.5-2026-04-23", "provider": "openai.responses",
            "settings": {"reasoning": {"effort": "low", "summary": "auto"}},
            "surface": "reasoning.effort=low",
            "matches_calibration": "frame run: same id, same reasoning params (pc_common.ask_gpt)"},
    "claude": {"model_id": "claude-opus-5", "provider": "anthropic.messages",
               "settings": {"thinking": {"type": "disabled"}, "max_tokens": 1024},
               "surface": "thinking=disabled",
               "matches_calibration": "frame run: same alias, thinking disabled, max_tokens 1024 (pc_common.ask_claude)",
               "alias_note": "no dated snapshot exists; weights identity certified to the alias on the run date only"},
}

# Per-array reps for each stage x task. Multiples of 4 so Latin squares balance exactly.
DESIGN = {
    "preflight": {"CALIB": 1, "PLAYPASS": 1, "SELFPRED": 1, "AUDITOR": 1},
    "pilot":     {"PLAYPASS": 4, "SELFPRED": 4, "AUDITOR": 4},
    "anchor":    {"CALIB": 4},
    "main":      {"PLAYPASS": 12, "SELFPRED": 8, "AUDITOR": 8},
}
PREFLIGHT_ARRAY = "F01_oddone_m3"      # first VIS-FRAME-41 array in frame order; fixed a priori
PILOT_ARRAYS = ["F01_oddone_m3", "F02_size_m3"]   # first two in frame order; excluded from analysis


def latin_squares(table, k, rng):
    """k Latin squares of 4 perms each; returns perm ids. Each shape in each slot k times."""
    inv = {tuple(v): pid for pid, v in table.items()}
    out = []
    for _ in range(k):
        base = list(range(4)); rng.shuffle(base)
        sq = [tuple(base[(i + s) % 4] for i in range(4)) for s in range(4)]
        rng.shuffle(sq)
        out += [inv[p] for p in sq]
    return out


def check_balance(table, pids):
    c = [[0] * 4 for _ in range(4)]
    for p in pids:
        for slot, canon in enumerate(table[p]):
            c[canon][slot] += 1
    flat = [x for r in c for x in r]
    assert max(flat) == min(flat), c


def main():
    arrays = [r for r in csv.DictReader(open(os.path.join(SPC, "audits", "visual",
              "recommended_frame_arrays.csv"))) if r["frame_id"] == "VIS-FRAME-41"]
    assert len(arrays) == 41
    ids = [r["array_id"] for r in arrays]
    tables, stim = {}, {}
    for a in ids:
        tables[a] = {int(k): v for k, v in json.load(open(os.path.join(STIM, a, "manifest.json"))).items()}
        stim[a] = {"manifest_sha256": sha256f(os.path.join(STIM, a, "manifest.json")),
                   "perm_png_sha8": {str(p): sha256f(os.path.join(STIM, a, f"perm{p:02d}.png"))[:8]
                                     for p in range(24)}}

    # ---- prompts
    calib = None
    s4 = os.path.join(SC, "study2_4opt_20260830", "code", "s4_common.py")
    # Render STAGE_A_PROMPT without importing s4_common (it loads credentials on import).
    import ast
    env = {}
    for n in ast.parse(open(s4).read()).body:
        if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") in ("BASE", "CHOICE_FORMAT", "STAGE_A_PROMPT"):
            exec(compile(ast.Module([n], []), s4, "exec"), env)
    calib = env["STAGE_A_PROMPT"]
    assert sha8(calib) == "d40ea45d"
    P = {"CALIB|any": calib}
    for focal in ("gpt", "claude"):
        for t in ("PLAYPASS", "SELFPRED", "AUDITOR"):
            P[f"{t}|{focal}"] = PR.build(t, focal)
    assert P["PLAYPASS|gpt"] == P["PLAYPASS|claude"] and P["SELFPRED|gpt"] == P["SELFPRED|claude"]
    # leakage guard
    for k, v in P.items():
        low = v.lower()
        for bad in ("agreement", "high", "low ", "stable", "difficult", "predictab", "%"):
            if bad == "low " and "set to low" in low:
                low = low.replace("set to low", "")
            assert bad not in low, (k, bad)
    # common-structure check: the second-person game block is the calibration's, verbatim
    assert calib.startswith(PR.ROLE_SELF + PR.GAME_SELF)
    prompts = {k: {"text": v, "sha8": sha8(v)} for k, v in P.items()}

    # ---- who answers what
    def answerer(task, focal):
        return PR.OTHER[focal] if task == "AUDITOR" else focal

    # ---- schedules
    sched = []
    for stage, tasks in DESIGN.items():
        arr = [PREFLIGHT_ARRAY] if stage == "preflight" else PILOT_ARRAYS if stage == "pilot" else ids
        for task, n in tasks.items():
            for focal in ("gpt", "claude"):
                for a in arr:
                    rng = random.Random(f"{SEED}|{stage}|{task}|{focal}|{a}")
                    if n == 1:
                        pids = [0]
                    else:
                        pids = latin_squares(tables[a], n // 4, rng)
                        check_balance(tables[a], pids)
                    for rep, pid in enumerate(pids):
                        sched.append(dict(stage=stage, task=task, focal=focal,
                                          answerer=answerer(task, focal), array=a, rep=rep,
                                          perm_id=pid, display_order=tables[a][pid],
                                          prompt_key="CALIB|any" if task == "CALIB" else f"{task}|{focal}"))
    counts = {}
    for j in sched:
        counts.setdefault(j["stage"], {}).setdefault(f"{j['task']}|answerer={j['answerer']}", 0)
        counts[j["stage"]][f"{j['task']}|answerer={j['answerer']}"] += 1

    code = {os.path.basename(p): sha256f(p)[:8] for p in
            [os.path.join(HERE, f) for f in ("prompts.py", "freeze.py", "run.py")] +
            [os.path.join(SPC, "runners", "pc_common.py"), s4] if os.path.exists(p)}

    frozen = dict(
        study="Study 1 frontier minimal collection", frozen_utc="2026-10-07", seed=SEED,
        arrays=ids, stimuli_root=STIM, stimuli=stim, models=MODELS, prompts=prompts,
        design=DESIGN, preflight_array=PREFLIGHT_ARRAY, pilot_arrays=PILOT_ARRAYS,
        n_jobs=len(sched), counts=counts, schedule=sched, code_sha8=code,
        calibration_reuse=dict(
            source=os.path.join(SPC, "runs", "visual_frame", "visual_frame_20260909_204609.csv"),
            source_sha256=sha256f(os.path.join(SPC, "runs", "visual_frame", "visual_frame_20260909_204609.csv")),
            cell_metrics=os.path.join(SPC, "analysis", "out", "stage1_frame", "cell_metrics.csv"),
            cell_metrics_sha256=sha256f(os.path.join(SPC, "analysis", "out", "stage1_frame", "cell_metrics.csv")),
            prompt_sha8="d40ea45d", n_per_array=48, estimand="within_model_match (independent-order dyadic match)",
            expand_rule="anchor drift test p<.01 for a model -> recollect 48/array for that model before main"),
        gates=dict(
            preflight="returned==requested; Opus reply has no thinking block; GPT surface reasoning.effort=low accepted; all 4 prompts parse; stimulus sha matches frame log",
            pilot="parse rate >= .95 per model x task",
            anchor="log-lik of anchor choices under frame distribution (alpha .5) vs 10,000 parametric draws; p<.01 => expand calibration",
            main="hard budget cap"),
        parse_rules=dict(CALIB="CHOICE: [1-4], last match", PLAYPASS="DECISION: PLAY|PASS, last match",
                         SELFPRED="MATCH_PROBABILITY: integer 0-100, last match",
                         AUDITOR="MATCH_PROBABILITY: integer 0-100, last match",
                         failures="never defaulted; parse_ok=0"),
    )
    out = os.path.join(ROOT, "design", "FROZEN.json")
    json.dump(frozen, open(out, "w"), indent=1)
    h = sha256f(out)
    open(out.replace(".json", ".sha256"), "w").write(f"{h}  FROZEN.json\n")

    # ---- legacy (old PLAY/PASS preserved, recorded by hash only; never written to)
    legacy = {}
    for pat in [os.path.join(SC, "study_playpass_gpt", "data", "*.csv"),
                os.path.join(SC, "study_playpass_gpt", "data", "frozen_items.json"),
                os.path.join(STAG, "opus_playpass", "results", "*", "raw_rows.json"),
                os.path.join(STAG, "opus_playpass", "design", "*.json")]:
        for p in sorted(glob.glob(pat)):
            legacy[p] = sha256f(p)
    json.dump({"note": "Old PLAY/PASS assets. Read-only; preserved in place. Not pooled with this study.",
               "files": legacy}, open(os.path.join(ROOT, "design", "LEGACY_MANIFEST.json"), "w"), indent=1)
    print(f"FROZEN.json sha256 {h[:16]}  jobs {len(sched)}")
    for st, c in counts.items():
        print(f"  {st:9s} {sum(c.values()):5d}  {c}")
    for k, v in prompts.items():
        print(f"  prompt {k:18s} {v['sha8']}")
    print(f"legacy files hashed: {len(legacy)}")


if __name__ == "__main__":
    main()
