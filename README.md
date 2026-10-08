# GAIA-FP

Gaia-only probabilistic test for stellar-binary impostors among astrometric substellar candidates (Gaia DR4).

## Structure
- `src/` — pipeline (numpy/scipy/emcee): orbit fit, MCMC, FP score, blind-evaluation harness, RVS phase test, injection–recovery
- `data/` — Gaia DR4 pre-release epoch astrometry (per-transit weighted means) for Gaia-4 and Gaia BH3
- `results/` — validation against published orbits, injection–recovery map
- `sealed/` — SHA-256 of the labelled set only (the label file itself is kept private until unblinding)
- `PREREGISTRATION.md` — hypotheses, metrics, thresholds; commit before 2 Dec 2026

## External data (not included)
- Lammers & Winn mock catalogues: https://github.com/CalebLammers/GaiaForecasts → place in `dl/GaiaForecasts/`
- Gaia DR4 pre-release: https://www.cosmos.esa.int/web/gaia/dr4-prerelease

## Run
pip install numpy scipy pandas emcee
cd src && python fit_real.py        # orbit fits for Gaia-4 & BH3
python mcmc_orbit.py      # posteriors
python inj_rec.py         # completeness map
