"""PASS=5 adapted-pilot analysis (also scores the completed PASS=7 reciprocal pilot identically for the matched comparison).
Usage: python analyze_pass5.py [run|mock]. Outputs results/<run>/analysis/{per_item.csv, aggregate.csv, fig_pass5_outcomes.png/.pdf}."""
import csv, json, random, sys
from pathlib import Path
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
sys.path.insert(0, str(Path(__file__).resolve().parent))
import scoring_pass as SP, rc_parse

HERE = Path(__file__).resolve().parent.parent; RUN = sys.argv[1] if len(sys.argv) > 1 else "run"
OUT = HERE / "results" / RUN / "analysis"; OUT.mkdir(parents=True, exist_ok=True)
CAND = json.loads((HERE / "design/CANDIDATE.json").read_text()); ITEMS = CAND["items"]
MODELS = ["GPT-5.5", "Claude Opus 5"]; OTHER = {"GPT-5.5": "Claude Opus 5", "Claude Opus 5": "GPT-5.5"}; A = SP.ACTIONS
TOLS = (0.01, 0.1, 0.5)
act = lambda r: "PASS" if r["decision"] == "PASS" else ("PLAY", r["object_canonical"])

def score(rows, pv):
    get = lambda it, m, c, role: [r for r in rows if (r["array"], r["model"], r["condition"], r["role"]) == (it, m, c, role) and r["status"] == "ok"]
    out = {}
    for it in ITEMS:
        for m in MODELS:
            for c in ("COPY", "DIFFERENT"):
                ev = get(it, m, c, "eval"); p = [act(r) for r in ev]
                q = [act(r) for r in get(it, m if c == "COPY" else OTHER[m], c, "policy")]
                pe = [act(r) for r in get(it, OTHER[m], c, "eval")]
                pairs = [(p[i], p[k]) for i in range(len(p)) for k in range(len(p)) if i != k] if c == "COPY" else [(a, b) for a in p for b in pe]
                if not p or not q: continue
                allr = ev + get(it, m, c, "policy")
                arith = {}
                for t in TOLS:
                    ok = [all(abs(r["expected_points"][str(k)] - 10 * r["partner_distribution"][str(k)]) <= t + 1e-9 for k in range(1, 5))
                          and abs(r["expected_points"]["PASS"] - pv) <= t + 1e-9 for r in allr if r.get("expected_points")]
                    arith[t] = sum(ok) / len(ok) if ok else None
                st = SP.pairs_stats(pairs, pv) or {}
                fp = [rc_parse.to_canon(r["partner_distribution"], r["slot_to_canonical"]) for r in ev if r.get("partner_distribution")]
                mq = SP.dist(q)
                ptvd = sum(0.5 * sum(abs(f[a] - mq[a]) for a in A) for f in fp) / len(fp) if fp else None
                def brc(r):
                    f = rc_parse.to_canon(r["partner_distribution"], r["slot_to_canonical"])
                    v = {a: (pv if a == "PASS" else 10 * f[a]) for a in A}; return v[act(r)] >= max(v.values()) - 1e-9
                out[(it, m, c)] = dict(array=it, focal=m, condition=c, n_eval=len(p), n_partner_policy=len(q),
                                       regret=SP.regret_norm(SP.dist(p), mq, pv), V_norm=SP.value(SP.dist(p), mq, pv) / 10,
                                       joint_shortfall=st.get("joint_shortfall"), realized_match=st.get("match_rate"), focal_payoff_norm=st.get("focal_payoff_norm"),
                                       focal_play=1 - SP.dist(p)["PASS"], partner_play=1 - mq["PASS"], partner_forecast_tvd=ptvd,
                                       br_consistent_exact=sum(brc(r) for r in allr) / len(allr),
                                       **{f"ev_arith_tol_{t}": v for t, v in arith.items()})
    return out

rows5 = [json.loads(l) for l in open(HERE / "results" / RUN / "responses.jsonl")]
rows7 = [json.loads(l) for l in open(Path.home() / "Desktop/Coordination/Self_Coordination/study3a_reciprocal_confidence_20261016/results/run/responses.jsonl")]
s5, s7 = score(rows5, 5), score(rows7, 7)
per = []
for k, v in s5.items():
    b = s7.get(k, {}); per.append(dict(v, **{f"pass7_{x}": b.get(x) for x in ("regret", "joint_shortfall", "realized_match", "focal_play")}))
rng = random.Random(20261016)
def boot(key_rows, pv, rowsrc, B=1000):
    vals = []
    for _ in range(B):
        tot = 0
        for (it, m, c) in key_rows:
            get = lambda mm, cc, role: [act(r) for r in rowsrc if (r["array"], r["model"], r["condition"], r["role"]) == (it, mm, cc, role) and r["status"] == "ok"]
            p = get(m, c, "eval"); q = get(m if c == "COPY" else OTHER[m], c, "policy")
            tot += SP.regret_norm(SP.dist([rng.choice(p) for _ in p]), SP.dist([rng.choice(q) for _ in q]), pv)
        vals.append(tot / len(key_rows))
    vals.sort(); return vals[int(.025 * (B - 1))], vals[int(.975 * (B - 1))]
agg = []
for m in MODELS:
    for c in ("COPY", "DIFFERENT"):
        rs = [r for r in per if r["focal"] == m and r["condition"] == c]
        mean = lambda k: (sum(r[k] for r in rs if r.get(k) is not None) / max(1, sum(r.get(k) is not None for r in rs))) if rs else None
        lo, hi = boot([(r["array"], m, c) for r in rs], 5, rows5)
        agg.append(dict(focal=m, condition=c, items=len(rs), mean_regret=mean("regret"), boot_lo=lo, boot_hi=hi, joint_shortfall=mean("joint_shortfall"),
                        realized_match=mean("realized_match"), focal_payoff_norm=mean("focal_payoff_norm"), focal_play=mean("focal_play"),
                        partner_forecast_tvd=mean("partner_forecast_tvd"), br_consistent_exact=mean("br_consistent_exact"),
                        **{f"ev_arith_tol_{t}": mean(f"ev_arith_tol_{t}") for t in TOLS},
                        pass7_regret=mean("pass7_regret"), pass7_joint_shortfall=mean("pass7_joint_shortfall"), pass7_realized_match=mean("pass7_realized_match")))
for name, data in (("per_item.csv", per), ("aggregate.csv", agg)):
    keys = list(dict.fromkeys(k for d in data for k in d))
    with open(OUT / name, "w", newline="") as fh: w = csv.DictWriter(fh, keys); w.writeheader(); w.writerows(data)

# figure: two panels (regret | joint shortfall); PASS=7 (open circle, grey) vs PASS=5 (filled square, black); academic style
try: plt.style.use("academic")
except OSError: pass
plt.rcParams.update({"font.family": ["Arial", "Helvetica"], "font.size": 9, "axes.linewidth": 0.8, "axes.spines.top": False, "axes.spines.right": False,
                     "xtick.direction": "out", "ytick.direction": "out"})
fig, axes = plt.subplots(1, 3, figsize=(5.5, 3.2), sharey=False)
groups = [(m, c) for m in MODELS for c in ("COPY", "DIFFERENT")]
for ax, key, lab in ((axes[0], "regret", "Normalized regret"), (axes[1], "joint_shortfall", "Joint payoff shortfall"), (axes[2], "realized_match", "10-point match rate")):
    for i, g in enumerate(groups):
        a_ = next(x for x in agg if (x["focal"], x["condition"]) == g)
        v5 = a_["mean_regret"] if key == "regret" else a_[key]; v7 = a_["pass7_" + key]
        if v7 is not None: ax.plot([i - .12], [v7], marker="o", mfc="none", mec="0.45", ls="none", ms=5)
        if v5 is not None: ax.plot([i + .12], [v5], marker="s", color="black", ls="none", ms=5)
        if key == "regret" and v5 is not None:
            ax.errorbar(i + .12, v5, yerr=[[v5 - a_["boot_lo"]], [a_["boot_hi"] - v5]], fmt="none", ecolor="black", elinewidth=0.8, capsize=2.5)
    ax.axhline(0, color="black", lw=0.8, ls="--")
    ax.set_xticks(range(4)); ax.set_xticklabels([f"{'G' if m=='GPT-5.5' else 'O'}\n{c[:4].lower()}" for m, c in groups], fontsize=8); ax.set_ylabel(lab)
fig.legend(handles=[Line2D([], [], marker="o", mfc="none", mec="0.45", ls="none", label="PASS = 7 pilot"),
                        Line2D([], [], marker="s", color="black", ls="none", label="PASS = 5")], frameon=False, fontsize=7, loc="upper center", ncol=2)
fig.tight_layout(rect=(0, 0, 1, 0.93))
for ext in ("png", "pdf"): fig.savefig(OUT / f"fig_pass5_outcomes.{ext}", dpi=300)
print(json.dumps(agg, indent=1, default=str)[:1500])
