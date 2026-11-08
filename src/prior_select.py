"""
prior_select.py — label-free choice of how flexible the population prior pi(x) may be (GAIA-FP v3.2 candidate).

Motivation: on real Gaia DR3 the covariate EM prior saturated (mean pi = 0.94) and reordered candidates for the worse
(RESULTS_DR3.md §3). On the DR4 mocks the same prior helped. The rule therefore has to decide from the data.

Rule: for every regularisation strength C in a fixed grid (C = 0 means a constant pi, no covariates), fit EM on K-1
folds and score the held-out fold by the observed-data log-likelihood of the two-component mixture,
    log p(x_i) = log p(x_i | planet) + log( pi(x_i) * LR_i + 1 - pi(x_i) ).
The first term does not depend on pi, so only the second term is compared. It uses no labels.
The C with the highest held-out score is chosen; ties within 1 nat go to the SIMPLER model (smaller C).
"""
import numpy as np
from scipy.special import expit, logit
from sklearn.linear_model import LogisticRegression

GRID = (0.0, 0.003, 0.03, 0.3, 1.0)
TIE_NATS = 1.0

def em_fit(L, F, C, iters=300, pi0=0.3):
    """EM for pi(x). Returns a predictor F -> pi."""
    if C == 0.0:
        pi = pi0
        for _ in range(2000):
            new = float(np.clip(np.mean(expit(L + logit(pi))), 1e-4, 1-1e-4))
            if abs(new-pi) < 1e-9: break
            pi = new
        return lambda G: np.full(len(G), pi)
    lr = LogisticRegression(C=C, max_iter=500); pi = np.full(len(L), pi0)
    for _ in range(iters):
        r = expit(L + logit(np.clip(pi, 1e-4, 1-1e-4)))
        lr.fit(np.r_[F, F], np.r_[np.ones(len(F)), np.zeros(len(F))], sample_weight=np.r_[r, 1-r])
        new = lr.predict_proba(F)[:, 1]
        if np.max(np.abs(new-pi)) < 1e-5: pi = new; break
        pi = new
    return lambda G: lr.predict_proba(G)[:, 1]

def heldout_ll(L, pi):
    pi = np.clip(pi, 1e-6, 1-1e-6)
    return float(np.sum(np.logaddexp(np.log(pi) + L, np.log1p(-pi))))

def select(L, F, grid=GRID, k=5, seed=0):
    rng = np.random.default_rng(seed); fold = rng.permutation(len(L)) % k
    score = {}
    for C in grid:
        s = 0.0
        for f in range(k):
            tr, te = fold != f, fold == f
            s += heldout_ll(L[te], em_fit(L[tr], F[tr], C)(F[te]))
        score[C] = s
    best = max(score.values())
    C_star = min(C for C in grid if score[C] >= best - TIE_NATS)
    return C_star, score

def posterior(L, F, seed=0):
    """Posterior P(impostor) with the label-free selected prior. Returns p, pi, C_star, cv_scores."""
    C_star, sc = select(L, F, seed=seed)
    pi = em_fit(L, F, C_star)(F)
    return expit(L + logit(np.clip(pi, 1e-6, 1-1e-6))), pi, C_star, sc
