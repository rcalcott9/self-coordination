"""SHAPES SELF pilot: GPT-5.5 reasoning-summary coding, action vs prediction calls. Local only, no API calls.

Single coder (Claude, 2026-10-14), hand-coded from the visible reasoning summaries (OpenAI summary=auto),
NOT from the hidden reasoning. Categories overlap; each needs an explicit textual reference:
  CS   copy symmetry: the other player is the same model / identical instance / same reasoning / clone /
       superrationality. General statements about "models" or "others" do not count.
  SAL  shape salience: a named shape is described as standing out, focal, simplest, canonical, distinctive,
       culturally special. A shape merely named, or named only as alphabetically first, does not count.
  ORD  option order: presentation order, randomization, position, or first-listed option in this prompt.
  SAFE safety / expected payoff: KEEP as safe/guaranteed/risk-dominant, expected payoff/value, or the .7 threshold.
  ALPHA (supplementary, not requested): alphabetical order used as a tie-breaker.
Borderline calls recorded in NOTES and coded 0. Not reliability-tested; the earlier Study 3 trace coding
failed reliability (AC1 .27), so these counts are descriptive only.
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
RUN = os.path.dirname(HERE)
CATS = ["CS", "SAL", "ORD", "SAFE", "ALPHA"]
C = {  # call index -> set of codes
 "action": {0: "SAL ALPHA", 2: "CS SAL ORD SAFE ALPHA", 3: "CS SAL SAFE", 9: "CS SAL ORD SAFE ALPHA", 13: "SAL ORD SAFE",
            14: "CS", 16: "CS SAFE", 21: "CS SAL ORD SAFE ALPHA", 22: "SAL ORD", 24: "SAL SAFE", 26: "CS SAL ORD SAFE",
            27: "CS ORD SAFE", 28: "CS SAL SAFE ALPHA", 29: "SAL", 30: "CS SAL ORD SAFE ALPHA", 31: "CS SAL ORD SAFE ALPHA",
            32: "CS SAL ORD SAFE", 33: "CS SAL SAFE", 34: "CS SAL SAFE", 36: "SAL ORD", 37: "CS SAL", 38: "CS SAL", 39: "ORD ALPHA"},
 "prediction": {0: "ORD", 3: "CS SAL ORD SAFE", 4: "ORD SAFE", 6: "CS SAL ORD SAFE", 9: "SAL ORD SAFE", 11: "SAL ORD SAFE",
                13: "SAL ORD SAFE", 14: "CS SAL ORD SAFE ALPHA", 15: "ORD", 16: "", 17: "ORD", 18: "SAL SAFE ALPHA", 19: ""},
}
NOTES = {
 "action|14": "SAL 0: 'focal label' with no shape named.",
 "action|27": "SAL 0: CIRCLE named without any attribute.",
 "action|28": "ORD 0: 'four shapes without any order info' ambiguous.",
 "action|37": "SAFE 0: KEEP sentence garbled ('yield 0 both ways').",
 "action|39": "SAL 0: 'CIRCLE might be common for many language models' is a population claim, not a shape attribute.",
 "prediction|4": "CS 0: 'If I were in the same situation' is self-as-player, not copy.",
 "prediction|11": "CS 0: 'deterministic nature of the model' without reference to the other player.",
 "prediction|13": "CS 0: 'If most models lean towards CIRCLE' is a population claim.",
 "prediction|17": "CS 0: 'players are independent instances' concerns sampling, not symmetry.",
 "prediction|18": "ORD 0: 'star ... often listed first' refers to lists in general, not this prompt.",
}


def main():
    rows = [json.loads(l) for l in open(os.path.join(RUN, "pilot_responses.jsonl"))]
    out, tab = [], {}
    for r in rows:
        if r["model"] != "gpt-5.5":
            continue
        s = "\n".join(x["text"] for o in r["raw"]["output"] if o["type"] == "reasoning" for x in o.get("summary") or [])
        k, i = r["kind"], r["i"]
        has = bool(s.strip())
        assert has == (i in C[k]), (k, i)
        codes = set(C[k].get(i, "").split())
        out.append(dict(call_id=r["call_id"], kind=k, i=i, order=r["order"], response=r["response"], has_summary=has,
                        reasoning_tokens=r["usage"]["output_tokens_details"]["reasoning_tokens"],
                        **{c: int(c in codes) for c in CATS}, note=NOTES.get(f"{k}|{i}", ""), summary=s))
    json.dump(out, open(os.path.join(HERE, "gpt_reasoning_coded.json"), "w"), indent=1)
    for k in ("action", "prediction"):
        xs = [x for x in out if x["kind"] == k]; ys = [x for x in xs if x["has_summary"]]
        tab[k] = dict(n_calls=len(xs), n_with_summary=len(ys), **{c: sum(y[c] for y in ys) for c in CATS})
        print(k, tab[k])
    acts = [x for x in out if x["kind"] == "action" and x["has_summary"]]
    for c in CATS:
        sub = [json.loads(x["response"])["action"] for x in acts if x[c]]
        print(f"action choices | {c}: n={len(sub)} KEEP={sub.count('KEEP')} STAR={sub.count('STAR')} CIRCLE={sub.count('CIRCLE')}")
    json.dump(tab, open(os.path.join(HERE, "counts.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
