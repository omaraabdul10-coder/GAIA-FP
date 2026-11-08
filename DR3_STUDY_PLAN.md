# DR3 real-data study (H7-DR3): plan written BEFORE any survey match or score is computed

**Written:** 9 October 2026, 04:20 (UTC+4); amended at 04:40, still before any data download, to add the one-row-per-source rule. This file is committed and hashed before the analysis is run.

## Why this study

Until now, every GAIA-FP classification number has been a simulation. Gaia DR3 (public since 2022) already contains astrometric orbits and photometry, though not epoch RVS line widths. Public spectroscopic surveys have independently found thousands of double-lined binaries (SB2). This study therefore gives a **real-data** test of GAIA-FP's astrometry + photometry component now, before DR4.

The study is exploratory with respect to DR4: it does not replace the DR4 confirmatory test. It is, however, fully pre-specified here.

## Data, all public

| Source | Content | Access |
|---|---|---|
| Gaia DR3 `nss_two_body_orbit` + `binary_masses` + `gaia_source` + `dr2_neighbourhood` | Astrometric orbits (Thiele–Innes), photometric primary mass m1, photometry, astrometry, DR2 ids | Gaia archive TAP |
| Gaia DR3 field stars | Random sample with parallax/error > 20, RUWE < 1.2, `non_single_star` = 0, parallax > 5 mas. Used **only** to measure the main-sequence ridge and its scatter. | Gaia archive TAP |
| APOGEE SB2: Kounkel et al. 2021, AJ 162, 184 (VizieR J/AJ/162/184/table1) | 8105 SB2 / higher-order systems | VizieR TAP |
| GALAH SB2: Traven et al. 2020, A&A 638, A145 (J/A+A/638/A145/catalog) | 12760 analysed binaries | VizieR TAP |
| LAMOST-MRS SB2: Kovalev et al. 2024, MNRAS 527, 521 (J/MNRAS/527/521/tableb1) | 12426 SB2 candidates | VizieR TAP |
| LAMOST-MRS RV catalogue: Wang et al. 2019, ApJS 244, 27 (J/ApJS/244/27/lamostMRS) | Which stars LAMOST-MRS observed, and how many epochs | VizieR TAP |

## Candidate sample (fixed rule)

1. Take every DR3 `nss_two_body_orbit` solution with Thiele–Innes elements and parallax > 0.
2. Join to `binary_masses` to obtain m1.
3. Compute the dark-companion mass estimate m2 = 1047.6 · m1 · (a0/ϖ) / (m1 P²)^(1/3), in M_J, with P in years.
4. Keep candidates with **m2 < 80 M_J**. A server-side count on 9 Oct gave **2192**.
5. **One row per source.** If a source has several orbital solutions, keep one, preferring this order of `nss_solution_type`: Orbital, AstroSpectroSB1, OrbitalTargetedSearchValidated, OrbitalTargetedSearch, OrbitalAlternativeValidated, OrbitalAlternative. Ties go to the nearest DR2 neighbour.
6. **Sealed objects removed first.** Every source_id in the private labels_v1/labels_v2 files is dropped automatically by code before any feature is computed. No DR3 feature of a sealed object is inspected. The public file `realdata/excluded_sealed_ids.csv` lists these ids **without labels**, so the exclusion can be reproduced; the labels stay private.

## Labels (fixed rules, independent of Gaia)

| Label | Rule |
|---|---|
| Survey-SB2 (impostor) | Candidate matched to any of the three SB2 catalogues |
| LAMOST-single | Observed by LAMOST-MRS with ≥ 2 epochs (Wang 2019) and **not** in the LAMOST SB2 catalogue |

Matching rules:
- **LAMOST SB2:** by Gaia DR3 id.
- **GALAH:** by Gaia DR2 id, mapped through `dr2_neighbourhood` (nearest, angular distance < 1″).
- **APOGEE:** by position. Gaia positions are propagated to J2000 with proper motions, the radius is 2″, and ambiguous multiple matches are flagged and excluded.

The absence of an SB2 flag is **not** treated as evidence for a planet.

## Methods compared (all frozen; none tuned on these labels)

| Method | Definition |
|---|---|
| **GAIA-FP v3.1** | Joint a0 \| CMD likelihood (`joint_lr.py`) with the measured CMD scatter of the colour bin, plus the label-free EM prior fitted on all candidates. No RVS term, because DR3 has no epoch widths. |
| B1 | RUWE (higher = more suspicious) |
| B2 | CMD over-luminosity ΔM_G alone (more negative = more suspicious) |
| B3 | Inverse orbit significance |
| B4 | Random |

## Primary metric and success criterion

**P1 (primary).** AUC of GAIA-FP for survey-SB2 vs LAMOST-single, restricted to candidates observed by LAMOST-MRS, so that both classes share one survey selection. The 95% CI comes from a stratified bootstrap with 2000 resamples.
- **Success:** the lower CI bound is above 0.5.
- **Failure:** the CI includes 0.5.

**P2 (secondary, exploratory).** Positive-unlabelled AUC for all survey-SB2 candidates vs every other candidate. This is a lower bound, because the unlabelled set contains unflagged impostors.

**P3 (secondary).** Recall: the fraction of survey-SB2 candidates with P ≥ 0.85, and with P ≥ 0.5. Also the fraction labelled "ambiguous".

**P4 (secondary).** GAIA-FP AUC minus each baseline's AUC, with paired bootstrap CIs.

## Reporting

- If the survey-SB2 class has fewer than 10 members in P1, P1 is reported as **underpowered** and not as a success or failure.
- All numbers are reported whatever their sign.
- Nothing in the method is changed after seeing these labels. Any later change is labelled exploratory and reported both with and without the change.
