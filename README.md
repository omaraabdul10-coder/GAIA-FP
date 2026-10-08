# GAIA-FP

**Unmasking stellar impostors:** a pre-registered, Gaia-only Bayesian test for binary false positives among astrometric planet and brown-dwarf candidates (Gaia DR4).

Author: Omar Abdullayev (Ganja, Azerbaijan). Website: `index.html` (GitHub Pages).

## Key ideas
- **Physics likelihoods instead of a trained classifier.** The astrometric amplitude a0 and the colour–magnitude over-luminosity share one latent mass ratio q, so they are modelled jointly. The mass–luminosity slope is marginalised.
- **Phase-locked RVS line-width test.** It is predicted per candidate from the candidate's own orbit, epochs and precision. RV *centroids* are provably degenerate with the photocentre motion; line *widths* are not (see `rv_degeneracy.py`).
- **Label-free population prior.** It is fitted by EM on the unlabelled candidate list, and also yields the **contamination fraction** without labels.
- **Pre-registered and frozen before Gaia DR4 (2 Dec 2026).** Evaluation is blind on a sealed, RV-labelled set; only its SHA-256 is public.

## Research documents (start here)
- `FINAL_RESEARCH_STRATEGY.md`: the chosen version (v3.1), what was kept or rejected, and what remains unproven.
- `EXPERIMENT_TOURNAMENT.md`: pre-registered tournament (`TOURNAMENT_PLAN.md`), validation results, and a one-time held-out (DR5 mock) evaluation.
- `IDENTIFIABILITY_ANALYSIS.md`: when a planet and a twin impostor can or cannot be told apart.
- `NOVELTY_AND_PRIOR_ART.md` and `prior_art_notes.md`: closest prior work (notably Bailer-Jones & Kreidberg 2026) and the narrow contribution we can defend.
- `RESEARCH_OPPORTUNITIES.md`: ranked extensions, with what was actually done.

All classification numbers so far are **simulations**. The real test is the blind Gaia DR4 evaluation after 2 December 2026.

## Structure
- `src/`
  - `gaia_orbit.py`, `fit_real.py`, `mcmc_orbit.py`: astrometric orbit pipeline.
  - `joint_lr.py`, `rvs_predict.py`, `hier_em.py`: GAIA-FP v3 likelihoods and the EM prior.
  - `benchmark.py`, `eval_v3.py`, `eval_lib.py`, `contam_bins.py`: baselines, stress tests and contamination recovery.
  - `sim.py`, `lik.py`, `followup.py`, `tournament.py`, `x3_sens.py`: v3.1 tools: configurable simulator, competing hypotheses, three-way output, EIG follow-up, and the tournament.
  - `identifiability.py`, `realism.py`: identifiability maps and checks of the simulator against real cadence.
  - `inj_rec.py`: injection–recovery on real Gaia cadence.
  - `blind_eval.py`: metrics, bootstrap CIs and the freeze harness.
  - `rv_degeneracy.py`: centroid vs width theory.
  - Older v0.1 scripts are kept for the record.
- `data/` — Gaia DR4 pre-release epoch astrometry for Gaia-4 and Gaia BH3 (per-transit weighted means). Data: ESA/Gaia/DPAC.
- `results/` — `RESULTS_validation.md` (real-data pipeline check), `RESULTS_v3.md` (mock-based development), JSON outputs.
- `sealed/` — SHA-256 of the labelled sets only. The label files stay private until unblinding.
- `PREREGISTRATION.md` — hypotheses H1–H6, frozen method, metrics, deviations policy.

## External data (not included)
- Lammers & Winn (2025) mock catalogues: https://github.com/CalebLammers/GaiaForecasts → place in `dl/GaiaForecasts/` at the repository root.
- Gaia DR4 pre-release: https://www.cosmos.esa.int/web/gaia/dr4-prerelease

## Run
`./run_all.sh` reproduces everything with fixed seeds. To run individual steps:
```
pip install -r requirements.txt
cd src
python fit_real.py        # orbit fits for Gaia-4 & BH3
python mcmc_orbit.py      # posteriors
python inj_rec.py         # completeness map
python rv_degeneracy.py   # centroid vs width theory
python eval_v3.py         # v1/v2/v3/EM vs ML, stress tests, contamination recovery
python contam_bins.py     # contamination by magnitude and mass, without labels
```

## AI-use disclosure
Code drafting and the literature search were assisted by an AI system (Claude, Anthropic). Analysis choices are reviewed and owned by the author.
