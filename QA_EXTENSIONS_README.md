# GAIA-FP v0.6 — additional QA extension pack (2026-11-01)

This is an **unfrozen engineering add-on**, not a change to the registered scientific hypotheses or existing frozen outputs.

## Verified in this workspace

- Re-opened `GAIA-FP-v0.6-QA-47tests.zip` and executed `pytest -q`: **47 passed** (20.03 s) before adding this extension.
- Added `src/gaiafp_qa_extensions.py` and six deterministic unit tests in `tests/test_qa_extensions.py`.
- Re-ran the complete suite after the extension: **53 passed** (22.34 s).
- The extension tests exercise a synthetic time conversion, strict CCD array handling, correlated 4x4 Thiele–Innes covariance draws, rejection of a non-PSD covariance matrix, explicit multi-relation mass sensitivity, and reproducible null bootstrap calibration.

## What the extension provides

1. `epoch_astrometry_to_relative_days`: strict H4 epoch-astrometry normalizer. It requires caller-supplied exact column names and explicit time units; it does not guess unpublished DR4 column names. CCD array selection must be explicit.
2. `draw_thiele_innes`: multivariate draws from a supplied full 4x4 covariance matrix for A/B/F/G. If no covariance is supplied, it clearly flags the diagonal-independence fallback. It does not invent correlations.
3. `bootstrap_null_calibration`: Monte Carlo type-I diagnostic for the stratified percentile-bootstrap AUC test. It is a diagnostic, not a replacement for the preregistered test.
4. `mass_relation_sensitivity`: evaluates several externally supplied, documented M_G-to-mass grids without silently selecting one. No PARSEC/MIST table was bundled because the project has not specified age, metallicity, extinction and interpolation choices.
5. `h6_ml_comparison`: reusable H6 comparator with paired stratified bootstrap. The existing `dr4_evaluate.h6()` already calls the tournament ML model, but the tournament training data are external simulated catalogues under `dl/GaiaForecasts/`; if absent, H6 correctly returns NOT_CONDUCTED.

## Important items NOT completed / NOT claimed

- **Live Gaia Archive DR3 TAP/DataLink:** attempted a direct TAP request from this execution environment; DNS resolution failed (`Temporary failure in name resolution`). Therefore no live server response, query job, archive login, or DataLink product was verified. This must be run on the user's internet-connected computer. Never send the archive password in chat.
- **DR4 H4 production adapter:** final DR4 epoch-astrometry schema is not available in this workspace before release. The new adapter is a strict normalization layer, not a verified binding to final ESA field names or a validated orbital fit. Exact mappings must be set from the released DR4 DataLink table and checked on real products.
- **Mass/isochrone calibration:** not scientifically resolved. Supply chosen PARSEC/MIST isochrones and document age, [Fe/H], extinction, and main-sequence selection before freezing. Current approximate anchor relation remains exploratory.
- **Bootstrap calibration:** helper is implemented, but the null simulation must be run at sufficiently high `n_rep` and the observed type-I rate reported with Monte Carlo uncertainty before claiming calibration. It has not been used to change the preregistered p-value rule.
- **Correlated Thiele–Innes errors:** sampler supports full covariance if supplied; current project data path still needs to ingest verified covariance/correlation fields. Until then, the old diagonal-error assumption remains and must be labelled as such.

## Official interface references consulted

- Astroquery Gaia TAP+/DataLink documentation: https://docs.astropy.org/projects/astroquery/en/latest/gaia/gaia.html
- Astroquery `Gaia.load_data` retrieval types: https://docs.astropy.org/projects/astroquery/en/latest/api/astroquery.gaia.GaiaClass.html
- ESA `gaiasupdate` (epoch astrometry processing): https://esa.github.io/gaia-supdate/

## Reproduction

From the project root:

```bash
pytest -q
```

Expected in this packaged environment: **53 passed**. This verifies the included software tests only; it does not verify live archive access, unpublished DR4 schema, scientific model adequacy, or DR4 outcomes.
