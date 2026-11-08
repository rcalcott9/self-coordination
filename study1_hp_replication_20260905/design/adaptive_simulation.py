"""Cost/power simulation for staged screening designs, Study 1-HP.

Ground truth is calibrated to Study 1's measured battery (n=30 model x stimulus
cells): p(identity_1) is strongly bimodal (deterministic conventions at 0/1, a
chance cluster near 0.5), auditor ratings are tight (within-cell sd 0.0365),
salience is broad (0.1485).

Measurement models
  Stage A, depth n : p_hat ~ Binom(n, p)/n ; self_match = p^2 + (1-p)^2
                     (delta-method SE vanishes at p=0.5 AND at p=0/1, so the
                      informative extremes are cheap to measure)
  Stage B, depth n : mean of n ratings, SE = sd_within / sqrt(n)

Eligibility (UNCHANGED from Study 1, on z = delta / battery SD)
  |z_true| >= 0.75   |z_salience| <= 0.35   |z_auditor| <= 0.35
"""
import json, sys
import numpy as np

SD_TRUE, SD_AUD, SD_SAL = 0.230, 0.060, 0.223      # battery SDs (Study 1)
W_AUD, W_SAL = 0.0365, 0.1485                      # within-cell rating SDs
LT, SP = 0.75, 0.35
THR_TRUE, THR_AUD, THR_SAL = LT*SD_TRUE, SP*SD_AUD, SP*SD_SAL   # .1725 / .0210 / .0781
MODELS = ("gpt", "claude")


def make_battery(n_stim, rng, fam_size=3, fam_sd_sal=0.18, fam_sd_aud=0.02):
    """True values per (model, stimulus), with CUE-FAMILY structure.

    Family random effects on salience and auditor reproduce the clustering seen
    in real batteries, where eligible pairs concentrate on a few stimuli and
    non-reuse bites hard. Calibrated so a 15-stimulus battery reproduces Study
    1's observed funnel (3.05 eligible / 1.91 independent per model vs 3 / 2).
    NOTE: at 45 stimuli this still yields MORE independent pairs than the
    observed Opus 4.6 run (9.9 vs 8), so simulated yield is an UPPER BOUND and
    the design anchors on the empirical ratio instead.
    """
    B = {}
    nf = int(np.ceil(n_stim/fam_size))
    fam = np.repeat(np.arange(nf), fam_size)[:n_stim]
    f_sal = rng.normal(0, fam_sd_sal, nf)[fam]
    sal_true = np.clip(0.404 + f_sal + rng.normal(0, SD_SAL*0.5, n_stim), 0.02, 0.98)
    for m in MODELS:
        f_aud = rng.normal(0, fam_sd_aud, nf)[fam]
        u = rng.random(n_stim)
        p = np.where(u < 0.50, rng.beta(30, 1.2, n_stim),
            np.where(u < 0.60, rng.beta(6, 2.5, n_stim),
                     np.clip(rng.normal(0.5, 0.08, n_stim), 0.05, 0.95)))
        p = np.where(rng.random(n_stim) < 0.5, p, 1 - p)
        true = p**2 + (1-p)**2
        fc = np.abs(2*p - 1)
        aud = np.clip(0.718 + 0.39*(true-0.777)/SD_TRUE*SD_AUD + f_aud
                      + 0.5*(sal_true-0.404)/SD_SAL*SD_AUD
                      + rng.normal(0, SD_AUD*0.45, n_stim), 0.3, 0.95)
        B[m] = dict(p=p, true=true, aud=aud, sal=sal_true, fc=fc)
    return B


def measure(B, m, idx, n_a, n_b, rng, arms=("A", "aud", "sal")):
    """Fresh independent draws at the given depths. Returns estimates + calls."""
    out, calls = {}, 0
    if "A" in arms:
        p = B[m]["p"][idx]
        ph = rng.binomial(n_a, p) / n_a
        out["true"] = ph**2 + (1-ph)**2
        calls += n_a * len(idx)
    if "aud" in arms:
        out["aud"] = B[m]["aud"][idx] + rng.normal(0, W_AUD/np.sqrt(n_b), len(idx))
        calls += n_b * len(idx)
    if "sal" in arms:
        out["sal"] = B[m]["sal"][idx] + rng.normal(0, W_SAL/np.sqrt(n_b), len(idx))
        calls += n_b * len(idx)
    return out, calls


def pair_up(est, idx, truth=None):
    """Greedy non-reuse pairing on the supplied estimates. Returns list of
    (hi, lo) global indices meeting all three criteria."""
    n = len(idx)
    cands = []
    for i in range(n):
        for j in range(i+1, n):
            a, b = (i, j) if est["true"][i] >= est["true"][j] else (j, i)
            dt = est["true"][a] - est["true"][b]
            if dt < THR_TRUE: continue
            if abs(est["aud"][a]-est["aud"][b]) > THR_AUD: continue
            if abs(est["sal"][a]-est["sal"][b]) > THR_SAL: continue
            cands.append((dt, idx[a], idx[b]))
    cands.sort(key=lambda x: -x[0])
    used, pairs = set(), []
    for dt, h, l in cands:
        if h in used or l in used: continue
        used |= {h, l}; pairs.append((h, l))
    return pairs


def true_admissible(B, m, h, l):
    d = B[m]["true"][h] - B[m]["true"][l]
    return (d >= THR_TRUE and abs(B[m]["aud"][h]-B[m]["aud"][l]) <= THR_AUD
            and abs(B[m]["sal"][h]-B[m]["sal"][l]) <= THR_SAL)


def run_strategy(name, n_stim, nA1, nB1, nA2, nB2, adaptive, rng, conf_arm):
    """Returns dict with calls by component, confirmed pairs, quality metrics."""
    B = make_battery(n_stim, rng)
    calls = dict(stageA=0, auditor=0, salience=0, confidence=0, stageC=0)
    pairs_all, fp, dt_true = [], 0, []
    for m in MODELS:
        idx = np.arange(n_stim)
        # ---- screen ----
        s1, c = measure(B, m, idx, nA1, nB1, rng); calls["stageA"] += nA1*n_stim
        calls["auditor"] += nB1*n_stim; calls["salience"] += nB1*n_stim
        if adaptive:
            # keep only stimuli that could plausibly enter SOME admissible pair:
            # a partner exists within the public windows and beyond the true gap.
            keep = []
            for i in idx:
                ok = any(abs(s1["true"][i]-s1["true"][j]) >= THR_TRUE*0.7
                         and abs(s1["aud"][i]-s1["aud"][j]) <= THR_AUD*2.0
                         and abs(s1["sal"][i]-s1["sal"][j]) <= THR_SAL*1.6
                         for j in idx if j != i)
                if ok: keep.append(i)
            surv = np.array(keep) if keep else idx[:2]
        else:
            surv = idx
        # ---- confirmation: FRESH draws, and these alone decide selection ----
        s2, c = measure(B, m, surv, nA2, nB2, rng)
        calls["stageA"] += nA2*len(surv); calls["auditor"] += nB2*len(surv)
        calls["salience"] += nB2*len(surv)
        prs = pair_up(s2, surv)
        for h, l in prs:
            pairs_all.append((m, h, l))
            if not true_admissible(B, m, h, l): fp += 1
            dt_true.append(B[m]["true"][h] - B[m]["true"][l])
        # ---- confidence arm ----
        if conf_arm == "all_battery":   calls["confidence"] += nB2*n_stim
        elif conf_arm == "survivors":   calls["confidence"] += nB2*len(surv)
        elif conf_arm == "final_pairs": calls["confidence"] += nB2*2*len(prs)
    return dict(name=name, n_pairs=len(pairs_all), calls=calls,
                false_pos=fp, mean_true_gap=float(np.mean(dt_true)) if dt_true else 0.0,
                n_surv=len(surv))


def power_pairs(n_pairs, mu, tau, n_cell, rng, n_sim=400, payoffs=(3,5,7,9)):
    BASE_LOW = {3:1.000, 5:0.973, 7:0.740, 9:0.207}
    p_lo = np.array([BASE_LOW[s] for s in payoffs])
    room = (1.0-p_lo)/(1.0-BASE_LOW[9])
    hits = 0
    for _ in range(n_sim):
        eff = rng.normal(mu, tau, n_pairs)
        p_hi = np.clip(p_lo[None,:]+eff[:,None]*room[None,:], .001, .999)
        hi = rng.binomial(n_cell, p_hi); lo = rng.binomial(n_cell, np.broadcast_to(p_lo,(n_pairs,len(payoffs))))
        d = (hi.sum(1)-lo.sum(1))/(n_cell*len(payoffs)); obs = d.mean()
        if n_pairs <= 12:
            sg = np.array([[1 if (k>>j)&1 else -1 for j in range(n_pairs)] for k in range(2**n_pairs)], np.int8)
            p = float(np.sum((sg*d).mean(1) >= obs))/len(sg)
        else:
            sg = rng.choice([-1,1], size=(3000,n_pairs)).astype(np.int8)
            p = float(np.sum((sg*d).mean(1) >= obs)+1)/3001
        hits += p <= 0.05
    return hits/n_sim
