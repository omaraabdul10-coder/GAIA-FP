"""Injection-recovery check of the M3 depletion statistic (no vbroad used). Synthetic catalogues are built from the real
orbital parameters with a redrawn companion; one WITHOUT and one WITH Gaia-like SB2 removal. M3 must give D ~ 1 and D << 1."""
import json, numpy as np, pandas as pd
import mechanism as M

X = pd.read_csv('../results/dark_companion_scored.csv', dtype={'source_id': str})
X['rho_sig'] = M.rho_sigma(X); X = M.physics(X)
V = np.isfinite(X.vbroad) & (X.vbroad_nb_transits >= 5) & np.isfinite(X.vb_med) & (X.vb_sig > 0)
Y = X[V & np.isfinite(X[['Kmax', 'beta', 'rho_sig']]).all(1)].reset_index(drop=True)
rng = np.random.default_rng(11); n = len(Y)
q = rng.uniform(0.1, 1, n); nn = rng.choice(np.arange(2.0, 6.01, 0.5), n)
m1 = Y.m1.values; Pyr = Y.period.values/365.25; e = Y.eccentricity.clip(0, 0.95).values; s = np.sin(np.radians(Y.inc.values))
m2 = q*m1; arel = ((m1 + m2)*Pyr**2)**(1/3); B = m2/(m1 + m2); beta = q**nn/(1 + q**nn)
S = Y.copy(); S['a0'] = arel*np.abs(B - beta)*Y.parallax.values + Y.a0err.values*rng.standard_normal(n)
S['K1'] = M.VKMS*arel*B*s/(Pyr*np.sqrt(1 - e**2)); S['Kmax'] = S.K1/B*Y.smax.values
S['beta'] = np.clip(B*(1 - (1 - beta/B + Y.rho_sig.values*rng.standard_normal(n))), 0, 0.5)
det = (S.a0/S.a0err >= np.percentile(Y.a0/Y.a0err, 1)) & (S.K1 >= np.percentile(Y.K1, 1))
sb2 = (beta >= 0.2) & (S.Kmax >= 30)
out = {}
for name, keep in (('no_selection', det), ('with_sb2_removal', det & ~sb2)):
    r = M.m3(S[keep].reset_index(drop=True), 'uniform'); out[name] = dict(n=int(keep.sum()), D=r['D'], pass_=r['pass_'])
print(json.dumps(out, indent=1)); json.dump(out, open('../results/mechanism_m3_validation.json', 'w'), indent=1)
