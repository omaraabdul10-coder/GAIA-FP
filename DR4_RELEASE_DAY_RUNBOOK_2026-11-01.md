# GAIA-FP — Gaia DR4 release runbook

**Prepared:** 1 November 2026  
**Purpose:** operational checklist only; this is not evidence of DR4 validation.  
**Time zone:** all local times below are Azerbaijan Time (AZT, UTC+4).

## Official schedule

ESA's published schedule states that Gaia DR4 and the archive reopening are planned for **2 December 2026 at 12:00 CET = 15:00 AZT**. The Gaia Archive downtime is scheduled to start **25 November 2026 at 12:00 CET = 15:00 AZT**. Treat these as published schedule times and re-check ESA on the day in case of operational changes.

## A. Before archive downtime — by 25 November, 15:00 AZT

1. Preserve the current working package and supplemental SHA-256 manifest. Do not rewrite the historical v0.6 freeze manifest.
2. Run the two separate local test suites and archive their full stdout:

   ```bash
   PYTHONPATH=src pytest -q
   PYTHONPATH=src pytest -q audit/tests_geometry.py audit/tests_stats.py
   ```

3. From a machine with Gaia Archive network access, run the live DR3 smoke test. A PASS means only that the endpoint answered in the expected format; it is not DR4 schema validation:

   ```bash
   PYTHONPATH=src python src/gaia_live_smoke.py \
     --release gaiadr3 --timeout 60 \
     --out results/qa2/live_smoke_pre_DR4.json
   ```

4. Test the real-data fetcher in DR3 mode with the registered Gaia account and archive every ADQL query, job ID, row count, returned column/unit list, provenance JSON and SHA-256:

   ```bash
   PYTHONPATH=src python src/dr4_fetch.py \
     --release gaiadr3 --out results/preflight_dr3 \
     --user YOUR_GAIA_ARCHIVE_LOGIN
   ```

5. Retrieve the exact external DR3 sources still absent from this supplied workspace:

   ```bash
   PYTHONPATH=src python tools/fetch_dr3_astrospectro.py \
     --out realdata/dr3_astrospectro_all.csv
   python tools/fetch_realdata.py
   ```

   The first fetch must satisfy its exact row-count and column guard before writing. The LAMOST file must be the full positional coverage catalogue, not a candidate-only subset. Preserve the original downloads and their source URLs/versions.

6. Rebuild and verify H11 controls from the recovered source file. Confirm the registered seed-11 reproduction, one-to-one cardinality, no overlap with candidates/sealed IDs, covariate balance and mass-proxy assumptions. The existing `h11_controls.csv` is a DR3 preparation artifact, not a DR4 outcome.
7. Verify the H11 control selection uses the same source columns/units as the registered plan. If the mass proxy cannot be validated, mark H11 control construction `NOT_CONDUCTED` rather than treating the proxy as a measured dynamical mass.
8. Freeze code, inputs, provenance and the supplement manifest before the release. The public OSF registration text must be checked against the recovered local preregistration. A mismatch requires a dated deviation, never an outcome-driven correction.

## B. Archive downtime — 25 November, 15:00 AZT to 2 December, 15:00 AZT

- No Gaia Archive fetch is expected during the scheduled downtime.
- Do not simulate real catalogue results, infer missing rows or fill schema gaps with synthetic data.
- Complete local documentation, deterministic tests and the blind-analysis checklist.
- Keep the sealed labelled-set IDs and DR4 outcome labels inaccessible to the scoring stage until the frozen prediction catalogue has been hashed.

## C. DR4 release day — from 2 December, 15:00 AZT

### Gate 1: prove the live archive and schema

1. Re-run the live smoke test with `--release gaiadr4` and archive the TAP and DataLink stages separately.
2. Query `TAP_SCHEMA.tables` and `TAP_SCHEMA.columns` for every table actually required by the frozen analyses. Save the raw metadata output and units.
3. Verify the observed `ref_epoch` against the expected DR4 reference epoch, and verify all units/time representations against the published DR4 data model.
4. Check DataLink product types from the live service. Do not rely on a hard-coded retrieval-type name. Record the DataLink `data_structure` tag returned by the service; recent archive notices changed DataLink tags, so use the tag documented for the live endpoint.
5. **Hard stop:** if a required table, column, unit, time definition, ID cross-match or DataLink product is absent or ambiguous, record `NOT_CONDUCTED: SCHEMA_MISMATCH` and do not score any hypothesis that depends on it. Do not silently rename or substitute fields.

### Gate 2: retrieve and preserve frozen inputs

1. Fetch only the candidate IDs and required calibration/control fields, in bounded chunks. Preserve source IDs as decimal strings to avoid 64-bit precision loss.
2. Fetch all distinct data products required by the H12–H14 input contract: combined orbit inputs, candidate RVS measurements, field CMD calibration, field mean-`vbroad` calibration, sealed IDs and the official DR3–DR4 neighbourhood cross-match (or the exact preregistered positional fallback if the official product is unavailable and the fallback is validly registered).
3. Hash every raw table before transformations. Store query text, job ID, row count, units, archive timestamp, client versions and SHA-256 in a new immutable run directory.
4. Make a blind prediction output from the frozen DR3 scores, hash it, and only then perform any DR4 outcome joins/unblinding.

### Gate 3: run only after the previous gates pass

1. H4: build the epoch mapping from the released schema and its units; run `src/dr4_epoch_adapter.py` only with a completed, non-placeholder mapping. Report per-source dropped observations and quality-control counts.
2. H1–H3, H5–H8: execute only the endpoints whose exact prerequisites and labels are available. Record all `NOT_CONDUCTED` reasons before examining outcome values.
3. H11: map DR3 IDs to DR4 IDs using the official neighbourhood relation or preregistered fallback; enforce the 1-arcsec matching rule; exclude sealed IDs; compute O1–O5 and labels from the registered definitions. Run candidates and matched controls through identical logic.
4. H12–H14: prepare the separate inputs with `src/dr4_h12_prepare.py`, inspect the emitted provenance and hashes, then call the fail-closed runner:

   ```bash
   PYTHONPATH=src python src/dr4_mechanism_guarded.py \
     prepared_dr4_h12/dr4_new_orbits.csv \
     prepared_dr4_h12/dr4_field_cmd.csv \
     prepared_dr4_h12/dr4_field_vbroad.csv \
     --idmap dr3_dr4_idmap.csv
   ```

5. Preserve negative, null and failed results. Do not retune thresholds, priors, mass cuts, score directions or confidence levels after seeing outcomes. Any deviation must be timestamped, justified and reported separately from confirmatory results.

## D. Immediate data blockers in the current workspace

- Exact `realdata/dr3_astrospectro_all.csv` source export: absent.
- Full positional `realdata/lamost_cov.csv`: absent.
- Official DR3–DR4 neighbourhood ID map: absent.
- DR4 candidate orbit, field CMD, field `vbroad` and epoch RVS inputs: not yet available.
- Final released schema and units: not yet verified on live DR4.

**No DR4 scientific result can be claimed until those gates pass.**
