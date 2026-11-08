"""Offline self-test (no calls): parsers, position->object mapping, descriptors, screening, forecast scores,
implied best response, regret sign conventions, and the full estimand pipeline on mock data built from jobs_PROPOSED."""
import json, random, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import pk_analysis_PROPOSED as K
from prompts_PROPOSED import PROMPTS, sha8

HERE = Path(__file__).resolve().parent.parent
fails = []
def check(name, cond):
    print(("PASS " if cond else "FAIL ") + name); fails.append(name) if not cond else None
A = K.A; P = lambda j: ("PLAY", j)

# prompts
check("act prompts are the archived ones", sha8(PROMPTS["ACT_COPY"]) == "49e35910" and sha8(PROMPTS["ACT_DIFFERENT"]) == "8222a371")
check("new prompts share the archived game text verbatim", all(PROMPTS[k].startswith(PROMPTS["ACT_COPY"].split("Answer with exactly")[0]) for k in ("F_COPY", "FA_COPY")))
check("forecast-then-act states that only the focal player gives an estimate", "Only you are asked for this estimate" in PROMPTS["FA_DIFFERENT"])
check("auditor prompt names GPT-5.5 truthfully and says the auditor is not a player", "GPT-5.5 (made by OpenAI)" in PROMPTS["AUDITOR_COPY"] and "You are not a player" in PROMPTS["AUDITOR_COPY"])

# parsers + mapping
f, n = K.parse_forecast('{"PASS": 10, "1": 0, "2": 70, "3": 20, "4": 0}')
check("forecast parse ok", n == "ok" and abs(sum(f.values()) - 100) < 1e-9)
check("forecast sum outside 95-105 rejected", K.parse_forecast('{"PASS": 10, "1": 0, "2": 50, "3": 20, "4": 0}')[0] is None)
check("forecast extra key rejected", K.parse_forecast('{"PASS": 10, "1": 0, "2": 70, "3": 20, "4": 0, "x": 0}')[0] is None)
c = K.to_canon(f, [2, 0, 3, 1])                       # position 2 shows canonical object 0
check("position->canonical mapping", abs(c[P(0)] - .7) < 1e-9 and abs(c[P(3)] - .2) < 1e-9 and abs(c["PASS"] - .1) < 1e-9)
ff, act, n = K.parse_forecast_then_act('{"forecast": {"PASS": 0, "1": 100, "2": 0, "3": 0, "4": 0}, "decision":"PLAY","object":"1"}')
check("forecast-then-act parse", n == "ok" and act == ("PLAY", 1))
check("forecast-then-act PASS with object rejected", K.parse_forecast_then_act('{"forecast": {"PASS": 100, "1": 0, "2": 0, "3": 0, "4": 0}, "decision":"PASS","object":"2"}')[2] != "ok")

# descriptors and screening
d = K.descriptors({"PASS": 1.0, P(0): 0, P(1): 0, P(2): 0, P(3): 0})
check("consistent PASS: h = 1, s = 0 (concentrated, not weak)", d["h"] == 1 and d["s"] == 0 and d["c"] is None)
check("screen 24/24 one object -> strong-PLAY", K.posterior_class([P(3)] * 24)[0] == "strong-PLAY")
check("screen 24/24 PASS -> concentrated-PASS", K.posterior_class(["PASS"] * 24)[0] == "concentrated-PASS")
check("screen diffuse 5/5/5/5/4 -> diffuse", K.posterior_class(["PASS"] * 5 + [P(0)] * 5 + [P(1)] * 5 + [P(2)] * 5 + [P(3)] * 4)[0] == "diffuse")

# forecast scores, implied BR, regret signs
q = {"PASS": 0, P(0): .8, P(1): .2, P(2): 0, P(3): 0}
check("TVD 0 for perfect forecast; Brier minimal at truth", K.tvd(q, q) == 0 and K.brier(q, q) < K.brier({a: .2 for a in A}, q))
check("implied BR: forecast PLAY0 .8 -> PLAY0", K.implied_br(q) == [P(0)])
check("implied BR: forecast PLAY0 .7 -> tie PASS/PLAY0 kept", set(map(str, K.implied_br({"PASS": .3, P(0): .7, P(1): 0, P(2): 0, P(3): 0}))) == {"PASS", str(P(0))})
rng = random.Random(1); pool = list(A)
check("same-q plug-in regret never negative (2,000 random)", min(K.regret([rng.choice(pool) for _ in range(12)], [rng.choice(pool) for _ in range(24)]) for _ in range(2000)) >= 0)
check("independent shortfall can be negative", K.realized_shortfall([P(3)] * 12, [P(3)] * 20 + ["PASS"] * 4, [P(3)] * 12) < 0)

# full mock pipeline over the proposed jobs
jobs = [json.loads(l) for l in open(HERE / "jobs_PROPOSED.jsonl")]
truth = {"F27_linecount_m1": {"GPT": [P(3)] * 24, "OPUS": ["PASS"] * 18 + [P(3)] * 6},
         "F14_bars_m1": {"GPT": [P(2)] * 23 + ["PASS"], "OPUS": [P(2)] * 12 + ["PASS"] * 12},
         "F05_orient_m5": {"GPT": ["PASS"] * 9 + [P(0)] * 3 + [P(1)] * 4 + [P(2)] * 4 + [P(3)] * 4, "OPUS": ["PASS"] * 24},
         "F12_mirror_m3": {"GPT": ["PASS"] * 9 + [P(0)] * 6 + [P(1)] * 3 + [P(2)] * 3 + [P(3)] * 3, "OPUS": ["PASS"] * 24}}
out = {}
for j in jobs:
    t = truth[j["array"]]; src = t["OPUS"] if (j["model"] == "Claude Opus 5" and j["arm"] == "P_OPUS_DIFF") else t["GPT"]
    if j["arm"].startswith(("P_", "E0")): out.setdefault((j["array"], j["arm"]), []).append(rng.choice(src))
    elif j["arm"].startswith(("F_", "AU")):
        tgt = t["OPUS"] if j["arm"] == "F_DIFF" else t["GPT"]
        out.setdefault((j["array"], j["arm"]), []).append({a: (sum(x == a for x in tgt) / len(tgt) * .8 + .04) for a in A})
    else:
        out.setdefault((j["array"], j["arm"]), []).append(rng.choice(src))
for it in truth:
    out.setdefault((it, "P_OPUS_DIFF"), list(truth[it]["OPUS"]))           # F27: reused pilot policy (mock)
res = {}
for it in truth:
    qg, qo = out[(it, "P_GPT_COPY")], out[(it, "P_OPUS_DIFF")]
    Fself, Fdiff, Au = (K.mean_forecast(out[(it, k)]) for k in ("F_COPY", "F_DIFF", "AU_COPY"))
    res[it] = dict(cls=K.posterior_class(qg)[0], tvd_self=K.tvd(Fself, S_ := __import__("scoring").dist(qg)), tvd_auditor=K.tvd(Au, S_),
                   projection=K.tvd(Fdiff, __import__("scoring").dist(qo)) - K.tvd(Fdiff, S_),
                   d_regret_copy=K.regret(out[(it, "E1_COPY")], qg) - K.regret(out[(it, "E0_COPY")], qg),
                   d_regret_diff=K.regret(out[(it, "E1_DIFF")], qo) - K.regret(out[(it, "E0_DIFF")], qo))
check("pipeline produces all estimands for 4 items", len(res) == 4 and all(len(v) == 6 for v in res.values()))
check("mock classes: F27/F14 strong-PLAY, F05/F12 diffuse", [res[i]["cls"] for i in truth] == ["strong-PLAY", "strong-PLAY", "diffuse", "diffuse"])
check("item bootstrap returns an interval", None not in K.item_bootstrap([v["d_regret_diff"] for v in res.values()]))
check("job counts: 504 total, 24 policy per item (F27 Opus reused)", len(jobs) == 504 and sum(j["arm"] == "P_OPUS_DIFF" for j in jobs) == 72)
print(json.dumps({k: {kk: (round(vv, 3) if isinstance(vv, float) else vv) for kk, vv in v.items()} for k, v in res.items()}, indent=1))
print(f"\n{len(fails)} failed"); sys.exit(1 if fails else 0)
