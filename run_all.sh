#!/usr/bin/env bash
# Reproduces every simulated result in results/ (fixed seeds). Needs the Lammers & Winn mocks in ../dl/GaiaForecasts/ relative to src/.
set -e
cd "$(dirname "$0")/src"
python fit_real.py && python mcmc_orbit.py          # real DR4 pre-release: Gaia-4 & BH3 orbits
python inj_rec.py                                     # completeness on real Gaia-4 cadence
python rv_degeneracy.py                               # centroid vs width theory
python eval_v3.py && python contam_bins.py            # v3 development results
python tournament.py val ../results/                  # tournament on VALIDATION
python x3_sens.py                                     # follow-up sensitivity
python identifiability.py && python realism.py        # identifiability maps, realism checks
python tournament.py final ../results/ 0.15 0.05      # one-time HELD-OUT (DR5) evaluation
