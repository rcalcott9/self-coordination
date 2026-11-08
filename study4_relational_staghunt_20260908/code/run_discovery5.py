"""Study 5 four-object DISCOVERY premeasure - 42 arrays x 2 models x 24 permutations.

Uses the frozen four-option coordination prompt UNCHANGED (s4_common.STAGE_A_PROMPT,
sha8 d40ea45d). NOTE: the task brief asked to verify prompt hash 3003ae1b; that is the
BINARY parent of this prompt ("one of the TWO shapes") and cannot address a four-object
array. d40ea45d is its arity-adapted sibling and is the only prompt satisfying "the
existing four-option coordination prompt, unchanged". Deviation recorded in the report.

Nothing under study2_4opt/ is modified: s4_common is imported and its STIM pointer is
redirected in-process to this study's stimuli5/, and all output goes to a new run dir.

Sharding: --shard I --nshards N slices the battery BY ARRAY (array index % N == I) so
several processes can run disjoint slices concurrently. Each shard writes its own
out_prefix (data/stageA_discovery5_s{I}of{N}), so concurrent shards never collide.
"""
import argparse, csv, json, os, sys

S4 = "/Users/calypsocalcott/Desktop/Coordination/Self_Coordination/study2_4opt_20260830/code"
EXP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, S4)
import s4_common as S

S.STIM = os.path.join(EXP, "stimuli5")          # in-process redirect, file untouched

N_ARRAYS = 42


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--resume-from", default=None)
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--shard", type=int, default=0)
    ap.add_argument("--nshards", type=int, default=1)
    a = ap.parse_args()

    assert a.nshards >= 1, a.nshards
    assert 0 <= a.shard < a.nshards, (a.shard, a.nshards)

    battery = list(csv.DictReader(open(os.path.join(S.STIM, "battery5_manifest.csv"))))
    sids = [r["array_id"] for r in battery]        # id column is array_id in battery5
    assert len(sids) == N_ARRAYS, sids
    assert len(set(sids)) == len(sids), "duplicate array_id in battery5_manifest.csv"

    # shard by ARRAY: every array lands in exactly one shard, so the union of the
    # N shards covers each of the 42*2*24 jobs exactly once (no gaps, no overlap).
    shards = {s: [sid for i, sid in enumerate(sids) if i % a.nshards == s]
              for s in range(a.nshards)}
    covered = [sid for s in range(a.nshards) for sid in shards[s]]
    assert sorted(covered) == sorted(sids), "shards do not cover every array"
    assert len(covered) == len(set(covered)) == len(sids), "array in >1 shard"
    my_sids = shards[a.shard]

    all_jobs, jobs = [], []
    for i, sid in enumerate(sids):
        for actor in ("gpt", "claude"):
            # all 24 permutations exactly once => every object in every position 6x
            for trial, perm_id in enumerate(range(24)):
                j = dict(job_key=f"discovery5|{sid}|{actor}|{perm_id}",
                         mode="discovery", sid=sid, actor=actor,
                         trial=trial, perm_id=perm_id)
                all_jobs.append(j)
                if i % a.nshards == a.shard:
                    jobs.append(j)
    assert len(all_jobs) == N_ARRAYS * 2 * 24 == 2016, len(all_jobs)
    assert len(jobs) == len(my_sids) * 2 * 24, (len(jobs), len(my_sids))
    seen = [(j["sid"], j["actor"], j["perm_id"]) for j in all_jobs]
    assert len(set(seen)) == len(seen), "duplicate permutation in job list"

    print("=== STUDY 5 FOUR-OBJECT DISCOVERY ===")
    print(f"arrays   : {len(sids)}   models: gpt, claude   perms/cell: 24")
    print(f"shard    : {a.shard} of {a.nshards}   arrays in shard: {len(my_sids)}")
    print(f"gpt      : {S.GPT_ID}")
    print(f"claude   : {S.CLAUDE_ID}")
    print(f"prompt   : sha8={S.PROMPT_SHA['stage_a']}  (four-option; binary parent 3003ae1b)")
    print(f"stimuli  : {S.STIM}")
    print(f"run dir  : {a.run_dir}")
    print(f"calls    : {len(jobs)} of {len(all_jobs)} total"
          f"{'   [DRY RUN]' if a.dry_run else ''}\n", flush=True)

    imgs = {}

    def images_for(job):
        k = (job["sid"], job["perm_id"])
        if k not in imgs:
            imgs[k] = S.b64(os.path.join(S.STIM, job["sid"],
                                         f"perm{job['perm_id']:02d}.png"))
        return imgs[k]

    prefix = os.path.join(a.run_dir, "data",
                          f"stageA_discovery5_s{a.shard}of{a.nshards}")
    os.makedirs(os.path.dirname(prefix), exist_ok=True)
    prefix, rows = S.run_stage("stageA_discovery5", jobs, lambda j: S.STAGE_A_PROMPT,
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
            mode=r["mode"], array_id=sid, model=r["actor"], trial=r["trial"],
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
