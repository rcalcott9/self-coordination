"""Study 2 runner — relational prediction. ISOLATED: writes only into this study directory.

Reads Stage A data and the shared stimuli READ-ONLY. Never touches study_playpass_* or any
other study's outputs. Refuses to start unless the frozen item set exists.
"""
import argparse, csv, json, os, sys, time
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S4 = "/Users/calypsocalcott/Desktop/Coordination/Self_Coordination/study2_4opt_20260830/code"
sys.path.insert(0, S4); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import s4_common as S
import prompts as PR

STIM = "/Users/calypsocalcott/Desktop/Coordination/Self_Coordination/study2_4opt_20260830/stimuli"
N_REP = 10
CONDS = ("COPY", "DIFFERENT")
FOCALS = ("gpt", "claude")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--frozen", default=os.path.join(HERE, "data", "frozen_items.json"))
    ap.add_argument("--reps", type=int, default=N_REP)
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    assert os.path.exists(a.frozen), (
        f"frozen item set not found at {a.frozen} - freeze the item list before running")
    items = json.load(open(a.frozen))
    run = os.path.join(HERE, "results", f"run_{time.strftime('%Y%m%d_%H%M%S')}")
    os.makedirs(os.path.join(run, "raw"), exist_ok=True)
    assert not os.path.exists(os.path.join(run, "raw", "study2.jsonl"))

    jobs = []
    for it in items:
        sid = it["stimulus_id"]
        man = json.load(open(os.path.join(STIM, sid, "manifest.json")))
        for focal in FOCALS:
            for cond in CONDS:
                for rep in range(a.reps):
                    perm = rep % 24                       # rotate through permutations
                    # s4_common.run_stage dispatches the API client on job["actor"], so the
                    # focal model must be carried under that key as well as "focal".
                    jobs.append(dict(stimulus_id=sid, sid=sid, focal=focal, actor=focal,
                                     condition=cond, rep=rep, perm_id=perm,
                                     perm=man[str(perm)],
                                     job_key=f"s2|{sid}|{focal}|{cond}|r{rep}|p{perm}"))
    assert len({j["job_key"] for j in jobs}) == len(jobs)
    print(f"=== STUDY 2: relational prediction ===")
    print(f"items {len(items)}  focal {len(FOCALS)}  conditions {len(CONDS)}  reps {a.reps}")
    print(f"total calls {len(jobs)}")
    print(f"run dir {run}")
    if a.dry_run:
        j = jobs[0]
        print("\n--- example prompt ---\n")
        print(PR.build(j["focal"], j["condition"]))
        return

    imgs = {}

    def img(j):
        k = (j["sid"], j["perm_id"])
        if k not in imgs:
            imgs[k] = S.b64(os.path.join(STIM, j["sid"], f"perm{j['perm_id']:02d}.png"))
        return imgs[k]

    prefix = os.path.join(run, "raw", "study2")
    prefix, rows = S.run_stage("study2", jobs,
                               lambda j: PR.build(j["focal"], j["condition"]),
                               img, workers=a.workers, out_prefix=prefix)
    import re
    RE = re.compile(r"^\s*([ABCD])\s*:\s*(\d{1,3})", re.M)
    out, bad = [], 0
    for r in rows:
        m = dict(RE.findall(r["raw"] or ""))
        if len(m) != 4:
            bad += 1; continue
        v = [float(m[k]) for k in "ABCD"]
        if not (98 <= sum(v) <= 102):
            bad += 1; continue
        p = [x / sum(v) for x in v]
        # map displayed slots -> canonical shape indices
        canon = [0.0] * 4
        for slot, item in enumerate(r["perm"]):
            canon[item] = p[slot]
        out.append(dict(stimulus_id=r["stimulus_id"], focal=r["focal"],
                        condition=r["condition"], rep=r["rep"], perm_id=r["perm_id"],
                        p_slots=p, p_canonical=canon, api_model=r["api_model"], raw=r["raw"]))
    with open(os.path.join(run, "raw", "parsed.jsonl"), "w") as f:
        for r in out:
            f.write(json.dumps(r) + "\n")
    print(f"\nparsed {len(out)}/{len(rows)}  unparseable {bad}\n-> {run}")


if __name__ == "__main__":
    main()
