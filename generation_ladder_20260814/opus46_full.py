"""
Opus 4.6 - first full-battery run.

WHY. Opus 4.6 failed the competence gate on a 2-stimulus, n=24 screen: no transferable
convention on `proto` or `s_contrast`, and zero payoff response (ATTEMPT 1.00 at both
SAFE=3 and SAFE=9). Mapping fidelity was 1.00, so it understood the task.

That base was too thin to support "no convention anywhere". Opus 4.5 also position-locked
on `proto` yet had a convention on `s_contrast` and later yielded 5 admissible pairs on
the expanded battery; Opus 4.7 scored 1.000 on both controls. And the gate's small Stage C
screen demonstrably mis-called Opus 4.5 (+0.125 there, 0.000 on its real selected stimuli).

So this run gives 4.6 the same test every other rung got: Stage A n=60 on all 45 stimuli,
Stage B both arms, the unchanged frozen selector, and the frozen payoff-saturation screen
on the ACTUAL selected stimuli as the real Gate D.

THE ORIGINAL GATE VERDICT IS NOT OVERTURNED. It stands as a record of what a 48-trial
screen showed. This run measures the same model properly; if the payoff screen fails
again, that is now a well-powered finding rather than an underpowered one.

No threshold, ranking rule or payoff grid is changed. There is no prior Stage C for this
model, so nothing is excluded and there is no original sample to compare against.
"""
import csv, glob, json, os, random, statistics as st, subprocess, sys, time

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
from ladder_models import CODE
from run_expansion_select import EXPANSION, merge, saturation_screen, SATURATION_LIMIT

EXP = os.path.join(ROOT, "models", "opus46_expanded")
ORIG = None        # no earlier Stage C sample exists for Opus 4.6
ROLE = "claude"
USED = []          # no prior Stage C for this model - nothing is spent
TARGET_PAIRS = 8            # frozen before selection; >=5 required to proceed
SEED, PERM = 20260816, 20000


def env():
    e = dict(os.environ)
    e.update(PSC_EXP_DIR=EXP, PSC_CLAUDE_ID="claude-opus-4-6",
             PSC_CLAUDE_NAME="Claude Opus 4.6", PSC_CLAUDE_SURFACE="thinking",
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
    L = lambda n: os.path.join(ROOT, "run_logs", f"opus46_rob_{n}.log")
    out = {}

    print("=== Opus 4.6 robustness: select NEW pairs from the 45-stimulus universe ===")
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

    orig_ids = []
    overlap = {p["hi"] for p in new_pairs} | {p["lo"] for p in new_pairs}
    assert not (overlap & set(USED)), "new sample must not reuse original stimuli"
    print("  no prior Stage C for this model - full 45-stimulus pool used")

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

    _save(out)
    return out


def _save(out):
    os.makedirs(os.path.join(ROOT, "analysis"), exist_ok=True)
    p = os.path.join(ROOT, "analysis", "opus46_robustness.json")
    json.dump(out, open(p, "w"), indent=2, default=str)
    print(f"\n-> {p}")
    return out


if __name__ == "__main__":
    main()
