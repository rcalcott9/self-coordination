#!/usr/bin/env python3
"""Study 3A feasibility pilot runner. Reads only design/FROZEN.json + design/jobs.jsonl (hash-checked).
Logs every attempt (requests.jsonl) and every reply with raw response, stop reason, usage and cost (responses.jsonl).
Budget guard reserves a conservative per-call estimate before dispatch and reconciles on completion.
  --dry-run   verify hashes, print counts and projected cost, send nothing
  --mock      offline pipeline test (writes to results/mock/)
  --approved  live calls
"""
import argparse, ast, asyncio, base64, hashlib, json, random, sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
ap = argparse.ArgumentParser()
ap.add_argument("--dry-run", action="store_true"); ap.add_argument("--mock", action="store_true")
ap.add_argument("--approved", action="store_true"); ap.add_argument("--concurrency", type=int, default=4)
a = ap.parse_args()
now = lambda: datetime.now(timezone.utc).isoformat()
fsha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
for f in ("FROZEN.json", "jobs.jsonl"):
    assert (HERE / "design" / (f + ".sha256")).read_text().split()[0] == fsha(HERE / "design" / f), f"{f} changed after freezing"
FZ = json.loads((HERE / "design/FROZEN.json").read_text())
jobs = sorted((json.loads(l) for l in open(HERE / "design/jobs.jsonl")), key=lambda j: j["order"])
PROMPT = {c: v["text"] for c, v in FZ["prompts"].items()}
for j in jobs:
    assert hashlib.sha256(PROMPT[j["condition"]].encode()).hexdigest()[:8] == j["prompt_sha8"]
    assert fsha(j["image_path"]) == j["image_sha256"], j["job_key"]

# historical parser, loaded read-only (function defs + the two regex globals; no module execution)
src = Path(FZ["parsing"].split("(")[1].split(")")[0])
src = Path.home() / "Desktop/Superrationality/Stag" / src if not src.is_absolute() else src
tree = ast.parse(src.read_text()); ns = {"json": json, "re": __import__("re")}
for node in tree.body:
    if (isinstance(node, ast.FunctionDef) and node.name == "parse_game") or \
       (isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") in ("_JSON",)):
        exec(compile(ast.Module([node], []), str(src), "exec"), ns)
parse_game = ns["parse_game"]

out = HERE / "results" / ("mock" if a.mock else "pilot"); out.mkdir(parents=True, exist_ok=True)
RESP, REQ, LEDGER = out / "responses.jsonl", out / "requests.jsonl", out / "run_ledger.jsonl"
done, spent_prior = set(), 0.0
if RESP.exists():
    for l in open(RESP):
        r = json.loads(l); done.add(r["job_key"]); spent_prior += r["cost_usd"]
pending = [j for j in jobs if j["job_key"] not in done]
CAP, CUM_CAP, CUM_PRIOR = FZ["caps"]["run_hard_cap_usd"], FZ["caps"]["cumulative_cap_usd"], FZ["caps"]["cumulative_prior_usd"]
EST = {"GPT-5.5": 0.0241 * 1.5, "Claude Opus 5": 0.0104 * 1.5}       # 1.5 x max observed per game call in the source run
proj = sum(EST[j["model"]] for j in pending)
print(f"jobs {len(jobs)} · final {len(done)} · pending {len(pending)} · spent ${spent_prior:.4f} · "
      f"conservative projection for pending ${proj:.2f} · run cap ${CAP} · cumulative ${CUM_PRIOR:.2f}+run <= ${CUM_CAP}")
with open(LEDGER, "a") as fh:
    fh.write(json.dumps(dict(ts=now(), argv=sys.argv, mode="dry-run" if a.dry_run else "mock" if a.mock else "live" if a.approved else "refused",
                             pending=len(pending), spent_prior=spent_prior, frozen_sha256=fsha(HERE / "design/FROZEN.json"))) + "\n")
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
MR = random.Random(1)

class State:
    spent, reserved, refusals, consec_fail, stop_reason = spent_prior, 0.0, 0, 0, None
S = State(); lock = asyncio.Lock(); wlock = asyncio.Lock(); sem = asyncio.Semaphore(a.concurrency)

async def log(path, row):
    async with wlock:
        with open(path, "a") as fh: fh.write(json.dumps(row, default=str) + "\n")

async def call(j):
    M = FZ["models"][j["model"]]; img = base64.b64encode(Path(j["image_path"]).read_bytes()).decode()
    if a.mock:
        txt = '{"decision":"PASS","object":null}' if MR.random() < .4 else json.dumps({"decision": "PLAY", "object": str(MR.randint(1, 4))})
        return dict(text=txt, stop="mock", model_returned="MOCK", in_tok=0, out_tok=0, raw={"mock": True}, refusal=False)
    if M["api"] == "openai.responses":
        r = await OA.responses.create(model=M["model"], reasoning=M["reasoning"], input=[{"role": "user", "content": [
            {"type": "input_text", "text": PROMPT[j["condition"]]},
            {"type": "input_image", "image_url": f"data:image/png;base64,{img}"}]}])
        raw = r.model_dump(mode="json")
        refusal = any(c.get("type") == "refusal" for o in raw.get("output", []) for c in (o.get("content") or []))
        return dict(text=r.output_text or "", stop=r.status, incomplete=raw.get("incomplete_details"), model_returned=r.model,
                    in_tok=r.usage.input_tokens, out_tok=r.usage.output_tokens, raw=raw, refusal=refusal)
    r = await AN.messages.create(model=M["model"], max_tokens=M["max_tokens"], thinking=M["thinking"], output_config=M["output_config"],
                                 messages=[{"role": "user", "content": [{"type": "text", "text": PROMPT[j["condition"]]},
                                           {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": img}}]}])
    raw = r.model_dump(mode="json")
    return dict(text="".join(b.text for b in r.content if b.type == "text"), stop=r.stop_reason, stop_details=raw.get("stop_details"),
                model_returned=r.model, in_tok=r.usage.input_tokens, out_tok=r.usage.output_tokens, raw=raw,
                refusal=r.stop_reason == "refusal")

async def one(j):
    async with sem:
        est = EST[j["model"]]
        async with lock:
            if S.stop_reason: return
            if S.spent + S.reserved + est > CAP or CUM_PRIOR + S.spent + S.reserved + est > CUM_CAP:
                S.stop_reason = "budget guard: next call could exceed a cap"; return
            S.reserved += est
        M = FZ["models"][j["model"]]; pr = M["price_per_mtok"]; cost = 0.0; res = None; errors = []
        try:
            for att in range(1, 4):
                settings = {k: M[k] for k in M if k not in ("note", "label")}
                await log(REQ, dict(ts=now(), job_key=j["job_key"], attempt=att, settings=settings, prompt_sha8=j["prompt_sha8"],
                                    image_sha256=j["image_sha256"], perm=j["perm"], content_order=M["content_order"]))
                try:
                    res = await call(j)
                    cost += ((res["in_tok"] or 0) * pr["input"] + (res["out_tok"] or 0) * pr["output"]) / 1e6
                    break
                except FATAL as e:
                    errors.append(dict(attempt=att, type=type(e).__name__, status=getattr(e, "status_code", None), body=str(e)[:2000]))
                    async with lock: S.stop_reason = f"non-retryable {type(e).__name__} on {j['job_key']}"
                    break
                except Exception as e:
                    errors.append(dict(attempt=att, type=type(e).__name__, status=getattr(e, "status_code", None), body=str(e)[:2000]))
                    await asyncio.sleep(2 ** att)
        finally:
            async with lock:
                S.reserved -= est; S.spent += cost
                if res is None:
                    S.consec_fail += 1
                    if S.consec_fail >= 5 and not S.stop_reason: S.stop_reason = "5 consecutive API failures"
                else:
                    S.consec_fail = 0
                    if res["refusal"]:
                        S.refusals += 1
                        if S.refusals >= 3 and not S.stop_reason: S.stop_reason = "3 refusals"
        parsed, note = parse_game(res["text"]) if res else (None, "no response")
        status = "ok" if parsed else ("api_failure" if res is None else "refusal" if res["refusal"] else "invalid_response")
        slot = (parsed or {}).get("slot")
        await log(RESP, dict(ts=now(), job_key=j["job_key"], array=j["array"], label=j["label"], condition=j["condition"], role=j["role"],
                             rep=j["rep"], model=j["model"], perm=j["perm"], slot_to_canonical=j["slot_to_canonical"], status=status,
                             decision=(parsed or {}).get("decision"), object_slot=slot,
                             object_canonical=j["slot_to_canonical"][slot - 1] if slot else None, parse_note=note,
                             attempts=len(errors) + (1 if res else 0), errors=errors, text=(res or {}).get("text"),
                             stop=(res or {}).get("stop"), stop_details=(res or {}).get("stop_details") or (res or {}).get("incomplete"),
                             model_returned=(res or {}).get("model_returned"), in_tok=(res or {}).get("in_tok"), out_tok=(res or {}).get("out_tok"),
                             cost_usd=cost, raw=(res or {}).get("raw"), mock=a.mock))

async def main():
    await asyncio.gather(*[one(j) for j in pending])
    rows = [json.loads(l) for l in open(RESP)] if RESP.exists() else []
    summ = dict(ts=now(), records=len(rows), by_status={s: sum(r["status"] == s for r in rows) for s in ("ok", "invalid_response", "refusal", "api_failure")},
                spent_run=S.spent, cumulative=CUM_PRIOR + S.spent, refusals=S.refusals, stop_reason=S.stop_reason)
    print(json.dumps(summ))
    with open(LEDGER, "a") as fh: fh.write(json.dumps(summ) + "\n")

asyncio.run(main())
