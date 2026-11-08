# Independent RV check with APOGEE DR17 (EXPLORATORY, 6 Nov 2026)

**Data**
- APOGEE DR17 allStar (VizieR III/286/catalog), downloaded through the CfA VizieR mirror on 6 Nov 2026.
- 485 709 stars with ≥ 2 visits and a Gaia EDR3 id. Saved as `realdata/external/apogee_dr17_multivisit.csv` (SHA-256 a942246a…).
- APOGEE was never used to build or tune GAIA-FP.

**Code:** `src/apogee_validation.py` → `results/apogee_validation.json`, `results/apogee_candidates.csv`.

**Status:** exploratory. Not pre-registered and not time-separated (APOGEE DR17 is public), but it is independent instrument data.

## A. Does a second spectrograph confirm Gaia's dynamical labels?
APOGEE counts how many sets of spectral lines it sees (Ncomp). Two sets means it sees the companion's light directly.

| Gaia dynamical label | Systems in APOGEE | APOGEE sees 2 sets of lines | 95% CI |
|---|---|---|---|
| luminous companion (impostor type) | 51 | **12 (24%)** | 13–37% |
| dark-consistent | 69 | **2 (3%)** | 0.4–10% |

**Reading:** an independent instrument sees the companion's light about 8 times more often in the systems Gaia's dynamics called luminous. The ρ labels used in H10, M1–M4 and H13 are therefore real, not an artefact of our method.

## B. Do our frozen DR3 predictions rank real impostors?
- **The test:** a companion of ≤ 80 MJ cannot make the star's RV scatter exceed K₈₀(1+e). K₈₀ is the reflex amplitude for an 80 MJ companion with that candidate's own P, e, i and M (median 2.6 km/s). We call a candidate **RV-incompatible with a substellar companion** if its APOGEE RV scatter exceeds K₈₀(1+e) + 1 km/s.
- **Sample:** 61 of the 2102 DR3 candidates have APOGEE multi-visit data. **8** are RV-incompatible, i.e. confirmed impostors by an independent instrument.

| Score (frozen 9 Oct, OSF TBJGY) | AUC for the 8 confirmed impostors | 95% CI |
|---|---|---|
| **GAIA-FP P_impostor** | **0.73** | 0.58–0.88 |
| log LR only | 0.62 | 0.41–0.80 |
| CMD only (B2) | 0.60 | 0.36–0.81 |

- **All 8 confirmed impostors** had been given the verdict "likely_impostor" by the frozen model. None was "ambiguous".

## Limitations (stated plainly)
- **n = 8 positives:** the intervals are wide.
- **Exploratory:** not pre-registered.
- **Short visit baselines:** most APOGEE visits are a few days apart while the orbits last hundreds of days. A quiet RV is therefore **not** proof of a substellar companion; the 19 "RV-quiet" candidates are not counted as negatives.
- **APOGEE targets** are biased toward bright, red stars.
