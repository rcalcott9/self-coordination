"""SHAPES SELF run: format check, then (only if all 8 pass) the pilot. Sequential, full logging.

Authorization (user, 2026-10-14, session 80332460): "User authorises running SHAPES SELF now. Hard cap:
$2 total for this run, including format checks." Format check 2 action + 2 prediction per model; if all
8 pass, 40 fresh action + 20 fresh prediction calls per model. No fixed-partner pilot.

- Models/settings as agreed (Study 1/2 surfaces): GPT-5.5 reasoning effort low, summary auto;
  Opus 5 adaptive thinking (display summarized), output_config effort low, max_tokens 4000.
- GPT output cap: max_output_tokens = 4000 is added ONLY so a call has a finite maximum cost for the
  budget rule (no prior cap existed). Prior GPT replies used 77-437 tokens. Hitting it = format failure.
- Format-check slots use seeds "fc_action"/"fc_prediction"; pilot slots use "action"/"prediction"
  (the slots in manifest_PROPOSED.jsonl, hash-checked). Separate output files.
- Stops (no further calls) on: refusal, any API error, any unparseable/truncated reply, or when the
  next call's maximum cost (input + 4000 output tokens) exceeds the remaining budget.
- No automatic retries (max_retries=0), no prompt changes.
"""
import hashlib, json, os, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import selfplay as SP

CAP, PRIOR = 2.00, 0.04687
MAXOUT = 4000
PRICE = {"gpt-5.5": (5e-6, 30e-6), "claude-opus-5": (5e-6, 25e-6)}
GPT_ID, CLAUDE_ID = "gpt-5.5", "claude-opus-5"


def summarize(fam, r):
    """Copied from M07 run_format_check.summarize: stop reason, full usage, block types/lengths, raw."""
    raw = r.model_dump(mode="json")
    if fam == "gpt":
        blocks = [dict(type=o.get("type"), n_chars=sum(len(c.get("text") or "") for c in o.get("content") or [])
                       + sum(len(x.get("text") or "") for x in o.get("summary") or []))
                  for o in raw.get("output") or []]
        return dict(text=r.output_text or "", api_model=r.model, response_id=r.id, stop_reason=raw.get("status"),
                    incomplete_details=raw.get("incomplete_details"), usage=raw.get("usage"), blocks=blocks, raw=raw)
    blocks = [dict(type=b.get("type"), n_chars=len(b.get("text") or b.get("thinking") or ""),
                   has_signature=bool(b.get("signature")), has_data=bool(b.get("data")))
              for b in raw.get("content") or []]
    return dict(text="".join(b.get("text") or "" for b in raw.get("content") or [] if b.get("type") == "text"),
                api_model=r.model, response_id=r.id, stop_reason=raw.get("stop_reason"),
                stop_details=raw.get("stop_details"), usage=raw.get("usage"), blocks=blocks, raw=raw)


def clients():
    from dotenv import load_dotenv
    load_dotenv(os.path.expanduser("~/Desktop/Coordination/LLM_Coordination/.env"))
    from openai import OpenAI
    import anthropic
    return {"gpt-5.5": OpenAI(max_retries=0, timeout=600), "claude-opus-5": anthropic.Anthropic(max_retries=0, timeout=600)}


def ask(cl, model, prompt):
    if model == "gpt-5.5":
        r = cl[model].responses.create(model=GPT_ID, reasoning={"effort": "low", "summary": "auto"},
                                       max_output_tokens=MAXOUT,
                                       input=[{"role": "user", "content": [{"type": "input_text", "text": prompt}]}])
        return summarize("gpt", r)
    r = cl[model].messages.create(model=CLAUDE_ID, max_tokens=MAXOUT,
                                  thinking={"type": "adaptive", "display": "summarized"},
                                  output_config={"effort": "low"},
                                  messages=[{"role": "user", "content": prompt}])
    return summarize("claude", r)


def jobs(kinds, n):
    out = []
    for k, (kind, cnt) in enumerate(zip(kinds, n)):
        for i in range(cnt):
            for m in SP.MODELS:                      # interleave models
                o = SP.order(m, kind, i)
                base = kind.replace("fc_", "")
                p = (SP.action_prompt if base == "action" else SP.prediction_prompt)(m, o)
                out.append(dict(call_id=f"{m}|{kind}|{i}", model=m, kind=base, slot_kind=kind, i=i,
                                order="|".join(o), prompt=p, prompt_sha16=hashlib.sha256(p.encode()).hexdigest()[:16]))
    return out


def parse_ok(j, text):
    return (SP.parse_action(text) if j["kind"] == "action" else SP.parse_prediction(text, None)) is not None


def run_phase(name, js, cl, state, outdir):
    path = os.path.join(outdir, f"{name}_responses.jsonl")
    for j in js:
        pin, pout = PRICE[j["model"]]
        maxcost = (len(j["prompt"]) // 2) * pin + MAXOUT * pout      # chars/2 over-counts tokens
        remaining = CAP - state["spent"]
        if maxcost > remaining:
            return f"budget: next call max ${maxcost:.4f} > remaining ${remaining:.4f}"
        t0 = time.time()
        rec = dict(j, phase=name, ts=time.strftime("%Y-%m-%dT%H:%M:%S%z"))
        try:
            x = ask(cl, j["model"], j["prompt"])
            u = x["usage"]
            cost = u["input_tokens"] * pin + u["output_tokens"] * pout
            state["spent"] += cost
            rec.update(response=x.pop("text"), cost=cost, secs=round(time.time() - t0, 2), error=None, **x)
        except Exception as e:
            rec.update(response=None, error=f"{type(e).__name__}: {e}", error_body=getattr(e, "body", None),
                       status_code=getattr(e, "status_code", None), secs=round(time.time() - t0, 2))
        rec["parsed_ok"] = bool(rec["response"]) and parse_ok(j, rec["response"])
        with open(path, "a") as fh:
            fh.write(json.dumps(rec, default=str) + "\n")
        state["n"] += 1
        print(f"[{name} {state['n']}] {j['call_id']} stop={rec.get('stop_reason')} out={rec.get('usage', {}).get('output_tokens') if rec.get('usage') else None} "
              f"ok={rec['parsed_ok']} ${rec.get('cost', 0):.4f} spent=${state['spent']:.4f} {rec['error'] or ''}", flush=True)
        if rec["error"]:
            return f"API error on {j['call_id']}: {rec['error']}"
        if rec.get("stop_reason") == "refusal":
            return f"refusal on {j['call_id']}: {rec.get('stop_details')}"
        if rec.get("stop_reason") not in ("end_turn", "completed"):
            return f"stop_reason {rec.get('stop_reason')} on {j['call_id']}"
        if not rec["parsed_ok"]:
            return f"format failure on {j['call_id']}: {rec['response']!r}"
    return None


def main():
    out = os.path.join(SP.HERE, "results", f"run_{time.strftime('%Y%m%d_%H%M%S')}")
    os.makedirs(out)
    man = {json.loads(l)["call_id"]: json.loads(l)["prompt_sha16"] for l in open(os.path.join(SP.HERE, "manifest_PROPOSED.jsonl"))}
    fc = jobs(["fc_action", "fc_prediction"], [2, 2])
    pilot = jobs(["action", "prediction"], [40, 20])
    assert len(fc) == 8 and len(pilot) == 120
    assert all(man[j["call_id"]] == j["prompt_sha16"] for j in pilot), "pilot prompts differ from manifest"
    assert not ({j["call_id"] for j in fc} & {j["call_id"] for j in pilot})
    cl = clients()
    state = dict(spent=0.0, n=0)
    log = dict(cap=CAP, prior_spend=PRIOR, max_output_tokens=MAXOUT)
    stop = run_phase("format_check", fc, cl, state, out)
    log["format_check"] = dict(stop=stop, spent=state["spent"])
    if stop is None:
        stop = run_phase("pilot", pilot, cl, state, out)
        log["pilot"] = dict(stop=stop, spent=state["spent"] - log["format_check"]["spent"])
    log.update(stop=stop, run_spend=state["spent"], cumulative=PRIOR + state["spent"], n_calls=state["n"])
    json.dump(log, open(os.path.join(out, "run_log.json"), "w"), indent=1)
    print(json.dumps(log, indent=1))
    print("->", out)


def resume(run_dir):
    """2026-10-14 resume after the parser amendment (user-directed): send only the outstanding Opus
    format-check prediction (claude-opus-5|fc_prediction|1); if it passes, the pilot. Same run dir,
    same $2 cap with the original run's spend carried over. Original files are never rewritten."""
    prior_log = json.load(open(os.path.join(run_dir, "run_log.json")))
    done = {json.loads(l)["call_id"] for l in open(os.path.join(run_dir, "format_check_responses.jsonl"))}
    fc = [j for j in jobs(["fc_action", "fc_prediction"], [2, 2]) if j["call_id"] not in done]
    assert [j["call_id"] for j in fc] == ["claude-opus-5|fc_prediction|1"], fc
    man = {json.loads(l)["call_id"]: json.loads(l)["prompt_sha16"] for l in open(os.path.join(SP.HERE, "manifest_PROPOSED.jsonl"))}
    pilot = jobs(["action", "prediction"], [40, 20])
    assert all(man[j["call_id"]] == j["prompt_sha16"] for j in pilot)
    assert not os.path.exists(os.path.join(run_dir, "pilot_responses.jsonl"))
    cl = clients()
    state = dict(spent=prior_log["run_spend"], n=prior_log["n_calls"])
    log = dict(cap=CAP, prior_spend=PRIOR, max_output_tokens=MAXOUT, resumed_from_spend=state["spent"],
               parser="selfplay.py with 2026-10-14 (label) amendment")
    stop = run_phase("format_check_resume", fc, cl, state, run_dir)
    log["format_check_resume"] = dict(stop=stop, spent=state["spent"] - log["resumed_from_spend"])
    if stop is None:
        s0 = state["spent"]
        stop = run_phase("pilot", pilot, cl, state, run_dir)
        log["pilot"] = dict(stop=stop, spent=state["spent"] - s0)
    log.update(stop=stop, run_spend=state["spent"], cumulative=PRIOR + state["spent"], n_calls=state["n"])
    json.dump(log, open(os.path.join(run_dir, "resume_log.json"), "x"), indent=1)
    print(json.dumps(log, indent=1))


def resume_concurrent(run_dir, workers=5, inflight_reserve=1):
    """2026-10-14 (user: "send 4-6 calls at once"): continue the pilot with `workers` concurrent calls.
    Same prompts, slots, settings, logging and stop rules. Completed pilot slots are never re-sent.
    Budget: recorded spend across all phase files, plus the maximum cost of `inflight_reserve` call(s)
    that may have been in flight when the sequential process was stopped (sent, possibly billed, never
    recorded). Before each dispatch the call's maximum cost is reserved; nothing is dispatched unless
    recorded + reserved + that maximum <= CAP. After any stop condition no new call is dispatched;
    calls already in flight finish and are recorded."""
    import threading
    from concurrent.futures import ThreadPoolExecutor, FIRST_COMPLETED, wait
    files = ["format_check_responses.jsonl", "format_check_resume_responses.jsonl", "pilot_responses.jsonl"]
    recs = [json.loads(l) for f in files for l in open(os.path.join(run_dir, f))]
    spent = sum(r.get("cost") or 0 for r in recs)
    done = {r["call_id"] for r in recs if r["phase"] == "pilot"}
    man = {json.loads(l)["call_id"]: json.loads(l)["prompt_sha16"] for l in open(os.path.join(SP.HERE, "manifest_PROPOSED.jsonl"))}
    todo = [j for j in jobs(["action", "prediction"], [40, 20]) if j["call_id"] not in done]
    assert all(man[j["call_id"]] == j["prompt_sha16"] for j in todo)
    ghost = inflight_reserve * (2000 * 5e-6 + MAXOUT * 30e-6)       # unrecorded in-flight call(s), max cost
    state = dict(spent=spent, reserved=0.0, stop=None, n=len(recs))
    print(f"resume_concurrent: {len(done)} pilot calls done, {len(todo)} to send, recorded spend ${spent:.5f}, "
          f"in-flight reserve ${ghost:.4f}, workers {workers}", flush=True)
    lock = threading.Lock()
    cl = clients()
    path = os.path.join(run_dir, "pilot_responses.jsonl")

    def one(j, maxcost):
        pin, pout = PRICE[j["model"]]
        t0 = time.time()
        rec = dict(j, phase="pilot", dispatch="concurrent", ts=time.strftime("%Y-%m-%dT%H:%M:%S%z"))
        try:
            x = ask(cl, j["model"], j["prompt"])
            u = x["usage"]
            rec.update(response=x.pop("text"), cost=u["input_tokens"] * pin + u["output_tokens"] * pout,
                       secs=round(time.time() - t0, 2), error=None, **x)
        except Exception as e:
            rec.update(response=None, cost=None, error=f"{type(e).__name__}: {e}", error_body=getattr(e, "body", None),
                       status_code=getattr(e, "status_code", None), secs=round(time.time() - t0, 2))
        rec["parsed_ok"] = bool(rec["response"]) and parse_ok(j, rec["response"])
        with lock:
            state["reserved"] -= maxcost
            state["spent"] += rec["cost"] or 0
            state["n"] += 1
            with open(path, "a") as fh:
                fh.write(json.dumps(rec, default=str) + "\n")
            why = None
            if rec["error"]:
                why = f"API error on {j['call_id']}: {rec['error']}"
            elif rec.get("stop_reason") == "refusal":
                why = f"refusal on {j['call_id']}: {rec.get('stop_details')}"
            elif rec.get("stop_reason") not in ("end_turn", "completed"):
                why = f"stop_reason {rec.get('stop_reason')} on {j['call_id']}"
            elif not rec["parsed_ok"]:
                why = f"invalid output on {j['call_id']}: {rec['response']!r}"
            if why and not state["stop"]:
                state["stop"] = why
            print(f"[pilot {state['n']}] {j['call_id']} stop={rec.get('stop_reason')} ok={rec['parsed_ok']} "
                  f"{rec['secs']}s ${rec['cost'] or 0:.4f} spent=${state['spent']:.4f} {rec['error'] or ''}", flush=True)

    with ThreadPoolExecutor(workers) as ex:
        pending, queue = set(), list(todo)
        while queue or pending:
            while queue and len(pending) < workers and not state["stop"]:
                j = queue[0]
                pin, pout = PRICE[j["model"]]
                maxcost = (len(j["prompt"]) // 2) * pin + MAXOUT * pout
                with lock:
                    if state["spent"] + state["reserved"] + ghost + maxcost > CAP:
                        state["stop"] = state["stop"] or f"budget: next call max ${maxcost:.4f} exceeds remaining"
                        break
                    state["reserved"] += maxcost
                queue.pop(0)
                pending.add(ex.submit(one, j, maxcost))
            if not pending:
                break
            finished, pending = wait(pending, return_when=FIRST_COMPLETED)
            pending = set(pending)
            if state["stop"]:
                queue = []
    log = dict(cap=CAP, prior_spend=PRIOR, workers=workers, inflight_reserve=ghost, stop=state["stop"],
               run_spend_recorded=state["spent"], cumulative_recorded=PRIOR + state["spent"],
               pilot_done=len({json.loads(l)["call_id"] for l in open(path)}), n_records=state["n"])
    json.dump(log, open(os.path.join(run_dir, "resume_concurrent_log.json"), "x"), indent=1)
    print(json.dumps(log, indent=1))


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--resume-concurrent":
        resume_concurrent(sys.argv[2])
    elif len(sys.argv) > 2 and sys.argv[1] == "--resume":
        resume(sys.argv[2])
    else:
        main()
