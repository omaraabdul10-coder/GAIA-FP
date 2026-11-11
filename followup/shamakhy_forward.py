"""
shamakhy_forward.py — what ground-based high-resolution spectroscopy (ShAO 2-m + ShaFES) can and cannot
tell about the 16 GAIA-FP follow-up targets.

Two hypotheses per target, both constrained to reproduce Gaia's photocentre orbit a0:
  H_sub : dark companion. Primary orbit = photocentre orbit. One narrow line. K_c = K_ast.
  H_imp : luminous stellar companion, mass ratio q solved from a0 = a_rel(q) (B(q) - beta_G(q)).
          Two blended line profiles with velocities v1 = +K1 g(t), v2 = -K2 g(t), flux weight f = beta_spec(q).
g(t) = cos(nu + omega) + e cos(omega)  (shape of the orbit; sign of omega is ambiguous from astrometry).

Forward model of the observable cross-correlation profile: sum of two Gaussians (instrumental R plus an intrinsic
width), fitted with ONE Gaussian (centroid, width) as a standard CCF pipeline would do.

Outputs per target:
  - K_ast (the centroid amplitude under H_sub),
  - q_imp, K1, K2, f under H_imp,
  - centroid amplitude predicted under H_imp  -> shows the centroid degeneracy (rv_degeneracy.py),
  - CCF width excess at the orbit extremes under H_imp vs ~0 under H_sub  -> the discriminating observable,
  - whether the two components separate (SB2) at R = 56 000 / 28 000,
  - dates of the orbit extremes (g max, g min) and of g = 0 in the ShAO observing window, with phase uncertainty
    propagated from the Gaia period error.
Approximations (stated, not hidden): L ~ M^n with n_G = 4.0, n_spec = 4.3 (main-sequence, as in rv_degeneracy.py);
intrinsic line sigma 2.5 km/s; T0 error not available in the scored file (period error only).
"""
import sys, json, csv
import numpy as np
from scipy.optimize import brentq, curve_fit

C_KMS = 299792.458
AU_KMS_YR = 4.740470463533348          # km/s per (AU/yr)
J2016 = 2457389.0                       # JD of J2016.0, Gaia DR3 reference epoch (t_periastron is counted from it)
SIG_INTR = 2.5                          # km/s, intrinsic line sigma of a slowly rotating FGK dwarf (assumption)
N_G, N_SPEC = 4.0, 4.3


def solve_kepler(M, e):
    E = M.copy()
    for _ in range(60):
        E = E - (E - e * np.sin(E) - M) / (1 - e * np.cos(E))
    return E


def g_shape(t_jd, P, e, T0_rel, om_deg):
    M = np.mod(2 * np.pi * (t_jd - (J2016 + T0_rel)) / P, 2 * np.pi)
    E = solve_kepler(M, e)
    nu = 2 * np.arctan2(np.sqrt(1 + e) * np.sin(E / 2), np.sqrt(1 - e) * np.cos(E / 2))
    w = np.radians(om_deg)
    return np.cos(nu + w) + e * np.cos(w)


def beta(q, n):
    return q ** n / (1 + q ** n)


def a_rel_AU(M1, q, P_day):
    return ((M1 * (1 + q)) * (P_day / 365.25) ** 2) ** (1 / 3)


def K_of(a_AU, P_day, e, inc_deg):
    return 2 * np.pi * a_AU * np.sin(np.radians(inc_deg)) / ((P_day / 365.25) * np.sqrt(1 - e ** 2)) * AU_KMS_YR


def solve_q_imp(a0_AU, M1, P):
    """Largest q in (0.3, 1) with a_rel (B - beta_G) = a0. None if no stellar solution exists."""
    h = lambda q: a_rel_AU(M1, q, P) * (q / (1 + q) - beta(q, N_G)) - a0_AU
    qs = np.linspace(0.3, 0.999, 400)
    v = h(qs)
    roots = [brentq(h, qs[i], qs[i + 1]) for i in range(len(qs) - 1) if v[i] * v[i + 1] < 0]
    return max(roots) if roots else None


def profile_moments(v1, v2, f, R):
    """Two blended Gaussian lines. Returns centroid (first moment), sigma (second moment), sigma of one line,
    and the number of separate peaks (2 = double-lined at this resolution)."""
    s0 = np.hypot(C_KMS / R / 2.3548, SIG_INTR)
    mu = (1 - f) * v1 + f * v2
    sig = np.sqrt(s0 ** 2 + f * (1 - f) * (v1 - v2) ** 2)
    v = np.linspace(-150, 150, 6001)
    prof = (1 - f) * np.exp(-0.5 * ((v - v1) / s0) ** 2) + f * np.exp(-0.5 * ((v - v2) / s0) ** 2)
    peaks = int(np.sum((prof[1:-1] > prof[:-2]) & (prof[1:-1] > prof[2:]) & (prof[1:-1] > 0.05 * prof.max())))
    return mu, sig, s0, peaks


def observable_nights(ra_deg, dec_deg, t0_jd, t1_jd, min_alt=30.0, min_hours=1.0):
    """JD (local midnight) of nights on which the target stays above min_alt for >= min_hours of astronomical night
    at the Shamakhy Astrophysical Observatory (40.7722 N, 48.5847 E, 1435 m)."""
    from astropy.time import Time
    from astropy.utils import iers
    iers.conf.auto_download = False
    from astropy.coordinates import EarthLocation, SkyCoord, AltAz, get_sun
    import astropy.units as u
    loc = EarthLocation(lat=40.7722 * u.deg, lon=48.5847 * u.deg, height=1435 * u.m)
    star = SkyCoord(ra_deg * u.deg, dec_deg * u.deg)
    nights = np.arange(np.floor(t0_jd) + 0.3, t1_jd, 1.0)          # ~ local midnight is JD + 0.3 (UTC+4 -> 20:00 UT)
    ok = []
    for n in nights:
        tt = Time(n + np.linspace(-0.3, 0.3, 37), format="jd")
        fr = AltAz(obstime=tt, location=loc)
        sun = get_sun(tt).transform_to(fr).alt.deg
        alt = star.transform_to(fr).alt.deg
        good = (sun < -18) & (alt > min_alt)
        ok.append(good.sum() * (0.6 * 24 / 36) >= min_hours)
    return nights[np.array(ok)]


def analyse(row, R_list=(56000, 28000), window=("2026-12-01", "2027-10-31")):
    from astropy.time import Time
    P, e, T0, inc, om = row["P"], row["e"], row["T0"], row["inc"], row["om"]
    a0_AU = row["a0"] * row["d"] / 1000.0
    K_ast = K_of(a0_AU, P, e, inc)
    out = dict(source_id=str(row["source_id"]), G=row["G"], P=P, sigP_frac=row["sigP"], e=e, K_ast=K_ast,
               P_impostor=row["P_impostor"], mfit_MJ=row["mfit"])
    q = solve_q_imp(a0_AU, row["M"], P)
    out["q_imp"] = q
    t0, t1 = Time(window[0]).jd, Time(window[1]).jd
    nights = observable_nights(row["ra"], row["dec"], t0, t1)
    out["n_observable_nights"] = int(len(nights))
    if len(nights) == 0:
        out["note"] = "not observable from ShAO in the window"
        return out
    # phase-robust extremes: average |g| over Monte Carlo draws of the period (Gaia period error)
    rng = np.random.default_rng(int(row["source_id"]) % 2**32)
    Pd = P * (1 + row["sigP"] * rng.standard_normal(200))
    G = np.array([g_shape(nights, p, e, T0, om) for p in Pd])
    gg = g_shape(nights, P, e, T0, om)
    score_hi, score_lo = np.mean(G, 0), -np.mean(G, 0)
    out["t_gmax"] = Time(nights[score_hi.argmax()], format="jd").iso[:10]
    out["t_gmin"] = Time(nights[score_lo.argmax()], format="jd").iso[:10]
    out["g_at_tgmax_nominal"], out["g_at_tgmin_nominal"] = float(gg[score_hi.argmax()]), float(gg[score_lo.argmax()])
    out["g_at_tgmax_mc_mean"], out["g_at_tgmin_mc_mean"] = float(score_hi.max()), float(-score_lo.max())
    out["first_observable"] = Time(nights[0], format="jd").iso[:10]
    gmax, gmin = out["g_at_tgmax_mc_mean"], out["g_at_tgmin_mc_mean"]
    out["sigma_phase_cycles"] = float(((t0 + t1) / 2 - (J2016 + T0)) * row["sigP"] / P)
    if q is None:
        out["note"] = "no stellar companion reproduces a0 with this M1"
        return out
    B, fG, fS = q / (1 + q), beta(q, N_G), beta(q, N_SPEC)
    Ksum = K_of(a_rel_AU(row["M"], q, P), P, e, inc)
    K1, K2 = Ksum * B, Ksum * (1 - B)
    out.update(B=B, beta_G=fG, beta_spec=fS, K_sum=Ksum, K1=K1, K2=K2)
    for R in R_list:
        best = None
        for g in (gmax, gmin):
            mu, sig, s0, npk = profile_moments(K1 * g, -K2 * g, fS, R)
            sep = Ksum * abs(g) / (2.3548 * s0)
            if best is None or sep > best[3]:
                best = (mu, sig, s0, sep, npk)
        out[f"R{R}_centroid_amp_imp"] = (fS * 0 + (1 - fS) * K1 - fS * K2) * (gmax - gmin) / 2
        out[f"R{R}_width_excess_pct"] = 100 * (best[1] / best[2] - 1)
        out[f"R{R}_sep_over_fwhm"] = best[3]
        out[f"R{R}_double_lined"] = bool(best[4] >= 2)
        # probability that at least one of the two planned spectra is double-lined (separation > 1 FWHM),
        # over the period uncertainty; and the same for one spectrum taken at a random phase
        s0 = np.hypot(C_KMS / R / 2.3548, SIG_INTR)
        i_hi, i_lo = score_hi.argmax(), score_lo.argmax()
        sep2 = Ksum * np.maximum(np.abs(G[:, i_hi]), np.abs(G[:, i_lo])) / (2.3548 * s0)
        out[f"R{R}_p_double_2epochs"] = float(np.mean(sep2 > 1.0))
        ph = np.linspace(0, P, 2000, endpoint=False) + J2016 + T0
        out[f"R{R}_p_double_random_epoch"] = float(np.mean(Ksum * np.abs(g_shape(ph, P, e, T0, om)) / (2.3548 * s0) > 1.0))
    return out


def main(targets_csv, scored_csv, out_json, out_csv):
    import pandas as pd
    T = pd.read_csv(targets_csv)
    S = pd.read_csv(scored_csv)
    m = T[["source_id", "ra", "dec"]].merge(S, on="source_id", how="left")
    res = [analyse(r) for _, r in m.iterrows()]
    json.dump(res, open(out_json, "w"), indent=1, default=float)
    keys = sorted({k for r in res for k in r}, key=lambda k: list(res[0]).index(k) if k in res[0] else 99)
    with open(out_csv, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=keys); w.writeheader(); [w.writerow(r) for r in res]
    return res


if __name__ == "__main__":
    main(*sys.argv[1:5])
