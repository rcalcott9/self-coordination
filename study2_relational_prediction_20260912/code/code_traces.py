"""Exploratory coding of Study 2 reasoning traces.

The null says partner identity did not move predictions. These codes ask whether the partner
label registered in the reasoning at all, and what the models reasoned about instead.
Transparent regex rules, multi-label, hand-validated on a random sample.
"""
import glob, json, os, re, sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PAT = {
 # does the partner's identity appear at all?
 "partner_mentioned": re.compile(r"\b(other model|another model|the other (one|ai|agent)|"
     r"partner|copy of (me|myself)|same model|another instance|identical model)\b", re.I),
 # names the specific other family
 "names_other_family": re.compile(r"\b(claude|opus|gpt[- ]?5|gpt)\b", re.I),
 # reasons about a DIFFERENCE between the two models
 "model_difference": re.compile(r"\b(different (model|architecture|training|preferences|"
     r"policy|biases)|trained differently|another lab|may differ|might differ|"
     r"differ(s|ent) from (me|mine)|not necessarily the same)\b", re.I),
 # reasons about SAMENESS / shared policy
 "model_sameness": re.compile(r"\b(same (model|policy|preferences|training|biases)|"
     r"identical|like me|as i would|mirror(s)? my|shares my|we would both)\b", re.I),
 # introspects on own choice
 "self_policy": re.compile(r"\b(i would (pick|choose|select)|my own (choice|preference)|"
     r"what i('d| would) (pick|choose)|if i were choosing)\b", re.I),
 # stimulus-level salience reasoning (model-agnostic)
 "salience": re.compile(r"\b(salien\w+|distinct\w+|stand(s)? out|most unusual|odd one|"
     r"unique|conspicuous|eye-?catching|smoothest|spikiest|jagged|irregular)\b", re.I),
 # explicit focal-point / coordination framing
 "schelling": re.compile(r"\b(schelling|focal point|coordinat\w+|converge|common choice)\b", re.I),
 # hedging toward uniform
 "hedge_uniform": re.compile(r"\b(uniform|spread (it|them|the mass)|even(ly)? (split|spread)|"
     r"no (clear|strong) basis|hard to say|25%|roughly equal)\b", re.I),
 # worries about randomized position
 "position": re.compile(r"\b(position|order|left-to-right|randomi[sz]ed|shuffled|slot)\b", re.I),
}


def main():
    run = sorted(glob.glob(os.path.join(HERE, "results", "run_2026*")))[-1]
    rs = [json.loads(l) for l in open(os.path.join(run, "raw", "study2.jsonl"))]
    has = [r for r in rs if r.get("reasoning")]
    for r in has:
        t = r["reasoning"]
        r["codes"] = {k: bool(p.search(t)) for k, p in PAT.items()}
    print(f"traces with reasoning: {len(has)}/{len(rs)}")
    cov = Counter((r["focal"], r["condition"]) for r in has)
    print("coverage by cell:", dict(cov))
    print()
    for focal in ("gpt", "claude"):
        g = [r for r in has if r["focal"] == focal]
        if not g:
            continue
        C = [r for r in g if r["condition"] == "COPY"]
        D = [r for r in g if r["condition"] == "DIFFERENT"]
        nm = "GPT-5.5" if focal == "gpt" else "Opus 5"
        print(f"--- {nm}  (COPY n={len(C)}, DIFFERENT n={len(D)}) ---")
        print(f"  {'code':<22}{'COPY':>8}{'DIFF':>8}{'diff':>9}")
        for k in PAT:
            a = sum(r["codes"][k] for r in C) / len(C) if C else float("nan")
            b = sum(r["codes"][k] for r in D) / len(D) if D else float("nan")
            star = " *" if abs(a - b) > 0.15 else ""
            print(f"  {k:<22}{a:>8.3f}{b:>8.3f}{b-a:>+9.3f}{star}")
        print()
    json.dump([{k: r[k] for k in ("focal", "condition", "sid", "codes", "reasoning")}
               for r in has], open(os.path.join(run, "trace_codes.json"), "w"), indent=1)
    print("* = |difference| > 0.15 (descriptive only, exploratory)")


if __name__ == "__main__":
    main()
