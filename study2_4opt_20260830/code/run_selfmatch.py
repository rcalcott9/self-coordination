"""
Stage A - self-match estimation for the 4-option battery.

Two MODES, written to separate files and never pooled:
  --mode discovery    ranks candidates; default n=24 per model x stimulus
  --mode validation   held-out estimate used for SELECTION; default n=60

Selection is applied to validation numbers only. Discovery exists to shortlist so
validation is not spent on the whole battery; using the same sample for both is
exactly the winner's-curse that halved `a_chev_ud` (+0.650 -> +0.294) on the Aug-22
screen.

POSITION. Each trial draws a perm id from a schedule in which every ITEM appears in
every POSITION exactly n/4 times (asserted in s4_common.position_schedule). The
model answers with a POSITION 1-4; the manifest maps that back to the ITEM, and
only the item is the estimand. Position bias is computed from the same trials as a
separate diagnostic, and is a recorded covariate, not an exclusion criterion - at
4 options a position responder scores .25, i.e. chance, so it is a genuine floor
rather than an artefact that needs removing.

Run:
  python3 run_selfmatch.py --mode discovery --dry-run
  python3 run_selfmatch.py --mode discovery --stimuli F01_oddone_m0 F11_noise_m0 -n 8
  python3 run_selfmatch.py --mode discovery
"""
import os, csv, json, argparse
import s4_common as S


def load_battery():
    p = os.path.join(S.STIM, "battery_manifest.csv")
    return list(csv.DictReader(open(p)))


def build_jobs(sids, models, n, mode):
    jobs = []
    for sid in sids:
        for actor in models:
            # One schedule per (stimulus, model) cell so each cell is internally
            # balanced; cells are independent samples, not a shared sequence.
            sched = S.position_schedule(n)
            for trial, perm_id in enumerate(sched):
                jobs.append(dict(
                    job_key=f"{mode}|{sid}|{actor}|{trial}",
                    mode=mode, sid=sid, actor=actor, trial=trial, perm_id=perm_id))
    return jobs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=("discovery", "validation"), required=True)
    ap.add_argument("-n", type=int, default=None,
                    help="trials per model x stimulus (must be divisible by 4)")
    ap.add_argument("--stimuli", nargs="*", default=None)
    ap.add_argument("--models", nargs="*", default=["gpt", "claude"])
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--resume-from", default=None)
    ap.add_argument("--workers", type=int, default=S.WORKERS)
    a = ap.parse_args()

    n = a.n or (24 if a.mode == "discovery" else 60)
    battery = load_battery()
    sids = a.stimuli or [r["stimulus_id"] for r in battery]
    known = {r["stimulus_id"] for r in battery}
    bad = [s for s in sids if s not in known]
    if bad:
        raise SystemExit(f"unknown stimuli: {bad}")

    jobs = build_jobs(sids, a.models, n, a.mode)
    print(f"mode={a.mode}  stimuli={len(sids)}  models={a.models}  n={n}")
    print(f"prompt sha8 stage_a = {S.PROMPT_SHA['stage_a']}")
    print(f"planned calls = {len(jobs)}")

    imgs = {}

    def images_for(job):
        k = (job["sid"], job["perm_id"])
        if k not in imgs:
            imgs[k] = S.b64(os.path.join(S.STIM, job["sid"],
                                         f"perm{job['perm_id']:02d}.png"))
        return imgs[k]

    prefix, rows = S.run_stage(
        f"stageA_{a.mode}", jobs, lambda j: S.STAGE_A_PROMPT, images_for,
        dry_run=a.dry_run, workers=a.workers, resume_from=a.resume_from)
    if a.dry_run:
        return

    # ---- parse into a long CSV; malformed rows are KEPT with parsed=None -------
    man = {}
    out = []
    n_fail = 0
    for r in rows:
        sid = r["sid"]
        if sid not in man:
            man[sid] = json.load(open(os.path.join(S.STIM, sid, "manifest.json")))
        pos = S.parse_choice(r["raw"]) if r["ok"] else None
        item = None
        if pos is not None:
            item = man[sid][str(r["perm_id"])][pos]
        if r["ok"] and pos is None:
            n_fail += 1
        out.append(dict(
            mode=r["mode"], stimulus_id=sid, model=r["actor"], trial=r["trial"],
            perm_id=r["perm_id"], chosen_position=("" if pos is None else pos + 1),
            chosen_item=("" if item is None else item),
            ok=r["ok"], parse_ok=(pos is not None), error=r["error"],
            api_model=r["api_model"], secs=r["secs"], ts=r["ts"],
            raw=r["raw"].replace("\n", " ")[:1500],
            reasoning=(r["reasoning"] or "").replace("\n", " ")[:1500]))

    with open(prefix + ".csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0].keys()))
        w.writeheader(); w.writerows(out)

    n_ok = sum(1 for r in out if r["parse_ok"])
    print(f"\nwrote {prefix}.csv   ({len(out)} rows)")
    print(f"  transport ok   : {sum(1 for r in out if r['ok'])}/{len(out)}")
    print(f"  parsed ok      : {n_ok}/{len(out)}")
    print(f"  PARSE FAILURES : {n_fail} (kept in file with parse_ok=False)")


if __name__ == "__main__":
    main()
