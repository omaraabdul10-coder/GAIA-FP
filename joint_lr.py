"""
joint_lr.py — GAIA-FP v3 likelihood: astrometric amplitude a0 and CMD over-luminosity share the SAME latent
mass ratio q under the impostor hypothesis, so they are modelled jointly (not as independent evidence).

H_t (luminous binary): q ~ U(0.1, 1) (flat), G-band slope n ~ U(2, 6), beta = q^n/(1+q^n), M1 = M_phot/(1+q^n)^(1/n)
    a0_pred(q)  = a_rel(M1, q, P) * (q/(1+q) - beta(q)) * plx
    dM_G(q)     = -2.5 log10(1 + q^n)
H_p (dark substellar companion): m ~ log-U(0.3, 80) M_J, dM_G = 0
    a0_pred(m)  = a_rel(M1, m, P) * m/(M1+m) * plx
Likelihood ratio uses p(dM | a0, H): the a0 constraint selects the q an impostor must have (Bayes conditional),
so the selection on a0 is not double counted with the population prior pi.
The small photocentre wobble of an impostor forces q -> 1 (near twins) automatically: no hand-set q prior.
"""
import numpy as np
from scipy.special import logsumexp
MJ = 9.546e-4

def _lognorm(x, mu, s): return -0.5*((x-mu)/s)**2 - np.log(s) - 0.9189385

def llr_a0_cmd(a0, a0err, P, M, d, dm, s_cmd, nq=400, nm=300, M_relerr=0.08):
    a0 = np.asarray(a0)[:, None]; P = np.asarray(P)[:, None]; M = np.asarray(M)[:, None]; plx = 1000/np.asarray(d)[:, None]
    dm = np.asarray(dm)[:, None]
    s_a0 = np.sqrt(np.asarray(a0err)[:, None]**2 + (a0*M_relerr/3)**2)
    # latent (q, n): mass ratio and G-band mass-luminosity slope n ~ U(2, 6) (nuisance, marginalised)
    qq, nn = np.meshgrid(np.linspace(0.1, 1.0, nq), np.linspace(2.0, 6.0, 9))
    q = qq.ravel()[None, :]; n = nn.ravel()[None, :]
    lq = q**n; beta = lq/(1+lq)
    M1 = M/(1+lq)**(1/n)                       # photometric mass of the blend overestimates the primary
    arel_t = ((M1*(1+q))*(P/365.25)**2)**(1/3)
    a0t = arel_t*np.abs(q/(1+q)-beta)*plx
    La0 = _lognorm(a0, a0t, s_a0)
    # CONDITIONAL on the astrometric amplitude: candidates were SELECTED because a0 looks substellar, so the
    # marginal p(a0|H) is already part of the selection / prior pi. We use p(dM | a0, H_t), i.e. a0 only
    # tells us which q (hence which over-luminosity) an impostor would need.
    Lt = logsumexp(La0 + _lognorm(dm, -2.5*np.log10(1+lq), s_cmd), axis=1) - logsumexp(La0, axis=1)
    Lp = _lognorm(dm, 0.0, s_cmd)[:, 0]          # dark companion: no extra light, whatever its mass
    return np.clip(Lt - Lp, -30, 30)
