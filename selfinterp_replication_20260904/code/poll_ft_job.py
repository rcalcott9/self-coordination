"""Poll a fine-tuning job to a terminal state. Tolerates the transient DNS/TLS faults
seen on this network -- a failed poll is retried, not treated as job failure."""
import json, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
cfg = {}
for line in (ROOT/'.env').read_text().splitlines():
    if '=' in line and not line.strip().startswith('#'):
        k,_,v = line.partition('='); cfg[k.strip()] = v.strip()
from openai import AzureOpenAI
c = AzureOpenAI(azure_endpoint=cfg['AZURE_OPENAI_ENDPOINT'], api_key=cfg['AZURE_OPENAI_API_KEY'],
                api_version='2025-04-01-preview')
job_id = sys.argv[1]
net_errors = 0
while True:
    try:
        j = c.fine_tuning.jobs.retrieve(job_id)
        net_errors = 0
        print(f"{time.strftime('%H:%M:%S')}  {j.status}  trained_tokens={getattr(j,'trained_tokens',None)}", flush=True)
        if j.status in ("succeeded","failed","cancelled"):
            print(f"\nFINAL: {j.status}")
            print(f"fine_tuned_model: {j.fine_tuned_model}")
            print(f"hyperparameters : {getattr(j,'hyperparameters',None)}")
            print(f"trained_tokens  : {getattr(j,'trained_tokens',None)}")
            if getattr(j,'error',None): print(f"error: {j.error}")
            (ROOT/'data'/'gate0'/'gate0_job_final.json').write_text(
                json.dumps(j.model_dump(), indent=2, default=str))
            break
    except Exception as e:
        net_errors += 1
        print(f"{time.strftime('%H:%M:%S')}  poll error ({net_errors}): {type(e).__name__}", flush=True)
        if net_errors >= 40:
            print("giving up after 40 consecutive network errors"); break
    time.sleep(60)
