#!/usr/bin/env python3
"""PD three-condition pilot runner (adapted from study3a_pass5_PROPOSED_20261016/code/run.py; text-only). Reads only the hash-checked frozen design.
Phase 1 = same_model (the response bank) + different_model. The bank is sealed once all 64 same_model records of a model exist; only then are that
model's fixed_response jobs dispatched, each after its preassigned bank response is recorded in assignments.jsonl.
Budget: dispatch only if run actual + outstanding reservations + next bound <= cap AND prior + same <= ceiling. Unknown usage keeps the full bound;
retries of API errors are new reservations; invalid replies are recorded and never resampled.
  --dry-run / --mock / --approved ; --limit N (first N pending in frozen order) ; --concurrency K"""
import argparse, asyncio, glob, hashlib, json, os, random, sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
SC = Path.home() / "Desktop/Coordination/Self_Coordination"
STATUS = Path.home() / ".codex/.chatgpt-projects/g-p-6aa069d23ae08191a861f83470dbc913/review_loop/pd_execution_status.json"
RUN_ID = "pd-three-condition-pilot-20usd-01"
ap = argparse.ArgumentParser()
for f in ("--dry-run", "--mock", "--approved"): ap.add_argument(f, action="store_true")
ap.add_argument("--limit", type=int); ap.add_argument("--concurrency", type=int, default=6)
a = ap.parse_args()
now = lambda: datetime.now(timezone.utc).isoformat(timespec="seconds")
fsha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
tsha = lambda s: hashlib.sha256((s or "").encode()).hexdigest()
for f in ("FROZEN.json", "jobs.jsonl"):
    assert (HERE / "design" / (f + ".sha256")).read_text().split()[0] == fsha(HERE / "design" / f), f"{f} changed after freezing"
FZ = json.loads((HERE / "design/FROZEN.json").read_text())
jobs = sorted((json.loads(l) for l in open(HERE / "design/jobs.jsonl")), key=lambda j: j["order"])
PROMPT = {k: v["text"] for k, v in FZ["prompts"].items()}
for j in jobs:
    assert tsha(PROMPT[j["prompt_key"]])[:8] == j["prompt_sha8"]
    M = FZ["models"][j["model"]]; pr = M["price_per_mtok"]
    # token-limit bound: input tokens <= characters; output <= max tokens
    j["bound_usd"] = round((len(PROMPT[j["prompt_key"]]) * pr["input"] + M["max_out"] * pr["output"]) / 1e6, 6)

def recompute_prior():
    """Study 3 spend recorded before this run (same raw files as the PASS=5 freeze, plus the PASS=5 run)."""
    s = 0.0
    files = (glob.glob(str(SC / "study3_item_M07_20261013/basic_stag_hunt/results/*/*.jsonl")) +
             glob.glob(str(SC / "study3_item_SHAPES_20261014/results/run_20261014_002715/*.jsonl")) +
             [str(SC / "study3a_feasibility_20261015/results/pilot/responses.jsonl"), str(SC / "study3a_baseline_20261016/results/run/responses.jsonl"),
              str(SC / "study3a_reciprocal_confidence_20261016/results/run/responses.jsonl"), str(SC / "study3a_pass5_PROPOSED_20261016/results/run/responses.jsonl")])
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
if a.mock and os.environ.get("PD_MOCK_TEST_CAP"): CAP = float(os.environ["PD_MOCK_TEST_CAP"])   # offline test of the stop rule only

sys.path.insert(0, str(Path(__file__).resolve().parent)); import pd_parse

out = HERE / "results" / ("mock" if a.mock else "run"); out.mkdir(parents=True, exist_ok=True)
RESP, REQ, LEDGER, ASSIGN, BANK = out / "responses.jsonl", out / "requests.jsonl", out / "run_ledger.jsonl", out / "assignments.jsonl", out / "bank_sealed.json"
records, run_spent_prior = {}, 0.0
if RESP.exists():
    for l in open(RESP):
        r = json.loads(l); records[r["job_key"]] = r; run_spent_prior += r["cost_usd"]
pending = [j for j in jobs if j["job_key"] not in records]
if a.limit is not None: pending = pending[: a.limit]
print(f"jobs {len(jobs)} · final {len(records)} · pending now {len(pending)} · prior Study 3 ${PRIOR:.5f} · this pilot so far ${run_spent_prior:.4f} · cap ${CAP} · ceiling ${CEIL}")
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
    st = dict(run_id=RUN_ID, state=state, updated_at=now(), frozen_manifest=str(HERE / "design/FROZEN.json"), responses=str(RESP),
              admitted_new_calls_total=len(jobs), final_records=len(records), prior_study3_usd=round(PRIOR, 5), run_actual_usd=round(S.spent, 5),
              outstanding_reservations_usd=round(S.reserved, 4), cumulative_actual_usd=round(PRIOR + S.spent, 5), pilot_cap_usd=CAP,
              cumulative_ceiling_usd=CEIL, refusals=S.refusals, bank_sealed=BANK.exists(), stop_reason=S.stop_reason)
    t = str(STATUS) + ".tmp"; Path(t).write_text(json.dumps(st, indent=1)); os.replace(t, STATUS)

async def call(j):
    M = FZ["models"][j["model"]]; text = PROMPT[j["prompt_key"]]
    if a.mock:
        act = "A" if MR.random() < .5 else "B"
        return dict(text=json.dumps({"action": act, "reason": "mock"}) if MR.random() > .03 else "mock garbage", stop="mock", model_returned="MOCK",
                    in_tok=330, out_tok=200, raw={"mock": True}, refusal=False)
    if M["api"] == "openai.responses":
        r = await OA.responses.create(model=M["model"], reasoning=M["reasoning"], max_output_tokens=M["max_output_tokens"],
                                      input=[{"role": "user", "content": [{"type": "input_text", "text": text}]}])
        raw = r.model_dump(mode="json")
        refusal = any(c.get("type") == "refusal" for o in raw.get("output", []) for c in (o.get("content") or []))
        return dict(text=r.output_text or "", stop=r.status, stop_details=raw.get("incomplete_details"), model_returned=r.model,
                    in_tok=r.usage.input_tokens, out_tok=r.usage.output_tokens, raw=raw, refusal=refusal)
    r = await AN.messages.create(model=M["model"], max_tokens=M["max_tokens"], thinking=M["thinking"], output_config=M["output_config"],
                                 messages=[{"role": "user", "content": [{"type": "text", "text": text}]}])
    raw = r.model_dump(mode="json")
    return dict(text="".join(b.text for b in r.content if b.type == "text"), stop=r.stop_reason, stop_details=raw.get("stop_details"),
                model_returned=r.model, in_tok=r.usage.input_tokens, out_tok=r.usage.output_tokens, raw=raw, refusal=r.stop_reason == "refusal")

def seal_bank():
    """Seal each model's same_model bank once all 64 records exist. Returns set of models whose bank is sealed."""
    bank = json.loads(BANK.read_text()) if BANK.exists() else {}
    for mo in FZ["models"]:
        if mo in bank: continue
        keys = [j["job_key"] for j in jobs if j["model"] == mo and j["condition"] == "same_model"]
        if all(k in records for k in keys):
            bank[mo] = dict(sealed_at=now(), responses={k: dict(status=records[k]["status"], action_label=records[k]["action_label"],
                            action_canonical=records[k]["action_canonical"], text_sha256=tsha(records[k]["text"])) for k in keys})
    if bank:
        BANK.write_text(json.dumps(bank, indent=1))
        (out / "bank_sealed.json.sha256").write_text(fsha(BANK) + "  bank_sealed.json\n")
    return set(bank), bank

async def one(j, bank=None):
    async with sem:
        M = FZ["models"][j["model"]]; pr = M["price_per_mtok"]; b = j["bound_usd"]
        cost, res, errors = 0.0, None, []
        if j["condition"] == "fixed_response":                       # record assigned bank response before the call
            bk = j["bank_assignment"]; br = bank[j["model"]]["responses"][bk]
            assert bk != j["job_key"] and records[bk]["mapping"] == j["mapping"]
            await log(ASSIGN, dict(ts=now(), job_key=j["job_key"], bank_job_key=bk, bank_status=br["status"], bank_action_label=br["action_label"],
                                   bank_action_canonical=br["action_canonical"], bank_text_sha256=br["text_sha256"], disclosed_to_focal=False))
        for att in range(1, 4):
            async with lock:
                if S.stop_reason: break
                if S.spent + S.reserved + b > CAP or PRIOR + S.spent + S.reserved + b > CEIL:
                    S.stop_reason = "budget rule: next reservation could exceed the pilot cap or cumulative ceiling"; break
                S.reserved += b
            await log(REQ, dict(ts=now(), job_key=j["job_key"], attempt=att, model=M["model"], settings={k: v for k, v in M.items() if k != "note"},
                                prompt_key=j["prompt_key"], prompt_sha8=j["prompt_sha8"], mapping=j["mapping"], reserved_usd=b))
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
            except Exception as e:                                    # possible billing without usage: keep the full bound charged
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
        parsed, note = pd_parse.parse(res["text"]) if res else (None, "no response")
        status = "ok" if parsed else ("api_failure" if res is None else "refusal" if res["refusal"] else "invalid_response")
        lab = (parsed or {}).get("action")
        row = dict(ts=now(), job_key=j["job_key"], model=j["model"], condition=j["condition"], rep=j["rep"], mapping=j["mapping"],
                   label_to_canonical=j["label_to_canonical"], partner_job_key=j["partner_job_key"], bank_assignment=j.get("bank_assignment"),
                   format_check=j["format_check"], status=status, action_label=lab, action_canonical=j["label_to_canonical"][lab] if lab else None,
                   reason=(parsed or {}).get("reason"), parse_note=note, attempts=len(errors) + (1 if res else 0), errors=errors,
                   text=(res or {}).get("text"), stop=(res or {}).get("stop"), stop_details=(res or {}).get("stop_details"),
                   model_returned=(res or {}).get("model_returned"), in_tok=(res or {}).get("in_tok"), out_tok=(res or {}).get("out_tok"),
                   cost_usd=cost, source="new (2026-10-17 PD three-condition pilot)", raw=(res or {}).get("raw"), mock=a.mock)
        await log(RESP, row)
        async with lock:
            records[j["job_key"]] = row; S.n_done += 1
            if S.n_done % 25 == 0: write_status("running")

async def main():
    write_status("running")
    p1 = [j for j in pending if j["phase"] == 1]; p2 = [j for j in pending if j["phase"] == 2]
    await asyncio.gather(*[one(j) for j in p1])
    sealed, bank = seal_bank()
    if p2 and not S.stop_reason:
        ready = [j for j in p2 if j["model"] in sealed]
        if len(ready) < len(p2): print(f"fixed_response held back for models without a sealed bank: {sorted({j['model'] for j in p2} - sealed)}")
        write_status("running: bank sealed; fixed_response phase")
        await asyncio.gather(*[one(j, bank) for j in ready])
    rows = list(records.values())
    summ = dict(ts=now(), records=len(rows), by_status={s: sum(r["status"] == s for r in rows) for s in ("ok", "invalid_response", "refusal", "api_failure")},
                run_spent=round(S.spent, 5), cumulative=round(PRIOR + S.spent, 5), refusals=S.refusals, bank_sealed=sorted(sealed), stop_reason=S.stop_reason)
    print(json.dumps(summ))
    with open(LEDGER, "a") as fh: fh.write(json.dumps(summ) + "\n")
    write_status("stopped: " + S.stop_reason if S.stop_reason else ("complete" if len(rows) >= len(jobs) else "batch finished"))

asyncio.run(main())
