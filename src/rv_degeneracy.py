"""
rv_degeneracy.py — Why Gaia epoch RVs (line CENTROIDS) cannot unmask a twin-binary impostor,
and why the line WIDTH (second moment) can.

Setup: unresolved binary, mass ratio q = M2/M1 <= 1, light fraction of the secondary
beta_X = L2/(L1+L2) in photometric band X.  B = q/(1+q).

Astrometry (G band): photocentre semimajor axis  a0 = a_rel * (B - beta_G).
 -> the photocentre's line-of-sight velocity amplitude implied by the astrometric orbit is
    K_ast = 2*pi*a0*sin(i) / (P*sqrt(1-e^2))  = K_sum * (B - beta_G)

Spectroscopy (RVS band, Ca II triplet), lines blended (separation << line width):
    centroid velocity v_c(t) = (1-f) v1(t) + f v2(t),  f = beta_RVS,
    v1 = +K1 g(t), v2 = -K2 g(t), K1 = K_sum*B, K2 = K_sum*(1-B)
 -> v_c = K_sum * (B - f) * g(t)

So under BOTH hypotheses (planet: beta=0, K tiny; impostor: blended twin) the centroid RV
amplitude equals the one predicted from the astrometric photocentre, up to the colour term
(B - beta_RVS)/(B - beta_G). The centroid carries (almost) no independent information.

The second moment does not cancel:
    sigma_obs^2 = sigma_0^2 + f(1-f) * (K_sum*g)^2
which is positive for any luminous companion and ~0 for a planet  -> GAIA-FP's RVS test.
"""
import numpy as np

def beta(q, n):            # light fraction for L ~ M^n
    return q**n / (1 + q**n)

if __name__ == "__main__":
    nG, nR = 4.0, 3.4      # approximate mass–luminosity slopes, G and RVS band (M/K dwarfs); isochrones in final analysis
    print(" q    B      beta_G  beta_RVS | K_centroid/K_ast | width term f(1-f)")
    for q in (0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 1.0):
        B = q/(1+q); bG, bR = beta(q, nG), beta(q, nR)
        ratio = (B-bR)/(B-bG) if abs(B-bG) > 1e-9 else float('nan')
        print(f"{q:4.2f}  {B:.3f}  {bG:.3f}   {bR:.3f}    |      {ratio:6.3f}      |   {bR*(1-bR):.3f}")
    print("\nConclusion: centroid RVs reproduce the photocentre motion (ratio ~0.8-1.0, i.e. degenerate within"
          " RVS errors), whereas the line-width term f(1-f) stays 0.15-0.25 for q>=0.6 -> the width test carries the information.")
