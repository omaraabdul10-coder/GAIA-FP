"""prior_select: label-free choice of prior flexibility (synthetic data only)."""
import sys, os, numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
import prior_select as PS

def _data(informative, n=3000, seed=0):
    rng = np.random.default_rng(seed); F = rng.normal(size=(n, 3))
    pi = 1/(1+np.exp(-(2.5*F[:, 0] - 1))) if informative else np.full(n, 0.3)
    y = rng.random(n) < pi
    L = np.where(y, rng.normal(1.5, 1.5, n), rng.normal(-1.5, 1.5, n))   # roughly calibrated LLR
    return L, F, y

def test_uninformative_covariates_choose_constant_prior():
    L, F, _ = _data(False); C, _ = PS.select(L, F); assert C == 0.0

def test_informative_covariates_choose_covariate_prior():
    L, F, y = _data(True); C, _ = PS.select(L, F); assert C > 0
    p, pi, _, _ = PS.posterior(L, F); assert abs(p.mean() - y.mean()) < 0.05
