"""Study 5 four-object CONFIRMATION - locked candidates x 2 models x 72 responses.

n = 72 = THREE full 24-permutation cycles, so every canonical object appears in every
screen position exactly 18 times. FRESH sample: written to its own run directory and
never pooled with discovery. The locked focal identity is TESTED, not re-chosen; an
unconstrained confirmation mode is reported separately by the analyser.

Uses the frozen four-option coordination prompt UNCHANGED (s4_common.STAGE_A_PROMPT,
sha8 d40ea45d). NOTE: the task brief asked to verify prompt hash 3003ae1b; that is the
BINARY parent of this prompt ("one of the TWO shapes") and cannot address a four-object
array. d40ea45d is its arity-adapted sibling and is the only prompt satisfying "the
existing four-option coordination prompt, unchanged". Deviation recorded in the report.

Nothing under study2_4opt/ is modified: s4_common is imported and its STIM pointer is
redirected in-process to this study's stimuli6/, and all output goes to a new run dir.

Sharding: --shard I --nshards N slices the battery BY ARRAY (array index % N == I) so
several processes can run disjoint slices concurrently. Each shard writes its own
out_prefix (data/stageA_confirm6_s{I}of{N}), so concurrent shards never collide.
"""
import argparse, csv, json, os, sys

S4 = "/Users/calypsocalcott/Desktop/Coordination/Self_Coordination/study2_4opt_20260830/code"
EXP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, S4)
import s4_common as S

S.STIM = os.path.join(EXP, "stimuli6")          # in-process redirect, file untouched

N_CYCLES = 3                     # 3 x 24 = 72 responses per model per array


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--resume-from", default=None)
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--shard", type=int, default=0)
    ap.add_argument("--nshards", type=int, default=1)
    ap.add_argument("--locked", required=True, help="CONFIRMATION_CANDIDATES_LOCKED6.json")
    a = ap.parse_args()

    assert a.nshards >= 1, a.nshards
    assert 0 <= a.shard < a.nshards, (a.shard, a.nshards)

    battery = list(csv.DictReader(open(os.path.join(S.STIM, "battery6_manifest.csv"))))
    locked = json.load(open(a.locked))
    want = sorted({r["array_id"] for r in locked if r["track"] != "shared_control"})
    battery = [r for r in battery if r["array_id"] in want]
    assert len(battery) == len(want), (len(battery), len(want))
    sids = [r["array_id"] for r in battery]        # id column is array_id in battery6
    assert len(set(sids)) == len(sids), "duplicate array_id in battery6_manifest.csv"

    # shard by ARRAY: every array lands in exactly one shard, so the union of the
    # N shards covers each of the len(sids)*2*24*N_CYCLES jobs exactly once (no gaps, no overlap).
    shards = {s: [sid for i, sid in enumerate(sids) if i % a.nshards == s]
              for s in range(a.nshards)}
    covered = [sid for s in range(a.nshards) for sid in shards[s]]
    assert sorted(covered) == sorted(sids), "shards do not cover every array"
    assert len(covered) == len(set(covered)) == len(sids), "array in >1 shard"
    my_sids = shards[a.shard]

    all_jobs, jobs = [], []
    for i, sid in enumerate(sids):
        for actor in ("gpt", "claude"):
            # 3 full cycles of all 24 permutations => every object in every position 18x
            for trial, perm_id in enumerate(list(range(24)) * N_CYCLES):
                j = dict(job_key=f"confirm6|{sid}|{actor}|t{trial}|p{perm_id}",
                         mode="confirmation", sid=sid, actor=actor,
                         trial=trial, perm_id=perm_id)
                all_jobs.append(j)
                if i % a.nshards == a.shard:
                    jobs.append(j)
    assert len(all_jobs) == len(sids) * 2 * 24 * N_CYCLES, len(all_jobs)
    assert len(jobs) == len(my_sids) * 2 * 24 * N_CYCLES, (len(jobs), len(my_sids))
    assert len({j["job_key"] for j in all_jobs}) == len(all_jobs), "duplicate job_key"
    from collections import Counter
    for sid in sids:                                  # exact position balance per cell
        for actor in ("gpt", "claude"):
            c = Counter(j["perm_id"] for j in all_jobs
                        if j["sid"] == sid and j["actor"] == actor)
            assert set(c.values()) == {N_CYCLES} and len(c) == 24, (sid, actor, c)

    print("=== STUDY 4 FOUR-OBJECT CONFIRMATION (n=72, fresh) ===")
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
                          f"stageA_confirm6_s{a.shard}of{a.nshards}")
    os.makedirs(os.path.dirname(prefix), exist_ok=True)
    prefix, rows = S.run_stage("stageA_confirm6", jobs, lambda j: S.STAGE_A_PROMPT,
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
