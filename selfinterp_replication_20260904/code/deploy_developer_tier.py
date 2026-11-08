"""Attempt a Developer-tier (no hourly hosting fee) deployment of a fine-tuned model.

Decision procedure fixed in advance, per the run plan:

  * Developer tier ACCEPTED for gpt-4o-mini -> run the whole project on gpt-4o-mini
    (Plunkett's own base model, literal replication, zero hosting cost).
  * Developer tier REJECTED -> create NO paid deployment. Fall back to gpt-4.1-mini
    on Developer tier, keeping gpt-4o-mini as a literal-replication diagnostic only.

This script never creates a Standard or GlobalStandard deployment. The only sku it
will ever send is "DeveloperTier"; a rejection is recorded and the script exits.

Auth: management plane, so it needs an Azure AD token, not the data-plane key.
    az login
    python code/deploy_developer_tier.py --list          # show what exists
    python code/deploy_developer_tier.py --deploy        # attempt Developer tier
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
RESOURCE_GROUP = "self_coord"
RESOURCE_NAME = "self-coord"
API_VERSION = "2026-07-01"
OUT = ROOT / "data" / "gate0"

# The only sku this script is permitted to request.
DEVELOPER_SKU = "DeveloperTier"


def az(*args):
    r = subprocess.run(["az", *args], capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"az {' '.join(args)} failed:\n{r.stderr.strip()}")
    return r.stdout.strip()


def token_and_subscription():
    try:
        acct = json.loads(az("account", "show", "-o", "json"))
    except FileNotFoundError:
        sys.exit("az CLI not found -- install it and run `az login` first")
    sub = acct["id"]
    tok = json.loads(
        az("account", "get-access-token", "--resource", "https://management.azure.com/", "-o", "json")
    )["accessToken"]
    print(f"subscription : {sub}  ({acct.get('name')})")
    print(f"tenant       : {acct.get('tenantId')}")
    return tok, sub


def base_url(sub, deployment=None):
    u = (
        f"https://management.azure.com/subscriptions/{sub}/resourceGroups/{RESOURCE_GROUP}"
        f"/providers/Microsoft.CognitiveServices/accounts/{RESOURCE_NAME}/deployments"
    )
    return f"{u}/{deployment}" if deployment else u


def list_deployments(tok, sub):
    r = requests.get(
        base_url(sub), params={"api-version": API_VERSION},
        headers={"Authorization": f"Bearer {tok}"}, timeout=60,
    )
    print(f"\nHTTP {r.status_code} listing deployments")
    if r.status_code != 200:
        print(r.text[:600])
        return
    items = r.json().get("value", [])
    if not items:
        print("  (none -- nothing is billing)")
    for d in items:
        sku = d.get("sku", {})
        print(f"  {d['name']}: model={d['properties']['model']['name']} "
              f"sku={sku.get('name')} capacity={sku.get('capacity')}")


def deploy(tok, sub, fine_tuned_model, deployment_name):
    body = {
        "sku": {"name": DEVELOPER_SKU, "capacity": 1},
        "properties": {
            "model": {"format": "OpenAI", "name": fine_tuned_model, "version": "1"}
        },
    }
    print(f"\nattempting {DEVELOPER_SKU} deployment")
    print(f"  model      : {fine_tuned_model}")
    print(f"  deployment : {deployment_name}")
    r = requests.put(
        base_url(sub, deployment_name), params={"api-version": API_VERSION},
        headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json"},
        json=body, timeout=120,
    )
    print(f"\nHTTP {r.status_code}")
    try:
        payload = r.json()
    except ValueError:
        payload = {"raw": r.text[:1000]}
    print(json.dumps(payload, indent=2)[:1500])

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "developer_tier_attempt.json").write_text(
        json.dumps({"status": r.status_code, "request": body, "response": payload}, indent=2)
    )

    if r.status_code in (200, 201, 202):
        print("\nDEVELOPER TIER ACCEPTED -> run the full project on this model.")
        print("Verify no hourly charge appears in Cost Analysis before Phase A spend.")
        return True
    print("\nDEVELOPER TIER REJECTED -> creating NO paid deployment.")
    print("Fall back: gpt-4.1-mini on Developer tier; keep gpt-4o-mini as diagnostic only.")
    return False


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--deploy", action="store_true")
    ap.add_argument("--model", help="fine_tuned_model id from the completed job")
    ap.add_argument("--name", default="gate0-4omini-dev", help="deployment name")
    a = ap.parse_args()
    if not (a.list or a.deploy):
        ap.error("pass --list or --deploy")

    tok, sub = token_and_subscription()
    if a.list:
        list_deployments(tok, sub)
    if a.deploy:
        if not a.model:
            sys.exit("--deploy needs --model <fine_tuned_model id>")
        deploy(tok, sub, a.model, a.name)
