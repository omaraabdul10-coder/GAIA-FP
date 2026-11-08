# GAIA-FP QA2 add-on (2026-11-01) — how to run each component

Unfrozen engineering add-on. No preregistered hypothesis, threshold, frozen file or existing source file was edited
(verified with `diff -rq` against the uploaded zip: only new files were added). Everything uses NEW files.

Run all commands from `src/` unless noted. Python 3.12, numpy/scipy/pandas/scikit-learn; `requests` for the live test.

## Task 1 — live Gaia Archive smoke test (`src/gaia_live_smoke.py`)
    python gaia_live_smoke.py --release gaiadr3 --timeout 30 --out ../results/qa2/live_smoke_report.json
TAP (`SELECT TOP 3 ... FROM gaiadr3.gaia_source`) and DataLink (link table for one source, default Gaia BH3) are tested as two
independent stages. Each is PASS / FAIL(category: DNS, CONNECT, TIMEOUT, TLS, HTTP_<code>, AUTH, API_CHANGED) / SKIPPED. Exit code 0 only if both PASS.
Anonymous access, no credentials stored. Use `--release gaiadr4` on release day (not meaningful before).
`dr4_fetch.py` (authenticated bulk fetch) is untouched and still unverified live.

## Task 2 — H6 comparison (`src/h6_runner.py`)
    python h6_runner.py --catalogue CAT.csv [--label-col y] [--ml-score-col ml] --out h6_report.json
    python h6_runner.py --selftest        # SYNTHETIC mechanics check, not a result
Same registered procedure as `dr4_evaluate.h6` (AUC_ML − AUC_GAIA-FP, paired stratified bootstrap, 2000 reps, seed 7, percentile 95% CI,
falsified iff CI entirely > 0; min 10/class). ML scores either from a catalogue column or by training `tournament.ml_model` on the simulator.
Needs (otherwise NOT_CONDUCTED with an exact list): `../dl/GaiaForecasts/DR4_mock_planet_impostor_catalog.csv`,
`../dl/GaiaForecasts/DR4_mock_exoplanet_catalog.csv` (Lammers & Winn mocks) and catalogue columns `P,e,mfit,d,G,dm,z,y,P_impostor`.

## Task 3 — DR4 epoch-astrometry adapter (`src/dr4_epoch_adapter.py`, `configs/dr4_epoch_astrometry_mapping.template.json`)
    import dr4_epoch_adapter as A; epochs, qc = A.adapt(df, mapping_dict_or_json_path)
Copy the template, fill column names from the RELEASED DR4 data model (placeholders are rejected). Handles time units
(ns/days since 2010 TCB, JD, Julian year) → days relative to a stated reference epoch, CCD selection, NaN/sentinel/flag filtering with counts,
sigma/variance/inverse-variance uncertainties with explicit scale/floor/extra noise. No DR4 names are assumed; nothing is validated on DR4.

## Task 4 — sensitivity / uncertainty (`src/sensitivity.py`)
A. `read_isochrone_table(text_or_path)`, `IsoAssumptions(name, log_age, mh, av, ag_over_av)`, `compare_assumptions(MG, table, [..], reference, thresholds_msun)`.
   PARSEC and MIST layouts; no table is bundled; A_G/A_V must be supplied by you whenever A_V ≠ 0.
B. `null_calibration(n_rep, n_pos=39, n_neg=26, n_boot=2000, statistic='auc'|'dauc')` — synthetic-null type-I diagnostic of the registered p rule.
C. `covariance_from_corr`, `validate_covariance`, `sample_ti`, `compare_correlated_vs_diagonal`, explicit `nearest_psd` (never automatic).

## Tests
    python tools/mini_runner.py tests/test_live_smoke.py tests/test_h6_runner.py tests/test_dr4_epoch_adapter.py tests/test_sensitivity.py
    # with pytest installed:  PYTHONPATH=src pytest -q
`tools/mini_runner.py` exists only because pytest could not be installed offline in the authoring sandbox.
All fixtures are SYNTHETIC and labelled; stub-transport tests prove parsing logic only, not live access.
