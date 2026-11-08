"""eval_lib.py — shared scoring functions (v1/v2/v3 likelihood ratios) used by eval_v3.py and contam_bins.py."""
import json, sys, warnings, numpy as np, pandas as pd
warnings.filterwarnings('ignore')
from scipy.stats import norm
from scipy.special import expit, logit
from sklearn.ensemble import HistGradientBoostingClassifier
import benchmark as B, hier_em as H
from rvs_predict import llr_rvs_physics
from joint_lr import llr_a0_cmd

def llr_cmd(X, sig):
    dm = X['dm'].values
    return np.log(np.mean(norm.pdf(dm[:, None], H.mu_cmd[None, :], sig), axis=1)) - norm.logpdf(dm, 0, sig)
def llr_rvs_v1(X):
    z = X['z'].values; out = np.zeros(len(z)); m = np.isfinite(z)
    out[m] = np.log(np.mean(norm.pdf(z[m][:, None], H.mu_z[None, :], 1), axis=1)) - norm.logpdf(z[m], 0, 1); return out
def llr_rvs_v2(X, seed):
    rng = np.random.default_rng(seed); return np.array([llr_rvs_physics(r, rng=rng) for _, r in X.iterrows()])

def scores(X, sig, seed):
    c = llr_cmd(X, sig); r2 = llr_rvs_v2(X, seed)
    j = llr_a0_cmd(X['a0'].values, X['a0err'].values, X['P'].values, X['M'].values, X['d'].values, X['dm'].values, sig)
    return dict(cmd=np.clip(c, -30, 30), v1=np.clip(c + llr_rvs_v1(X), -30, 30), v2=np.clip(c + r2, -30, 30),
                v3_joint_a0=j, v3=np.clip(j + r2, -30, 30))

