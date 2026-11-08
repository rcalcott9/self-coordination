"""Gate 1 stage 1 -- submit (or resume) the acquisition fine-tune. Training only.

Uses the frozen preflight artifacts. Hyperparameters stay on AUTO; what Azure
resolves is recorded, not chosen.

    python code/gate1_train.py                 # submit (refuses if a job exists)
    python code/gate1_train.py --resume <id>   # attach to an existing job
"""

import argparse
import datetime as dt
import hashlib
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FROZEN = ROOT / "data" / "gate1"
STATE = FROZEN / "gate1_state.json"

BASE_MODEL = "gpt-4.1-mini-2025-04-14"
EXPECT = {
    "gate1_train_5000.jsonl": "8610f03beedbf981c5bf2bc09e8b00b0d2b926c125d7c77d78b30f786df72863",
    "gate1_val_1000.jsonl": "a2946d4d92faaa7a46fc6ea068fc497f0ca2f0bb62095f083fc3aed0191b3ed2",
}


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
                       api_key=c["AZURE_OPENAI_API_KEY"], api_version="2025-04-01-preview")


def save(st):
    STATE.write_text(json.dumps(st, indent=2))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--resume")
    a = ap.parse_args()
    c = client()

    st = json.loads(STATE.read_text()) if STATE.exists() else {}

    # Integrity: the files we are about to pay to train on must be the frozen ones.
    for name, want in EXPECT.items():
        got = hashlib.sha256((FROZEN / name).read_bytes()).hexdigest()
        if got != want:
            sys.exit(f"HASH MISMATCH {name}\n  expected {want}\n  got      {got}\nSTOP.")
    print("[hash] frozen train/val artifacts verified")

    job_id = a.resume or st.get("job_id")
    if job_id:
        job = c.fine_tuning.jobs.retrieve(job_id)
        print(f"[resume] {job.id} status={job.status} -- no new job created")
    else:
        # Never auto-resubmit: refuse if any gpt-4.1-mini gate1 job already exists.
        for j in c.fine_tuning.jobs.list(limit=20):
            if j.model == BASE_MODEL and (j.suffix or "").startswith("gate1") \
               and j.status in ("pending", "running", "succeeded"):
                sys.exit(f"REFUSING: gate1 job already exists ({j.id}, {j.status}). "
                         f"Resume it with --resume {j.id}.")
        tr = c.files.create(file=open(FROZEN / "gate1_train_5000.jsonl", "rb"), purpose="fine-tune")
        va = c.files.create(file=open(FROZEN / "gate1_val_1000.jsonl", "rb"), purpose="fine-tune")
        for fid in (tr.id, va.id):
            for _ in range(120):
                if getattr(c.files.retrieve(fid), "status", "processed") in ("processed", None):
                    break
                time.sleep(5)
        print(f"[upload] train={tr.id} val={va.id}")
        job = c.fine_tuning.jobs.create(
            model=BASE_MODEL, training_file=tr.id, validation_file=va.id,
            suffix="gate1", seed=4,
            extra_body={"trainingType": "GlobalStandard"},   # training mode, not a deployment
        )
        st.update({"job_id": job.id, "job_created_utc": now(),
                   "train_file": tr.id, "val_file": va.id, "base_model": BASE_MODEL})
        save(st)
        print(f"[submit] {job.id} status={job.status}")

    while job.status not in ("succeeded", "failed", "cancelled"):
        time.sleep(60)
        try:
            job = c.fine_tuning.jobs.retrieve(job.id)
            print(f"  {time.strftime('%H:%M:%S')} {job.status}", flush=True)
        except Exception as e:
            print(f"  poll error: {type(e).__name__}", flush=True)

    hp = job.hyperparameters
    st.update({
        "job_id": job.id, "job_status": job.status, "job_finished_utc": now(),
        "fine_tuned_model": job.fine_tuned_model,
        "resolved_epochs": getattr(hp, "n_epochs", None),
        "resolved_batch_size": getattr(hp, "batch_size", None),
        "resolved_lr_multiplier": getattr(hp, "learning_rate_multiplier", None),
        "trained_tokens": getattr(job, "trained_tokens", None),
    })
    tt = st["trained_tokens"] or 0
    st["cost_training_usd"] = round(tt / 1e6 * 5.00, 4)
    if job.status != "succeeded":
        st["job_error"] = str(getattr(job, "error", None))
    save(st)
    print("\n" + json.dumps(st, indent=2))


if __name__ == "__main__":
    main()
