# A larger RV label set from Gaia DR3's own RV amplitudes (plan, written before any value was looked at)

**Written:** 8 Nov 2026. The SHA-256 is stored in `GAIA_RV_LABEL_PLAN.sha256` before the run. Exploratory: it changes no DR4 test.

**Why:** the APOGEE test has only 8 positives (61 candidates with data). Gaia DR3 publishes `rv_amplitude_robust` (peak-to-peak of the epoch RVs) for bright RVS stars, for far more candidates. The column is already in `realdata/dr3_candidates_vbroad_raw.csv` (D1, downloaded 9 Oct).

**Label rule** (same physics as APOGEE rule B, fixed before looking):
- A companion of ≤ 80 MJ cannot produce a peak-to-peak RV range larger than 2·K80, where K80 is the primary's semi-amplitude for an 80 MJ companion with the candidate's own P, e, i and M (`apogee_validation.py` formula).
- Per-epoch noise: σ_ep = radial_velocity_error·√(2·rv_nb_transits/π).
- **Positive** (RV-incompatible with a substellar companion): rv_nb_transits ≥ 6 **and** rv_amplitude_robust > 2·K80 + 5·σ_ep + 1 km/s.
- Every other candidate with rv_nb_transits ≥ 6 and a finite rv_amplitude_robust is **unlabelled** (positive-vs-unlabelled, as for APOGEE).
- Sealed ids are dropped first.

**Caveat (stated in advance):** the label uses Gaia RVS centroids, and P_impostor uses Gaia RVS line widths. These are different quantities from the same instrument, so they are not fully independent. Unresolved near-twins move the RV centroid less (label blindness), so this label misses some impostors. It cannot invent them.

**Statistics:**
- **Primary:** AUC of the frozen P_impostor, with a 95% stratified-bootstrap CI (B = 2000, seed 7). Pass if the lower bound is > 0.5.
- **Secondary:** paired ΔAUC vs CMD-only (frozen P_B2) and vs BJK m2 (where available). "Better" only if the 95% CI lies above 0.
- Reported in `RESULTS_GAIA_RV_LABELS.md` whatever the outcome; run once.
