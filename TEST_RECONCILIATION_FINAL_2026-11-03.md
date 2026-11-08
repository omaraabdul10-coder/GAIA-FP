# Final test reconciliation — 3 November 2026

`pytest --collect-only -q tests` collected **119 tests**. All 119 passed across per-file/per-test runs. The two slow `test_dr3_study.py` cases were completed separately after the first six tests passed; this is not a single monolithic invocation.

| Test module | Passed |
|---|---:|
| `test_core.py` | 7 |
| `test_dr3_integration.py` | 1 |
| `test_dr3_study.py` | 8 |
| `test_dr4_adapters.py` | 4 |
| `test_dr4_dynamical.py` | 2 |
| `test_dr4_empirical.py` | 2 |
| `test_dr4_epoch_adapter.py` | 10 |
| `test_dr4_evaluate.py` | 7 |
| `test_dr4_h12_prepare.py` | 4 |
| `test_dr4_mechanism_guarded.py` | 8 |
| `test_dr4_schema.py` | 5 |
| `test_fetch_realdata.py` | 8 |
| `test_h6_runner.py` | 10 |
| `test_live_smoke.py` | 8 |
| `test_mechanism.py` | 4 |
| `test_prior_select.py` | 2 |
| `test_qa_extensions.py` | 6 |
| `test_rvs_v32.py` | 7 |
| `test_sensitivity.py` | 11 |
| `test_final_epoch_rv.py` | 5 |
| **Total** | **119** |

## New tests

`test_final_epoch_rv.py` checks:
- exact Gaia DR3 ID matching and LAMOST per-source summaries;
- LAMOST science-fiber filtering when `fibertype` is present;
- APOGEE allVisit quality-bit filtering and preservation of actual MJD values;
- deterministic Keplerian RV evaluation;
- exact-cadence injection runner consumes the supplied MJD series and writes seed/trial metadata.

These tests use synthetic fixtures for code validation. They are not astronomical observations or scientific epoch-RV results.

## Execution caveat

A full `pytest -q` monolithic run timed out in the earlier pre-DR4 closeout. In this session, every test module was run separately or the remaining slow cases were run individually. Do not describe the monolithic suite as having passed in one process.
