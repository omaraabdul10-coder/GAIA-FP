# Baseline aliases in Gaia DR3: an independent check with SBX (exploratory, 24 Nov 2026)

Status: exploratory, not pre-registered, no sealed objects (none of the matches is in `realdata/excluded_sealed_ids.csv`). Code: `exploratory/sbx_baseline_alias.py`; data: `realdata/external/sbx_long/`; output: `exploratory/sbx_baseline_alias.json`.

## Question

H21 assumes that Gaia DR3 often fits a ~1000 d orbit to a binary whose real period is much longer. Is that true for stars whose real orbit is known from the ground?

## Data

- SBX (TAP, 24 Nov 2026): every system with at least one orbit longer than 1500 d and a Gaia DR3 position. That gives 679 systems, with all their known orbits.
- Gaia archive (TAP upload, 1″ match, `gaiadr3.nss_two_body_orbit`): 42 orbital solutions, after leaving out one eclipsing-binary solution.

## Result

Of the 42 Gaia solutions, 24 have periods between 600 and 1400 d. Only 3 of those 24 agree (within 25%) with any known orbit of the system, and 4 are 2:1 or 3:1 harmonics. For 14 of them the known orbit is 1.8–25 times longer (median 3.0×) and no known orbit lies near the Gaia period. Twelve of the 14 are RVS (SB1) solutions; two are astrometric: SBX 2188 (Gaia DR3 1878822452815621120, see RESULTS_1878822452815621120.md) and SBX 2551 (Gaia DR3 1717627794711189760, Gaia 1264 d against SBX 4000–4118 d).

Gaia periods that match no known orbit pile up at the baseline: 17 of 28 lie between 600 and 1400 d. If they were real unknown inner orbits spread log-uniformly over 1–1500 d, about 12% would lie there (one-sided binomial p ≈ 7 × 10⁻¹⁰). A real inner orbit only 2–4 times shorter than the outer one would also be dynamically unstable in most cases, so most of these must be aliases.

## This is not new, and that is useful

Merle et al. (2026, MNRAS, arXiv:2602.17870) compared 827 SB9 binaries with Gaia DR3 NSS and found 115 period outliers. They attribute 61 of them to the ~1000 d threshold ("aliasing effect"): Gaia NSS periods saturate around 1000 d, the length of the DR3 data. Our small census reproduces their result with SBX on our own code.

What it gives GAIA-FP:
1. Published, independent evidence for the mechanism behind H21. H21 should cite Merle et al. 2026 in its motivation (a citation, not a change to the test).
2. A gap we can still fill. Merle et al. look at periods. The consequence for planet and brown-dwarf candidates (a long stellar orbit fitted at ~1000 d gives a photocentre orbit that is too small, and so a companion mass that is too low) is what H21 tests on DR4. 1878822452815621120 is the one case of this inside our candidate list.

## Limits

- Only stars that both SBX and Gaia DR3 solved are counted (42 solutions), so the 14/24 rate is for this selection, not for all of Gaia.
- SBX orbits can be incomplete; a few unmatched short periods (3–125 d) may be real inner companions (Merle et al. list such triple candidates).
- Three source ids came back masked by the browser's display filter (SBX 3874, 3941, 3971). Their rows are kept with sn only; re-fetch the ids before any public use.
