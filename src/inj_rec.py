"""Real Gaia-4 kadensi və skan bucaqları ilə injeksiya–bərpa: FAP həddi + tamlıq xəritəsi."""
import numpy as np, json, time
from gaia_orbit import design_single, design_orbit, thiele_innes, wls
from fit_real import load
rng = np.random.default_rng(2026)
d0 = load('../data/gaia4.csv'); d0['sig'] = d0['sig']*1.23          # MCMC-dən alınan xəta miqyası
Ms = design_single(d0); N = len(d0['sig'])
Ps = np.exp(np.linspace(np.log(30), np.log(2500), 700))
ORB = {P: design_orbit(d0, P, 0.0, 0.0) for P in Ps}           # dairəvi şablonlar (T0 xətti əmsallara udulur)
def max_dchi(w):
    _, _, c0 = wls(Ms, w, d0['sig']); best = (0, None)
    for P in Ps:
        _, _, c = wls(np.hstack([Ms, ORB[P]]), w, d0['sig'])
        if c0-c > best[0]: best = (c0-c, P)
    return best
truth5 = np.array([0, 0, 13.62, -75.55, 17.94])
# 1) null paylanma -> 1% FAP həddi
t = time.time(); null = []
for _ in range(400):
    w = Ms @ truth5 + rng.normal(0, d0['sig']); null.append(max_dchi(w)[0])
thr = float(np.percentile(null, 99)); print(f"Null: median {np.median(null):.1f}, 99% (FAP=1%) hədd = {thr:.1f}   [{time.time()-t:.0f}s]")
# 2) injeksiya: 0.64 Msun ulduz, məsafə 50 və 100 pc
MJ = 9.546e-4; res = {}
for dist in (50, 100):
    plx = 1000/dist; grid = []
    for mp in (0.5, 1, 2, 4, 8, 16):
        row = []
        for P in (100, 250, 600, 1200, 2400):
            ok = 0; ntr = 40
            for _ in range(ntr):
                M = 0.64; a_rel = ((M+mp*MJ)*(P/365.25)**2)**(1/3); a0 = a_rel*mp*MJ/(M+mp*MJ)*plx
                inc = np.degrees(np.arccos(rng.uniform(-1, 1))); e = min(rng.rayleigh(0.2), 0.8)
                A,B,F,G = thiele_innes(a0, inc, rng.uniform(0,360), rng.uniform(0,180))
                w = Ms @ np.array([0,0,plx,-75.55,17.94]) + design_orbit(d0, P, e, rng.uniform(0,P)) @ np.array([A,B,F,G]) + rng.normal(0, d0['sig'])
                dc, Pb = max_dchi(w)
                ok += (dc > thr) and (abs(Pb/P-1) < 0.15)
            row.append(ok/ntr)
        grid.append(row); print(f"  {dist}pc  {mp:>4} MJ: " + " ".join(f"{x:4.2f}" for x in row), flush=True)
    res[dist] = grid
json.dump(dict(thr=thr, periods=[100,250,600,1200,2400], masses=[0.5,1,2,4,8,16], completeness=res), open('../data/inj_rec_gaia4cadence.json','w'), indent=1)
print(f"cəmi {time.time()-t:.0f}s")
