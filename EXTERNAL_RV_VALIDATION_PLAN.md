# External ground-based RV validation: plan (written and hashed before any data are fetched)

Date: 9 Nov 2026. Status: **exploratory** (not part of the confirmatory family; does not change any registered test).

## Why
The development checks so far use one small independent RV sample (APOGEE, 8 positives) or labels that come from Gaia itself
(AstroSpectroSB1). This analysis adds independent ground-based radial-velocity orbits, so that GAIA-FP can be scored on
labels that do not come from Gaia, and so that real false positives can be characterised with an independent mass.

## Sample
- `results/dr3_candidates_scored.csv` (frozen DR3 predictions, OSF TBJGY). No re-fit, no new score.
- Sealed ids (`realdata/excluded_sealed_ids.csv`) are dropped **before** any cross-match. The fetched catalogues are also
  filtered against the sealed list before they are saved.

## External data (fetched once, saved with provenance in `realdata/external/`)
1. **SB9** catalogue of spectroscopic binary orbits (Pourbaix et al. 2004, VizieR `B/sb9`): coordinates, period P, K1, K2, e.
2. **NASA Exoplanet Archive** `pscomppars`: hosts with a Gaia id, companion msini or mass from radial velocity, period.

Cross-match: SB9 by position (≤ 5 arcsec after propagating Gaia positions to J2000 with proper motion) and |ΔG| or V–G
consistent within 1.5 mag; Exoplanet Archive by Gaia DR2/DR3 id, falling back to position ≤ 3 arcsec.

## Labels (set by these rules only)
For each matched candidate, K80 = RV semi-amplitude of the primary for an 80 MJ companion, from the Gaia orbit
(P, e, inclination) and the frozen primary mass M (same formula as `followup/shamakhy_targets.py`).

An orbit is used only if its period agrees with the Gaia period: |P_ext − P_Gaia| / P_Gaia ≤ 0.20. Others are listed
as "different orbit" and excluded.

- **Impostor (positive)**: SB9 lists K2 (double-lined), **or** the external K1 ≥ K80.
- **Substellar (negative)**: external K1 < K80 and single-lined, **or** an Exoplanet Archive companion with RV mass
  (or msini combined with the Gaia inclination) < 80 MJ and period match.
- Conflicting labels between sources → excluded and listed.

## Endpoints
- **E1 (task: independent RV cross-match)**: AUC of `P_impostor` on these labels, 95% stratified bootstrap CI
  (B = 2000, seed 7). Reported only if ≥ 5 positives and ≥ 5 negatives; otherwise NOT_CONDUCTED with counts.
- **E2 (task: strong baseline comparison)**: on the same labels, AUC of (a) CMD-only `llr_cmd`, (b) the catalogue
  astrometric companion mass `mfit` (higher = more stellar), (c) Bailer-Jones & Kreidberg 2026 m2 where available.
  Paired bootstrap ΔAUC (GAIA-FP minus each). Verdict "better" only if the 95% CI is above 0.
- **E3 (task: real false-positive characterisation)**: for every positive: external K1, the companion mass implied by
  K1 with the Gaia inclination (m2_RV), the ratio m2_RV / mfit, double-lined flag, reference. Median ratio with
  bootstrap CI. Descriptive only.

## Reporting
All counts are reported, including excluded and "different orbit" matches. Results go to
`RESULTS_EXTERNAL_RV.md` and `results/external_rv_validation.json`, whatever they show.
The script asserts the SHA-256 prefix of this plan before running.
