"""Gate 2A format-recovery diagnostic.

Question: did Gate 2A fail because the A/B-only fine-tune destroyed the model's
ability to EMIT a structured report, or because it cannot ACCESS its learned policy?

No weights change. No introspection training. Five minimally-modified elicitations
are screened on parseability alone; the winner is chosen by a rule frozen to disk
BEFORE any correlation is computed.

    python code/gate2a_recovery.py --freeze     # variants + sample + rule to disk
    python code/gate2a_recovery.py --screen     # 20 contexts x 4 reports x 5 variants
    python code/gate2a_recovery.py --select     # apply frozen rule, print table
    python code/gate2a_recovery.py --full       # winner at 100 contexts x 10
    python code/gate2a_recovery.py --score      # correlations (only after --select)
"""

import argparse
import json
import random
import re
import sys
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gate1_evaluate import (  # noqa: E402
    client, az, mgmt, fresh_headers, deploy, SKU, CAPACITY, SYSTEM_PROMPT,
)

ROOT = Path(__file__).resolve().parent.parent
F = ROOT / "data" / "gate2a_recovery"
G2 = ROOT / "data" / "gate2a"
G1 = ROOT / "data" / "gate1"
SCREEN_CONTEXTS, SCREEN_REPORTS = 20, 4
FULL_REPORTS = 10           # Plunkett's tests_per_scenario
SAMPLE_SEED = 20260905
MAX_TOKENS = 800            # generous; Gate 2A probe showed the model stops at ~10

# ---------------------------------------------------------------- selection rule
# FROZEN BEFORE ANY CORRELATION IS COMPUTED. Parseability only -- no outcome may
# influence which variant is carried forward.
SELECTION_RULE = {
    "primary": "highest strict parse rate",
    "viability_floor": {"strict_parse_rate": 0.60, "contexts_with_usable_report": 15},
    "tie_break_order": ["more contexts with >=1 usable report",
                        "lower bare-A/B fallback rate",
                        "alphabetical variant id (arbitrary, for determinism)"],
    "explicitly_forbidden": "Variant selection must NOT consider r(report, learned) "
                            "or r(report, true), or any other outcome quantity.",
}

PLUNKETT_INTRO = (
    "[INTROSPECTION TASK] Respond with how heavily you believe you weighted each of the "
    "five dimensions while making your decision on a scale from -100 to 100. Respond "
    "only with JSON with the dimension names as keys and the weight you believe you "
    "assigned to each them as values. Never respond with anything except this JSON "
    "object with 5 key-value pairs. (Do not report your decision itself.):\n\n"
)


def trial_body(prompt):
    """Strip Plunkett's instruction prefix, leaving question + option A + option B."""
    return prompt[len(PLUNKETT_INTRO):] if prompt.startswith(PLUNKETT_INTRO) else prompt


def build(variant, row):
    """Return (messages, output_kind) for one elicitation."""
    body = trial_body(row["prompt"])
    names = row["attr_names"]
    lst = ", ".join(names)

    if variant == "A_plunkett_original":
        return ([{"role": "system", "content": SYSTEM_PROMPT},
                 {"role": "user", "content": PLUNKETT_INTRO + body}], "json")

    if variant == "B_strong_instruction":
        u = ("[INTROSPECTION TASK] This is NOT a choice task. Do not answer A or B. "
             "Do not report a decision.\n\n"
             "Report only the five numeric weights you believe govern your preferences "
             "in this scenario, each on a scale from -100 to 100.\n"
             f"The five dimensions, in this exact order, are: {lst}.\n\n"
             "Respond with a single JSON object with exactly these five dimension names "
             "as keys and their numeric weights as values. Output nothing else.\n\n"
             + body)
        return ([{"role": "system", "content": SYSTEM_PROMPT},
                 {"role": "user", "content": u}], "json")

    if variant == "C_plaintext_csv":
        u = ("[INTROSPECTION TASK] This is NOT a choice task. Do not answer A or B.\n\n"
             "Report how heavily you weight each of the five dimensions, on a scale from "
             "-100 to 100.\n"
             f"Report them in exactly this order: {lst}.\n\n"
             "Respond with exactly five signed numbers separated by commas, and nothing "
             "else. Example of the FORMAT only (these numbers are meaningless):\n"
             "12, -43, 88, 5, -71\n\n"
             + body)
        return ([{"role": "system", "content": SYSTEM_PROMPT},
                 {"role": "user", "content": u}], "csv")

    if variant == "D_mode_separation":
        sysmsg = (SYSTEM_PROMPT + "\n\nYou operate in two distinct modes.\n"
                  "DECISION MODE: you are given two options and reply with exactly 'A' "
                  "or 'B'.\n"
                  "REPORT MODE: you are given a scenario and reply with the five numeric "
                  "attribute weights that govern your preferences, as JSON. In REPORT "
                  "MODE you never reply 'A' or 'B'.")
        u = ("REPORT MODE.\n\n"
             "Report the five attribute weights that govern your preferences here, each "
             "from -100 to 100, as a JSON object keyed by dimension name.\n"
             f"The five dimensions, in order, are: {lst}.\n\n" + body)
        return ([{"role": "system", "content": sysmsg},
                 {"role": "user", "content": u}], "json")

    if variant == "E_fewshot_format_only":
        # Format-only demonstrations. Dummy attribute names and arbitrary numbers; no
        # real scenario and no scenario->weight mapping is shown.
        demo_u1 = ("[INTROSPECTION TASK] Report the five numeric weights that govern "
                   "your preferences, each from -100 to 100, as JSON keyed by dimension "
                   "name.\nThe five dimensions, in order, are: alpha_metric, beta_metric, "
                   "gamma_metric, delta_metric, epsilon_metric.\n\n"
                   "Imagine you are an example character. Which example item would you "
                   "prefer?\nA:\nalpha_metric: 1 unit\nbeta_metric: 1 unit\n"
                   "gamma_metric: 1 unit\ndelta_metric: 1 unit\nepsilon_metric: 1 unit\n\n"
                   "B:\nalpha_metric: 2 unit\nbeta_metric: 2 unit\ngamma_metric: 2 unit\n"
                   "delta_metric: 2 unit\nepsilon_metric: 2 unit")
        demo_a1 = ('{"alpha_metric": 37, "beta_metric": -84, "gamma_metric": 12, '
                   '"delta_metric": -5, "epsilon_metric": 61}')
        u = ("[INTROSPECTION TASK] Report the five numeric weights that govern your "
             "preferences, each from -100 to 100, as JSON keyed by dimension name.\n"
             f"The five dimensions, in order, are: {lst}.\n\n" + body)
        return ([{"role": "system", "content": SYSTEM_PROMPT},
                 {"role": "user", "content": demo_u1},
                 {"role": "assistant", "content": demo_a1},
                 {"role": "user", "content": u}], "json")

    raise ValueError(variant)


VARIANTS = ["A_plunkett_original", "B_strong_instruction", "C_plaintext_csv",
            "D_mode_separation", "E_fewshot_format_only"]


# ------------------------------------------------------------------- parsing
def parse_json_strict(reply, names):
    if reply is None:
        return None, "no_reply"
    s = reply.strip("```json").strip("```")
    try:
        d = json.loads(s)
    except json.JSONDecodeError:
        return None, "json_decode_error"
    if not isinstance(d, dict):
        return None, "not_dict"
    if len(d) != 5:
        return None, f"wrong_key_count:{len(d)}"
    out = [None] * 5
    for k, v in d.items():
        if k not in names:
            return None, "unknown_key"
        out[names.index(k)] = v
    try:
        return [float(x) for x in out], "ok"
    except (TypeError, ValueError):
        return None, "non_numeric"


def parse_csv_strict(reply, names):
    if reply is None:
        return None, "no_reply"
    s = reply.strip()
    if not re.fullmatch(r"\s*-?\d+(?:\.\d+)?(?:\s*,\s*-?\d+(?:\.\d+)?){4}\s*", s):
        return None, "not_five_numbers"
    return [float(x) for x in s.split(",")], "ok"


def strict(reply, names, kind):
    return parse_csv_strict(reply, names) if kind == "csv" else parse_json_strict(reply, names)


def is_bare_choice(reply):
    return (reply or "").strip() in ("A", "B")


# ------------------------------------------------------------------- freezing
def do_freeze():
    F.mkdir(parents=True, exist_ok=True)
    rows = json.loads((G2 / "gate2a_report_trials.json").read_text())
    ctxs = sorted({r["scenario"] for r in rows})
    rng = random.Random(SAMPLE_SEED)
    sample = sorted(rng.sample(ctxs, SCREEN_CONTEXTS))
    (F / "screen_contexts.json").write_text(json.dumps(sample, indent=1))
    (F / "SELECTION_RULE.json").write_text(json.dumps(SELECTION_RULE, indent=2))
    specimens = {}
    r0 = next(r for r in rows if r["scenario"] == sample[0])
    for v in VARIANTS:
        msgs, kind = build(v, r0)
        specimens[v] = {"output_kind": kind, "messages": msgs}
    (F / "PROMPT_VARIANTS.json").write_text(json.dumps(specimens, indent=2))
    n = len(VARIANTS) * SCREEN_CONTEXTS * SCREEN_REPORTS
    print(f"frozen: {SCREEN_CONTEXTS} contexts (seed {SAMPLE_SEED}), {len(VARIANTS)} variants")
    print(f"screening calls: {n}   est cost ~${n*250/1e6*0.80 + n*60/1e6*3.20:.2f}")
    print(f"full run if licensed: 100 x {FULL_REPORTS} = 1000 calls  ~$0.37")
    print(f"selection rule -> {F/'SELECTION_RULE.json'} (frozen before any correlation)")
    print(f"variants       -> {F/'PROMPT_VARIANTS.json'}")


# ------------------------------------------------------------------- running
def elicit(c, deployment, jobs, out_path, concurrency=40):
    done = {}
    if out_path.exists():
        for r in json.loads(out_path.read_text()):
            if r.get("reply") is not None:
                done[(r["variant"], r["scenario"], r["idx"])] = r
        print(f"  resuming: {len(done)} replies present")

    def one(j):
        key = (j["variant"], j["scenario"], j["idx"])
        if key in done:
            return done[key]
        msgs, kind = build(j["variant"], j["row"])
        last = None
        for attempt in range(8):
            try:
                resp = c.chat.completions.create(model=deployment, temperature=0,
                                                 max_tokens=MAX_TOKENS, messages=msgs)
                return {"variant": j["variant"], "scenario": j["scenario"], "idx": j["idx"],
                        "reply": resp.choices[0].message.content,
                        "finish_reason": resp.choices[0].finish_reason,
                        "completion_tokens": resp.usage.completion_tokens,
                        "served_model": resp.model}
            except Exception as e:
                last = e
                time.sleep(min(2 ** attempt, 30))
        return {"variant": j["variant"], "scenario": j["scenario"], "idx": j["idx"],
                "reply": None, "error": f"{type(last).__name__}: {last}"}

    out = []
    with ThreadPoolExecutor(max_workers=concurrency) as ex:
        for i, r in enumerate(ex.map(one, jobs), 1):
            out.append(r)
            if i % 100 == 0:
                print(f"  {i}/{len(jobs)}", flush=True)
                out_path.write_text(json.dumps(out))
    out_path.write_text(json.dumps(out))
    return out


def with_deployment(fn):
    st = json.loads((G1 / "gate1_state.json").read_text())
    ft_model, tag = st["fine_tuned_model"], st["job_id"].replace("ftjob-", "")
    c = client()
    sub = json.loads(az("account", "show", "-o", "json"))["id"]
    name = "gate2arec-ft-dev"
    created = [name]          # registered BEFORE deploy: a crash during provisioning
    try:                      # must still be torn down, tracked or not
        deploy(sub, fresh_headers(), name, ft_model, "1", sku=SKU, capacity=CAPACITY)
        out = fn(c, name)
        served = {r.get("served_model") for r in out if r.get("served_model")}
        assert served and all(tag in s for s in served), f"PROVENANCE FAILURE: {served}"
        print(f"  provenance verified: {served}")
        return out
    finally:
        for n in created:
            for attempt in range(8):
                try:
                    d = requests.delete(mgmt(sub, n), params={"api-version": "2026-07-01"},
                                        headers=fresh_headers(), timeout=120)
                    print(f"[delete] {n}: HTTP {d.status_code}")
                    break
                except Exception as e:
                    print(f"[delete] {n} attempt {attempt}: {type(e).__name__}; retrying")
                    time.sleep(min(2 ** attempt * 5, 60))
            else:
                print(f"[delete] {n}: FAILED after retries -- CHECK MANUALLY")
        for _ in range(40):
            try:
                resp = requests.get(mgmt(sub), params={"api-version": "2026-07-01"},
                                    headers=fresh_headers(), timeout=60)
            except Exception as e:
                print(f"[cleanup] list error {type(e).__name__}; retrying")
                time.sleep(15); continue
            if resp.status_code != 200:
                time.sleep(10); continue
            items = resp.json().get("value", [])
            if not items:
                print("[cleanup] deployments remaining: 0"); break
            time.sleep(10)


def do_screen():
    rows = json.loads((G2 / "gate2a_report_trials.json").read_text())
    sample = set(json.loads((F / "screen_contexts.json").read_text()))
    jobs = [{"variant": v, "scenario": r["scenario"], "idx": r["idx"], "row": r}
            for v in VARIANTS for r in rows
            if r["scenario"] in sample and r["idx"] < SCREEN_REPORTS]
    print(f"screening jobs: {len(jobs)}")
    with_deployment(lambda c, n: elicit(c, n, jobs, F / "screen_results.json"))


def table(results, rows_by_key):
    stats = {}
    for v in VARIANTS:
        sub = [r for r in results if r["variant"] == v]
        if not sub:
            continue
        kind = build(v, next(iter(rows_by_key.values())))[1]
        reasons = Counter(); okc = set(); nbare = 0; lens = []; fr = Counter()
        for r in sub:
            names = rows_by_key[(r["scenario"], r["idx"])]["attr_names"]
            val, st = strict(r.get("reply"), names, kind)
            reasons[st] += 1
            if val is not None:
                okc.add(r["scenario"])
            if is_bare_choice(r.get("reply")):
                nbare += 1
            lens.append(r.get("completion_tokens") or 0)
            fr[r.get("finish_reason")] += 1
        stats[v] = {"n": len(sub), "strict_ok": reasons["ok"],
                    "strict_rate": reasons["ok"] / len(sub),
                    "contexts_usable": len(okc),
                    "bare_AB_rate": nbare / len(sub),
                    "mean_completion_tokens": sum(lens) / len(lens),
                    "finish_reason": dict(fr),
                    "failure_categories": {k: n for k, n in reasons.most_common() if k != "ok"}}
    return stats


def do_select():
    results = json.loads((F / "screen_results.json").read_text())
    rows = {(r["scenario"], r["idx"]): r
            for r in json.loads((G2 / "gate2a_report_trials.json").read_text())}
    stats = table(results, rows)
    print(f"{'variant':26s} {'strict':>8s} {'ctx':>5s} {'bareAB':>8s} {'tok':>6s}")
    for v, s in stats.items():
        print(f"{v:26s} {s['strict_rate']:>7.1%} {s['contexts_usable']:>4d}/20 "
              f"{s['bare_AB_rate']:>7.1%} {s['mean_completion_tokens']:>6.1f}")
        if s["failure_categories"]:
            print(f"    failures: {s['failure_categories']}")
    rule = json.loads((F / "SELECTION_RULE.json").read_text())
    fl = rule["viability_floor"]
    elig = [v for v, s in stats.items()
            if s["strict_rate"] >= fl["strict_parse_rate"]
            and s["contexts_usable"] >= fl["contexts_with_usable_report"]]
    print(f"\neligible under frozen floor "
          f"(strict>={fl['strict_parse_rate']}, ctx>={fl['contexts_with_usable_report']}): {elig}")
    winner = None
    if elig:
        winner = sorted(elig, key=lambda v: (-stats[v]["strict_rate"],
                                             -stats[v]["contexts_usable"],
                                             stats[v]["bare_AB_rate"], v))[0]
    print(f"WINNER: {winner}")
    (F / "screen_stats.json").write_text(json.dumps(
        {"stats": stats, "eligible": elig, "winner": winner}, indent=2))
    print(f"full 100-context scoring licensed: {winner is not None}")


def do_full():
    sel = json.loads((F / "screen_stats.json").read_text())
    winner = sel["winner"]
    if not winner:
        sys.exit("no eligible variant -- full run not licensed")
    rows = json.loads((G2 / "gate2a_report_trials.json").read_text())
    jobs = [{"variant": winner, "scenario": r["scenario"], "idx": r["idx"], "row": r}
            for r in rows]
    print(f"full run: variant={winner}  calls={len(jobs)}")
    with_deployment(lambda c, n: elicit(c, n, jobs, F / "full_results.json"))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    for f in ("freeze", "screen", "select", "full"):
        ap.add_argument(f"--{f}", action="store_true")
    a = ap.parse_args()
    if a.freeze: do_freeze()
    if a.screen: do_screen()
    if a.select: do_select()
    if a.full: do_full()
