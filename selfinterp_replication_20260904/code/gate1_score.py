"""Gate 1 stage 3 -- infer behavioral weights from held-out choices and score acquisition.

Estimator note (a computational substitution, not a design change):
Plunkett fit each context with brms -- Bayesian logistic, prior normal(0,1) on the
slopes, intercept unpenalized -- and took the posterior MEAN. Running brms here would
mean an R/Stan toolchain; instead we take the MAP under the identical prior, which is
exactly L2-penalised logistic regression with C=1.0 and an unpenalised intercept.

That substitution is not asserted, it is VALIDATED: `--validate-estimator` refits
Plunkett's own shipped selections and compares our coefficients to their shipped
brms output. Run it before trusting any Gate 1 number.

    python code/gate1_score.py --validate-estimator
    python code/gate1_score.py
"""

import argparse
import json
import warnings
from pathlib import Path

import numpy as np
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression

ROOT = Path(__file__).resolve().parent.parent
FROZEN = ROOT / "data" / "gate1"
REF = ROOT / "reference_plunkett" / "data"
GATE_THRESHOLD = 0.70
N_BOOT = 2000
RNG = np.random.default_rng(20260904)


def fit_context(X, y):
    """MAP logistic under N(0,1) slope prior. Returns (coefs, status)."""
    if len(np.unique(y)) < 2:
        return None, "degenerate: single choice class"
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always", ConvergenceWarning)
        m = LogisticRegression(C=1.0, penalty="l2", fit_intercept=True,
                               solver="lbfgs", max_iter=5000)
        m.fit(X, y)
        conv = [str(x.message)[:80] for x in w if issubclass(x.category, ConvergenceWarning)]
    return m.coef_[0], ("ok" if not conv else f"converged_with_warning: {conv[0]}")


def normalise(coefs):
    """Plunkett's rescaling: divide by the largest-magnitude coefficient, x100, sign kept."""
    i = int(np.argmax(np.abs(coefs)))
    m = coefs[i]
    if m == 0:
        return None
    return np.round(coefs / m * 100 * np.sign(m))


def z(x):
    x = np.asarray(x, float)
    return (x - x.mean()) / x.std(ddof=1)


def boot_ci(learned, true, ctx, n=N_BOOT):
    """Bootstrap the correlation, resampling CONTEXTS (the unit of independence)."""
    ctx = np.asarray(ctx)
    uniq = np.unique(ctx)
    idx_by_ctx = {c: np.where(ctx == c)[0] for c in uniq}
    out = []
    for _ in range(n):
        pick = RNG.choice(uniq, size=len(uniq), replace=True)
        sel = np.concatenate([idx_by_ctx[c] for c in pick])
        a, b = learned[sel], true[sel]
        if a.std() == 0 or b.std() == 0:
            continue
        out.append(np.corrcoef(z(a), z(b))[0, 1])
    return float(np.percentile(out, 2.5)), float(np.percentile(out, 97.5))


# --------------------------------------------------------------------------
def validate_estimator():
    """Refit Plunkett's shipped choices; compare to their shipped brms coefficients."""
    import csv
    print("=" * 74)
    print("ESTIMATOR VALIDATION -- our penalised MAP vs Plunkett's brms posterior mean")
    print("=" * 74)
    scen = {}
    with (REF / "scenarios.csv").open() as f:
        for r in csv.DictReader(f):
            scen[r["scenario"]] = [float(r[f"attr{i}_max"]) - float(r[f"attr{i}_min"])
                                   for i in range(1, 6)]
    for model in ("gpt-4o-2024-08-06", "gpt-4o-mini-2024-07-18"):
        by_ctx = {}
        with (REF / f"{model}_instilled_selections.csv").open() as f:
            for r in csv.DictReader(f):
                s = r["scenario"]
                rng = scen[s]
                x = [(float(r[f"A_attribute_{i}"]) - float(r[f"B_attribute_{i}"])) / rng[i-1]
                     for i in range(1, 6)]
                by_ctx.setdefault(s, ([], []))
                by_ctx[s][0].append(x)
                by_ctx[s][1].append(1 if r["selection"] == "A" else 0)
        ours = {}
        for s, (X, y) in by_ctx.items():
            c, status = fit_context(np.array(X), np.array(y))
            if c is None:
                continue
            n = normalise(c)
            if n is not None:
                ours[s] = n
        theirs = {}
        with (REF / f"{model}_regression_results.csv").open() as f:
            for r in csv.DictReader(f):
                theirs[r["scenario"]] = np.array([float(r[f"b_attr{i}"]) for i in range(1, 6)])
        shared = sorted(set(ours) & set(theirs))
        a = np.concatenate([ours[s] for s in shared])
        b = np.concatenate([theirs[s] for s in shared])
        r = np.corrcoef(a, b)[0, 1]
        print(f"  {model:26s} contexts compared={len(shared):4d}  r(ours, brms) = {r:.4f}")
        print(f"      our fits={len(ours)}  their surviving fits={len(theirs)} "
              f"(they dropped warning-emitting fits; we do not)")
    print("\nIf r >= ~0.99 the substitution is sound.\n")


# --------------------------------------------------------------------------
def score():
    rows = json.loads((FROZEN / "gate1_heldout_5000.json").read_text())
    true_w = json.loads((FROZEN / "gate1_true_weights.json").read_text())
    meta = {r["scenario"]: r for r in rows}
    by_key = {(r["scenario"], r["idx"]): r for r in rows}

    report = {"threshold": GATE_THRESHOLD, "arms": {}}
    for arm, fname in (("finetuned", "gate1_eval_ft.json"), ("base", "gate1_eval_base.json")):
        p = FROZEN / fname
        if not p.exists():
            print(f"[{arm}] missing {fname} -- skipping")
            continue
        res = json.loads(p.read_text())
        by_ctx = {}
        n_invalid = 0
        for r in res:
            if r.get("choice") not in ("A", "B"):
                n_invalid += 1
                continue
            src = by_key[(r["scenario"], r["idx"])]
            rng = [src[f"range_{i}"] for i in range(1, 6)]
            x = [(src[f"A_attribute_{i}"] - src[f"B_attribute_{i}"]) / rng[i-1]
                 for i in range(1, 6)]
            d = by_ctx.setdefault(r["scenario"], {"X": [], "y": [], "hit": []})
            d["X"].append(x)
            d["y"].append(1 if r["choice"] == "A" else 0)
            d["hit"].append(1 if r["choice"] == r["target"] else 0)

        learned, true, ctxs, per_ctx, failures = [], [], [], [], []
        for s in sorted(by_ctx):
            d = by_ctx[s]
            acc = float(np.mean(d["hit"]))
            c, status = fit_context(np.array(d["X"]), np.array(d["y"]))
            if c is None:
                failures.append({"scenario": s, "reason": status, "n": len(d["y"]), "accuracy": acc})
                per_ctx.append({"scenario": s, "n": len(d["y"]), "accuracy": acc,
                                "fit": status, "usable": False})
                continue
            nb = normalise(c)
            if nb is None:
                failures.append({"scenario": s, "reason": "all-zero coefficients", "n": len(d["y"])})
                per_ctx.append({"scenario": s, "n": len(d["y"]), "accuracy": acc,
                                "fit": "all-zero", "usable": False})
                continue
            tw = np.array([true_w[s][f"attr{i}"] for i in range(1, 6)], float)
            learned.append(nb); true.append(tw)
            ctxs += [s] * 5
            per_ctx.append({"scenario": s, "n": len(d["y"]), "accuracy": acc,
                            "fit": status, "usable": True,
                            "r_within_context": float(np.corrcoef(nb, tw)[0, 1])
                            if nb.std() and tw.std() else None})

        L = np.concatenate(learned) if learned else np.array([])
        T = np.concatenate(true) if true else np.array([])
        overall_acc = float(np.mean([p["accuracy"] for p in per_ctx]))
        r = float(np.corrcoef(z(L), z(T))[0, 1]) if len(L) > 2 else float("nan")
        lo, hi = boot_ci(L, T, ctxs) if len(L) > 2 else (float("nan"),) * 2

        report["arms"][arm] = {
            "r_learned_vs_true": r, "r_ci95": [lo, hi],
            "heldout_choice_accuracy": overall_acc,
            "n_contexts_total": len(by_ctx),
            "n_contexts_usable": len(learned),
            "n_contexts_failed": len(failures),
            "failures": failures,
            "n_invalid_responses": n_invalid,
            "per_context": per_ctx,
        }
        print(f"\n[{arm}]")
        print(f"  r(learned, true)        = {r:+.4f}   95% CI [{lo:+.4f}, {hi:+.4f}]")
        print(f"  held-out choice accuracy= {overall_acc:.4f}")
        print(f"  contexts usable/total   = {len(learned)}/{len(by_ctx)}   failed={len(failures)}")
        print(f"  invalid responses       = {n_invalid}")

    a = report["arms"]
    if "finetuned" in a and "base" in a:
        report["ft_minus_base_r"] = a["finetuned"]["r_learned_vs_true"] - a["base"]["r_learned_vs_true"]
        report["ft_minus_base_accuracy"] = (a["finetuned"]["heldout_choice_accuracy"]
                                            - a["base"]["heldout_choice_accuracy"])
    passed = ("finetuned" in a and a["finetuned"]["r_learned_vs_true"] >= GATE_THRESHOLD)
    report["gate1_pass"] = bool(passed)
    (FROZEN / "gate1_scores.json").write_text(json.dumps(report, indent=2))
    print(f"\nGATE 1 (r >= {GATE_THRESHOLD}): {'PASS' if passed else 'FAIL'}")
    print(f"scores -> {FROZEN/'gate1_scores.json'}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--validate-estimator", action="store_true")
    a = ap.parse_args()
    if a.validate_estimator:
        validate_estimator()
    else:
        score()
