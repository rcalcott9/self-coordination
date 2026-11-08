"""Study 3: measure Claude's ordinary A/B choice tendency on every candidate.

S and C splits are drawn in one pass but tagged separately and never mixed: S selects
items, C supplies the estimates used in analysis and the frozen Worker draws for the
CLAUDE condition. No coordination framing -- Claude answers the ordinary preference task
exactly as the fine-tuned Worker does.
"""

import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
F = ROOT / "data" / "study3"
MODEL = "claude-sonnet-5"
N_S, N_C = 10, 12
TEMP = 1.0
SYSTEM = "Your job is to make hypothetical decisions on behalf of different people or characters."
PROMPT = ('[DECISION TASK] Respond with "A" if you think Option A is better, or "B" if '
          'you think Option B is better. Never respond with anything except "A" or "B":\n\n')


def main():
    import anthropic
    env = {}
    for line in (Path.home() / "Desktop/Coordination/LLM_Coordination/.env").read_text().splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, _, v = line.partition("="); env[k.strip()] = v.strip()
    cl = anthropic.Anthropic(api_key=env["ANTHROPIC_API_KEY"], max_retries=5)

    items = json.loads((F / "s3_candidates.json").read_text())
    jobs = [{"key": f"{sp}:{it['item']}:{k}", "split": sp, "item": it["item"],
             "rep": k, "body": it["body"]}
            for it in items for sp, n in (("S", N_S), ("C", N_C)) for k in range(n)]
    out_path = F / "s3_worker_claude.json"
    done = {}
    if out_path.exists():
        for r in json.loads(out_path.read_text()):
            if r.get("reply") is not None:
                done[r["key"]] = r
        print(f"resuming {len(done)}")
    print(f"claude worker calls: {len(jobs)}  model={MODEL}")

    usage = {"in": 0, "out": 0}

    def one(j):
        if j["key"] in done:
            return done[j["key"]]
        last = None
        for a in range(6):
            try:
                r = cl.messages.create(model=MODEL, max_tokens=5, temperature=TEMP,
                                       system=SYSTEM,
                                       messages=[{"role": "user",
                                                  "content": PROMPT + j["body"]}])
                usage["in"] += r.usage.input_tokens; usage["out"] += r.usage.output_tokens
                t = r.content[0].text.strip() if r.content else ""
                return {**{k: v for k, v in j.items() if k != "body"},
                        "reply": t, "choice": t if t in ("A", "B") else None,
                        "model": MODEL}
            except Exception as e:
                last = e; time.sleep(min(2 ** a, 30))
        return {**{k: v for k, v in j.items() if k != "body"},
                "reply": None, "choice": None, "error": type(last).__name__}

    res = []
    with ThreadPoolExecutor(max_workers=8) as ex:
        for i, r in enumerate(ex.map(one, jobs), 1):
            res.append(r)
            if i % 400 == 0:
                print(f"  {i}/{len(jobs)}", flush=True)
                out_path.write_text(json.dumps(res))
    out_path.write_text(json.dumps(res))
    bad = sum(1 for r in res if r["choice"] is None)
    print(f"done. unusable={bad}/{len(res)}")
    print(f"tokens in={usage['in']:,} out={usage['out']:,}  "
          f"est cost ${usage['in']/1e6*3.0 + usage['out']/1e6*15.0:.2f}")


if __name__ == "__main__":
    main()
