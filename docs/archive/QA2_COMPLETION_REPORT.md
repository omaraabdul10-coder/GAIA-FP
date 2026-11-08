# QA2 completion report — CORRECTED after consistency audit (2026-11-01)

Supersedes the earlier version. Nothing below claims scientific validation, a passing full suite, or any real-Gaia result.

## Status by area
| Area | IMPLEMENTED | TESTED (synthetic/stub only) | REAL-DATA-VERIFIED | NOT-COMPLETED |
|---|---|---|---|---|
| 1 Live TAP/DataLink (`gaia_live_smoke.py`) | yes | 8 stub-transport tests (error classes, API-change, stage independence, no false live claim) | **NO. The only live attempt FAILED (DNS on both stages)** | live run on a connected machine; DR4 endpoints |
| 2 H6 runner (`h6_runner.py`) | yes | 8 tests, incl. numerical equivalence with legacy `dr4_evaluate.h6` on identical SYNTHETIC inputs | NO | simulator mocks `dl/GaiaForecasts/DR4_mock_*` + scored catalogue; the training path (`tournament.ml_model` on real mocks) was never executed |
| 3 DR4 epoch adapter | yes | 10 tests, synthetic fixtures with invented column names | NO (DR4 unreleased) | fill mapping from released data model; H4 orbit fit on real epochs |
| 4A Isochrone sensitivity | yes | 5 tests, synthetic analytic tables | NO | no real PARSEC/MIST table; assumptions must be chosen |
| 4B Bootstrap null calibration | yes | 2 tests + 2 synthetic runs | NO; diagnostic only (`scientific_calibration_complete` hard-coded False) | high-n run, stated tolerance, real score distributions |
| 4C Correlated Thiele–Innes | yes | 4 tests | NO | real covariance/correlation fields not ingested |

## Audit findings
1. **"2,000 replicates" vs 500/300.** Two different quantities. `n_boot = 2000` is the number of bootstrap resamples inside ONE simulated null dataset (the registered procedure's replicate count). `n_rep = 500` (AUC rule) and `300` (ΔAUC rule) are how many independent null datasets were simulated, i.e. how many p-values the rejection rates are based on. My earlier table headed its count column just "Reps", which blurred this; the Wilson intervals depend only on n_rep. Corrected table below.
2. **Which tests ran (mini-runner, Python 3.12.3).** New: 37/37 passed (35 originally + 2 added during this audit). Legacy: 47 of the 53 pytest-collected tests ran and passed: core 7, dr3_integration 1, dr3_study 8, dr4_adapters 4, dr4_dynamical 2, dr4_empirical 2, dr4_evaluate 7, dr4_schema 5, mechanism 3, prior_select 2, qa_extensions 6. **NOT run: `tests/test_rvs_v32.py` — 6 collected tests (3 plain test functions plus `test_mc_noise_small` parametrized over signal 0/60/100), because the shim does not implement `pytest.mark.parametrize`.** The 53-test pytest result was not reproduced, `audit/tests_geometry.py` and `audit/tests_stats.py` were not run, and the mini-runner is not pytest (no fixtures beyond `tmp_path`, no markers, no warnings capture).
3. **Why pytest failed.** First `pip install pytest` stopped at PEP 668 (externally managed environment). With `--break-system-packages` it failed with `Name or service not known` for `/simple/pytest/` → "No matching distribution found": the sandbox has no network (bash network disabled). It is an environment limit, not a project problem.
4. **Originals unchanged.** `diff -rq` against the uploaded zip: 0 differing files, 0 files removed; only added files (4 modules, 4 test files + `_minipytest.py`, `tools/mini_runner.py`, `configs/`, `results/qa2/`, 2 docs) plus `__pycache__` bytecode created by my runs (cpython-312; the original cpython-313 `.pyc` remain). No hypothesis ledger, prereg/amendment, config, result or source file was edited. **Caveat:** `sha256sum -c` on the three freeze manifests gives the same results on the pristine unzip and on my tree (v0.5: 31 OK, 25 FAILED, 25 files absent; v0.6 draft: 86 OK, 26 failed incl. `tests/test_dr4_schema.py`; v0.4/base: 21 OK, 27 failed). So the packaged project already does not fully match its manifests (many listed files are absent from the zip; a few mismatch), independently of my work — worth resolving before freezing. The new files are not in any manifest.
5. **Imports/usability.** All four modules import and their public entry points were called (offline smoke, `h6_from_scores`, `adapt`, `compare_correlated_vs_diagonal`, `null_calibration`); both CLIs run (`h6_runner.py --selftest` exit 0; `gaia_live_smoke.py` exit 1 on DNS failure, exit 2 on bad argument). Not exercised: the real `requests` success path against the live server, the H6 training path on real mocks, `read_isochrone_table` on real PARSEC/MIST files, `adapt` on real DR4 data.
6. **Synthetic vs real labelling.** Result files: `h6_selftest_SYNTHETIC.json` carries `DATA: SYNTHETIC SELFTEST - NOT A SCIENTIFIC RESULT`; both null-calibration files carry `data: SYNTHETIC NULL (pure noise)`; the live report is a real attempt and says FAIL. Two labelling defects found and fixed: the live report had `live_data: true` even when it failed (now `live_attempt`, false when offline), and `compare_correlated_vs_diagonal` labelled its output "SYNTHETIC unless stated otherwise" (now states provenance is not determined by the function). Stub-transport tests prove parsing logic only. No Gaia (DR3 or DR4) data were used anywhere, so there is no DR3-as-DR4 claim.

## Synthetic null calibration (pure noise; seed 20261101; n_boot = 2000 per dataset)
| Rule | n_rep (null datasets) | rejection @0.05 [Wilson 95%] | rejection @0.025 [Wilson 95%] | KS vs U(0,1) |
|---|---|---|---|---|
| AUC, 39 vs 26 | 500 | 0.062 [0.044, 0.087] | 0.030 [0.018, 0.049] | p = 0.53 |
| ΔAUC, ρ = 0.7 | 300 | 0.057 [0.036, 0.089] | 0.020 [0.009, 0.043] | p = 0.45 |
Consistent with nominal levels, but too few datasets to exclude modest inflation. Not a completed calibration.

## Commands for the complete suite on a normal online machine
    unzip GAIA-FP-v0_6-QA2.zip && cd GAIA-FP-update
    python -m venv .venv && source .venv/bin/activate
    pip install -r requirements.txt pytest requests
    PYTHONPATH=src python -m pytest -q tests                                  # legacy 53 + new 37 = 90 expected collected (verify)
    PYTHONPATH=src python -m pytest -q audit/tests_geometry.py audit/tests_stats.py   # QA_STATUS reports 65 passed, 35 xfailed
    cd src && python gaia_live_smoke.py --timeout 30 --out ../results/qa2/live_smoke_report.json   # real live check
The 90 count is arithmetic from the test inventory, not an observed result; `requirements.txt` lists emcee, which the sandbox lacked (some legacy modules may need it).

## Remaining work
Run the commands above; supply simulator mocks for H6; fill and validate the DR4 epoch mapping on release day; choose/document isochrone assumptions; run null calibration at ≥10⁴ datasets with a stated tolerance; ingest real Thiele–Innes correlations; reconcile the pre-existing manifest mismatches; add new files to a new manifest if they are to be frozen.
