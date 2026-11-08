"""Study 1 frontier minimal collection - single runner for every stage.

  /opt/anaconda3/bin/python code/run.py --stage preflight --cap 1   [--dry]
  stages: preflight | pilot | anchor | main

Refuses to run unless FROZEN.json matches its .sha256, and this file, prompts.py and
pc_common.py match the code hashes frozen inside it. Request kwargs mirror the calibration
frame run (pc_common.ask_gpt / ask_claude) exactly; the D-017 thinking-off assertions are
reused from pc_common. Every raw reply and full provenance is logged per row. Parse
failures are never defaulted. Resume-safe on (stage, task, focal, array, rep).
"""
import argparse, base64, csv, datetime, hashlib, json, os, platform, re, sys, threading, time
from concurrent.futures import ThreadPoolExecutor, as_completed

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SC = os.path.dirname(ROOT)
SPC = os.path.join(SC, "study_policy_convergence_20260909")
sys.path.insert(0, os.path.join(SPC, "runners"))
import pc_common as P                                                  # noqa: E402

FROZEN = os.path.join(ROOT, "design", "FROZEN.json")
FIELDS = ["run_id", "stage", "task", "focal", "answerer", "array", "rep", "perm_id",
          "display_order", "stimulus_sha8", "prompt_key", "prompt_sha8", "frozen_sha8",
          "code_sha8", "model_requested", "model_returned", "model_match", "request_settings",
          "surface", "response_id", "stop_reason", "thinking_blocks", "transport_ok",
          "parse_ok", "slot_returned", "canonical_choice", "decision", "match_probability",
          "in_tokens", "out_tokens", "reasoning_tokens", "cost_usd", "secs", "ts_utc",
          "error", "raw", "reasoning_summary"]

DEC = re.compile(r"DECISION:\s*[\s*_`\"'\[\(]*(PLAY|PASS)\b", re.I)
PROB = re.compile(r"MATCH_PROBABILITY:\s*[\s*_`\"'\[\(]*(\d{1,3})(?![0-9])", re.I)


def sha256f(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def verify_frozen():
    want = open(FROZEN.replace(".json", ".sha256")).read().split()[0]
    got = sha256f(FROZEN)
    if got != want:
        sys.exit(f"ABORT: FROZEN.json sha256 {got[:16]} != frozen {want[:16]}")
    F = json.load(open(FROZEN))
    live = {"run.py": __file__, "prompts.py": os.path.join(HERE, "prompts.py"),
            "pc_common.py": os.path.join(SPC, "runners", "pc_common.py")}
    for k, p in live.items():
        if sha256f(p)[:8] != F["code_sha8"][k]:
            sys.exit(f"ABORT: {k} changed since freeze ({sha256f(p)[:8]} != {F['code_sha8'][k]})")
    return F, got[:8]


def ask_gpt(client, model, prompt, img):
    kw = dict(model=model, reasoning={"effort": "low", "summary": "auto"},
              input=[{"role": "user", "content": [
                  {"type": "input_text", "text": prompt},
                  {"type": "input_image", "image_url": f"data:image/png;base64,{img}"}]}])
    r = client.responses.create(**kw)
    summ = []
    for it in r.output or []:
        if getattr(it, "type", "") == "reasoning":
            for s in getattr(it, "summary", None) or []:
                summ.append(getattr(s, "text", ""))
    u = r.usage
    det = getattr(u, "output_tokens_details", None)
    return dict(text=r.output_text or "", returned=r.model, response_id=r.id,
                stop_reason=getattr(r, "status", ""), thinking_blocks=0,
                surface="reasoning.effort=low", settings={"reasoning": {"effort": "low", "summary": "auto"}},
                in_tok=u.input_tokens, out_tok=u.output_tokens,
                reasoning_tok=getattr(det, "reasoning_tokens", "") if det else "",
                summary=" ".join(summ))


def ask_claude(client, model, prompt, img):
    kw = dict(model=model, max_tokens=1024, thinking={"type": "disabled"},
              messages=[{"role": "user", "content": [
                  {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": img}},
                  {"type": "text", "text": prompt}]}])
    P.assert_thinking_off(kw)
    r = client.messages.create(**kw)
    P.check_no_thinking_block(r.content)
    txt = "".join(b.text for b in r.content if getattr(b, "type", "") == "text")
    return dict(text=txt, returned=r.model, response_id=r.id, stop_reason=r.stop_reason,
                thinking_blocks=0, surface="thinking=disabled",
                settings={"thinking": {"type": "disabled"}, "max_tokens": 1024},
                in_tok=r.usage.input_tokens, out_tok=r.usage.output_tokens,
                reasoning_tok="", summary="")


ASK = {"gpt": ask_gpt, "claude": ask_claude}


def parse(task, txt, order):
    if task == "CALIB":
        s = P.parse_slot(txt)
        return {} if s is None else {"slot_returned": s, "canonical_choice": order[s]}
    if task == "PLAYPASS":
        m = DEC.findall(txt or "")
        return {"decision": m[-1].upper()} if m else {}
    m = PROB.findall(txt or "")
    if not m or not 0 <= int(m[-1]) <= 100:
        return {}
    return {"match_probability": int(m[-1])}


def preflight_report(rows, F, path):
    chk = []
    for r in rows:
        ok = (r["transport_ok"] == 1 and r["parse_ok"] == 1 and r["model_match"] == 1
              and r["thinking_blocks"] == 0
              and r["stimulus_sha8"] == F["stimuli"][r["array"]]["perm_png_sha8"][str(r["perm_id"])])
        chk.append(dict(task=r["task"], answerer=r["answerer"], focal=r["focal"],
                        requested=r["model_requested"], returned=r["model_returned"],
                        surface=r["surface"], parsed=r["parse_ok"],
                        value=r["canonical_choice"] if r["task"] == "CALIB" else r["decision"] or r["match_probability"],
                        stop_reason=r["stop_reason"], in_tok=r["in_tokens"], out_tok=r["out_tokens"],
                        cost=r["cost_usd"], PASS=ok, error=r["error"]))
    rep = dict(passed=all(c["PASS"] for c in chk) and len(chk) == 8, checks=chk,
               python=platform.python_version())
    json.dump(rep, open(path, "w"), indent=1)
    return rep


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", required=True, choices=["preflight", "pilot", "anchor", "main"])
    ap.add_argument("--cap", type=float, required=True)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()
    F, fsha = verify_frozen()
    code8 = json.dumps(F["code_sha8"], sort_keys=True)
    out = os.path.join(ROOT, "runs", a.stage); os.makedirs(out, exist_ok=True)
    done = set()
    for f in os.listdir(out):
        if f.endswith(".csv"):
            for r in csv.DictReader(open(os.path.join(out, f))):
                if r["transport_ok"] == "1":
                    done.add((r["task"], r["focal"], r["array"], int(r["rep"])))
    jobs = [j for j in F["schedule"] if j["stage"] == a.stage
            and (j["task"], j["focal"], j["array"], j["rep"]) not in done]
    RATE = {"gpt": 0.0115, "claude": 0.0063}       # measured per-call, pessimistic 5/30
    est = sum(RATE[j["answerer"]] for j in jobs)
    print(f"[{a.stage}] FROZEN {fsha} | {len(jobs)} calls (skipping {len(done)} done) | est ${est:.2f} cap ${a.cap:.2f}")
    if est > a.cap:
        sys.exit("ABORT: estimate exceeds cap")
    if a.dry:
        for j in jobs[:8]:
            print("  ", {k: j[k] for k in ("task", "focal", "answerer", "array", "rep", "perm_id", "prompt_key")})
        print("[dry] no calls made"); return
    clients = P.make_clients()
    budget = P.Budget(a.cap)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = os.path.join(out, f"{a.stage}_{stamp}.csv")
    fh = open(path, "w", newline=""); w = csv.DictWriter(fh, fieldnames=FIELDS); w.writeheader()
    lock = threading.Lock(); rows = []

    def one(j):
        if not budget.ok():
            return None
        mid = F["models"][j["answerer"]]["model_id"]
        prompt = F["prompts"][j["prompt_key"]]["text"]
        pp = os.path.join(F["stimuli_root"], j["array"], f"perm{j['perm_id']:02d}.png")
        raw = open(pp, "rb").read()
        row = dict.fromkeys(FIELDS, "")
        row.update(run_id=f"S1FMIN-{a.stage}-{stamp}", stage=a.stage, task=j["task"], focal=j["focal"],
                   answerer=j["answerer"], array=j["array"], rep=j["rep"], perm_id=j["perm_id"],
                   display_order=json.dumps(j["display_order"]),
                   stimulus_sha8=hashlib.sha256(raw).hexdigest()[:8], prompt_key=j["prompt_key"],
                   prompt_sha8=hashlib.sha256(prompt.encode()).hexdigest()[:8],
                   frozen_sha8=fsha, code_sha8=code8, model_requested=mid, thinking_blocks=0)
        assert row["prompt_sha8"] == F["prompts"][j["prompt_key"]]["sha8"]
        t0 = time.time()
        res, err = P.call_with_backoff(ASK[j["answerer"]], clients[j["answerer"]], mid, prompt,
                                       base64.b64encode(raw).decode())
        row.update(secs=f"{time.time()-t0:.2f}",
                   ts_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
        if res is None:
            row.update(transport_ok=0, parse_ok=0, model_match=0, error=err); return row
        c = P.cost(res["in_tok"], res["out_tok"]); budget.add(c)
        pr = parse(j["task"], res["text"], j["display_order"])
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
    spent = sum(float(r["cost_usd"] or 0) for r in rows)
    summ = dict(path=path, n=len(rows), ok=sum(r["transport_ok"] == 1 for r in rows),
                parsed=sum(r["parse_ok"] == 1 for r in rows),
                mismatch=sum(r["transport_ok"] == 1 and r["model_match"] == 0 for r in rows),
                cost_usd=round(spent, 4), frozen_sha8=fsha, budget_stopped=budget.stopped)
    json.dump(summ, open(path.replace(".csv", "_summary.json"), "w"), indent=1)
    print(json.dumps(summ, indent=1))
    if a.stage == "preflight":
        rep = preflight_report(rows, F, path.replace(".csv", "_REPORT.json"))
        for c in rep["checks"]:
            print(f"  {'PASS' if c['PASS'] else 'FAIL'}  {c['task']:8s} answerer={c['answerer']:6s} "
                  f"returned={c['returned']} {c['surface']} value={c['value']} "
                  f"tok={c['in_tok']}/{c['out_tok']} {c['error'] or ''}")
        print("PREFLIGHT", "PASSED" if rep["passed"] else "FAILED")


if __name__ == "__main__":
    main()
