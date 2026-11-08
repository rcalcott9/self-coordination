"""
E18 analysis. Three datasets, identical treatment:
  A  original 12-item code battery   (runs/code_pilot)
  B  expansion 5 survivors           (runs/e18_full)
  C  combined 17-item code battery

Estimators are T5's convergence_metrics, unchanged. Item-clustered bootstrap, same
procedure and seed policy as Stage 1. No API calls.
"""
import csv, glob, json, os, sys, collections, itertools
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import convergence_metrics as cm                                  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
OUT = os.path.join(ROOT, "analysis", "out", "e18")
os.makedirs(OUT, exist_ok=True)
K, B = 4, 2000
RNG = np.random.default_rng(20260910)

PANEL = [("gpt-4-turbo-2024-04-09", "gpt", "2024-04", "G-SAMPLE"),
         ("gpt-4.1-2025-04-14", "gpt", "2025-04", "G-SAMPLE"),
         ("gpt-5-2025-08-07", "gpt", "2025-08", "G-REASON"),
         ("gpt-5.5-2026-04-23", "gpt", "2026-04", "G-REASON"),
         ("claude-opus-4-5-20251101", "claude", "2025-11", "C-OFF"),
         ("claude-opus-4-6", "claude", "2026-02", "C-OFF"),
         ("claude-opus-4-7", "claude", "2026-04", "C-OFF"),
         ("claude-opus-4-8", "claude", "2026-05", "C-OFF"),
         ("claude-opus-5", "claude", "2026-07", "C-OFF")]
FAM = {m: f for m, f, _, _ in PANEL}
VINT = {m: (int(v[:4]) - 2025) + (int(v[5:]) - 1) / 12.0 for m, _, v, _ in PANEL}
STRAT = {m: s for m, _, _, s in PANEL}


def load(pats):
    cells = collections.defaultdict(collections.Counter)
    mech = {}
    for pat in pats:
        for f in glob.glob(os.path.join(ROOT, pat)):
            for r in csv.DictReader(open(f, newline="")):
                if r["transport_ok"] != "1" or r["parse_ok"] != "1":
                    continue
                cells[(r["item_id"], r["checkpoint_requested"])][int(r["canonical_index"])] += 1
                mech[r["item_id"]] = r["mechanism"]
    return cells, mech


def counts(c):
    return [c.get(i, 0) for i in range(K)]


def ols(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    m = np.isfinite(x) & np.isfinite(y)
    return float(np.polyfit(x[m], y[m], 1)[0]) if m.sum() > 1 and np.ptp(x[m]) > 0 else np.nan


def boot_slope(items, x, y, b=B):
    """Item-clustered bootstrap, same procedure as Stage 1."""
    items = np.asarray(items); x = np.asarray(x, float); y = np.asarray(y, float)
    uniq = np.unique(items)
    idx = {u: np.where(items == u)[0] for u in uniq}
    out = []
    for _ in range(b):
        pick = RNG.choice(uniq, len(uniq), replace=True)
        sel = np.concatenate([idx[u] for u in pick])
        s = ols(x[sel], y[sel])
        if np.isfinite(s):
            out.append(s)
    out = np.array(out)
    if out.size < 50:
        return ols(x, y), np.nan, np.nan
    return ols(x, y), float(np.percentile(out, 2.5)), float(np.percentile(out, 97.5))


def analyse(name, cells, mech):
    items = sorted({i for i, _ in cells})
    models = [m for m, _, _, _ in PANEL if any((i, m) in cells for i in items)]
    cellrows, pairrows = [], []
    for it in items:
        for m in models:
            c = counts(cells[(it, m)])
            n = sum(c)
            if not n:
                continue
            p = np.array(c, float) / n
            cellrows.append(dict(dataset=name, item_id=it, mechanism=mech[it], model_id=m,
                family=FAM[m], vintage=round(VINT[m], 4), stratum=STRAT[m], n=n,
                counts="|".join(map(str, c)),
                modal_identity=int(np.argmax(c)), modal_share=float(max(c) / n),
                within_model_match=cm.within_model_match(c),
                effective_support=float(1 / (p ** 2).sum()),
                fully_deterministic=int(max(c) == n)))
    for it in items:
        for a, b_ in itertools.combinations(models, 2):
            ca, cb = counts(cells[(it, a)]), counts(cells[(it, b_)])
            if not sum(ca) or not sum(cb):
                continue
            d = cm.match_decomposition(ca, cb)
            pa = np.array(ca, float) / sum(ca); pb = np.array(cb, float) / sum(cb)
            pairrows.append(dict(dataset=name, item_id=it, mechanism=mech[it],
                model_a=a, model_b=b_, family_a=FAM[a], family_b=FAM[b_],
                pair_type="within_family" if FAM[a] == FAM[b_] else "cross_family",
                same_stratum=int(STRAT[a] == STRAT[b_]),
                vintage=round((VINT[a] + VINT[b_]) / 2, 4),
                modal_agreement=int(np.argmax(ca) == np.argmax(cb)),
                cross_model_match=float((pa * pb).sum()),
                cos_raw=cm.cos_raw(ca, cb),
                das=float(cm.das_batch(np.array([ca], float), np.array([cb], float), 2.0, .5)[0]),
                log_cross_match=d["log_cross_match"],
                determinism_channel=d["determinism_channel"],
                alignment_channel=d["alignment_channel"],
                decomposition_residual=d["residual"]))
    P_ = pairrows
    key = [r["item_id"] for r in P_]; vv = [r["vintage"] for r in P_]
    res = dict(dataset=name, n_items=len(items), n_models=len(models),
               n_cells=len(cellrows), n_pairs=len(P_))
    for stat in ("log_cross_match", "determinism_channel", "alignment_channel",
                 "cross_model_match", "das", "cos_raw", "modal_agreement"):
        s, lo, hi = boot_slope(key, vv, [r[stat] for r in P_])
        res[stat] = dict(mean=float(np.nanmean([r[stat] for r in P_])),
                         slope=s, lo=lo, hi=hi)
    tot = res["log_cross_match"]["slope"]
    det = res["determinism_channel"]["slope"]; ali = res["alignment_channel"]["slope"]
    res["decomposition"] = dict(total=tot, determinism=det, alignment=ali,
        residual=float(np.mean([r["decomposition_residual"] for r in P_])),
        share_determinism=det / tot if tot else np.nan)
    for pt in ("within_family", "cross_family"):
        sub = [r for r in P_ if r["pair_type"] == pt]
        if len(sub) > 5:
            s, lo, hi = boot_slope([r["item_id"] for r in sub],
                                   [r["vintage"] for r in sub], [r["das"] for r in sub])
            res.setdefault("das_by_pair_type", {})[pt] = dict(n=len(sub), slope=s, lo=lo, hi=hi)
    bym = {}
    for m in models:
        cr = [r for r in cellrows if r["model_id"] == m]
        bym[m] = dict(vintage=VINT[m], family=FAM[m], n_cells=len(cr),
            median_support=float(np.median([r["effective_support"] for r in cr])),
            frac_deterministic=float(np.mean([r["fully_deterministic"] for r in cr])),
            median_modal_share=float(np.median([r["modal_share"] for r in cr])))
    res["by_checkpoint"] = bym
    res["frac_deterministic_overall"] = float(np.mean([r["fully_deterministic"] for r in cellrows]))
    return res, cellrows, pairrows


A = load(["runs/code_pilot/code_pilot_*.csv"])
Bd = load(["runs/e18_full/e18_full_*.csv"])
C = (collections.defaultdict(collections.Counter, {**A[0], **Bd[0]}), {**A[1], **Bd[1]})
ALLC, ALLP, SUM = [], [], {}
for nm, (cl, mh) in (("A_original_12", A), ("B_expansion_5", Bd), ("C_combined_17", C)):
    r, cr, pr = analyse(nm, cl, mh)
    SUM[nm] = r; ALLC += cr; ALLP += pr
    d = r["decomposition"]
    print(f"\n=== {nm} ===  {r['n_items']} items, {r['n_cells']} cells, {r['n_pairs']} pairs")
    print(f"  deterministic cells overall      {100*r['frac_deterministic_overall']:.0f}%")
    print(f"  log agreement slope   {d['total']:+.4f}  = determinism {d['determinism']:+.4f}"
          f" + alignment {d['alignment']:+.4f}   ({100*d['share_determinism']:.0f}% determinism)")
    t = r["das"]; print(f"  das slope             {t['slope']:+.4f}  [{t['lo']:+.4f}, {t['hi']:+.4f}]")
    for pt, v in r.get("das_by_pair_type", {}).items():
        z = "contains zero" if v["lo"] < 0 < v["hi"] else "excludes zero"
        print(f"    {pt:14} n={v['n']:4d}  {v['slope']:+.4f} [{v['lo']:+.4f}, {v['hi']:+.4f}]  {z}")

for fn, rows in (("cell_metrics.csv", ALLC), ("pair_metrics.csv", ALLP)):
    with open(os.path.join(OUT, fn), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
json.dump(SUM, open(os.path.join(OUT, "summary.json"), "w"), indent=1, default=float)
print(f"\nwrote {OUT}")
