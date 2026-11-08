# C — Gaia DR4 data model and archive audit (research cut-off 2026-10-31)

Purpose: tell the release-day pipeline what Gaia DR4 tables, epoch products and archive limits will look like, what is documented, and what is not.

**Confidence levels**
- **High**: stated on a primary ESA page or in ESA-published code.
- **Med**: ESA internal or pre-release sample or code, or a consistent secondary source. It may still change at release.
- **Low**: inferred from DR3 conventions.
- **NOT DOCUMENTED**: no public source found.

## 0. Access limits of this audit

Read these before trusting the gaps below.

**Blocked sources (not read):**
- `anonftp.cosmos.esa.int` is blocked from this session. The egress proxy returns 403, and WebFetch is refused by robots.txt. As a result I could not open:
  - the **draft DR4 data model** (`gaia-dr4-prerelease-draft-data-model_2026-06-26.zip`, a single PDF covering all tables and columns);
  - the pre-release epoch-astrometry zip.
- `gea.esac.esa.int/archive/documentation/GDR4/` is robots-blocked.
- The `github.com` web UI is robots-blocked.
- `esa/gaia-jupyter-notebooks` (`data-release-4-tutorials`) was not accessed.

**What I used instead:**
- I read two ESA repos through anonymous `git clone` (read-only, code not executed):
  - `esa/gaia-supdate`. It contains internal DR4 DataLink sample files `EPOCH_ASTROMETRY-Gaia DR4_INT2 1.{ecsv,csv,xml,votplain.xml,fits}`.
  - `esa/gaia-bhthree`, branch `gaia-dr4-prerelease`. It contains a notebook with real pre-release outputs.

**Action item (highest value, about 30 minutes):** someone with normal internet access should download the draft data model zip and check this note against it. Check in particular:
- `nss_two_body_orbit`
- `rvs_epoch_parameters_single` and `rvs_epoch_parameters_double`
- `gaia_source`
- `dr3_neighbourhood`
- `epoch_astrometry`

Link: https://anonftp.cosmos.esa.int/pub/GAIA_PUBLIC_DATA/Gaia_DR4/dr4-prerelease/gaia-dr4-prerelease-draft-data-model_2026-06-26.zip

---

## Summary table

| item | what we know | source URL | confidence |
|---|---|---|---|
| Release date/time | **2 Dec 2026, about 12:00 CET**. The archive is down from 25 Nov 2026 12:00 CET and reopens 2 Dec 12:00 CET with DR4. | https://www.cosmos.esa.int/web/gaia/data-release-4 ; https://www.cosmos.esa.int/web/gaia/release ; https://www.cosmos.esa.int/web/gaia/news (2026-10-08 item) | High |
| Data span / volume | 25 Jul 2014 to 20 Jan 2020 (66 months). About 2.8e9 sources processed. `gaia_source` holds 2,000,033,276 rows. Total about 400 TB, mostly epoch data. | https://www.cosmos.esa.int/web/gaia/dr4 | High (content page says "under development", last update 14 Sep 2026) |
| Reference epoch | **J2017.5 (TCB)**. DR3 was J2016.0. The frame is ICRS aligned to Gaia-CRF4. | https://www.cosmos.esa.int/web/gaia/dr4 ; `gaiasupdate/constants.py` (`DR4_REFERENCE_EPOCH = Time('2017.5', format='jyear', scale='tcb')`) | High |
| source_id | DR4 source list must be treated as **independent** of DR1/DR2/DR3. Use `dr3_neighbourhood` (TAP, 2,448,832,159 rows, 29 GB), which can give 0, 1 or (rarely) several counterparts. | https://www.cosmos.esa.int/web/gaia/dr4 | High (table name); columns NOT DOCUMENTED |
| NSS two-body table | `nss_two_body_orbit` (TAP, DL3): 5,901,111 rows, 2.7 GB. Covers astrometric, spectroscopic and eclipsing binaries and combinations. DR3 had 443,205 rows, so about 13x more. | https://www.cosmos.esa.int/web/gaia/dr4 | High (name and count); columns NOT DOCUMENTED |
| New NSS tables | `rvs_two_body_orbit` (638,966 rows; SB solutions from the LIA modules using astrometric orbits and CCFs), `nss_multiple_orbits` (16,681), `nss_resolved_pair` (22.8M), `nss_multiplicity` (229M), `nss_masses` (4.32M), `nss_epoch_flags` (DataLink `EPOCH_FLAGS_NSS`, 2.68e9 rows). Also `nss_acceleration_astro` 3.37M, `nss_non_linear_spectro` 79,653, `nss_vim_fl` 3,775. | https://www.cosmos.esa.int/web/gaia/dr4 | High |
| NSS solution types in DR4 | **NOT DOCUMENTED** publicly. The DR3 list is Orbital, OrbitalAlternative[Validated], OrbitalTargetedSearch[Validated], AstroSpectroSB1, SB1, SB1C, SB2, SB2C, EclipsingBinary, EclipsingSpectro. | DR3: https://gea.esac.esa.int/archive/documentation/GDR3/Gaia_archive/chap_datamodel/sec_dm_non--single_stars_tables/ssec_dm_nss_two_body_orbit.html | Low for DR4 |
| Thiele–Innes units (DR3 baseline) | A, B, F, G in **mas**; C, H in **AU** (AstroSpectroSB1 only). Period in **day**. `t_periastron` in **day relative to `gaia_source.ref_epoch`**. | DR3 data model page above | High for DR3; Low for DR4, where t_periastron is presumably relative to J2017.5 |
| Epoch astrometry | `epoch_astrometry` (DataLink `EPOCH_ASTROMETRY`, DL2): 129,625,750,708 rows, 62 TB. A row is one FoV transit with **10-element per-CCD arrays (index 0 = SM, 1–9 = AF1–AF9)**. Times are int64 **ns TCB since 2010-01-01T00:00:00**, with the barycentric correction in a separate column (ns). | https://www.cosmos.esa.int/web/gaia/dr4 ; gaia-supdate samples and code ; gaia-bhthree notebook | High (product); Med (columns) |
| Epoch RV / line broadening per transit | **Yes.** `rvs_epoch_parameters_single` (6,910,423,894 rows, 323 GB) and `rvs_epoch_parameters_double` (787,312 rows, 128 MB). Both give **per-FoV-transit RV, line broadening and Grvs**, the double table for double-lined transits. DataLink types `EPOCH_PARAMETERS_RVS_SINGLE` / `EPOCH_PARAMETERS_RVS_DOUBLE`. | https://www.cosmos.esa.int/web/gaia/dr4 ; astroquery PR #3371 | High (existence); column names NOT DOCUMENTED |
| RVS epoch spectra | `rvs_epoch_spectrum` (DataLink `EPOCH_SPECTRUM_RVS`): 6,910,785,949 rows, 49 TB. Normalised, combined per FoV transit, in the solar barycentric frame. `rvs_mean_spectrum` (`MEAN_SPECTRUM_RVS`): 250M rows, 1.8 TB. | https://www.cosmos.esa.int/web/gaia/dr4 | High |
| Mean RVS parameters | `all_source_rvs` (TAP, 312,247,580 rows, 28 GB): RV, line broadening and Grvs. Plus `vari_rad_vel_statistics` (15.2M rows) and `rvs_transit_description` (TAP, CCD-level, 9.0e9 rows). | https://www.cosmos.esa.int/web/gaia/dr4 | High |
| gaia_source columns | Parameters are now **consolidated across modules**: "the best-suited model has been applied … e.g. a binary-star model instead of the default single-star model". Column list NOT DOCUMENTED; it is in the draft data model I could not read. | https://www.cosmos.esa.int/web/gaia/dr4 | High (consolidation); NOT DOCUMENTED (columns) |
| TAP quotas | Sync timeout 60 s (all users). Async timeout 1 min anonymous / 120 min registered. Max rows 50,000 anonymous / unlimited registered. Active jobs: 5 per registered user; anonymous users share a pool of 100. Queue 50. Job retention 24 h anonymous / unlimited. Persistent job output 20 GB. User tables 1 GB. | https://www.cosmos.esa.int/web/gaia-users/archive/collaborate#GaiaArchiveUserQuotas ; https://www.cosmos.esa.int/web/gaia/news (2026-10-14) | High |
| DataLink limits | **50 sources per request anonymous, 5,000 registered.** Formats: votable (default), votable_plain, csv, ecsv, json, fits. Responses are gzip by default. | quotas page above ; https://www.cosmos.esa.int/web/gaia-users/archive/datalink-products ; astroquery `load_data` docstring | High |
| DataLink structure rename | **14 Oct 2026 (archive v3.15), breaking:** `INDIVIDUAL` became `DATAMODEL_STANDARD` (one file per source) and `RAW` became `DATAMODEL_GAIA` (DPAC model). `COMBINED` has been deprecated since v3.6 (Dec 2024). | https://www.cosmos.esa.int/web/gaia-users/archive/release-notes ; https://www.cosmos.esa.int/web/gaia/news | High |
| astroquery | **Stable 0.4.11 (20 Sep 2025) still defaults to `data_structure='INDIVIDUAL'`** and accepts only INDIVIDUAL/RAW. The dev 0.4.12 line (latest 0.4.12.dev11095, 9 Oct 2026) uses DATAMODEL_STANDARD/DATAMODEL_GAIA. | https://docs.astropy.org/projects/astroquery/en/stable/_modules/astroquery/gaia/core.html ; https://docs.astropy.org/projects/astroquery/en/latest/_modules/astroquery/gaia/core.html ; https://pypi.org/project/astroquery/#history | High |
| Number of sources with epoch RVs | NOT DOCUMENTED as a source count. Epoch RVs are "baselined … for all objects with grvs_mag ≤ 14". A NAM 2025 talk quotes "650 million reliable epoch RVs (1.3 billion total)". The upper bound is 312M sources (`all_source_rvs`). | https://www.cosmos.esa.int/web/gaia/science-performance ; https://conference.astro.dur.ac.uk/event/7/contributions/327/attachments/351/628/gaia-status-nam25-jul25.pdf | Low–Med |
| Release-day load | NOT DOCUMENTED. Archive moved from Greenplum to EDB WarehousePG (v3.15). Partner centres (CDS, ASDC, ARI, AIP, Flatiron) serve "the data (or a subset thereof)", with no day-1 timing given. No DR4 bulk/CDN download announced. | release notes ; https://www.cosmos.esa.int/web/gaia/dr4 | — |

---

## 1. Release date and DR4 contents

**Release date.** The release is set for 2 December 2026 at about 12:00 CET (High).
- The overview page says "Coming up: 2 December 2026 at ~12:00 CET": https://www.cosmos.esa.int/web/gaia/data-release-4
- The release page lists "Gaia DR4 (based on 66 months of data) 2 December 2026": https://www.cosmos.esa.int/web/gaia/release
- Gaia Bulletin #10 confirms 2 Dec 12:00 CET: https://www.cosmos.esa.int/web/gaia/bulletin-archive
- ESA warns that final contents "will be decided only after validation".

**Contents overview** (https://www.cosmos.esa.int/web/gaia/dr4, "Last update: 14 September 2026", "under development and changes can be expected"):
- **Catalogue (TAP, DL3):**

  | Table | Rows | Size |
  |---|---|---|
  | `gaia_source` | 2,000,033,276 | 586 GB |
  | `all_source_astrometry` | 2,793,009,568 | 610 GB |
  | `all_source_photometry` | 2,793,009,568 | 755 GB |
  | `all_source_flags` | 2,793,009,568 | 44 GB |
  | `all_source_rvs` | 312,247,580 | 28 GB |

  Other catalogue tables include `spurious_signal`, `crowded_field_source`, `gaia_source_environment`, `optical_pair`, `sso_source`, `gaia_crf4` and `dr3_neighbourhood`.
- **Epoch data (DataLink, DL2):**

  | Product | Rows | Size |
  |---|---|---|
  | `epoch_astrometry` | 1.296e11 | 62 TB |
  | `epoch_photometry` (G/BP/RP per FoV transit) | 1.218e11 | 7.2 TB |
  | `epoch_photometry_ccd` | — | 23 TB |
  | `epoch_image` | — | 113 TB |
  | `xp_epoch_spectrum` | — | 119 TB |
  | `rvs_epoch_spectrum` | — | 49 TB |
  | `rvs_epoch_parameters_single` | — | 323 GB |
  | `rvs_epoch_parameters_double` | — | 128 MB |
  | `nss_epoch_flags` | — | 20 GB |

  Crowded-field and bright-star epoch astrometry are also included. Some epoch-level tables are TAP-accessible: `rvs_transit_description`, `onboard_detection_*` and `sso_observation`.
- **Spectra:**
  - `rvs_mean_spectrum`: 250M rows
  - `xp_continuous_mean_spectrum`: 1.82e9 rows
  - `rvs_epoch_spectrum`, `xp_epoch_spectrum`
- Software published so far is `gaiasupdate` (https://www.cosmos.esa.int/web/gaia/gaia-source-update, https://github.com/esa/gaia-supdate, docs https://esa.github.io/gaia-supdate/) and the BH3 notebook (https://github.com/esa/gaia-bhthree/tree/gaia-dr4-prerelease). "All other tools will be published along with the Gaia Data Release 4 data on the release day" (https://www.cosmos.esa.int/web/gaia/dr4-software-tools).
- **Pre-release (June 2026):** epoch astrometry for 12 sources, file dated 2026-06-26, plus the draft data model.
  - The 12 sources include HD 114762, Gaia-4 and Gaia BH3 (with DR4 source_ids). There are **no** RVS or NSS sample data.
  - Pre-release page: https://www.cosmos.esa.int/web/gaia/dr4-prerelease

### 1a. NSS two-body orbit table

**Documented for DR4** (High):
- **Name:** `nss_two_body_orbit`, unchanged from DR3.
- **Size:** 5,901,111 rows, 2.7 GB, TAP, DL3.
- **Coverage:** "orbital solution parameters for sources compatible with a two-body solution", including astrometric, spectroscopic and eclipsing binaries and some combinations.
- **Related tables:**
  - **`rvs_two_body_orbit`** (638,966 rows; "spectroscopic binary solutions from the LIA modules, using astrometric orbits and cross-correlation functions"). Some RV-based orbits for astrometric binaries therefore live **outside** `nss_two_body_orbit`.
  - `nss_multiple_orbits` (more than two bodies)
  - `nss_masses` (masses from NSS orbits; "NEW in Archive")
  - `nss_epoch_flags`: which epochs were used by NSS, via DataLink `EPOCH_FLAGS_NSS`.

**NOT DOCUMENTED publicly:**
- the DR4 column list, units and `nss_solution_type` values;
- any change to `t_periastron` reference or `bit_index`/`corr_vec` layout.

**DR4 papers announced but not yet public** (https://www.cosmos.esa.int/web/gaia/dr4-papers):
- "Astrometric binaries"
- "Astrometric orbit determination for exoplanet discovery"
- "Exoplanet orbit processing with radial velocity constraints" (hints at a combined astrometry+RV solution family, possibly new solution types)
- "Spectroscopic characterisation of astrometric binaries by line integral analysis of Gaia RVS spectra" (the LIA modules, so `rvs_two_body_orbit`)
- "Measuring and validating radial velocities of RVS double lined spectra and the related SB2 orbital solutions"
- "Spectroscopic multiple star processing"

**DR3 baseline the adapter must at least support** (High for DR3; source https://gea.esac.esa.int/archive/documentation/GDR3/Gaia_archive/chap_datamodel/sec_dm_non--single_stars_tables/ssec_dm_nss_two_body_orbit.html):

*Columns:*
- `solution_id, source_id, nss_solution_type`
- `ra, dec` [deg]; `ra_error, dec_error` [mas]
- `parallax` [mas]; `pmra, pmdec` [mas/yr]
- `a/b/f/g_thiele_innes` [**mas**]; `c/h_thiele_innes` [**AU**, AstroSpectroSB1 only; C = a1 sin ω sin i, H = a1 cos ω sin i]
- `period` [day]
- `t_periastron` [day, **"relative to gaia_source.ref_epoch"**, range ±P/2]
- `eccentricity`; `center_of_mass_velocity`, `semi_amplitude_primary/secondary` [km/s]
- `mass_ratio`, `fill_factor_primary/secondary`, `inclination` [deg, EB only], `arg_periastron` [deg]
- `temperature_ratio(_error, _definition)`
- `astrometric_n_obs_al`, `astrometric_n_good_obs_al`, `rv_n_obs_primary/secondary`, `rv_n_good_obs_*`, `phot_g_n_obs`, `phot_g_n_good_obs`
- `bit_index`, `corr_vec` (float[231], upper-triangle, column-major, order set by `bit_index`)
- `obj_func`, `goodness_of_fit`, `efficiency`, `significance`, `flags` (bits 0–7 astrometric, 8–31 spectroscopic, 32 EB, 48–57 combined), `conf_spectro_period`
- `r_pole_sum`, `r_l1_point_sum`, `r_spher_sum`, `ecl_time_primary/secondary` [JD], `ecl_dur_*`, `g_luminosity_ratio`, `input_period_error`, `g_rank`, `astrometric_jitter` [mas]
- Every parameter has an `_error` column.

*`bit_index` values:*
- Orbital: 8191/8179
- SB1: 127; SB1C: 31; SB2: 255; SB2C: 63
- AstroSpectroSB1: 65535/65435

*DR3 counts:* Orbital 134,598; OrbitalAlternative* 629; OrbitalTargetedSearch* 533; AstroSpectroSB1 33,467; SB1 or SB2 186,905; EclipsingSpectro 155; EclipsingBinary 86,918. Source: Arenou et al. 2023, Table 1, https://www.aanda.org/articles/aa/full_html/2023/06/aa43782-22/T1.html.

**Expected changes vs DR3 (inference, Low):**
- `t_periastron` is most likely relative to the DR4 `ref_epoch`, J2017.5. That is a shift of 1.5 Julian yr = **547.875 d** vs DR3, then re-wrapped into ±P/2.
- New solution types are plausible: RV-constrained exoplanet orbits, SB2 from double-lined transits, multiple orbits (moved to their own table).
- Longer periods are now accessible (66-month baseline), so `corr_vec` length could change if the parameter count grows.

### 1b. Epoch astrometry

**Product** (High; https://www.cosmos.esa.int/web/gaia/dr4 ; https://www.cosmos.esa.int/web/gaia/gaia-source-update):
- `epoch_astrometry`, DataLink retrieval type **`EPOCH_ASTROMETRY`**.
- Variants: `EPOCH_ASTROMETRY_CROWDED_FIELD` and `EPOCH_ASTROMETRY_BRIGHT`.
- ESA says it reproduces the DR4 core (AGIS) astrometric solution with negligible deviations for most sources.

**Structure** (Med: ESA internal DR4 sample "Gaia DR4_INT2" and pre-release outputs):
- One row per **FoV transit**.
- CCD-level fields are **arrays of length 10**: index 0 = SM, 1–9 = AF1–AF9. `gaiasupdate` explodes them into one row per CCD with a derived `component_index` column; `filter_out_skymapper` drops `component_index == 0`.
- The pre-release file is named `GAIA_DR4_PRERELEASE_EPOCH_ASTROMETRY_RAW.xml`, i.e. RAW (now DATAMODEL_GAIA) serialisation, VOTable, all 12 sources in one file.
- BH3 has 770 CCD records (77 transits), of which 558 have `used_by_agis_al == True`.

**Columns** (35 native columns in pre-release, as listed by the BH3 notebook `ea.epoch_data.info()`):
- `solution_id, source_id, transit_id, ra0, dec0, agis_source_excess_noise`
- `obs_time_tcb, obs_time_bary_corr`
- `scan_pos_angle, zeta`
- `parallax_factor_al, parallax_factor_ac, colour_factor_al, colour_factor_ac`
- `nu_eff_used_in_astrometry, nu_eff_error`
- `centroid_pos_al, calculated_pos_ac, centroid_pos_error_al`
- `used_by_agis_al, used_by_agis_ac`
- `transit_acq_flags, transit_proc_flags, ccd_proc_flags`
- `multipeak, blended`
- `ipd_error_al, ipd_error_ac`
- `g_mag, g_class, gates, source_dist_to_last_ci, ac_rate, sub_pixel_coord, mu`

The exogaia tutorial reports a raw shape of (1008, 37), so the final file may carry 1–2 more columns (https://exogaia.readthedocs.io/en/latest/tutorials/dr4_pre-release.html).

**Units and types from the DR4_INT2 DataLink sample** (ECSV/VOTable headers):

| Column | Unit | Type |
|---|---|---|
| `obs_time_tcb` | **ns** | int64 array; ns TCB since 2010-01-01T00:00:00 |
| `obs_time_bary_corr` | ns | float32 scalar |
| `centroid_pos_al` | mas | float64 array; "local plane coordinate (w) of image centroid AL", relative to `ra0, dec0` |
| `centroid_pos_error_al` | mas | float32 array |
| `scan_pos_angle` | deg | float64 array |
| `parallax_factor_al` | — | float32 scalar per transit |
| `colour_factor_al` | — | float32 scalar per transit |
| `used_by_agis_al/ac` | — | bool arrays; VOTable `bit` |
| `agis_source_excess_noise` | mas | float32 |
| `ccd_proc_flags` | — | int16 array |
| `ipd_error_al` | mas | float32 array |
| `nu_eff_used_in_astrometry` | **nm⁻¹** | float32; value 0.0016 means 1.6 µm⁻¹. DR3 `gaia_source` used µm⁻¹. |

Time relative to J2017.5 per gaiasupdate: `t_yr = 2010-01-01T00:00 TCB (jyear) + (obs_time_tcb + obs_time_bary_corr)·1e-9/yr − 2017.5`.

**Retrieval:**
```python
Gaia.load_data(ids=[...], data_release='Gaia DR4', retrieval_type='EPOCH_ASTROMETRY',
               data_structure='DATAMODEL_GAIA' | 'DATAMODEL_STANDARD', format='votable'|'ecsv'|'csv'|'fits'|...)
```
- The return value is a dict `{filename: [Table|VOTable]}`.
- `gaiasupdate` keys files as `f"{retrieval_type}-{data_release} {source_id}.xml"`.
- Archive v3.15 says file naming for DATAMODEL_GAIA was "improved", so **do not hard-code file names**.
- The `data_release` string 'Gaia DR4' is inferred. ESA code uses internal tags ('Gaia DR4_INT2', 'Gaia DR4_INT4').

**NOT DOCUMENTED:**
- whether DATAMODEL_STANDARD epoch astrometry is exploded per CCD or kept as arrays. gaiasupdate handles both via `check_if_is_exploded`;
- the units of `zeta`, `calculated_pos_ac`, `mu` and `sub_pixel_coord`.

### 1c. Epoch radial velocities, per-transit line broadening, RVS epoch spectra

**Documented** (High; https://www.cosmos.esa.int/web/gaia/dr4 rows 17.01–17.06, 02.05, 18.14):
- **`rvs_epoch_parameters_single`** (DataLink **`EPOCH_PARAMETERS_RVS_SINGLE`**): per-FoV-transit **radial velocity, spectral line broadening and Grvs magnitude** for single-lined transits. 6,910,423,894 rows, 323 GB.
- **`rvs_epoch_parameters_double`** (DataLink **`EPOCH_PARAMETERS_RVS_DOUBLE`**): the same quantities for **double-lined (SB2) transits**. 787,312 rows, 128 MB. SB2 transit RVs **are** published.
- **`rvs_epoch_spectrum`** (DataLink **`EPOCH_SPECTRUM_RVS`**): normalised RVS spectra per FoV transit, solar-barycentric frame. 6.91e9 rows, 49 TB.
- **`rvs_mean_spectrum`** (DataLink **`MEAN_SPECTRUM_RVS`**; DR3's retrieval type was `RVS`). Rest frame, 250M rows.
- **`rvs_transit_description`** (TAP): CCD-level information for RVS transits, 9.0e9 rows.
- **Mean values:** `all_source_rvs` (TAP) holds "radial velocities, spectral line broadening, and Grvs magnitudes"; `vari_rad_vel_statistics` (TAP) holds statistics of the RV time series.
- **So vbroad is published per transit** (as "line broadening" in the epoch-parameter tables) **and as a mean** (`all_source_rvs`, and presumably `gaia_source`). The content page never uses the string "vbroad".
- Epoch RVs are "baselined to be published in Gaia DR4 for all objects with GRVS ≤ 14 mag" (https://www.cosmos.esa.int/web/gaia/science-performance).

**NOT DOCUMENTED:**
- column names, time column and units;
- whether there is an outlier/rejection flag (an ML outlier-filtering paper is announced);
- whether rows exist for transits without an RV (6.9e9 rows vs "1.3 billion" epoch RVs suggests many rows carry only Grvs or null RV);
- the SB2 component naming (`_primary/_secondary` vs `_1/_2`);
- whether DR3-style RV corrections (e.g. the Katz et al. 2023 grvs ≥ 11 correction) are already applied.

**Related papers** (not public): "Epoch RVS spectra and radial velocities", "Validation of the line broadening parameters", "Statistical parameters for radial velocity, line broadening and RVS magnitude time series", "Deblending the RVS spectra".

### 1d. gaia_source changes

**Documented** (High; https://www.cosmos.esa.int/web/gaia/dr4 ; Bulletin #10):
- `gaia_source` is a **high-quality subset (2.0e9 of 2.79e9)** of processed sources. All processed sources are in `all_source_astrometry/_photometry/_rvs/_flags`.
- Parameters are **"consolidated from several different processing modules … the best-suited model has been applied for a given source (e.g. a binary-star model instead of the default single-star model as was the case in Gaia DR3)"**.
- `ref_epoch` = 2017.5.

**NOT DOCUMENTED:** the column list, and whether there is an indicator column saying which model or module supplied the astrometry. Status of each column the pipeline uses:

| Column | DR3 definition (https://gea.esac.esa.int/archive/documentation/GDR3/Gaia_archive/chap_datamodel/sec_dm_main_source_catalogue/ssec_dm_gaia_source.html) | DR4 expectation | Conf. |
|---|---|---|---|
| `parallax` | mas at ref_epoch | Name likely kept. **Value may come from a binary/NSS model for some sources.** | Low |
| `ruwe` | χ²-based, renormalised by f(G, BP−RP); null for 2-p solutions | Name likely kept. Semantics under consolidation unknown: single-star AGIS residuals or chosen model? Renormalisation function re-derived for DR4. | Low |
| `phot_g_mean_mag`, `bp_rp` | Vega mag | Names likely kept. New calibration: DR3 corrections (e.g. 6-p G correction) must not be reused. | Low |
| `grvs_mag` | Median of epoch GRVS, ≤ 14.1 mag, about 32M sources | Likely kept. Possibly fainter coverage (`all_source_rvs` has 312M rows). | Low |
| `vbroad`, `vbroad_error`, `vbroad_nb_transits` | Rotational-kernel broadening; error = std of epoch vbroad; DR3 restricted to bright sources | Likely kept. Mean also in `all_source_rvs`, per transit in `rvs_epoch_parameters_*`. | Low |
| `random_index` | Random permutation of 0…N−1 | If kept, N ≈ 2.0e9 for gaia_source. Fraction cuts must be recomputed. | Low |
| `non_single_star` | 3-bit flag (astrometric/spectroscopic/eclipsing) | May gain bits or new meaning, given new NSS tables (resolved pairs, multiple orbits). | Low |

---

## 2. Gaia archive practicalities

### User quotas

Source, verbatim: https://www.cosmos.esa.int/web/gaia-users/archive/collaborate#GaiaArchiveUserQuotas. Limits were updated in archive v3.15 (14 Oct 2026; https://www.cosmos.esa.int/web/gaia/news).

| Item | Anonymous | Authenticated |
|---|---|---|
| Synchronous query time-out | 60 s | 60 s |
| Asynchronous query time-out | 1 min | 120 min |
| Max queued queries | 50 (shared anonymous pool) | 50 |
| Max active queries | 100 (shared anonymous pool) | **5** |
| Max rows per query | 50,000 | unlimited |
| **Max sources per DataLink request** | **50** | **5,000** |
| Job retention | 24 h | unlimited |
| Persistent job output | N/A | 20 GB |
| User tables | N/A | 1 GB |

Jobs submitted beyond the 50-job queue are **rejected**, not delayed. Self-registration: https://www.cosmos.esa.int/web/gaia-users/register. Temporary quota increases can be requested through the Helpdesk: https://www.cosmos.esa.int/web/gaia/gaia-helpdesk

### DataLink
- **Structures:**
  - `DATAMODEL_STANDARD`: one file per source; DR3 analogue: INDIVIDUAL epoch photometry, one row per transit and band.
  - `DATAMODEL_GAIA`: DPAC/MDB-like, many sources per file, array cells.
  - `COMBINED`: gone.
- **Formats:** `votable` (default, binary), `votable_plain`, `csv`, `ecsv`, `json`, `fits`. Downloads are gzip by default. Preparing large requests "can take several minutes".
- **Links endpoint:** `https://gea.esac.esa.int/data-server/datalink/links?ID=Gaia+DR3+<id>` (DR4 form presumably `Gaia+DR4+<id>`).
- **Empty products:** since v3.15 "DataLink no longer retrieves empty data products", so a missing file is normal for sources without that product.
- **Large samples:** ESA notebooks `tutorial_datalink_large_samples.ipynb`; https://www.cosmos.esa.int/web/gaia-users/archive/datalink-products

**DR4 retrieval types** (astroquery latest `load_data` docstring):
`EPOCH_PHOTOMETRY, MEAN_SPECTRUM_RVS, MCMC_GSP_PHOT, EPOCH_ASTROMETRY, EPOCH_SPECTRUM_RVS, EPOCH_ASTROMETRY_CROWDED_FIELD, EPOCH_PHOTOMETRY_CROWDED_FIELD, EPOCH_IMAGE, EPOCH_PHOTOMETRY_CCD, EPOCH_SPECTRUM_XP_SSO, EPOCH_SPECTRUM_XP_CROWDING, MEAN_SPECTRUM_XP, EPOCH_SPECTRUM_XP, CROWDED_FIELD_IMAGE, EPOCH_ASTROMETRY_BRIGHT, MEAN_SPECTRUM_XP_GRAVLENS, EPOCH_FLAGS_NSS, EPOCH_PARAMETERS_RVS_SINGLE, EPOCH_PARAMETERS_RVS_DOUBLE, EPOCH_FLAGS_VARI, RESIDUAL_IMAGE`

These names have already changed once: PR #3371 (Jul 2025) had `XP_MEAN_SPECTRUM_GRAVLENS`, and `RESIDUAL_IMAGE` is not in 0.4.11. Sources:
- https://docs.astropy.org/projects/astroquery/en/latest/_modules/astroquery/gaia/core.html
- https://github.com/astropy/astroquery/pull/3371

### astroquery.gaia
- `load_data(ids, *, data_release=None, data_structure='DATAMODEL_STANDARD', retrieval_type='ALL', linking_parameter='SOURCE_ID'|'TRANSIT_ID'|'IMAGE_ID', valid_data=False, avoid_datatype_check=False, format='votable', dump_to_file=False, overwrite_output_file=False, verbose=False, output_file=None)` (dev docs).
- It returns `{file_name: [astropy Table / VOTable]}`.
- **Stable 0.4.11 has default `data_structure='INDIVIDUAL'` and accepts only INDIVIDUAL/RAW.** The archive renamed these on 14 Oct 2026. The archive release notes tell users to update astroquery. No stable release with the new names exists as of 31 Oct 2026; only 0.4.12.dev builds, the latest being dev11095 of 9 Oct 2026 (https://pypi.org/project/astroquery/#history).
- Set `Gaia.ROW_LIMIT = -1`, `Gaia.MAIN_GAIA_TABLE` explicitly, and `Gaia.login()` for registered quotas.
- ESA's `gaiasupdate.from_gacs_datalink` defaults to `data_structure='RAW'`. It will need the new name too.

### Release-day load and access
- **Expected load:** NOT DOCUMENTED. The archive is offline from 25 Nov 12:00 CET until the release at 2 Dec 12:00 CET.
- **Infrastructure:** the database migrated to EDB WarehousePG in v3.15. New UDFs: `gaia_healpix_index`, `ivo_healpix_index`, `ivo_healpix_center`.
- **Anonymous users** share 100 active and 50 queued jobs in total, so expect anonymous failures on day 1. **Register beforehand.**
- **Partner centres** (CDS, ASDC, ARI/GAVO, AIP, Flatiron) will serve all or part of the data; day-1 availability is not stated.
- **Bulk CDN:** `http://cdn.gea.esac.esa.int/Gaia/` serves DR1–DR3 as (e)csv; DR4 bulk is not announced (FAQ: https://www.cosmos.esa.int/web/gaia-users/archive/faq).

### Size estimates for 1e4–1e5 sources

My arithmetic uses ESA row counts and volumes; per-source download sizes are scaled from the INT2 sample.

| Product | Mean rows per source | DB bytes/row | Est. download per bright (G≲15) source | 1e4 sources | 1e5 sources |
|---|---|---|---|---|---|
| `epoch_astrometry` | 46 FoV transits over all 2.79e9 sources; about 70–120 for well-observed sources (BH3: 77) | ~478 B (22 kB per source on average) | Sample: 79 transits × 14/~35 columns = 48 kB VOTable-binary, 58 kB FITS, 94 kB ECSV, 84 kB CSV. Full columns: **~100–150 kB binary, ~200–300 kB text** | ~1–3 GB; ~1e6 transit rows (~1e7 exploded CCD rows) | ~10–30 GB; ~1e7 transit rows (~1e8 CCD rows); ≥20 DataLink calls at 5,000 per call |
| `rvs_epoch_parameters_single` | 22 over 312M `all_source_rvs` sources; ~30–60 for GRVS ≤ 14 | ~47 B | ~5–20 kB | ~0.05–0.2 GB | ~0.5–2 GB; ~3–6e6 rows |
| `rvs_epoch_parameters_double` | rare (787k rows total) | ~160 B | small | negligible | negligible |
| `rvs_epoch_spectrum` | same transits as single | ~7.1 kB | ~0.2–0.4 MB binary; several× larger in text | ~2–4 GB | **~20–40 GB binary (100+ GB as ECSV/CSV)** |
| `nss_two_body_orbit` (TAP) | — | ~458 B | — | trivial | Whole table 5.9M rows, 2.7 GB; fine as an async job for registered users within the 120-min timeout |

---

## 3. Expected sizes (NSS and epoch RV)

- **`nss_two_body_orbit`:** **5,901,111 rows** (High; ESA content page as of 14 Sep 2026; may change). DR3 had 443,205, so ×13.3.
- **Per-type breakdown and the number of combined astrometric+SB1 (AstroSpectroSB1-like) solutions:** **NOT DOCUMENTED.**
  - DR3 had 33,467 AstroSpectroSB1.
  - Many DR4 rows are probably EclipsingBinary (a second EB catalogue is announced), so 5.9M must not be read as 5.9M orbits of one type.
  - The external forecast is **~1 million astrometric orbits** in DR4, mostly G ≲ 15 and P ≳ 1000 d (arXiv:2411.00088, https://arxiv.org/abs/2411.00088) (Low–Med).
- **Other orbit counts:** `rvs_two_body_orbit` 638,966; `nss_multiple_orbits` 16,681; `nss_acceleration_astro` 3,365,947 (DR3: 338,215); `nss_non_linear_spectro` 79,653 (DR3: 56,808); `nss_masses` 4,323,300 (High).
- **Sources with epoch RVs:** **NOT DOCUMENTED** as a source count.
  - Constraints: epoch RVs for all GRVS ≤ 14 (ESA science-performance page); `all_source_rvs` 312,247,580 sources (upper bound for any RVS product); 6.91e9 single-lined epoch rows (≈ 22 per `all_source_rvs` source); 787k double-lined transit rows.
  - The NAM 2025 talk gives "650 million reliable epoch RVs (1.3 billion total)" and "~6 million faint sources (GRVS > 14) have combined spectra". That implies roughly **30–40 million sources with epoch RVs** (my inference, Low).
  - DR3 had about 33.8M sources with `radial_velocity`.

---

## 4. RVS epoch data: candidate formats the adapter must accept

The basis is DR3 DataLink conventions (INDIVIDUAL epoch photometry, `vari_epoch_radial_velocity`) and the DR4 epoch-astrometry sample. No DR4 RVS column list is public.

**Format A: long table, one row per FoV transit (scalar cells).** **MOST LIKELY** for both DATAMODEL_STANDARD (one file per source) and DATAMODEL_GAIA (many sources per file).
- Reasons:
  - ESA counts these tables in per-FoV-transit rows (6.9e9).
  - The DR4 DPAC epoch-astrometry model is one row per transit.
  - RV, line broadening and Grvs are per-transit scalars (the RV comes from the combined 3-CCD spectrum).
- Single-lined columns, by DR3 conventions:
  - `source_id, solution_id, transit_id`
  - time: `rv_obs_time` [d, BJD(TCB) − 2455197.5] **or** `obs_time_tcb` [ns since 2010.0 TCB]
  - `radial_velocity, radial_velocity_error` [km/s, barycentric]
  - `vbroad, vbroad_error` [km/s]
  - `grvs_mag, grvs_mag_error` [mag]
  - optional: `rv_template_teff`, a rejection/outlier boolean (e.g. `rejected_by_*`), a quality flag, and maybe a per-CCD array (3 RVS CCDs) for some flags.
- Double-lined (`EPOCH_PARAMETERS_RVS_DOUBLE`) adds component-split columns. Likely `radial_velocity_primary/_secondary` with `_error` (NSS naming), possibly `vbroad_primary/_secondary` and a flux or line-depth ratio. The alternative `_1/_2` suffixes should also be accepted.

**Format B: one row per source with per-transit arrays.** **LESS LIKELY**, but plausible for DATAMODEL_GAIA, since DR3 RAW epoch photometry used it (`n_transits`, `transit_id[]`, `g_transit_time[]`, …; https://gea.esac.esa.int/archive/documentation/GDR3/Gaia_archive/chap_datamodel/sec_dm_photometry/ssec_dm_epoch_photometry.html).
- Columns: `source_id, solution_id, n_transits` plus arrays `transit_id[], rv_obs_time[] (or obs_time_tcb[]), radial_velocity[], radial_velocity_error[], vbroad[], vbroad_error[], grvs_mag[], grvs_mag_error[], <flag>[]`.
- Serialisation: in ECSV/CSV, arrays arrive as strings; in VOTable as `arraysize="*"`; in FITS as variable-length arrays.

**Variant A′: per-transit rows with CCD arrays**, like DR4 `epoch_astrometry` DATAMODEL_GAIA. Possible if per-CCD Grvs/flags are included. Accept by exploding arrays as gaiasupdate does.

**Likelihood:** A > A′ > B. The adapter should detect structure (scalar vs array cells; row per source vs per transit) rather than assume it, and map column synonyms. Join to `rvs_epoch_spectrum` and `rvs_transit_description` via `transit_id`.

---

## 5. Other things that can break a DR3-era pipeline

1. **Reference epoch J2016.0 → J2017.5** (High).
   - Positions, `ra0/dec0` and epoch-astrometry relative times all change.
   - Propagate DR3 positions by 1.5 yr before positional matching.
   - `t_periastron` most likely shifts by 547.875 d (Low, unverified).
2. **source_id is independent of DR3** (High).
   - Use `dr3_neighbourhood`, never ID equality.
   - Columns are NOT DOCUMENTED. By analogy with DR3 `dr2_neighbourhood` (`dr2_source_id, dr3_source_id, angular_distance [mas], magnitude_difference [mag], proper_motion_propagation [bool]`; https://gaia.aip.de/metadata/gaiadr3/dr2_neighbourhood/), expect `dr3_source_id, dr4_source_id, angular_distance, magnitude_difference, proper_motion_propagation` (Low).
   - **Trap:** the pre-release "DR4 source_id"s for Gaia BH3 (4318465066420528000), HD 114762 (3937211745905473024) and Gaia-4 (1457486023639239296) are identical to their DR3 source_ids, as far as I know from the literature (Med). Many IDs will coincide, so a naive `source_id` join will *mostly* work and silently fail on the rest. Handle 0, 1 and N matches.
3. **gaia_source is a subset (2.0e9 of 2.79e9)** (High). DR3 targets can be missing from `gaia_source` but present in `all_source_*`. Query `all_source_astrometry`/`all_source_rvs` when a join fails.
4. **Consolidated gaia_source** (High). For binaries, `parallax`/`pm*`, and possibly `ruwe`, may come from a non-single-star model. A DR3-style "RUWE > 1.4 flags binarity" cut, or a comparison of `gaia_source` parallax with the NSS parallax, can behave differently. Find the model/solution indicator column in the final data model.
5. **DataLink names** (High).
   - `INDIVIDUAL/RAW` became `DATAMODEL_STANDARD/DATAMODEL_GAIA`; `COMBINED` was removed.
   - DR3 `RVS` became `MEAN_SPECTRUM_RVS`; `XP_CONTINUOUS/XP_SAMPLED` became `MEAN_SPECTRUM_XP`; `MCMC_GSPPHOT` became `MCMC_GSP_PHOT`.
   - Stable astroquery 0.4.11 defaults to the removed names.
6. **Units and serialisation in epoch astrometry** (Med).
   - Times are int64 **ns**, not days.
   - `nu_eff_used_in_astrometry` is in **nm⁻¹** in the DataLink sample, not µm⁻¹ as in DR3 `gaia_source`.
   - Array cells: ECSV writes `[...]` strings; CSV writes `(...)` strings, and the internal sample had a duplicated `used_by_agis_al` header; VOTable uses `bit`/`*` arrays; FITS booleans arrive as bytes 84 ('T') / 70 ('F').
   - Masked values become NaN.
   - SM (index 0) must be excluded for AGIS-like fits (`used_by_agis_al` is False there in the sample).
7. **Time conventions differ across products.** DR3 photometry/RV epochs were BJD(TCB) − 2455197.5 [d]; DR4 astrometry uses ns since 2010-01-01T00:00 TCB plus a separate barycentric correction.
8. **Archive limits.**
   - Anonymous users get 50,000 rows, 50 DataLink IDs and a 1-min async timeout.
   - Registered users get 5 parallel jobs, a 50-job queue (excess rejected) and 5,000 IDs per DataLink call.
   - The sync timeout is 60 s for everyone, so use async for anything non-trivial.
9. **Schema name** `gaiadr4` is presumed by pattern (gaiadr2, gaiadr3, gaiafpr) but **not confirmed**. Discover it via `TAP_SCHEMA.tables`.
10. **DR3 corrections must not be reused blindly**: RV corrections for faint stars, the known vbroad overestimate below about 10 km/s, G-band and BP/RP flux-excess corrections, the parallax zero-point (a DR4 recipe paper is announced), and the RUWE threshold.
11. **NSS decoding.** `corr_vec` length/order is tied to `bit_index`. New solution types or parameters break a hard-coded 231-element or DR3-ordered decoder.
12. **Content may still change.** The DR4 content page is "under development" (last update 14 Sep 2026). The final data model and documentation (about 2,500 pages, HTML and PDF) arrive on release day; known issues will be posted on a page to be announced.

---

## Adapter requirements (release-day checklist)

1. **Pin and verify astroquery.** Install astroquery 0.4.12 (or the newest dev). At start-up, assert `'DATAMODEL_STANDARD'` is accepted. Pass `data_structure` explicitly, with a fallback to the old names only if the server rejects the new ones.
2. **Log in** (registered account) before any job. Assert the quotas you rely on (5,000 DataLink IDs per call, unlimited rows, 120-min async). Chunk DataLink requests at ≤5,000 IDs. Keep ≤5 concurrent jobs and <50 queued, with retry/backoff.
3. **Discover the schema at run time.** Read `TAP_SCHEMA.tables`/`columns` for `gaiadr4%`:
   - Fail loudly if any required table is missing: `gaia_source`, `nss_two_body_orbit`, `dr3_neighbourhood`, `all_source_rvs`, `all_source_astrometry`, `rvs_two_body_orbit`.
   - Diff the actual column lists and units against an expected-schema file; this note is the first draft.
4. **Discover DataLink types at run time.** Call the DataLink `links` endpoint (or `get_datalinks`) for 2–3 known sources, e.g. the pre-release IDs above, and read the actual retrieval-type names: `EPOCH_ASTROMETRY`, `EPOCH_PARAMETERS_RVS_SINGLE`, `EPOCH_PARAMETERS_RVS_DOUBLE`, `EPOCH_SPECTRUM_RVS`, `EPOCH_FLAGS_NSS`. Never hard-code returned file names; iterate the dict.
5. **Assert `ref_epoch == 2017.5`** in `gaia_source` and in NSS (if present). Read the `t_periastron` reference from the column description and convert to a common epoch before any DR3 comparison.
6. **Cross-match only via `dr3_neighbourhood`.** Check its column names and units. Handle 0, 1 or N counterparts. Keep the angular distance and magnitude difference. Never assume `dr3_source_id == dr4_source_id`, even though they often match.
7. **NSS table:**
   - Enumerate `SELECT nss_solution_type, COUNT(*) … GROUP BY 1`. Unknown types go to a quarantine path, not a crash.
   - Check Thiele–Innes units (A, B, F, G in mas; C, H in AU), `period` in d, and `t_periastron` reference.
   - Decode `corr_vec` from `bit_index` generically.
   - Also pull `rvs_two_body_orbit`, `nss_multiple_orbits` and `nss_masses`.
8. **RVS epoch adapter:** accept Formats A, A′ and B (Section 4). Map synonyms:
   - time: `rv_obs_time`/`obs_time_tcb`/`transit_time`
   - RV: `radial_velocity`/`rv`
   - broadening: `vbroad`/`line_broadening`
   - SB2 components: `_primary/_secondary`/`_1/_2`
   - Convert times to a single scale and assert units from metadata (km/s, mag, d or ns).
   - Allow null RVs on rows that carry only Grvs.
   - Treat the double table as optional and sparse.
9. **Epoch-astrometry adapter:**
   - Detect exploded vs array form; explode 10-element CCD arrays with `component_index` (0 = SM, excluded).
   - Parse array strings for CSV `(...)` and ECSV `[...]`; convert FITS byte booleans.
   - Times are ns plus `obs_time_bary_corr` (ns); relative time is to J2017.5.
   - Check the `nu_eff` unit.
   - Cross-check one source against `gaiasupdate` output vs `gaia_source`.
10. **gaia_source fields used** (`phot_g_mean_mag, bp_rp, grvs_mag, vbroad, vbroad_error, vbroad_nb_transits, ruwe, parallax, random_index, non_single_star`):
    - assert each exists, its unit, and its null fraction;
    - read the `non_single_star` bit definition from the column description;
    - recompute any `random_index` fraction cut from the actual row count;
    - identify the column that says which astrometric model was adopted.
11. **Missing-source fallback.** If a DR3 target is not in DR4 `gaia_source`, query `all_source_*`. A missing DataLink file for a source means "no product", not an error.
12. **Sizes and timeouts.** Prefer binary VOTable or FITS over CSV/ECSV. Budget 10–30 GB for epoch astrometry and 20–40 GB+ for RVS epoch spectra per 1e5 sources. Stream to disk (`dump_to_file`/`output_file`) and resume by chunk. Async TAP jobs must finish within 120 min, so split by `source_id` ranges.
13. **Day-1 resilience.** The archive opens at 12:00 CET; expect load. Have a partner-centre fallback (ARI/GAVO, AIP, CDS, ASDC, Flatiron) and record which service and astroquery version produced each file. Re-run schema checks once the final data model and known-issues page are published.

---

## Sources

**ESA primary pages:**
- https://www.cosmos.esa.int/web/gaia/release
- https://www.cosmos.esa.int/web/gaia/data-release-4
- https://www.cosmos.esa.int/web/gaia/dr4 (content table, `#datamodel`)
- https://www.cosmos.esa.int/web/gaia/dr4-prerelease
- https://www.cosmos.esa.int/web/gaia/dr4-papers
- https://www.cosmos.esa.int/web/gaia/dr4-software-tools
- https://www.cosmos.esa.int/web/gaia/dr4-events
- https://www.cosmos.esa.int/web/gaia/dr4-previews
- https://www.cosmos.esa.int/web/gaia/gaia-source-update
- https://www.cosmos.esa.int/web/gaia/news
- https://www.cosmos.esa.int/web/gaia/news-2026
- https://www.cosmos.esa.int/web/gaia/bulletin-archive
- https://www.cosmos.esa.int/web/gaia-users/archive/collaborate#GaiaArchiveUserQuotas
- https://www.cosmos.esa.int/web/gaia-users/archive/release-notes
- https://www.cosmos.esa.int/web/gaia-users/archive/faq
- https://www.cosmos.esa.int/web/gaia-users/archive/datalink-products
- https://www.cosmos.esa.int/web/gaia/science-performance
- https://cosmos.esa.int/web/gaia/home/-/asset_publisher/wEXKCCPdRxv0/content/2022-12-02-xxx (2024-12-03 archive towards DR4)

**DR3 data model:**
- https://gea.esac.esa.int/archive/documentation/GDR3/Gaia_archive/chap_datamodel/sec_dm_non--single_stars_tables/ssec_dm_nss_two_body_orbit.html
- https://gea.esac.esa.int/archive/documentation/GDR3/Gaia_archive/chap_datamodel/sec_dm_main_source_catalogue/ssec_dm_gaia_source.html
- https://gea.esac.esa.int/archive/documentation/GDR3/Gaia_archive/chap_datamodel/sec_dm_photometry/ssec_dm_epoch_photometry.html
- https://gea.esac.esa.int/archive/documentation/GDR2/Gaia_archive/chap_datamodel/sec_dm_datalink_tables/ssec_dm_light_curve.html
- https://gaia.aip.de/metadata/gaiadr3/dr2_neighbourhood/
- https://gaia.aip.de/metadata/gaiadr3/vari_epoch_radial_velocity/
- https://gaia.aip.de/metadata/gaiafpr/vari_epoch_radial_velocity/
- https://www.aanda.org/articles/aa/full_html/2023/06/aa43782-22/T1.html

**Code:**
- https://github.com/esa/gaia-supdate (`src/gaiasupdate/constants.py`, `epoch_astrometry.py`, `tests/test_data/gacs_data_link/*`)
- https://github.com/esa/gaia-bhthree/tree/gaia-dr4-prerelease (`Gaia-DR4-prerelease_BH3_fit_astrometric_orbit.ipynb`)
- https://docs.astropy.org/projects/astroquery/en/latest/_modules/astroquery/gaia/core.html
- https://docs.astropy.org/projects/astroquery/en/stable/_modules/astroquery/gaia/core.html
- https://github.com/astropy/astroquery/pull/3371
- https://pypi.org/project/astroquery/#history
- https://exogaia.readthedocs.io/en/latest/tutorials/dr4_pre-release.html

**Talks and papers:**
- https://conference.astro.dur.ac.uk/event/7/contributions/327/attachments/351/628/gaia-status-nam25-jul25.pdf
- https://conference.astro.dur.ac.uk/event/7/contributions/939/attachments/324/586/gaiadr4-gaianir-nam25-walton-jul25.pdf
- https://ohp2025.sciencesconf.org/data/pages/Sahlmann_ohp2025_review.pdf
- https://arxiv.org/abs/2411.00088
- https://arxiv.org/abs/2607.00264
- https://www.aanda.org/articles/aa/full_html/2026/04/aa58618-25/aa58618-25.html

**Not readable from this session** (must be checked manually):
- https://anonftp.cosmos.esa.int/pub/GAIA_PUBLIC_DATA/Gaia_DR4/dr4-prerelease/gaia-dr4-prerelease-draft-data-model_2026-06-26.zip
- https://anonftp.cosmos.esa.int/pub/GAIA_PUBLIC_DATA/Gaia_DR4/dr4-prerelease/gaia-dr4-prerelease-epoch-astrometry_2026-06-26.zip
- https://gea.esac.esa.int/archive/documentation/GDR4/
- https://github.com/esa/gaia-jupyter-notebooks/tree/main/data-release-4-tutorials
