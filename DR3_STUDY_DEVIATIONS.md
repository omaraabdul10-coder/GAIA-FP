# DR3 study: deviations and notes, logged in time order

`DR3_STUDY_PLAN.md` is unchanged and its hash still verifies (`DR3_STUDY_PLAN.sha256`). Every change made after hashing is recorded here, with its date and reason.

## 1. 9 Oct 2026, ~11:30 UTC+4 — bug fix in `dr4_pipeline.campbell()` (inclination)

- **Bug:** the inclination used tan(i/2) = √ratio. The correct relation is tan⁴(i/2) = ratio.
- **How it was found:** the new unit test `tests/test_core.py::test_campbell_roundtrip_a0_and_inclination`. This was **before any real data were scored**.
- **Impact on the DR3 primary metric: none.** The DR3 GAIA-FP score uses a0, P, e and the CMD (`joint_lr.llr_a0_cmd`), not the inclination. The inclination enters only the RVS prediction and the follow-up EIG, and neither is used in the DR3 study.
- **Consequence:** `src/dr4_pipeline.py` now differs from its hash in `DR3_STUDY_PLAN.sha256`. The pre-fix hash is kept there for the record.

## 2. 9 Oct 2026, ~11:05 UTC+4 — field-star sample size

The pre-registered field query (TOP 20000 … `random_index < 3000000`) returned **2541** stars, which is fewer than the TOP limit. This was observed as a **row count only**, with no candidate or label information.

The query is kept exactly as pre-registered. With 40 colour bins this gives about 63 stars per bin for the ridge and scatter estimate. The resulting uncertainty in σ_CMD is propagated in the sensitivity analysis (see `EXPERIMENT_TOURNAMENT.md` X4: σ errors of ±20% shift the contamination estimate by about ±0.03).

## 3. Data retrieval route

The analysis workspace cannot reach the Gaia archive or VizieR directly.

**First attempt (browser session, 9 Oct, ~11:00–11:15 UTC+4).** The data were retrieved in a browser:
- Gaia async job `9cea2325-c3af-11f1-826d-bc97e148b76b-O`: 2209 rows. 71 sealed rows were dropped in the browser **before** anything was stored, leaving 2138 rows.
- VizieR: LAMOST SB2 12426 rows, GALAH 12760, APOGEE SB2 8105.

The browser link dropped during the transfer, so **none of these data reached the analysis workspace and nothing was analysed**.

**Replacement route.** `tools/fetch_realdata.py` runs the identical queries on any internet-connected computer and writes `realdata/PROVENANCE.md`.

## 4. 9 Oct 2026, ~11:45 UTC+4 — LAMOST-MRS coverage matched by position, not by DR2 id

- **Problem:** VizieR serves the `Gaia` column of J/ApJS/244/27/lamostMRS as a floating-point number (for example `5.1616941445547802E17`). Gaia DR2 ids have 18–19 digits, more than a double can hold exactly, so matching by id is unreliable.
- **Fix:** coverage is now matched by **position**. The retrieved table is one row per LAMOST star (grouped by `Gaia`), with `n_epochs`, AVG(RAJ2000) and AVG(DEJ2000). The matching rule is the one already pre-registered for APOGEE:
  - Gaia positions are propagated to J2000;
  - the match radius is 2″;
  - ambiguous matches count as no coverage.
- **Epoch of the LAMOST input catalogue:** this epoch is not uniform, so both J2000 and the Gaia epoch (2016.0) are tried. A coverage match is accepted only if it is unique; if the two epochs give different stars, the match counts as ambiguous.
- **What else changed:** the full coverage table is downloaded and the filtering is done in the workspace, instead of sending an IN-list query.
- **Timing:** this was decided after seeing only the column format, before any cross-match or score was computed.
- **Code:** `dr3_study.build_labels` uses the positional path when `lamost_cov.csv` has `ra` and `dec` columns.

## 5. 9 Oct 2026, ~11:50 UTC+4 — 17 candidates without Thiele–Innes errors
- **Problem:** the first run stopped with a NaN error. 17 of the 2119 candidates have no `*_thiele_innes_error` values, so a0err is NaN. The pre-registered "drop missing or invalid inputs" filter listed a0, P, e, dm, M and d, but not a0err.
- **Fix:** a0err (> 0) and sig_cmd were added to that filter. 2102 candidates are scored.
- **Timing:** this was diagnosed from input columns only, **before any label or score was seen**.

## 6. Exploratory analyses after unblinding (NOT pre-registered)
`RESULTS_DR3.md §3` contains extra analyses done **after** the pre-registered results were seen:
- a field-star calibration check;
- a decomposition of the likelihood;
- the AUC with a flat prior.

They are labelled exploratory. They cannot replace the pre-registered P1–P3 numbers.

## 7. 9 Oct 2026, ~12:30 UTC+4 — independent AstroSpectroSB1 labels (exploratory)
- **New data:** an extra Gaia TAP query for Thiele–Innes C and H of the 95 AstroSpectroSB1 candidates. All 95 are non-sealed, because the id list was built from the already-filtered file. The data were transferred in the browser and verified by a SHA-256 of the sorted rows. The file is `realdata/dr3_astrospectro_ch.csv`.
- **Label rules** were written into `astrospectro_check.py` before any comparison with scores.
- **Bug fixed before any comparison:** degrees were passed to `np.sin`, which gave a median ρ < 0, which is impossible. The first output was discarded.
- **Results** are in `RESULTS_DR3.md` §4–5. Proposed changes for DR4 are in `PREREG_AMENDMENT_v0.4.md` (not frozen).

## 8. 9 Oct 2026, ~16:20 UTC+4: H10 field-calibration query (D2)
- **Deviation:** the pre-registered D2 query (`ORDER BY random_index`, TOP 30000) had not finished after more than 20 minutes and was aborted.
- **Replacement (D2b):** the same filters, `random_index < 100000000`, TOP 30000. This is also a random subset, because random_index is a random permutation.
- **Timing:** decided before any D2 or D3 data were seen.

## 9. 9 Oct 2026, ~17:00 UTC+4: main-sequence cut applied to the vbroad field calibration
- **Problem:** the D2b field sample has median parallax ≈ 1 mas, so it includes giants.
- **Change:** the plan's main-sequence cut for the targets (M_G > ridge − 2.0, colour within the ridge range) is applied to the calibration stars too, so that like is compared with like.
- **Timing:** decided after seeing only the field sample's summary statistics, before any vbroad of a labelled object or any score was computed.

## 10. 9 Oct 2026, ~17:35 UTC+4: D3 retrieved from the CDS VizieR mirror; m1 from the photometric relation
- **Why:** the Gaia archive repeatedly failed or stalled on D3 (one server-side quota lock error; chunked jobs still running after more than 30 minutes).
- **Source used instead:** VizieR I/357/tboasb1c (Gaia DR3 nss_two_body_orbit, AstroSpectroSB1), joined with I/355/gaiadr3 on Source. These are the same Gaia DR3 values: Thiele–Innes A, B, F, G, C, H with their errors, P, e, T_peri, ϖ, G, BP−RP, RUWE, vbroad, its error, its number of transits, and G_RVS.
- **What changed:** binary_masses is not in VizieR. m1 therefore comes from `dr4_pipeline.mass_from_MG` (the project's fixed photometric relation, applied to the blended M_G) instead of binary_masses m1.
- **Effect:** m1 enters only K_sum and the AMRF normalisation. ρ labels, the CMD score and VB do not use m1.
- **Timing:** decided before any D3 data were seen.

## 11. D3 contained one sealed source
- **What happened:** the VizieR D3 file contained 1 of the 76 sealed source_ids. VizieR has no browser-side filter, so the row was not removed at download time.
- **How it was handled:** `dark_companion.h10` drops sealed ids before any computation. The row was also deleted from the stored file `realdata/dr3_astrospectro_all.csv` (33 463 rows remain).
- **Inspection:** none of its values was inspected.

## 12. vbroad v2: TRAIN/TEST split rule
- **Problem:** the pre-registered split (source_id even/odd) is degenerate. Every Gaia source_id is even, by construction of the identifier. The first run therefore crashed with an empty TEST set, and no output was printed.
- **Replacement rule:** the parity of the sum of the source_id's decimal digits. This is deterministic and unrelated to the physics.
- **Timing:** fixed before any TRAIN or TEST result was seen.
