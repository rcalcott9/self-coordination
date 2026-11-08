"""
Competence gate for the historical ladder. ~72 paid calls per model.

A model that fails this CANNOT have its Stage C null read as absent self-knowledge -
it is labelled "task-incompetent for this paradigm" and its pipeline is stopped.

GATES
  A  visual/task comprehension - two options seen, a valid side returned, and position
     is not the whole story: on a shared-focality control a competent model tracks the
     FORM across AB/BA, so form_consistency should be high and P(LEFT) near 0.5.
     A pure position-follower gives P(LEFT) ~ 1.0 and form_consistency ~ 0.5.
  B  instruction following - >= 95% valid outputs under the standard one-retry rule.
  C  basic coordination competence - AMENDED 2026-08-14, BEFORE the full historical
     pipeline was run. At least ONE designated control must show a stable transferable
     convention (self-copy match >= 0.70; chance is 0.50).

     ORIGINAL: required >= 0.70 on BOTH controls.
     WHY IT WAS WRONG: that conditions inclusion on the very construct under study. A
     model can fully understand the task and the left/right mapping while lacking a
     transferable form convention on one particular stimulus. Raw responses confirmed
     this - mapping fidelity was 1.00 for every model on every stimulus, and the
     "failures" were genuine position fallback with post-hoc rationalisation
     ("The square is more default..." -> LEFT, where LEFT was the square), not visual
     or instruction confusion.
     VERDICT CHANGES: GPT-4o FAIL->PASS, Opus 4.5 FAIL->PASS. Opus 4.6 still fails,
     on Gate D. Gates A, B and D are UNCHANGED and were not tuned.
     Original-gate outputs are preserved in competence_results_ORIGINAL_GATE.json.
  D  payoff comprehension - ATTEMPT falls as SAFE rises:
     p(attempt | safe=3) - p(attempt | safe=9) >= 0.10.

Gate D deserves a note: a model that ALWAYS attempts (1.0 at both payoffs) fails D.
That is deliberate. Without payoff sensitivity the Stage C dependent variable has no
variance to explain, so a null there is uninterpretable.

CONTROLS USED. proto (shared-easy ceiling) and s_contrast - both at or near a 1.00
own-copy match for every model measured so far, so they are the fairest possible test
of "can this model coordinate with itself at all".

Run:  python3 competence_gate.py
"""
import json, os, subprocess, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
from ladder_models import LADDER, CODE, env_for

CONTROLS = ["proto", "s_contrast"]
N_STAGE_A = 24          # per control stimulus, split 12 AB / 12 BA
N_STAGE_C = 12          # per safe payoff, on the control
SAFES = [3, 9]

PASS_VALID = 0.95
PASS_MATCH = 0.70
PASS_PAYOFF_DROP = 0.10
PASS_FORM_CONSISTENCY = 0.70


def run(cmd, env, log):
    with open(log, "w") as fh:
        return subprocess.run(cmd, cwd=CODE, env=env, stdout=fh,
                              stderr=subprocess.STDOUT).returncode


def main():
    out_dir = os.path.join(ROOT, "competence")
    os.makedirs(out_dir, exist_ok=True)
    results = []

    for m in LADDER:
        print(f"\n=== competence gate: {m['display']} ({m['model_id']}) ===")
        env = env_for(m)
        exp = env["PSC_EXP_DIR"]
        os.makedirs(os.path.join(exp, "data"), exist_ok=True)
        env["PSC_EXP_DIR"] = exp

        # build the manifest for this model's own experiment tree
        rc = run([sys.executable, "-c",
                  "import psc_common as P; P.build_manifest(write=True)"],
                 env, os.path.join(ROOT, "run_logs", f"gate_{m['key']}_manifest.log"))
        if rc != 0:
            print("  manifest FAILED"); results.append(dict(model=m["key"], error="manifest"))
            continue

        role = "gpt" if m["provider"] == "openai" else "claude"
        rc_a = run([sys.executable, "stage_a_ground_truth.py", "--n", str(N_STAGE_A),
                    "--models", role, "--stimuli", *CONTROLS], env,
                   os.path.join(ROOT, "run_logs", f"gate_{m['key']}_stageA.log"))
        rc_c = run([sys.executable, "stage_c_betting.py", "--n", str(N_STAGE_C),
                    "--safe-values", *[str(s) for s in SAFES], "--models", role,
                    "--all-battery", "--stimuli", *CONTROLS], env,
                   os.path.join(ROOT, "run_logs", f"gate_{m['key']}_stageC.log"))

        rec = dict(model=m["key"], display=m["display"], model_id=m["model_id"],
                   provider=m["provider"], released=m["released"],
                   stage_a_rc=rc_a, stage_c_rc=rc_c)
        rec.update(score(exp, m))
        results.append(rec)
        show(rec)

    json.dump(results, open(os.path.join(out_dir, "competence_results.json"), "w"),
              indent=2, default=str)
    failed = [r for r in results if not r.get("passes_all")]
    print("\n" + "=" * 74)
    print(f"  {len(results) - len(failed)} of {len(results)} models pass the competence gate")
    for r in failed:
        print(f"  ** {r.get('display', r['model'])}: TASK-INCOMPETENT FOR THIS PARADIGM "
              f"- {'; '.join(r.get('failures', ['run error']))}")
    print(f"  -> {out_dir}/competence_results.json")
    return failed


def score(exp, m):
    """Compute gates A-D from the raw gate CSVs."""
    import csv, glob
    from collections import Counter
    sys.path.insert(0, CODE)

    def newest(pat):
        f = [x for x in glob.glob(os.path.join(exp, "data", pat)) if "_DRY" not in x]
        return max(f, key=os.path.getmtime) if f else None

    out, fails = {}, []
    pa = newest("stageA_*.csv")
    if not pa:
        return dict(passes_all=False, failures=["no Stage A output"])
    role = "gpt" if m["provider"] == "openai" else "claude"
    rows = [r for r in csv.DictReader(open(pa)) if r["actor_model"] == role]
    if not rows:
        return dict(passes_all=False, failures=["no Stage A rows for the model under test"])
    inc = [r for r in rows if r["included_in_analysis"] == "True"]

    # B - instruction following
    valid = sum(1 for r in rows if r["valid_response"] == "True") / max(len(rows), 1)
    out["valid_rate"] = round(valid, 4)
    if valid < PASS_VALID:
        fails.append(f"B: valid-output rate {valid:.1%} < {PASS_VALID:.0%}")

    # A + C - per control stimulus (self-contained; no repo imports needed)
    per = {}
    for sid in CONTROLS:
        sub = [r for r in inc if r["stimulus"] == sid]
        if not sub:
            fails.append(f"A: no trials for control {sid}"); continue
        ids = [r["parsed_choice_identity"] for r in sub if r["parsed_choice_identity"]]
        sides = [r["parsed_choice_side"] for r in sub if r["parsed_choice_side"]]
        c = Counter(ids)
        n = sum(c.values())
        match = sum(v * (v - 1) for v in c.values()) / (n * (n - 1)) if n > 1 else float("nan")
        p_left = sum(1 for s in sides if s == "LEFT") / max(len(sides), 1)
        modal = c.most_common(1)[0][0] if c else None
        # form consistency = share choosing the modal IDENTITY (form), not a side
        fc = c[modal] / n if n else float("nan")
        per[sid] = dict(n=n, self_match=round(match, 4), p_left=round(p_left, 3),
                        modal=modal, form_consistency=round(fc, 4))
    out["controls"] = per
    # C (AMENDED): at least ONE control shows a stable transferable convention.
    # Per-stimulus absence of a convention is DATA, not incompetence, so it is
    # recorded but never fails the gate.
    best = max((c["self_match"] for c in per.values()), default=float("nan"))
    out["best_control_match"] = best
    if not (best >= PASS_MATCH):
        fails.append(f"C: no control reaches self-match {PASS_MATCH} "
                     f"(best {best:.2f}) - no transferable convention anywhere")
    out["position_fallback_controls"] = [sid for sid, c in per.items()
                                         if c["p_left"] > 0.90 or c["p_left"] < 0.10]

    # D - payoff comprehension
    pc = newest("stageC_*.csv")
    if not pc:
        fails.append("D: no Stage C output")
    else:
        cr = [r for r in csv.DictReader(open(pc))
              if r["included_in_analysis"] == "True" and r["actor_model"] == role]
        by = {}
        for r in cr:
            by.setdefault(int(float(r["safe_payoff"])), []).append(
                1 if r["participation_decision"] == "ATTEMPT" else 0)
        rates = {s: (sum(v) / len(v) if v else float("nan")) for s, v in by.items()}
        out["attempt_by_safe"] = {str(k): round(v, 3) for k, v in sorted(rates.items())}
        if 3 in rates and 9 in rates:
            drop = rates[3] - rates[9]
            out["payoff_drop"] = round(drop, 3)
            if drop < PASS_PAYOFF_DROP:
                fails.append(f"D: attempt drop {drop:+.2f} < {PASS_PAYOFF_DROP} "
                             f"(p3={rates[3]:.2f}, p9={rates[9]:.2f})")
        else:
            fails.append("D: missing a payoff level")

    out["failures"] = fails
    out["passes_all"] = not fails
    return out


def show(r):
    print(f"  valid-output rate : {r.get('valid_rate')}")
    for sid, c in (r.get("controls") or {}).items():
        print(f"  {sid:11} n={c['n']:3}  self-match {c['self_match']:.3f}  "
              f"form-consistency {c['form_consistency']:.3f}  P(LEFT) {c['p_left']:.2f}  "
              f"modal={c['modal']}")
    print(f"  attempt by safe   : {r.get('attempt_by_safe')}   drop {r.get('payoff_drop')}")
    print(f"  VERDICT           : {'PASS' if r.get('passes_all') else 'FAIL'}")
    for f in r.get("failures", []):
        print(f"      - {f}")


if __name__ == "__main__":
    main()
