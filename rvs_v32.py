"""
rvs_v32.py: corrected RVS physics likelihood for DR4 (amendment v0.6 A25, "v3.2"). Replaces rvs_predict.llr_rvs_physics on
the DR4 path; the frozen function is kept and reported as v3.1. Each change answers an audit finding (AUDIT_REPORT.md):

  A2-F2  LLR not monotone in z  -> KDE bandwidth 1.0 (= null SD) and a monotone envelope LLR(max(z, z*)), z* = argmin
  A2-F3  40 draws, verdicts flip with the seed -> 8000 draws; a test checks the Monte Carlo SD of LLR
  A2-F4  one RNG threaded through all rows -> per-candidate seed from source_id (order-independent, reproducible)
  A2-F10 q not shared across modalities -> (q, n) drawn from p(q, n | a0, dM_G) (dark_companion.q_weights with a0),
         the same posterior the CMD/a0 term uses, instead of an independent prior q ~ U(0.5, 1)
  A2-F11 random epochs over 2000 d -> the candidate's OWN epoch times and per-epoch width errors (prereg §6.3)
  A2-F13/F14 invalid input -> NaN + reason (no information), never a silent finite number
Unchanged (registered physics): sigma0 = 11 km/s, f(1-f) blend variance, analyst-orbit perturbations as in simulate_stat,
A6 SB1 truncation (secondary-to-primary light ratio q**n >= 0.2 and K_sum(1+e) >= 30 km/s), H_p: z ~ N(0, 1).
"""
import hashlib, numpy as np
from scipy.special import logsumexp
from scipy.stats import norm
from rvs_phase_test import K_sum_kms
import dark_companion as DC

N_DRAW, BW, SIG0 = 8000, 1.0, 11.0
LMIN_SB2, DVMAX_SB2 = 0.2, 30.0

def seed_of(source_id): return int(hashlib.sha256(f'gaiafp-v32-{str(source_id).strip()}'.encode()).hexdigest()[:8], 16)

def sb1_keep_mask(q, n, K_sum, e, enabled=True):
    """Registered A6: retain H_t draws unless ell=q**n >= 0.2 AND K_sum*(1+e) >= 30 km/s.

    Do not substitute beta=ell/(1+ell): beta is the secondary fraction of TOTAL light,
    whereas the registered A6 threshold is the secondary/primary light ratio ell.
    """
    q, n, K_sum = np.asarray(q, float), np.asarray(n, float), np.asarray(K_sum, float)
    if not enabled:
        return np.ones(np.broadcast(q, n, K_sum).shape, dtype=bool)
    ell = q**n
    separation = K_sum * (1.0 + min(float(e), 0.95))
    return ~((ell >= LMIN_SB2) & (separation >= DVMAX_SB2))

def kepler_E(M, e, it=30):
    E = M + e*np.sin(M)
    for _ in range(it): E = E - (E - e*np.sin(E) - M)/(1 - e*np.cos(E))
    return E

def nu_of(t, P, e, T0):
    M = np.mod(2*np.pi*(t - T0)/P, 2*np.pi); E = kepler_E(M, e)
    return 2*np.arctan2(np.sqrt(1+e)*np.sin(E/2), np.sqrt(1-e)*np.cos(E/2))

def z_stat(tmpl, s2):
    """row-wise z = atanh(corr)*sqrt(n-3); NaN where a row has no variance (no information)."""
    a = tmpl - tmpl.mean(-1, keepdims=True); b = s2 - s2.mean(-1, keepdims=True)
    den = np.sqrt((a*a).sum(-1)*(b*b).sum(-1)); r = np.where(den > 0, (a*b).sum(-1)/np.where(den > 0, den, 1), np.nan)
    return np.arctanh(np.clip(r, -.999, .999))*np.sqrt(tmpl.shape[-1] - 3)

def z_observed(t, width, P, e, T0, om):
    nu = nu_of(np.asarray(t, float), P, e, T0); w = np.radians(om)
    return float(z_stat(((np.cos(nu + w) + e*np.cos(w))**2)[None, :], (np.asarray(width, float)**2)[None, :])[0])

def simulate_z(rng, t, werr, P, e, T0, om, sigP, K, f, n):
    """z under H_t for n draws (vectorised), the candidate's own epochs t and per-epoch width errors werr."""
    w = np.radians(om); nu = nu_of(t[None, :], P, e, T0)
    dv = K[:, None]*np.abs(np.cos(nu + w) + e*np.cos(w))
    sig_obs = np.sqrt(SIG0**2 + (f*(1-f))[:, None]*dv**2) + rng.normal(0, 1, (n, len(t)))*werr[None, :]
    Pa = P*(1 + rng.normal(0, sigP, n)); ea = np.clip(e + rng.normal(0, 0.05, n), 0, 0.95)
    Ta = T0 + rng.normal(0, 0.02*P, n); wa = np.radians(om + rng.normal(0, 10, n))
    nua = nu_of(t[None, :], Pa[:, None], ea[:, None], Ta[:, None])
    tmpl = (np.cos(nua + wa[:, None]) + ea[:, None]*np.cos(wa)[:, None])**2
    return z_stat(tmpl, sig_obs**2)

def llr_rvs(row, t, width, werr, sb1_truncate=True, n_draw=N_DRAW):
    """Return (z_obs, LLR, info). LLR = log p(z|H_t) - log p(z|H_p); NaN z -> LLR 0 with a reason (no information)."""
    t, width, werr = (np.asarray(x, float) for x in (t, width, werr))
    ok = np.isfinite(t) & np.isfinite(width) & np.isfinite(werr) & (werr > 0); t, width, werr = t[ok], width[ok], werr[ok]
    P, e, T0, om, M = (float(row[k]) for k in ('P', 'e', 'T0', 'om', 'M'))
    if len(t) < 6: return np.nan, 0.0, 'FEWER_THAN_6_EPOCHS'
    if not (P > 0 and 0 <= e < 1 and M > 0 and np.isfinite(T0) and np.isfinite(om)): return np.nan, 0.0, 'INVALID_ORBIT'
    if np.std(width) == 0: return np.nan, 0.0, 'CONSTANT_WIDTHS'
    z = z_observed(t, width, P, e, T0, om)
    if not np.isfinite(z): return np.nan, 0.0, 'Z_UNDEFINED'
    rng = np.random.default_rng(seed_of(row['source_id']))
    W = DC.q_weights(np.array([row['dm']]), np.array([row['sig_cmd']]), np.array([row['a0']]), np.array([row['a0err']]),
                     np.array([M]), np.array([P]), np.array([1000.0/row['d']]))[0]
    j = rng.choice(len(W), n_draw, p=W/W.sum()); q, nn = DC.QG[j], DC.NG[j]
    M1 = M/(1 + q**nn)**(1/nn); K = K_sum_kms(M1, q*M1, P, min(e, 0.95), float(row['inc'])); f = q**nn/(1 + q**nn)
    keep = sb1_keep_mask(q, nn, K, e, enabled=sb1_truncate)
    if keep.sum() < 50: return z, 0.0, 'H_T_EXCLUDED_BY_A6'
    sigP = float(row.get('sigP', 0.01)) if np.isfinite(row.get('sigP', np.nan)) else 0.01
    zs = simulate_z(rng, t, werr, P, e, T0, om, sigP, K[keep], f[keep], int(keep.sum())); zs = zs[np.isfinite(zs)]
    if len(zs) < 50: return z, 0.0, 'H_T_SIMULATION_UNDEFINED'
    def L(x): return float(logsumexp(norm.logpdf(x, zs, BW)) - np.log(len(zs)) - norm.logpdf(x, 0, 1))
    grid = np.linspace(-8, 8, 321); Lg = np.array([L(x) for x in grid]); zstar = grid[int(np.argmin(Lg))]
    return z, float(np.clip(L(max(z, zstar)), -30, 30)), 'OK'
