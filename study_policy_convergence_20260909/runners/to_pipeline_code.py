"""Adapter: code-pilot raw CSV -> the aid_perm schema analysis/run_stage1.py reads.

Same role as to_pipeline.py, for the code arm. Writes ONLY into analysis_input/; the raw
run CSV stays the record.

CHOICE OF POLICY FIELD. `canonical_index` is used as chosen_item, not `convention_group`.
Two reasons: it keeps k = 4 for every item, exactly as in the visual arm, so the two
figures are computed by the identical estimator and are comparable side by side; and
collapsing to convention groups makes k vary by item, which moves the chance floor and
the determinism decomposition item by item. The collapsed coding remains available in the
raw file for a sensitivity check.
"""
import csv, glob, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "analysis_input")
COLS = ["aid", "perm", "trial", "chosen_item", "chosen_position", "parse_ok", "ok",
        "api_model", "prompt_sha8"]
VINTAGE = {"gpt-4-turbo-2024-04-09": "2024-04", "gpt-4.1-2025-04-14": "2025-04",
           "gpt-5-2025-08-07": "2025-08", "gpt-5.5-2026-04-23": "2026-04",
           "claude-opus-4-5-20251101": "2025-11", "claude-opus-4-6": "2026-02",
           "claude-opus-4-7": "2026-04", "claude-opus-4-8": "2026-05",
           "claude-opus-5": "2026-07"}
STRATUM = {"gpt-4-turbo-2024-04-09": "G-SAMPLE", "gpt-4.1-2025-04-14": "G-SAMPLE",
           "gpt-5-2025-08-07": "G-REASON", "gpt-5.5-2026-04-23": "G-REASON",
           "claude-opus-4-5-20251101": "C-OFF", "claude-opus-4-6": "C-OFF",
           "claude-opus-4-7": "C-OFF", "claude-opus-4-8": "C-OFF",
           "claude-opus-5": "C-OFF"}


def main():
    files = sorted(glob.glob(os.path.join(ROOT, "runs/code_pilot/code_pilot_*.csv")))
    assert len(files) == 1, files
    rows = list(csv.DictReader(open(files[0])))
    assert len(rows) == 5184, len(rows)
    by = {}
    shas, items = set(), set()
    for r in rows:
        mid = r["checkpoint_returned"]
        assert r["domain"] == "code", r["domain"]
        ok = r["parse_ok"] in ("True", "1", "true") and r["transport_ok"] in ("True", "1", "true")
        by.setdefault(mid, []).append(dict(
            aid=r["item_id"], perm=r["presentation_id"], trial=r["trial"],
            chosen_item=r["canonical_index"] if ok else "",
            chosen_position=r["display_position"] if ok else "",
            parse_ok=str(ok), ok=str(r["transport_ok"] in ("True", "1", "true")),
            api_model=mid, prompt_sha8=r["prompt_hash"]))
        shas.add(r["prompt_hash"]); items.add(r["item_id"])
    assert len(by) == 9, sorted(by)
    assert len(items) == 12, len(items)
    assert len(shas) == 1, shas
    os.makedirs(OUT, exist_ok=True)
    models = []
    for mid in sorted(by):
        assert len(by[mid]) == 12 * 48, (mid, len(by[mid]))
        p = os.path.join(OUT, f"code_{mid}.csv")
        with open(p, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=COLS); w.writeheader(); w.writerows(by[mid])
        models.append(dict(model_id=mid, family="gpt" if mid.startswith("gpt") else "claude",
                           files=[p], schema="aid_perm", api_model_contains=mid,
                           vintage_date=VINTAGE[mid], stratum=STRATUM[mid]))
    src = dict(_note="Code-arm pilot (12 items x 9 checkpoints x n=48), adapter view of "
                     "runs/code_pilot/. chosen_item = canonical_index (k=4), matching the "
                     "visual arm's estimator exactly.",
               domain="code", k_options=4,
               battery_manifest="", stimuli_root="",
               expect_prompt_sha8=sorted(shas)[0], models=models)
    sp = os.path.join(ROOT, "analysis", "sources_code_pilot.json")
    json.dump(src, open(sp, "w"), indent=1)
    print(f"wrote {len(models)} model files + {os.path.basename(sp)}  "
          f"items={len(items)} prompt_sha={sorted(shas)[0]}")


if __name__ == "__main__":
    main()
