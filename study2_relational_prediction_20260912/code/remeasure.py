"""Study 2 candidate re-measurement: 13 items x 2 models x n=100 fresh Stage A choices.

Identical configuration to the Stage A ground truth - same STAGE_A_PROMPT (sha8 d40ea45d),
same model ids, same balanced position schedule (each shape in each slot exactly n/4 = 25
times). Purpose is to replace noisy n=24 estimates before the Study 2 item set is frozen.

ISOLATED: writes only inside this study directory. Reads stimuli and s4_common read-only.
Touches no Study 1 / playpass files.
"""
import argparse, csv, json, os, sys, time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S4 = "/Users/calypsocalcott/Desktop/Coordination/Self_Coordination/study2_4opt_20260830/code"
sys.path.insert(0, S4)
import s4_common as S

STIM = "/Users/calypsocalcott/Desktop/Coordination/Self_Coordination/study2_4opt_20260830/stimuli"
N = 100


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=N)
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--resume-from", default=None)
    a = ap.parse_args()

    cands = [r["stimulus_id"] for r in
             csv.DictReader(open(os.path.join(HERE, "data", "candidates_ranked.csv")))
             if float(r["min_stability"]) >= 0.60 and float(r["tvd"]) >= 0.50]
    assert len(cands) == 13, (len(cands), cands)

    sched = S.position_schedule(a.n)          # balanced: each shape in each slot n/4 times
    jobs = []
    for sid in cands:
        for actor in ("gpt", "claude"):
            for trial, perm in enumerate(sched):
                jobs.append(dict(job_key=f"remeas|{sid}|{actor}|t{trial}|p{perm}",
                                 sid=sid, actor=actor, trial=trial, perm_id=perm))
    assert len(jobs) == 13 * 2 * a.n, len(jobs)
    assert len({j["job_key"] for j in jobs}) == len(jobs)

    run = os.path.join(HERE, "results", f"remeasure_{time.strftime('%Y%m%d_%H%M%S')}")
    os.makedirs(os.path.join(run, "data"), exist_ok=True)
    print("=== STUDY 2 CANDIDATE RE-MEASUREMENT ===")
    print(f"items {len(cands)}  models gpt+claude  n={a.n} each")
    print(f"gpt {S.GPT_ID}   claude {S.CLAUDE_ID}   prompt sha8 {S.PROMPT_SHA['stage_a']}")
    print(f"calls {len(jobs)}   run {run}")
    if a.dry_run:
        print("[DRY RUN]"); return

    imgs = {}

    def img(j):
        k = (j["sid"], j["perm_id"])
        if k not in imgs:
            imgs[k] = S.b64(os.path.join(STIM, j["sid"], f"perm{j['perm_id']:02d}.png"))
        return imgs[k]

    prefix = os.path.join(run, "data", "remeasure")
    prefix, rows = S.run_stage("remeasure", jobs, lambda j: S.STAGE_A_PROMPT, img,
                               workers=a.workers, out_prefix=prefix,
                               resume_from=a.resume_from)
    man, out, bad = {}, [], 0
    for r in rows:
        sid = r["sid"]
        if sid not in man:
            man[sid] = json.load(open(os.path.join(STIM, sid, "manifest.json")))
        pos = S.parse_choice(r["raw"]) if r["ok"] else None
        item = man[sid][str(r["perm_id"])][pos] if pos is not None else None
        if item is None:
            bad += 1
        out.append(dict(sid=sid, actor=r["actor"], trial=r["trial"], perm_id=r["perm_id"],
                        chosen_position=pos, chosen_item=item, api_model=r["api_model"],
                        ok=r["ok"]))
    with open(os.path.join(run, "data", "parsed.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
    print(f"\nrows {len(out)}  transport_fail {sum(1 for r in out if not r['ok'])}  "
          f"parse_fail {bad}\n-> {run}")


if __name__ == "__main__":
    main()
