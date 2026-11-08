# APOGEE DR17 exact-cadence RV analysis — GAIA-FP

## Official data model (verified against SDSS DR17 documentation)

For each APOGEE visit, use:
- `APOGEE_ID` (join key to the DR17 allStarLite crosswalk)
- `JD` (`JD-MID`, floating-point days; the actual visit midpoint)
- `VHELIO` (barycentric-corrected visit RV; despite its name, not heliocentric)
- `VRELERR` (km/s; the uncertainty for `VHELIO`)
- `STARFLAG` and `RV_FLAG` (quality bitmasks)

**Do not use integer-day `MJD` as the cadence timestamp.** SDSS explicitly says the allVisit `JD` is the visit midpoint and `MJD` is integer day only. The five primary STARFLAG rejection bits are 0 (`BAD_PIXELS`), 3 (`VERY_BRIGHT_NEIGHBOR`), 4 (`LOW_SNR`), 19 (`RV_REJECT`), and 22 (`RV_FAIL`). RV_FLAG bit 10 is `RV_REJECT`, bit 11 is `RV_SUSPECT`. Retain RV-suspect and multiple-suspect visits as flagged records for a sensitivity review; `MULTIPLE_SUSPECT` is an SB2 warning, not an automatic compact-object label. For the strictest quality sensitivity, also exclude STARFLAG persistence bits 9, 12, and 13.

Official sources: [SDSS DR17 using radial velocities](https://www.sdss4.org/dr17/irspec/use-radial-velocities/), [APOGEE bitmasks](https://www.sdss4.org/dr17/irspec/apogee-bitmasks/).

## Required DR17 files

- allVisit: [official DR17 allVisit product](https://data.sdss.org/sas/dr17/apogee/spectro/aspcap/dr17/synspec_rev1/allVisit-dr17-synspec_rev1.fits)
- allStarLite: [official DR17 allStarLite product](https://data.sdss.org/sas/dr17/apogee/spectro/aspcap/dr17/synspec_rev1/allStarLite-dr17-synspec_rev1.fits)

The archived GAIA-FP package does not include the original visit-level rows nor a complete verified `source_id` ↔ `APOGEE_ID` map for the 46 analysed APOGEE targets. `realdata/sb2_apogee.csv` is an SB2 cross-match, not a substitute for that visit map.

## Reproducible execution

```bash
# Build a one-to-one Gaia DR3 source_id ↔ APOGEE_ID map from allStarLite.
python tools/epoch_rv/build_apogee_mapping.py \
  --allstar /path/allStarLite-dr17-synspec_rev1.fits \
  --candidates realdata/dr3_candidates.csv \
  --outdir results/final_completion/apogee

# Extract exact visit epochs and RVs. The default run applies the five
# primary SDSS rejection bits and preserves suspect flags for review.
python tools/epoch_rv/process_apogee_allvisit.py \
  --allvisit /path/allVisit-dr17-synspec_rev1.fits \
  --mapping results/final_completion/apogee/apogee_gaia_dr3_mapping.csv \
  --outdir results/final_completion/apogee

# Optional quality sensitivity: SNR >= 10 (recommended by SDSS).
# Run separately; do not silently replace the primary extraction.
python tools/epoch_rv/process_apogee_allvisit.py \
  --allvisit /path/allVisit-dr17-synspec_rev1.fits \
  --mapping results/final_completion/apogee/apogee_gaia_dr3_mapping.csv \
  --outdir results/final_completion/apogee_snr10 --require-snr10

# Cadence-matched Keplerian recovery (only after actual visit rows exist).
python tools/epoch_rv/run_exact_cadence_injection.py \
  --input results/final_completion/apogee/apogee_allvisit_accepted.csv \
  --outdir results/final_completion/apogee_exact_cadence \
  --trials 1000 --seed 20261103
```

The extractor writes both the primary accepted visit table and a strict-quality sensitivity table (`apogee_allvisit_high_quality.csv`) that additionally excludes STARFLAG persistence bits 9, 12, and 13. The injection grid spans periods 1, 10, 30, 100, 300, and 1,000 days; K1 amplitudes 0.1–10 km/s; and eccentricities 0, 0.3, and 0.6. Each source's observed JD cadence and `VRELERR` values are used directly, with a constant-RV chi-square diagnostic at alpha=0.01. This reports conditional detection power under the observed cadence/errors; it is not a compact-object confirmation test.

## Status

**PARTIAL — processing pipeline and unit tests complete; empirical cadence analysis not executed.** The required large official files could not be downloaded from this execution environment because external DNS resolution failed for `data.sdss.org`. The former 414k synthetic/matched-baseline proxy remains separate and must not be described as exact cadence.
