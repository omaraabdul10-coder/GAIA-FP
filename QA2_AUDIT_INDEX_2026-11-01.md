# QA2 audit index — 1 November 2026

This is a supplementary audit layer over the existing GAIA-FP v0.6 / QA2 package. It does not replace the historical frozen manifest or preregistration.

## Primary documents

- `QA2_SCIENTIFIC_AUDIT_2026-11-01.md` — results of the new reproducibility, robustness and statistical calibration audits.
- `H6_RULE_RECONCILIATION_2026-11-01.md` — recovered local preregistration resolves the H6 comparison definition; no scientific code changed.
- `DR4_RELEASE_DAY_RUNBOOK_2026-11-01.md` — exact operational gates, local AZT times and no-go conditions for release day.
- `QA2_SCIENCE_AUDIT_MANIFEST_2026-11-01.sha256` — checksums for the new documents, scripts and audit outputs.

## Partial-analysis completion addendum (same date)

- `results/qa2/partial_completion/PARTIAL_ANALYSES_COMPLETION_REPORT_2026-11-01.md` — completed local SB2 cross-match reconciliation, expanded 95-object physical characterization, corrected H10 baseline reconciliation, and a real-DR3 2×2 ablation of the available astrometric/CMD likelihood and prior components (epoch-RVS ablation remains blocked by missing per-transit data).
- `GALAH_RV_EPOCH_CROSSMATCH_PROTOCOL.md` — reproducible 2,102-target GALAH epoch-RV query package and post-download summarizer. Actual external epoch rows remain un-fetched, so no epoch-RV outcomes are claimed.
- `tools/qa_audits/complete_partial_analyses.py` and `tools/qa_audits/summarize_galah_epoch_rv.py` — new local analysis and epoch-RV summarization scripts.
- `results/qa2/partial_completion/` — candidate-level cross-match CSV, 95-object characterization CSV/JSON, baseline comparison JSON, target IDs and 22 chunked ADQL queries.

This addendum supersedes any earlier “not run” status for the 10,000-outer-iteration null calibration. The calibration was completed and reported in `QA2_SCIENTIFIC_AUDIT_2026-11-01.md`. It does not supersede frozen data, historical labels, or preregistration.

## New reproducibility scripts

| Script | Purpose |
|---|---|
| `tools/qa_audits/audit_h11_control_matching.py` | Rebuild seed-11 H11 DR3 controls and quantify random-order matching balance sensitivity. |
| `tools/qa_audits/audit_h8_seed_stability.py` | Re-run the frozen 400-draw A3 label procedure on five seeds without replacing historical output. |
| `tools/qa_audits/audit_astrospectro_mc_precision.py` | Supplementary 50,000-draw-per-seed precision audit for the 95-object dynamical-label sample. |
| `tools/qa_audits/run_null_bootstrap_10k.py` | Run independent 1,000-replicate chunks for AUC and paired ΔAUC synthetic null calibration. |
| `tools/qa_audits/summarize_null_calibration_10k.py` | Combine and summarize the 10,000 outer replicates per synthetic null family. |
| `tools/qa_audits/complete_partial_analyses.py` | Reconcile the local independent SB2 matches, characterize the 95-object dynamical subset, and reconcile corrected H10 baselines. |
| `tools/qa_audits/summarize_galah_epoch_rv.py` | Summarize downloaded GALAH per-epoch RV rows without imposing an unregistered binary cutoff. |

## Reproduction commands

```bash
PYTHONPATH=src pytest -q
PYTHONPATH=src pytest -q audit/tests_geometry.py audit/tests_stats.py

python tools/qa_audits/audit_h11_control_matching.py
python tools/qa_audits/audit_h8_seed_stability.py
python tools/qa_audits/audit_astrospectro_mc_precision.py
python tools/qa_audits/summarize_null_calibration_10k.py
python tools/qa_audits/complete_partial_analyses.py
python tools/qa_audits/run_ablation_dr3.py
python tools/qa_audits/summarize_galah_epoch_rv.py --selftest
PYTHONPATH=src python -m h6_runner --selftest --out results/qa2/h6_selftest_2026-11-01.json
```

The two full pytest commands are separate suites. The H6 self-test and all null-calibration outputs are synthetic diagnostics, not real Gaia science results. The H8 50,000-draw audit is supplementary, not the registered historical output.
