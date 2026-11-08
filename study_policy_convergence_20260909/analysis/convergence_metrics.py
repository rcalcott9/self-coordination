"""
Stage 1 policy-convergence estimators.

Every metric name and formula follows DATA_DICTIONARY.md exactly. This module is pure
computation: no I/O, no API calls, no globals that depend on a particular run.

The organising idea is the ESTIMATOR LADDER (see ANALYSIS_SPEC.md S4):

    tier 0  cross_model_match          raw expected agreement    CONFOUNDED
    tier 1  cos_raw                    scale-free alignment      PARTLY adjusted
    tier 2  das                        tempering-invariant       DETERMINISM-ADJUSTED  <- primary
    tier 3  rank_similarity            monotone-invariant        assumption-free floor

and the exact accounting identity that links tiers 0 and 1

    log M_AB = 0.5*log M_AA + 0.5*log M_BB + log cos_raw

which splits any change in raw match into a DETERMINISM CHANNEL (the two self-match
terms) and an ALIGNMENT CHANNEL (the cosine term), with no residual.

Conventions
-----------
counts      integer numpy array, length K, indexed by CANONICAL option identity
p           probability vector, length K
alpha       add-alpha smoothing applied once, uniformly, before any nonlinear transform
            (default 0.5 = Krichevsky-Trofimov). Never applied to the raw count metrics
            (modal_share, within_model_match, cross_model_match), which are reported
            unsmoothed.
"""
from __future__ import annotations

import math
from collections import Counter

import numpy as np

LOG2 = math.log(2.0)

DEFAULT_ALPHA = 0.5          # Krichevsky-Trofimov smoothing
DEFAULT_TARGET_SUPPORT = 2.0  # reference determinism S* for standardisation
TAU_LO, TAU_HI = 1e-3, 1e3    # bisection bracket for the tempering exponent


# --------------------------------------------------------------------------- basics


def as_counts(x, k):
    """Accept a Counter/dict/list of labels/array and return an int array of length k."""
    if isinstance(x, np.ndarray):
        return x.astype(np.int64)
    if isinstance(x, (dict, Counter)):
        out = np.zeros(k, dtype=np.int64)
        for key, v in x.items():
            out[int(key)] = v
        return out
    out = np.zeros(k, dtype=np.int64)
    for lab in x:
        out[int(lab)] += 1
    return out


def probs(counts, alpha=0.0):
    c = np.asarray(counts, dtype=float) + alpha
    s = c.sum()
    if s <= 0:
        return np.full(len(c), 1.0 / len(c))
    return c / s


def modal_identity(counts):
    """Deterministic tie-break: lowest canonical index among the maxima."""
    c = np.asarray(counts)
    return int(np.flatnonzero(c == c.max())[0])


def modal_share(counts):
    c = np.asarray(counts, dtype=float)
    n = c.sum()
    return float(c.max() / n) if n else float("nan")


def modal_margin(counts):
    """modal_share - runner_up_share."""
    c = np.sort(np.asarray(counts, dtype=float))[::-1]
    n = c.sum()
    if not n:
        return float("nan")
    runner = c[1] if len(c) > 1 else 0.0
    return float((c[0] - runner) / n)


def within_model_match(counts):
    """Unbiased dyadic self-match: sum_k n_k(n_k-1) / [N(N-1)].  DATA_DICTIONARY."""
    c = np.asarray(counts, dtype=float)
    n = c.sum()
    if n < 2:
        return float("nan")
    return float((c * (c - 1.0)).sum() / (n * (n - 1.0)))


def plugin_match(counts, alpha=0.0):
    """sum_i p_i^2. Biased up by ~1/n relative to within_model_match; used only where
    an algebraic identity requires the plug-in form."""
    p = probs(counts, alpha)
    return float((p * p).sum())


def effective_support(counts, alpha=0.0):
    """1 / sum_i p_i^2.  1 = deterministic, K = uniform.  DATA_DICTIONARY."""
    s = plugin_match(counts, alpha)
    return float(1.0 / s) if s > 0 else float("nan")


def entropy_bits(p):
    p = np.asarray(p, dtype=float)
    nz = p[p > 0]
    return float(-(nz * np.log2(nz)).sum())


# ------------------------------------------------------------------ pair, tier 0/1


def cross_model_match(counts_a, counts_b):
    """sum_i p_A(i) p_B(i).  DATA_DICTIONARY.

    NOTE: the plug-in form is already UNBIASED here, because the two samples are
    independent: E[ph_A(i) ph_B(i)] = p_A(i) p_B(i). No n_k(n_k-1) correction is
    correct or needed for the CROSS term -- only for the WITHIN term.
    """
    return float((probs(counts_a) * probs(counts_b)).sum())


def p_other_modal(counts_self, counts_other):
    """Probability the SELF model assigns to the OTHER model's modal action.
    Directed: report both orderings."""
    return float(probs(counts_self)[modal_identity(counts_other)])


def modal_agreement(counts_a, counts_b):
    return int(modal_identity(counts_a) == modal_identity(counts_b))


def cos_raw(counts_a, counts_b, alpha=0.0):
    """M_AB / sqrt(M_AA * M_BB) -- the alignment channel of the exact identity.

    Cauchy-Schwarz: in [0,1], = 1 iff p_A == p_B. Removes the SCALE part of
    determinism (a policy that is uniformly sharper contributes to both numerator
    and denominator) but NOT the mode-collapse part -- see ANALYSIS_SPEC S4.2.
    """
    pa, pb = probs(counts_a, alpha), probs(counts_b, alpha)
    den = math.sqrt(float((pa * pa).sum()) * float((pb * pb).sum()))
    return float((pa * pb).sum() / den) if den > 0 else float("nan")


def match_decomposition(counts_a, counts_b, alpha=0.0):
    """The EXACT identity  log M_AB = .5 log M_AA + .5 log M_BB + log cos_raw.

    Returns the three log terms plus the two channels. Residual is 0 by construction
    and is returned so the caller can assert it.
    """
    m_ab = float((probs(counts_a, alpha) * probs(counts_b, alpha)).sum())
    m_aa = plugin_match(counts_a, alpha)
    m_bb = plugin_match(counts_b, alpha)
    c = cos_raw(counts_a, counts_b, alpha)
    det_channel = 0.5 * math.log(m_aa) + 0.5 * math.log(m_bb)
    align_channel = math.log(c) if c > 0 else float("-inf")
    return dict(
        log_cross_match=math.log(m_ab) if m_ab > 0 else float("-inf"),
        determinism_channel=det_channel,
        alignment_channel=align_channel,
        residual=(math.log(m_ab) - det_channel - align_channel) if m_ab > 0 else 0.0,
    )


# ------------------------------------------------------------- distributional distance


def js_divergence_bits(pa, pb):
    """Jensen-Shannon divergence, base 2. In [0,1]. Symmetric, finite with zeros."""
    pa, pb = np.asarray(pa, float), np.asarray(pb, float)
    m = 0.5 * (pa + pb)
    return float(entropy_bits(m) - 0.5 * entropy_bits(pa) - 0.5 * entropy_bits(pb))


def js_distance(counts_a, counts_b, alpha=0.0, miller_madow=True):
    """PRIMARY distribution_distance: sqrt(JSD) -- a true metric on the simplex.

    Miller-Madow correction removes the leading 1/n entropy bias in each of the three
    entropy terms. Because the mixture term is estimated from n_A + n_B draws while the
    two marginal terms use n_A and n_B, the net correction is NEGATIVE, i.e. it removes
    the well-known upward small-sample bias of plug-in JSD. Clamped to [0,1].
    """
    ca, cb = np.asarray(counts_a, float), np.asarray(counts_b, float)
    pa, pb = probs(ca, alpha), probs(cb, alpha)
    jsd = js_divergence_bits(pa, pb)
    if miller_madow:
        na, nb = ca.sum(), cb.sum()
        if na > 0 and nb > 0:
            # Miller-Madow on each of the three entropies: H_MM = H_plugin + (Khat-1)/(2N).
            # The mixture term uses na+nb draws while the two marginals use na and nb, so
            # the net additive correction is NEGATIVE -- it removes the upward bias that
            # plug-in JSD carries at small n. Verified numerically in the module docstring
            # test and in run_stage1.py --selftest.
            ka = max(int((ca > 0).sum()), 1)
            kb = max(int((cb > 0).sum()), 1)
            km = max(int(((ca + cb) > 0).sum()), 1)
            corr = ((km - 1) / (2.0 * (na + nb))
                    - 0.5 * (ka - 1) / (2.0 * na)
                    - 0.5 * (kb - 1) / (2.0 * nb)) / LOG2
            jsd = jsd + corr
    jsd = min(max(jsd, 0.0), 1.0)
    return float(math.sqrt(jsd))


def hellinger(counts_a, counts_b, alpha=0.0):
    """Pre-registered SECONDARY distance. Metric, bounded, most stable at small n."""
    pa, pb = probs(counts_a, alpha), probs(counts_b, alpha)
    return float(math.sqrt(max(0.0, 1.0 - float(np.sqrt(pa * pb).sum()))))


def total_variation(counts_a, counts_b, alpha=0.0):
    """Descriptive THIRD distance. Reported, never used for inference (piecewise
    linear; insensitive to redistribution inside the agreeing region)."""
    pa, pb = probs(counts_a, alpha), probs(counts_b, alpha)
    return float(0.5 * np.abs(pa - pb).sum())


# ------------------------------------------------------- tier 2: determinism adjustment


def temper(p, tau):
    """p^tau, renormalised. The tempering family is a one-parameter group:
    (q^b)^t = q^(bt). This closure is what makes standardisation exactly invariant."""
    p = np.asarray(p, dtype=float)
    p = np.clip(p, 1e-300, None)
    lp = tau * np.log(p)
    lp -= lp.max()
    e = np.exp(lp)
    return e / e.sum()


def _support_of(p):
    return float(1.0 / (np.asarray(p, float) ** 2).sum())


def tempering_exponent(p, target_support=DEFAULT_TARGET_SUPPORT):
    """tau such that effective_support(temper(p, tau)) == target_support.

    effective_support(temper(p,tau)) is strictly decreasing in tau for non-uniform p
    (-> K as tau->0, -> 1 as tau->inf), so the root is unique and bisection is exact
    to machine tolerance. Returns (tau, flag) where flag is '' or a diagnostic.
    """
    p = np.asarray(p, float)
    k = len(p)
    if target_support >= k - 1e-12:
        return 0.0, "target_ge_K"
    if np.allclose(p, p[0]):
        return 0.0, "degenerate_uniform"
    lo, hi = TAU_LO, TAU_HI
    if _support_of(temper(p, hi)) > target_support:
        return hi, "hit_tau_hi"
    if _support_of(temper(p, lo)) < target_support:
        return lo, "hit_tau_lo"
    for _ in range(80):
        mid = math.sqrt(lo * hi)
        if _support_of(temper(p, mid)) > target_support:
            lo = mid
        else:
            hi = mid
    return math.sqrt(lo * hi), ""


def standardize(counts, target_support=DEFAULT_TARGET_SUPPORT, alpha=DEFAULT_ALPHA):
    """Map an observed cell onto the reference determinism level S*.

    Returns (p_tilde, tau, beta_hat, flag). beta_hat = 1/tau is the cell's estimated
    determinism (inverse temperature) RELATIVE to the reference: beta_hat > 1 means the
    cell is sharper than the reference, < 1 means flatter.

    Exact invariance (ANALYSIS_SPEC S4.3): if p = temper(q, b) with support(q)=S*, then
    standardize(p) == q for every b > 0.
    """
    p = probs(counts, alpha)
    tau, flag = tempering_exponent(p, target_support)
    if tau <= 0:
        return p.copy(), float("nan"), float("nan"), flag or "no_solution"
    return temper(p, tau), float(tau), float(1.0 / tau), flag


def das(counts_a, counts_b, target_support=DEFAULT_TARGET_SUPPORT, alpha=DEFAULT_ALPHA):
    """PRIMARY determinism-adjusted similarity.

        DAS = S* * sum_i pt_A(i) pt_B(i)

    where pt are the two policies standardised to common effective support S*.
    Because both standardised policies have self-match exactly 1/S*, this equals the
    cosine of the standardised policies: in [0,1], = 1 iff the standardised policies
    are identical. Invariant to per-model tempering, hence unmoved by pure determinism
    change (mandatory separation, MASTER_DESIGN S5).
    """
    ta, _, _, fa = standardize(counts_a, target_support, alpha)
    tb, _, _, fb = standardize(counts_b, target_support, alpha)
    return float(target_support * (ta * tb).sum()), (fa or fb)


def dajs(counts_a, counts_b, target_support=DEFAULT_TARGET_SUPPORT, alpha=DEFAULT_ALPHA):
    """Companion adjusted similarity on the JS metric: 1 - JSdist(pt_A, pt_B)."""
    ta, _, _, _ = standardize(counts_a, target_support, alpha)
    tb, _, _, _ = standardize(counts_b, target_support, alpha)
    jsd = min(max(js_divergence_bits(ta, tb), 0.0), 1.0)
    return float(1.0 - math.sqrt(jsd))


# ------------------------------------------------- tier 3: monotone-invariant floor


def rank_similarity(counts_a, counts_b):
    """Kendall-tau-b between the two option RANKINGS, rescaled to [0,1].

    Invariant under ANY strictly monotone per-model transform of the probability
    vector, not merely tempering. Weakest assumptions, lowest resolution (K=4 gives
    only 6 comparisons); reported as the assumption-free floor under DAS.
    """
    a, b = np.asarray(counts_a, float), np.asarray(counts_b, float)
    k = len(a)
    conc = disc = ta = tb = 0
    for i in range(k):
        for j in range(i + 1, k):
            da, db = np.sign(a[i] - a[j]), np.sign(b[i] - b[j])
            if da == 0 and db == 0:
                ta += 1
                tb += 1
            elif da == 0:
                ta += 1
            elif db == 0:
                tb += 1
            elif da == db:
                conc += 1
            else:
                disc += 1
    n0 = k * (k - 1) / 2.0
    den = math.sqrt((n0 - ta) * (n0 - tb))
    if den <= 0:
        return float("nan")
    return float(((conc - disc) / den + 1.0) / 2.0)


# ----------------------------------------------------------------- position metrics


def position_metrics(rows, perm_table, modal, k=4):
    """Visual-domain position diagnostics.

    rows       iterable of dicts with 'item' (canonical choice) and 'perm_id'
    perm_table {perm_id(str) -> [canonical item at slot 0..K-1]}
    modal      the cell's modal canonical identity

    position_modal_share : max share over DISPLAY positions (chance .25)
    position_match       : unbiased dyadic self-match over display positions
    form_consistency     : 1 - (max - min) of P(choose modal | modal shown at slot p)
                           over the 4 slots; NaN unless all 4 slots are observed.
    """
    pos_counts = np.zeros(k, dtype=np.int64)
    by_slot_hits = {p: [] for p in range(k)}
    cond = {p: np.zeros(k, dtype=np.int64) for p in range(k)}
    for r in rows:
        perm = perm_table[str(r["perm_id"])]
        slot_of_choice = list(perm).index(int(r["item"]))
        pos_counts[slot_of_choice] += 1
        slot_of_modal = list(perm).index(int(modal))
        by_slot_hits[slot_of_modal].append(int(int(r["item"]) == int(modal)))
        cond[slot_of_modal][int(r["item"])] += 1
    hit = {p: float(np.mean(v)) for p, v in by_slot_hits.items() if v}
    fc = (1.0 - (max(hit.values()) - min(hit.values()))) if len(hit) == k else float("nan")
    n = pos_counts.sum()
    return dict(
        position_modal_share=float(pos_counts.max() / n) if n else float("nan"),
        position_match=within_model_match(pos_counts),
        position_counts=pos_counts.tolist(),
        form_consistency=float(fc),
        cond_choice_by_slot={str(p): cond[p].tolist() for p in range(k)},
        n_slots_observed=len(hit),
    )


# ------------------------------------------------------------------ cell / pair rollups


def cell_metrics(counts, alpha=DEFAULT_ALPHA, target_support=DEFAULT_TARGET_SUPPORT):
    """All per model x item metrics named in DATA_DICTIONARY."""
    c = np.asarray(counts, dtype=np.int64)
    pt, tau, beta, flag = standardize(c, target_support, alpha)
    return dict(
        n=int(c.sum()),
        choice_distribution=c.tolist(),
        choice_shares=[round(float(x), 6) for x in probs(c)],
        modal_identity=modal_identity(c),
        modal_share=round(modal_share(c), 6),
        modal_margin=round(modal_margin(c), 6),
        within_model_match=round(within_model_match(c), 6),
        effective_support=round(effective_support(c), 6),
        entropy_bits=round(entropy_bits(probs(c)), 6),
        n_live_options=int((probs(c) >= 0.10).sum()),
        beta_hat=round(beta, 6) if beta == beta else float("nan"),
        standardized_policy=[round(float(x), 6) for x in pt],
        standardize_flag=flag,
    )


def pair_metrics(counts_a, counts_b, alpha=DEFAULT_ALPHA,
                 target_support=DEFAULT_TARGET_SUPPORT):
    """All per model-pair x item metrics named in DATA_DICTIONARY, plus the ladder."""
    a, b = np.asarray(counts_a, np.int64), np.asarray(counts_b, np.int64)
    dec = match_decomposition(a, b, alpha)
    d, flag = das(a, b, target_support, alpha)
    return dict(
        modal_agreement=modal_agreement(a, b),
        cross_model_match=round(cross_model_match(a, b), 6),
        distribution_distance=round(js_distance(a, b, alpha), 6),          # PRIMARY
        distribution_distance_plugin=round(js_distance(a, b, alpha, False), 6),
        hellinger=round(hellinger(a, b, alpha), 6),                        # SECONDARY
        total_variation=round(total_variation(a, b, alpha), 6),            # descriptive
        p_other_modal_a_to_b=round(p_other_modal(a, b), 6),
        p_other_modal_b_to_a=round(p_other_modal(b, a), 6),
        cos_raw=round(cos_raw(a, b, alpha), 6),
        das=round(d, 6),
        dajs=round(dajs(a, b, target_support, alpha), 6),
        rank_similarity=round(rank_similarity(a, b), 6),
        determinism_channel=round(dec["determinism_channel"], 6),
        alignment_channel=round(dec["alignment_channel"], 6),
        log_cross_match=round(dec["log_cross_match"], 6),
        decomposition_residual=round(dec["residual"], 12),
        das_flag=flag,
    )


# ------------------------------------------------------------------------ inference


def ols_slope(x, y, w=None):
    x, y = np.asarray(x, float), np.asarray(y, float)
    ok = np.isfinite(x) & np.isfinite(y)
    x, y = x[ok], y[ok]
    if len(x) < 2 or np.allclose(x, x[0]):
        return float("nan"), float("nan")
    xm, ym = x.mean(), y.mean()
    b = ((x - xm) * (y - ym)).sum() / ((x - xm) ** 2).sum()
    return float(b), float(ym - b * xm)


def cluster_bootstrap_slope(x, y, clusters, b=2000, seed=20260909):
    """Slope of y on x with a cluster (item-level) bootstrap CI.

    Items are the resampling unit because the same item contributes to every model
    pair; treating pair x item rows as independent would understate the SE.
    """
    rng = np.random.default_rng(seed)
    x, y = np.asarray(x, float), np.asarray(y, float)
    clusters = np.asarray(clusters)
    uniq = np.unique(clusters)
    idx_by = {u: np.flatnonzero(clusters == u) for u in uniq}
    point, _ = ols_slope(x, y)
    draws = np.empty(b)
    for i in range(b):
        pick = rng.choice(uniq, size=len(uniq), replace=True)
        sel = np.concatenate([idx_by[u] for u in pick])
        draws[i], _ = ols_slope(x[sel], y[sel])
    good = draws[np.isfinite(draws)]
    if len(good) < 20:
        return point, float("nan"), float("nan")
    lo, hi = np.percentile(good, [2.5, 97.5])
    return point, float(lo), float(hi)


def group_slopes(records, x_key, y_key, group_key, cluster_key="item_id", b=1000,
                 seed=20260909):
    """Vintage slope of y within each level of group_key (family, mechanism, domain...)."""
    out = {}
    groups = sorted({r[group_key] for r in records})
    for gi, g in enumerate(groups):
        sub = [r for r in records if r[group_key] == g]
        if len(sub) < 3:
            continue
        pt, lo, hi = cluster_bootstrap_slope(
            [r[x_key] for r in sub], [r[y_key] for r in sub],
            [r[cluster_key] for r in sub], b=b, seed=seed + gi)
        out[g] = dict(n=len(sub), slope=pt, lo=lo, hi=hi)
    return out


def leave_one_out_slopes(records, x_key, y_key, drop_key, cluster_key="item_id",
                         b=1000, seed=20260909):
    """Leave-one-family-out / leave-one-mechanism-out sensitivity."""
    out = {}
    levels = sorted({r[drop_key] for r in records})
    full = cluster_bootstrap_slope([r[x_key] for r in records],
                                   [r[y_key] for r in records],
                                   [r[cluster_key] for r in records], b=b, seed=seed)
    out["__ALL__"] = dict(n=len(records), slope=full[0], lo=full[1], hi=full[2])
    for li, lv in enumerate(levels):
        sub = [r for r in records if r[drop_key] != lv]
        if len(sub) < 3:
            continue
        pt, lo, hi = cluster_bootstrap_slope(
            [r[x_key] for r in sub], [r[y_key] for r in sub],
            [r[cluster_key] for r in sub], b=b, seed=seed + 7919 * (li + 1))
        out[f"drop:{lv}"] = dict(n=len(sub), slope=pt, lo=lo, hi=hi)
    return out


# -------------------------------------------- determinism-matched parametric null


def support_targets(C, k=None):
    """Near-unbiased effective support per cell: 1 / within_model_match(counts).

    within_model_match is UNBIASED for sum_i p_i^2, so its reciprocal reads a cell's
    true effective support with far less bias than the plug-in 1/sum(ph_i^2). Clipped
    into (1, K)."""
    C = np.asarray(C, float)
    k = k or C.shape[1]
    w = np.array([within_model_match(c) for c in C])
    w = np.clip(w, 1.0 / (k - 1e-6), 1.0 - 1e-6)
    return np.clip(1.0 / w, 1.0 + 1e-6, k - 1e-6)


def determinism_matched_null_band(rows, b=400, target_support=DEFAULT_TARGET_SUPPORT,
                                  alpha=DEFAULT_ALPHA, seed=20260909, ref_frac=0.9,
                                  min_ref=8):
    """H0 band for the DAS-vs-vintage slope: alignment CONSTANT, determinism AS OBSERVED.

    WHY THIS EXISTS (ANALYSIS_SPEC S4.5; measurements in synthetic_validation.md). DAS is
    exactly tempering-invariant in the POPULATION but not in a finite sample, and the
    failure is not a small bias a bootstrap could remove -- it is an IDENTIFIABILITY
    LIMIT. A cell whose true effective support is ~1.02 yields (48,0,0,0) on nearly
    every draw, so the sample carries almost no information about the ORDER of the
    tail; after add-alpha smoothing all such cells standardise to nearly the same
    vector and DAS between two of them is driven toward 1 whatever the truth. Measured
    on synthetic Case A (true DAS 0.932 at every vintage):

        effective support   2.00   1.51   1.23   1.08   1.02
        estimated DAS      0.925  0.941  0.968  0.984  0.995

    Bootstrap bias correction does NOT fix this (verified: it moves the estimate the
    wrong way) because the information is absent, not merely noisy. The fix is to stop
    testing the DAS slope against ZERO and test it against the slope this same pipeline
    produces when alignment is genuinely constant and determinism follows the observed
    trajectory. The artefact then sits in the null band too, and cancels.

    Construction
      1. per-cell determinism target = support_targets(counts) -- near unbiased, since
         within_model_match is unbiased for sum p_i^2.
      2. REFERENCE ROWS = rows where BOTH cells sit at >= ref_frac * S* observed
         support. These are the rows where standardisation interpolates rather than
         extrapolates, so their standardised policies are the trustworthy ones.
      3. H0 pseudo-truth: for every row, draw a reference row at random and adopt ITS
         PAIR of standardised policies wholesale. Resampling the PAIR (not a mean
         alignment level) preserves the data's joint structure -- modal-agreement rate,
         alignment spread, shape family -- while carrying no vintage information. An
         earlier construction that matched only the MEAN alignment failed calibration
         badly (Case A rejected 100% of the time) because it under-reproduced the
         modal-agreement rate, and the artefact's size depends on it.
      4. temper both to the row's determinism target, resample at the observed n,
         recompute DAS, refit the vintage slope. b times -> null band.

    identifiable=False (fewer than min_ref reference rows) means the panel is too
    deterministic for this design to separate determinism from similarity at all. That
    is a REPORTABLE OUTCOME, not a failure to engineer around: it says the items must be
    chosen to keep effective support alive, or n raised, before the question is
    answerable.

    Conservatism, stated rather than hidden: the reference pairs are themselves
    estimated, so the null's alignment distribution is slightly over-dispersed, which
    widens the band. The test is therefore mildly conservative, in the safe direction
    for a study whose primary inferential error would be a FALSE convergence claim.

    rows : list of dicts with keys item_id, vintage, n_a, n_b, counts_a, counts_b
    """
    rng = np.random.default_rng(seed)
    Ca = np.array([r["counts_a"] for r in rows], float)
    Cb = np.array([r["counts_b"] for r in rows], float)
    xs = np.array([r["vintage"] for r in rows], float)
    na = np.array([int(r["n_a"]) for r in rows])
    nb = np.array([int(r["n_b"]) for r in rows])
    m, k = Ca.shape

    obs = das_batch(Ca, Cb, target_support, alpha)
    observed, _ = ols_slope(xs, obs)

    sa_t, sb_t = support_targets(Ca, k), support_targets(Cb, k)
    ref = (sa_t >= ref_frac * target_support) & (sb_t >= ref_frac * target_support)
    n_ref_strict = int(ref.sum())
    identifiable = bool(n_ref_strict >= min_ref)
    if not identifiable:
        # fall back to the flattest quartile so a band is still produced, but the
        # identifiable=False flag says the band rests on extrapolated shapes
        ref = (sa_t + sb_t) >= np.percentile(sa_t + sb_t, 75)
    QA_ref, _, _ = standardize_batch(Ca[ref], target_support, alpha)
    QB_ref, _, _ = standardize_batch(Cb[ref], target_support, alpha)
    delta0 = float(np.nanmean(obs[ref]))

    null = np.empty(b)
    for j in range(b):
        pick = rng.integers(0, len(QA_ref), m)      # resample PAIRS, keeping them paired
        Pa = temper_batch(QA_ref[pick], tempering_exponent_batch(QA_ref[pick], sa_t))
        Pb = temper_batch(QB_ref[pick], tempering_exponent_batch(QB_ref[pick], sb_t))
        sa = np.array([rng.multinomial(na[i], Pa[i]) for i in range(m)], float)
        sb = np.array([rng.multinomial(nb[i], Pb[i]) for i in range(m)], float)
        null[j], _ = ols_slope(xs, das_batch(sa, sb, target_support, alpha))
    good = null[np.isfinite(null)]
    # LEAD GUARD 2026-09-09. T5's logic is unchanged; this only stops a degenerate input
    # from crashing the run AFTER collection is paid for. `good` is empty whenever the
    # vintage axis has no spread -- e.g. a single model pair, where ols_slope is nan by
    # construction -- and np.percentile then raises IndexError on an empty array. A run
    # that cannot be identified must return identifiable=False, not lose the whole
    # analysis. Hit for real on the liveness preflight (one pair, 24 items).
    if good.size == 0 or not np.isfinite(observed):
        return dict(observed_slope=float(observed) if np.isfinite(observed) else None,
                    null_mean=None, null_lo=None, null_hi=None, p_two_sided=None,
                    reject=False, excess_slope=None,
                    identifiable=False, n_reference_rows=int(ref.sum()),
                    n_reference_rows_strict=n_ref_strict,
                    reference_threshold=float(ref_frac * target_support),
                    delta0=delta0, n_rows=m, b=b,
                    mean_support_a=float(sa_t.mean()), mean_support_b=float(sb_t.mean()),
                    degenerate=True,
                    degenerate_reason=("vintage axis has no spread (n distinct vintages = "
                                       f"{len(set(xs.tolist()))}) so every slope is "
                                       "undefined" if len(set(xs.tolist())) < 2
                                       else "all null replicates non-finite"))
    lo, hi = np.percentile(good, [2.5, 97.5])
    p = 2.0 * min((good <= observed).mean(), (good >= observed).mean())
    return dict(observed_slope=float(observed), null_mean=float(good.mean()),
                null_lo=float(lo), null_hi=float(hi), p_two_sided=float(min(1.0, p)),
                reject=bool(observed < lo or observed > hi),
                excess_slope=float(observed - good.mean()),
                identifiable=identifiable, n_reference_rows=int(ref.sum()),
                n_reference_rows_strict=n_ref_strict,
                reference_threshold=float(ref_frac * target_support),
                delta0=delta0, n_rows=m, b=b,
                mean_support_a=float(sa_t.mean()), mean_support_b=float(sb_t.mean()))


# backwards-compatible alias
determinism_matched_null_slope = determinism_matched_null_band


# ------------------------------------------------------- vectorised (batch) fast paths
# Identical mathematics to the scalar functions above; used by the parametric null and
# the synthetic driver, where the same transform is applied to thousands of cells.


def temper_batch(P, tau):
    """P (M,K) -> temper(P[i], tau[i]) row-wise."""
    P = np.clip(np.asarray(P, float), 1e-300, None)
    lp = np.asarray(tau, float)[:, None] * np.log(P)
    lp -= lp.max(axis=1, keepdims=True)
    e = np.exp(lp)
    return e / e.sum(axis=1, keepdims=True)


def support_batch(P):
    return 1.0 / (np.asarray(P, float) ** 2).sum(axis=1)


def tempering_exponent_batch(P, target_support=DEFAULT_TARGET_SUPPORT, iters=80):
    """Row-wise bisection for the standardising exponent. `target_support` may be a
    scalar or a per-row vector. Same bracket and tolerance as tempering_exponent();
    agreement with the scalar version is asserted in selftest()."""
    P = np.asarray(P, float)
    m = P.shape[0]
    tgt = np.broadcast_to(np.asarray(target_support, float), (m,))
    lo = np.full(m, TAU_LO)
    hi = np.full(m, TAU_HI)
    for _ in range(iters):
        mid = np.sqrt(lo * hi)
        too_flat = support_batch(temper_batch(P, mid)) > tgt
        lo = np.where(too_flat, mid, lo)
        hi = np.where(too_flat, hi, mid)
    return np.sqrt(lo * hi)


def standardize_batch(C, target_support=DEFAULT_TARGET_SUPPORT, alpha=DEFAULT_ALPHA):
    """(M,K) counts -> (P_tilde (M,K), tau (M,), beta (M,))."""
    C = np.asarray(C, float) + alpha
    P = C / C.sum(axis=1, keepdims=True)
    tau = tempering_exponent_batch(P, target_support)
    return temper_batch(P, tau), tau, 1.0 / tau


def das_batch(Ca, Cb, target_support=DEFAULT_TARGET_SUPPORT, alpha=DEFAULT_ALPHA):
    ta, _, _ = standardize_batch(Ca, target_support, alpha)
    tb, _, _ = standardize_batch(Cb, target_support, alpha)
    return target_support * (ta * tb).sum(axis=1)


def cross_match_batch(Ca, Cb):
    Pa = np.asarray(Ca, float); Pa = Pa / Pa.sum(axis=1, keepdims=True)
    Pb = np.asarray(Cb, float); Pb = Pb / Pb.sum(axis=1, keepdims=True)
    return (Pa * Pb).sum(axis=1)


def cos_raw_batch(Ca, Cb, alpha=0.0):
    Pa = np.asarray(Ca, float) + alpha; Pa = Pa / Pa.sum(axis=1, keepdims=True)
    Pb = np.asarray(Cb, float) + alpha; Pb = Pb / Pb.sum(axis=1, keepdims=True)
    num = (Pa * Pb).sum(axis=1)
    den = np.sqrt((Pa ** 2).sum(axis=1) * (Pb ** 2).sum(axis=1))
    return num / den


def effective_support_batch(C, alpha=0.0):
    P = np.asarray(C, float) + alpha
    P = P / P.sum(axis=1, keepdims=True)
    return 1.0 / (P ** 2).sum(axis=1)


def standardize_probs_batch(P, target_support=DEFAULT_TARGET_SUPPORT):
    # clip at the float64 floor, NOT at something like 1e-12: a policy tempered to
    # beta=25 legitimately has entries near 1e-33, and clipping those would destroy the
    # tail structure that standardisation must recover (this broke selftest 1).
    P = np.clip(np.asarray(P, float), 1e-300, None)
    P = P / P.sum(axis=1, keepdims=True)
    return temper_batch(P, tempering_exponent_batch(P, target_support))
