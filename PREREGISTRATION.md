# Pre-registration — GAIA-FP

**A Gaia-only probabilistic test for stellar-binary impostors among astrometric substellar-companion candidates, evaluated blind on Gaia DR4**

- Author: Omar Abdullayev (Secondary School No. 39, Ganja, Azerbaijan)
- Version: v0.1 DRAFT, 8 October 2026
- **Freeze deadline: before Gaia DR4 release (2 December 2026, ~12:00 CET).** The final version and every hash below must be committed to a public GitHub repository, which provides the timestamp, before that moment. Any change after freezing is reported as a deviation (§9).

## 1. Background and gap

Astrometric orbits from Gaia can be mimicked by unresolved near-equal-mass stellar binaries ("impostors"), whose photocentre wobble is small.

Recent radial-velocity follow-up of Gaia DR3 substellar candidates found a high impostor fraction:
- Marcussen et al. 2026: 13 of 20.
- Barbato et al. 2026: 6 of 14, an estimated contamination of 43 (+13/−11) %.

These authors state that no Gaia-only diagnostic has been validated. Gaia DR4 is the first release with epoch astrometry, epoch RVS radial velocities and line broadening (including double-lined transits), and epoch XP spectra.

## 2. Research questions

- **RQ1.** Can a physics-based Bayesian model using only Gaia observables output a calibrated probability P(impostor | Gaia data) for astrometric substellar candidates?
- **RQ2.** Does the phase-locked RVS line-broadening statistic add discriminating power beyond colour–magnitude (CMD) over-luminosity?

## 3. Hypotheses and falsification criteria

All hypotheses are evaluated on the sealed labelled set (§5), using DR4 data.

- **H1 (discrimination).** The full GAIA-FP score separates impostors from confirmed substellar systems with ROC AUC ≥ 0.80.
  - *Falsified if* the 95% bootstrap CI of the AUC includes 0.5.
- **H2 (added value of RVS).** Among candidates with ≥ 15 RVS epochs, adding the RVS phase statistic increases the impostor rejection fraction at 95% substellar retention, relative to CMD-only.
  - Tested with a paired comparison on the same objects, reported with a bootstrap CI of the difference.
  - *Falsified if* that CI includes 0 **and** the point estimate is ≤ 0.
- **H3 (calibration).** In the pooled synthetic and real evaluation, the Brier score of the full model is lower than that of the CMD-only model.
- **H4 (pipeline validity).** The independent orbit pipeline recovers the published DR4 orbits of Gaia BH3 and Gaia-4 within 2σ in P, e and a0.
  - Already verified on the June 2026 pre-release: BH3 P = 4194 ± 128 d vs 4195 ± 112; e = 0.728 ± 0.006 vs 0.726 ± 0.006; a0 = 27.15 ± 0.67 vs 27.07 ± 0.56 mas.

## 4. Data

- **Gaia DR4** (from 2 December 2026): `epoch_astrometry`, `nss_two_body_orbit`, `gaia_source` (photometry, parallax, RUWE), `rvs_epoch_parameters_single` / `_double` (RV, line broadening), `xp_continuous_mean_spectrum`.
- **Synthetic populations:** Lammers & Winn (2025) DR4 mock exoplanet (7545) and impostor (1151) catalogues, GitHub CalebLammers/GaiaForecasts. These are used for development only. They are **not** used to tune the priors in §6.

## 5. Sealed labelled set

- File: `sealed/labels_v1.json`.
- **SHA-256: `44f30e2279664cdb0c977413cee4ca5117356ef18f7166fcde4e4563f45edb51`**
- Contents: 33 entries.
  - 19 impostors (near-twin SB2).
  - 12 substellar (brown dwarfs or planet, RV-confirmed).
  - 2 unresolved, which are **excluded** from all metrics.
- 7 entries from Barbato et al. 2026 have source_id = PENDING. They will be resolved from the published tables before freezing, then re-sealed as `labels_v2`.
- Sources: Marcussen et al. 2026; Marcussen & Albrecht 2023; Barbato et al. 2026.
- **Honesty note:** the labels were compiled by the analysis team, so blinding relies on *time ordering*. The method, priors and thresholds are frozen before any DR4 feature of any labelled object exists. No DR3 or DR4 feature of a labelled object is inspected before freezing.

## 6. Method (frozen)

1. **Astrometric fit.** A 5-parameter single-star model plus a Keplerian, using Thiele–Innes linearisation. Linear parameters are marginalised analytically, and (P, e, T0) are sampled with MCMC. Errors are inflated so that the reduced χ² = 1.
2. **CMD evidence.** ΔM_G = M_G − M_G,MS(BP−RP). Under H_t, ΔM_G ~ N(μ(q), σ) with q ~ U(0.5, 1), μ = −2.5 log10(1 + q⁴). Under H_p, μ = 0. Here σ is the empirical main-sequence scatter of field stars in the same colour bin, measured from DR4 non-candidate stars.
3. **RVS phase evidence.** S = corr(σ_obs²(t_i), [cos(ν_i + ω) + e cos ω]²), using orbital elements from step 1 only. Then z = atanh(S)·√(n−3). Under H_p, z ~ N(0, 1); under H_t, z ~ N(μ, 1) with μ ~ U(0, 6).
4. **Combination.** log BF = log LR_CMD + log LR_RVS (independent evidence), and P(impostor) = σ(log BF + logit π). The prior π = 0.3 is fixed a priori and is not taken from the labelled set.

## 7. Metrics, baselines and analysis

- **Primary metrics:**
  - ROC AUC with a stratified 95% bootstrap CI (2000 resamples).
  - Impostor rejection at 95% and 90% substellar retention, with Clopper–Pearson 95% CIs.
  - Brier score and a reliability table with 5 bins.
- **Baselines:**
  1. RUWE threshold.
  2. CMD-only likelihood ratio.
  3. A re-implementation of Sahlmann & Gómez (2025), where feasible.
  4. Random scoring (null).
- **Ablations:** CMD only, RVS only, CMD + RVS; and bright (G_RVS ≤ 12) vs faint subsamples.
- **Injection–recovery:** synthetic orbits injected into real DR4 epoch geometry of non-candidate stars. The FAP = 1% detection threshold comes from 400 null simulations per cadence. Completeness is mapped over mass × period × distance.
  - The pre-release result on Gaia-4 cadence, at 50 pc for a 0.64 M☉ star, is 100% completeness for ≥ 2 M_J at P = 250–1200 d.
- **Sample-size caveat:** with about 12 substellar and 19 impostor objects, the rejection-rate CIs will be wide. Precise curves come from the synthetic set; the real set provides external validation.

## 8. Secondary (exploratory, clearly labelled)

- An independent search of DR4 epoch astrometry of nearby stars for substellar candidates not in `nss_two_body_orbit`.
- Any such candidate is reported with its FAP and P(impostor). No candidate is called a "planet" without RV confirmation.

## 9. Deviations policy

Any change after freezing is logged with its date and reason. Results are reported both with and without the change.

## 10. AI-use disclosure

Code drafting and the literature search were assisted by an AI system (Claude, Anthropic). All analysis choices are reviewed, understood and owned by the author. The AI-assisted portions are disclosed on the ISEF forms.

## 11. Frozen file hashes (v0.1 draft; to be recomputed at freeze)

```
f422c294c9680007c0b0d59af9848c393baecce671ffa062acbb6be865096113  gaia_orbit.py
cc1f13fea9a50b40700f30ff333d3eb9a155f146c29e554f2def4e4dbb56af79  fit_real.py
77b1193d2f2dc450789086e8aeb5905134eecdcee96345d24992f6a9ac8483db  mcmc_orbit.py
e00c07b1b24120fb44beb6c85e332be94f8ea31a6533c63adbda1daa231e6077  fp_score.py
9efc580fcee720a3484494aaf8a8e9985a4c1ab3dfb7921f71e498251a80387c  blind_eval.py
b3fc3f7fac3cd4643388162fd5011eb175006e68521fd71ff502deccd2ec274c  rvs_phase_test.py
2e34a6e695c5a4a54e23c0e26e0e24298561c615ebca69f6cb79b32aa5a76334  combo_lr.py
def4edfd12f63105ab85af7253adf04918a62aa4a56a5ce3a87708443a50a69f  inj_rec.py
44f30e2279664cdb0c977413cee4ca5117356ef18f7166fcde4e4563f45edb51  sealed/labels_v1.json
```
