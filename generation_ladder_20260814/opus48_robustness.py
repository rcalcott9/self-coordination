"""
Prospective robustness extension for Claude Opus 4.8.

QUESTION. Was the -0.103 Stage C estimate mainly a stimulus-specific reversal on `rot`,
or does weak/negative policy-specific coordination sensitivity generalise?

ORIGINAL SAMPLE: the 2 Claude pairs from the 5.4/4.8 replication, preserved untouched. The 3-pair Stage C, its raw data, its
permutation result and the `rot > b_spiral_cw` reversal all stay in the record. `rot` is
never excluded from the historical result; the only exclusion analysis is a clearly
labelled sensitivity check that shows how much that one pair contributes.

INDEPENDENCE. The six stimuli already spent in the original Stage C
(proto, a_chev_ud, rot, b_spiral_cw, d_dens_extreme, s_density) are excluded from the
robustness candidate pool, so the new sample shares no stimulus with the original.

WHAT IS AND IS NOT CHANGED. Nothing in the selector's science changes: E1-E6 thresholds,
held-out validation, ranking, and the non-reuse rule are untouched. Two parameters are
set explicitly and documented:
  PSC_EXCLUDE_STIMULI  restricts the pool (a restriction, never a relaxation)
  PSC_TARGET_PAIRS     how many pairs a SINGLE-model sample draws. The default 3+2=5 was
                       built for a two-model study; a one-model robustness sample needs
                       5-8 from one model. This is an allocation parameter, not a
                       threshold.

THE EXPANSION BATTERY IS NOT TARGETED AT `rot`. It is the same frozen 30-stimulus,
10-cue-family battery already used for GPT-5 and Opus 4.5, generated before any of this
was known. No pointed blobs, rotations or `rot`-like features were added.

Run:  python3 opus48_robustness.py
"""
import csv, glob, json, os, random, statistics as st, subprocess, sys, time

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
from ladder_models import CODE
from run_expansion_select import EXPANSION, merge, saturation_screen, SATURATION_LIMIT

EXP = os.path.join(ROOT, "models", "opus48_expanded")
ORIG = os.path.expanduser("~/Desktop/Coordination/Self_Coordination/"
                          "policy_specific_self_coordination_20260812_1401/"
                          "replication_5_4_4_8")
ROLE = "claude"
USED = ["c_open_cplx", "d_texture", "s_density", "d_dens_extreme"]
TARGET_PAIRS = 8            # frozen before selection; >=5 required to proceed
SEED, PERM = 20260816, 20000


def env():
    e = dict(os.environ)
    e.update(PSC_EXP_DIR=EXP, PSC_CLAUDE_ID="claude-opus-4-8",
             PSC_CLAUDE_NAME="Claude Opus 4.8", PSC_CLAUDE_SURFACE="thinking",
             PSC_CLAUDE_MAX_TOKENS="2000", PSC_GPT_ID="gpt-5.5",
             PSC_GPT_NAME="GPT-5.5", PSC_GPT_SURFACE="reasoning",
             PSC_EXTRA_STIMULI=",".join(EXPANSION))
    return e


def sh(cmd, e, log, label):
    t0 = time.time()
    with open(log, "w") as fh:
        rc = subprocess.run(cmd, cwd=CODE, env=e, stdout=fh,
                            stderr=subprocess.STDOUT).returncode
    print(f"    {label:36} rc={rc}  {time.time()-t0:6.0f}s")
    return rc


def stage_c_trials(dirpath, pairs):
    cs = [x for x in glob.glob(os.path.join(dirpath, "data", "stageC_*.csv"))
          if "DRY" not in x]
    if not cs:
        return []
    rows = [r for r in csv.DictReader(open(max(cs, key=os.path.getmtime)))
            if r["included_in_analysis"] == "True" and r["actor_model"] == ROLE]
    cell = {}
    for r in rows:
        cell.setdefault(r["stimulus"], []).append(r)
    tr = []
    for i, p in enumerate(pairs):
        for sid, hi in ((p["hi"], 1), (p["lo"], 0)):
            for r in cell.get(sid, []):
                tr.append(dict(y=1 if r["participation_decision"] == "ATTEMPT" else 0,
                               hi=hi, safe=int(float(r["safe_payoff"])), pair=i))
    return tr


def perm_test(tr):
    strata = {}
    for t in tr:
        strata.setdefault((t["pair"], t["safe"]), []).append(t)

    def stat(a):
        pp = {}
        for k, ts in strata.items():
            for t, h in zip(ts, a[k]):
                q = pp.setdefault(k[0], [0, 0, 0, 0])
                if h:
                    q[0] += t["y"]; q[1] += 1
                else:
                    q[2] += t["y"]; q[3] += 1
        v = [q[0] / q[1] - q[2] / q[3] for q in pp.values() if q[1] and q[3]]
        return sum(v) / len(v) if v else 0.0

    obs = stat({k: [t["hi"] == 1 for t in ts] for k, ts in strata.items()})
    rng = random.Random(SEED); ge = 0
    for _ in range(PERM):
        a = {}
        for k, ts in strata.items():
            l = [t["hi"] == 1 for t in ts]; rng.shuffle(l); a[k] = l
        if stat(a) >= obs - 1e-12:
            ge += 1
    return obs, (ge + 1) / (PERM + 1)


def summarise(pairs, tr, label):
    gaps = []
    for i in range(len(pairs)):
        h = [t["y"] for t in tr if t["pair"] == i and t["hi"] == 1]
        l = [t["y"] for t in tr if t["pair"] == i and t["hi"] == 0]
        gaps.append(st.fmean(h) - st.fmean(l))
    obs, pval = perm_test(tr)          # NOT `p` - the pair loop below reuses that name
    by = {}
    for s in sorted({t["safe"] for t in tr}):
        h = [t["y"] for t in tr if t["safe"] == s and t["hi"] == 1]
        l = [t["y"] for t in tr if t["safe"] == s and t["hi"] == 0]
        by[s] = round(st.fmean(h) - st.fmean(l), 4)
    print(f"\n  {label}: {len(pairs)} pairs, {len(tr)} trials")
    for i, q in enumerate(pairs):
        print(f"     {q['hi']:16} > {q['lo']:16} gap {gaps[i]:+.3f}")
    print(f"     mean gap {obs:+.4f}   positive {sum(1 for g in gaps if g>0)}/{len(gaps)}"
          f"   permutation p = {pval:.5f}")
    print(f"     payoff gaps {by}")
    return dict(label=label, n_pairs=len(pairs), n_trials=len(tr), mean_gap=round(obs, 4),
                n_positive=sum(1 for g in gaps if g > 0), perm_p=round(pval, 5),
                payoff_gaps=by, gaps=[round(g, 4) for g in gaps],
                pairs=[f"{q['hi']} > {q['lo']}" for q in pairs])


def read_pairs(path):
    return [{**p, "hi": p["stimulus_high"], "lo": p["stimulus_low"]}
            for p in csv.DictReader(open(path))]


def main():
    e = env()
    L = lambda n: os.path.join(ROOT, "run_logs", f"opus48_rob_{n}.log")
    out = {}

    print("=== Opus 4.8 robustness: select NEW pairs from the 45-stimulus universe ===")
    merge(EXP, "stageA", "orig15_stageA_*.csv", "stageA_*.csv")
    # Stage B was re-run on ALL 45 stimuli in this tree, so there is nothing to merge
    # for those arms - the single fresh file already covers the whole universe.
    if sh([sys.executable, "analyze_stage_ab.py"], e, L("analyze"), "analyze A+B") != 0:
        return _save({"stopped_at": "analyze"})

    e2 = dict(e, PSC_EXCLUDE_STIMULI=",".join(USED),
              PSC_TARGET_PAIRS=str(TARGET_PAIRS))
    sh([sys.executable, "select_pairs_replication.py"], e2, L("select"),
       f"frozen selector ({len(USED)} used stimuli excluded)")
    apf = os.path.join(EXP, "pairs", "approved_pairs.csv")
    new_pairs = read_pairs(apf) if os.path.exists(apf) else []
    out["n_new_pairs"] = len(new_pairs)
    print(f"\n  {len(new_pairs)} NEW pairs selected")
    for p in new_pairs:
        print(f"     {p['hi']:16} > {p['lo']:16}  holdout {float(p['delta_true_holdout']):+.3f}"
              f"  sal {float(p['delta_salience_holdout']):+.3f}"
              f"  aud {float(p['delta_auditor_holdout']):+.3f}")
    if len(new_pairs) < 5:
        print("  STOP: fewer than 5 new admissible pairs.")
        return _save({**out, "stopped_at": "insufficient_new_pairs"})

    orig_ids = [r for r in csv.DictReader(open(os.path.join(ORIG, "matched_pairs.csv")))
                if str(r.get("approved", "")).lower() == "true"
                and r["focal_model"] == "claude"]
    overlap = {p["hi"] for p in new_pairs} | {p["lo"] for p in new_pairs}
    assert not (overlap & set(USED)), "new sample must not reuse original stimuli"
    print(f"  independence check: no stimulus shared with the original "
          f"{len(orig_ids)}-pair set  OK")

    # mark approved for the Stage C runner
    mp = os.path.join(EXP, "matched_pairs.csv")
    rows = list(csv.DictReader(open(mp)))
    ids = {p["pair_id"] for p in new_pairs}
    f = list(rows[0]) + ([] if "approved" in rows[0] else ["approved"])
    for r in rows:
        r["approved"] = "True" if r["pair_id"] in ids else "False"
    with open(mp, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=f, restval=""); w.writeheader(); w.writerows(rows)

    stim = sorted(overlap)
    sat, rate = saturation_screen(e, ROLE, EXP, stim, L("payoff_screen"))
    out["screen_attempt_at_safe9"] = rate
    print(f"\n  payoff screen: ATTEMPT at SAFE=9 = {rate}  (limit {SATURATION_LIMIT})")
    if sat is None or sat:
        print("  STOP: robustness sample Stage-C-uninformative (payoff saturation).")
        return _save({**out, "stopped_at": "payoff_saturation"})

    sh([sys.executable, "stage_c_betting.py", "--n", "30", "--models", ROLE], e,
       L("stageC"), "Stage C (new pairs only)")

    new_tr = stage_c_trials(EXP, new_pairs)
    out["new_sample"] = summarise(new_pairs, new_tr, "NEW prospective sample (PRIMARY)")

    orig_pairs = [p for p in (
        {**r, "hi": r["stimulus_high"], "lo": r["stimulus_low"]}
        for r in csv.DictReader(open(os.path.join(ORIG, "matched_pairs.csv"))))
        if str(p.get("approved", "")).lower() == "true" and p["focal_model"] == "claude"]
    orig_tr = stage_c_trials(ORIG, orig_pairs)
    out["original_sample"] = summarise(orig_pairs, orig_tr, f"ORIGINAL {len(orig_pairs)}-pair sample")

    comb_pairs = orig_pairs + new_pairs
    comb_tr = orig_tr + [dict(t, pair=t["pair"] + len(orig_pairs)) for t in new_tr]
    out["combined"] = summarise(comb_pairs, comb_tr, "COMBINED (descriptive)")

    keep = list(range(len(comb_pairs)))   # no rot pair in the Opus 4.8 record
    cp = [comb_pairs[i] for i in keep]
    remap = {old: new for new, old in enumerate(keep)}
    ct = [dict(t, pair=remap[t["pair"]]) for t in comb_tr if t["pair"] in remap]
    out["combined_excluding_rot"] = summarise(
        cp, ct, "COMBINED excluding rot>b_spiral_cw (SENSITIVITY, not a justification)")

    _save(out)
    return out


def _save(out):
    os.makedirs(os.path.join(ROOT, "analysis"), exist_ok=True)
    p = os.path.join(ROOT, "analysis", "opus48_robustness.json")
    json.dump(out, open(p, "w"), indent=2, default=str)
    print(f"\n-> {p}")
    return out


if __name__ == "__main__":
    main()
