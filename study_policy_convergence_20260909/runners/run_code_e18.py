"""
Expansion battery E18 — pilot and full run.

  python3 run_code_e18.py --stage pilot   # 17 items x 4 boundary ckpts x n=12
  python3 run_code_e18.py --stage full    # N items  x 9 ckpts        x n=48

SCHEDULER. One bounded thread pool PER ENDPOINT, cap 4. This is structural, not an
ordering convention: with a single shared pool over an interleaved list the cap holds only
as long as the list stays interleaved, and Stage 1 lost 59 calls to exactly that assumption
(jobs ordered array -> checkpoint -> trial put all 30 workers on one endpoint; 57 of the 59
connection errors landed on the two oldest GPT endpoints). Per-endpoint pools make the cap
impossible to violate. Wall clock is then bounded by the slowest endpoint's own queue.

RETRIES. Transport and rate errors only, exponential backoff with jitter. A parse failure is
NEVER retried - retrying only unparseable trials selects for parseable responses, which is
Threat 15's mechanism. Parse failures are recorded and the cell carries the shortfall.

COUNTERBALANCING. n=48 is two complete cycles of all 24 permutations (every option at every
label 12x). n=12 is three Latin squares (every option at every label 3x). Exact at both;
asserted before any call.
"""
import argparse, collections, csv, datetime, hashlib, json, os, random, sys, threading, time
from concurrent.futures import ThreadPoolExecutor, as_completed

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pc_common as P                                              # noqa: E402

ROOT = P.ROOT
BATTERY = os.path.join(ROOT, "code", "design_x2", "candidates_e18.json")
CAP_PER_ENDPOINT = 4
SEED = 20260910
BOUNDARY = ["gpt-4-turbo-2024-04-09", "gpt-5.5-2026-04-23",
            "claude-opus-4-5-20251101", "claude-opus-5"]

FIELDS = ["run_id", "stage", "domain", "item_id", "mechanism", "checkpoint_requested",
          "checkpoint_returned", "checkpoint_match", "model_family", "vintage", "stratum",
          "control_surface", "thinking_blocks_returned", "trial", "presentation_id",
          "label_returned", "display_position", "canonical_index", "option_key",
          "parse_ok", "transport_ok", "failure_type", "retries", "worker",
          "t_start_utc", "t_end_utc", "secs", "in_tokens", "out_tokens", "cost_usd",
          "prompt_hash", "battery_hash", "error", "raw"]


def latin_perms(table, n):
    """n presentation ids, exactly balanced over labels.

    Built from Latin squares: cycling a base ordering gives 4 permutations in which every
    option occupies every label exactly once. n//4 distinct bases give n//4 such blocks.
    """
    assert n % 4 == 0, n
    bases = [[0, 1, 2, 3], [0, 2, 1, 3], [0, 3, 1, 2], [1, 0, 2, 3],
             [1, 2, 0, 3], [2, 0, 1, 3]]
    idx = {tuple(p): i for i, p in enumerate(table)}
    out = []
    for b in bases[: n // 4]:
        for j in range(4):
            out.append(idx[tuple(b[(i + j) % 4] for i in range(4))])
    assert len(out) == n
    return out


def schedule(table, n, key):
    """n=48 -> two full 24-cycles; anything else -> Latin-square blocks. Deterministic."""
    rng = random.Random(hash((SEED, key)) & 0xFFFFFFFF)
    if n % P.N_PERMS == 0:
        out = []
        for _ in range(n // P.N_PERMS):
            c = list(range(P.N_PERMS)); rng.shuffle(c); out.extend(c)
    else:
        out = latin_perms(table, n)
        rng.shuffle(out)
    P.verify_slot_balance(table, out)
    return out


def render(item, perm):
    parts = []
    for slot, canon in enumerate(perm):
        body = "\n".join("    " + ln for ln in item["options"][canon]["display"].split("\n"))
        parts.append(f"{chr(65 + slot)}.\n{body}")
    return "\n\n".join(parts)


def classify(err):
    low = (err or "").lower()
    if "rate" in low or "429" in low:
        return "rate_limit"
    if "connection" in low or "timeout" in low or "apiconnection" in low:
        return "transport"
    if "400" in low or "not_found" in low or "invalid" in low:
        return "request_rejected"
    return "other"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", required=True, choices=["pilot", "full"])
    ap.add_argument("--items", default="")
    ap.add_argument("--cap", type=float, required=True)
    ap.add_argument("--n", type=int, default=0)
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()

    bat = json.load(open(BATTERY))
    battery_hash = hashlib.sha256(open(BATTERY, "rb").read()).hexdigest()[:8]
    table = bat["presentation"]["permutation_table"]
    items = {i["item_id"]: i for i in bat["items"]}
    if a.stage == "pilot":
        keep = list(items); n = a.n or 12
        panel = [p for p in P.PANEL if p[1] in BOUNDARY]
        assert len(panel) == 4
    else:
        keep = [x.strip() for x in a.items.split(",") if x.strip()]
        assert keep, "--items required for the full run"
        assert all(k in items for k in keep), [k for k in keep if k not in items]
        n = a.n or P.N_FLOOR
        panel = P.PANEL

    pj = json.load(open(os.path.join(ROOT, "prompts", "code_prompt_v2.json")))
    tmpl = pj["user_prompt_template"]
    prompt_hash = hashlib.sha256(tmpl.encode()).hexdigest()[:8]

    sched = {(it, mid): schedule(table, n, (it, mid))
             for it in keep for _, mid, _, _ in panel}
    per_cell = n // 4
    print(f"[preflight] stage={a.stage}  {len(keep)} items x {len(panel)} endpoints x n={n} "
          f"= {len(keep)*len(panel)*n} calls")
    print(f"[preflight] counterbalancing verified: every option at every label {per_cell}x "
          f"in every cell")
    print(f"[preflight] prompt {prompt_hash}  battery {battery_hash}")
    print(f"[preflight] scheduler: {len(panel)} independent pools, cap "
          f"{CAP_PER_ENDPOINT}/endpoint, {CAP_PER_ENDPOINT*len(panel)} workers total")
    if a.stage == "full":
        # ---- PART 3 integrity gates, all asserted BEFORE any dispatch ----
        frozen = json.load(open(os.path.join(
            ROOT, "audits", "code_x2", "screen_result.json")))["final"]
        pv2 = os.path.join(ROOT, "prompts", "code_prompt_v2.json")
        g = [("1  exactly 5 frozen items",
              sorted(keep) == sorted(frozen) and len(keep) == 5),
             ("2  exactly 9 checkpoints", len(panel) == 9),
             ("3  n = 48 per model x item cell", n == 48 == P.N_FLOOR),
             ("4  exactly two complete 24-permutation cycles",
              n % P.N_PERMS == 0 and n // P.N_PERMS == 2),
             ("5  exact option-position balance", all(
                 len(set(collections.Counter(
                     tuple(table[pid]) for pid in sched[(it, mid)]).values())) == 1
                 and len(sched[(it, mid)]) == n
                 for it in keep for _, mid, _, _ in panel)),
             ("6  prompt hash matches frozen v2", prompt_hash == hashlib.sha256(
                 json.load(open(pv2))["user_prompt_template"].encode()).hexdigest()[:8]),
             ("7  prompt file unedited since freezing",
              hashlib.sha256(open(pv2, "rb").read()).hexdigest()
              == open(pv2.replace(".json", ".sha256")).read().split()[0]),
             ("8  checkpoint ids match the frozen Stage 1 ladder",
              [m for _, m, _, _ in panel] == [m for _, m, _, _ in P.PANEL])]
        print("[gates]")
        for name, ok in g:
            print(f"   [{'PASS' if ok else 'FAIL'}] {name}")
        if not all(ok for _, ok in g):
            sys.exit("ABORT: integrity gate failed before dispatch")


    out = os.path.join(ROOT, "runs", f"e18_{a.stage}")
    os.makedirs(out, exist_ok=True)
    done = set()
    for f in sorted(os.listdir(out)):
        if f.endswith(".csv"):
            for r in csv.DictReader(open(os.path.join(out, f), newline="")):
                if r.get("transport_ok") == "1":
                    done.add((r["item_id"], r["checkpoint_requested"], int(r["trial"])))
    if done:
        print(f"[resume] skipping {len(done)} completed trials")

    RATE = {"gpt-4-turbo-2024-04-09": .00217, "gpt-4.1-2025-04-14": .00214,
            "gpt-5-2025-08-07": .00829, "gpt-5.5-2026-04-23": .00457,
            "claude-opus-4-5-20251101": .00277, "claude-opus-4-6": .00291,
            "claude-opus-4-7": .00338, "claude-opus-4-8": .00327, "claude-opus-5": .00343}
    byend = {}
    for it in keep:
        for fam, mid, vin, st in panel:
            for t in range(n):
                if (it, mid, t) not in done:
                    byend.setdefault(mid, []).append((it, fam, mid, vin, st, t))
    est = sum(RATE[m] * len(v) for m, v in byend.items())
    tot = sum(len(v) for v in byend.values())
    print(f"[plan] {tot} calls, estimated ${est:.2f} at measured per-checkpoint rates, "
          f"cap ${a.cap:.2f}")
    for m, v in sorted(byend.items(), key=lambda kv: -len(kv[1]) * RATE[kv[0]]):
        print(f"         {m:28} {len(v):5d} calls  ${RATE[m]*len(v):6.2f}")
    if est > a.cap:
        sys.exit(f"ABORT: estimate ${est:.2f} exceeds cap ${a.cap:.2f}")
    if a.dry:
        print("[dry] no calls made"); return

    clients = P.make_clients()
    budget = P.Budget(a.cap)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = os.path.join(out, f"e18_{a.stage}_{stamp}.csv")
    fh = open(path, "w", newline="")
    w = csv.DictWriter(fh, fieldnames=FIELDS); w.writeheader()
    lock = threading.Lock()
    tally = {"ok": 0, "parse_fail": 0, "transport_fail": 0, "mismatch": 0,
             "retries": 0, "cost": 0.0}
    t0 = time.time()

    def one(job):
        it, fam, mid, vin, st, t = job
        if not budget.ok():
            return None
        item = items[it]
        pid = sched[(it, mid)][t]
        perm = table[pid]
        prompt = tmpl.replace("{spec}", item["spec"]).replace("{options}", render(item, perm))
        row = dict.fromkeys(FIELDS, "")
        row.update(run_id=f"E18-{a.stage.upper()}-{stamp}", stage=a.stage, domain="code",
                   item_id=it, mechanism=item["mechanism"], checkpoint_requested=mid,
                   model_family=fam, vintage=vin, stratum=st, trial=t, presentation_id=pid,
                   prompt_hash=prompt_hash, battery_hash=battery_hash,
                   worker=threading.current_thread().name)
        tries, err, res = 0, None, None
        t_start = datetime.datetime.now(datetime.timezone.utc)
        while tries < 5:
            try:
                res = P.ASK[fam](clients[fam], mid, prompt); err = None; break
            except AssertionError:
                raise
            except Exception as e:
                err = f"{type(e).__name__}: {e}"[:300]
                if classify(err) == "request_rejected":
                    break                              # never retry a rejected request
                tries += 1
                if tries < 5:
                    time.sleep(1.5 * (2 ** tries) * (.6 + .8 * random.random()))
        t_end = datetime.datetime.now(datetime.timezone.utc)
        row.update(retries=tries, t_start_utc=t_start.isoformat(),
                   t_end_utc=t_end.isoformat(), secs=f"{(t_end-t_start).total_seconds():.2f}")
        if res is None:
            row.update(transport_ok=0, parse_ok=0, error=err, failure_type=classify(err))
            return row
        letter = P.parse_label(res["text"])
        c = P.cost(res["in_tok"], res["out_tok"])
        row.update(transport_ok=1, checkpoint_returned=res["returned"],
                   checkpoint_match=int(res["returned"] == mid),
                   control_surface=res["surface"],
                   thinking_blocks_returned=int(bool(res["thinking_blocks"])),
                   in_tokens=res["in_tok"], out_tokens=res["out_tok"],
                   cost_usd=f"{c:.6f}", raw=res["text"][:1000])
        if letter is None:
            row.update(parse_ok=0, failure_type="parse")   # NOT retried, by design
        else:
            slot = "ABCD".index(letter)
            canon = perm[slot]
            row.update(parse_ok=1, failure_type="", label_returned=letter,
                       display_position=slot + 1, canonical_index=canon,
                       option_key=item["options"][canon]["option_key"])
        budget.add(c)
        return row

    pools, futs = [], []
    for mid, jobs in byend.items():
        ex = ThreadPoolExecutor(max_workers=CAP_PER_ENDPOINT,
                                thread_name_prefix=mid.split("-2")[0][:14])
        pools.append(ex)
        futs += [ex.submit(one, j) for j in jobs]
    n_done = 0
    for f in as_completed(futs):
        row = f.result()
        n_done += 1
        if row is None:
            continue
        with lock:
            w.writerow(row); fh.flush()
            tally["retries"] += int(row["retries"] or 0)
            if not row["transport_ok"]:
                tally["transport_fail"] += 1
            else:
                tally["cost"] += float(row["cost_usd"])
                tally["ok" if row["parse_ok"] else "parse_fail"] += 1
                if not row["checkpoint_match"]:
                    tally["mismatch"] += 1
            if n_done % 200 == 0 or n_done == len(futs):
                el = time.time() - t0
                print(f"  {n_done}/{len(futs)}  ok={tally['ok']} parse_fail="
                      f"{tally['parse_fail']} tx_fail={tally['transport_fail']} "
                      f"retries={tally['retries']} mismatch={tally['mismatch']} "
                      f"${tally['cost']:.2f}  {n_done/max(el,1):.1f}/s", flush=True)
    for ex in pools:
        ex.shutdown()
    fh.close()
    el = time.time() - t0
    print(f"\n[done] {path}\n  ok {tally['ok']}  parse_fail {tally['parse_fail']}  "
          f"tx_fail {tally['transport_fail']}  retries {tally['retries']}  "
          f"mismatch {tally['mismatch']}\n  ${tally['cost']:.4f} in {el:.0f}s "
          f"({len(futs)/max(el,1):.1f} calls/s)")
    if budget.stopped:
        print("  *** BUDGET CAP REACHED — INCOMPLETE ***")
    json.dump(dict(tally, path=path, stamp=stamp, stage=a.stage, n=n, items=keep,
                   endpoints=list(byend), cap_per_endpoint=CAP_PER_ENDPOINT,
                   seconds=el, prompt_hash=prompt_hash, battery_hash=battery_hash),
              open(path.replace(".csv", "_summary.json"), "w"), indent=2)


if __name__ == "__main__":
    main()
