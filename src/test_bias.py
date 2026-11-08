import numpy as np
from gaia_orbit import *
truth = dict(P=571.0, e=0.40, T0=120.0, a0=0.27, inc=60.0, omega=40.0, Omega=110.0)
for a0 in (2.0, 0.27):
    tr = dict(truth, a0=a0); res=[]
    for s in range(12):
        d = simulate(orbit=tr, seed=100+s)
        Ps, dchi, _ = periodogram(d, n=2500)
        f = fit_keplerian(d, Ps[np.argmax(dchi)])
        res.append((f['P'], f['e'], f['a0'], f['inc'], dchi.max()))
    r=np.array(res)
    print(f"a0={a0} mas: P median {np.median(r[:,0]):.1f} [{r[:,0].min():.0f}-{r[:,0].max():.0f}], "
          f"e median {np.median(r[:,1]):.2f}, a0 median {np.median(r[:,2]):.3f}, inc median {np.median(r[:,3]):.0f}, "
          f"dchi2 median {np.median(r[:,4]):.0f}, P within 5%: {np.mean(abs(r[:,0]-571)<28.5)*100:.0f}%")
