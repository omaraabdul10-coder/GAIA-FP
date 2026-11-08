import numpy as np, sys
from gaia_orbit import *
def load(f):
    a=np.loadtxt(f,delimiter=','); psi=np.radians(a[:,1])
    return dict(t_day=a[:,0], sin_psi=np.sin(psi), cos_psi=np.cos(psi), f_plx=a[:,4], w=a[:,2], sig=a[:,3])
if __name__=='__main__':
  for name,Pmax in (('gaia4',3000),('bh3',9000)):
      d=load(f'../data/{name}.csv'); n=len(d['w'])
      p,cov,chi0=fit_single(d)
      print(f"\n=== {name}: {n} tranzit ===")
      print(f"Tek ulduz: plx={p[2]:.3f} mas, pm=({p[3]:.2f},{p[4]:.2f}) mas/il, chi2/dof={chi0/(n-5):.1f}")
      Ps,dchi,_=periodogram(d,Pmin=20,Pmax=Pmax,n=6000); k=np.argmax(dchi)
      print(f"Periodoqram pik: P={Ps[k]:.1f} gun, dchi2={dchi[k]:.0f}")
      best=None
      for P0 in sorted(set([Ps[k]]+list(Ps[np.argsort(dchi)[-5:]]))):
          f=fit_keplerian(d,P0,n_e=10,n_T=16)
          if best is None or f['chi2']<best['chi2']: best=f
      f=best
      print(f"Kepler: P={f['P']:.1f} gun, e={f['e']:.3f}, a0={f['a0']:.3f} mas, inc={f['inc']:.1f}, omega={f['omega']:.0f}, Omega={f['Omega']:.0f}, chi2/dof={f['chi2']/(n-12):.2f}, plx={f['lin'][2]:.3f}")
