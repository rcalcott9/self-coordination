"""Phase C freeze: build FROZEN_MAIN.json from the frozen SELECTION.json. No API calls.

  python code/freeze_main.py [--root DIR] [--n-target 48] [--n-pred 8]

(i)  TARGET reference draws: fresh, held-out (never used for selection), both models, every
     selected array, n_target each, balanced Latin squares, prompt d40ea45d.
(ii) CROSSED predictions: predictor in {gpt, claude} x target in {gpt, claude}, separate calls,
     matched wording from prompts.build_predict, n_pred each, balanced orderings of the
     PREDICTOR's image.
"""
import argparse, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C                                                     # noqa: E402
import prompts as PR                                                   # noqa: E402

SEED = "S1B-MAIN-20261007"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=C.STUDY)
    ap.add_argument("--n-target", type=int, default=48); ap.add_argument("--n-pred", type=int, default=8)
    a = ap.parse_args()
    sel_path = os.path.join(a.root, "design", "SELECTION.json")
    SEL, sel_sha8 = C.load_frozen(sel_path)
    sel_sha256 = C.sha256f(sel_path)
    arrays = SEL["selected_flat"]
    strat = {x: s for s, v in SEL["selected"].items() for x in v}
    # parse-pilot / preflight arrays: 2 screened, NON-selected arrays, chosen by seeded hash (Amendment 1, item 8)
    import hashlib as _h
    FS, _ = C.load_frozen(os.path.join(a.root, "design", "FROZEN_SCREEN.json"))
    pool = sorted([x for x in FS["candidates"] if x not in arrays],
                  key=lambda x: _h.sha256(f"{SEED}|PILOT|{x}".encode()).hexdigest())
    pilot_arrays = pool[:2]
    ref = C.calib_prompt()
    prompts = {"REF": {"text": ref, "sha8": C.sha8(ref)}}
    for p in C.MODELS:
        for t in C.MODELS:
            txt = PR.build_predict(p, t)
            prompts[f"PRED|p={p}|t={t}"] = {"text": txt, "sha8": C.sha8(txt)}
    sched = []
    for i, x in enumerate(pilot_arrays):
        tab = C.perm_table(x)
        pids = C.latin_squares(tab, 4, f"{SEED}|PILOT|{x}")
        for p in C.MODELS:
            for t in C.MODELS:
                for rep, pid in enumerate(pids):
                    sched.append(dict(phase="main", stage="pilot", task="PRED", answerer=p, target=t, array=x,
                                      stratum="PILOT", rep=rep, perm_id=pid, display_order=tab[pid],
                                      prompt_key=f"PRED|p={p}|t={t}"))
                    if i == 0 and rep == 0:
                        sched.append(dict(sched[-1], stage="preflight"))
        if i == 0:
            for m in C.MODELS:
                sched.append(dict(phase="main", stage="preflight", task="REF", answerer=m, target=m, array=x,
                                  stratum="PILOT", rep=0, perm_id=pids[0], display_order=tab[pids[0]], prompt_key="REF"))
    for x in arrays:
        tab = C.perm_table(x)
        for m in C.MODELS:
            for rep, pid in enumerate(C.latin_squares(tab, a.n_target, f"{SEED}|REF|{m}|{x}")):
                sched.append(dict(phase="main", stage="main", task="REF", answerer=m, target=m, array=x, stratum=strat[x],
                                  rep=rep, perm_id=pid, display_order=tab[pid], prompt_key="REF"))
        for p in C.MODELS:
            for t in C.MODELS:
                for rep, pid in enumerate(C.latin_squares(tab, a.n_pred, f"{SEED}|PRED|{x}")):  # identical orderings in all 4 predictor x target cells
                    sched.append(dict(phase="main", stage="main", task="PRED", answerer=p, target=t, array=x, stratum=strat[x],
                                      rep=rep, perm_id=pid, display_order=tab[pid], prompt_key=f"PRED|p={p}|t={t}"))
    frozen = dict(study="Study 1b crossed object-level prediction", phase="main", seed=SEED,
                  selection_sha256=sel_sha256, selection_sha8=sel_sha8, selection_self_test=SEL["self_test"],
                  prompts_placeholder=getattr(PR, "PLACEHOLDER", False),
                  arrays=arrays, strata=SEL["selected"], n_target=a.n_target, n_pred=a.n_pred,
                  models=C.MODELS, stimuli_root=C.STIM, stimuli={x: C.stim_hashes(x) for x in arrays + pilot_arrays}, pilot_arrays=pilot_arrays,
                  prompts=prompts, schedule=sched, n_jobs=len(sched), code_sha8=C.code_sha8(),
                  parse_rules=dict(REF="CHOICE: [1-4], last match",
                                   PRED="A-D numbers, last per letter, all four, sum 95-105, renormalised, mapped to canonical; else parse_ok=0"),
                  primary_test=("AMENDMENT_1: primary sample = selected S1+S2_G+S2_O arrays; outcome = pooled self-minus-cross "
                                "Brier advantage D_j = 0.5*[(B_O->G + B_G->O) - (B_G->G + B_O->O)] scored on held-out REF draws; "
                                "two-sided array sign-flip, p=(k+1)/(B+1) with B=10000 simulated flips; array bootstrap CI. "
                                "Target-specific advantages reported (Holm over 2). S3 and continuous TVD moderation secondary. "
                                "Study 1 matching-probability results kept separate, never pooled."),
                  amendment_sha256=C.sha256f(os.path.join(a.root, "design", "final", "AMENDMENT_1.md")) if os.path.exists(os.path.join(a.root, "design", "final", "AMENDMENT_1.md")) else None)
    h = C.write_frozen(os.path.join(a.root, "design", "FROZEN_MAIN.json"), frozen)
    print(f"FROZEN_MAIN sha256 {h[:16]}  selection {sel_sha8}  arrays {len(arrays)}  jobs {len(sched)}"
          + ("  [PLACEHOLDER PROMPTS]" if frozen["prompts_placeholder"] else ""))


if __name__ == "__main__":
    main()
