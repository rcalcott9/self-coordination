"""Freeze the high-reasoning Study 1a + 1b replication. No API calls.

Counts per model x array (as instructed):
  1a (41 VIS-FRAME arrays): 48 fresh REF choices, 12 PLAYPASS, 8 SELFPRED, 8 reciprocal AUDITOR
  1b (20 previously selected arrays, selection NOT redone): 8 PRED per predictor x target cell, 48 fresh REF
  REF draws are shared wherever 1a and 1b use the same array (same prompt d40ea45d, same settings):
  one 48-draw set per model x array serves both studies.

Dispatch priority (frozen; matters only if the $150 cap binds):
  block A  1b primary arrays (10 divergent: S1, S2_G, S2_O) - REF + PRED
  block B  1a arrays (41), seeded order, array-major - REF (if not already in A) + PLAYPASS/SELFPRED/AUDITOR
  block C  1b S3 controls (10) - REF (if not already in A/B) + PRED
"""
import csv, json, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hi_common as H                                                   # noqa: E402

SEED = "S1HI-20261009"
N_REF, N_PP, N_SP, N_AUD, N_PRED = 48, 12, 8, 8, 8
CAP_USD = 150.0
CODE = ["hi_common.py", "freeze.py", "run.py", "analyze_1a.py", "analyze_1b.py", "compare.py", "glmm.R"]


def main():
    F1A = json.load(open(os.path.join(H.S1A, "design", "FROZEN.json")))
    F1B = json.load(open(os.path.join(H.S1B, "design", "FROZEN_MAIN.json")))
    SEL = json.load(open(os.path.join(H.S1B, "design", "SELECTION.json")))
    A1 = F1A["arrays"]; assert len(A1) == 41
    B1 = F1B["arrays"]; assert len(B1) == 20 and B1 == SEL["selected_flat"]
    strat = {x: s for s, v in SEL["selected"].items() for x in v}
    prim = [x for x in B1 if strat[x] in ("S1", "S2_G", "S2_O")]; s3 = [x for x in B1 if strat[x] == "S3"]
    assert len(prim) == 10 and len(s3) == 10
    pilot_1a = F1A["pilot_arrays"]; pilot_1b = F1B["pilot_arrays"]; pre_1a = F1A["preflight_array"]
    prompts, diff = H.build_prompts()
    P = {k: {"text": v, "sha8": H.sha8(v)} for k, v in prompts.items()}
    assert P["REF"]["sha8"] == "d40ea45d"
    allarr = sorted(set(A1) | set(B1) | set(pilot_1a) | set(pilot_1b))
    tables = {x: H.C.perm_table(x) for x in allarr}
    other = {"gpt": "claude", "claude": "gpt"}

    def ls(x, n, tag):
        return H.C.latin_squares(tables[x], n, f"{SEED}|{tag}|{x}")

    def job(stage, block, task, answerer, focal, x, rep, pid, key, studies):
        return dict(stage=stage, block=block, task=task, answerer=answerer, focal=focal, array=x, rep=rep,
                    perm_id=pid, display_order=tables[x][pid], prompt_key=key, studies=studies,
                    job_id=f"{stage}|{task}|{answerer}|{focal}|{x}|{rep}")

    sched = []
    # ---- preflight: one call per (task, answerer) incl. every PRED cell; first perm of a 4-square
    pf = ls(pre_1a, 4, "PRE")[0]; pfb = ls(pilot_1b[0], 4, "PRE")[0]
    for m in ("gpt", "claude"):
        sched.append(job("preflight", "PRE", "REF", m, m, pre_1a, 0, pf, "REF", "1a,1b"))
        sched.append(job("preflight", "PRE", "PLAYPASS", m, m, pre_1a, 0, pf, f"PLAYPASS|{m}", "1a"))
        sched.append(job("preflight", "PRE", "SELFPRED", m, m, pre_1a, 0, pf, f"SELFPRED|{m}", "1a"))
        sched.append(job("preflight", "PRE", "AUDITOR", other[m], m, pre_1a, 0, pf, f"AUDITOR|{m}", "1a"))
        for t in ("gpt", "claude"):
            sched.append(job("preflight", "PRE", "PRED", m, t, pilot_1b[0], 0, pfb, f"PRED|p={m}|t={t}", "1b"))
    # ---- pilot (parse gates; excluded from analysis): 1a tasks x4 on the 1a pilot arrays, REF x4 there,
    #      PRED x4 per cell on the 1b pilot arrays
    for x in pilot_1a:
        for m in ("gpt", "claude"):
            for rep, pid in enumerate(ls(x, 4, f"PILOT|REF|{m}")):
                sched.append(job("pilot", "PILOT", "REF", m, m, x, rep, pid, "REF", "1a,1b"))
            for t in ("PLAYPASS", "SELFPRED", "AUDITOR"):
                for rep, pid in enumerate(ls(x, 4, f"PILOT|{t}|{m}")):
                    sched.append(job("pilot", "PILOT", t, other[m] if t == "AUDITOR" else m, m, x, rep, pid,
                                     f"{t}|{m}", "1a"))
    for x in pilot_1b:
        pids = ls(x, 4, "PILOT|PRED")
        for p in ("gpt", "claude"):
            for t in ("gpt", "claude"):
                for rep, pid in enumerate(pids):
                    sched.append(job("pilot", "PILOT", "PRED", p, t, x, rep, pid, f"PRED|p={p}|t={t}", "1b"))
    # ---- main, in frozen priority order
    ref_done = set()

    def ref_jobs(x, block):
        out = []
        if x in ref_done:
            return out
        ref_done.add(x)
        tags = ",".join(s for s, ok in (("1a", x in A1), ("1b", x in B1)) if ok)
        for m in ("gpt", "claude"):
            for rep, pid in enumerate(ls(x, N_REF, f"REF|{m}")):
                out.append(job("main", block, "REF", m, m, x, rep, pid, "REF", tags))
        return out

    def pred_jobs(x, block):
        pids = ls(x, N_PRED, "PRED")                                   # identical orderings in all 4 cells
        return [job("main", block, "PRED", p, t, x, rep, pid, f"PRED|p={p}|t={t}", "1b")
                for p in ("gpt", "claude") for t in ("gpt", "claude") for rep, pid in enumerate(pids)]

    def a_jobs(x, block):
        out = []
        for m in ("gpt", "claude"):
            for t, n in (("PLAYPASS", N_PP), ("SELFPRED", N_SP), ("AUDITOR", N_AUD)):
                for rep, pid in enumerate(ls(x, n, f"{t}|{m}")):
                    out.append(job("main", block, t, other[m] if t == "AUDITOR" else m, m, x, rep, pid, f"{t}|{m}", "1a"))
        return out

    def interleave(js):                                                # rep-major within an array: both models,
        return sorted(js, key=lambda j: (j["rep"], j["task"], j["answerer"], j["focal"]))   # all tasks, alternate

    order_rng = random.Random(f"{SEED}|ORDER")
    for x in prim:
        sched += interleave(ref_jobs(x, "A") + pred_jobs(x, "A"))
    a_order = list(A1); order_rng.shuffle(a_order)
    for x in a_order:
        sched += interleave(ref_jobs(x, "B") + a_jobs(x, "B"))
    for x in s3:
        sched += interleave(ref_jobs(x, "C") + pred_jobs(x, "C"))
    ids = [j["job_id"] for j in sched]; assert len(ids) == len(set(ids))

    # ---- sanity: counts per model x array
    main = [j for j in sched if j["stage"] == "main"]
    for x in A1:
        for m in ("gpt", "claude"):
            c = lambda t, by="focal": sum(1 for j in main if j["array"] == x and j["task"] == t and j[by] == m)
            assert (c("REF"), c("PLAYPASS"), c("SELFPRED"), c("AUDITOR")) == (N_REF, N_PP, N_SP, N_AUD), x
    for x in B1:
        for m in ("gpt", "claude"):
            assert sum(1 for j in main if j["array"] == x and j["task"] == "REF" and j["answerer"] == m) == N_REF
            for t in ("gpt", "claude"):
                assert sum(1 for j in main if j["array"] == x and j["task"] == "PRED" and j["answerer"] == m
                           and j["focal"] == t) == N_PRED
    counts = {}
    for j in sched:
        k = f"{j['stage']}|{j['block']}|{j['task']}|{j['answerer']}"
        counts[k] = counts.get(k, 0) + 1

    stim = {x: H.C.stim_hashes(x) for x in allarr}
    frozen = dict(
        study="Study 1 high-reasoning replication (1a + 1b)", frozen_utc="2026-10-09", seed=SEED,
        models=H.MODELS, cap_usd=CAP_USD, cost_rule="pc_common.cost: pessimistic $5/M in, $30/M out for BOTH providers "
        "(D-016); reasoning/thinking tokens are billed as output and included in out_tokens",
        arrays_1a=A1, arrays_1b=B1, strata_1b=SEL["selected"], primary_1b=prim, s3_1b=s3,
        pilot_arrays_1a=pilot_1a, pilot_arrays_1b=pilot_1b, preflight_array_1a=pre_1a,
        sources=dict(frozen_1a=H.sha256f(os.path.join(H.S1A, "design", "FROZEN.json")),
                     frozen_1b=H.sha256f(os.path.join(H.S1B, "design", "FROZEN_MAIN.json")),
                     selection_1b=H.sha256f(os.path.join(H.S1B, "design", "SELECTION.json"))),
        prompts=P, prompt_change_vs_low=diff, cfg_low=H.CFG_LOW, cfg_high=H.CFG_HIGH,
        counts=dict(per_model_array_1a=dict(REF=N_REF, PLAYPASS=N_PP, SELFPRED=N_SP, AUDITOR=N_AUD),
                    per_cell_1b=dict(PRED=N_PRED, REF=N_REF), by_stage_block_task_answerer=counts,
                    n_main=len(main), n_total=len(sched), ref_arrays=len(ref_done)),
        schedule=sched, stimuli_root=H.C.STIM, stimuli=stim,
        gates=dict(preflight="every preflight call: transport ok, parsed, returned==requested, no max_tokens stop; "
                             "GPT echoed reasoning.effort=high where returned; Opus request accepted with adaptive+high",
                   pilot="parse rate >= .95 per (task, answerer, target) cell (existing 1a and 1b gate)",
                   main=f"global hard cap ${CAP_USD:.0f} incl. preflight, pilot and retries; in-flight reservation"),
        parse_rules=dict(REF="CHOICE: [1-4], last match (pc_common.parse_slot)", PLAYPASS="DECISION: PLAY|PASS, last match",
                         SELFPRED="MATCH_PROBABILITY 0-100, last match", AUDITOR="same as SELFPRED",
                         PRED="A-D, last per letter, all four, sum 95-105, renormalised, mapped to canonical",
                         failures="kept with parse_ok=0 or transport_ok=0; never imputed; transport failures retried on resume"),
        analysis=dict(
            a1="analyze_1a.py: y = unbiased independent-order match from fresh high REF (48/array); P1 D=|A-y|-|S-y| "
               "sign-flip + hierarchical bootstrap; P2 calibration of S and A; S1 PLAY ~ y (GLM + GLMM via glmm.R, "
               "GLMM primary per the 1a audit) and adjusted for A; S2 auditor old HIGH vs LOW; S4 legacy d'/AUC/c. "
               "S3 (old-wording PLAY/PASS) is not repeated: it concerned the low-reasoning legacy data only. "
               "Inclusion: model x array needs >=40/48 REF and >=75% of each task parsed; exclusions reported.",
            b1="analyze_1b.py: primary = pooled self-minus-cross Brier advantage on the ORIGINAL 10 divergent arrays, "
               "scored on fresh high REF; array sign-flip (B=10000 flips) + exact enumeration; bootstrap CI; "
               "target-specific Holm(2); S3 secondary; family-level sensitivity; current divergence (TVD, modal shares) "
               "reported without reselection. Exclusion: any cell <6/8 parsed.",
            compare="compare.py: secondary paired high-minus-low per array, family-cluster bootstrap and family-level "
                    "sign-flip: 1a y, S, A, PLAY rate, D; 1b Delta_j on the 10 primary arrays."),
        code_sha8={f: H.sha256f(os.path.join(H.HERE, f))[:8] for f in CODE if os.path.exists(os.path.join(H.HERE, f))})
    frozen["code_sha8"]["pc_common.py"] = H.sha256f(os.path.join(H.C.SPC, "runners", "pc_common.py"))[:8]
    frozen["code_sha8"]["s1b_common.py"] = H.sha256f(os.path.join(H.S1B, "code", "common.py"))[:8]
    frozen["code_sha8"]["s1a_prompts.py"] = H.sha256f(os.path.join(H.S1A, "code", "prompts.py"))[:8]
    frozen["code_sha8"]["s1b_prompts.py"] = H.sha256f(os.path.join(H.S1B, "code", "prompts.py"))[:8]
    os.makedirs(os.path.join(H.STUDY, "design"), exist_ok=True)
    h = H.C.write_frozen(os.path.join(H.STUDY, "design", "FROZEN.json"), frozen)
    print(f"FROZEN sha256 {h[:16]} | jobs {len(sched)} (main {len(main)}) | REF arrays {len(ref_done)}")
    for k in sorted(counts):
        print(f"  {k:40s} {counts[k]}")
    for k, v in P.items():
        print(f"  prompt {k:24s} {v['sha8']}  {diff.get(k, '')}")


if __name__ == "__main__":
    main()
