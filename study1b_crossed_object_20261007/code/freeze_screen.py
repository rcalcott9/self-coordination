"""Phase A freeze: screening reference choices on a candidate array list. No API calls.

  python code/freeze_screen.py [--candidates FILE] [--n 24] [--exclude-frame41] [--root DIR]

FILE has one array id per line; default = every array in the existing 4-option battery.
The prompt is the calibration prompt d40ea45d; settings are the frame configuration.
"""
import argparse, csv, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C                                                     # noqa: E402

SEED = "S1B-SCREEN-20261007"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidates"); ap.add_argument("--n", type=int, default=24)
    ap.add_argument("--exclude-frame41", action="store_true"); ap.add_argument("--root", default=C.STUDY)
    a = ap.parse_args()
    arrays = ([l.strip() for l in open(a.candidates) if l.strip()] if a.candidates else C.all_candidate_arrays())
    if a.exclude_frame41:
        f41 = {r["array_id"] for r in csv.DictReader(open(os.path.join(C.SPC, "audits", "visual",
               "recommended_frame_arrays.csv"))) if r["frame_id"] == "VIS-FRAME-41"}
        arrays = [x for x in arrays if x not in f41]
    for x in arrays:
        assert os.path.isdir(os.path.join(C.STIM, x)), x
    prompt = C.calib_prompt()
    sched = []
    for m in C.MODELS:
        for x in arrays:
            t = C.perm_table(x)
            for rep, pid in enumerate(C.latin_squares(t, a.n, f"{SEED}|{m}|{x}")):
                sched.append(dict(phase="screen", task="REF", answerer=m, target=m, array=x, rep=rep,
                                  perm_id=pid, display_order=t[pid], prompt_key="REF"))
    frozen = dict(study="Study 1b crossed object-level prediction", phase="screen", seed=SEED,
                  candidates=arrays, candidates_source=a.candidates or "all 4-option battery arrays",
                  n_per_array=a.n, models=C.MODELS, stimuli_root=C.STIM,
                  stimuli={x: C.stim_hashes(x) for x in arrays},
                  prompts={"REF": {"text": prompt, "sha8": C.sha8(prompt)}},
                  schedule=sched, n_jobs=len(sched),
                  # screen depends only on these files; prompts/select/freeze_main may still change
                  code_sha8={k: v for k, v in C.code_sha8().items()
                             if k in ('common.py', 'freeze_screen.py', 'run.py', 'pc_common.py')},
                  note="Screening draws are used ONLY for selection (Phase B). Measured targets come "
                       "from fresh held-out draws in Phase C.")
    os.makedirs(os.path.join(a.root, "design"), exist_ok=True)
    h = C.write_frozen(os.path.join(a.root, "design", "FROZEN_SCREEN.json"), frozen)
    print(f"FROZEN_SCREEN sha256 {h[:16]}  arrays {len(arrays)}  jobs {len(sched)}")


if __name__ == "__main__":
    main()
