"""
rvs_phase_test.py — Gaia RVS epoxa xətt-eni ilə "əkiz binar" testinin gücünü simulyasiya edir.

Fizika:
  Əkiz binarda iki ulduzun spektral xətləri Δv(t) = (K1+K2)|cos(ν+ω) + e cosω| qədər ayrılır.
  Ayrılmamış iki Gaussian xəttin qarışığının dispersiyası:  σ_obs² = σ0² + f(1-f)·Δv²
  (f = ikinci ulduzun axın payı; bərabər axında f(1-f)=1/4).
  Tək ulduz + planet: Δv≈0 (planetin K-sı m/s səviyyəsindədir) → σ_obs sabitdir.
Test statistikası (fazaya bağlı, əlavə sərbəst parametr YOXDUR — orbit astrometriyadan gəlir):
  S = korrelyasiya( σ_obs²(t_i) ,  Δv²_pred(t_i) )   ; Δv_pred yalnız orbitin formasıdır (ν, ω, e)
Fərziyyələr (DR4 məlumat modeli ilə yoxlanmalıdır!):
  - n_epoch ~ 20–40 RVS tranziti 5.5 ildə
  - epoxa xətt-eni ölçmə xətası σ_meas: 2, 4, 8 km/s (parlaqlıqdan asılı)
  - instrumental genişlik σ0 ≈ 11 km/s (R≈11500 → FWHM≈26 km/s)
"""
import numpy as np, pandas as pd
from gaia_orbit import solve_kepler

G = 2.959122e-4        # AU^3 / (Msun day^2)
AU_KMS = 1731.456      # 1 AU/gün = 1731.456 km/s

def true_anomaly(t, P, e, T0):
    E = solve_kepler(np.mod(2*np.pi*(t-T0)/P, 2*np.pi), e)
    return 2*np.arctan2(np.sqrt(1+e)*np.sin(E/2), np.sqrt(1-e)*np.cos(E/2))

def K_sum_kms(M1, M2, P, e, inc_deg):
    a = (G*(M1+M2)*P**2/(4*np.pi**2))**(1/3)                  # AU
    return 2*np.pi*a*np.sin(np.radians(inc_deg))/(P*np.sqrt(1-e**2))*AU_KMS

def phase_stat(t, P, e, T0, omega_deg, sig_obs2):
    nu = true_anomaly(t, P, e, T0); w = np.radians(omega_deg)
    shape2 = (np.cos(nu+w) + e*np.cos(w))**2
    if np.std(shape2) == 0 or np.std(sig_obs2) == 0:
        return 0.0
    return float(np.corrcoef(shape2, sig_obs2)[0, 1])

def simulate_stat(is_binary, P, e, T0, omega, K, f, n_ep, sig_meas, rng, sig0=11.0, span=2000.0, dP=0.01):
    """dP: fractional period uncertainty of the analyst's astrometric orbit (default 1%; v3.1 passes the candidate's own)."""
    t = np.sort(rng.uniform(0, span, n_ep))
    nu = true_anomaly(t, P, e, T0); w = np.radians(omega)
    dv = K*np.abs(np.cos(nu+w) + e*np.cos(w)) if is_binary else 0*t
    sig_true = np.sqrt(sig0**2 + f*(1-f)*dv**2)
    sig_obs = sig_true + rng.normal(0, sig_meas, n_ep)
    # təhlilçi Gaia astrometrik orbitindən (P, e, T0, ω) istifadə edir — burada həqiqi dəyərlər + kiçik xəta
    return phase_stat(t, P*(1+rng.normal(0, dP)), np.clip(e+rng.normal(0, 0.05), 0, 0.95),
                      T0+rng.normal(0, 0.02*P), omega+rng.normal(0, 10), sig_obs**2)

def auc(s_pos, s_neg):
    s_pos, s_neg = np.asarray(s_pos), np.asarray(s_neg)
    return (np.sum(s_pos[:, None] > s_neg[None, :]) + 0.5*np.sum(s_pos[:, None] == s_neg[None, :]))/(len(s_pos)*len(s_neg))

if __name__ == "__main__":
    R = '../dl/GaiaForecasts/'
    im = pd.read_csv(R+'DR4_mock_planet_impostor_catalog.csv')
    pl = pd.read_csv(R+'DR4_mock_exoplanet_catalog.csv').sample(1500, random_state=1)
    rng = np.random.default_rng(11)
    M1, M2 = im['Primary stellar mass [M_\\odot]'].values, im['Secondary stellar mass [M_\\odot]'].values
    K = K_sum_kms(M1, M2, im['True period [days]'].values, im['True eccentricity'].values, im['True inclination [deg]'].values)
    L1 = 10**(-0.4*im['Primary G-band mag'].values); L2 = 10**(-0.4*im['Secondary G-band mag'].values)
    f = L2/(L1+L2)
    print(f"Impostor K1+K2: median {np.median(K):.1f} km/s, 10-90%: {np.percentile(K,10):.1f}-{np.percentile(K,90):.1f} km/s")
    print(f"Axın payı f: median {np.median(f):.2f}")
    print("\n n_epoch  sig_meas[km/s] |  AUC (yalnız RVS faza testi)")
    for n_ep in (20, 40):
        for sm in (2.0, 4.0, 8.0):
            sb = [simulate_stat(True, r['True period [days]'], r['True eccentricity'], r['True T_peri [days]'],
                                r['True omega [deg]'], K[i], f[i], n_ep, sm, rng) for i, (_, r) in enumerate(im.iterrows())]
            sp = [simulate_stat(False, r['True period [days]'], r['True eccentricity'], r['True T_peri [days]'],
                                r['True omega [deg]'], 0.0, 0.0, n_ep, sm, rng) for _, r in pl.iterrows()]
            print(f"   {n_ep:3d}      {sm:4.1f}         |  {auc(sb, sp):.3f}")
