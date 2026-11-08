"""
Stage 1 VISUAL collection. Shared runner for the liveness preflight and the full frame.

  python3 run_visual.py --set preflight   # 24 arrays x 2 checkpoints x n=24  (~$6.5)
  python3 run_visual.py --set frame       # 41 arrays x 9 checkpoints x n=48  (~$100)

Claude is called with thinking={"type":"disabled"} explicitly, asserted before dispatch and
verified from the reply (D-017). Every raw reply is preserved. Resume-safe on
(array_id, checkpoint, trial). Nothing is defaulted on a parse failure.
"""
import argparse, base64, csv, datetime, hashlib, json, os, sys, threading, time
from concurrent.futures import ThreadPoolExecutor, as_completed

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pc_common as P                                              # noqa: E402

ROOT, TREE = P.ROOT, P.TREE
STIM = os.path.join(TREE, "study2_4opt_20260830", "stimuli")
sys.path.insert(0, os.path.join(TREE, "study2_4opt_20260830", "code"))
import s4_common as S4                                             # noqa: E402

SEED = 20260909
FIELDS = ["run_id", "domain", "collection_set", "array_id", "family", "mechanism",
          "on_stratum", "checkpoint_requested", "checkpoint_returned", "checkpoint_match",
          "model_family", "vintage", "stratum", "control_surface",
          "thinking_blocks_returned", "trial", "presentation_id", "slot_returned",
          "display_position", "canonical_index", "parse_ok", "transport_ok", "attempts",
          "in_tokens", "out_tokens", "cost_usd", "prompt_hash", "stimulus_sha8",
          "secs", "ts_utc", "error", "raw"]

_imgs = {}
_imglock = threading.Lock()


def img_b64(array_id, pid):
    key = (array_id, pid)
    with _imglock:
        if key in _imgs:
            return _imgs[key]
    path = os.path.join(STIM, array_id, f"perm{pid:02d}.png")
    raw = open(path, "rb").read()
    v = (base64.b64encode(raw).decode(), hashlib.sha256(raw).hexdigest()[:8])
    with _imglock:
        _imgs[key] = v
    return v


def load_set(name):
    if name == "preflight":
        spec = json.load(open(os.path.join(ROOT, "runs", "liveness_preflight",
                                           "selection.json")))
        arrays = [(a["array_id"], a["family"], a["mechanism"], a["on_stratum"])
                  for a in spec["arrays"]]
        panel = [p for p in P.PANEL if p[1] in spec["checkpoints"]]
        assert len(panel) == 2, panel
        return arrays, panel, spec["n_per_cell"], os.path.join(ROOT, "runs",
                                                               "liveness_preflight")
    rows = [r for r in csv.DictReader(open(os.path.join(
        ROOT, "audits", "visual", "recommended_frame_arrays.csv")))
        if r["frame_id"] == "VIS-FRAME-41"]
    arrays = [(r["array_id"], r["family"], r["mechanism"], "") for r in rows]
    assert len(arrays) == 41, len(arrays)
    return arrays, P.PANEL, P.N_FLOOR, os.path.join(ROOT, "runs", "visual_frame")


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
    ap.add_argument("--set", required=True, choices=["preflight", "frame"])
    ap.add_argument("--workers", type=int, default=20)
    ap.add_argument("--cap", type=float, default=8.0)
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args()

    arrays, panel, n, out = load_set(args.set)
    os.makedirs(out, exist_ok=True)
    prompt = S4.STAGE_A_PROMPT
    prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()[:8]
    assert prompt_hash == "d40ea45d", f"prompt drift: {prompt_hash}"

    manifests = {a: {int(k): v for k, v in
                     json.load(open(os.path.join(STIM, a, "manifest.json"))).items()}
                 for a, *_ in arrays}
    sched = {}
    for a, *_ in arrays:
        table = [manifests[a][i] for i in range(P.N_PERMS)]
        for _, mid, _, _ in panel:
            perms = P.trial_perms(n, seed=hash((SEED, a, mid)) & 0xFFFFFFFF)
            P.verify_slot_balance(table, perms)
            sched[(a, mid)] = perms
    per_cell = n // 4
    print(f"[preflight] set={args.set}  {len(arrays)} arrays x {len(panel)} checkpoints "
          f"x n={n} = {len(arrays)*len(panel)*n} calls")
    print(f"[preflight] prompt {prompt_hash}; slot balance verified {per_cell}x per cell")

    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")
    done = set()
    for f in sorted(os.listdir(out)):
        if f.startswith(f"visual_{args.set}_") and f.endswith(".csv"):
            for r in csv.DictReader(open(os.path.join(out, f), newline="")):
                if r.get("transport_ok") == "1":
                    done.add((r["array_id"], r["checkpoint_requested"], int(r["trial"])))
    if done:
        print(f"[resume] skipping {len(done)} trials already collected")

    jobs = [(a, fam, mech, strat, mfam, mid, vin, mstrat, t)
            for a, fam, mech, strat in arrays
            for mfam, mid, vin, mstrat in panel
            for t in range(n)
            if (a, mid, t) not in done]
    if not jobs:
        print("nothing to do"); return
    jobs = interleave(jobs, lambda j: j[5])     # spread workers across endpoints
    est = len(jobs) * 0.00567
    print(f"[plan] {len(jobs)} calls, estimated ${est:.2f}, cap ${args.cap:.2f}, "
          f"{args.workers} workers")
    if est > args.cap:
        sys.exit(f"ABORT: estimate ${est:.2f} exceeds cap ${args.cap:.2f}")
    if args.dry:
        print("[dry] no calls made"); return

    clients = P.make_clients()
    budget = P.Budget(args.cap)
    path = os.path.join(out, f"visual_{args.set}_{stamp}.csv")
    fh = open(path, "w", newline="")
    w = csv.DictWriter(fh, fieldnames=FIELDS); w.writeheader()
    lock = threading.Lock()
    tally = {"ok": 0, "parse_fail": 0, "transport_fail": 0, "mismatch": 0, "cost": 0.0}
    t0 = time.time()

    def one(job):
        a, fam, mech, strat, mfam, mid, vin, mstrat, t = job
        if not budget.ok():
            return None
        pid = sched[(a, mid)][t]
        b64, ssha = img_b64(a, pid)
        s0 = time.time()
        res, err = P.call_with_backoff(P.ASK[mfam], clients[mfam], mid, prompt,
                                       image_b64=b64)
        row = dict.fromkeys(FIELDS, "")
        row.update(run_id=f"VIS-{args.set.upper()}-{stamp}", domain="visual",
                   collection_set=args.set, array_id=a, family=fam, mechanism=mech,
                   on_stratum=strat, checkpoint_requested=mid, model_family=mfam,
                   vintage=vin, stratum=mstrat, trial=t, presentation_id=pid,
                   prompt_hash=prompt_hash, stimulus_sha8=ssha, attempts=1,
                   secs=f"{time.time()-s0:.2f}",
                   ts_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
        if res is None:
            row.update(transport_ok=0, parse_ok=0, error=err)
            return row
        slot = P.parse_slot(res["text"])
        c = P.cost(res["in_tok"], res["out_tok"])
        row.update(transport_ok=1, checkpoint_returned=res["returned"],
                   checkpoint_match=int(res["returned"] == mid),
                   control_surface=res["surface"],
                   thinking_blocks_returned=int(bool(res["thinking_blocks"])),
                   in_tokens=res["in_tok"], out_tokens=res["out_tok"],
                   cost_usd=f"{c:.6f}", raw=res["text"][:1200])
        if slot is None:
            row.update(parse_ok=0)
        else:
            row.update(parse_ok=1, slot_returned=slot, display_position=slot + 1,
                       canonical_index=manifests[a][pid][slot])
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
                    tally["ok" if row["parse_ok"] else "parse_fail"] += 1
                    if not row["checkpoint_match"]:
                        tally["mismatch"] += 1
                if i % 200 == 0 or i == len(futs):
                    print(f"  {i}/{len(futs)}  ok={tally['ok']} "
                          f"parse_fail={tally['parse_fail']} "
                          f"tx_fail={tally['transport_fail']} "
                          f"mismatch={tally['mismatch']} ${tally['cost']:.2f} "
                          f"{i/max(time.time()-t0,1):.1f}/s", flush=True)
    fh.close()
    print(f"\n[done] {path}\n  ok {tally['ok']}  parse_fail {tally['parse_fail']}  "
          f"tx_fail {tally['transport_fail']}  mismatch {tally['mismatch']}  "
          f"${tally['cost']:.4f} in {time.time()-t0:.0f}s")
    if budget.stopped:
        print("  *** BUDGET CAP REACHED - INCOMPLETE ***")
    json.dump(dict(tally, path=path, stamp=stamp, set=args.set, n=n,
                   n_arrays=len(arrays), n_checkpoints=len(panel),
                   prompt_hash=prompt_hash, seconds=time.time() - t0),
              open(os.path.join(out, f"visual_{args.set}_{stamp}_summary.json"), "w"),
              indent=2)


if __name__ == "__main__":
    main()
