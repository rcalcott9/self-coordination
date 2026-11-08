"""Item SHAPES: basic simultaneous Stag Hunt, same-model self-play. No model calls.

Derived 2026-10-14 from M07 basic_stag_hunt/code/selfplay.py. Only the stimulus changed: the four
protocol labels and their descriptions are replaced by CIRCLE, SQUARE, TRIANGLE, STAR, and the sentence
about protocols / JSON-using services is removed. KEEP, payoffs, randomization, pairing and scoring are
unchanged. This is a different stimulus (no protocol semantics, no explicit JSON cue): M07
observations must not be pooled with this item.

  render   build every action and prediction prompt with its own seeded option order -> manifest
  score    parse saved responses, pair fresh action responses, score by option identity
  selftest run `score` on synthetic responses (no calls) and check every rule below

Rules (fixed before any collection):
- Option identities: KEEP, CIRCLE, SQUARE, TRIANGLE, STAR. Each call shows them in its own
  uniformly random order (seed f"{SEED}-{model}-{kind}-{i}"); the order is recorded, never scored.
- An action parses only as one JSON line {"action": X} where X matches one identity exactly after
  trimming whitespace/backticks and ignoring case. Anything else is INVALID.
- Pairing: the valid action responses of one model are put in a seeded random order (seed
  f"{SEED}-{model}-pairing", fixed now) and paired consecutively, so each response is used in
  exactly one pair; an odd leftover is reported and unpaired.
- Payoff per player: KEEP 7; a label 10 if the partner's identity is the same label, else 0.
- Secondary: expected payoffs and outcome shares over all distinct pairs (U-statistic), which uses
  each response many times; bootstrap over responses.
- Sensitivity: INVALID responses stay in the pairing and count as a non-action (0 points; partner
  KEEP still 7, partner label 0).
- Order checks: for each option and each display position 1-5, the number of valid action calls
  showing it there and the share of those calls choosing it (plus the overall chosen-position counts).
- Predictions (separate calls) are scored against the same model's live SELF action responses, never
  a reference pool. A prediction is valid only with five lines naming each option once, numbers
  >= 0, summing to 100 +/- 1; valid predictions are renormalized to sum to 1 (p). Over the n valid
  live actions a_1..a_n with empirical frequencies f:
    TVD      = 1/2 * sum_o |p_o - f_o|
    Brier    = (1/n) sum_j sum_o (1[a_j = o] - p_o)^2          (multiclass, 5 terms, range 0-2)
    log loss = (1/n) sum_j -ln q_{a_j},  q_o = max(p_o, EPS) / sum_o' max(p_o', EPS),  EPS = .01
  TVD and Brier use p (unclipped); only log loss uses q. Each metric is computed per prediction call
  and averaged over valid prediction calls. The count of calls giving p = 0 to an option that some
  live action chose is reported. Pilot prediction metrics are descriptive only: the empirical
  target uses only 40 actions per model.
- Prediction-implied best response: expected payoff KEEP = 7, label = 10 * p_label. Every option
  within 1e-9 of the maximum is kept, so a tie (e.g. a label at p = .7 vs KEEP) is reported as the
  set "KEEP|<label>", never broken.
"""
import argparse, csv, hashlib, itertools, json, os, random, re, sys
from collections import Counter

SEED = 20261014   # own seed namespace (M07 used 20261015); same procedure
OPTIONS = ["KEEP", "CIRCLE", "SQUARE", "TRIANGLE", "STAR"]
LABELS = OPTIONS[1:]
DESC = {"KEEP": "- KEEP", "CIRCLE": "- CIRCLE (label)", "SQUARE": "- SQUARE (label)",
        "TRIANGLE": "- TRIANGLE (label)", "STAR": "- STAR (label)"}
MODELS = {"gpt-5.5": "GPT-5.5", "claude-opus-5": "Claude Opus 5"}
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CATS = ["coordinated_label", "miscoordinated_labels", "mixed_keep_label", "both_keep"]


def tmpl(name):
    return open(os.path.join(HERE, "prompts", name)).read().rstrip("\n")


def order(model, kind, i):
    o = OPTIONS[:]
    random.Random(f"{SEED}-{model}-{kind}-{i}").shuffle(o)
    return o


def action_prompt(model, o):
    block = "\n".join(DESC[x] for x in o)
    return tmpl("action_selfplay.txt").replace("{MODEL}", MODELS[model]).replace("{OPTIONS_BLOCK}", block)


def prediction_prompt(model, o):
    return tmpl("prediction_selfplay.txt").replace("{ACTION_PROMPT}", action_prompt(model, o)).replace("{MODEL}", MODELS[model])


def render(n_action, n_pred, out):
    rows = []
    for m in MODELS:
        for kind, n, f in (("action", n_action, action_prompt), ("prediction", n_pred, prediction_prompt)):
            for i in range(n):
                o = order(m, kind, i); p = f(m, o)
                rows.append(dict(call_id=f"{m}|{kind}|{i}", model=m, kind=kind, i=i, order="|".join(o),
                                 prompt_sha16=hashlib.sha256(p.encode()).hexdigest()[:16], prompt=p))
    with open(out, "w") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")
    return rows


def norm(s):
    return s.strip().strip("`").strip().lower()


def parse_action(text):
    m = re.fullmatch(r'\s*`*\s*(\{.*\})\s*`*\s*', text or "", re.S)
    try:
        x = json.loads(m.group(1))["action"] if m else None
    except (ValueError, KeyError, TypeError):
        return None
    hits = [o for o in OPTIONS if isinstance(x, str) and norm(x) == o.lower()]
    return hits[0] if len(hits) == 1 else None


def parse_prediction(text, shown):
    got = {}
    for line in (text or "").strip().splitlines():
        # Amendment 2026-10-14 (before pilot collection): an optional trailing "(label)" after one of
        # the four label names maps to the bare identity, for both models. Not allowed after KEEP.
        m = re.fullmatch(r'\s*`?([A-Za-z0-9-]+)(\s*\(label\))?`?\s*:\s*([0-9]+(?:\.[0-9]+)?)\s*%?\s*', line)
        if not m:
            return None
        k = [o for o in OPTIONS if o.lower() == m.group(1).lower()]
        if not k or (m.group(2) and k[0] == "KEEP") or k[0] in got or float(m.group(3)) < 0:
            return None
        got[k[0]] = float(m.group(3))
    if set(got) != set(OPTIONS) or abs(sum(got.values()) - 100) > 1:
        return None
    s = sum(got.values())
    return {k: v / s for k, v in got.items()}


def pay(a, b):
    """Points to the player choosing a against b; None = INVALID (non-action)."""
    if a == "KEEP":
        return 7
    return 10 if (a is not None and a == b) else 0


def category(a, b):
    if a == "KEEP" and b == "KEEP":
        return "both_keep"
    if "KEEP" in (a, b):
        return "mixed_keep_label"
    return "coordinated_label" if a == b else "miscoordinated_labels"


def score_pairs(ids_choices, model):
    ids = [c for c, _ in ids_choices]
    ch = dict(ids_choices)
    random.Random(f"{SEED}-{model}-pairing").shuffle(ids)
    pairs = [(ids[k], ids[k + 1]) for k in range(0, len(ids) - 1, 2)]
    out = []
    for x, y in pairs:
        a, b = ch[x], ch[y]
        out.append(dict(model=model, p1=x, p2=y, a1=a, a2=b, pts1=pay(a, b), pts2=pay(b, a),
                        category=category(a, b) if None not in (a, b) else "invalid_involved"))
    return out, (ids[-1] if len(ids) % 2 else None)


def allpairs(choices):
    n = len(choices); c = Counter(); pts = 0
    for a, b in itertools.combinations(choices, 2):
        c[category(a, b)] += 1; pts += pay(a, b) + pay(b, a)
    npairs = n * (n - 1) // 2
    return {k: c[k] / npairs for k in CATS}, pts / (2 * npairs)


def boot(choices, reps=2000, seed=0):
    rng = random.Random(f"{SEED}-boot-{seed}"); vals = []
    for _ in range(reps):
        vals.append(allpairs([rng.choice(choices) for _ in choices])[1])
    vals.sort()
    return vals[int(.025 * reps)], vals[int(.975 * reps) - 1]


EPS, TIE_TOL = .01, 1e-9


def implied_best(pred):
    ev = {o: 7.0 if o == "KEEP" else 10 * pred[o] for o in OPTIONS}
    top = max(ev.values())
    return "|".join(o for o in OPTIONS if ev[o] >= top - TIE_TOL)


def pred_metrics(pred, actions):
    """pred: renormalized p over OPTIONS; actions: list of valid live action identities."""
    import math
    n = len(actions)
    f = {o: actions.count(o) / n for o in OPTIONS}
    z = sum(max(pred[o], EPS) for o in OPTIONS)
    q = {o: max(pred[o], EPS) / z for o in OPTIONS}
    return dict(tvd=.5 * sum(abs(pred[o] - f[o]) for o in OPTIONS),
                brier=sum(sum(((a == o) - pred[o]) ** 2 for o in OPTIONS) for a in actions) / n,
                logloss=sum(-math.log(q[a]) for a in actions) / n,
                zero_on_observed=any(pred[o] == 0 and f[o] > 0 for o in OPTIONS),
                implied_best=implied_best(pred))


def score(responses_path, outdir):
    resp = [json.loads(l) for l in open(responses_path)]
    os.makedirs(outdir, exist_ok=True)
    summary, all_pairs = {}, []
    for m in MODELS:
        act = [(r["call_id"], parse_action(r["response"])) for r in resp if r["model"] == m and r["kind"] == "action"]
        if not act:
            continue
        valid = [(c, a) for c, a in act if a is not None]
        prim, left = score_pairs(valid, m)
        sens, _ = score_pairs(act, m)
        all_pairs += [dict(analysis="primary", **p) for p in prim] + [dict(analysis="sensitivity_invalid_kept", **p) for p in sens]
        choices = [a for _, a in valid]
        dist = {o: choices.count(o) / len(choices) for o in OPTIONS}
        shares, ev = allpairs(choices)
        orders = {r["call_id"]: r["order"].split("|") for r in resp}
        pos = Counter(orders[c].index(a) + 1 for c, a in valid)
        by_pos = {o: {k: dict(shown=0, chosen=0) for k in range(1, 6)} for o in OPTIONS}
        for c, a in valid:
            for k, o in enumerate(orders[c], 1):
                by_pos[o][k]["shown"] += 1; by_pos[o][k]["chosen"] += (o == a)
        for o in OPTIONS:
            for k, v in by_pos[o].items():
                v["rate"] = v["chosen"] / v["shown"] if v["shown"] else None
        preds = [parse_prediction(r["response"], r["order"].split("|")) for r in resp if r["model"] == m and r["kind"] == "prediction"]
        pm = [pred_metrics(p, choices) for p in preds if p]
        summary[m] = dict(
            n_action_calls=len(act), n_invalid=len(act) - len(valid), unpaired=left,
            action_distribution=dist, chosen_position=dict(sorted(pos.items())),
            selection_rate_by_position=by_pos,
            primary_pairs=dict(n=len(prim), categories={k: sum(p["category"] == k for p in prim) for k in CATS},
                               mean_points=sum(p["pts1"] + p["pts2"] for p in prim) / (2 * len(prim)) if prim else None),
            allpairs=dict(category_shares=shares, mean_points=ev, mean_points_ci95=boot(choices)),
            sensitivity_invalid_kept=dict(n=len(sens), mean_points=sum(p["pts1"] + p["pts2"] for p in sens) / (2 * len(sens)) if sens else None),
            predictions=dict(n_calls=len(preds), n_invalid=sum(p is None for p in preds),
                             mean={k: sum(x[k] for x in pm) / len(pm) for k in ("tvd", "brier", "logloss")} if pm else None,
                             n_zero_on_observed=sum(x["zero_on_observed"] for x in pm),
                             implied_best=dict(Counter(x["implied_best"] for x in pm))))
    with open(os.path.join(outdir, "pairs.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(all_pairs[0])); w.writeheader(); w.writerows(all_pairs)
    json.dump(summary, open(os.path.join(outdir, "summary.json"), "w"), indent=1)
    return summary, all_pairs


def selftest():
    d = os.path.join(HERE, "selftest")
    rows = render(8, 3, os.path.join(d, "manifest_selftest.jsonl"))
    # every prompt carries all five options once, orders vary, prediction embeds the action game
    for r in rows:
        assert all(r["prompt"].splitlines().count(DESC[o]) == 1 for o in OPTIONS), r["call_id"]
        assert "{" + "MODEL}" not in r["prompt"] and "{OPTIONS_BLOCK}" not in r["prompt"]
    assert len({r["order"] for r in rows}) > 10
    assert all("<game>" in r["prompt"] for r in rows if r["kind"] == "prediction")
    # stimulus: no protocol semantics or JSON cue anywhere in rendered prompts (the answer line is
    # the only JSON-shaped text, as in M07)
    banned = ["json", "protocol", "base64", "base85", "hex", "zlib", "xml", "binary", "payload",
              "encod", "service", "request", "message"]
    for r in rows:
        low = r["prompt"].lower()
        assert not [w for w in banned if w in low], (r["call_id"], [w for w in banned if w in low])
    # identical stimulus across models apart from model identity: same slot -> same order, and the
    # prompts are equal once the model name is replaced by a placeholder
    for kind, f in (("action", action_prompt), ("prediction", prediction_prompt)):
        for i in range(8 if kind == "action" else 3):
            o = order("gpt-5.5", kind, i)
            a = f("gpt-5.5", o).replace(MODELS["gpt-5.5"], "<M>")
            b = f("claude-opus-5", o).replace(MODELS["claude-opus-5"], "<M>")
            assert a == b and "<M>" in a
    assert all(SEED == 20261014 for _ in [0])
    # synthetic responses: identities fixed, written in whatever form exercises the parser
    g = ["CIRCLE", "CIRCLE", "KEEP", "SQUARE", "CIRCLE", "KEEP", "nonsense", "circle"]
    o = ["KEEP"] * 4 + ["STAR", "STAR", "TRIANGLE", "KEEP"]
    resp = []
    for r in rows:
        m, i = r["model"], r["i"]
        if r["kind"] == "action":
            a = (g if m == "gpt-5.5" else o)[i]
            text = '{"action": "%s"}' % a if a != "nonsense" else "I would pick circle"
            if i == 7:
                text = "```\n" + text + "\n```"
        else:
            sh = r["order"].split("|")
            text = "\n".join(f"{x}: {[40, 30, 10, 10, 10][k]}%" for k, x in enumerate(sh))
        resp.append(dict(call_id=r["call_id"], model=m, kind=r["kind"], order=r["order"], response=text))
    p = os.path.join(d, "responses_selftest.jsonl")
    with open(p, "w") as fh:
        for x in resp:
            fh.write(json.dumps(x) + "\n")
    s, pairs = score(p, d)
    assert pay("KEEP", "CIRCLE") == 7 and pay("CIRCLE", "CIRCLE") == 10 and pay("CIRCLE", "SQUARE") == 0
    assert pay("CIRCLE", "KEEP") == 0 and pay(None, "KEEP") == 0 and pay("KEEP", None) == 7
    assert s["gpt-5.5"]["n_invalid"] == 1 and s["gpt-5.5"]["unpaired"] is not None
    assert s["gpt-5.5"]["action_distribution"]["CIRCLE"] == 4 / 7   # "circle" in a code fence parses
    assert s["claude-opus-5"]["n_invalid"] == 0 and s["claude-opus-5"]["unpaired"] is None
    for pr in pairs:   # payoff follows identities only
        if pr["category"] == "coordinated_label":
            assert pr["a1"] == pr["a2"] != "KEEP" and pr["pts1"] == pr["pts2"] == 10
        if pr["category"] == "miscoordinated_labels":
            assert pr["pts1"] == pr["pts2"] == 0
        if pr["category"] == "mixed_keep_label":
            assert sorted((pr["pts1"], pr["pts2"])) == [0, 7]
        if pr["category"] == "both_keep":
            assert pr["pts1"] == pr["pts2"] == 7
    used = [x for pr in pairs if pr["analysis"] == "primary" for x in (pr["p1"], pr["p2"])]
    assert len(used) == len(set(used))       # no response reused in primary pairing
    # all-pairs shares by hand for Opus: KEEP x5, STAR x2, TRIANGLE x1 -> 28 pairs
    sh, _ = allpairs(["KEEP"] * 5 + ["STAR"] * 2 + ["TRIANGLE"])
    assert abs(sh["both_keep"] - 10 / 28) < 1e-12 and abs(sh["coordinated_label"] - 1 / 28) < 1e-12
    assert abs(sh["mixed_keep_label"] - 15 / 28) < 1e-12 and abs(sh["miscoordinated_labels"] - 2 / 28) < 1e-12
    assert parse_prediction("KEEP: 50%\nCIRCLE: 50%", None) is None   # must cover all five
    # amendment: optional "(label)" suffix on labels only; duplicates after normalization rejected
    a = parse_prediction("KEEP: 92%\nCIRCLE (label): 4%\nTRIANGLE (label): 1%\nSTAR (label): 2%\nSQUARE (label): 1%", None)
    assert a == {"KEEP": .92, "CIRCLE": .04, "TRIANGLE": .01, "STAR": .02, "SQUARE": .01}
    assert parse_prediction("KEEP: 90%\nCIRCLE (label): 4%\nCIRCLE: 2%\nSTAR: 2%\nSQUARE: 2%", None) is None
    assert parse_prediction("KEEP (label): 92%\nCIRCLE: 4%\nTRIANGLE: 1%\nSTAR: 2%\nSQUARE: 1%", None) is None
    assert parse_prediction("KEEP: 92%\nCIRCLE (lab): 4%\nTRIANGLE: 1%\nSTAR: 2%\nSQUARE: 1%", None) is None
    assert parse_prediction("KEEP: 92%\nCIRCLE (label) (label): 4%\nTRIANGLE: 1%\nSTAR: 2%\nSQUARE: 1%", None) is None
    assert parse_prediction("KEEP: 80%\nCIRCLE (label): 4%\nTRIANGLE: 1%\nSTAR: 2%\nSQUARE: 1%", None) is None   # sums to 88
    # implied best response: ties at p = .7 preserved; otherwise strict
    tie = parse_prediction("KEEP: 0\nCIRCLE: 70\nSQUARE: 10\nTRIANGLE: 10\nSTAR: 10", None)
    assert implied_best(tie) == "KEEP|CIRCLE"
    assert implied_best(parse_prediction("KEEP: 0\nCIRCLE: 71\nSQUARE: 9\nTRIANGLE: 10\nSTAR: 10", None)) == "CIRCLE"
    assert implied_best(parse_prediction("KEEP: 40\nCIRCLE: 30\nSQUARE: 30\nTRIANGLE: 0\nSTAR: 0", None)) == "KEEP"
    # scoring formulas by hand: actions K,K,J; p = (.5,.5,0,0,0)
    import math
    mm = pred_metrics(dict(zip(OPTIONS, [.5, .5, 0, 0, 0])), ["KEEP", "KEEP", "CIRCLE"])
    assert abs(mm["tvd"] - (abs(.5 - 2 / 3) + abs(.5 - 1 / 3)) / 2) < 1e-12
    assert abs(mm["brier"] - .5) < 1e-12                       # each action: .25 + .25
    assert abs(mm["logloss"] + math.log(.5 / 1.03)) < 1e-12    # clip 3 zeros to .01, renormalize by 1.03
    mz = pred_metrics(dict(zip(OPTIONS, [1, 0, 0, 0, 0])), ["KEEP", "SQUARE"])
    assert mz["zero_on_observed"] and abs(mz["logloss"] - (-math.log(1 / 1.04) - math.log(.01 / 1.04)) / 2) < 1e-12
    # position table: shown counts sum to n valid per position; chosen sums to n
    for m_, v in s.items():
        bp = v["selection_rate_by_position"]
        nv = v["n_action_calls"] - v["n_invalid"]
        assert all(sum(bp[o][k]["shown"] for o in OPTIONS) == nv for k in range(1, 6))
        assert sum(bp[o][k]["chosen"] for o in OPTIONS for k in range(1, 6)) == nv
    print(json.dumps(s, indent=1))
    print("selftest: all checks passed")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["render", "score", "selftest"])
    ap.add_argument("--n-action", type=int, default=40)
    ap.add_argument("--n-pred", type=int, default=20)
    ap.add_argument("--responses"); ap.add_argument("--out")
    a = ap.parse_args()
    if a.cmd == "selftest":
        selftest()
    elif a.cmd == "render":
        rows = render(a.n_action, a.n_pred, a.out or os.path.join(HERE, "manifest_PROPOSED.jsonl"))
        print(len(rows), "prompts rendered; nothing sent")
    else:
        score(a.responses, a.out)
