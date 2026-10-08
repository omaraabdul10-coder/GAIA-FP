"""MCMC: qeyri-xətti (P, e, T0) üzrə posterior; xətti parametrlər (5 astrometrik + A,B,F,G) analitik marjinallaşdırılır."""
import numpy as np, emcee, sys
from gaia_orbit import design_single, design_orbit, campbell, fit_keplerian, periodogram
from fit_real import load

def make_logpost(d, Pmin, Pmax):
    Ms = design_single(d)
    def lp(x):
        lnP, e, ph = x
        P = np.exp(lnP)
        if not (np.log(Pmin) < lnP < np.log(Pmax) and 0 <= e < 0.95 and 0 <= ph < 1): return -np.inf, None
        M = np.hstack([Ms, design_orbit(d, P, e, ph*P)])
        W = M / d['sig'][:, None]; y = d['w']/d['sig']
        A = W.T @ W; b = W.T @ y
        try: c = np.linalg.solve(A, b)
        except np.linalg.LinAlgError: return -np.inf, None
        chi2 = y @ y - b @ c
        sign, logdet = np.linalg.slogdet(A)
        return -0.5*chi2 - 0.5*logdet, c
    return lp

def run(name, P0, Pmin, Pmax, nwalk=32, nstep=3000):
    d = load(f'../data/{name}.csv')
    f = fit_keplerian(d, P0, n_e=10, n_T=16)
    s = np.sqrt(f['chi2']/(len(d['w'])-12)); d['sig'] = d['sig']*max(s, 1.0)      # chi2/dof=1 olsun deyə xətaları böyüt
    lp = make_logpost(d, Pmin, Pmax)
    def logp(x): return lp(x)[0]
    p0 = np.array([np.log(f['P']), f['e'], (f['T0']/f['P']) % 1])
    pos = p0 + 1e-4*np.random.default_rng(0).normal(size=(nwalk, 3))
    pos[:, 1] = np.clip(pos[:, 1], 0, 0.94); pos[:, 2] %= 1
    sam = emcee.EnsembleSampler(nwalk, 3, logp); sam.run_mcmc(pos, nstep, progress=False)
    ch = sam.get_chain(discard=nstep//3, thin=10, flat=True)
    a0s, incs, plx = [], [], []
    for x in ch[np.random.default_rng(1).choice(len(ch), 600, replace=False)]:
        c = lp(x)[1]; cb = campbell(*c[5:]); a0s.append(cb['a0']); incs.append(cb['inc']); plx.append(c[2])
    q = lambda v: np.percentile(v, [16, 50, 84])
    out = dict(P=q(np.exp(ch[:, 0])), e=q(ch[:, 1]), a0=q(a0s), inc=q(incs), plx=q(plx), err_scale=s, acc=np.mean(sam.acceptance_fraction))
    print(f"\n=== {name} (xəta miqyası x{s:.2f}, qəbul {out['acc']:.2f}) ===")
    for k in ('P', 'e', 'a0', 'inc', 'plx'):
        lo, me, hi = out[k]; print(f"  {k:4s} = {me:.4g}  (+{hi-me:.3g} / -{me-lo:.3g})")
    return out

if __name__ == '__main__':
    g4 = run('gaia4', 578.8, 300, 1200)
    bh = run('bh3', 4183.5, 2000, 9000)
    M, MJ = 0.64, 9.546e-4
    P = g4['P'][1]; a_rel = (M*(P/365.25)**2)**(1/3); mp = g4['a0'][1]/g4['plx'][1]/a_rel*M/MJ
    print(f"\nGaia-4b minimum-fərziyyəli kütlə ~ {mp:.1f} M_Jup (M*=0.64)")
