"""Gate 2A -- elicit self-reported attribute weights from the Gate 1 fine-tuned model
and from the unchanged base model, then tear both deployments down.

Parsing is done two ways and BOTH are recorded:
  strict  -- Plunkett's rule verbatim (JSON decodes, is a dict, exactly 5 keys, every
             key matches an attribute name). This is the primary.
  lenient -- case/whitespace-insensitive key matching and numeric coercion. Secondary,
             used only to quantify how much of the strict attrition is formatting
             rather than genuine inability. Their design cannot separate the two.

Every unparsed reply is logged verbatim with its context. Nothing is silently dropped.

    python code/gate2a_elicit.py --which ft
    python code/gate2a_elicit.py --which base
"""

import argparse
import datetime as dt
import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gate1_evaluate import (  # noqa: E402
    client, az, mgmt, fresh_headers, deploy, SKU, CAPACITY, BASE_SKU, BASE_CAPACITY,
    BASE_MODEL, BASE_VERSION, SYSTEM_PROMPT,
)

ROOT = Path(__file__).resolve().parent.parent
FROZEN = ROOT / "data" / "gate2a"
GATE1 = ROOT / "data" / "gate1"
CONCURRENCY_FT, CONCURRENCY_BASE = 40, 10
MAX_TOKENS = 300      # Plunkett set none; 300 cannot truncate a 5-key JSON


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def parse_strict(reply, attr_names):
    """Plunkett's save_reported_weights logic, verbatim in behaviour."""
    if reply is None:
        return None, "no_reply"
    s = reply.strip("```json").strip("```")
    try:
        d = json.loads(s)
    except json.JSONDecodeError:
        return None, "json_decode_error"
    if not isinstance(d, dict):
        return None, f"not_dict:{type(d).__name__}"
    if len(d) != 5:
        return None, f"wrong_key_count:{len(d)}"
    out = [None] * 5
    for k, v in d.items():
        if k not in attr_names:
            return None, f"unknown_key:{k}"
        out[attr_names.index(k)] = v
    if any(o is None for o in out):
        return None, "missing_attr"
    try:
        return [float(x) for x in out], "ok"
    except (TypeError, ValueError):
        return None, "non_numeric_value"


def parse_lenient(reply, attr_names):
    """Secondary only: recover reports the strict rule discards for formatting."""
    if reply is None:
        return None
    s = reply.strip()
    s = re.sub(r"^```(?:json)?|```$", "", s, flags=re.M).strip()
    m = re.search(r"\{.*\}", s, flags=re.S)
    if not m:
        return None
    try:
        d = json.loads(m.group(0))
    except json.JSONDecodeError:
        return None
    if not isinstance(d, dict):
        return None
    norm = {re.sub(r"[^a-z0-9]", "", k.lower()): v for k, v in d.items()}
    out = []
    for a in attr_names:
        key = re.sub(r"[^a-z0-9]", "", a.lower())
        if key not in norm:
            return None
        v = norm[key]
        if isinstance(v, str):
            mm = re.search(r"-?\d+(?:\.\d+)?", v)
            if not mm:
                return None
            v = mm.group(0)
        try:
            out.append(float(v))
        except (TypeError, ValueError):
            return None
    return out if len(out) == 5 else None


def run_arm(c, deployment, rows, out_path, provenance_ok, desc, concurrency):
    done = {}
    if out_path.exists():
        for r in json.loads(out_path.read_text()):
            if r.get("reply") is not None:      # transport failures get retried
                done[(r["scenario"], r["idx"])] = r
        print(f"  resuming: {len(done)} replies already collected")
    served = {"id": None}

    def one(row):
        key = (row["scenario"], row["idx"])
        if key in done:
            return done[key]
        last = None
        for attempt in range(10):
            try:
                resp = c.chat.completions.create(
                    model=deployment, temperature=0, max_tokens=MAX_TOKENS,
                    messages=[{"role": "system", "content": SYSTEM_PROMPT},
                              {"role": "user", "content": row["prompt"]}])
                served["id"] = resp.model
                return {"scenario": row["scenario"], "idx": row["idx"],
                        "reply": resp.choices[0].message.content,
                        "served_model": resp.model}
            except Exception as e:
                last = e
                time.sleep(min(2 ** attempt, 30))
        return {"scenario": row["scenario"], "idx": row["idx"], "reply": None,
                "error": f"{type(last).__name__}: {last}"}

    out = []
    with ThreadPoolExecutor(max_workers=concurrency) as ex:
        for i, r in enumerate(ex.map(one, rows), 1):
            out.append(r)
            if i % 200 == 0:
                print(f"  {i}/{len(rows)}", flush=True)
                out_path.write_text(json.dumps(out))
    out_path.write_text(json.dumps(out))

    sid = served["id"] or ""
    if not provenance_ok(sid):
        sys.exit(f"PROVENANCE FAILURE: served={sid} ({desc}). Aborting.")
    print(f"  served_model={sid}\n  provenance ({desc}): True")
    n_none = sum(1 for r in out if r.get("reply") is None)
    print(f"  transport failures: {n_none}/{len(out)}")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--which", choices=["ft", "base"], required=True)
    a = ap.parse_args()

    rows = json.loads((FROZEN / "gate2a_report_trials.json").read_text())
    st = json.loads((GATE1 / "gate1_state.json").read_text())
    ft_model, job_tag = st["fine_tuned_model"], st["job_id"].replace("ftjob-", "")
    print(f"report trials: {len(rows)}  contexts: {len({r['scenario'] for r in rows})}")

    c = client()
    sub = json.loads(az("account", "show", "-o", "json"))["id"]
    H = fresh_headers()
    created = []
    try:
        if a.which == "ft":
            name = "gate2a-ft-dev"
            deploy(sub, H, name, ft_model, "1", sku=SKU, capacity=CAPACITY)
            created.append(name)
            run_arm(c, name, rows, FROZEN / "gate2a_reports_ft.json",
                    lambda m: job_tag in m, f"must contain {job_tag}", CONCURRENCY_FT)
        else:
            name = "gate2a-base-dev"
            deploy(sub, H, name, BASE_MODEL, BASE_VERSION,
                   sku=BASE_SKU, capacity=BASE_CAPACITY)
            created.append(name)
            run_arm(c, name, rows, FROZEN / "gate2a_reports_base.json",
                    lambda m: BASE_MODEL in m and "ft-" not in m and job_tag not in m,
                    "base gpt-4.1-mini AND no ft- tag", CONCURRENCY_BASE)
    finally:
        for n in created:
            d = requests.delete(mgmt(sub, n), params={"api-version": "2026-07-01"},
                                headers=fresh_headers(), timeout=120)
            print(f"[delete] {n}: HTTP {d.status_code} at {now()}")
        items, verified = None, False
        for _ in range(30):
            resp = requests.get(mgmt(sub), params={"api-version": "2026-07-01"},
                                headers=fresh_headers(), timeout=60)
            if resp.status_code != 200:
                print(f"[cleanup] list failed HTTP {resp.status_code} -- retrying")
                time.sleep(10); continue
            items = resp.json().get("value", []); verified = True
            if not items:
                break
            time.sleep(10)
        print(f"[cleanup] deployments remaining: "
              f"{len(items) if verified else 'UNVERIFIED'}")


if __name__ == "__main__":
    main()
