"""Shared loaders for the Opus-5 payoff-mechanism analysis. Read-only on raw data."""
import csv, os, collections, math, statistics, random
EXP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAY = ["3", "5", "7", "9"]
ARMS = {
    "GPT-5.5": dict(stagec="data/stageC_20260905_200932.csv",
                    pairs="matched_pairs_FROZEN.csv", mid="gpt-5.5-2026-04-23"),
    "Claude Opus 5": dict(stagec="data/stageC_20260910_162358.csv",
                          pairs="opus5/matched_pairs_FROZEN_opus5.csv", mid="claude-opus-5"),
}


def load(arm):
    a = ARMS[arm]
    rows = [r for r in csv.DictReader(open(os.path.join(EXP, a["stagec"])))
            if r["included_in_analysis"] == "True"]
    assert {r["actor_model_id_returned"] for r in rows} == {a["mid"]}, arm
    pairs = [p for p in csv.DictReader(open(os.path.join(EXP, a["pairs"])))
             if p["approved"] == "True"]
    return rows, pairs


def cell_rates(rows):
    """(stimulus, safe) -> attempt rate, and raw trial lists."""
    d = collections.defaultdict(list)
    for r in rows:
        d[(r["stimulus"], r["safe_payoff"])].append(r["participation_decision"] == "ATTEMPT")
    return {k: statistics.mean(v) for k, v in d.items()}, d


def pair_deltas(rows, pairs, safe):
    """Per-pair high-minus-low attempt-rate difference at one payoff. Pair = unit."""
    A, _ = cell_rates(rows)
    return [A[(p["stimulus_high"], safe)] - A[(p["stimulus_low"], safe)] for p in pairs]


def mean_ci(v):
    n = len(v); m = statistics.mean(v)
    if n < 2: return m, float("nan"), float("nan"), float("nan")
    se = statistics.stdev(v) / math.sqrt(n)
    return m, se, m - 1.96 * se, m + 1.96 * se


def signflip_p(v, B=200000, seed=0):
    """Exact-in-spirit paired sign-flip permutation, one-sided, as in Study 1."""
    rng = random.Random(seed); obs = statistics.mean(v); c = 0
    for _ in range(B):
        if statistics.mean([x if rng.random() < .5 else -x for x in v]) >= obs: c += 1
    return (c + 1) / (B + 1)


def self_match_map(pairs):
    m = {}
    for p in pairs:
        m[p["stimulus_high"]] = float(p["true_high_select"])
        m[p["stimulus_low"]] = float(p["true_low_select"])
    return m


def holdout_map(pairs):
    m = {}
    for p in pairs:
        m[p["stimulus_high"]] = float(p["true_high_holdout"])
        m[p["stimulus_low"]] = float(p["true_low_holdout"])
    return m
