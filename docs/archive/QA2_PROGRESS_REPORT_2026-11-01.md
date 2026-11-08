> **Updated 1 November 2026:** this file is the earlier engineering-only snapshot. The newer scientific/robustness audit is `QA2_SCIENTIFIC_AUDIT_2026-11-01.md`; release-day operations are in `DR4_RELEASE_DAY_RUNBOOK_2026-11-01.md`. Use those newer documents for the 10,000-replicate null audits, H8 seed-sensitivity results, H11 matching sensitivity and H6 rule reconciliation.

# GAIA-FP v0.6 / QA2 — engineering progress snapshot

**Date:** 1 November 2026  
**Status:** working QA2 snapshot; not a final scientific release, not a DR4 validation, and not a new OSF registration.

## What was advanced in this pass

### 1. DR4 mechanism preflight is now fail-closed

Added `src/dr4_mechanism_guarded.py`. It refuses to start H12–H14 scoring unless the candidate-orbit table, field CMD table, field-vbroad calibration table, exact full DR3 AstroSpectroSB1 exclusion population, sealed-ID file, and explicit DR3–DR4 ID map are all present and structurally valid. It checks decimal-string source IDs, unique/one-to-one correspondences, the registered 1-arcsec match radius, the required orbit columns, and the project's own CMD/vbroad calibration machinery.

The underlying `src/dr4_mechanism.py` scientific scoring equations were not changed. The guard is an engineering safeguard, not a new scientific decision rule. It intentionally refuses to substitute the 95-row `realdata/dr3_astrospectro_ch.csv` fixture for the full exclusion catalogue.

### 2. DR4 input preparation is separated from scoring

Added `src/dr4_h12_prepare.py`. It joins the four separately downloaded input tables using exact decimal-string Gaia IDs, checks one-to-one join cardinality, preserves candidates without mean RVS measurements (with a recorded count), validates the field CMD/RVS calibration, and writes three deterministic H12–H14 input CSVs plus hashes and provenance. It makes no network calls and does not claim that any DR4 data were fetched.

### 3. Repaired two data-fetch preparation gaps

Updated `tools/fetch_realdata.py` so `lamost_cov.csv` is requested as the **full** LAMOST-MRS source-coverage table with `COUNT(*)`, `AVG(RAJ2000)`, and `AVG(DEJ2000)`, matching the existing real-data provenance and the positional matching used in `src/dr3_study.py`. The previous candidate-only `IN (...)` chunk query produced the wrong scope and omitted the positions needed by the documented fallback. The async fetcher now fails explicitly on timeout, and the downloaded table is schema/domain checked before saving; all downloaded CSVs now receive SHA-256 entries in the regenerated provenance log.

Added `tools/fetch_dr3_astrospectro.py` to reconstruct the D3 AstroSpectroSB1 input by joining VizieR `I/357/tboasb1c` with Gaia DR3 main-source table `I/355/gaiadr3`, applying the documented parallax-over-error cut, and mapping the VizieR columns into the project's expected schema. It uses a default 33,464-row guard and refuses to overwrite the target CSV if the count or required columns differ. The script has **not** been run against VizieR in this environment because outbound DNS resolution is unavailable here.

### 4. H6 rule conflict documented, not silently “fixed”

Added `H6_RULE_DISCREPANCY.md`. The current v0.6 `HYPOTHESIS_LEDGER.md` and matching `h6_runner.py` / `dr4_evaluate.py` describe the comparison as `AUC(ML) - AUC(GAIA-FP)` and mark the registered claim falsified only when the paired-bootstrap CI lies entirely above zero. Earlier project context describes a different `LCL95%(AUC_ML - AUC_Baseline) >= -0.01` rule. The comparison baseline and direction differ as well as the margin. The canonical historical `PREREGISTRATION.md` needed to resolve this is absent from this supplied QA2 snapshot. Therefore the v0.6 code and ledger were preserved; no threshold or scientific hypothesis was changed. Two synthetic unit tests cover the current v0.6 code/ledger behavior.

## Verification actually run in this workspace

| Check | Result | Interpretation |
|---|---:|---|
| Main project suite: `PYTHONPATH=src pytest -q` | **112 passed** (23.43 s) | Automated software/unit/integration tests in `tests/`; synthetic fixtures where specified. |
| Geometry/statistics audit: `PYTHONPATH=src pytest -q audit/tests_geometry.py audit/tests_stats.py` | **65 passed, 35 xfailed** (16.01 s; 14 warnings) | The xfails are expected documented edge cases; warnings arise in degenerate-input guards. This was a separate run. |
| H11 control reconstruction | **31,349 eligible pool → 2,102 matched controls** | Reproduced archived CSV byte-for-byte; SHA-256 `cd56e49a6d1ae0baccfd7b334780bee29c351fff3b0751fa803d246570d3b42d`. This is DR3 control construction, not H11 DR4 validation. |
| Live Gaia Archive smoke test | **Not completed: local DNS resolution failed** | The environment could not resolve `gea.esac.esa.int`; this does not establish an ESA-side outage. No live archive data were received. |
| LAMOST full-catalogue and D3 VizieR downloaders | **Offline contract tests pass; network retrieval not run** | Query schemas, validation and row-count guard are unit-tested; no downloaded source is fabricated. |

The main suite includes the new fail-closed mechanism and H12 preparation tests, H6 discrepancy tests, and offline fetcher-contract tests. A combined run of the main and audit suites was attempted but hit the execution time limit; the two suites above completed separately and are reported separately.

## Scientific evidence retained from archived outputs (not rerun in this pass)

The previous DR3 result files remain the archived source for the following claims; they are not represented as newly recomputed in this pass:

- `results/dr3_study.json`: historical Gaia DR3 × survey-SB2 analysis. Its primary labelled subset was underpowered; it did not establish that GAIA-FP beat the CMD-only baseline.
- `results/dark_companion.json`: historical H10 result on 33,464 D3 AstroSpectroSB1 records before sealed-ID exclusion, 33,463 after that exclusion, and 1,927 labelled systems with usable `vbroad`. The recorded CMD AUC is about 0.732 and CMD+vbroad AUC about 0.800; the paired difference is about +0.068 with 95% interval about [+0.042, +0.095].
- `results/astrospectro_check.json` and `results/astrospectro_labels.csv`: historical 95-system independent dynamical comparison. 42 systems were labelled luminous/impostor, two were dark-companion-compatible, and 51 indeterminate; GAIA-FP identified 40/42 labelled luminous systems and did not flag either of the two dark-compatible systems. The selected AstroSpectroSB1 sample is not a representative population sample.
- `results/qa2/null_calibration_auc_SYNTHETIC.json` and `null_calibration_dauc_SYNTHETIC.json`: diagnostic synthetic-null runs only (N=500 and N=300 outer null datasets respectively); they do not complete the planned 10,000-iteration outer Monte Carlo.
- `results/qa2/h6_selftest_SYNTHETIC.json`: H6 mechanics self-test on synthetic data, explicitly not a scientific performance result.

## Current hard blockers

1. `realdata/dr3_astrospectro_all.csv` is absent. The included `realdata/dr3_astrospectro_ch.csv` is only a 95-row fixture and is not a valid replacement for the full exclusion population.
2. `realdata/lamost_cov.csv` (full positional coverage catalogue) is absent. The fixed downloader is ready but cannot run here due to DNS/network restrictions.
3. The official DR3–DR4 ID map is absent.
4. The required DR4 candidate/field orbit, CMD, and mean-RVS inputs do not exist yet; the DR4 mapping remains provisional and must be checked against the actual release schema.
5. No real Gaia DR4 catalogue has been fetched or analysed.
6. The full 10,000-outer-iteration null Monte Carlo has not been run. The earlier parallel script flagged in prior QA is not accepted as a valid result because its bootstrap indexing was not used to recompute model-derived AUCs.
7. The supplied v0.6 preregistration is a draft; this work did not submit/register a new OSF record. New engineering files are not added to the frozen historical manifest.

## Reproduction commands

```bash
PYTHONPATH=src pytest -q
PYTHONPATH=src pytest -q audit/tests_geometry.py audit/tests_stats.py

# After VizieR access is available; creates the full LAMOST positional coverage file
python tools/fetch_realdata.py

# After VizieR access is available; writes only after the 33,464-row/schema guard passes
python tools/fetch_dr3_astrospectro.py --out realdata/dr3_astrospectro_all.csv

# Local DR4 inputs only; these commands do not fetch DR4 data
python src/dr4_h12_prepare.py --orbits ... --candidate-rvs ... --field-cmd ... --field-rvs ... --out prepared_dr4_h12
python src/dr4_mechanism_guarded.py prepared_dr4_h12/dr4_new_orbits.csv prepared_dr4_h12/dr4_field_cmd.csv prepared_dr4_h12/dr4_field_vbroad.csv --idmap dr3_dr4_idmap.csv
```

**Bottom line:** GAIA-FP has been advanced at the engineering/reproducibility layer, with 112 main tests and the separate geometry/statistics audit passing as recorded. The critical scientific claims were not inflated: the DR3 results are archived evidence, the H11 control build is reproduced, and DR4 confirmatory validation remains blocked by missing data/schema and unavailable network access in this environment.
