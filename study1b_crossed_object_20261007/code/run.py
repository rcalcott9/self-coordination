"""Study 1b runner for Phase A (screen) and Phase C (main). Phase B is select_arrays.py (no calls).

  /opt/anaconda3/bin/python code/run.py --phase screen --cap X [--dry] [--root DIR]
  /opt/anaconda3/bin/python code/run.py --phase main   --cap X [--dry] [--root DIR]

Refuses to start unless the phase's FROZEN file matches its .sha256 and all code matches the
hashes frozen inside it. Phase main also refuses unless SELECTION.json's sha256 equals the one
frozen in FROZEN_MAIN and the prompts are no longer placeholders (dry runs may proceed).
Every row carries the frozen hash, the selection hash, the code hashes and full request/response
provenance. Parsing never defaults. Resume-safe on (task, answerer, target, array, rep).
"""
import argparse, glob, base64, csv, datetime, hashlib, json, os, sys, threading, time
from concurrent.futures import ThreadPoolExecutor, as_completed
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C                                                     # noqa: E402

FIELDS = ["run_id", "phase", "task", "answerer", "target", "array", "stratum", "rep", "perm_id",
          "display_order", "stimulus_sha8", "prompt_key", "prompt_sha8", "frozen_sha8", "selection_sha8",
          "code_sha8", "model_requested", "model_returned", "model_match", "request_settings", "surface",
          "response_id", "stop_reason", "transport_ok", "parse_ok", "slot_returned", "canonical_choice",
          "p_slots_raw", "p_sum_raw", "p_canonical", "in_tokens", "out_tokens", "reasoning_tokens",
          "cost_usd", "secs", "ts_utc", "error", "raw", "reasoning_summary"]


def check_gates(root, fsha):
    """Existing gates (design section 7): preflight all OK; parse pilot >= .95 per predictor x target cell."""
    def rows(stage):
        return [r for f in glob.glob(os.path.join(root, "runs", stage, "*.csv")) for r in csv.DictReader(open(f))
                if r["frozen_sha8"] == fsha]
    pf = rows("preflight")
    if len(pf) < 6 or not all(r["transport_ok"] == "1" and r["parse_ok"] == "1" and r["model_match"] == "1" for r in pf):
        return False, f"preflight incomplete or failed ({len(pf)} rows)"
    pl = rows("pilot"); rates = {}
    for r in pl:
        k = (r["answerer"], r["target"]); rates.setdefault(k, []).append(r["parse_ok"] == "1")
    if len(rates) < 4 or any(len(v) < 8 for v in rates.values()):
        return False, "pilot incomplete"
    bad = {k: sum(v) / len(v) for k, v in rates.items() if sum(v) / len(v) < 0.95}
    if bad:
        return False, f"pilot parse rate < .95: {bad}"
    return True, "preflight 6/6 OK; pilot parse " + ", ".join(f"{k[0]}->{k[1]} {sum(v)}/{len(v)}" for k, v in sorted(rates.items()))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", required=True, choices=["screen", "main"])
    ap.add_argument("--cap", type=float, required=True); ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--dry", action="store_true"); ap.add_argument("--root", default=C.STUDY)
    ap.add_argument("--stage", choices=["preflight", "pilot", "main"], default="main",
                    help="phase main only: existing gates run as stages preflight -> pilot -> main")
    a = ap.parse_args()
    fpath = os.path.join(a.root, "design", "FROZEN_SCREEN.json" if a.phase == "screen" else "FROZEN_MAIN.json")
    F, fsha = C.load_frozen(fpath)
    C.verify_code(F["code_sha8"])
    sel8 = ""
    if a.phase == "main":
        sp = os.path.join(a.root, "design", "SELECTION.json")
        if C.sha256f(sp) != F["selection_sha256"]:
            sys.exit("ABORT: SELECTION.json does not match the selection frozen in FROZEN_MAIN")
        C.load_frozen(sp)
        sel8 = F["selection_sha8"]
        if not a.dry and (F.get("prompts_placeholder") or F.get("selection_self_test")):
            sys.exit("ABORT: placeholder prompts or self-test selection; live main run refused")
    stage = a.stage if a.phase == "main" else "screen"
    if a.phase == "main" and stage == "main" and not a.dry:
        gate_ok, msg = check_gates(a.root, fsha)
        if not gate_ok:
            sys.exit(f"ABORT: gate not passed - {msg}")
        print(f"[gates] {msg}")
    out = os.path.join(a.root, "runs", stage if a.phase == "main" else a.phase); os.makedirs(out, exist_ok=True)
    done = set()
    for f in os.listdir(out):
        if f.endswith(".csv"):
            for r in csv.DictReader(open(os.path.join(out, f))):
                if r["transport_ok"] == "1" and r["frozen_sha8"] == fsha:
                    done.add((r["task"], r["answerer"], r["target"], r["array"], int(r["rep"])))
    jobs = [j for j in F["schedule"] if j.get("stage", "main" if a.phase == "main" else "screen") in (stage, "screen")
            and (a.phase == "screen" or j.get("stage", "main") == stage)
            and (j["task"], j["answerer"], j["target"], j["array"], j["rep"]) not in done]
    est = sum(C.RATE[(j["answerer"], j["task"])] for j in jobs)
    by = {}
    for j in jobs:
        k = f"{j['task']}|answerer={j['answerer']}|target={j['target']}"
        by[k] = by.get(k, 0) + 1
    print(f"[{a.phase}] FROZEN {fsha} selection {sel8 or '-'} | {len(jobs)} calls (skip {len(done)}) | "
          f"est ${est:.2f} cap ${a.cap:.2f}")
    for k, v in sorted(by.items()):
        t, ans, _ = k.split("|")
        print(f"   {k:42s} {v:6d}  ${v * C.RATE[(ans.split('=')[1], t)]:.2f}")
    if est > a.cap:
        sys.exit("ABORT: estimate exceeds cap")
    if a.dry:
        print("[dry] no calls made"); return

    clients = C.P.make_clients(); budget = C.P.Budget(a.cap)
    code8 = json.dumps(F["code_sha8"], sort_keys=True)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = os.path.join(out, f"{stage}_{stamp}.csv")
    fh = open(path, "w", newline=""); w = csv.DictWriter(fh, fieldnames=FIELDS); w.writeheader()
    lock = threading.Lock(); rows = []

    def one(j):
        if not budget.ok():
            return None
        mid = F["models"][j["answerer"]]["model_id"]
        prompt = F["prompts"][j["prompt_key"]]["text"]
        raw = open(os.path.join(F["stimuli_root"], j["array"], f"perm{j['perm_id']:02d}.png"), "rb").read()
        row = dict.fromkeys(FIELDS, "")
        row.update(run_id=f"S1B-{stage}-{stamp}", phase=a.phase, task=j["task"], answerer=j["answerer"],
                   target=j["target"], array=j["array"], stratum=j.get("stratum", ""), rep=j["rep"],
                   perm_id=j["perm_id"], display_order=json.dumps(j["display_order"]),
                   stimulus_sha8=hashlib.sha256(raw).hexdigest()[:8], prompt_key=j["prompt_key"],
                   prompt_sha8=C.sha8(prompt), frozen_sha8=fsha, selection_sha8=sel8, code_sha8=code8,
                   model_requested=mid)
        assert row["prompt_sha8"] == F["prompts"][j["prompt_key"]]["sha8"]
        assert row["stimulus_sha8"] == F["stimuli"][j["array"]]["perm_png_sha8"][str(j["perm_id"])]
        t0 = time.time()
        res, err = C.P.call_with_backoff(C.ASK[j["answerer"]], clients[j["answerer"]], mid, prompt,
                                         base64.b64encode(raw).decode())
        row.update(secs=f"{time.time()-t0:.2f}", ts_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
        if res is None:
            row.update(transport_ok=0, parse_ok=0, model_match=0, error=err); return row
        c = C.P.cost(res["in_tok"], res["out_tok"]); budget.add(c)
        pr = (C.parse_ref if j["task"] == "REF" else C.parse_pred)(res["text"], j["display_order"])
        row.update(transport_ok=1, parse_ok=int(bool(pr)), model_returned=res["returned"],
                   model_match=int(res["returned"] == mid), request_settings=json.dumps(res["settings"]),
                   surface=res["surface"], response_id=res["response_id"], stop_reason=res["stop_reason"],
                   in_tokens=res["in_tok"], out_tokens=res["out_tok"], reasoning_tokens=res["reasoning_tok"],
                   cost_usd=f"{c:.6f}", raw=res["text"][:4000], reasoning_summary=res["summary"][:4000], **pr)
        return row

    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        for f in as_completed([ex.submit(one, j) for j in jobs]):
            r = f.result()
            if r is None:
                continue
            with lock:
                w.writerow(r); fh.flush(); rows.append(r)
    fh.close()
    summ = dict(path=path, n=len(rows), ok=sum(r["transport_ok"] == 1 for r in rows),
                parsed=sum(r["parse_ok"] == 1 for r in rows),
                mismatch=sum(r["transport_ok"] == 1 and r["model_match"] == 0 for r in rows),
                cost_usd=round(sum(float(r["cost_usd"] or 0) for r in rows), 4),
                frozen_sha8=fsha, selection_sha8=sel8, budget_stopped=budget.stopped)
    json.dump(summ, open(path.replace(".csv", "_summary.json"), "w"), indent=1)
    print(json.dumps(summ, indent=1))


if __name__ == "__main__":
    main()
