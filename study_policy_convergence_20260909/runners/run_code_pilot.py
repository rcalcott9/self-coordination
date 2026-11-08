"""
Stage 1 CODE PILOT GATE. 12 core items x 9 checkpoints x n=48 = 5184 calls.

Approved at Gate 1 (GATE1_REPORT.md S6, tranche B). Budget guard $20.
Prompt: prompts/code_prompt_v2.json (parser and render rule fixed; v1 never collected).
Coding:  coding/convention_groups_v1.json, pre-registered BEFORE this run.

Resume-safe: keyed on (item_id, checkpoint, trial). Re-running skips completed trials.
Every raw reply is preserved, including parse failures. Nothing is defaulted.

  python3 run_code_pilot.py [--dry] [--workers N] [--cap USD]
"""
import argparse, csv, datetime, hashlib, json, os, sys, threading, time
from concurrent.futures import ThreadPoolExecutor, as_completed

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pc_common as P                                              # noqa: E402

ROOT = P.ROOT
OUT = os.path.join(ROOT, "runs", "code_pilot")
CORE = ["code_argorder_003", "code_error_001", "code_fileorg_001", "code_fnname_001",
        "code_iface_003", "code_jsonname_001", "code_outorder_003", "code_return_001",
        "code_sentinel_001", "code_serial_001", "code_tie_001", "code_varname_002"]
SEED = 20260909
N = P.N_FLOOR

FIELDS = ["run_id", "domain", "item_id", "mechanism", "family", "checkpoint_requested",
          "checkpoint_returned", "checkpoint_match", "model_family", "vintage", "stratum",
          "control_surface", "thinking_blocks_returned", "trial", "presentation_id",
          "label_returned", "display_position", "canonical_index", "canonical_id",
          "convention_group", "parse_ok", "transport_ok", "attempts", "in_tokens",
          "out_tokens", "cost_usd", "prompt_hash", "battery_hash", "coding_hash",
          "secs", "ts_utc", "error", "raw"]


def render(item, perm):
    """v2 render rule: '<LABEL>.' on its own line, display indented 4, blank line between."""
    parts = []
    for slot, canon in enumerate(perm):
        disp = item["options"][canon]["display"]
        body = "\n".join("    " + ln for ln in disp.split("\n"))
        parts.append(f"{chr(65 + slot)}.\n{body}")
    return "\n\n".join(parts)


def interleave(jobs, key):
    """Round-robin jobs across `key` so consecutive jobs hit DIFFERENT endpoints.

    The natural comprehension order (array -> checkpoint -> trial) puts 48 consecutive
    jobs inside ONE (array, checkpoint) cell. With W workers and W < 48 that means every
    worker is calling the SAME endpoint at once while the other checkpoints sit idle:
    the run is serialised across checkpoints, throughput is bounded by whichever endpoint
    is current rather than by aggregate capacity, and that one endpoint absorbs all the
    rate pressure. Measured cost of getting this wrong on the 2026-09-09 frame run:
    8.2 -> 1.2 calls/s in the tail, and 57 of 59 connection errors landing on the two
    oldest GPT endpoints.
    """
    import collections
    buckets = collections.OrderedDict()
    for j in jobs:
        buckets.setdefault(key(j), []).append(j)
    out, qs = [], list(buckets.values())
    i = 0
    while any(qs):
        q = qs[i % len(qs)]
        if q:
            out.append(q.pop(0))
        i += 1
        if i % len(qs) == 0:
            qs = [q for q in qs if q]
            i = 0
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--cap", type=float, default=20.0)
    args = ap.parse_args()

    os.makedirs(OUT, exist_ok=True)
    pj = json.load(open(os.path.join(ROOT, "prompts", "code_prompt_v2.json")))
    tmpl = pj["user_prompt_template"]
    prompt_hash = hashlib.sha256(tmpl.encode()).hexdigest()[:8]
    bpath = os.path.join(ROOT, "code", "design", "code_items.json")
    battery_hash = hashlib.sha256(open(bpath, "rb").read()).hexdigest()[:8]
    cpath = os.path.join(ROOT, "coding", "convention_groups_v1.json")
    coding_hash = hashlib.sha256(open(cpath, "rb").read()).hexdigest()[:8]
    bat = json.load(open(bpath))
    coding = json.load(open(cpath))["items"]
    ptable = bat["presentation"]["permutation_table"]
    items = {i["item_id"]: i for i in bat["items"]}
    assert all(k in items for k in CORE), "core item missing from battery"

    # option -> convention_group lookup, pre-registered
    grp = {}
    for iid, spec in coding.items():
        for gname, idxs in spec["groups_canonical_index"].items():
            for ix in idxs:
                grp[(iid, ix)] = gname
    for iid in CORE:                       # every option must carry a group
        for o in items[iid]["options"]:
            assert (iid, o["canonical_index"]) in grp, f"ungrouped option {iid} {o}"

    # presentation schedule, verified balanced BEFORE any call
    sched = {}
    for iid in CORE:
        for _, mid, _, _ in P.PANEL:
            perms = P.trial_perms(N, seed=hash((SEED, iid, mid)) & 0xFFFFFFFF)
            P.verify_slot_balance(ptable, perms)
            sched[(iid, mid)] = perms
    print(f"[preflight] {len(CORE)} items x {len(P.PANEL)} checkpoints x n={N} "
          f"= {len(CORE) * len(P.PANEL) * N} calls; slot balance verified 12x per cell")
    print(f"[preflight] prompt {prompt_hash}  battery {battery_hash}  coding {coding_hash}")

    # resume
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")
    done = set()
    for f in sorted(os.listdir(OUT)):
        if f.startswith("code_pilot_") and f.endswith(".csv"):
            for r in csv.DictReader(open(os.path.join(OUT, f), newline="")):
                if r.get("transport_ok") == "1":
                    done.add((r["item_id"], r["checkpoint_requested"], int(r["trial"])))
    if done:
        print(f"[resume] {len(done)} trials already collected, skipping them")

    jobs = [(iid, fam, mid, vin, strat, t)
            for iid in CORE
            for fam, mid, vin, strat in P.PANEL
            for t in range(N)
            if (iid, mid, t) not in done]
    if not jobs:
        print("nothing to do"); return
    jobs = interleave(jobs, lambda j: j[2])     # spread workers across endpoints
    est = len(jobs) * 0.00324
    print(f"[plan] {len(jobs)} calls, estimated ${est:.2f}, cap ${args.cap:.2f}, "
          f"{args.workers} workers")
    if est > args.cap:
        sys.exit(f"ABORT: estimate ${est:.2f} exceeds cap ${args.cap:.2f}")
    if args.dry:
        iid, fam, mid, vin, st, t = jobs[0]
        pid = sched[(iid, mid)][t]
        print("\n---- sample rendered prompt ----")
        print(tmpl.replace("{spec}", items[iid]["spec"])
                  .replace("{options}", render(items[iid], ptable[pid])))
        print("---- end ----\n[dry] no calls made"); return

    clients = P.make_clients()
    budget = P.Budget(args.cap)
    path = os.path.join(OUT, f"code_pilot_{stamp}.csv")
    fh = open(path, "w", newline="")
    w = csv.DictWriter(fh, fieldnames=FIELDS); w.writeheader()
    lock = threading.Lock()
    tally = {"ok": 0, "parse_fail": 0, "transport_fail": 0, "mismatch": 0, "cost": 0.0}
    t0 = time.time()

    def one(job):
        iid, fam, mid, vin, strat, t = job
        if not budget.ok():
            return None
        pid = sched[(iid, mid)][t]
        perm = ptable[pid]
        item = items[iid]
        prompt = (tmpl.replace("{spec}", item["spec"])
                      .replace("{options}", render(item, perm)))
        s0 = time.time()
        res, err = P.call_with_backoff(P.ASK[fam], clients[fam], mid, prompt)
        secs = time.time() - s0
        row = dict.fromkeys(FIELDS, "")
        row.update(run_id=f"CODEPILOT-{stamp}", domain="code", item_id=iid,
                   mechanism=item["mechanism"], family=item["family"],
                   checkpoint_requested=mid, model_family=fam, vintage=vin,
                   stratum=strat, trial=t, presentation_id=pid,
                   prompt_hash=prompt_hash, battery_hash=battery_hash,
                   coding_hash=coding_hash, secs=f"{secs:.2f}",
                   ts_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                   attempts=1)
        if res is None:
            row.update(transport_ok=0, parse_ok=0, error=err)
            return row
        letter = P.parse_label(res["text"])
        c = P.cost(res["in_tok"], res["out_tok"])
        row.update(transport_ok=1, checkpoint_returned=res["returned"],
                   checkpoint_match=int(res["returned"] == mid),
                   control_surface=res["surface"],
                   thinking_blocks_returned=int(bool(res["thinking_blocks"])),
                   in_tokens=res["in_tok"], out_tokens=res["out_tok"],
                   cost_usd=f"{c:.6f}", raw=res["text"][:1200])
        if letter is None:
            row.update(parse_ok=0)
        else:
            slot = "ABCD".index(letter)
            canon = perm[slot]
            opt = item["options"][canon]
            row.update(parse_ok=1, label_returned=letter, display_position=slot + 1,
                       canonical_index=canon, canonical_id=opt["canonical_id"],
                       convention_group=grp[(iid, canon)])
        budget.add(c)
        return row

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = [ex.submit(one, j) for j in jobs]
        for i, f in enumerate(as_completed(futs), 1):
            row = f.result()
            if row is None:
                continue
            with lock:
                w.writerow(row); fh.flush()
                if not row["transport_ok"]:
                    tally["transport_fail"] += 1
                else:
                    tally["cost"] += float(row["cost_usd"])
                    if not row["parse_ok"]:
                        tally["parse_fail"] += 1
                    else:
                        tally["ok"] += 1
                    if not row["checkpoint_match"]:
                        tally["mismatch"] += 1
                if i % 250 == 0 or i == len(futs):
                    el = time.time() - t0
                    print(f"  {i}/{len(futs)}  ok={tally['ok']} "
                          f"parse_fail={tally['parse_fail']} tx_fail={tally['transport_fail']} "
                          f"mismatch={tally['mismatch']} ${tally['cost']:.2f} "
                          f"{i/max(el,1):.1f} calls/s", flush=True)
    fh.close()
    print(f"\n[done] {path}")
    print(f"  ok {tally['ok']}  parse_fail {tally['parse_fail']}  "
          f"transport_fail {tally['transport_fail']}  checkpoint_mismatch {tally['mismatch']}")
    print(f"  measured cost ${tally['cost']:.4f} in {time.time()-t0:.0f}s")
    if budget.stopped:
        print("  *** BUDGET CAP REACHED - run is INCOMPLETE ***")
    json.dump(dict(tally, path=path, stamp=stamp, prompt_hash=prompt_hash,
                   battery_hash=battery_hash, coding_hash=coding_hash,
                   n_jobs=len(jobs), seconds=time.time() - t0),
              open(os.path.join(OUT, f"code_pilot_{stamp}_summary.json"), "w"), indent=2)


if __name__ == "__main__":
    main()
