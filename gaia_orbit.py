"""
gaia_orbit.py  —  N7 layihəsi üçün sadə, şəffaf astrometrik orbit pipeline-ı.

Gaia hər müşahidədə ulduzun mövqeyini yalnız SKAN istiqamətində (along-scan, AL) ölçür:
    w_i  (mas)  =  ölçülmüş AL mövqe
Model (tək ulduz, 5 parametr):
    w = (dra + mura*t) * sin(psi) + (ddec + mudec*t) * cos(psi) + plx * f_plx
Orbit əlavə edildikdə (Thiele–Innes, xətti 4 parametr A,B,F,G):
    w += (B*X + G*Y) * sin(psi) + (A*X + F*Y) * cos(psi)
    X = cos(E) - e,  Y = sqrt(1-e^2) sin(E),  E - e sin E = 2*pi*(t - T0)/P

Yalnız numpy/scipy istifadə olunur — hər addım lövhədə izah oluna bilər.
"""
import numpy as np
from scipy.optimize import minimize

YEAR = 365.25

# ----------------------------------------------------------------- Kepler tənliyi
def solve_kepler(M, e, tol=1e-12):
    """E - e sin E = M  tənliyini Newton üsulu ilə həll et."""
    E = np.where(e < 0.8, M, np.pi * np.ones_like(M))
    for _ in range(50):
        dE = (E - e * np.sin(E) - M) / (1 - e * np.cos(E))
        E -= dE
        if np.max(np.abs(dE)) < tol:
            break
    return E

def orbit_XY(t_day, P, e, T0):
    M = 2 * np.pi * (t_day - T0) / P
    E = solve_kepler(np.mod(M, 2 * np.pi), e)
    return np.cos(E) - e, np.sqrt(1 - e**2) * np.sin(E)

# ----------------------------------------------------------------- dizayn matrisləri
def design_single(d):
    s, c, ty = d["sin_psi"], d["cos_psi"], d["t_day"] / YEAR
    return np.column_stack([s, c, d["f_plx"], ty * s, ty * c])   # dra, ddec, plx, mura, mudec

def design_orbit(d, P, e, T0):
    X, Y = orbit_XY(d["t_day"], P, e, T0)
    s, c = d["sin_psi"], d["cos_psi"]
    return np.column_stack([c * X, s * X, c * Y, s * Y])          # A, B, F, G

def wls(Mx, w, sig):
    """Çəkili ən kiçik kvadratlar: parametrlər, kovariasiya, chi^2."""
    Wm = Mx / sig[:, None]; wv = w / sig
    p, *_ = np.linalg.lstsq(Wm, wv, rcond=None)
    cov = np.linalg.inv(Wm.T @ Wm)
    r = wv - Wm @ p
    return p, cov, float(r @ r)

def fit_single(d):
    return wls(design_single(d), d["w"], d["sig"])

def chi2_orbit(d, P, e, T0, Ms=None):
    Ms = design_single(d) if Ms is None else Ms
    return wls(np.hstack([Ms, design_orbit(d, P, e, T0)]), d["w"], d["sig"])

# ----------------------------------------------------------------- periodoqram
def periodogram(d, Pmin=30, Pmax=4000, n=4000):
    """Dairəvi orbitlər üçün (e=0) T0 xətti əmsallara 'udulur' — sürətli Δχ² periodoqramı."""
    Ms = design_single(d)
    _, _, chi0 = wls(Ms, d["w"], d["sig"])
    Ps = np.exp(np.linspace(np.log(Pmin), np.log(Pmax), n))
    dchi = np.empty(n)
    for k, P in enumerate(Ps):
        _, _, ch = chi2_orbit(d, P, 0.0, 0.0, Ms)
        dchi[k] = chi0 - ch
    return Ps, dchi, chi0

# ----------------------------------------------------------------- tam Kepler fit
def fit_keplerian(d, P_init, n_e=8, n_T=12):
    """(P, e, T0) üzrə qeyri-xətti, (A,B,F,G)+5 üzrə xətti. Əvvəl kiçik şəbəkə, sonra Nelder–Mead."""
    Ms = design_single(d)
    best = (np.inf, None)
    for e in np.linspace(0, 0.8, n_e):
        for T0 in np.linspace(0, P_init, n_T, endpoint=False):
            ch = chi2_orbit(d, P_init, e, T0, Ms)[2]
            if ch < best[0]:
                best = (ch, (P_init, e, T0))
    def f(x):
        P, e, T0 = x
        if P <= 1 or not (0 <= e < 0.97):
            return 1e30
        return chi2_orbit(d, P, e, T0, Ms)[2]
    res = minimize(f, best[1], method="Nelder-Mead",
                   options=dict(xatol=1e-6, fatol=1e-6, maxiter=4000))
    P, e, T0 = res.x
    p, cov, ch = chi2_orbit(d, P, e, T0, Ms)
    A, B, F, G = p[5:]
    return dict(P=P, e=e, T0=T0, chi2=ch, lin=p, cov=cov, **campbell(A, B, F, G))

def campbell(A, B, F, G):
    """Thiele–Innes -> a0, i, omega, Omega (standart düsturlar)."""
    u = (A**2 + B**2 + F**2 + G**2) / 2
    v = A * G - B * F
    a0 = np.sqrt(u + np.sqrt((u + v) * (u - v)))
    w_p_W = np.arctan2(B - F, A + G)
    w_m_W = np.arctan2(-B - F, A - G)
    omega = (w_p_W + w_m_W) / 2
    Omega = (w_p_W - w_m_W) / 2
    i = np.degrees(np.arccos(np.clip(v / a0**2, -1, 1)))
    return dict(a0=a0, inc=i, omega=np.degrees(omega) % 360, Omega=np.degrees(Omega) % 180)

# ----------------------------------------------------------------- simulyasiya
def simulate(n_transits=70, n_ccd=8, sig_ccd=0.4, plx=13.3, pm=(50.0, -30.0),
             orbit=None, seed=0, span_day=5.5 * YEAR):
    """
    Gaia-ya bənzər məlumat: təsadüfi skan bucaqları, Yer orbitinə əsaslanan paralaks faktoru.
    (Real skan qanunu deyil — yalnız metodun sınağı üçün.)
    orbit = dict(P, e, T0, a0, inc, omega, Omega)   [mas, gün, dərəcə]
    """
    rng = np.random.default_rng(seed)
    t_tr = np.sort(rng.uniform(-span_day / 2, span_day / 2, n_transits))
    t = np.repeat(t_tr, n_ccd)
    psi = np.repeat(rng.uniform(0, 2 * np.pi, n_transits), n_ccd)
    lam = 2 * np.pi * t / YEAR + 1.0                         # Günəşin ekliptik uzunluğu (sadə)
    ra, dec, eps = np.radians(120.0), np.radians(30.0), np.radians(23.44)
    Xs, Ys, Zs = np.cos(lam), np.sin(lam) * np.cos(eps), np.sin(lam) * np.sin(eps)
    pa = Xs * np.sin(ra) - Ys * np.cos(ra)
    pd = Xs * np.cos(ra) * np.sin(dec) + Ys * np.sin(ra) * np.sin(dec) - Zs * np.cos(dec)
    d = dict(t_day=t, sin_psi=np.sin(psi), cos_psi=np.cos(psi),
             f_plx=pa * np.sin(psi) + pd * np.cos(psi), sig=np.full(t.size, sig_ccd))
    w = design_single(d) @ np.array([0.0, 0.0, plx, pm[0], pm[1]])
    if orbit:
        A, B, F, G = thiele_innes(orbit["a0"], orbit["inc"], orbit["omega"], orbit["Omega"])
        w = w + design_orbit(d, orbit["P"], orbit["e"], orbit["T0"]) @ np.array([A, B, F, G])
    d["w"] = w + rng.normal(0, sig_ccd, t.size)
    return d

def thiele_innes(a0, inc, omega, Omega):
    i, w, W = np.radians([inc, omega, Omega])
    A = a0 * (np.cos(w) * np.cos(W) - np.sin(w) * np.sin(W) * np.cos(i))
    B = a0 * (np.cos(w) * np.sin(W) + np.sin(w) * np.cos(W) * np.cos(i))
    F = -a0 * (np.sin(w) * np.cos(W) + np.cos(w) * np.sin(W) * np.cos(i))
    G = -a0 * (np.sin(w) * np.sin(W) - np.cos(w) * np.cos(W) * np.cos(i))
    return A, B, F, G
