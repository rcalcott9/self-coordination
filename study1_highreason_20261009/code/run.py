"""Runner for the high-reasoning Study 1 replication.

  /opt/anaconda3/bin/python code/run.py --stage preflight|pilot|main [--dry] [--mock] [--workers N]

Refuses to start unless FROZEN.json matches its sha256 and every code file matches the frozen hashes.
Main refuses unless the preflight report passed and every pilot cell parsed >= .95.
Budget: ONE global cap (FROZEN cap_usd) over every stage and retry. Spend already logged in runs/ counts; each
in-flight call reserves the current per-(answerer, task) estimate (max of frozen prior and observed mean x1.5);
dispatch stops when spent + reserved + next estimate would exceed the cap. Resume-safe on job_id; rows with
transport_ok=0 are retried on resume, parse failures are not. --mock writes to runs_mock/ with synthetic replies.
"""
import argparse, base64, csv, datetime, glob, hashlib, json, os, random, sys, threading, time
from concurrent.futures import ThreadPoolExecutor, as_completed
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hi_common as H                                                   # noqa: E402

FROZEN = os.path.join(H.STUDY, "design", "FROZEN.json")
FIELDS = ["run_id", "stage", "block", "studies", "task", "answerer", "focal", "array", "rep", "perm_id", "display_order",
          "job_id", "stimulus_sha8", "prompt_key", "prompt_sha8", "frozen_sha8", "model_requested", "model_returned",
          "model_match", "request_settings", "surface", "echoed_effort", "response_id", "stop_reason", "thinking_blocks",
          "transport_ok", "parse_ok", "slot_returned", "canonical_choice", "decision", "match_probability",
          "p_slots_raw", "p_sum_raw", "p_canonical", "in_tokens", "out_tokens", "reasoning_tokens", "cost_usd",
          "secs", "ts_utc", "error", "raw", "reasoning_summary"]
PRIOR = {("gpt", "REF"): .06, ("gpt", "PRED"): .08, ("gpt", "X"): .07,           # pessimistic priors until observed
         ("claude", "REF"): .05, ("claude", "PRED"): .06, ("claude", "X"): .05}


def kind(task):
    return task if task in ("REF", "PRED") else "X"


def verify():
    F, fsha = H.C.load_frozen(FROZEN)
    live = {f: H.sha256f(os.path.join(H.HERE, f))[:8] for f in F["code_sha8"] if os.path.exists(os.path.join(H.HERE, f))}
    live["pc_common.py"] = H.sha256f(os.path.join(H.C.SPC, "runners", "pc_common.py"))[:8]
    live["s1b_common.py"] = H.sha256f(os.path.join(H.S1B, "code", "common.py"))[:8]
    live["s1a_prompts.py"] = H.sha256f(os.path.join(H.S1A, "code", "prompts.py"))[:8]
    live["s1b_prompts.py"] = H.sha256f(os.path.join(H.S1B, "code", "prompts.py"))[:8]
    bad = {k: (live.get(k), v) for k, v in F["code_sha8"].items() if live.get(k) != v}
    if bad:
        sys.exit(f"ABORT: code changed since freeze: {bad}")
    prompts, _ = H.build_prompts()
    for k, v in F["prompts"].items():
        assert H.sha8(prompts[k]) == v["sha8"], k
    return F, fsha


def all_rows(base):
    return [r for f in glob.glob(os.path.join(base, "*", "*.csv")) for r in csv.DictReader(open(f))]


def gates_ok(base, fsha):
    pre = [r for r in all_rows(base) if r["stage"] == "preflight" and r["frozen_sha8"] == fsha and r["transport_ok"] == "1"]
    reps = sorted(glob.glob(os.path.join(base, "preflight", "*_REPORT.json")))
    if not reps or not json.load(open(reps[-1]))["passed"]:
        return False, "preflight not passed"
    pl = [r for r in all_rows(base) if r["stage"] == "pilot" and r["frozen_sha8"] == fsha]
    cells = {}
    for r in pl:
        if r["transport_ok"] == "1":
            cells.setdefault((r["task"], r["answerer"], r["focal"]), []).append(r["parse_ok"] == "1")
    if len(cells) < 12 or any(len(v) < 8 for v in cells.values()):
        return False, f"pilot incomplete ({len(cells)} cells)"
    bad = {k: f"{sum(v)}/{len(v)}" for k, v in cells.items() if sum(v) / len(v) < .95}
    if bad:
        return False, f"pilot parse < .95: {bad}"
    return True, f"preflight {len(pre)} ok; pilot " + ", ".join(f"{k[0]}:{k[1]}->{k[2]} {sum(v)}/{len(v)}" for k, v in sorted(cells.items()))


def mock_reply(j, rng):
    t = j["task"]
    if rng.random() < float(os.environ.get("MOCK_FAIL", ".02")):
        return "I cannot decide."
    if t == "REF":
        return f"The odd one stands out. CHOICE: {rng.choice([1, 1, 2, 3, 4])}"
    if t == "PLAYPASS":
        return f"Reason. DECISION: {rng.choice(['PLAY', 'PLAY', 'PASS'])}"
    if t in ("SELFPRED", "AUDITOR"):
        return f"Reason. MATCH_PROBABILITY: {rng.randint(20, 95)}"
    w = [rng.random() for _ in range(4)]; s = sum(w); v = [round(100 * x / s) for x in w]; v[0] += 100 - sum(v)
    return "Reason.\nA: {}\nB: {}\nC: {}\nD: {}".format(*v)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", required=True, choices=["preflight", "pilot", "main"])
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--dry", action="store_true"); ap.add_argument("--mock", action="store_true")
    a = ap.parse_args()
    F, fsha = verify()
    base = os.path.join(H.STUDY, "runs_mock" if a.mock else "runs")
    out = os.path.join(base, a.stage); os.makedirs(out, exist_ok=True)
    rows_all = all_rows(base)
    spent0 = sum(float(r["cost_usd"] or 0) for r in rows_all)
    obs = {}
    for r in rows_all:
        if r["transport_ok"] == "1":
            obs.setdefault((r["answerer"], kind(r["task"])), []).append(float(r["cost_usd"] or 0))
    done = {r["job_id"] for r in rows_all if r["transport_ok"] == "1" and r["frozen_sha8"] == fsha}
    jobs = [j for j in F["schedule"] if j["stage"] == a.stage and j["job_id"] not in done]
    if a.stage == "main" and not a.dry:
        ok, msg = gates_ok(base, fsha)
        if not ok:
            sys.exit(f"ABORT: gate not passed - {msg}")
        print(f"[gates] {msg}")

    est = {k: max(PRIOR[k], 1.5 * (sum(obs[k]) / len(obs[k])) if obs.get(k) else 0) for k in PRIOR}
    proj = sum(est[(j["answerer"], kind(j["task"]))] for j in jobs)
    mean_obs = {f"{k[0]}/{k[1]}": round(sum(v) / len(v), 4) for k, v in obs.items()}
    print(f"[{a.stage}] FROZEN {fsha} | pending {len(jobs)} (done {len(done)}) | spent so far ${spent0:.2f} of "
          f"${F['cap_usd']:.0f} | reserve-basis projection ${proj:.2f} | observed mean cost {mean_obs}")
    if a.dry:
        print("[dry] no calls made"); return

    clients = None if a.mock else H.make_clients()
    lock = threading.Lock()
    state = dict(spent=spent0, reserved=0.0, stopped=False)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = os.path.join(out, f"{a.stage}_{stamp}.csv")
    fh = open(path, "w", newline=""); w = csv.DictWriter(fh, fieldnames=FIELDS); w.writeheader()
    rows = []; rng = random.Random(stamp)

    def reserve(k):
        with lock:
            e = est[k]
            if state["stopped"] or state["spent"] + state["reserved"] + e > F["cap_usd"]:
                state["stopped"] = True; return None
            state["reserved"] += e; return e

    def settle(k, e, c):
        with lock:
            state["reserved"] -= e; state["spent"] += c
            v = obs.setdefault(k, []); v.append(c)
            est[k] = max(PRIOR[k], 1.5 * sum(v) / len(v))

    def one(j):
        k = (j["answerer"], kind(j["task"]))
        e = reserve(k)
        if e is None:
            return None
        mid = F["models"][j["answerer"]]["model_id"]
        prompt = F["prompts"][j["prompt_key"]]["text"]
        raw = open(os.path.join(F["stimuli_root"], j["array"], f"perm{j['perm_id']:02d}.png"), "rb").read()
        row = dict.fromkeys(FIELDS, "")
        row.update(run_id=f"S1HI-{a.stage}-{stamp}", **{f: j[f] for f in ("stage", "block", "studies", "task", "answerer",
                   "focal", "array", "rep", "perm_id", "job_id", "prompt_key")},
                   display_order=json.dumps(j["display_order"]), stimulus_sha8=hashlib.sha256(raw).hexdigest()[:8],
                   prompt_sha8=H.sha8(prompt), frozen_sha8=fsha, model_requested=mid)
        assert row["prompt_sha8"] == F["prompts"][j["prompt_key"]]["sha8"]
        assert row["stimulus_sha8"] == F["stimuli"][j["array"]]["perm_png_sha8"][str(j["perm_id"])]
        t0 = time.time(); c = 0.0
        try:
            if a.mock:
                res, err = dict(text=mock_reply(j, rng), returned=mid, response_id="mock", stop_reason="mock",
                                surface=F["models"][j["answerer"]]["surface"], settings=F["models"][j["answerer"]]["settings"],
                                echoed_effort="high", thinking_blocks=1, in_tok=900, out_tok=1500, reasoning_tok="",
                                summary=""), None
            else:
                res, err = H.P.call_with_backoff(H.ASK[j["answerer"]], clients[j["answerer"]], mid, prompt,
                                                 base64.b64encode(raw).decode())
            row.update(secs=f"{time.time()-t0:.2f}", ts_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
            if res is None:
                row.update(transport_ok=0, parse_ok=0, model_match=0, error=err); return row
            c = H.P.cost(res["in_tok"], res["out_tok"])
            pr = H.parse(j["task"], res["text"], j["display_order"])
            row.update(transport_ok=1, parse_ok=int(bool(pr)), model_returned=res["returned"],
                       model_match=int(res["returned"] == mid), request_settings=json.dumps(res["settings"]),
                       surface=res["surface"], echoed_effort=res["echoed_effort"], response_id=res["response_id"],
                       stop_reason=res["stop_reason"], thinking_blocks=res["thinking_blocks"],
                       in_tokens=res["in_tok"], out_tokens=res["out_tok"], reasoning_tokens=res["reasoning_tok"],
                       cost_usd=f"{c:.6f}", raw=res["text"][:6000], reasoning_summary=res["summary"][:6000], **pr)
            return row
        finally:
            settle(k, e, c)

    def write(r):
        with lock:
            w.writerow(r); fh.flush(); rows.append(r)

    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        for fut in as_completed([ex.submit(one, j) for j in jobs]):   # FIFO submission keeps the frozen priority
            r = fut.result()
            if r is not None:
                write(r)
    fh.close()
    summ = dict(path=path, n=len(rows), transport_ok=sum(r["transport_ok"] == 1 for r in rows),
                parsed=sum(r["parse_ok"] == 1 for r in rows),
                mismatch=sum(r["transport_ok"] == 1 and r["model_match"] == 0 for r in rows),
                cost_this_run=round(state["spent"] - spent0, 4), spent_total=round(state["spent"], 4),
                budget_stopped=state["stopped"], pending_left=len(jobs) - len(rows), frozen_sha8=fsha)
    json.dump(summ, open(path.replace(".csv", "_summary.json"), "w"), indent=1)
    print(json.dumps(summ, indent=1))
    if a.stage == "preflight":
        chk = []
        for r in rows:
            okr = (r["transport_ok"] == 1 and r["parse_ok"] == 1 and r["model_match"] == 1
                   and r["stop_reason"] not in ("max_tokens", "incomplete")
                   and (r["answerer"] != "gpt" or r["echoed_effort"] in ("high", "")))
            chk.append(dict(task=r["task"], answerer=r["answerer"], focal=r["focal"], returned=r["model_returned"],
                            surface=r["surface"], echoed_effort=r["echoed_effort"], stop=r["stop_reason"],
                            thinking_blocks=r["thinking_blocks"], in_tok=r["in_tokens"], out_tok=r["out_tokens"],
                            reasoning_tok=r["reasoning_tokens"], cost=r["cost_usd"], parsed=r["parse_ok"],
                            PASS=okr, error=r["error"]))
        n_pf = sum(1 for j in F["schedule"] if j["stage"] == "preflight")
        rep = dict(passed=all(c["PASS"] for c in chk) and len(chk) == n_pf, checks=chk)
        json.dump(rep, open(path.replace(".csv", "_REPORT.json"), "w"), indent=1)
        for c in chk:
            print(f"  {'PASS' if c['PASS'] else 'FAIL'} {c['task']:8s} {c['answerer']:6s}->{c['focal']:6s} {c['returned']} "
                  f"eff={c['echoed_effort'] or '-'} stop={c['stop']} think={c['thinking_blocks']} "
                  f"tok {c['in_tok']}/{c['out_tok']} (reasoning {c['reasoning_tok'] or '-'}) ${float(c['cost'] or 0):.4f} {c['error'] or ''}")
        print("PREFLIGHT", "PASSED" if rep["passed"] else "FAILED")


if __name__ == "__main__":
    main()
