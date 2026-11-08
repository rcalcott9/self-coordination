"""Local pooling checks (2026-10-15, no calls).
(1) GPT settings/input evidence per source: requested settings, returned model, input-token counts.
(2) GPT in-game action distributions on EVERY item x condition observed in >= 2 GPT sources (no selection by result):
    5-category counts (PASS, PLAY0-3), TVD, and a Monte-Carlo permutation test of homogeneity (chi-square statistic).
(3) Opus Sep vs Oct: every item x condition observed in both periods."""
import csv, glob, json, random
from collections import Counter, defaultdict
from pathlib import Path

STAG = Path.home() / "Desktop/Superrationality/Stag"
SC = Path.home() / "Desktop/Coordination/Self_Coordination"
OUT = Path(__file__).resolve().parent
GAME = {"49e35910": "COPY", "8222a371": "DIFFERENT"}
CATS = ["PASS", "PLAY0", "PLAY1", "PLAY2", "PLAY3"]
pilot_jobs = {json.loads(l)["job_key"]: json.loads(l) for l in open(SC / "study3a_feasibility_20261015/design/jobs.jsonl")}
pilot_req = {}
for l in open(SC / "study3a_feasibility_20261015/results/pilot/requests.jsonl"):
    r = json.loads(l); pilot_req[r["job_key"]] = r["settings"]

def rows():
    for f in glob.glob(str(STAG / "two_model_staghunt_20260916/results/*/responses.jsonl")):
        sub = Path(f).parent.name
        for l in open(f):
            r = json.loads(l)
            if r.get("prompt_sha8") in GAME and r["phase"] == "game":
                yield dict(r, source=f"two_model/{sub}", effort=r.get("effort") or ("high" if "high" in sub else "low"),
                           month="2026-09", requested="gpt-5.5" if r["model"] == "GPT-5.5" else "claude-opus-5")
    for l in open(STAG / "gpt_staghunt_pilot_20260916/results/pilot/responses.jsonl"):
        r = json.loads(l)
        yield dict(r, model="GPT-5.5", source="gpt_staghunt_pilot", effort="low", month="2026-09", requested="gpt-5.5")
    for l in open(SC / "study3a_feasibility_20261015/results/pilot/responses.jsonl"):
        r = json.loads(l)
        yield dict(r, source=f"study3a_pilot/{r['role']}", effort="low", month="2026-10", prompt_sha8=pilot_jobs[r["job_key"]]["prompt_sha8"],
                   requested=pilot_req[r["job_key"]]["model"])

R = [r for r in rows() if r["status"] == "ok"]
act = lambda r: "PASS" if r["decision"] == "PASS" else f"PLAY{r['object_canonical']}"
lines = []
P = lambda *a: (print(*a), lines.append(" ".join(map(str, a))))

P("## (1) settings evidence per source (GPT, low effort unless stated)")
ev = defaultdict(lambda: dict(n=0, returned=Counter(), in_tok=Counter()))
for r in R:
    if r["model"] != "GPT-5.5": continue
    k = (r["source"], r["effort"], GAME[r["prompt_sha8"]], r["requested"]); e = ev[k]
    e["n"] += 1; e["returned"][r["model_returned"]] += 1; e["in_tok"][r["in_tok"]] += 1
for k, e in sorted(ev.items()):
    P(k, "n", e["n"], "returned", dict(e["returned"]), "input tokens", dict(e["in_tok"]))
P("pilot request settings (GPT):", json.dumps(next(v for v in pilot_req.values() if v["model"].startswith("gpt"))))

def perm_test(groups, B=20000, seed=20261015):
    """groups: list of action lists. Chi-square homogeneity statistic, Monte-Carlo permutation p (labels shuffled)."""
    def chi(gs):
        tot = Counter(a for g in gs for a in g); N = sum(tot.values()); s = 0.0
        for g in gs:
            c = Counter(g)
            for a in tot:
                e = len(g) * tot[a] / N
                s += (c[a] - e) ** 2 / e if e > 0 else 0
        return s
    obs = chi(groups); pooled = [a for g in groups for a in g]; sizes = [len(g) for g in groups]
    rng = random.Random(seed); ge = 0
    for _ in range(B):
        rng.shuffle(pooled); i = 0; gs = []
        for n in sizes: gs.append(pooled[i:i + n]); i += n
        ge += chi(gs) >= obs - 1e-12
    return obs, (ge + 1) / (B + 1)

def compare(model, effort, key_fn, label):
    by = defaultdict(lambda: defaultdict(list))
    for r in R:
        if r["model"] == model and r["effort"] == effort:
            by[(r["array"], GAME[r["prompt_sha8"]])][key_fn(r)].append(act(r))
    out = []
    for (arr, cond), g in sorted(by.items()):
        if len(g) < 2: continue
        names = sorted(g); groups = [g[n] for n in names]
        dists = [{c: x.count(c) / len(x) for c in CATS} for x in groups]
        tvd = max(0.5 * sum(abs(dists[i][c] - dists[j][c]) for c in CATS) for i in range(len(groups)) for j in range(i + 1, len(groups)))
        stat, p = perm_test(groups)
        out.append(dict(comparison=label, model=model, array=arr, condition=cond, sources=" vs ".join(names),
                        counts=" | ".join(f"{n}: " + "/".join(str(x.count(c)) for c in CATS) for n, x in zip(names, groups)),
                        max_pairwise_TVD=round(tvd, 3), chi2=round(stat, 2), perm_p=round(p, 4)))
    return out

P("\n## (2) GPT in-game distributions, every item x condition in >= 2 sources (counts PASS/PLAY0/PLAY1/PLAY2/PLAY3)")
g_src = compare("GPT-5.5", "low", lambda r: r["source"].split("/")[0] + ("" if not r["source"].startswith("study3a") else ""), "GPT by run")
g_sub = compare("GPT-5.5", "low", lambda r: r["source"], "GPT by sub-run/role")
for row in g_src + g_sub: P(row)
P("\n## (3) Opus Sep vs Oct, every item x condition in both periods")
o = compare("Claude Opus 5", "low", lambda r: r["month"], "Opus Sep vs Oct")
for row in o: P(row)
allrows = g_src + g_sub + o
with open(OUT / "pooling_checks.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, list(allrows[0])); w.writeheader(); w.writerows(allrows)
(OUT / "pooling_checks.txt").write_text("\n".join(lines) + "\n")
