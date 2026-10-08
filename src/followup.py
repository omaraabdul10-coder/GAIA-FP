"""
followup.py — expected information gain (EIG) of follow-up observations for ambiguous candidates,
and a TRUTH-BASED outcome simulator used only for validation.

Options (illustrative instrument assumptions, explored in the sensitivity run):
  O1  ground high-resolution spectroscopy, 3 epochs (cost 3): double-lined (SB2) detection if the line
      separation K_sum*|cos(nu+w)+e cos w| exceeds DV_MIN at >=1 epoch. False SB2 rate under H_p: FP_SB2.
  O2  speckle / AO imaging, 1 visit (cost 1): binary resolved if projected separation > RHO_MIN.
  O3  single medium-resolution spectrum (cost 1): metallicity -> CMD scatter shrinks from sig to SIG_Z,
      plus a one-epoch SB2 check.
Under H_t, (q, n) are drawn from their posterior given a0 and dM_G (same grid as joint_lr.py), so the
EIG uses only Gaia information. Entropies in bits. GAIA-FP does not acquire observations itself.
"""
import numpy as np
from scipy.stats import norm
from scipy.special import expit, logit, logsumexp
from rvs_phase_test import K_sum_kms, true_anomaly

DV_MIN, FP_SB2, RHO_MIN, SIG_Z = 8.0, 0.01, 30.0, 0.12
G_GRAV = 2.959122e-4

def H2(p):
    p = np.clip(p, 1e-12, 1-1e-12); return -(p*np.log2(p) + (1-p)*np.log2(1-p))

def q_post(row, sig, k, rng):
    """Draw (q, n, M1) under H_t from p(q, n | a0, dM_G)."""
    q, n = np.meshgrid(np.linspace(0.1, 1.0, 300), np.linspace(2.0, 6.0, 9)); q, n = q.ravel(), n.ravel()
    lq = q**n; beta = lq/(1+lq); M1 = row['M']/(1+lq)**(1/n)
    plx = 1000/row['d']; arel = ((M1*(1+q))*(row['P']/365.25)**2)**(1/3)
    a0t = arel*np.abs(q/(1+q)-beta)*plx
    s_a0 = np.sqrt(row['a0err']**2 + (row['a0']*0.08/3)**2)
    lw = norm.logpdf(row['a0'], a0t, s_a0) + norm.logpdf(row['dm'], -2.5*np.log10(1+lq), sig)
    w = np.exp(lw - logsumexp(lw)); i = rng.choice(len(q), k, p=w)
    return q[i], n[i], M1[i], arel[i], plx

def _sep_kms(K, P, e, om, rng, n_ep):
    t = rng.uniform(0, P, (len(K), n_ep)); nu = true_anomaly(t, P, e, 0.0); w = np.radians(om)
    return K[:, None]*np.abs(np.cos(nu+w) + e*np.cos(w))

def _rho_proj(arel, plx, e, inc, P, rng):
    t = rng.uniform(0, P, len(arel)); nu = true_anomaly(t, P, e, 0.0); w = rng.uniform(0, 2*np.pi, len(arel))
    r = arel*(1-e**2)/(1+e*np.cos(nu)); i = np.radians(inc)
    return r*np.sqrt(np.cos(nu+w)**2 + (np.sin(nu+w)*np.cos(i))**2)*plx

def eig(row, p, sig, rng, k=300):
    """Return dict option -> (EIG bits, cost). p = current P(H_t | data)."""
    q, n, M1, arel, plx = q_post(row, sig, k, rng)
    e = min(row['e'], 0.95)
    K = K_sum_kms(M1, q*M1, row['P'], e, row['inc'])
    out = {}
    # O1: 3-epoch SB2
    d1 = np.mean(_sep_kms(K, row['P'], e, row['om'], rng, 3).max(1) > DV_MIN)
    py = p*d1 + (1-p)*FP_SB2
    out['O1_RV_3ep'] = (H2(p) - (py*H2(p*d1/max(py, 1e-12)) + (1-py)*H2(p*(1-d1)/max(1-py, 1e-12))), 3)
    # O2: imaging
    d2 = np.mean(_rho_proj(arel, plx, e, row['inc'], row['P'], rng) > RHO_MIN)
    py = p*d2
    out['O2_imaging'] = (H2(p) - (py*0 + (1-py)*H2(p*(1-d2)/max(1-py, 1e-12))), 1)
    # O3: one spectrum -> metallicity-corrected CMD (sig -> SIG_Z) + 1-epoch SB2, Monte Carlo
    d3 = np.mean(_sep_kms(K, row['P'], e, row['om'], rng, 1).max(1) > DV_MIN)
    mc = 400; Ht = rng.random(mc) < p
    dm_t = np.where(Ht, -2.5*np.log10(1+q[rng.integers(0, k, mc)]**n[rng.integers(0, k, mc)]), 0.0)
    dm2 = dm_t + rng.normal(0, SIG_Z, mc)
    sb2 = np.where(Ht, rng.random(mc) < d3, rng.random(mc) < FP_SB2)
    # likelihoods for each simulated outcome
    mu_t = -2.5*np.log10(1+q**n)
    lt = logsumexp(norm.logpdf(dm2[:, None], mu_t[None, :], SIG_Z), axis=1) - np.log(k) + np.where(sb2, np.log(max(d3, 1e-9)), np.log(max(1-d3, 1e-9)))
    lp = norm.logpdf(dm2, 0, SIG_Z) + np.where(sb2, np.log(FP_SB2), np.log(1-FP_SB2))
    # prior for the update removes the old CMD term: use p_noCMD = p with CMD evidence divided out (approx: use p)
    post = expit(lt - lp + logit(np.clip(p, 1e-9, 1-1e-9)) - row.get('llr_cmd', 0.0))
    out['O3_spec_1ep'] = (float(H2(p) - np.mean(H2(post))), 1)
    return out

# --------------------------------------------------------------------------- truth-based outcome simulator
def simulate_outcome(row, option, p, sig, rng):
    """Use TRUE parameters (t_ columns) to draw the observation, then update p with the Gaia-only model."""
    is_t = row['y'] == 1
    if option == 'O1_RV_3ep':
        e = min(row['t_e'], 0.95)
        sb2 = (_sep_kms(np.array([row['t_K']]), row['t_P'], e, rng.uniform(0, 360), rng, 3).max() > DV_MIN) if is_t else (rng.random() < FP_SB2)
        q, n, M1, arel, plx = q_post(row, sig, 300, rng)
        d1 = np.mean(_sep_kms(K_sum_kms(M1, q*M1, row['P'], min(row['e'], .95), row['inc']), row['P'], min(row['e'], .95), row['om'], rng, 3).max(1) > DV_MIN)
        lr = (d1/FP_SB2) if sb2 else ((1-d1)/(1-FP_SB2))
    elif option == 'O2_imaging':
        res = (_rho_proj(np.array([row['t_arel']]), row['t_plx'], min(row['t_e'], .95), row['t_inc'], row['t_P'], rng)[0] > RHO_MIN) if is_t else False
        q, n, M1, arel, plx = q_post(row, sig, 300, rng)
        d2 = np.mean(_rho_proj(arel, plx, min(row['e'], .95), row['inc'], row['P'], rng) > RHO_MIN)
        lr = 1e6 if res else (1-d2)
    else:
        e = min(row['t_e'], 0.95)
        sb2 = (_sep_kms(np.array([row['t_K']]), row['t_P'], e, rng.uniform(0, 360), rng, 1).max() > DV_MIN) if is_t else (rng.random() < FP_SB2)
        dm2 = row['t_dm'] + rng.normal(0, SIG_Z)
        q, n, M1, arel, plx = q_post(row, sig, 300, rng)
        d3 = np.mean(_sep_kms(K_sum_kms(M1, q*M1, row['P'], min(row['e'], .95), row['inc']), row['P'], min(row['e'], .95), row['om'], rng, 1).max(1) > DV_MIN)
        lt = logsumexp(norm.logpdf(dm2, -2.5*np.log10(1+q**n), SIG_Z)) - np.log(len(q))
        lr = np.exp(np.clip(lt - norm.logpdf(dm2, 0, SIG_Z) - row.get('llr_cmd', 0.0), -30, 30)) * ((d3/FP_SB2) if sb2 else ((1-d3)/(1-FP_SB2)))
    return float(expit(np.log(max(lr, 1e-30)) + logit(np.clip(p, 1e-9, 1-1e-9))))
