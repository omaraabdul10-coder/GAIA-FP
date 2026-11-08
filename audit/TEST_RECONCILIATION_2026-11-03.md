# Test reconciliation — 3 November 2026

Environment: Python 3.13.5, pytest 9.0.2, NumPy 2.3.5, SciPy 1.17.0, pandas 2.2.3. `astropy` is not installed. The complete repository suite was run in one process after the latest closeout changes: `pytest -q` completed with **125 passed in 23.57 s**. The per-file table below is retained as a historical breakdown; the complete 125-test result is authoritative.

| Test file | Result |
|---|---:|
| test_core.py | 7 passed |
| test_dr3_integration.py | 1 passed |
| test_dr3_study.py | 8 passed |
| test_dr4_adapters.py | 4 passed |
| test_dr4_dynamical.py | 2 passed |
| test_dr4_empirical.py | 2 passed |
| test_dr4_epoch_adapter.py | 10 passed |
| test_dr4_evaluate.py | 7 passed |
| test_dr4_h12_prepare.py | 4 passed |
| test_dr4_mechanism_guarded.py | 8 passed |
| test_dr4_schema.py | 5 passed |
| test_fetch_realdata.py | 8 passed |
| test_h6_runner.py | 10 passed |
| test_live_smoke.py | 8 passed |
| test_mechanism.py | 4 passed (includes new S1-retirement regression) |
| test_prior_select.py | 2 passed |
| test_qa_extensions.py | 6 passed |
| test_rvs_v32.py | 7 passed (includes new A6 threshold regression) |
| test_sensitivity.py | 11 passed |
| **Earlier file-by-file subtotal** | **114 passed** |

The earlier archived run collected 112 tests and the intermediate module-by-module verification reported 114 passes. The final suite now includes the additional closeout regression coverage and has been successfully executed in one process, as recorded below.


## Final full-suite verification (3 November 2026)

```text
$ pytest -q
125 passed in 23.57s
```

The 125-test full-suite result is the authoritative final code-test result. A passing test suite verifies software behavior covered by tests; it does not substitute for missing APOGEE, GALAH, LAMOST, or Gaia DR4 observations.
