"""Study 3A BASELINE analysis: normalized full-action best-response regret per focal model x condition, per item and
equal-weight aggregate, with companions. Reads results/<run>/responses.jsonl + design/reuse.jsonl (+ the historical pilot
responses those rows point to). Usage: python analyze.py [run|mock]"""
import csv, json, random, sys
from collections import defaultdict
from pathlib import Path
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
sys.path.insert(0, str(Path.home() / "Desktop/Coordination/Self_Coordination/study3a_feasibility_20261015/code"))
import scoring as S                                                     # unchanged, read-only

HERE = Path(__file__).resolve().parent.parent
RUN = sys.argv[1] if len(sys.argv) > 1 else "run"
OUT = HERE / "results" / RUN / "analysis"; OUT.mkdir(parents=True, exist_ok=True)
FZ = json.loads((HERE / "design/FROZEN.json").read_text())
ITEMS = [i["array"] for i in FZ["items"]]
MODELS = ["GPT-5.5", "Claude Opus 5"]; OTHER = {"GPT-5.5": "Claude Opus 5", "Claude Opus 5": "GPT-5.5"}
act = lambda r: "PASS" if r["decision"] == "PASS" else ("PLAY", r["object_canonical"])

rows = [json.loads(l) for l in open(HERE / "results" / RUN / "responses.jsonl")]
pilot = {json.loads(l)["job_key"]: json.loads(l) for l in open(Path.home() / "Desktop/Coordination/Self_Coordination/study3a_feasibility_20261015/results/pilot/responses.jsonl")}
for u in (json.loads(l) for l in open(HERE / "design/reuse.jsonl")):
    p = pilot[u["source_job_key"]]
    rows.append(dict(job_key=u["job_key"], array=u["array"], model=u["model"], condition=u["condition"], role=u["role"], status=p["status"],
                     decision=p["decision"], object_canonical=p["object_canonical"], object_slot=p["object_slot"],
                     slot_to_canonical=p["slot_to_canonical"], source="historical 2026-10-15 pilot (exact match)", cost_usd=0.0))
assert len({r["job_key"] for r in rows}) == len(rows), "duplicate job keys"
cells = defaultdict(list); status = defaultdict(lambda: defaultdict(int))
for r in rows:
    k = (r["array"], r["model"], r["condition"], r["role"]); status[k][r["status"]] += 1
    if r["status"] == "ok": cells[k].append(act(r))

def realized_copy(ev):
    """All distinct ordered pairs within one model's COPY eval draws; never self-paired."""
    pay = [S.u(ev[i], ev[k]) for i in range(len(ev)) for k in range(len(ev)) if i != k]
    match = [ev[i] != "PASS" and ev[k] != "PASS" and ev[i][1] == ev[k][1] for i in range(len(ev)) for k in range(len(ev)) if i != k]
    return (sum(pay) / len(pay) / 10, sum(match) / len(match)) if pay else (None, None)

def realized_cross(ev, ev_other):
    pay = [S.u(a, b) for a in ev for b in ev_other]
    match = [a != "PASS" and b != "PASS" and a[1] == b[1] for a in ev for b in ev_other]
    return (sum(pay) / len(pay) / 10, sum(match) / len(match)) if pay else (None, None)

def cell_stats(p, q):
    if not p or not q: return None
    br = S.best_response(S.dist(q))[0]
    return dict(regret=S.regret_norm(S.dist(p), S.dist(q)), V_norm=S.value(S.dist(p), S.dist(q)) / 10, BR=br,
                s=max(S.dist(q)[a] for a in S.ACTIONS[1:]), focal_pass=S.dist(p)["PASS"], partner_pass=S.dist(q)["PASS"])

def inputs(it, m, c):
    p = cells[(it, m, c, "eval")]
    q = cells[(it, m, "COPY", "policy")] if c == "COPY" else cells[(it, OTHER[m], "DIFFERENT", "policy")]
    return p, q

per_item = []
for it in ITEMS:
    for m in MODELS:
        for c in ("COPY", "DIFFERENT"):
            p, q = inputs(it, m, c); st = cell_stats(p, q)
            rp, rm = realized_copy(p) if c == "COPY" else realized_cross(p, cells[(it, OTHER[m], "DIFFERENT", "eval")])
            qs = q; dq = S.dist(qs) if qs else None
            pi = (1 - dq["PASS"]) if dq else None; s_ = max(dq[a] for a in S.ACTIONS[1:]) if dq else None
            per_item.append(dict(array=it, focal=m, condition=c, partner=(m if c == "COPY" else OTHER[m]), n_eval=len(p), n_policy=len(q),
                                 eval_status=dict(status[(it, m, c, "eval")]), policy_status=dict(status[(it, m if c == "COPY" else OTHER[m], c, "policy")]),
                                 eval_counts_PASS_P0_P1_P2_P3="/".join(str(sum(x == a for x in p)) for a in S.ACTIONS),
                                 policy_counts_PASS_P0_P1_P2_P3="/".join(str(sum(x == a for x in q)) for a in S.ACTIONS),
                                 partner_participation=pi, partner_s=s_, partner_cond_concentration=(s_ / pi if pi else None),
                                 realized_payoff_norm=rp, realized_match=rm, **(st or {})))

def boot_cell(p, q, rng):
    P = [rng.choice(p) for _ in p]; Q = [rng.choice(q) for _ in q]
    return S.regret_norm(S.dist(P), S.dist(Q))

def jeffreys_cell(p, q, rng):
    def draw(x):
        g = [rng.gammavariate(sum(y == a for y in x) + .5, 1) for a in S.ACTIONS]; t = sum(g); return {a: v / t for a, v in zip(S.ACTIONS, g)}
    return S.regret_norm(draw(p), draw(q))

rng = random.Random(20261016); B = 2000; agg = []
for m in MODELS:
    for c in ("COPY", "DIFFERENT"):
        its = [it for it in ITEMS if all(inputs(it, m, c))]
        point = sum(S.regret_norm(S.dist(inputs(it, m, c)[0]), S.dist(inputs(it, m, c)[1])) for it in its) / len(its) if its else None
        bs = sorted(sum(boot_cell(*inputs(it, m, c), rng) for it in its) / len(its) for _ in range(B)) if its else []
        js = sorted(sum(jeffreys_cell(*inputs(it, m, c), rng) for it in its) / len(its) for _ in range(B)) if its else []
        rows_mc = [r for r in per_item if r["focal"] == m and r["condition"] == c and r.get("regret") is not None]
        agg.append(dict(focal=m, condition=c, items_covered=len(its), items_total=len(ITEMS), mean_regret=point,
                        boot_lo=bs[int(.025 * (B - 1))] if bs else None, boot_hi=bs[int(.975 * (B - 1))] if bs else None,
                        jeffreys_lo=js[int(.025 * (B - 1))] if js else None, jeffreys_hi=js[int(.975 * (B - 1))] if js else None,
                        items_regret_zero=sum(r["regret"] < 1e-12 for r in rows_mc),
                        mean_V_norm=sum(r["V_norm"] for r in rows_mc) / len(rows_mc) if rows_mc else None,
                        mean_realized_payoff_norm=sum(r["realized_payoff_norm"] for r in rows_mc if r["realized_payoff_norm"] is not None) / max(1, len(rows_mc)),
                        mean_realized_match=sum(r["realized_match"] for r in rows_mc if r["realized_match"] is not None) / max(1, len(rows_mc)),
                        mean_focal_pass=sum(r["focal_pass"] for r in rows_mc) / len(rows_mc) if rows_mc else None))

def wcsv(name, data):
    keys = list(dict.fromkeys(k for d in data for k in d))
    with open(OUT / name, "w", newline="") as fh:
        w = csv.DictWriter(fh, keys); w.writeheader(); [w.writerow({k: (json.dumps(v) if isinstance(v, dict) else v) for k, v in d.items()}) for d in data]
wcsv("per_item.csv", per_item); wcsv("aggregate.csv", agg)

# ---- figure: academic style (global preference); no title; caption lives in README/report
try: plt.style.use("academic")
except OSError: plt.rcParams.update({"font.family": "Arial", "font.size": 9, "axes.spines.top": False, "axes.spines.right": False})
plt.rcParams.update({"font.family": ["Arial", "Helvetica"], "font.size": 9, "axes.linewidth": 0.8, "xtick.direction": "out", "ytick.direction": "out"})
fig, ax = plt.subplots(figsize=(5.5, 3.2))
groups = [(m, c) for m in MODELS for c in ("COPY", "DIFFERENT")]
xpos = {g: i + (0.4 if g[0] == "Claude Opus 5" else 0) for i, g in enumerate(groups)}
jit = random.Random(7)
for g in groups:
    vals = [r["regret"] for r in per_item if (r["focal"], r["condition"]) == g and r.get("regret") is not None]
    mk = "o" if g[1] == "COPY" else "s"
    ax.scatter([xpos[g] + jit.uniform(-.12, .12) for _ in vals], vals, s=10, facecolors="none", edgecolors="0.45", linewidths=0.6, marker=mk, zorder=2)
    a_ = next(x for x in agg if (x["focal"], x["condition"]) == g)
    if a_["mean_regret"] is not None:
        ax.errorbar(xpos[g] + .28, a_["mean_regret"], yerr=[[a_["mean_regret"] - a_["boot_lo"]], [a_["boot_hi"] - a_["mean_regret"]]],
                    fmt=mk, color="black", markersize=5, capsize=2.5, elinewidth=0.8, capthick=0.8, zorder=3)
ax.axhline(0, color="black", lw=0.8, ls="--", zorder=1)
from matplotlib.lines import Line2D
ax.legend(handles=[Line2D([], [], color="black", lw=0.8, ls="--", label="0 = best response to measured partner"),
                   Line2D([], [], marker="o", ls="none", mfc="none", mec="0.45", ms=4, label="single item (open)"),
                   Line2D([], [], marker="o", ls="none", color="black", ms=5, label="equal-item mean, 95% bootstrap CI (filled)")],
          loc="upper right", frameon=False, fontsize=7, handlelength=2.2)
ax.set_xticks([xpos[g] + .14 for g in groups]); ax.set_xticklabels([f"{'GPT-5.5' if m=='GPT-5.5' else 'Opus 5'}\n{c.lower()}" for m, c in groups])
ax.set_ylabel("Normalized regret (lower is better)"); ax.set_ylim(-0.03, max(0.35, max((r.get("regret") or 0) for r in per_item) + .05))
ax.set_xlim(-0.4, max(xpos.values()) + 0.6)
fig.tight_layout()
for ext in ("png", "pdf"): fig.savefig(OUT / f"fig_baseline_regret.{ext}", dpi=300)
print(json.dumps(agg, indent=1))
