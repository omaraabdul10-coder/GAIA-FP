"""
lik.py — GAIA-FP likelihood library (v3 frozen baseline + competing-hypothesis extension).

Hypotheses
  H_p  : substellar companion, no extra light
  H_t  : unresolved near-equal-mass stellar binary (impostor) — orbit and extra light share q
  H_pw : substellar companion AND an unresolved WIDE stellar companion (third light, orbit >> DR4 baseline):
         extra light like a binary, but no phase-locked RVS line-width signal (wide pair barely moves in 5.5 yr)
Returned quantities are natural-log likelihood ratios relative to H_p.
"""
import numpy as np
from scipy.stats import norm
from scipy.special import expit, logit, logsumexp
from joint_lr import llr_a0_cmd
from rvs_predict import llr_rvs_physics

def llr_rvs(X, seed=0):
    rng = np.random.default_rng(seed)
    return np.array([llr_rvs_physics(r, rng=rng) for _, r in X.iterrows()])

def llr_t(X, sig, seed=0, rvs=None):
    """v3: log p(D|H_t)/p(D|H_p) with D = (a0 [conditioning], dM_G, z_RVS)."""
    j = llr_a0_cmd(X['a0'].values, X['a0err'].values, X['P'].values, X['M'].values, X['d'].values, X['dm'].values, sig)
    r = llr_rvs(X, seed) if rvs is None else rvs
    return np.clip(j + r, -30, 30), r

def llr_w(X, sig, nq=200):
    """log p(dM|H_pw)/p(dM|H_p): third light from a wide companion, q_w ~ U(0.3,1), slope n ~ U(2,6)."""
    q, n = np.meshgrid(np.linspace(0.3, 1, nq), np.linspace(2, 6, 9)); mu = -2.5*np.log10(1+q.ravel()**n.ravel())
    dm = X['dm'].values[:, None]
    return np.clip(logsumexp(norm.logpdf(dm, mu[None, :], sig), axis=1) - np.log(mu.size) - norm.logpdf(X['dm'].values, 0, sig), -30, 30)

def effective_llr(Lt, Lw=None, w=0.0):
    """Impostor vs (substellar mixture of H_p and H_pw with weight w)."""
    if Lw is None or w == 0: return Lt
    return Lt - np.logaddexp(np.log1p(-w), np.log(w) + Lw)

def posterior(L_eff, pi):
    return expit(L_eff + logit(np.clip(pi, 1e-6, 1-1e-6)))
