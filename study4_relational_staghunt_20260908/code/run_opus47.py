"""Opus 4.7 discovery on the frozen 22-array set. Claude side only; GPT is already measured.

n = 48 per array = 2 full cycles of all 24 permutations => every canonical identity in every
screen position exactly 12 times. Arrays span stimuli5 AND stimuli6, so the stimulus
directory is taken per-array from the frozen manifest rather than from a single S.STIM.

Records token usage per call (s4_common.run_stage does not), so the run can be metered.
Never pooled with the historical binary Opus 4.7 data.
"""
import argparse, csv, json, os, sys, threading, time
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor

S4 = "/Users/calypsocalcott/Desktop/Coordination/Self_Coordination/study2_4opt_20260830/code"
EXP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, S4)
import s4_common as S

CKPT = os.environ.get("OPUS_CKPT", "claude-opus-4-7")
IN_PER_MTOK, OUT_PER_MTOK = 5.00, 25.00
LOCK = threading.Lock()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--limit", type=int, default=None, help="meter mode: stop after N calls")
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--cycles", type=int, default=2)
    ap.add_argument("--resume-from", default=None)
    a = ap.parse_args()

    man = json.load(open(os.path.join(EXP, "design", "FROZEN_22_ARRAY_MANIFEST.json")))
    arrays = man["arrays"]
    assert man["prompt_sha8"] == S.PROMPT_SHA["stage_a"] == "d40ea45d"

    jobs = []
    for r in arrays:
        for trial, perm in enumerate(list(range(24)) * a.cycles):
            jobs.append(dict(job_key=f"opus47|{r['array_id']}|t{trial}|p{perm}",
                             aid=r["array_id"], dirp=r["stimulus_dir"], trial=trial, perm=perm))
    assert len(jobs) == len(arrays) * 24 * a.cycles
    assert len({j["job_key"] for j in jobs}) == len(jobs)

    done = set()
    if a.resume_from and os.path.exists(a.resume_from):
        for line in open(a.resume_from):
            try:
                d = json.loads(line)
                if d.get("ok"): done.add(d["job_key"])
            except Exception: pass
    todo = [j for j in jobs if j["job_key"] not in done]
    if a.limit: todo = todo[:a.limit]

    print(f"=== OPUS 4.7 DISCOVERY on the frozen 22 ===")
    print(f"checkpoint : {CKPT}")
    print(f"arrays     : {len(arrays)}   n/array: {24*a.cycles}   cycles: {a.cycles}")
    print(f"prompt     : sha8={S.PROMPT_SHA['stage_a']}")
    print(f"planned    : {len(jobs)}   to run now: {len(todo)}{'   [METER]' if a.limit else ''}")
    print(f"run dir    : {a.run_dir}\n", flush=True)

    os.makedirs(os.path.join(a.run_dir, "data"), exist_ok=True)
    stem = os.path.join(a.run_dir, "data", os.environ.get("OPUS_STEM","opus47_discovery"))
    fh = open(stem + ".jsonl", "a")
    cl = S.make_clients()["claude"]
    imgs, mans, rows, usage = {}, {}, [], dict(inp=0, out=0, n=0)

    def one(j):
        t0 = time.time()
        k = (j["aid"], j["perm"])
        with LOCK:
            if k not in imgs:
                imgs[k] = S.b64(os.path.join(j["dirp"], f"perm{j['perm']:02d}.png"))
            if j["aid"] not in mans:
                mans[j["aid"]] = json.load(open(os.path.join(j["dirp"], "manifest.json")))
            img, mn = imgs[k], mans[j["aid"]]
        rec = dict(j); rec.pop("dirp", None)
        try:
            r = cl.messages.create(
                model=CKPT, max_tokens=S.CLAUDE_MAX_TOKENS,
                thinking={"type": "adaptive", "display": "summarized"},
                output_config={"effort": "low"},
                messages=[{"role": "user", "content": [
                    {"type": "image", "source": {"type": "base64",
                                                 "media_type": "image/png", "data": img}},
                    {"type": "text", "text": S.STAGE_A_PROMPT}]}])
            txt = "".join(b.text for b in r.content if getattr(b, "type", "") == "text")
            pos = S.parse_choice(txt)
            rec.update(ok=True, error="", api_model=r.model, raw=txt.replace("\n", " ")[:1200],
                       chosen_position=(None if pos is None else pos + 1),
                       chosen_item=(None if pos is None else mn[str(j["perm"])][pos]),
                       parse_ok=pos is not None,
                       input_tokens=r.usage.input_tokens, output_tokens=r.usage.output_tokens)
        except Exception as e:
            rec.update(ok=False, error=f"{type(e).__name__}: {e}", api_model="", raw="",
                       chosen_position=None, chosen_item=None, parse_ok=False,
                       input_tokens=0, output_tokens=0)
        rec.update(prompt_sha8=S.PROMPT_SHA["stage_a"], secs=round(time.time()-t0, 2),
                   ts=datetime.now(timezone.utc).isoformat())
        with LOCK:
            fh.write(json.dumps(rec) + "\n"); fh.flush(); rows.append(rec)
            usage["inp"] += rec["input_tokens"]; usage["out"] += rec["output_tokens"]
            usage["n"] += 1
            if usage["n"] % 100 == 0: print(f"    {usage['n']}/{len(todo)}", flush=True)
        return rec

    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        list(ex.map(one, todo))
    fh.close()

    cost = usage["inp"]/1e6*IN_PER_MTOK + usage["out"]/1e6*OUT_PER_MTOK
    per = cost/max(usage["n"], 1)
    print(f"\ncalls {usage['n']}   in_tok {usage['inp']}   out_tok {usage['out']}")
    print(f"cost so far ${cost:.3f}   per call ${per:.5f}")
    print(f"PROJECTED full {len(jobs)} calls: ${per*len(jobs):.2f}")
    ok = sum(1 for r in rows if r["ok"]); pk = sum(1 for r in rows if r["parse_ok"])
    bad = sum(1 for r in rows if r["ok"] and CKPT not in (r["api_model"] or ""))
    print(f"transport ok {ok}/{len(rows)}   parsed {pk}/{len(rows)}   checkpoint mismatches {bad}")
    if rows:
        with open(stem + ".csv", "a", newline="") as ch:
            w = csv.DictWriter(ch, fieldnames=list(rows[0].keys()))
            if ch.tell() == 0: w.writeheader()
            w.writerows(rows)
    json.dump(dict(calls=usage["n"], input_tokens=usage["inp"], output_tokens=usage["out"],
                   cost_usd=round(cost, 4), per_call_usd=round(per, 6),
                   projected_full_usd=round(per*len(jobs), 2)),
              open(os.path.join(a.run_dir, "metering.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
