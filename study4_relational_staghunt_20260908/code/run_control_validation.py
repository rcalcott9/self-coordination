"""STAGE 1 - independent validation of the shared-policy controls. 7 x 2 x 24 = 336 calls.

Ungreened stimuli5, frozen four-option prompt, fresh run directory, no pooling.
Job key carries stage|array|model|perm so a resume can never collapse two cells.
"""
import argparse, csv, json, os, sys
from collections import Counter

S4 = "/Users/calypsocalcott/Desktop/Coordination/Self_Coordination/study2_4opt_20260830/code"
EXP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, S4)
import s4_common as S

S.STIM = os.path.join(EXP, "stimuli5")
LOCK = os.path.join(EXP, "pilot", "CONTROL_VALIDATION_LOCKED.json")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--resume-from", default=None)
    ap.add_argument("--workers", type=int, default=12)
    a = ap.parse_args()

    spec = json.load(open(LOCK))
    assert spec["green_used"] is False
    sids = [c["array_id"] for c in spec["candidates"]]
    assert len(set(sids)) == len(sids) == 7, sids

    jobs = []
    for sid in sids:
        for actor in ("gpt", "claude"):
            for perm_id in range(24):                 # each permutation exactly once
                jobs.append(dict(
                    job_key=f"ctrlval|{sid}|{actor}|p{perm_id:02d}",
                    stage="control_validation", sid=sid, actor=actor,
                    trial=perm_id, perm_id=perm_id))
    assert len(jobs) == 7 * 2 * 24 == 336, len(jobs)
    assert len({j["job_key"] for j in jobs}) == len(jobs), "duplicate job_key"
    for sid in sids:                                   # exact counterbalance per cell
        for actor in ("gpt", "claude"):
            c = Counter(j["perm_id"] for j in jobs if j["sid"] == sid and j["actor"] == actor)
            assert len(c) == 24 and set(c.values()) == {1}, (sid, actor, c)

    print("=== STAGE 1: SHARED-POLICY CONTROL VALIDATION (n=24, ungreened, fresh) ===")
    print(f"arrays  : {len(sids)}   models: gpt, claude   perms/cell: 24 (each once)")
    print(f"gpt     : {S.GPT_ID}\nclaude  : {S.CLAUDE_ID}")
    print(f"prompt  : sha8={S.PROMPT_SHA['stage_a']}")
    print(f"locked  : {open(LOCK+'.sha256').read().strip()[:16]}")
    print(f"run dir : {a.run_dir}\ncalls   : {len(jobs)}"
          f"{'   [DRY RUN]' if a.dry_run else ''}\n", flush=True)

    imgs = {}

    def images_for(job):
        k = (job["sid"], job["perm_id"])
        if k not in imgs:
            imgs[k] = S.b64(os.path.join(S.STIM, job["sid"], f"perm{job['perm_id']:02d}.png"))
        return imgs[k]

    prefix = os.path.join(a.run_dir, "data", "stageA_ctrlval")
    os.makedirs(os.path.dirname(prefix), exist_ok=True)
    prefix, rows = S.run_stage("stageA_ctrlval", jobs, lambda j: S.STAGE_A_PROMPT,
                               images_for, dry_run=a.dry_run, workers=a.workers,
                               out_prefix=prefix, resume_from=a.resume_from)
    if a.dry_run:
        return

    man, out, nfail = {}, [], 0
    for r in rows:
        sid = r["sid"]
        if sid not in man:
            man[sid] = json.load(open(os.path.join(S.STIM, sid, "manifest.json")))
        pos = S.parse_choice(r["raw"]) if r["ok"] else None
        item = man[sid][str(r["perm_id"])][pos] if pos is not None else None
        if item is None:
            nfail += 1
        out.append(dict(job_key=r["job_key"], sid=sid, actor=r["actor"],
                        perm_id=r["perm_id"], api_model=r["api_model"], ok=r["ok"],
                        chosen_position=pos, chosen_item=item, error=r["error"]))
    with open(prefix + "_parsed.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0].keys()))
        w.writeheader(); w.writerows(out)
    print(f"\nrows {len(out)}  transport_fail {sum(1 for r in out if not r['ok'])}"
          f"  parse_fail {nfail}")
    print(f"-> {prefix}_parsed.csv")


if __name__ == "__main__":
    main()
