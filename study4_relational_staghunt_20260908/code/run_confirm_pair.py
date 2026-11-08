"""n=72 confirmation for a GPT-5.5-focal / older-Claude-OTHER pairing.

Both models, 3 full cycles of all 24 permutations (every identity in every screen position
exactly 18x). Tests the LOCKED GPT identity; never reselects it. Fresh directory, never
pooled with discovery.
"""
import argparse, csv, json, os, sys, threading, time
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor

S4 = "/Users/calypsocalcott/Desktop/Coordination/Self_Coordination/study2_4opt_20260830/code"
EXP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, S4)
import s4_common as S

LOCK = threading.Lock()
PRICE = {"gpt": (1.25, 10.00), "claude": (5.00, 25.00)}   # $/MTok in, out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--locked", required=True)
    ap.add_argument("--frozen", default=os.path.join(EXP, "design", "FROZEN_22_ARRAY_MANIFEST.json"))
    ap.add_argument("--other-ckpt", required=True)
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--cycles", type=int, default=3)
    a = ap.parse_args()

    lock = json.load(open(a.locked))
    frozen = {r["array_id"]: r for r in json.load(open(a.frozen))["arrays"]}
    aids = [c["array_id"] for c in lock["candidates"]]
    jobs = []
    for aid in aids:
        for actor in ("gpt", "claude"):
            for trial, perm in enumerate(list(range(24)) * a.cycles):
                jobs.append(dict(job_key=f"cf|{aid}|{actor}|t{trial}|p{perm}", aid=aid,
                                 actor=actor, trial=trial, perm=perm,
                                 dirp=frozen[aid]["stimulus_dir"]))
    assert len(jobs) == len(aids) * 2 * 24 * a.cycles
    assert len({j["job_key"] for j in jobs}) == len(jobs)
    print(f"=== CONFIRMATION  gpt-5.5 x {a.other_ckpt} ===")
    print(f"arrays {len(aids)}  n/model/array {24*a.cycles}  calls {len(jobs)}")
    print(f"prompt sha8 {S.PROMPT_SHA['stage_a']}\n", flush=True)

    os.makedirs(os.path.join(a.run_dir, "data"), exist_ok=True)
    stem = os.path.join(a.run_dir, "data", "confirm_pair")
    fh = open(stem + ".jsonl", "a")
    cls = S.make_clients()
    imgs, mans, rows, use = {}, {}, [], {"gpt": [0, 0], "claude": [0, 0]}

    def one(j):
        t0 = time.time(); k = (j["aid"], j["perm"])
        with LOCK:
            if k not in imgs:
                imgs[k] = S.b64(os.path.join(j["dirp"], f"perm{j['perm']:02d}.png"))
            if j["aid"] not in mans:
                mans[j["aid"]] = json.load(open(os.path.join(j["dirp"], "manifest.json")))
            img, mn = imgs[k], mans[j["aid"]]
        rec = {kk: vv for kk, vv in j.items() if kk != "dirp"}
        try:
            if j["actor"] == "gpt":
                txt, think, mid = S.ASK["gpt"](cls["gpt"], img, S.STAGE_A_PROMPT)
                ui = uo = 0
            else:
                r = cls["claude"].messages.create(
                    model=a.other_ckpt, max_tokens=S.CLAUDE_MAX_TOKENS,
                    thinking={"type": "adaptive", "display": "summarized"},
                    output_config={"effort": "low"},
                    messages=[{"role": "user", "content": [
                        {"type": "image", "source": {"type": "base64",
                                                     "media_type": "image/png", "data": img}},
                        {"type": "text", "text": S.STAGE_A_PROMPT}]}])
                txt = "".join(b.text for b in r.content if getattr(b, "type", "") == "text")
                mid = r.model; ui, uo = r.usage.input_tokens, r.usage.output_tokens
            pos = S.parse_choice(txt)
            rec.update(ok=True, error="", api_model=mid, raw=txt.replace("\n", " ")[:1000],
                       chosen_position=(None if pos is None else pos + 1),
                       chosen_item=(None if pos is None else mn[str(j["perm"])][pos]),
                       parse_ok=pos is not None, input_tokens=ui, output_tokens=uo)
        except Exception as e:
            rec.update(ok=False, error=f"{type(e).__name__}: {e}", api_model="", raw="",
                       chosen_position=None, chosen_item=None, parse_ok=False,
                       input_tokens=0, output_tokens=0)
        rec.update(prompt_sha8=S.PROMPT_SHA["stage_a"], secs=round(time.time()-t0, 2),
                   ts=datetime.now(timezone.utc).isoformat())
        with LOCK:
            fh.write(json.dumps(rec) + "\n"); fh.flush(); rows.append(rec)
            use[j["actor"]][0] += rec["input_tokens"]; use[j["actor"]][1] += rec["output_tokens"]
            if len(rows) % 100 == 0: print(f"    {len(rows)}/{len(jobs)}", flush=True)
        return rec

    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        list(ex.map(one, jobs))
    fh.close()
    cost = sum(use[m][0]/1e6*PRICE[m][0] + use[m][1]/1e6*PRICE[m][1] for m in use)
    ok = sum(r["ok"] for r in rows); pk = sum(r["parse_ok"] for r in rows)
    print(f"\ntransport {ok}/{len(rows)}  parsed {pk}/{len(rows)}")
    print(f"claude tokens {use['claude']}  measured cost ${cost:.2f} (gpt usage not exposed by ask_gpt)")
    with open(stem + ".csv", "w", newline="") as ch:
        w = csv.DictWriter(ch, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    json.dump(dict(calls=len(rows), transport_ok=ok, parse_ok=pk,
                   claude_tokens=use["claude"], measured_cost_usd=round(cost, 3)),
              open(os.path.join(a.run_dir, "metering.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
