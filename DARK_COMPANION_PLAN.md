# H9 / H10: is the companion dark? A plan written BEFORE any data download

**Written:** 9 Oct 2026, ~13:20 UTC+4. Its SHA-256 is computed and stored before the data are downloaded. This plan extends the frozen OSF registration ([10.17605/OSF.IO/N5H4B](https://doi.org/10.17605/OSF.IO/N5H4B)); it does not change it. All data are Gaia DR3, which is development data with respect to the frozen DR4 test. The DR4 evaluation set stays blind.

## Why
Two gaps in the frozen project:
1. The line-width (RVS) channel, our most original element, has not been tested on real data.
2. On real DR3, the CMD-only baseline matched GAIA-FP.

DR3 has no epoch line widths, but it does publish **vbroad**: the line broadening fitted to the *combined* RVS spectrum of all transits. When a binary's two sets of lines move apart and together along the orbit, the time-averaged blend is broader than either star. That is the time-averaged form of our phase-locked test, and it can be predicted for each system from its own orbit.

## Broader question
"Is the astrometric companion dark?" is the same question for:
- planets and brown dwarfs (impostor vetting);
- white dwarfs, neutron stars and dormant black holes.

## Closest prior work (to be cited; novelty is NOT claimed for these ideas)
- Shahaf et al. 2019, 2023, 2024 (AMRF "triage"): classify Gaia astrometric companions as main-sequence, possible triple, or likely compact, using a0, M1 and P.
- "Gaia vbroad. Spectral-line broadening and binarity" (arXiv:2412.13154): vbroad is inflated in binaries.
- Gaia DR3 binary_masses (Arenou et al. 2023): the a0-vs-a1 flux constraint for AstroSpectroSB1 solutions.

**Our possible contribution:**
- a per-system physical *prediction* of the blend broadening, from the orbit and the q posterior;
- a single likelihood combining CMD, astrometry and line width;
- calibration against physical labels at scale;
- pre-registration.

The claim is limited to whatever H9/H10 show.

## Data (Gaia archive TAP; sealed source_ids dropped in the browser before saving, as in the DR3 study)
- **D1:** the DR3 substellar candidates (same query as `DR3_STUDY_PLAN.md`) plus `vbroad`, `vbroad_error`, `vbroad_nb_transits`, `grvs_mag`, `rv_amplitude_robust`, `rv_nb_transits` from `gaia_source`.
- **D2:** field calibration. TOP 30000 stars with vbroad not null, `non_single_star` = 0, RUWE < 1.2, parallax_over_error > 10, random_index ordering. Columns: bp_rp, grvs_mag, vbroad, vbroad_error, phot_g_mean_mag, parallax.
- **D3:** every `nss_two_body_orbit` solution of type AstroSpectroSB1 with parallax_over_error > 10. Columns:
  - A, B, F, G, C, H and their errors;
  - period, eccentricity, t_periastron, parallax and their errors;
  - G, bp_rp, vbroad, vbroad_error, grvs_mag;
  - binary_masses m1, m1_lower, m1_upper (left join).

## Sample cuts (fixed now)
- One row per source.
- bp_rp inside the field ridge range.
- Main sequence: M_G > ridge(bp_rp) − 2.0.
- m1 available.
- **For vbroad analyses only:** vbroad not null and vbroad_nb_transits ≥ 5.

## Labels (physical, from C and H; rule frozen as amendment A3)
- **Luminous companion:** m2_dyn 2.5% > 80 MJ is NOT used here, because H10 spans all masses. The label is luminous if ρ 97.5% < 0.9.
- **Dark-consistent:** ρ 2.5% > 0.9.
- **Otherwise:** undetermined, and excluded.
- **Known limitation:** for a near-twin blend the RV centroid can be diluted like the photocentre (`rv_degeneracy.py`), which pushes ρ toward 1. The "dark-consistent" class may therefore contain some twins. This biases every method's AUC *down* equally; it does not favour any method.

## Scores (none tuned on these labels)
| ID | Score | Uses a0? |
|---|---|---|
| B2 | CMD only: −ΔM_G/σ_CMD | no |
| AMRF | a0 / (ϖ · M1^(1/3) · P^(2/3)), with the sign chosen so that low = luminous | yes |
| VB | vbroad excess only: (vbroad − field median(bp_rp, grvs))/robust σ | no |
| S1 | CMD-LR + vbroad-LR, with q posterior from ΔM_G only | **no** |
| S2 | full GAIA-FP: joint a0\|CMD LR + vbroad-LR (q posterior from a0 and ΔM_G) | yes |

**vbroad-LR (fixed now):**
- Under H_t: vb_pred² = vb_int² + c · f(1−f) · ⟨Δv²⟩, where
  - ⟨Δv²⟩ = K_sum² · ⟨(cos(ν+ω) + e·cos ω)²⟩ is the time average over the orbit;
  - f = β is the RVS-band light fraction, taken as the G-band β (a stated approximation);
  - c = 1;
  - vb_int is drawn from the field distribution in the same colour bin.
- Under H_dark: vb = vb_int, because a dark companion adds no lines.
- Likelihood: Gaussian in vbroad with σ² = vbroad_error² + field robust σ², marginalised over q draws (40 per system).
- **No parameter is fitted to labels.**

## Metrics and pre-stated criteria
- **H10a (primary, clean):** on the vbroad subset of D3, the paired-bootstrap ΔAUC(S1 − B2) has a lower 95% bound > 0.
- **H10b:** VB alone has AUC with a lower 95% bound > 0.5.
- **H10c (secondary, flagged for shared a0 input):** AUC of S2 and of AMRF vs B2.
- **H9 (candidates, D1):**
  - vbroad coverage of the 2102 candidates;
  - among candidates with vbroad, AUC of VB and S1 for (a) survey-SB2 PU labels and (b) AstroSpectroSB1 dynamical labels where available.
  - H9 is reported as **exploratory** if fewer than 10 positives.
- Bootstrap: 2000 resamples, stratified, seed 7.
- All numbers are reported whatever their sign. If H10a fails, the conclusion is "the time-averaged line width adds nothing beyond CMD in DR3".

## Not changed
The frozen OSF registration and its files. This plan is a development study; any resulting method change for DR4 needs a new dated amendment before 2 Dec 2026.
