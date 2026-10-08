# Novelty and prior art (review of 9 October 2026)

**How this review was done.** We read abstracts, arXiv HTML pages and journal pages; arXiv PDFs were blocked by the proxy. The working notes, including a list of leads we could not verify, are in `prior_art_notes.md`. **No claim of "first" or "only" is made.** Each item below states the narrow difference that we can actually demonstrate.

## Closest prior work overall

**Bailer-Jones & Kreidberg 2026**, A&A 708, A249, arXiv:2603.03036, "Component masses in stellar and substellar binaries from Gaia astrometry and photometry". We checked the abstract ourselves. They:
- fit Gaia DR3 astrometric orbits together with three-band Gaia photometry, using an isochrone-based mass–flux relation;
- marginalise over age and metallicity;
- treat about 20,000 systems;
- state that this separates near-twin stellar binaries from star–planet systems with Gaia data alone.

**This substantially pre-empts the core idea of using astrometry and photometry jointly to unmask twins.** GAIA-FP must not claim that idea.

## Item-by-item comparison

| GAIA-FP element | Closest prior work | Status | Our narrower, demonstrable difference |
|---|---|---|---|
| Joint a0–CMD likelihood with a shared q | Bailer-Jones & Kreidberg 2026; Shahaf et al. 2019, 2023, 2024 (AMRF triage) | **Done by others** (core idea) | We condition on a0 because candidates are *selected* on a0, and use the result as a calibrated likelihood ratio for a hypothesis test. Our own analysis (`IDENTIFIABILITY_ANALYSIS.md` §3) shows that the coupling adds calibration, not ranking power. |
| Phase-locked RVS epoch line-width test | Marcussen & Albrecht 2023 (ground-based line width vs orbital phase, recommended for impostors); Hadad, Mazeh et al. 2024/2025 (Gaia DR3 vbroad as a binarity indicator) | **Concept published**; application to Gaia **epoch** widths with an orbit-derived template not found | The orbit-driven template [cos(ν+ω) + e cos ω]², a per-candidate physics prediction of the expected signal, and a power map at RVS resolution. This only becomes testable with DR4, which provides per-transit line broadening. |
| "Centroid RVs are degenerate with the photocentre" | Marcussen & Albrecht 2023 | **Essentially known** | Only the quantitative colour factor of about 0.80–0.90. This is a teaching point, not a contribution. |
| Label-free contamination fraction (mixture EM with a covariate prior) | FDR regression (Scott et al., arXiv:1307.3495); VESPA (Morton 2012); TRICERATOPS (Giacalone 2021); Kepler false-positive rates (Fressin 2013; Santerne 2012). Gaia contamination numbers so far come from spectroscopic labels (Barbato 2026: 43%; Marcussen 2026: 13/20) | **Method is standard**; applying it to Gaia astrometric candidates was not found | A demonstration that the likelihood ratios are calibrated enough for the mixture to be identifiable, plus an explicit **non-identifiability boundary**: σ_CMD must be known to about ±20%, and unmodelled third light adds bias. This must be confirmed on DR4 against the labelled fraction (H5). |
| Abstention ("ambiguous") output | Generic reject-option classifiers; exoplanet vetting tools report probabilities | Pieces exist | A validated coverage–error curve for Gaia impostor vetting: held-out 84% decided at 2.0% error. |
| EIG-ranked follow-up | Loredo 2004 (Bayesian adaptive exploration); Ford 2008 (RV scheduling); active-learning follow-up (Ishida 2019; Astudillo 2019) | **Principle known**; not found for Gaia impostor vetting | Ranking candidates for a fixed instrument by EIG resolves 1.5–2.7× more ambiguous candidates than ranking by ambiguity, in a truth-based simulation. The choice of instrument depends on unvalidated assumptions about the metallicity correction. |
| Pre-registration and blind test with sealed labels | Blinding in KiDS-450 (Hildebrandt 2017) and DES (Muir 2020) | Not found for exoplanet candidate vetting | A credibility asset, not a scientific result in itself. |

## Defensible contribution statement (draft)

> We present an evaluation framework for unmasking stellar-binary impostors among Gaia astrometric substellar candidates. It has four parts:
> 1. calibrated per-object likelihood ratios that use only Gaia observables;
> 2. a label-free estimate of the contamination fraction, with its identifiability limits stated;
> 3. a three-way output with a validated coverage–error trade-off;
> 4. information-gain ranking of follow-up targets.
>
> The framework is pre-registered and tested blind on Gaia DR4 against a sealed set of spectroscopically labelled systems.

## Evidence still required before any contribution claim

1. **DR4 blind result on the 65 labelled systems** (H1, H5, H6). Without it, every number above is simulation.
2. **The phase-locked RVS test working on real DR4 epoch widths**, at least for the brightest labelled SB2 impostors.
3. **A comparison against the Bailer-Jones & Kreidberg approach** on the same labelled systems, or an explicit argument why the comparison is not possible.

## Scooping risk

The DR4 papers from the Gaia collaboration (DPAC), due 2 December 2026, may include their own impostor vetting. Lammers & Winn 2025 §V and Marcussen et al. 2026 §3.2/§5.2 could not be read in full and must be checked before submission.
