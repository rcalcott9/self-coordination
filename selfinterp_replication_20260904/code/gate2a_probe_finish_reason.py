"""Settle whether the FT model's truncated JSON is my max_tokens cap or the model
ending its own output. Deploys briefly on DeveloperTier, 60 calls at max_tokens=800,
records finish_reason, deletes."""
import json, sys, time
from pathlib import Path
import requests
sys.path.insert(0, str(Path(__file__).resolve().parent))
from gate1_evaluate import client, az, mgmt, fresh_headers, deploy, SKU, CAPACITY, SYSTEM_PROMPT
ROOT = Path(__file__).resolve().parent.parent
rows = json.loads((ROOT/'data'/'gate2a'/'gate2a_report_trials.json').read_text())[:60]
st = json.loads((ROOT/'data'/'gate1'/'gate1_state.json').read_text())
c = client(); sub = json.loads(az("account","show","-o","json"))["id"]
name = "gate2a-probe-dev"; created=[]
try:
    deploy(sub, fresh_headers(), name, st["fine_tuned_model"], "1", sku=SKU, capacity=CAPACITY)
    created.append(name)
    out=[]
    for r in rows:
        resp = c.chat.completions.create(model=name, temperature=0, max_tokens=800,
            messages=[{"role":"system","content":SYSTEM_PROMPT},{"role":"user","content":r["prompt"]}])
        out.append({"scenario":r["scenario"],"finish_reason":resp.choices[0].finish_reason,
                    "reply":resp.choices[0].message.content,
                    "completion_tokens":resp.usage.completion_tokens})
    (ROOT/'data'/'gate2a'/'probe_finish_reason.json').write_text(json.dumps(out,indent=1))
    from collections import Counter
    print("finish_reason:", dict(Counter(o["finish_reason"] for o in out)))
    print("completion_tokens: min=%d max=%d mean=%.1f"%(
        min(o["completion_tokens"] for o in out), max(o["completion_tokens"] for o in out),
        sum(o["completion_tokens"] for o in out)/len(out)))
    nb=[o for o in out if '{' in (o["reply"] or '')]
    print(f"replies with JSON: {len(nb)}/{len(out)}")
    for o in nb[:2]: print("  ", repr(o["reply"])[:200], "| finish:", o["finish_reason"])
    print(f"bare A/B: {sum(1 for o in out if (o['reply'] or '').strip() in ('A','B'))}/{len(out)}")
finally:
    for n in created:
        d=requests.delete(mgmt(sub,n),params={"api-version":"2026-07-01"},headers=fresh_headers(),timeout=120)
        print(f"[delete] {n}: HTTP {d.status_code}")
    resp=requests.get(mgmt(sub),params={"api-version":"2026-07-01"},headers=fresh_headers(),timeout=60)
    print("[cleanup] remaining:", len(resp.json().get("value",[])) if resp.status_code==200 else "UNVERIFIED")
