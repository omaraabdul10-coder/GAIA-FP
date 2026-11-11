# Shamakhy follow-up plan: line doubling, not the K amplitude

Status: **draft for the team.** Hash it and register it on OSF before the first spectrum is taken. Code: `followup/shamakhy_forward.py`. Outputs: `followup/forward.csv` and `forward.json`. Tests: `tests/test_shamakhy_forward.py`.

## 1. Why the plan in the 9 November letter has to change
The letter said a substellar companion would give a small K, about K_ast, and an impostor a K "several times larger", about 1.5–10 km/s (the `K_4x` column). That is the true K1 of the primary star. It is **not** what a blended spectrum measures.

Our own `src/rv_degeneracy.py` (A6, A9) explains why. When the two stars' lines are blended, the centroid moves with amplitude K_sum (B − f). With f equal to the light fraction, that is exactly the photocentre's amplitude, K_ast. So under both hypotheses the measured K comes out close to K_ast, and a K test cannot separate them. `test_centroid_reproduces_photocentre_in_blend_limit` checks this identity.

## 2. What does separate them: line doubling at the orbital extremes
To make an impostor reproduce Gaia's a0 with L ∝ M^4, the companion must be a near-twin: q ≈ 0.89–0.98 and f ≈ 0.37–0.48. Its relative velocity is then large, K_sum ≈ 11–49 km/s. ShaFES has FWHM ≈ 5.4 km/s at R = 56 000 (10.7 km/s at R = 28 000), so near the orbit extremes the two line systems separate and the spectrum is **double-lined**. A dark companion gives a single narrow line at every phase.

As a result, the test needs **2 spectra per target, timed to the extremes of the orbit**, not 3–4 spectra for fitting K.

## 3. Pre-registered decision rule (proposed)
Each spectrum is cross-correlated with a single-star template (broadening function or CCF; DECH30, as Kh. Mikailov recommended). We fit one Gaussian and two Gaussians to the profile.
- **DOUBLE** if ΔBIC(2 − 1) < −10, the weaker component is at least 10% as deep as the stronger, and the separation is at least 0.8 FWHM.
- **IMPOSTOR (confirmed)**: at least one of the two spectra is DOUBLE.
- **DARK-CONSISTENT**: both spectra are single, and the profile σ is within 15% of the template σ at both epochs.
- **INCONCLUSIVE**: anything else, including a missed planned night or S/N < 30.

Scoring: GAIA-FP's frozen verdicts (`P_impostor`) against these outcomes. 15 targets are predicted impostor and 1 dark. We report every outcome, including INCONCLUSIVE.

## 4. Targets, planned nights and expected power
The two nights are chosen from the nights on which the target is above 30° for at least one hour of astronomical night (ShAO, 2026-12-01 to 2027-10-31). They maximise |g| averaged over the Gaia period error.

p_double is the probability that at least one of the two spectra is double-lined if the target really is an impostor (separation > 1 FWHM).

| Gaia DR3 source_id | G | P_imp | K_ast (km/s) | q_imp | K_sum (km/s) | sep/FWHM (R56k) | p_double 2 ep. R56k | p_double 2 ep. R28k | night 1 | night 2 | σ_phase (cyc) | CMD Δm |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1878822452815621120 | 9.76 | 0.06 | 0.41 | 0.98 | 28 | 0.3 | 0.98 | 0.95 | 2026-12-04 | 2027-08-20 | 0.50 | -0.1 |
| 4321775627212956672 | 7.01 | 1.00 | 2.69 | 0.92 | 44 | 1.8 | 0.96 | 0.89 | 2027-04-06 | 2027-03-21 | 0.24 | -2.3 |
| 3913728032959687424 | 7.46 | 1.00 | 1.78 | 0.94 | 39 | 4.3 | 1.00 | 1.00 | 2027-06-02 | 2027-02-17 | 0.12 | -6.1 |
| 364792020789523584 | 7.94 | 1.00 | 1.37 | 0.95 | 33 | 1.6 | 0.92 | 0.83 | 2027-08-13 | 2027-02-14 | 0.19 | -2.5 |
| 2994437527894182272 | 8.50 | 1.00 | 0.42 | 0.95 | 11 | 0.8 | 0.00 | 0.00 | 2027-10-30 | 2027-03-15 | 0.05 | -0.9 |
| 2280560705703031552 | 8.71 | 1.00 | 1.68 | 0.94 | 39 | 2.0 | 0.99 | 0.92 | 2027-04-28 | 2027-10-09 | 0.15 | -3.2 |
| 1378978110276584704 | 8.77 | 0.94 | 1.08 | 0.94 | 24 | 3.1 | 0.99 | 0.98 | 2027-04-17 | 2027-06-22 | 0.06 | -0.6 |
| 1487637106373521280 | 8.92 | 0.97 | 0.61 | 0.95 | 17 | 2.4 | 0.99 | 0.90 | 2027-03-18 | 2026-12-10 | 0.05 | -0.8 |
| 1924030007264636032 | 9.23 | 0.91 | 1.39 | 0.94 | 30 | 2.9 | 1.00 | 0.99 | 2027-06-24 | 2027-10-30 | 0.08 | -0.6 |
| 5755182715519422336 | 9.24 | 1.00 | 1.51 | 0.91 | 21 | 2.6 | 1.00 | 1.00 | 2027-04-21 | 2026-12-23 | 0.04 | -0.8 |
| 1088033417872711680 | 9.29 | 1.00 | 2.05 | 0.94 | 48 | 2.4 | 0.99 | 0.97 | 2027-01-23 | 2027-09-15 | 0.17 | -8.2 |
| 1105311006155685888 | 9.37 | 0.97 | 3.04 | 0.89 | 34 | 4.9 | 1.00 | 1.00 | 2027-04-27 | 2027-03-01 | 0.03 | -0.7 |
| 6331686387431978496 | 9.44 | 0.94 | 1.44 | 0.94 | 32 | 1.3 | 0.94 | 0.91 | 2027-07-06 | 2027-01-08 | 0.23 | -0.5 |
| 2214819118774573440 | 9.54 | 0.96 | 3.00 | 0.92 | 49 | 4.2 | 1.00 | 1.00 | 2027-01-08 | 2027-04-16 | 0.09 | -0.9 |
| 136279144800019456 | 9.75 | 1.00 | 1.53 | 0.92 | 26 | 2.3 | 0.97 | 0.97 | 2027-02-06 | 2027-10-30 | 0.09 | -0.8 |
| 2984269003840680832 | 9.79 | 0.89 | 0.54 | 0.95 | 15 | 1.1 | 0.85 | 0.65 | 2027-03-01 | 2027-10-30 | 0.14 | -0.4 |

## 5. Notes per target and limitations
- **1878822452815621120** (the only "likely substellar" target): the phase is unknown (σ = 0.5 cycle, because P = 1009 ± 138 d), so the timing cannot be planned. One spectrum at a random phase would show doubling under the impostor hypothesis with probability 0.75 (R56k), and two spectra with 0.98. This target also has an SB9 orbit with a 3977 d period (Latham et al. 2002). If the CfA spectra were single-lined, that already argues against a twin at 1009 d. Worth checking before spending telescope time.
- **2994437527894182272**: K_sum is only 11 km/s, so the lines do not separate (p_double = 0). The only usable signal is extra width, about 41% at R56k. Report it as INCONCLUSIVE unless the width test is registered separately.
- **6331686387431978496** and **2984269003840680832**: p_double is 0.64–0.94. Use R = 56 000 where possible.
- **Twin assumption.** L ∝ M^4 (n_spec = 4.3) is a main-sequence approximation. Five targets lie 2.3–8.2 mag above the main-sequence ridge (CMD Δm). For evolved primaries the q solution is not reliable, and an impostor could have a fainter companion that does not produce doubling. Treat a single-lined result for those targets as weaker evidence.
- **Not modelled:** a hierarchical third star, rotation broadening (vsini > 10 km/s would hide doubling), and the T0 error (only the period error is propagated).
- A dark-consistent result cannot exclude an impostor with low f (f < 0.1). Such companions are not the near-twins that our a0 constraint predicts.

## 6. Telescope request
- 15 targets × 2 spectra, plus 2 spectra of 1878822452815621120, plus 1 RV standard per night.
- At about 1 h per spectrum (Kh. Mikailov: G = 7–8 at R ≈ 56 000), that is **about 32–40 h spread over Dec 2026 – Oct 2027**, instead of the 50–65 h in the K-fitting plan.
- Nights in December–January: 5755182715519422336 (2026-12-23), 1487637106373521280 (2026-12-10), 2214819118774573440 (2027-01-08), 6331686387431978496 (2027-01-08), 1088033417872711680 (2027-01-23).
