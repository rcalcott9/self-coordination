"""M07 Opus diagnostic: re-send the 4 saved Opus format-check prompts, sequentially, full logging.

Authorization (user, 2026-10-14, session 80332460): "Run the approved M07 Opus diagnostic: up to 4
calls, sequentially, $0.50 hard cap for this diagnostic." No retries (client max_retries=0), no
variants, no GPT calls, no pilot calls. Stops on a refusal, or before any call whose maximum possible
cost (input + max_tokens output) would exceed the remaining cap.
"""
import hashlib, json, os, sys, time
import anthropic

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import selfplay as SP
import run_format_check as R          # summarize(); same model id and settings as the format check

CAP = 0.50
PIN, POUT = 5 / 1e6, 25 / 1e6
SRC = os.path.join(SP.HERE, "results", "format_check_20261014_000026", "responses.jsonl")


def main():
    rows = [json.loads(l) for l in open(SRC)]
    rows = [r for r in rows if r["model"] == "claude-opus-5"]
    assert len(rows) == 4
    for r in rows:   # saved prompt must equal a fresh render of the same seeded slot
        o = SP.order(r["model"], "fc_" + r["kind"], r["i"])
        fresh = (SP.action_prompt if r["kind"] == "action" else SP.prediction_prompt)(r["model"], o)
        r["prompt_sha256"] = hashlib.sha256(r["prompt"].encode()).hexdigest()
        assert "|".join(o) == r["order"] and hashlib.sha256(fresh.encode()).hexdigest() == r["prompt_sha256"], r["call_id"]
        print(r["call_id"], r["prompt_sha256"][:16], "hash verified")
    out = os.path.join(SP.HERE, "results", f"opus_diagnostic_{time.strftime('%Y%m%d_%H%M%S')}")
    os.makedirs(out)
    from dotenv import load_dotenv
    load_dotenv(os.path.expanduser("~/Desktop/Coordination/LLM_Coordination/.env"))
    client = anthropic.Anthropic(max_retries=0)
    spent, log = 0.0, []
    for r in rows:
        max_cost = r["input_tokens"] * PIN + R.S.CLAUDE_MAX_TOKENS * POUT
        if spent + max_cost > CAP:
            log.append(dict(call_id=r["call_id"], skipped=f"max cost {max_cost:.4f} exceeds remaining {CAP - spent:.4f}"))
            break
        t0 = time.time()
        rec = dict(call_id=r["call_id"], kind=r["kind"], order=r["order"], prompt_sha256=r["prompt_sha256"],
                   settings=dict(model=R.S.CLAUDE_ID, max_tokens=R.S.CLAUDE_MAX_TOKENS,
                                 thinking={"type": "adaptive", "display": "summarized"}, output_config={"effort": "low"}),
                   ts=time.strftime("%Y-%m-%dT%H:%M:%S%z"))
        try:
            resp = client.messages.create(model=R.S.CLAUDE_ID, max_tokens=R.S.CLAUDE_MAX_TOKENS,
                                          thinking={"type": "adaptive", "display": "summarized"},
                                          output_config={"effort": "low"},
                                          messages=[{"role": "user", "content": r["prompt"]}])
            x = R.summarize("claude", resp)
            u = x["usage"]
            cost = u["input_tokens"] * PIN + u["output_tokens"] * POUT
            spent += cost
            parsed = SP.parse_action(x["text"]) if r["kind"] == "action" else SP.parse_prediction(x["text"], None)
            rec.update(x, cost=cost, parsed=parsed, secs=round(time.time() - t0, 2), error=None)
        except Exception as e:
            rec.update(error=f"{type(e).__name__}: {e}", error_body=getattr(e, "body", None),
                       status_code=getattr(e, "status_code", None), secs=round(time.time() - t0, 2))
        log.append(rec)
        with open(os.path.join(out, "diagnostic.jsonl"), "a") as fh:
            fh.write(json.dumps(rec, default=str) + "\n")
        print(f"--- {rec['call_id']} stop={rec.get('stop_reason')} usage_out={rec.get('usage', {}).get('output_tokens')} "
              f"blocks={rec.get('blocks')} parsed={rec.get('parsed')} cost=${rec.get('cost', 0):.4f} error={rec['error']}")
        print("text:", repr(rec.get("text", rec.get("response"))))
        if rec.get("error") or rec.get("stop_reason") == "refusal":
            print("STOP:", "refusal" if rec.get("stop_reason") == "refusal" else "error")
            break
    json.dump(dict(spent=spent, cap=CAP, n_calls=sum("error" in x for x in log), log=[{k: v for k, v in x.items() if k != "raw"} for x in log]),
              open(os.path.join(out, "summary.json"), "w"), indent=1, default=str)
    print(f"diagnostic spend ${spent:.4f}  ->  {out}")


if __name__ == "__main__":
    main()
