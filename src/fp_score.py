"""
fp_score.py — P(binary false positive | Gaia observations) üçün Bayes skoru (v0).

Hipotezlər:
  H_p : ulduz + qaranlıq substellar yoldaş (planet / qəhvəyi cırtdan), beta = 0
  H_t : işıqlı, oxşar kütləli binar (impostor), beta > 0

Müşahidələr (hər namizəd üçün):
  a0_obs   : fotomərkəz orbitinin yarımoxu [mas] (astrometrik fitdən)
  P_day    : period [gün]
  plx      : paralaks [mas]
  M1       : əsas ulduzun kütləsi [Msun] (rəng/parlaqlıqdan), M1_err
  dMG_obs  : CMD izafi parlaqlığı = M_G - M_G,MS(rəng)  [mag]  (mənfi = daha parlaq)
  r_rvs    : RVS xətt-eni ilə proqnozlaşdırılan |Δv_r(t)| arasındakı korrelyasiya (yoxdursa None)
  n_rvs    : RVS epoxa sayı

Hər hipotezin ehtimalı (likelihood) nuisance parametrlər üzrə Monte Carlo ilə marjinallaşdırılır.
Bu, "sadə classifier" deyil: hər ehtimal fiziki modeldən gəlir (Kepler + kütlə–işıqlılıq).
"""
import numpy as np

G_AU3_MSUN_YR2 = 4 * np.pi**2          # Kepler III: a^3 = M P^2 (AU, Msun, yr)
SIG_CMD = 0.12                         # CMD izafi parlaqlığında astrofiziki səpələnmə [mag] (metallik/yaş)

def mass_lum_beta(q):
    """G zolağında axın payı beta = L2/(L1+L2), sadə L ~ M^4 yaxınlaşması (v0; sonra izoxronla əvəz olunacaq)."""
    l = q**4
    return l / (1 + l)

def predicted_a0(P_day, M1, q, plx, beta):
    a_rel_au = ((M1 * (1 + q)) * (P_day / 365.25) ** 2) ** (1 / 3)
    return a_rel_au * plx * (q / (1 + q) - beta)

def loglike_obs(x, mu, sig):
    return -0.5 * ((x - mu) / sig) ** 2 - np.log(sig)

def log_likelihoods(obs, n_mc=4000, rng=None):
    rng = np.random.default_rng(0) if rng is None else rng
    M1 = np.clip(rng.normal(obs["M1"], obs["M1_err"], n_mc), 0.08, None)
    sig_a0 = obs["a0_err"]
    # ---- H_p: qaranlıq yoldaş, kütlə log-uniform 1–80 M_Jup
    mp = np.exp(rng.uniform(np.log(1), np.log(80), n_mc)) * 9.546e-4 / M1      # q = Mp/M1
    a0p = np.abs(predicted_a0(obs["P_day"], M1, mp, obs["plx"], 0.0))
    Lp = loglike_obs(obs["a0_obs"], a0p, sig_a0) + loglike_obs(obs["dMG_obs"], 0.0, SIG_CMD)
    # ---- H_t: işıqlı binar, q ~ U(0.5, 1)
    q = rng.uniform(0.5, 1.0, n_mc)
    beta = mass_lum_beta(q)
    a0t = np.abs(predicted_a0(obs["P_day"], M1, q, obs["plx"], beta))
    dMG_t = -2.5 * np.log10(1 + q**4)
    Lt = loglike_obs(obs["a0_obs"], a0t, sig_a0) + loglike_obs(obs["dMG_obs"], dMG_t, SIG_CMD)
    # ---- RVS xətt-eni fazası (yalnız mövcud olduqda)
    if obs.get("r_rvs") is not None:
        se = 1 / np.sqrt(max(obs["n_rvs"] - 3, 1))
        z = np.arctanh(np.clip(obs["r_rvs"], -0.999, 0.999))
        Lp = Lp + loglike_obs(z, 0.0, se)                                         # H_p: korrelyasiya yoxdur
        Lt = Lt + loglike_obs(z, np.arctanh(0.6) * np.ones(n_mc), se)              # H_t: güclü müsbət (v0 fərziyyə)
    lse = lambda L: np.max(L) + np.log(np.mean(np.exp(L - np.max(L))))
    return lse(Lp), lse(Lt)

def p_binary(obs, prior_binary=0.3, **kw):
    """P(H_t | data). Prior müstəqil mənbədən olmalıdır (məlumat sızması olmasın!)."""
    lp, lt = log_likelihoods(obs, **kw)
    lo = (lt - lp) + np.log(prior_binary / (1 - prior_binary))
    return 1 / (1 + np.exp(-lo))
