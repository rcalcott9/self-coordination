"""Planned analyses completed after the original report (see SPEC.md). No API calls.

Reads the original saved responses and reference distributions; writes only into this folder.
"""
import json, os
from collections import defaultdict
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)
RUN = os.path.join(STUDY, "results", "run_20260912_154308")
B_ITEM, B_LOIO, SEED, N_REF = 10_000, 4_000, 20261013, 100

tvd = lambda p, q: 0.5 * np.abs(p - q).sum(-1)
brier = lambda p, q: ((p - q) ** 2).sum(-1)


def logloss(p, q, eps):
    p = (p + eps) / (1 + 4 * eps)
    return -(q * np.log(p)).sum(-1)


def G(c, d, S, O):
    return (tvd(c, O) - tvd(c, S)) - (tvd(d, O) - tvd(d, S))


items = json.load(open(os.path.join(STUDY, "data", "frozen_items.json")))
resp = defaultdict(list)
for line in open(os.path.join(RUN, "raw", "parsed.jsonl")):
    r = json.loads(line)
    resp[(r["stimulus_id"], r["focal"], r["condition"])].append(r["p_canonical"])
resp = {k: np.array(v) for k, v in resp.items()}

rng = np.random.default_rng(SEED)
out = {"spec_sha256": open(os.path.join(HERE, "SPEC.sha256")).read().split()[0],
       "item": [], "model": {}, "loio": {}}
for focal in ("gpt", "claude"):
    other = "claude" if focal == "gpt" else "gpt"
    Gs = []
    for e in items:
        sid = e["stimulus_id"]
        S, O = np.array(e[f"p_{focal}"]), np.array(e[f"p_{other}"])
        C, D = resp[(sid, focal, "COPY")], resp[(sid, focal, "DIFFERENT")]
        c, d = C.mean(0), D.mean(0)
        pt = dict(G=G(c, d, S, O), brier_copy=brier(c, S), brier_diff=brier(d, O),
                  ll_copy=logloss(c, S, .01), ll_diff=logloss(d, O, .01),
                  ll_copy_e001=logloss(c, S, .001), ll_diff_e001=logloss(d, O, .001),
                  zero_copy=int(((c == 0) & (S > 0)).sum()),
                  zero_diff=int(((d == 0) & (O > 0)).sum()))
        # bootstrap: responses within cell, references as multinomial(100)
        cb = C[rng.integers(0, len(C), (B_ITEM, len(C)))].mean(1)
        db = D[rng.integers(0, len(D), (B_ITEM, len(D)))].mean(1)
        Sb = rng.multinomial(N_REF, S / S.sum(), B_ITEM) / N_REF
        Ob = rng.multinomial(N_REF, O / O.sum(), B_ITEM) / N_REF
        bs = dict(G=G(cb, db, Sb, Ob), brier_copy=brier(cb, Sb), brier_diff=brier(db, Ob),
                  ll_copy=logloss(cb, Sb, .01), ll_diff=logloss(db, Ob, .01))
        row = dict(stimulus_id=sid, family=e["family"], focal=focal, n_copy=len(C), n_diff=len(D))
        for k, v in pt.items():
            row[k] = float(v)
        for k, v in bs.items():
            row[k + "_ci"] = [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))]
        out["item"].append(row)
        Gs.append(pt["G"])
    rows = [r for r in out["item"] if r["focal"] == focal]
    out["model"][focal] = {k: float(np.mean([r[k] for r in rows])) for k in
                           ("G", "brier_copy", "brier_diff", "ll_copy", "ll_diff",
                            "ll_copy_e001", "ll_diff_e001")}
    out["model"][focal]["zero_cells"] = sum(r["zero_copy"] + r["zero_diff"] for r in rows)
    Gs = np.array(Gs); lo = []
    for i in range(len(Gs)):
        g = np.delete(Gs, i)
        b = g[rng.integers(0, len(g), (B_LOIO, len(g)))].mean(1)
        lo.append(dict(omitted=rows[i]["stimulus_id"], mean=float(g.mean()),
                       ci=[float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))]))
    out["loio"][focal] = lo

json.dump(out, open(os.path.join(HERE, "planned_analyses_results.json"), "w"), indent=1)

name = {"gpt": "GPT-5.5", "claude": "Opus 5"}
with open(os.path.join(HERE, "planned_analyses_report.txt"), "w") as f:
    for focal in ("gpt", "claude"):
        m = out["model"][focal]
        f.write(f"=== focal {name[focal]} ===\n")
        f.write(f"model G {m['G']:+.4f} (reproduces original)\n")
        f.write(f"Brier COPY->SELF {m['brier_copy']:.4f}  DIFF->OTHER {m['brier_diff']:.4f} (reproduce original)\n")
        f.write(f"log loss eps.01  COPY->SELF {m['ll_copy']:.4f}  DIFF->OTHER {m['ll_diff']:.4f}\n")
        f.write(f"log loss eps.001 COPY->SELF {m['ll_copy_e001']:.4f}  DIFF->OTHER {m['ll_diff_e001']:.4f}\n")
        f.write(f"cells with p=0 where q>0: {m['zero_cells']} of 22\n")
        f.write(f"{'item':<20}{'G':>8}{'G 95% CI':>20}{'Brier c':>9}{'Brier d':>9}{'LL c':>8}{'LL d':>8}\n")
        for r in sorted([r for r in out['item'] if r['focal'] == focal], key=lambda r: -r['G']):
            f.write(f"{r['stimulus_id']:<20}{r['G']:>+8.3f}  [{r['G_ci'][0]:+.3f}, {r['G_ci'][1]:+.3f}]"
                    f"{r['brier_copy']:>9.3f}{r['brier_diff']:>9.3f}{r['ll_copy']:>8.3f}{r['ll_diff']:>8.3f}\n")
        n_ex = sum(1 for r in out['item'] if r['focal'] == focal and (r['G_ci'][0] > 0 or r['G_ci'][1] < 0))
        f.write(f"items whose G CI excludes 0: {n_ex}/11\n")
        L = out["loio"][focal]
        f.write(f"LOIO mean G range [{min(x['mean'] for x in L):+.4f}, {max(x['mean'] for x in L):+.4f}]; "
                f"CIs excluding 0: {sum(1 for x in L if x['ci'][0] > 0 or x['ci'][1] < 0)}/11\n")
        for x in L:
            f.write(f"  drop {x['omitted']:<20}{x['mean']:+.4f}  [{x['ci'][0]:+.4f}, {x['ci'][1]:+.4f}]\n")
        f.write("\n")
print(open(os.path.join(HERE, "planned_analyses_report.txt")).read())
