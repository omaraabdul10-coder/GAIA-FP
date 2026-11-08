import numpy as np, time
from gaia_orbit import *
truth = dict(P=571.0, e=0.40, T0=120.0, a0=0.27, inc=60.0, omega=40.0, Omega=110.0)
t=time.time()
d = simulate(orbit=truth, seed=1)
p, cov, chi0 = fit_single(d)
print("tek ulduz fit: plx=%.3f±%.3f  chi2/dof=%.2f" % (p[2], np.sqrt(cov[2,2]), chi0/(len(d['w'])-5)))
Ps, dchi, _ = periodogram(d)
k = np.argmax(dchi); print("periodoqram pik: P=%.1f gun, dchi2=%.1f" % (Ps[k], dchi[k]))
fit = fit_keplerian(d, Ps[k])
print("Kepler fit:  P=%.1f (dogru 571)  e=%.2f (0.40)  a0=%.3f mas (0.27)  inc=%.0f (60)  chi2/dof=%.2f"
      % (fit['P'], fit['e'], fit['a0'], fit['inc'], fit['chi2']/(len(d['w'])-12)))
# null test: same data without planet
dn = simulate(orbit=None, seed=1)
Psn, dchin, _ = periodogram(dn)
print("NULL: en guclu pik dchi2=%.1f  (planetli: %.1f)" % (dchin.max(), dchi[k]))
print("vaxt %.1fs" % (time.time()-t))
