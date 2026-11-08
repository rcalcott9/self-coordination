"""Gate 0 -- prove Azure OpenAI fine-tuning actually works before any real spend.

Two stages, deliberately separated so nothing bills by accident:

    python code/gate0_azure_check.py --check     # free: auth, FT access, model list
    python code/gate0_azure_check.py --submit    # ~$0.02: 20-example throwaway job

Gate 0 passes when --submit reaches status "succeeded". Nothing in Phase A runs
until it does.
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
REF = ROOT / "reference_plunkett" / "data" / "instill_100_prefs.jsonl"
SCRATCH = ROOT / "data" / "gate0"

# Plunkett's cheaper base model. Global training type works in every region, so
# Gate 0 does not depend on where the self-coord resource happens to live.
GATE0_MODEL = "gpt-4o-mini-2024-07-18"
GATE0_N = 20


def load_env():
    env = ROOT / ".env"
    if not env.exists():
        sys.exit(f"missing {env} -- copy .env.example and fill it in")
    cfg = {}
    for line in env.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        cfg[k.strip()] = v.strip()
    key = cfg.get("AZURE_OPENAI_API_KEY", "")
    if not key or key == "PASTE_KEY_HERE":
        sys.exit("AZURE_OPENAI_API_KEY is still the placeholder -- paste KEY 1 into .env")
    if not cfg.get("AZURE_OPENAI_ENDPOINT"):
        sys.exit("AZURE_OPENAI_ENDPOINT is empty in .env")
    return cfg


def client_for(cfg, api_version):
    from openai import AzureOpenAI

    return AzureOpenAI(
        azure_endpoint=cfg["AZURE_OPENAI_ENDPOINT"],
        api_key=cfg["AZURE_OPENAI_API_KEY"],
        api_version=api_version,
    )


# Fine-tuning moved across api-versions more than once; try newest first and
# report which one actually answered rather than hardcoding a guess.
API_VERSIONS = ("2025-04-01-preview", "2024-10-21", "2024-08-01-preview")


def probe(cfg):
    """Free. Establishes auth, fine-tuning access, and a working api-version."""
    print(f"endpoint     : {cfg['AZURE_OPENAI_ENDPOINT']}")
    working = None
    for ver in API_VERSIONS:
        try:
            c = client_for(cfg, ver)
            jobs = c.fine_tuning.jobs.list(limit=10)
            data = list(jobs)
            print(f"api-version  : {ver}  -> OK, {len(data)} existing fine-tuning job(s)")
            for j in data:
                print(f"    {j.id} | {j.model} | {j.status}")
            working = ver
            break
        except Exception as e:  # noqa: BLE001 -- we want the message, whatever it is
            print(f"api-version  : {ver}  -> {type(e).__name__}: {str(e)[:160]}")
    if working is None:
        sys.exit("\nFAIL: no api-version could reach the fine-tuning endpoint.")

    c = client_for(cfg, working)
    try:
        names = sorted(m.id for m in c.models.list())
        ft_capable = [n for n in names if n.startswith(("gpt-4o", "gpt-4.1"))]
        print(f"models       : {len(names)} visible; 4o/4.1 family: {ft_capable[:12]}")
    except Exception as e:  # noqa: BLE001
        print(f"models       : could not list ({type(e).__name__}: {str(e)[:120]})")
    return working


def build_tiny_file():
    """20 real examples from Plunkett's own training set -- validates the format too."""
    if not REF.exists():
        sys.exit(f"missing {REF}")
    SCRATCH.mkdir(parents=True, exist_ok=True)
    lines = []
    with REF.open() as f:
        for i, line in enumerate(f):
            if i >= GATE0_N:
                break
            json.loads(line)  # fail loudly on malformed input
            lines.append(line.rstrip("\n"))
    out = SCRATCH / f"gate0_{GATE0_N}ex.jsonl"
    # Azure documents UTF-8 *with BOM* for training files.
    out.write_text("\n".join(lines) + "\n", encoding="utf-8-sig")
    print(f"training file: {out}  ({len(lines)} examples)")
    return out


def submit(cfg, api_version):
    c = client_for(cfg, api_version)
    path = build_tiny_file()

    up = c.files.create(file=open(path, "rb"), purpose="fine-tune")
    print(f"uploaded     : {up.id} (status={getattr(up, 'status', '?')})")

    # Azure rejects file ids that are not yet processed; wait for it.
    for _ in range(60):
        f = c.files.retrieve(up.id)
        if getattr(f, "status", "processed") in ("processed", "uploaded", None):
            break
        time.sleep(5)

    job = c.fine_tuning.jobs.create(
        model=GATE0_MODEL,
        training_file=up.id,
        suffix="gate0",
        seed=4,
        extra_body={"trainingType": "GlobalStandard"},
    )
    print(f"job created  : {job.id}  model={job.model}  status={job.status}")

    log = SCRATCH / "gate0_job.json"
    log.write_text(json.dumps(job.model_dump(), indent=2, default=str))
    print(f"job record   : {log}")

    print("\npolling (ctrl-c is safe; the job keeps running)...")
    while True:
        job = c.fine_tuning.jobs.retrieve(job.id)
        print(f"  {time.strftime('%H:%M:%S')}  {job.status}")
        if job.status in ("succeeded", "failed", "cancelled"):
            break
        time.sleep(30)

    # The resolved hyperparameters are the un-replicable part of Plunkett's
    # method (they specified none), so record whatever Azure chose for us.
    print(f"\nfinal status : {job.status}")
    print(f"fine_tuned   : {job.fine_tuned_model}")
    print(f"hyperparams  : {getattr(job, 'hyperparameters', None)}")
    if job.status != "succeeded":
        print(f"error        : {getattr(job, 'error', None)}")
    (SCRATCH / "gate0_job_final.json").write_text(
        json.dumps(job.model_dump(), indent=2, default=str)
    )
    print("\nGATE 0 " + ("PASSED" if job.status == "succeeded" else "FAILED"))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="free connectivity probe")
    ap.add_argument("--submit", action="store_true", help="create the throwaway job")
    a = ap.parse_args()
    if not (a.check or a.submit):
        ap.error("pass --check or --submit")
    cfg = load_env()
    ver = probe(cfg)
    if a.submit:
        print()
        submit(cfg, ver)
