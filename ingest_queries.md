# Real-data ingestion: exact queries, run in a browser because the analysis workspace cannot reach these hosts

Each query result is saved as the CSV named below in `realdata/`. Download timestamps are recorded in `realdata/PROVENANCE.md`.

## Gaia archive (https://gea.esac.esa.int/tap-server/tap/sync, ADQL, CSV)

### `dr3_candidates.csv`

```sql
SELECT o.source_id, g.ra, g.dec, g.pmra, g.pmdec, g.phot_g_mean_mag, g.bp_rp, g.ruwe,
       o.nss_solution_type, o.period, o.period_error, o.eccentricity, o.eccentricity_error, o.t_periastron,
       o.a_thiele_innes, o.b_thiele_innes, o.f_thiele_innes, o.g_thiele_innes,
       o.a_thiele_innes_error, o.b_thiele_innes_error, o.f_thiele_innes_error, o.g_thiele_innes_error,
       o.parallax, o.parallax_error, o.significance, b.m1, b.m1_lower, b.m1_upper,
       n.dr2_source_id, n.angular_distance AS dr2_angular_distance
FROM gaiadr3.nss_two_body_orbit AS o
JOIN gaiadr3.binary_masses AS b ON b.source_id = o.source_id
JOIN gaiadr3.gaia_source AS g ON g.source_id = o.source_id
LEFT JOIN gaiadr3.dr2_neighbourhood AS n ON n.dr3_source_id = o.source_id
WHERE o.a_thiele_innes IS NOT NULL AND o.parallax > 0 AND <m2_expr> < 80
```

`<m2_expr>` is the dark-companion mass in M_J, computed from the Thiele–Innes constants:

```
1047.6*b.m1*( SQRT(u + SQRT(u*u - v*v)) / o.parallax ) / POWER(b.m1*POWER(o.period/365.25,2), 1/3)
```

where:
- u = (A² + B² + F² + G²)/2
- v = A·G − B·F

The full expanded form is in the browser session log.

### `dr3_field.csv`

```sql
SELECT TOP 20000 phot_g_mean_mag, bp_rp, parallax FROM gaiadr3.gaia_source
WHERE parallax_over_error > 20 AND ruwe < 1.2 AND non_single_star = 0 AND parallax > 5 AND random_index < 3000000
```

## VizieR TAP (https://tapvizier.cds.unistra.fr/TAPVizieR/tap/sync)

| File | Query |
|---|---|
| `sb2_lamost.csv` | `SELECT GaiaDR3 AS gaia_dr3_source_id FROM "J/MNRAS/527/521/tableb1"` (Kovalev+2024) |
| `sb2_galah.csv` | `SELECT GaiaDR2 AS gaia_dr2_source_id FROM "J/A+A/638/A145/catalog"` (Traven+2020) |
| `sb2_apogee.csv` | `SELECT ID, RAJ2000 AS ra, DEJ2000 AS dec, SBn FROM "J/AJ/162/184/table1"` (Kounkel+2021) |
| `lamost_cov.csv` | `SELECT Gaia AS gaia_dr2_source_id, COUNT(*) AS n_epochs, AVG(RAJ2000) AS ra, AVG(DEJ2000) AS dec FROM "J/ApJS/244/27/lamostMRS" WHERE Gaia IS NOT NULL GROUP BY Gaia` (Wang+2019; full catalogue, async) |

The complete LAMOST-MRS coverage catalogue is required for the registered positional fallback in `src/dr3_study.py`. Do not restrict this query to candidate DR2 IDs: the coverage procedure needs all possible positional counterparts and must preserve ambiguous matches.
