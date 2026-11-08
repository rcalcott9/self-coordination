#!/usr/bin/env python3
"""Study 3A BASELINE runner (adapted from study3a_feasibility_20261015/code/run.py). Reads only the hash-checked frozen design.
Every attempt -> requests.jsonl; every final record (raw response, stop reason, usage, cost) -> responses.jsonl.
Budget: dispatch only if prior + run actual + outstanding reservations (token-limit bound each) + next bound <= cap.
  --dry-run / --mock / --approved ; --limit N (first N pending in frozen order) ; --concurrency K"""
import argparse, ast, asyncio, base64, glob, hashlib, json, os, random, sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
SC = Path.home() / "Desktop/Coordination/Self_Coordination"
STATUS = Path.home() / ".codex/.chatgpt-projects/g-p-6aa069d23ae08191a861f83470dbc913/review_loop/reciprocal_confidence_status.json"
ap = argparse.ArgumentParser()
for f in ("--dry-run", "--mock", "--approved"): ap.add_argument(f, action="store_true")
ap.add_argument("--limit", type=int); ap.add_argument("--concurrency", type=int, default=6)
a = ap.parse_args()
now = lambda: datetime.now(timezone.utc).isoformat(timespec="seconds")
fsha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
for f in ("FROZEN.json", "jobs.jsonl"):
    assert (HERE / "design" / (f + ".sha256")).read_text().split()[0] == fsha(HERE / "design" / f), f"{f} changed after freezing"
FZ = json.loads((HERE / "design/FROZEN.json").read_text())
jobs = sorted((json.loads(l) for l in open(HERE / "design/jobs.jsonl")), key=lambda j: j["order"])
PROMPT = {c: v["text"] for c, v in FZ["prompts"].items()}
for j in jobs:
    assert hashlib.sha256(PROMPT[j["condition"]].encode()).hexdigest()[:8] == j["prompt_sha8"]

def recompute_prior():
    """Study 3 spend recorded before this run (same raw files as the freeze)."""
    s = 0.0
    files = (glob.glob(str(SC / "study3_item_M07_20261013/basic_stag_hunt/results/*/*.jsonl")) +
             glob.glob(str(SC / "study3_item_SHAPES_20261014/results/run_20261014_002715/*.jsonl")) +
             [str(SC / "study3a_feasibility_20261015/results/pilot/responses.jsonl"), str(SC / "study3a_baseline_20261016/results/run/responses.jsonl")])
    for f in files:
        for l in open(f):
            try: r = json.loads(l)
            except json.JSONDecodeError: continue
            c = r.get("cost_usd", r.get("cost"))
            if isinstance(c, (int, float)): s += c
    return s
PRIOR = recompute_prior()
assert abs(PRIOR - FZ["budget"]["prior_cumulative_usd_recomputed"]) < 1e-4, f"prior spend changed: {PRIOR}"
CAP = FZ["budget"]["pilot_cap_usd"]; CEIL = FZ["budget"]["cumulative_ceiling_usd"]
if a.mock and os.environ.get("RC_MOCK_TEST_CAP"): CAP = float(os.environ["RC_MOCK_TEST_CAP"])   # offline test of the stop rule only

sys.path.insert(0, str(Path(__file__).resolve().parent)); import rc_parse

out = HERE / "results" / ("mock" if a.mock else "run"); out.mkdir(parents=True, exist_ok=True)
RESP, REQ, LEDGER = out / "responses.jsonl", out / "requests.jsonl", out / "run_ledger.jsonl"
done, run_spent_prior = set(), 0.0
if RESP.exists():
    for l in open(RESP):
        r = json.loads(l); done.add(r["job_key"]); run_spent_prior += r["cost_usd"]
pending = [j for j in jobs if j["job_key"] not in done]
if a.limit is not None: pending = pending[: a.limit]
print(f"jobs {len(jobs)} · final {len(done)} · pending now {len(pending)} · prior Study 3 ${PRIOR:.5f} · this pilot so far ${run_spent_prior:.4f} · pilot cap ${CAP} · ceiling ${CEIL}")
with open(LEDGER, "a") as fh:
    fh.write(json.dumps(dict(ts=now(), argv=sys.argv, mode="dry-run" if a.dry_run else "mock" if a.mock else "live" if a.approved else "refused",
                             pending=len(pending), prior=PRIOR, run_spent_prior=run_spent_prior, frozen_sha256=fsha(HERE / "design/FROZEN.json"))) + "\n")
if a.dry_run: sys.exit("[DRY RUN] verified; nothing sent")
if not (a.approved or a.mock): sys.exit("NOT LAUNCHED: live calls need --approved")

if not a.mock:
    from dotenv import load_dotenv
    load_dotenv(Path.home() / "Desktop/Coordination/LLM_Coordination/.env", override=False)
    import anthropic, openai
    OA, AN = openai.AsyncOpenAI(max_retries=0, timeout=300.0), anthropic.AsyncAnthropic(max_retries=0, timeout=300.0)
    FATAL = (openai.BadRequestError, openai.NotFoundError, openai.AuthenticationError, openai.PermissionDeniedError,
             anthropic.BadRequestError, anthropic.NotFoundError, anthropic.AuthenticationError, anthropic.PermissionDeniedError)
else:
    FATAL = ()
MR = random.Random(3)

class St:
    spent = run_spent_prior; reserved = 0.0; refusals = 0; consec_fail = 0; stop_reason = None; n_done = 0
S = St(); lock = asyncio.Lock(); wlock = asyncio.Lock(); sem = asyncio.Semaphore(a.concurrency)

async def log(path, row):
    async with wlock:
        with open(path, "a") as fh: fh.write(json.dumps(row, default=str) + "\n")

def write_status(state):
    if a.mock: return
    st = dict(run_id="study3a-reciprocal-confidence-pilot-20usd-01", state=state, updated_at=now(), frozen_manifest=str(HERE / "design/FROZEN.json"),
              responses=str(RESP), admitted_new_calls_total=len(jobs), final_records=len(done) + S.n_done,
              prior_study3_usd=round(PRIOR, 5), run_actual_usd=round(S.spent, 5), outstanding_reservations_usd=round(S.reserved, 4),
              cumulative_actual_usd=round(PRIOR + S.spent, 5), pilot_cap_usd=CAP, cumulative_ceiling_usd=CEIL, refusals=S.refusals, stop_reason=S.stop_reason)
    t = str(STATUS) + ".tmp"; Path(t).write_text(json.dumps(st, indent=1)); os.replace(t, STATUS)

async def call(j):
    M = FZ["models"][j["model"]]; img = base64.b64encode(Path(j["image_path"]).read_bytes()).decode()
    if a.mock:
        d = [MR.random() for _ in range(5)]; t = sum(d); d = dict(zip(('PASS','1','2','3','4'), [x / t for x in d])); play = MR.random() > .3
        txt = json.dumps({'own_distribution': d, 'partner_distribution': d, 'expected_points': {'PASS': 7, '1': 10*d['1'], '2': 10*d['2'], '3': 10*d['3'], '4': 10*d['4']}, 'decision': 'PLAY' if play else 'PASS', 'object': str(MR.randint(1, 4)) if play else None, 'explanation': 'mock'})
        return dict(text=txt, stop="mock", model_returned="MOCK", in_tok=800, out_tok=100, raw={"mock": True}, refusal=False)
    if M["api"] == "openai.responses":
        r = await OA.responses.create(model=M["model"], reasoning=M["reasoning"], max_output_tokens=M["max_output_tokens"],
                                      input=[{"role": "user", "content": [{"type": "input_text", "text": PROMPT[j["condition"]]},
                                                                          {"type": "input_image", "image_url": f"data:image/png;base64,{img}"}]}])
        raw = r.model_dump(mode="json")
        refusal = any(c.get("type") == "refusal" for o in raw.get("output", []) for c in (o.get("content") or []))
        return dict(text=r.output_text or "", stop=r.status, stop_details=raw.get("incomplete_details"), model_returned=r.model,
                    in_tok=r.usage.input_tokens, out_tok=r.usage.output_tokens, raw=raw, refusal=refusal)
    r = await AN.messages.create(model=M["model"], max_tokens=M["max_tokens"], thinking=M["thinking"], output_config=M["output_config"],
                                 messages=[{"role": "user", "content": [{"type": "text", "text": PROMPT[j["condition"]]},
                                           {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": img}}]}])
    raw = r.model_dump(mode="json")
    return dict(text="".join(b.text for b in r.content if b.type == "text"), stop=r.stop_reason, stop_details=raw.get("stop_details"),
                model_returned=r.model, in_tok=r.usage.input_tokens, out_tok=r.usage.output_tokens, raw=raw, refusal=r.stop_reason == "refusal")

async def one(j):
    async with sem:
        M = FZ["models"][j["model"]]; pr = M["price_per_mtok"]; b = j["bound_usd"]
        cost, res, errors = 0.0, None, []
        for att in range(1, 4):
            async with lock:
                if S.stop_reason: break
                if S.spent + S.reserved + b > CAP or PRIOR + S.spent + S.reserved + b > CEIL:
                    S.stop_reason = "budget rule: next reservation could exceed the pilot cap or cumulative ceiling"; break
                S.reserved += b
            await log(REQ, dict(ts=now(), job_key=j["job_key"], attempt=att, model=M["model"], settings={k: v for k, v in M.items() if k not in ("note",)},
                                prompt_sha8=j["prompt_sha8"], image_sha256=j["image_sha256"], perm=j["perm"], reserved_usd=b))
            charged = b                                   # if usage is unknown, the full bound stays charged
            try:
                res = await call(j)
                charged = ((res["in_tok"] or 0) * pr["input"] + (res["out_tok"] or 0) * pr["output"]) / 1e6
                cost += charged
                async with lock: S.reserved -= b; S.spent += charged
                break
            except FATAL as e:
                errors.append(dict(attempt=att, type=type(e).__name__, status=getattr(e, "status_code", None), body=str(e)[:2000], charged_usd=0.0))
                async with lock: S.reserved -= b; S.stop_reason = f"non-retryable {type(e).__name__} on {j['job_key']}"
                break
            except Exception as e:
                # possible billing without usage: keep the full bound charged
                errors.append(dict(attempt=att, type=type(e).__name__, status=getattr(e, "status_code", None), body=str(e)[:2000], charged_usd=b))
                cost += b
                async with lock: S.reserved -= b; S.spent += b
                await asyncio.sleep(2 ** att)
        if res is None and not errors: return                       # never dispatched (stop rule)
        async with lock:
            if res is None:
                S.consec_fail += 1
                if S.consec_fail >= 5 and not S.stop_reason: S.stop_reason = "5 consecutive API failures"
            else:
                S.consec_fail = 0
                if res["refusal"]:
                    S.refusals += 1
                    if S.refusals >= 3 and not S.stop_reason: S.stop_reason = "3 refusals"
        parsed, note = rc_parse.parse(res["text"]) if res else (None, "no response")
        status = "ok" if parsed else ("api_failure" if res is None else "refusal" if res["refusal"] else "invalid_response")
        slot = (parsed or {}).get("slot")
        await log(RESP, dict(ts=now(), job_key=j["job_key"], array=j["array"], model=j["model"], condition=j["condition"], role=j["role"], rep=j["rep"],
                             perm=j["perm"], slot_to_canonical=j["slot_to_canonical"], status=status, decision=(parsed or {}).get("decision"),
                             object_slot=slot, object_canonical=j["slot_to_canonical"][slot - 1] if slot else None, parse_note=note,
                             attempts=len(errors) + (1 if res else 0), errors=errors, text=(res or {}).get("text"), stop=(res or {}).get("stop"),
                             stop_details=(res or {}).get("stop_details"), model_returned=(res or {}).get("model_returned"),
                             in_tok=(res or {}).get("in_tok"), out_tok=(res or {}).get("out_tok"), cost_usd=cost, source="new (2026-10-16 reciprocal-confidence pilot)", own_distribution=(parsed or {}).get("own"), partner_distribution=(parsed or {}).get("partner"), expected_points=(parsed or {}).get("ev"), ev_note=(parsed or {}).get("ev_note"), explanation=(parsed or {}).get("explanation"),
                             raw=(res or {}).get("raw"), mock=a.mock))
        async with lock:
            S.n_done += 1
            if S.n_done % 25 == 0: write_status("running")

async def main():
    write_status("running")
    await asyncio.gather(*[one(j) for j in pending])
    rows = [json.loads(l) for l in open(RESP)] if RESP.exists() else []
    summ = dict(ts=now(), records=len(rows), by_status={s: sum(r["status"] == s for r in rows) for s in ("ok", "invalid_response", "refusal", "api_failure")},
                run_spent=round(S.spent, 5), cumulative=round(PRIOR + S.spent, 5), refusals=S.refusals, stop_reason=S.stop_reason)
    print(json.dumps(summ))
    with open(LEDGER, "a") as fh: fh.write(json.dumps(summ) + "\n")
    write_status("stopped: " + S.stop_reason if S.stop_reason else ("complete" if len(rows) >= len(jobs) else "batch finished"))

asyncio.run(main())
