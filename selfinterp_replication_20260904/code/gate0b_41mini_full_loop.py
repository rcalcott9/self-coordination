"""Gate 0b -- validate the full train -> DeveloperTier deploy -> infer -> delete loop
on gpt-4.1-mini, the model the project will actually use.

Hyperparameters are left on AUTO deliberately: what Azure resolves is itself the
datum, since Plunkett specified none and we need to know what "auto" means here.

The deployment is deleted in a finally block, so an exception mid-run still tears it
down rather than leaving something deployed.

    python code/gate0b_41mini_full_loop.py
"""

import datetime as dt
import json
import subprocess
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
REF = ROOT / "reference_plunkett" / "data" / "instill_100_prefs.jsonl"
OUT = ROOT / "data" / "gate0b"
RESOURCE_GROUP, RESOURCE_NAME = "self_coord", "self-coord"
MGMT_API = "2026-07-01"
DATA_API = "2025-04-01-preview"

BASE_MODEL = "gpt-4.1-mini-2025-04-14"
DEPLOY_NAME = "gate0b-41mini-dev"
SKU = "DeveloperTier"
N_EX = 20

# Azure list price, $/1M tokens (record-keeping only).
TRAIN_PRICE = 5.00
INFER_IN, INFER_OUT = 0.80, 3.20

rec = {"started_utc": dt.datetime.now(dt.timezone.utc).isoformat()}


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def cfg():
    d = {}
    for line in (ROOT / ".env").read_text().splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, _, v = line.partition("=")
            d[k.strip()] = v.strip()
    return d


def az(*a):
    r = subprocess.run(["az", *a], capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"az {' '.join(a)}: {r.stderr.strip()}")
    return r.stdout.strip()


def mgmt(sub, name=None):
    u = (f"https://management.azure.com/subscriptions/{sub}/resourceGroups/{RESOURCE_GROUP}"
         f"/providers/Microsoft.CognitiveServices/accounts/{RESOURCE_NAME}/deployments")
    return f"{u}/{name}" if name else u


def main():
    c = cfg()
    from openai import AzureOpenAI

    client = AzureOpenAI(azure_endpoint=c["AZURE_OPENAI_ENDPOINT"],
                         api_key=c["AZURE_OPENAI_API_KEY"], api_version=DATA_API)
    sub = json.loads(az("account", "show", "-o", "json"))["id"]
    tok = json.loads(az("account", "get-access-token", "--resource",
                        "https://management.azure.com/", "-o", "json"))["accessToken"]
    H = {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}
    OUT.mkdir(parents=True, exist_ok=True)

    # ---- 1. training file: 20 real Plunkett examples ----------------------------
    rows = []
    with REF.open() as f:
        for i, line in enumerate(f):
            if i >= N_EX:
                break
            rows.append(json.loads(line))
    path = OUT / f"gate0b_{N_EX}ex.jsonl"
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8-sig")
    print(f"[1] training file  : {path.name}  ({len(rows)} examples)")

    # Keep one example to probe the deployment with later.
    probe = rows[0]
    probe_user = next(m["content"] for m in probe["messages"] if m["role"] == "user")
    probe_sys = next(m["content"] for m in probe["messages"] if m["role"] == "system")
    probe_target = next(m["content"] for m in probe["messages"] if m["role"] == "assistant")

    # ---- 2. upload + create job (AUTO hyperparameters) --------------------------
    # Resume mode: attach to an existing job instead of creating a second one.
    # The first attempt was killed by host memory pressure *after* the job was
    # created, and the job kept training server-side.
    resume_id = sys.argv[1] if len(sys.argv) > 1 else None
    if resume_id:
        job = client.fine_tuning.jobs.retrieve(resume_id)
        print(f"[2] RESUMING       : {job.id} (status={job.status}) -- no new job created")
    else:
        up = client.files.create(file=open(path, "rb"), purpose="fine-tune")
        for _ in range(60):
            if getattr(client.files.retrieve(up.id), "status", "processed") in ("processed", None):
                break
            time.sleep(5)
        print(f"[2] uploaded       : {up.id}")

        job = client.fine_tuning.jobs.create(
            model=BASE_MODEL, training_file=up.id, suffix="gate0b", seed=4,
            extra_body={"trainingType": "GlobalStandard"},
        )
    rec["job_id"] = job.id
    rec["model_snapshot"] = BASE_MODEL
    rec["job_created_utc"] = now()
    print(f"[3] job            : {job.id}  status={job.status}")

    while job.status not in ("succeeded", "failed", "cancelled"):
        time.sleep(60)
        try:
            job = client.fine_tuning.jobs.retrieve(job.id)
            print(f"    {time.strftime('%H:%M:%S')} {job.status}")
        except Exception as e:
            print(f"    poll error: {type(e).__name__}")
    rec["job_status"] = job.status
    rec["job_finished_utc"] = now()
    if job.status != "succeeded":
        rec["job_error"] = str(getattr(job, "error", None))
        print(f"FAILED: {rec['job_error']}")
        return

    hp = job.hyperparameters
    ft_model = job.fine_tuned_model
    rec.update({
        "fine_tuned_model": ft_model,
        "resolved_epochs": getattr(hp, "n_epochs", None),
        "resolved_batch_size": getattr(hp, "batch_size", None),
        "resolved_lr_multiplier": getattr(hp, "learning_rate_multiplier", None),
        "trained_tokens": getattr(job, "trained_tokens", None),
    })
    print(f"[4] trained        : epochs={rec['resolved_epochs']} "
          f"batch={rec['resolved_batch_size']} tokens={rec['trained_tokens']}")

    # ---- 3. DeveloperTier deployment -------------------------------------------
    deployed = False
    try:
        body = {"sku": {"name": SKU, "capacity": 1},
                "properties": {"model": {"format": "OpenAI", "name": ft_model, "version": "1"}}}
        r = requests.put(mgmt(sub, DEPLOY_NAME), params={"api-version": MGMT_API},
                         headers=H, json=body, timeout=120)
        rec["deploy_http"] = r.status_code
        rec["deploy_sku_requested"] = SKU
        rec["deploy_created_utc"] = now()
        print(f"[5] deploy         : HTTP {r.status_code}")
        if r.status_code not in (200, 201, 202):
            rec["deploy_error"] = r.text[:600]
            print(r.text[:600])
            return
        deployed = True

        state = None
        for _ in range(60):
            g = requests.get(mgmt(sub, DEPLOY_NAME), params={"api-version": MGMT_API},
                             headers=H, timeout=60).json()
            state = g.get("properties", {}).get("provisioningState")
            rec["deploy_sku_granted"] = (g.get("sku") or {}).get("name")
            if state in ("Succeeded", "Failed"):
                break
            time.sleep(10)
        rec["deploy_state"] = state
        print(f"    provisioning   : {state}  sku_granted={rec.get('deploy_sku_granted')}")
        if state != "Succeeded":
            return

        # ---- 4. inference, and prove it came from the FT deployment -------------
        resp, last = None, None
        for _ in range(20):
            try:
                resp = client.chat.completions.create(
                    model=DEPLOY_NAME,
                    messages=[{"role": "system", "content": probe_sys},
                              {"role": "user", "content": probe_user}],
                    temperature=0, max_tokens=5)
                break
            except Exception as e:
                last = e
                time.sleep(15)
        if resp is None:
            rec["inference_error"] = f"{type(last).__name__}: {last}"
            print(f"[6] inference      : FAILED {rec['inference_error']}")
            return

        out = (resp.choices[0].message.content or "").strip()
        rec.update({
            "inference_output": out,
            "inference_target": probe_target,
            "inference_matches_target": out == probe_target,
            # The authoritative provenance signal: the served model id.
            "inference_served_model": resp.model,
            "inference_from_finetune": bool(resp.model and "ft-" in resp.model),
            "inference_tokens_in": resp.usage.prompt_tokens,
            "inference_tokens_out": resp.usage.completion_tokens,
        })
        print(f"[6] inference      : output={out!r} target={probe_target!r} "
              f"match={rec['inference_matches_target']}")
        print(f"    served model   : {resp.model}")
        print(f"    from finetune  : {rec['inference_from_finetune']}")

    finally:
        # ---- 5. always delete ---------------------------------------------------
        if deployed:
            d = requests.delete(mgmt(sub, DEPLOY_NAME), params={"api-version": MGMT_API},
                                headers=H, timeout=120)
            rec["delete_http"] = d.status_code
            rec["deleted_utc"] = now()
            print(f"[7] delete         : HTTP {d.status_code} at {rec['deleted_utc']}")
            for _ in range(30):
                items = requests.get(mgmt(sub), params={"api-version": MGMT_API},
                                     headers=H, timeout=60).json().get("value", [])
                if not items:
                    break
                time.sleep(10)
            rec["deployments_remaining"] = len(items)
            print(f"[8] remaining      : {len(items)}")

        tt = rec.get("trained_tokens") or 0
        rec["cost_training_usd"] = round(tt / 1e6 * TRAIN_PRICE, 4)
        rec["cost_inference_usd"] = round(
            rec.get("inference_tokens_in", 0) / 1e6 * INFER_IN
            + rec.get("inference_tokens_out", 0) / 1e6 * INFER_OUT, 6)
        rec["cost_hosting_usd"] = 0.0  # DeveloperTier
        rec["cost_total_usd"] = round(rec["cost_training_usd"] + rec["cost_inference_usd"], 4)
        (OUT / "gate0b_record.json").write_text(json.dumps(rec, indent=2))
        print(f"\nrecord -> {OUT/'gate0b_record.json'}")
        print(json.dumps(rec, indent=2))


if __name__ == "__main__":
    main()
