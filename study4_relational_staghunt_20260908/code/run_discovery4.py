"""Study 4 four-object DISCOVERY premeasure - 7 arrays x 2 models x 24 permutations.

Uses the frozen four-option coordination prompt UNCHANGED (s4_common.STAGE_A_PROMPT,
sha8 d40ea45d). NOTE: the task brief asked to verify prompt hash 3003ae1b; that is the
BINARY parent of this prompt ("one of the TWO shapes") and cannot address a four-object
array. d40ea45d is its arity-adapted sibling and is the only prompt satisfying "the
existing four-option coordination prompt, unchanged". Deviation recorded in the report.

Nothing under study2_4opt/ is modified: s4_common is imported and its STIM pointer is
redirected in-process to this study's stimuli4/, and all output goes to a new run dir.
"""
import argparse, csv, json, os, sys

S4 = "/Users/calypsocalcott/Desktop/Coordination/Self_Coordination/study2_4opt_20260830/code"
EXP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, S4)
import s4_common as S

S.STIM = os.path.join(EXP, "stimuli4")          # in-process redirect, file untouched


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--resume-from", default=None)
    ap.add_argument("--workers", type=int, default=S.WORKERS)
    a = ap.parse_args()

    battery = list(csv.DictReader(open(os.path.join(S.STIM, "battery4_manifest.csv"))))
    sids = [r["stimulus_id"] for r in battery]
    assert len(sids) == 7, sids

    jobs = []
    for sid in sids:
        for actor in ("gpt", "claude"):
            # all 24 permutations exactly once => every object in every position 6x
            for trial, perm_id in enumerate(range(24)):
                jobs.append(dict(job_key=f"discovery4|{sid}|{actor}|{perm_id}",
                                 mode="discovery", sid=sid, actor=actor,
                                 trial=trial, perm_id=perm_id))
    assert len(jobs) == 7 * 2 * 24 == 336, len(jobs)
    seen = [(j["sid"], j["actor"], j["perm_id"]) for j in jobs]
    assert len(set(seen)) == len(seen), "duplicate permutation in job list"

    print("=== STUDY 4 FOUR-OBJECT DISCOVERY ===")
    print(f"arrays   : {len(sids)}   models: gpt, claude   perms/cell: 24")
    print(f"gpt      : {S.GPT_ID}")
    print(f"claude   : {S.CLAUDE_ID}")
    print(f"prompt   : sha8={S.PROMPT_SHA['stage_a']}  (four-option; binary parent 3003ae1b)")
    print(f"stimuli  : {S.STIM}")
    print(f"run dir  : {a.run_dir}")
    print(f"calls    : {len(jobs)}{'   [DRY RUN]' if a.dry_run else ''}\n", flush=True)

    imgs = {}

    def images_for(job):
        k = (job["sid"], job["perm_id"])
        if k not in imgs:
            imgs[k] = S.b64(os.path.join(S.STIM, job["sid"],
                                         f"perm{job['perm_id']:02d}.png"))
        return imgs[k]

    prefix = os.path.join(a.run_dir, "data", "stageA_discovery4")
    prefix, rows = S.run_stage("stageA_discovery4", jobs, lambda j: S.STAGE_A_PROMPT,
                               images_for, dry_run=a.dry_run, workers=a.workers,
                               out_prefix=prefix, resume_from=a.resume_from)
    if a.dry_run:
        return

    man, out, n_fail = {}, [], 0
    for r in rows:
        sid = r["sid"]
        if sid not in man:
            man[sid] = json.load(open(os.path.join(S.STIM, sid, "manifest.json")))
        pos = S.parse_choice(r["raw"]) if r["ok"] else None
        item = man[sid][str(r["perm_id"])][pos] if pos is not None else None
        if r["ok"] and pos is None:
            n_fail += 1
        out.append(dict(
            mode=r["mode"], stimulus_id=sid, model=r["actor"], trial=r["trial"],
            perm_id=r["perm_id"],
            chosen_position=("" if pos is None else pos + 1),
            chosen_item=("" if item is None else item),
            ok=r["ok"], parse_ok=(pos is not None), error=r["error"],
            api_model=r["api_model"], prompt_sha8=S.PROMPT_SHA["stage_a"],
            secs=r["secs"], ts=r["ts"],
            raw=r["raw"].replace("\n", " ")[:1500],
            reasoning=(r["reasoning"] or "").replace("\n", " ")[:1500]))
    with open(prefix + ".csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0].keys()))
        w.writeheader(); w.writerows(out)
    print(f"\nwrote {prefix}.csv  ({len(out)} rows)")
    print(f"  transport ok : {sum(1 for r in out if r['ok'])}/{len(out)}")
    print(f"  parsed ok    : {sum(1 for r in out if r['parse_ok'])}/{len(out)}")
    print(f"  PARSE FAILS  : {n_fail}")


if __name__ == "__main__":
    main()
