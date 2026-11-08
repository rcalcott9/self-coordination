"""Reciprocal-confidence pilot analysis. Usage: python analyze.py [run|mock]
Regret (same-q plug-in, >= 0) per item x focal x condition; matched-item baseline comparison (exploratory);
own/partner forecast calibration (eval-draw forecasts vs independent policy draws); EV consistency; PLAY rates."""
import csv, json, random, sys
from pathlib import Path
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path.home() / "Desktop/Coordination/Self_Coordination/study3a_feasibility_20261015/code"))
import scoring as S, rc_parse

HERE = Path(__file__).resolve().parent.parent; RUN = sys.argv[1] if len(sys.argv) > 1 else "run"
OUT = HERE / "results" / RUN / "analysis"; OUT.mkdir(parents=True, exist_ok=True)
FZ = json.loads((HERE / "design/FROZEN.json").read_text()); ITEMS = FZ["items"]
MODELS = ["GPT-5.5", "Claude Opus 5"]; OTHER = {"GPT-5.5": "Claude Opus 5", "Claude Opus 5": "GPT-5.5"}; A = S.ACTIONS
rows = [json.loads(l) for l in open(HERE / "results" / RUN / "responses.jsonl")]
act = lambda r: "PASS" if r["decision"] == "PASS" else ("PLAY", r["object_canonical"])
cell = lambda it, m, c, role: [r for r in rows if (r["array"], r["model"], r["condition"], r["role"]) == (it, m, c, role)]
okr = lambda rs: [r for r in rs if r["status"] == "ok"]
tvd = lambda f, q: 0.5 * sum(abs(f[a] - q[a]) for a in A)
mean_f = lambda fs: {a: sum(f[a] for f in fs) / len(fs) for a in A} if fs else None

def forecasts(rs, key):
    return [rc_parse.to_canon(r[key], r["slot_to_canonical"]) for r in rs if r.get(key)]

def br_consistent(r):
    f = rc_parse.to_canon(r["partner_distribution"], r["slot_to_canonical"])
    vals = {a: (7.0 if a == "PASS" else 10 * f[a]) for a in A}; m = max(vals.values())
    return vals[act(r)] >= m - 0.2                                  # within 0.2 points of the best stated EV (ties/rounding)

def ev_arith(r):
    ev = r.get("expected_points")
    if not ev: return None
    return all(abs(ev[str(k)] - 10 * r["partner_distribution"][str(k)]) <= 0.5 for k in range(1, 5)) and abs(ev["PASS"] - 7) <= 0.01

BASE_ROWS = [r for r in csv.DictReader(open(Path.home() / "Desktop/Coordination/Self_Coordination/study3a_baseline_20261016/results/run/analysis/per_item.csv")) if r["array"] in ITEMS]
baseV = {(r["array"], r["focal"], r["condition"]): float(r["V_norm"]) for r in BASE_ROWS}
baseM = {(r["array"], r["focal"], r["condition"]): float(r["realized_match"]) for r in BASE_ROWS}
base = {(r["array"], r["focal"], r["condition"]): float(r["regret"]) for r in
        csv.DictReader(open(Path.home() / "Desktop/Coordination/Self_Coordination/study3a_baseline_20261016/results/run/analysis/per_item.csv"))
        if r["array"] in ITEMS}

per = []; rng = random.Random(20261017)
def stats(it, m, c):
    ev = okr(cell(it, m, c, "eval")); p = [act(r) for r in ev]
    pol_self = [act(r) for r in okr(cell(it, m, c, "policy"))]
    q = pol_self if c == "COPY" else [act(r) for r in okr(cell(it, OTHER[m], c, "policy"))]
    return ev, p, pol_self, q
for it in ITEMS:
    for m in MODELS:
        for c in ("COPY", "DIFFERENT"):
            ev, p, pol_self, q = stats(it, m, c)
            if not p or not q: per.append(dict(array=it, focal=m, condition=c, note="insufficient")); continue
            dq, dp, ds = S.dist(q), S.dist(p), S.dist(pol_self)
            fo, fp = mean_f(forecasts(ev, "own_distribution")), mean_f(forecasts(ev, "partner_distribution"))
            allr = okr(cell(it, m, c, "eval")) + okr(cell(it, m, c, "policy"))
            arith = [x for x in (ev_arith(r) for r in allr) if x is not None]
            per.append(dict(array=it, focal=m, condition=c, n_eval=len(p), n_policy_partner=len(q),
                            n_invalid_eval=len(cell(it, m, c, "eval")) - len(ev),
                            regret=S.regret_norm(dp, dq), baseline_regret=base.get((it, m, c)), BR=S.best_response(dq)[0],
                            V_norm=S.value(dp, dq) / 10, baseline_V_norm=baseV.get((it, m, c)), baseline_realized_match=baseM.get((it, m, c)),
                            expected_match=sum(dp[a] * dq[a] for a in A[1:]), focal_play=1 - dp["PASS"], partner_play=1 - dq["PASS"],
                            partner_s=max(dq[a] for a in A[1:]),
                            eval_counts="/".join(str(sum(x == a for x in p)) for a in A), partner_counts="/".join(str(sum(x == a for x in q)) for a in A),
                            own_forecast_tvd=tvd(fo, ds) if fo else None, partner_forecast_tvd=tvd(fp, dq) if fp else None,
                            own_forecast_PASS=fo["PASS"] if fo else None, own_measured_PASS=ds["PASS"],
                            partner_forecast_PASS=fp["PASS"] if fp else None, partner_measured_PASS=dq["PASS"],
                            br_consistent_rate=sum(br_consistent(r) for r in allr) / len(allr),
                            ev_arithmetic_rate=(sum(arith) / len(arith)) if arith else None))
def boot_mean(m, c, B=2000):
    vals = []
    for _ in range(B):
        tot = 0
        for it in ITEMS:
            _, p, _, q = stats(it, m, c)
            tot += S.regret_norm(S.dist([rng.choice(p) for _ in p]), S.dist([rng.choice(q) for _ in q]))
        vals.append(tot / len(ITEMS))
    vals.sort(); return vals[int(.025 * (B - 1))], vals[int(.975 * (B - 1))]
agg = []
for m in MODELS:
    for c in ("COPY", "DIFFERENT"):
        rs = [r for r in per if r["focal"] == m and r["condition"] == c and "regret" in r]
        lo, hi = boot_mean(m, c)
        mean = lambda k: sum(r[k] for r in rs if r[k] is not None) / max(1, sum(r[k] is not None for r in rs))
        agg.append(dict(focal=m, condition=c, items=len(rs), mean_regret=mean("regret"), boot_lo=lo, boot_hi=hi,
                        baseline_mean_regret_same_items=mean("baseline_regret"), mean_V_norm=mean("V_norm"), baseline_mean_V_norm=mean("baseline_V_norm"),
                        expected_match=mean("expected_match"), baseline_realized_match=mean("baseline_realized_match"), focal_play=mean("focal_play"), partner_play=mean("partner_play"),
                        own_forecast_tvd=mean("own_forecast_tvd"), partner_forecast_tvd=mean("partner_forecast_tvd"),
                        br_consistent_rate=mean("br_consistent_rate"), ev_arithmetic_rate=mean("ev_arithmetic_rate")))
for name, data in (("per_item.csv", per), ("aggregate.csv", agg)):
    keys = list(dict.fromkeys(k for d in data for k in d))
    with open(OUT / name, "w", newline="") as fh: w = csv.DictWriter(fh, keys); w.writeheader(); w.writerows(data)

try: plt.style.use("academic")
except OSError: pass
plt.rcParams.update({"font.family": ["Arial", "Helvetica"], "font.size": 9, "axes.linewidth": 0.8, "xtick.direction": "out",
                     "ytick.direction": "out", "axes.spines.top": False, "axes.spines.right": False})
fig, ax = plt.subplots(figsize=(5.5, 3.2))
groups = [(m, c) for m in MODELS for c in ("COPY", "DIFFERENT")]
for i, g in enumerate(groups):
    x0 = i + (0.4 if g[0] == "Claude Opus 5" else 0)
    rs = [r for r in per if (r["focal"], r["condition"]) == g and "regret" in r]
    for r in rs:
        if r["baseline_regret"] is not None:
            ax.plot([x0 - .15, x0 + .15], [r["baseline_regret"], r["regret"]], color="0.7", lw=0.6, zorder=1)
        ax.scatter([x0 - .15], [r["baseline_regret"]], s=12, facecolors="none", edgecolors="0.45", linewidths=0.6, marker="o", zorder=2)
        ax.scatter([x0 + .15], [r["regret"]], s=12, facecolors="none", edgecolors="black", linewidths=0.6, marker="s", zorder=2)
    a_ = next(x for x in agg if (x["focal"], x["condition"]) == g)
    ax.scatter([x0 - .32], [a_["baseline_mean_regret_same_items"]], s=22, color="0.45", marker="o", zorder=3)
    ax.errorbar(x0 + .32, a_["mean_regret"], yerr=[[a_["mean_regret"] - a_["boot_lo"]], [a_["boot_hi"] - a_["mean_regret"]]],
                fmt="s", color="black", markersize=4.5, capsize=2.5, elinewidth=0.8, capthick=0.8, zorder=3)
ax.axhline(0, color="black", lw=0.8, ls="--", zorder=0)
ax.set_xticks([i + (0.4 if g[0] == "Claude Opus 5" else 0) for i, g in enumerate(groups)])
ax.set_xticklabels([f"{'GPT-5.5' if m == 'GPT-5.5' else 'Opus 5'}\n{c.lower()}" for m, c in groups])
ax.set_ylabel("Normalized regret (lower is better)")
top = max([r.get("regret") or 0 for r in per] + [r.get("baseline_regret") or 0 for r in per])
ax.set_ylim(-0.03, max(0.3, top + 0.12)); ax.set_xlim(-0.6, len(groups) + 0.1)
ax.legend(handles=[Line2D([], [], color="black", lw=0.8, ls="--", label="0 = best response to measured partner"),
                   Line2D([], [], marker="o", ls="none", mfc="none", mec="0.45", ms=4, label="baseline, item (filled: mean)"),
                   Line2D([], [], marker="s", ls="none", mfc="none", mec="black", ms=4, label="reciprocal confidence, item (filled: mean, 95% CI)")],
          loc="upper right", frameon=False, fontsize=7)
fig.tight_layout()
for ext in ("png", "pdf"): fig.savefig(OUT / f"fig_reciprocal_regret.{ext}", dpi=300)
print(json.dumps(agg, indent=1))
