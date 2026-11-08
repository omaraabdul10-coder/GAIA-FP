# GAIA-FP prior-art review (compiled 2026-10-09)

Scope: telling true substellar companions apart from unresolved stellar-binary "impostors" among Gaia astrometric-orbit candidates, plus false-positive-probability (FPP) methodology.

How claims were checked: each paper's content was checked against its arXiv abstract page, arXiv HTML full text, or journal or archive page through WebFetch. Where a statement rests only on an abstract, the notes say so. Direct PDF download from arxiv.org was blocked by the proxy, so full-text checks were only possible through arXiv HTML renderings. For papers whose venue appeared only as a DOI, the venue below is inferred from the DOI prefix.

---

## Headline scooping risk

**The closest work to the whole GAIA-FP idea is Bailer-Jones & Kreidberg (2026), A&A 708, A249, arXiv:2603.03036, "Component masses in stellar and substellar binaries from Gaia astrometry and photometry".** It has the following features (checked against the arXiv HTML full text):
- It uses a single Bayesian likelihood over (M1, M2, age, [M/H]):
  - one Gaussian term for the astrometric quantity A = a_p^3/T^2, which depends on both masses and the G-band flux ratio through the van de Kamp photocentre relation;
  - three Gaussian terms for the summed G, BP and RP fluxes, using PARSEC isochrones emulated with gradient-boosted trees.
- The mass–luminosity relation is effectively marginalised, because age and metallicity are sampled.
- It is applied to 20,334 Gaia DR3 orbital NSS systems within 300 pc.
- It explicitly aims to separate near-equal-mass stellar binaries from star–planet systems that have the same astrometric signature.
- It produces 17 exoplanet candidates. Of the 5 that overlap the Stefánsson et al. (2025) radial-velocity (RV) follow-up, 4 are SB2s. The authors state the method "can help to clean exoplanet target lists".
- Appendix B gives only a population-level contamination estimate (about 0.037–0.18 star–star contaminants per star–planet system for FGK primaries, depending on assumptions).
- It gives **no per-object FPP or likelihood ratio between a "stellar binary" and a "substellar companion" hypothesis.**
- It **does not condition on the a0 / significance selection.**
- It **does not use RVS data.** The paper notes that adding the Gaia spectroscopic orbits changes the masses little.

Other 2025–2026 work in this area:
- Marcussen et al. 2026 (arXiv:2609.08590): 13 of 20 candidates are impostors.
- Barbato et al. 2026, GAPS LXXV (arXiv:2606.29001): contamination of 43 (+13/−11)%.
- Lammers & Winn 2025 (arXiv:2511.04673): forecasts for DR4/DR5.
- Venner et al. 2026 (arXiv:2603.19402): follow-up strategy with intermediate-precision RVs.

None of these is a Gaia-only FPP framework. All rely on spectroscopic follow-up or population forecasts.

**Conclusion: no work found that does the full GAIA-FP package**, meaning all of the following together:
- a per-object Gaia-only FPP;
- a selection-conditioned likelihood ratio;
- an RVS-based test for blended SB2s;
- an unlabelled estimate of the contamination fraction;
- abstention and follow-up triage.

Bailer-Jones & Kreidberg (2026) removes the novelty of "astrometry + photometry through a shared mass/flux ratio with the mass–luminosity relation marginalised". GAIA-FP must cite it and position itself against it.

---

## Item 1: Gaia-only Bayesian likelihood-ratio test; a0 and CMD over-luminosity share a latent q; mass–luminosity slope marginalised; conditioned on a0

**Closest prior work (verified):**

1. **Bailer-Jones & Kreidberg 2026**, A&A 708, A249, arXiv:2603.03036 (full text checked through arXiv HTML).
   - Astrometry and 3-band Gaia photometry enter one likelihood.
   - The secondary's flux is modelled. Forcing it to zero biases M2 low by 9% on average.
   - Age and metallicity are free parameters, so the mass–luminosity relation is marginalised.
   - Priors are log-uniform in mass. Posteriors are sampled with emcee.
   - The authors explicitly avoid modelling selection effects.
   - Output is a pair of mass posteriors, not a hypothesis test.
2. **Shahaf, Mazeh, Faigler & Holl 2019**, MNRAS (DOI 10.1093/mnras/stz1636), arXiv:1905.08542 (abstract checked).
   - Defines the AMRF from a0, P, parallax and M1.
   - Sorts systems into three classes (MS secondary, hierarchical triple, compact) using thresholds forward-modelled with a mass–luminosity relation.
3. **Shahaf, Bashi, Mazeh et al. 2023**, MNRAS (DOI 10.1093/mnras/stac3290), arXiv:2209.00828 (PDF text checked through WebFetch).
   - AMRF: 𝒜 = (α0/ϖ)(M1/M☉)^(−1/3)(P/yr)^(−2/3).
   - Photocentre factor: q/(1+q)^(2/3)·[1 − S(1+q)/(q(1+S))].
   - Class probabilities come from Monte Carlo resampling of catalogue errors. There is no likelihood ratio and no stated priors.
   - The mass–luminosity relation is a conservative envelope over MIST isochrones (99.9th percentile), not marginalised.
   - The colour–magnitude diagram (CMD) is used only as a consistency check.
   - Selection on α0 is applied as a cut and not modelled.
   - FDR is controlled with Benjamini–Hochberg at 10%.
4. **Shahaf et al. 2024**, "Triage II: a census of white dwarfs", arXiv:2309.15143 (abstract checked). Uses Gaia synthetic photometry together with the astrometric triage to separate white-dwarf companions from triples. This is photometry plus a0, but for the compact-versus-triple question.
5. **Gaia Collaboration, Arenou et al. 2023**, "Stellar multiplicity", arXiv:2206.05595 (abstract), and the **DR3 `binary_masses` table** (archive documentation checked).
   - For "Orbital+M1", m2 bounds come from fluxratio_lower/upper, the flux ratios that are compatible with both components being on the main sequence.
   - Also includes the AMRFClassIII flag.
   - This is a bounding approach, not a probabilistic one.
6. **Holl et al. 2023**, A&A 674, A10, arXiv:2206.05439 (abstract and full text checked).
   - Describes the exoplanet orbit pipeline. Validation uses significance, consistency with Gaia RVs, and literature.
   - Estimates 5–10% spurious solutions.
   - Assumes a dark companion (photocentre equals the host's orbit). No impostor model.
7. **Sahlmann & Gómez 2025**, MNRAS (DOI 10.1093/mnras/staf018), arXiv:2404.09350 (abstract checked). Machine-learning ranking (anomaly detection plus XGBoost and random forest) of DR3 orbits for low-mass companions, trained on literature substellar companions. Not a physical impostor model. The 3 false positives they report were biased short-period fits of long-period binaries.
8. **El-Badry et al. 2024**, OJAp (DOI 10.33232/001c.125461), arXiv:2411.00088 (abstract checked). A generative forward model of the DR3 astrometric-orbit selection function, released with code (gaiamock). This is the natural tool for conditioning on a0 / significance selection, but it is not used there for per-object FPP.
9. **Andrew, Penoyre et al. 2022**, arXiv:2206.04392 (abstract checked), and **Belokurov et al. 2020**, MNRAS, arXiv:2003.05467 (abstract checked). Infer period and mass ratio from astrometric (RUWE) excess and RV-error excess. Not aimed at substellar impostors.
10. **Hadad, Mazeh, Faigler & Brown 2024**, arXiv:2412.13154 (abstract checked). The over-luminous CMD strip is mostly twin binaries. Relevant for the CMD over-luminosity ingredient.

**Exact differences between GAIA-FP item 1 and Bailer-Jones & Kreidberg (BJK):**
- **(i) Output.** GAIA-FP returns an explicit two-hypothesis likelihood ratio and FPP (substellar versus luminous stellar secondary). BJK returns mass posteriors and cuts on M2 percentiles.
- **(ii) Selection.** GAIA-FP conditions on the a0-based selection. BJK does not. This is the cleanest unclaimed piece.
- **(iii) Mass–luminosity treatment.** GAIA-FP marginalises an explicit slope. BJK marginalises age and [M/H] through an isochrone emulator. These are functionally similar.
- **(iv) What photometry measures.** GAIA-FP uses over-luminosity relative to a single-star locus. BJK fits absolute fluxes in 3 bands. These are similar in information content.

**Verdict:** (b) partially done. The core "shared q links a0 and photometric excess, with the mass–luminosity relation marginalised" is already in BJK 2026, and the a0–q–S relation goes back to van de Kamp and Shahaf et al. (2019).

**Evidence needed to claim a contribution:**
- Show that the selection-conditioned likelihood ratio is better calibrated than BJK-style posteriors on spectroscopically labelled impostors and confirmed companions. Usable labels:
  - Stefánsson et al. 2025;
  - Marcussen & Albrecht 2023;
  - Marcussen et al. 2026;
  - Barbato et al. 2026;
  - Unger et al. 2023.
- Report reliability diagrams and Brier or log scores, comparing against BJK (whose catalogue is in VizieR J/A+A/708/A249) and against the AMRF.
- Quantify the effect of conditioning on a0 with injection–recovery through gaiamock.

## Item 2: Gaia RVS epoch line broadening correlated with astrometric orbital phase (template [cos(ν+ω)+e cos ω]^2)

**Closest prior work (verified):**
1. **Marcussen & Albrecht 2023**, AJ (DOI 10.3847/1538-3881/acd53d), arXiv:2305.08623 (full text checked through arXiv HTML).
   - Section 3.2: when the two sets of lines are not separated, the RV shift "may be identified as a change of the line width".
   - Section 4.1 (HD 68638): fits FWHM against orbital phase.
   - Section 4.3 (HIP 66074): no change in FWHM with phase, used to rule out a twin.
   - The conclusion recommends checking "the correlation of the FWHM with orbital phase" to reveal impostors.
   - Also uses DR3 vbroad: median 15.9 km/s for flux ratio > 0.25 versus 10.9 km/s below. They note vbroad exists only for G ≲ 12.
   - **This is the concept of item 2, done with ground-based spectra and qualitative phase fitting.**
2. **Hadad et al. 2024**, arXiv:2412.13154 (abstract checked). DR3 vbroad is statistically broader for CMD-selected twin binaries. Population-level, with no epoch or phase information.
3. **Frémat et al. 2023**, A&A 674, A8 (journal page checked). DR3 vbroad. About 40,000 suspected SB2 candidates were flagged and not processed. Binarity was ignored as a broadening source.
4. **Gaia DR3 SB2 processing** (archive documentation): 2D TODCOR-type detection of composite spectra in RVS epoch data. Line-width variations are not used for detection.
5. **Bashi & Tokovinin 2024**, arXiv:2411.17819 (abstract checked). Compares Gaia RV peak-to-peak amplitude with the astrometric semi-amplitude to flag compact hierarchical triples. Uses centroid RVs, not line widths.
6. **Chance et al. 2022/2024 ("paired")**, arXiv:2206.11275 (abstract checked). Forward-models Gaia RV noise to give per-star binary probabilities. Uses centroid RV scatter, not line widths.
7. **Gaia DR4 content page** (cosmos.esa.int/web/gaia/dr4, checked). DR4 is planned for 2 December 2026. It will include:
   - `rvs_epoch_parameters_single`: per-transit RV and line broadening, about 6.9 billion rows;
   - `rvs_epoch_parameters_double`;
   - `rvs_epoch_spectrum`: per-transit RVS spectra;
   - `epoch_astrometry`.

   So nobody can yet have applied item 2 to real Gaia epoch data.

**Searches found no work that fits a phase-locked broadening template, derived from the Gaia astrometric orbit, to Gaia RVS per-transit widths, and none forecasting this for DR4.**

**Verdict:** (b) partially done. The physical idea (FWHM varies with orbital phase for blended twins) and the recommendation to test for it are in Marcussen & Albrecht (2023). What looks new is:
- the analytic template [cos(ν+ω) + e cos ω]^2, driven by the Gaia astrometric orbit;
- a matched-filter statistic applied to Gaia RVS epoch broadening;
- sensitivity calculations at RVS resolution (R ≈ 11,500), as an all-Gaia test.

**Evidence needed:**
- Derive the template, including how much broadening RVS can detect given intrinsic vsini, signal-to-noise and resolution.
- Run injection–recovery on simulated RVS transits.
- Validate on known SB2 impostors after DR4, or on DR3 SB2/AstroSpectroSB1 systems.
- Show the template detects impostors that the DR3/DR4 SB2 pipeline misses (blended regime).
- Bring in DR4 data quickly: DPAC or others could publish this soon after 2 December 2026.

## Item 3: blended-line centroid RVs reproduce photocentre motion (K_centroid ≈ K_sum(B − f)), so they are degenerate with astrometry while line widths are not

**Closest prior work (verified):**
- **Marcussen & Albrecht 2023** (arXiv:2305.08623, HTML checked).
  - Section 3.2: the midpoint of a blended line shifts slightly depending on flux and rotation differences.
  - Fig. 4 simulates the ratio of RV-derived to astrometry-derived mass.
  - Conclusion: the wavelength shift of unresolved lines is dimmed "in almost perfect proportion to the astrometric dimming", so "both the astrometric and RV data may falsely – but consistently between the data sets – indicate the presence of an orbiting exoplanet".
  - Eq. 2–4 give a0 = a|1/(1+ε) − 1/(1+q)|.
  - They give no explicit centroid-RV formula.
- **Photocentre relations are standard:** van de Kamp (1956), as cited by BJK 2026, and Shahaf et al. 2019/2023.
- **Consistency tests between centroid RVs and astrometry are used:**
  - Holl et al. 2023 (consistency with Gaia RVs in validation);
  - Bashi & Tokovinin 2024 (RV amplitude versus astrometric amplitude).
- **Implication of item 3 for this prior work:** for blended twins these tests are by construction uninformative, a point not made explicitly in any paper I could verify.

**Note:** in the linear flux-weighted limit the identity is exact and elementary.
- v_c = (1−B)·f·v_rel − B(1−f)·v_rel = (f − B)·v_rel, with f = M2/M and B = L2/L.
- This is the same factor that sets a0/a.
- On its own it is unlikely to count as a publishable contribution.

**Verdict:** (b) partially done / essentially known. The qualitative statement and a simulation exist (Marcussen & Albrecht 2023). An explicit derivation is likely in older SB/blending literature but was not verified.

**Evidence needed to claim a contribution:**
- An explicit derivation with the conditions under which it fails: unequal line widths or vsini, line-profile asymmetry, finite velocity separation relative to the RVS resolution element, and template mismatch.
- A quantitative statement of when Gaia's combined astrometric–spectroscopic (AstroSpectroSB1) solutions and RV-consistency checks are blind to twins.
- The corollary that second moments (widths) break the degeneracy. This motivates item 2.

## Item 4: label-free estimation of the impostor fraction with an EM mixture over per-object likelihood ratios and a covariate-dependent prior

**Closest prior work (verified unless noted):**
- **Gaia-specific contamination estimates (all from spectroscopic labels, not label-free):**
  - Barbato et al. 2026 (arXiv:2606.29001): 6 of 14, about 43 (+13/−11)%;
  - Marcussen et al. 2026 (arXiv:2609.08590): 13 of 20 impostors;
  - Stefánsson et al. 2025 (arXiv:2410.05654): 21 of 28 ruled out as stellar binaries (abstract);
  - Marcussen & Albrecht 2023: 3 of 5.
  - Forecast: Lammers & Winn 2025 (arXiv:2511.04673; AJ, IOP page found) expect planets to outnumber impostors by at least 5, but about 50% false positives for M dwarfs with a < 1 au.
  - BJK 2026 Appendix B gives a prior-driven population estimate.
- **Shahaf et al. 2023:** controls the false discovery rate per class with Benjamini–Hochberg. This is frequentist and does not estimate the mixing fraction.
- **Transit FPP literature:**
  - Morton & Johnson 2011 (arXiv:1101.5630);
  - Morton 2012, VESPA (arXiv:1206.1568);
  - Fressin et al. 2013 (arXiv:1301.0842);
  - Santerne et al. 2012 (arXiv:1206.0601);
  - Giacalone & Dressing 2021, TRICERATOPS, AJ 161, 24 (arXiv:2002.00691);
  - Bryson et al. 2020 (arXiv:1906.03575), Kepler reliability folded into occurrence rates.
  - These use astrophysical priors from population synthesis, or reliability from injected/inverted data, rather than an EM fit of the mixing fraction on the candidates' own likelihood ratios.
- **Statistics:**
  - Efron's two-groups / local-FDR model (not separately verified here);
  - FDR regression with covariate-dependent prior: Scott, Kelly, Smith, Zhou & Kass, arXiv:1307.3495. The ar5iv title was confirmed. The JASA 2015 venue is from memory and not verified.
  - **This is essentially the statistical method of item 4.**

**Verdict:** (b) partially done. The statistical machinery (two-groups mixture with covariate-modulated prior, fitted by EM) is standard (FDR regression). No application was found to Gaia astrometric candidates, or that turns per-object Gaia likelihood ratios into an unlabelled contamination estimate.

**Evidence needed:**
- Show that the label-free EM estimate agrees with the spectroscopically labelled impostor fractions (Barbato, Marcussen, Stefánsson) within errors, on the overlapping subsample.
- Show it is identifiable: either the per-object likelihood ratios are calibrated, or misspecification is addressed.
- Show the covariate dependence (for example spectral type, P, a0) reproduces Lammers & Winn's M-dwarf, a < 1 au trend.
- Cite the two-groups/FDR-regression literature. Do not claim the method itself.

## Item 5: "ambiguous" abstention outputs and expected-information-gain (EIG) follow-up prioritisation

**Closest prior work (verified):**
- **Bayesian adaptive design for RV and astrometric planet observations:**
  - Loredo 2004, "Bayesian Adaptive Exploration" (astro-ph/0409386; DOI 10.1063/1.1751377);
  - Ford 2008, AJ 135, 1008, "Adaptive Scheduling Algorithms for Planet Searches" (astro-ph/0412703);
  - Loredo et al. 2011, Statistical Methodology (arXiv:1108.0020).
  - These choose observation times to learn orbits. They do not choose which candidates to observe in order to settle planet versus impostor.
- **Choosing follow-up by information for classification:**
  - Astudillo et al. 2019, AJ (arXiv:1911.02444): information-theoretic choice of spectroscopic follow-up for variable-star classification;
  - Ishida et al. 2019, MNRAS (arXiv:1804.03765): active learning for supernova spectroscopic follow-up.
- **Gaia-specific follow-up strategy:** Venner et al. 2026 (arXiv:2603.19402), a qualitative argument for intermediate-precision RVs. No EIG ranking.
- **Abstention / reject option:** no astronomy vetting paper with explicit selective classification ("ambiguous" class with a coverage–risk trade-off) was verified. Transit validation pipelines use fixed FPP thresholds (e.g. FPP < 1% to validate), which leaves an implicit "unvalidated" middle band, but they are not framed as abstention.

**Verdict:** (b/c). Pieces exist separately in astronomy (EIG for scheduling; information-based follow-up for classification). No combined application was found to Gaia astrometric candidates, nor an explicit abstention framework for exoplanet vetting.

**Evidence needed:**
- A risk–coverage curve on labelled systems.
- A retrospective simulation showing EIG-ranked follow-up resolves more planet-versus-impostor cases per night than ranking by FPP or a0/SNR. The real Barbato, Marcussen and Stefánsson outcomes can serve as a replay benchmark.
- Credit Loredo, Ford, Astudillo and Ishida.

## Item 6: pre-registration and blind evaluation

**Prior work (verified):**
- Blind analysis is standard in particle physics (Klein & Roodman 2005, Annu. Rev. Nucl. Part. Sci., DOI 10.1146/annurev.ns.55.121205.200001; found, abstract not read). It is also standard in weak-lensing cosmology:
  - KiDS-450, Hildebrandt et al. 2017 (arXiv:1606.05338; abstract says "The cosmology analysis was performed blind");
  - DES, Muir et al. 2020, MNRAS (arXiv:1911.05929).
- Blind data challenges in exoplanets exist: Dumusque et al. 2016/2017 RV fitting challenge (arXiv:1607.06487; title only verified).
- **No pre-registered exoplanet or Gaia vetting study was found.**

**Verdict:** (c) in the exoplanet/Gaia vetting context. This is a methodological practice, not a scientific contribution. It is a credibility asset, not a novelty claim.

**Evidence needed:**
- A timestamped registration (OSF or Zenodo) made before the DR4 release (2 December 2026) or before labels were revealed.
- An evaluation that follows the registered protocol exactly, with any deviations listed.

---

## Verified references
(Venue taken from the abstract or journal page, or inferred from the DOI where noted.)

- Andrew, S., Penoyre, Z., Belokurov, V., Evans, N. W., Oh, S. 2022, arXiv:2206.04392. "Binary parameters from astrometric and spectroscopic errors…"
- Astudillo, J., Protopapas, P., Pichara, K., Huijse, P. 2019, AJ (DOI 10.3847/1538-3881/ab557d), arXiv:1911.02444.
- Bailer-Jones, C. A. L., Kreidberg, L. 2026, A&A 708, A249 (DOI 10.1051/0004-6361/202659004), arXiv:2603.03036.
- Barbato, D., Pinamonti, M., Sozzetti, A., et al. 2026, "GAPS LXXV. Validating and confirming Gaia substellar astrometric candidates with HARPS-N", arXiv:2606.29001.
- Barbato, D., Ségransan, D., Udry, S., et al. 2023, A&A (DOI 10.1051/0004-6361/202345874), arXiv:2303.16717 (CORALIE XIX).
- Bashi, D., Tokovinin, A. 2024, arXiv:2411.17819.
- Belokurov, V., Penoyre, Z., Oh, S., et al. 2020, MNRAS (DOI 10.1093/mnras/staa1522), arXiv:2003.05467.
- Bryson, S., et al. 2020, arXiv:1906.03575 (title verified from search result only).
- Chance, Q., Foreman-Mackey, D., Ballard, S., et al. 2022 (v2 2024), arXiv:2206.11275 ("paired").
- Chevalier, S., Babusiaux, C., Merle, T., Arenou, F. 2023, A&A (DOI 10.1051/0004-6361/202347111), arXiv:2307.16719.
- El-Badry, K. 2024, "Gaia's binary star renaissance", arXiv:2403.12146.
- El-Badry, K., Lam, C., Holl, B., et al. 2024, OJAp (DOI 10.33232/001c.125461), arXiv:2411.00088.
- Ford, E. B. 2008, AJ 135, 1008 (DOI 10.1088/0004-6256/135/3/1008), astro-ph/0412703.
- Frémat, Y., Royer, F., Marchal, O., et al. 2023, A&A 674, A8.
- Fressin, F., et al. 2013, arXiv:1301.0842 (title verified from search result).
- Gaia Collaboration, Arenou, F., et al. 2023, "Stellar multiplicity, a teaser for the hidden treasure", arXiv:2206.05595 (A&A, DOI 10.1051/0004-6361/202243782).
- Gaia DR3 archive documentation, `binary_masses` data model (gea.esac.esa.int).
- Gaia DR4 content page, cosmos.esa.int/web/gaia/dr4 (accessed 2026-10-09).
- Giacalone, S., Dressing, C. D., et al. 2021, AJ 161, 24, arXiv:2002.00691 (TRICERATOPS).
- Hadad, E., Mazeh, T., Faigler, S., Brown, A. G. A. 2024, "Gaia vbroad: Spectral-line broadening, and binarity", arXiv:2412.13154.
- Hadad, E., Mazeh, T., Faigler, S. 2025, A&A 701, A195.
- Hallakoun, N., Shahaf, S., Mazeh, T., Toonen, S., Ben-Ami, S. 2024, ApJL (DOI 10.3847/2041-8213/ad5e63), arXiv:2311.17145.
- Hildebrandt, H., Viola, M., Heymans, C., et al. 2017, arXiv:1606.05338 (KiDS-450, blind).
- Holl, B., Sozzetti, A., Sahlmann, J., et al. 2023, A&A 674, A10, arXiv:2206.05439.
- Ishida, E. E. O., et al. 2019, MNRAS (DOI 10.1093/mnras/sty3015), arXiv:1804.03765.
- Lammers, C., Winn, J. N. 2025, "On the Exoplanet Yield of Gaia Astrometry", arXiv:2511.04673 (AJ, DOI 10.3847/1538-3881/ae21de).
- Loredo, T. J. 2004, "Bayesian Adaptive Exploration", astro-ph/0409386 (DOI 10.1063/1.1751377).
- Loredo, T. J., Berger, J. O., Chernoff, D. F., Clyde, M. A., Liu, B. 2011, arXiv:1108.0020 (DOI 10.1016/j.stamet.2011.07.005).
- Marcussen, M. L., Albrecht, S. H. 2023, AJ (DOI 10.3847/1538-3881/acd53d), arXiv:2305.08623.
- Marcussen, M. L., Albrecht, S. H., Kalinowski, K. K., Winn, J. N., Stefánsson, G., et al. 2026, arXiv:2609.08590.
- Merle, T., Jorissen, A., et al. 2026, arXiv:2602.17870 (SB9 versus DR3 NSS).
- Morton, T. D. 2012, arXiv:1206.1568 (VESPA method).
- Morton, T. D., Johnson, J. A. 2011, arXiv:1101.5630.
- Muir, J., et al. 2020, MNRAS, arXiv:1911.05929 (DES blinding).
- Müller-Horn, J., Rix, H.-W., El-Badry, K., et al. 2025/2026, arXiv:2510.05982 (forward model of RUWE and RV scatter).
- Nachmani, G., Faigler, S., Mazeh, T. 2026, arXiv:2602.05610 (MESS, SB2 detection).
- Pinamonti, M., Sozzetti, A., Barbato, D., et al. 2025, arXiv:2512.04606 (GAPS LXX, Gaia-6 B).
- Sahlmann, J., Gómez, P. 2025, MNRAS (DOI 10.1093/mnras/staf018), arXiv:2404.09350.
- Salazar, W. B., Giacalone, S., Howard, A. W. 2026, arXiv:2609.09734.
- Sandave, P., Garani, R. 2026, arXiv:2609.24321.
- Santerne, A., et al. 2012, arXiv:1206.0601 (SOPHIE / Kepler false-positive rate).
- Scott, J. G., Kelly, R. C., Smith, M. A., Zhou, P., Kass, R. E., arXiv:1307.3495 ("False discovery rate regression").
- Shahaf, S., Mazeh, T., Faigler, S., Holl, B. 2019, MNRAS (DOI 10.1093/mnras/stz1636), arXiv:1905.08542.
- Shahaf, S., Bashi, D., Mazeh, T., et al. 2023, MNRAS (DOI 10.1093/mnras/stac3290), arXiv:2209.00828.
- Shahaf, S., Hallakoun, N., Mazeh, T., et al. 2024, arXiv:2309.15143 (Triage II).
- Stefánsson, G., Mahadevan, S., Winn, J. N., Marcussen, M., et al. 2025, arXiv:2410.05654 (Gaia-4b/5b).
- Unger, N., Ségransan, D., Barbato, D., et al. 2023, A&A 680, A16 (DOI 10.1051/0004-6361/202347578).
- Van Zandt, J., et al. 2026, ApJ, GEODES I (found through an astrobites post and an arXiv HTML link to 2605.23018). The abstract itself was not read.
- Venner, A., Huang, C. X., Latham, D. W., et al. 2026, arXiv:2603.19402.
- Wallace, A. L., Casey, A. R. 2026, arXiv:2601.03539.

## Unverified leads (not checked; do not cite without checking)

- **Venues and details from memory or titles only:**
  - Klein & Roodman 2005, Annu. Rev. (found, abstract not read).
  - Dumusque et al. RV fitting challenge (arXiv:1607.06487, title only).
  - Morton et al. 2016, Kepler FPPs (arXiv:1605.02825 seen in results, not read).
  - Scott et al. FDR regression, JASA 2015 venue.
  - Efron (2001/2008) local FDR.
  - Chow (1970) reject option.
- **Older derivations of luminosity-weighted RV for blended SB2s.** Likely exists (e.g. eclipsing-binary line-blending literature). No specific paper was verified.
- **Damerdji et al. DR4 SB2 pipeline paper.** Not found. The DR3 SB2 documentation only describes 2D cross-correlation.
- **"Frankel et al." on Gaia RVS unresolved binaries.** Not found in searches.
- **Penoyre et al. 2022 "astromet" / "Gaia unresolved binaries II".** Not checked.
- **2025–2026 DPAC DR4 exoplanet-pipeline papers.** Expected with DR4 (2 December 2026). They may include impostor vetting and are the **main future scooping risk for items 1–2.**
- **Lammers & Winn 2025, Section V (impostor model).** Could not be read: the HTML text was truncated and the PDF was blocked. Whether they suggest CMD or RVS vetting is unknown.
- **Marcussen et al. 2026, Sections 3.2 and 5.2 (vetting and false-positive discussion).** Not visible in the HTML fetch. These may discuss Gaia-only diagnostics; check before submission.
- **emergentmind.com "open problems" page on DR4/DR5 impostor incidence.** Not a primary source.
