"""Study 3 figure: the model followed its own policy regardless of partner identity.

Panel A -- P(choose own learned policy), observed vs the ideal relational strategy
Panel B -- realized team success, showing why the Claude number is misleading

Values recomputed from trial-level data; CIs use the study's context-clustered bootstrap.
"""

import csv
import json
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
F = ROOT / "data" / "study3"
OUT = [Path.home() / "Downloads", Path(__file__).resolve().parent]
RNG = np.random.default_rng(20260909)
NB = 4000


def boot(units, fn):
    out = []
    for _ in range(NB):
        pick = [units[i] for i in RNG.integers(0, len(units), len(units))]
        v = fn(pick)
        if v is not None and np.isfinite(v):
            out.append(v)
    a = np.array(out)
    return float(np.percentile(a, 2.5)), float(np.percentile(a, 97.5))


def main():
    conf = {r["item"]: r for r in json.loads((F / "s3_confirmed.json").read_text())}
    focal = json.loads((F / "s3_focal.json").read_text())
    div = [k for k, r in conf.items() if r["stable_C"] and r["cls_C"] == "DIVERGENT"]
    ctx = {k: conf[k]["scenario"] for k in conf}
    contexts = sorted({ctx[k] for k in div})
    pred = float(np.mean([conf[k]["ft_predictability_C"] for k in div]))

    by = defaultdict(lambda: defaultdict(list))
    for r in focal:
        if r.get("choice") in ("A", "B"):
            by[r["cond"]][r["item"]].append(r)
    ordm = {}
    for it, rows in by["ORDINARY"].items():
        a = sum(1 for r in rows if r["choice"] == "A")
        ordm[it] = "A" if a >= len(rows) / 2 else "B"

    def rate(cond, kind, cs=None):
        hit = tot = 0
        for it in div:
            if cs is not None and ctx[it] not in cs:
                continue
            for r in by[cond].get(it, []):
                tot += 1
                hit += (r["choice"] == ordm[it]) if kind == "own" \
                    else (r["choice"] != r["worker_choice"])
        return hit / tot if tot else None

    vals = {}
    for cond in ("COPY", "CLAUDE"):
        for kind in ("own", "success"):
            p = rate(cond, kind)
            lo, hi = boot(contexts, lambda cs, c=cond, k=kind: rate(c, k, set(cs)))
            vals[(cond, kind)] = (p, lo, hi)
            print(f"  {cond:7s} {kind:8s} = {p:.4f}  95% CI [{lo:.4f}, {hi:.4f}]")
    ideal = {"COPY": 1 - pred, "CLAUDE": pred}
    print(f"  mean FT worker predictability = {pred:.4f}")
    print(f"  ideal P(own policy): COPY={ideal['COPY']:.3f}  CLAUDE={ideal['CLAUDE']:.3f}")

    with open(F / "s3_figure_data.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["panel", "partner", "measure", "estimate", "ci_low", "ci_high",
                    "n_items", "n_trials"])
        for (cond, kind), (p, lo, hi) in vals.items():
            w.writerow(["A" if kind == "own" else "B", cond,
                        "P(choose own learned policy)" if kind == "own"
                        else "realized team success",
                        f"{p:.4f}", f"{lo:.4f}", f"{hi:.4f}", len(div),
                        sum(len(v) for v in by[cond].values())])
        for cond, v in ideal.items():
            w.writerow(["A", cond, "ideal P(choose own learned policy)",
                        f"{v:.4f}", "", "", len(div), ""])

    plt.style.use("academic")
    plt.rcParams.update({"font.size": 9, "font.family": "sans-serif",
                         "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"]})
    fig, axA = plt.subplots(figsize=(3.8, 3.5))
    x = np.array([0, 1])
    labs = ["copy of\nitself", "Claude"]

    obs = [vals[(c, "own")][0] for c in ("COPY", "CLAUDE")]
    er = [[obs[i] - vals[(c, "own")][1] for i, c in enumerate(("COPY", "CLAUDE"))],
          [vals[(c, "own")][2] - obs[i] for i, c in enumerate(("COPY", "CLAUDE"))]]
    idl = [ideal["COPY"], ideal["CLAUDE"]]
    axA.plot(x, idl, "--", color="0.6", lw=1.0, zorder=1)
    axA.plot(x, idl, "s", color="0.6", markerfacecolor="w", markersize=6,
             zorder=2, label="ideal relational strategy")
    axA.plot(x, obs, "-", color="k", lw=1.0, zorder=3)
    axA.errorbar(x, obs, yerr=er, fmt="o", color="k", markerfacecolor="k",
                 markersize=6.5, capsize=3.5, elinewidth=0.9, capthick=0.9,
                 zorder=4, ls="none", label="observed")
    axA.legend(frameon=False, fontsize=7.6, loc="center left",
               bbox_to_anchor=(0.03, 0.50), handletextpad=0.6, labelspacing=0.35)
    axA.set_ylabel("P(choose own learned policy)", fontsize=9)
    axA.set_xticks(x); axA.set_xticklabels(labs, fontsize=9)
    axA.set_xlim(-0.5, 1.5); axA.set_ylim(0, 1)
    axA.set_yticks([0, 0.2, 0.4, 0.6, 0.8, 1.0])
    axA.set_xlabel("hidden partner", fontsize=9)
    axA.spines["top"].set_visible(False); axA.spines["right"].set_visible(False)
    axA.spines["left"].set_linewidth(0.8); axA.spines["bottom"].set_linewidth(0.8)
    axA.tick_params(direction="out", width=0.8, length=3, labelsize=8.5)
    axA.grid(False)
    fig.subplots_adjust(left=0.185, right=0.97, top=0.965, bottom=0.185)

    for d in OUT:
        d.mkdir(parents=True, exist_ok=True)
        for ext in ("pdf", "png"):
            fp = d / f"study3_partner_identity_null.{ext}"
            fig.savefig(fp, dpi=300); print(f"  saved {fp}")
    print(f"  data -> {F/'s3_figure_data.csv'}")


if __name__ == "__main__":
    main()
