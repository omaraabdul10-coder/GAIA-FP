"""Fit radius(beta) = slope * |beta0 - beta| to the bench runs.
Input CSV with columns: beta,beta_err,radius,radius_err (radius in px or mm, any one unit).
Usage: python fit_v.py runs.csv [--d D_in_same_unit] [--B B_mechanical]"""
import sys, json, argparse, numpy as np, pandas as pd
from scipy.optimize import least_squares
ap = argparse.ArgumentParser(); ap.add_argument('csv'); ap.add_argument('--d', type=float); ap.add_argument('--B', type=float)
a = ap.parse_args(); t = pd.read_csv(a.csv)
def res(p):
    s, b0 = p
    sig = np.hypot(t.radius_err, s * t.beta_err)
    return (t.radius - s * np.abs(b0 - t.beta)) / sig
f = least_squares(res, [t.radius.max() / 0.3, t.beta[t.radius.idxmin()]])
J = f.jac; cov = np.linalg.inv(J.T @ J) * max(1.0, (f.fun ** 2).sum() / (len(t) - 2))
out = dict(slope=f.x[0], slope_err=float(np.sqrt(cov[0, 0])), beta0=f.x[1], beta0_err=float(np.sqrt(cov[1, 1])),
           chi2_per_dof=float((f.fun ** 2).sum() / (len(t) - 2)))
if a.d: out['slope_vs_d_pct'] = 100 * (f.x[0] / a.d - 1)
if a.B is not None: out['beta0_minus_B'] = f.x[1] - a.B
print(json.dumps(out, indent=1))
