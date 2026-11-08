"""Gate 1 stage 2 -- deploy (DeveloperTier only), evaluate 5,000 held-out choices on
the fine-tuned model AND the unchanged base model, then delete both deployments.

Deployments are torn down in a finally block. The script will NOT create a Standard
or GlobalStandard deployment under any circumstance: DeveloperTier is the only SKU
it can send, and a refusal aborts rather than falling back.

    python code/gate1_evaluate.py
    python code/gate1_evaluate.py --which ft     # one arm only
"""

import argparse
import datetime as dt
import json
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
FROZEN = ROOT / "data" / "gate1"
STATE = FROZEN / "gate1_state.json"
RESOURCE_GROUP, RESOURCE_NAME = "self_coord", "self-coord"
MGMT_API = "2026-07-01"
BASE_MODEL = "gpt-4.1-mini"
BASE_VERSION = "2025-04-14"
SKU = "DeveloperTier"
# DeveloperTier bills PER TOKEN (Microsoft deployment-type table), so sku.capacity is a
# throughput knob, not a billing knob: rate limits scale as capacity req/min and
# 1000*capacity tokens/min. At the default capacity=1 that is 1 req/min -- 83 hours for
# one arm -- so we raise it. Cost is unchanged.
CAPACITY = 250
# The base model CANNOT use DeveloperTier (that SKU is fine-tuned-only), so the
# negative control runs on GlobalStandard -- pay-per-token, no hourly hosting fee
# (that fee applies to CUSTOMISED deployments). Authorised for the control only,
# torn down immediately after.
BASE_SKU = "GlobalStandard"
BASE_CAPACITY = 200          # units of 1k TPM -- subscription quota ceiling
CONCURRENCY = 10

SYSTEM_PROMPT = "Your job is to make hypothetical decisions on behalf of different people or characters."


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def cfg():
    d = {}
    for line in (ROOT / ".env").read_text().splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, _, v = line.partition("=")
            d[k.strip()] = v.strip()
    return d


def client():
    from openai import AzureOpenAI
    c = cfg()
    return AzureOpenAI(azure_endpoint=c["AZURE_OPENAI_ENDPOINT"],
                       api_key=c["AZURE_OPENAI_API_KEY"], api_version="2025-04-01-preview",
                       max_retries=5)


def az(*a):
    r = subprocess.run(["az", *a], capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"az {' '.join(a)}: {r.stderr.strip()}")
    return r.stdout.strip()


def fresh_headers():
    """Mint a new management token. They expire in ~1h and evaluation runs longer,
    which previously turned teardown into a silent 401."""
    t = json.loads(az("account", "get-access-token", "--resource",
                      "https://management.azure.com/", "-o", "json"))["accessToken"]
    return {"Authorization": f"Bearer {t}", "Content-Type": "application/json"}


def mgmt(sub, name=None):
    u = (f"https://management.azure.com/subscriptions/{sub}/resourceGroups/{RESOURCE_GROUP}"
         f"/providers/Microsoft.CognitiveServices/accounts/{RESOURCE_NAME}/deployments")
    return f"{u}/{name}" if name else u


def deploy(sub, H, name, model_name, model_version, sku=SKU, capacity=CAPACITY):
    body = {"sku": {"name": sku, "capacity": capacity},
            "properties": {"model": {"format": "OpenAI", "name": model_name,
                                     "version": model_version}}}
    # Transient Azure faults (502/503/504, throttling) are retried. A genuine SKU
    # refusal (4xx) still aborts -- we never substitute a paid SKU.
    TRANSIENT = {429, 500, 502, 503, 504}
    r = None
    for attempt in range(8):
        r = requests.put(mgmt(sub, name), params={"api-version": MGMT_API},
                         headers=fresh_headers(), json=body, timeout=120)
        if r.status_code in (200, 201, 202):
            break
        if r.status_code in TRANSIENT:
            wait = min(2 ** attempt * 5, 60)
            print(f"  transient HTTP {r.status_code} deploying {name}; retry in {wait}s")
            time.sleep(wait)
            continue
        sys.exit(f"{sku} deployment REFUSED for {model_name} (HTTP {r.status_code}):\n"
                 f"{r.text[:600]}\nAborting -- no SKU will be substituted.")
    if r.status_code not in (200, 201, 202):
        sys.exit(f"{sku} deployment failed for {model_name} after retries "
                 f"(last HTTP {r.status_code}). Aborting.")
    for _ in range(90):
        g = requests.get(mgmt(sub, name), params={"api-version": MGMT_API},
                         headers=fresh_headers(), timeout=60).json()
        state = g.get("properties", {}).get("provisioningState")
        granted = (g.get("sku") or {}).get("name")
        if state in ("Succeeded", "Failed"):
            break
        time.sleep(10)
    if state != "Succeeded" or granted != sku:
        sys.exit(f"deployment {name}: state={state} sku_granted={granted}. Aborting.")
    print(f"  deployed {name}: {model_name} sku={granted}")
    return granted


def run_arm(c, deployment, rows, out_path, provenance_ok, provenance_desc):
    """5,000 forced-choice calls at temperature 0. Returns list of result dicts."""
    done = {}
    if out_path.exists():
        for r in json.loads(out_path.read_text()):
            # Only successful rows count as done -- a transport failure must be retried,
            # not cached as a permanent gap.
            if r.get("choice") in ("A", "B"):
                done[(r["scenario"], r["idx"])] = r
        print(f"  resuming: {len(done)} already scored")

    served = {"id": None}

    def one(row):
        key = (row["scenario"], row["idx"])
        if key in done:
            return done[key]
        last = None
        for attempt in range(10):
            try:
                resp = c.chat.completions.create(
                    model=deployment, temperature=0, max_tokens=5,
                    messages=[{"role": "system", "content": SYSTEM_PROMPT},
                              {"role": "user", "content": row["prompt"]}])
                served["id"] = resp.model
                txt = (resp.choices[0].message.content or "").strip()
                return {"scenario": row["scenario"], "idx": row["idx"],
                        "target": row["target"], "raw": txt,
                        "choice": txt if txt in ("A", "B") else None,
                        "served_model": resp.model}
            except Exception as e:
                last = e
                time.sleep(min(2 ** attempt, 30))
        return {"scenario": row["scenario"], "idx": row["idx"], "target": row["target"],
                "raw": None, "choice": None, "error": f"{type(last).__name__}: {last}"}

    out = []
    with ThreadPoolExecutor(max_workers=CONCURRENCY) as ex:
        for i, r in enumerate(ex.map(one, rows), 1):
            out.append(r)
            if i % 500 == 0:
                print(f"  {i}/{len(rows)}", flush=True)
                out_path.write_text(json.dumps(out))
    out_path.write_text(json.dumps(out))

    # Provenance gate: the served model must carry the expected identity.
    sid = served["id"] or ""
    ok = provenance_ok(sid)
    print(f"  served_model={sid}\n  provenance ({provenance_desc}): {ok}")
    if not ok:
        sys.exit("PROVENANCE FAILURE -- served model does not match expectation. "
                 "Scoring aborted.")
    n_bad = sum(1 for r in out if r["choice"] is None)
    print(f"  invalid/failed responses: {n_bad}/{len(out)}")
    return out, sid


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--which", choices=["ft", "base", "both"], default="both")
    a = ap.parse_args()

    st = json.loads(STATE.read_text())
    if st.get("job_status") != "succeeded":
        sys.exit(f"training not succeeded (status={st.get('job_status')}). Stop.")
    ft_model = st["fine_tuned_model"]
    job_tag = st["job_id"].replace("ftjob-", "")
    rows = json.loads((FROZEN / "gate1_heldout_5000.json").read_text())
    print(f"held-out rows: {len(rows)}  contexts: {len({r['scenario'] for r in rows})}")

    c = client()
    sub = json.loads(az("account", "show", "-o", "json"))["id"]
    tok = json.loads(az("account", "get-access-token", "--resource",
                        "https://management.azure.com/", "-o", "json"))["accessToken"]
    H = {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}

    created = []
    try:
        if a.which in ("ft", "both"):
            print("\n[FT arm]")
            deploy(sub, H, "gate1-ft-dev", ft_model, "1"); created.append("gate1-ft-dev")
            _, sid = run_arm(c, "gate1-ft-dev", rows, FROZEN / "gate1_eval_ft.json",
                             lambda m: job_tag in m, f"must contain {job_tag}")
            st["ft_served_model"] = sid
        if a.which in ("base", "both"):
            print("\n[BASE arm -- negative control]")
            deploy(sub, H, "gate1-base-dev", BASE_MODEL, BASE_VERSION,
                   sku=BASE_SKU, capacity=BASE_CAPACITY)
            created.append("gate1-base-dev")
            _, sid = run_arm(
                c, "gate1-base-dev", rows, FROZEN / "gate1_eval_base.json",
                lambda m: BASE_MODEL in m and "ft-" not in m and job_tag not in m,
                "must be base gpt-4.1-mini AND carry no ft- tag")
            st["base_served_model"] = sid
        st["eval_finished_utc"] = now()
    finally:
        for name in created:
            d = requests.delete(mgmt(sub, name), params={"api-version": MGMT_API},
                                headers=fresh_headers(), timeout=120)
            print(f"[delete] {name}: HTTP {d.status_code} at {now()}")
            if d.status_code not in (200, 202, 204, 404):
                print(f"[delete] WARNING {name} not confirmed deleted: {d.text[:300]}")
        items, verified = None, False
        for _ in range(30):
            resp = requests.get(mgmt(sub), params={"api-version": MGMT_API},
                                headers=fresh_headers(), timeout=60)
            if resp.status_code != 200:
                # An auth/transport failure is NOT evidence of an empty list.
                print(f"[cleanup] list failed HTTP {resp.status_code} -- retrying")
                time.sleep(10)
                continue
            items = resp.json().get("value", [])
            verified = True
            if not items:
                break
            time.sleep(10)
        st["deployments_remaining"] = len(items) if verified else "UNVERIFIED"
        st["cleanup_verified"] = verified
        if not verified:
            print("[cleanup] !! COULD NOT VERIFY teardown -- check manually")
        st["deployments_deleted_utc"] = now()
        STATE.write_text(json.dumps(st, indent=2))
        print(f"[cleanup] deployments remaining: {len(items)}")


if __name__ == "__main__":
    main()
