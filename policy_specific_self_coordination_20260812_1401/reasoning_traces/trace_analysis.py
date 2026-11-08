"""
Stage C reasoning-trace analysis.

EXPLORATORY AND POST HOC. None of this was pre-specified. Lexical counts are weak
proxies for what a model is "doing"; they measure what the rationale SAYS, which is
not the same thing. No API calls, no change to any prior analysis.

WHAT IS ACTUALLY AVAILABLE - established before analysing anything:

  the prompt-mandated one-sentence rationale (text before "DECISION:")
      present for 1160/1200 trials, both models          <- primary corpus
  the provider reasoning/thinking summary (visible_reasoning)
      GPT-5.5   323/720 trials (45%)
      Claude Opus 5  5/480 trials (1%)                   <- unusable
  Claude ran adaptive thinking at effort=low; on a one-shot binary decision it
  mostly did not produce a summarisable thinking block. The GPT summaries are a
  45% subsample of one model only, so they are described, never used for inference.

THE QUESTION WORTH ASKING. Stage C showed that betting tracks own-copy reliability
within pairs matched on public appearance. Does the stated rationale carry the same
information? Two readings, and they are distinguishable:

  aligned      rationales hedge more on the low-reliability stimulus, so the model
               says what its betting implies
  dissociated  rationales assert a salient form just as often on both, and the
               policy-specific information appears only in the choice

The project's own Step 1b finding predicts dissociation: a model with no transferable
rule "defaults to a side and then justifies it in form language".

Run:  python3 trace_analysis.py
"""
import csv, glob, json, math, os, re, sys, random
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
DATA = os.path.join(EXP, "data")
BOOT, SEED = 5000, 20260813
LBL = {"gpt": "GPT-5.5", "claude": "Claude Opus 5"}

# Canonical pair order, identical to every other figure/table in the project.
CANON = [("gpt", "c_contr_subtle", "b_spiral_cw"),
         ("gpt", "s_convexity", "d_dens_extreme"),
         ("gpt", "c_open_cplx", "s_density"),
         ("claude", "b_spiral_cw", "rot"),
         ("claude", "s_convexity", "d_dens_extreme")]

# Lexicons built by reading the corpus first, not guessed a priori. Each is a
# transparent regex list; every hit is a surface-form match, nothing more.
LEX = {
    "hedge_no_rule": r"(unclear|ambiguous|not obvious|no (?:clear|obvious|strong)|"
                     r"hard to|difficult to|weak(?:ly)?|too similar|very similar|"
                     r"little to distinguish|toss-?up|coin[- ]?flip|50[/-]?50|"
                     r"arbitrar|uncertain|either way|no reliable|lacks?)",
    "asserts_salient": r"(salient|distinctive|obvious|focal|canonical|stands out|"
                       r"more (?:visually )?(?:striking|prominent|notable)|clearly)",
    "partner_self_ref": r"(another instance|other instance|identical model|same model|"
                        r"a copy|copies|another copy|the other player|itself|my copy)",
    "payoff_reasoning": r"(guaranteed|safe \d|\d+ points|expected|worth|beats|"
                        r"risk|payoff|not worth|better than)",
    "explicit_chance": r"(coin[- ]?flip|50[/-]?50|chance|random|even odds|gamble)",
    "position_word": r"\b(left|right|leftmost|rightmost|upper|lower|top|bottom)\b",
}
STOP = set("the a an and or of to in on is are be it its i we as so that this these "
           "those with for by at from will would should could more most than then "
           "one two both other another there here if but which while about into over "
           "them they he she you your my me our".split())


def newest(pat):
    return max(glob.glob(os.path.join(DATA, pat)), key=os.path.getmtime)


def rationale(row):
    return re.split(r"DECISION:", row["response_raw"], flags=re.I)[0].strip()


def boot_ci(vals, seed, b=BOOT):
    if not vals:
        return float("nan"), float("nan")
    rng = random.Random(seed)
    n = len(vals)
    d = sorted(sum(rng.choices(vals, k=n)) / n for _ in range(b))
    return d[int(0.025 * b)], d[int(0.975 * b)]


def logodds_dirichlet(counts_a, counts_b, prior, min_count=8):
    """Monroe et al. informative-Dirichlet log-odds z-scores for a 2-corpus contrast."""
    na, nb, n0 = sum(counts_a.values()), sum(counts_b.values()), sum(prior.values())
    out = []
    for w in set(counts_a) | set(counts_b):
        if counts_a[w] + counts_b[w] < min_count:
            continue
        a0 = prior[w]
        ya, yb = counts_a[w] + a0, counts_b[w] + a0
        d = math.log(ya / (na + n0 - ya)) - math.log(yb / (nb + n0 - yb))
        var = 1.0 / ya + 1.0 / yb
        out.append((d / math.sqrt(var), w, counts_a[w], counts_b[w]))
    return sorted(out, reverse=True)


def main():
    rows = [r for r in csv.DictReader(open(newest("stageC_2*.csv")))
            if r["included_in_analysis"] == "True"]
    fresh = {(r["model"], r["stimulus"]): r
             for r in csv.DictReader(open(os.path.join(DATA, "fresh_self_match.csv")))}
    pair_of = {}
    for i, (m, hi, lo) in enumerate(CANON, start=1):
        pair_of[(m, hi)] = (i, "high"); pair_of[(m, lo)] = (i, "low")

    for r in rows:
        r["_rat"] = rationale(r)
        r["_fc"] = float(fresh[(r["actor_model"], r["stimulus"])]["form_consistency"])
        r["_pair"], r["_side"] = pair_of[(r["actor_model"], r["stimulus"])]
        t = r["_rat"].lower()
        for k, pat in LEX.items():
            r[k] = 1 if re.search(pat, t) else 0
        r["_len"] = len(r["_rat"].split())

    corpus = [r for r in rows if r["_rat"]]
    print("=" * 78)
    print("STAGE C REASONING-TRACE ANALYSIS   (exploratory, post hoc)")
    print("=" * 78)
    print(f"  Stage C trials                : {len(rows)}")
    print(f"  with a rationale sentence     : {len(corpus)} "
          f"({len(corpus)/len(rows):.1%})  <- primary corpus")
    for m in ("gpt", "claude"):
        sub = [r for r in rows if r["actor_model"] == m]
        vr = sum(1 for r in sub if r["visible_reasoning"].strip())
        rr = sum(1 for r in sub if r["_rat"])
        print(f"    {LBL[m]:14} rationale {rr}/{len(sub)}   "
              f"provider reasoning summary {vr}/{len(sub)} ({vr/len(sub):.0%})")
    print("  Provider summaries are GPT-only and ~45% present; described later,")
    print("  never used for inference.")

    # ---------------- descriptive rates ----------------
    print("\nLEXICAL FEATURE RATES  (share of rationales containing >=1 match)")
    keys = list(LEX)
    print(f"  {'feature':18}" + "".join(f"{k:>12}" for k in ("ATTEMPT", "SAFE"))
          + f"{'diff':>9}   {'95% CI of diff':>20}")
    feat_rows = []
    for k in keys:
        A = [r[k] for r in corpus if r["participation_decision"] == "ATTEMPT"]
        S = [r[k] for r in corpus if r["participation_decision"] == "SAFE"]
        diff = sum(A)/len(A) - sum(S)/len(S)
        rng = random.Random(SEED)
        d = sorted((sum(rng.choices(A, k=len(A)))/len(A)) - (sum(rng.choices(S, k=len(S)))/len(S))
                   for _ in range(BOOT))
        lo, hi = d[int(.025*BOOT)], d[int(.975*BOOT)]
        star = "*" if (lo > 0 or hi < 0) else " "
        print(f" {star}{k:18}{sum(A)/len(A):12.3f}{sum(S)/len(S):12.3f}{diff:+9.3f}   "
              f"[{lo:+.3f}, {hi:+.3f}]")
        feat_rows.append(dict(feature=k, rate_attempt=round(sum(A)/len(A), 4),
                              rate_safe=round(sum(S)/len(S), 4), diff=round(diff, 4),
                              ci_lo=round(lo, 4), ci_hi=round(hi, 4),
                              n_attempt=len(A), n_safe=len(S)))

    # ---------------- the dissociation test ----------------
    print("\nWITHIN-PAIR CONTRAST  (high minus low reliability, matched on public appearance)")
    print("  Does the rationale carry the same information the betting does?")
    pair_rows = []
    for k in keys:
        print(f"\n  {k}")
        alld = []
        for i, (m, hi, lo) in enumerate(CANON, start=1):
            H = [r[k] for r in corpus if r["_pair"] == i and r["_side"] == "high"]
            L = [r[k] for r in corpus if r["_pair"] == i and r["_side"] == "low"]
            if not H or not L:
                continue
            diff = sum(H)/len(H) - sum(L)/len(L)
            rng = random.Random(SEED + i)
            d = sorted((sum(rng.choices(H, k=len(H)))/len(H))
                       - (sum(rng.choices(L, k=len(L)))/len(L)) for _ in range(BOOT))
            lo_, hi_ = d[int(.025*BOOT)], d[int(.975*BOOT)]
            alld.append(diff)
            star = "*" if (lo_ > 0 or hi_ < 0) else " "
            print(f"   {star}Pair {i} {LBL[m]:14} high {sum(H)/len(H):.3f}  "
                  f"low {sum(L)/len(L):.3f}  diff {diff:+.3f}  [{lo_:+.3f}, {hi_:+.3f}]")
            pair_rows.append(dict(feature=k, pair=i, model=m, stimulus_high=hi,
                                  stimulus_low=lo, rate_high=round(sum(H)/len(H), 4),
                                  rate_low=round(sum(L)/len(L), 4), diff=round(diff, 4),
                                  ci_lo=round(lo_, 4), ci_hi=round(hi_, 4)))
        pos = sum(1 for x in alld if x > 0)
        print(f"    -> {pos}/{len(alld)} pairs positive; median diff {sorted(alld)[len(alld)//2]:+.3f}")

    # ---------------- rationalisation check ----------------
    print("\nRATIONALISATION CHECK")
    print("  On stimuli where the model has NO transferable rule (form consistency < 0.80),")
    print("  do ATTEMPT rationales still assert a salient form?")
    for lab, sel in (("form rule (FC >= 0.80)", lambda r: r["_fc"] >= 0.80),
                     ("position fallback (FC < 0.80)", lambda r: r["_fc"] < 0.80)):
        sub = [r for r in corpus if sel(r) and r["participation_decision"] == "ATTEMPT"]
        if not sub:
            continue
        sal = sum(r["asserts_salient"] for r in sub) / len(sub)
        hedge = sum(r["hedge_no_rule"] for r in sub) / len(sub)
        lo, hi = boot_ci([r["asserts_salient"] for r in sub], SEED)
        print(f"    {lab:30} n={len(sub):4}  asserts salient form {sal:.3f} "
              f"[{lo:.3f}, {hi:.3f}]   hedges {hedge:.3f}")
    print("  A similar 'asserts salient' rate on both is the signature the Step 1b")
    print("  screen described: a side default dressed in form language.")

    # ---------------- payoff gradient ----------------
    print("\nHEDGING BY SAFE PAYOFF  (does stated uncertainty rise as the stakes rise?)")
    for sp in (3, 5, 7, 9):
        sub = [r for r in corpus if int(r["safe_payoff"]) == sp]
        h = sum(r["hedge_no_rule"] for r in sub)/len(sub)
        c = sum(r["explicit_chance"] for r in sub)/len(sub)
        p = sum(r["payoff_reasoning"] for r in sub)/len(sub)
        print(f"    safe={sp}  n={len(sub):4}  hedging {h:.3f}   explicit chance {c:.3f}"
              f"   payoff reasoning {p:.3f}")

    # ---------------- distinctive vocabulary ----------------
    print("\nDISTINCTIVE VOCABULARY  (Monroe log-odds with informative Dirichlet prior)")
    def toks(rs):
        c = Counter()
        for r in rs:
            c.update(w for w in re.findall(r"[a-z']+", r["_rat"].lower())
                     if w not in STOP and len(w) > 2)
        return c
    A = toks([r for r in corpus if r["participation_decision"] == "ATTEMPT"])
    S = toks([r for r in corpus if r["participation_decision"] == "SAFE"])
    prior = Counter({w: A[w] + S[w] for w in set(A) | set(S)})
    z = logodds_dirichlet(A, S, prior)
    print("  most ATTEMPT-distinctive :", ", ".join(f"{w}({a}/{b})" for _, w, a, b in z[:12]))
    print("  most SAFE-distinctive    :", ", ".join(f"{w}({a}/{b})" for _, w, a, b in z[-12:][::-1]))
    vocab_rows = [dict(term=w, z=round(zz, 3), n_attempt=a, n_safe=b) for zz, w, a, b in z]

    # ---------------- provider summaries, described only ----------------
    print("\nPROVIDER REASONING SUMMARIES  (GPT-5.5 only, 45% of its trials - descriptive)")
    g = [r for r in rows if r["actor_model"] == "gpt" and r["visible_reasoning"].strip()]
    if g:
        for k in keys:
            rate = sum(1 for r in g if re.search(LEX[k], r["visible_reasoning"].lower())) / len(g)
            print(f"    {k:18} {rate:.3f}")
        print(f"    median length {sorted(len(r['visible_reasoning'].split()) for r in g)[len(g)//2]} words")
    print("  Not compared against Claude and not used for inference: present on only")
    print("  45% of GPT trials and 1% of Claude trials, so any contrast would confound")
    print("  model identity with summary availability.")

    # ---------------- outputs ----------------
    def w(fn, rws):
        if not rws:
            return
        f = list(rws[0])
        with open(os.path.join(HERE, fn), "w", newline="") as fh:
            wr = csv.DictWriter(fh, fieldnames=f); wr.writeheader(); wr.writerows(rws)
        print(f"  -> {fn}")
    print("\nOUTPUTS")
    w("trace_feature_rates.csv", feat_rows)
    w("trace_pair_contrasts.csv", pair_rows)
    w("trace_distinctive_terms.csv", vocab_rows)
    with open(os.path.join(HERE, "trace_corpus.csv"), "w", newline="") as fh:
        cols = ["actor_model", "stimulus", "safe_payoff", "participation_decision",
                "_pair", "_side", "_fc", "_len", "_rat"] + keys
        wr = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        wr.writeheader(); wr.writerows(corpus)
    print("  -> trace_corpus.csv")
    json.dump({"lexicons": LEX}, open(os.path.join(HERE, "lexicons.json"), "w"), indent=1)
    print("  -> lexicons.json")


if __name__ == "__main__":
    main()
