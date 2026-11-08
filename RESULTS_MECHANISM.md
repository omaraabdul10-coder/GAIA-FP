# Mechanism: why Gaia line broadening flags luminous companions

**DATA: REAL, Gaia DR3. Status: DEVELOPMENT.** The confirmatory run is DR4 (amendment v0.6).

- **Plan:** `MECHANISM_PLAN.md`, SHA-256 `bc327170…`, hashed 30 Oct 2026 18:55 UTC, before the code was run. The plan text says "~23:30 UTC+4"; the correct time is 22:55 UTC+4 (deviation 13).
- **Code:** `src/mechanism.py`, tests in `tests/test_mechanism.py`.
- **Outputs:** `results/mechanism.json` and `results/mechanism_scored.csv`; exploratory checks in `results/mechanism_exploratory.json`.
- **Check:** the partial correlations were recomputed with independent code and agree to 10⁻¹⁵.

> **Erratum (31 Oct 2026, finding F6).** The plan's premise, "the first physical model ranked backwards; the SB1 selection fixed it", is wrong. The backwards ranking came from a units bug in the H10 code (K too large by 7.15×). The tests below do not use that code: K is computed here from a1 sin i with P in years and a matching constant. Their results are therefore unaffected. See `RESULTS_DARK_COMPANION.md` (ERRATUM) and deviation 17.

## Sample and per-system physics
- n = 10 118 AstroSpectroSB1 systems with vbroad (≥ 5 transits); 1085 of them are confidently dark (label 0).
- Every system gets three quantities from its own astrometric + RV orbit, with no vbroad used:
  - **light fraction** β̂ = B(1 − ρ);
  - **RV separation** K_sum = K1/B;
  - **blend term** b = β̂(1−β̂)·min(K_sum²·⟨shape²⟩, 30²).

## Pre-registered tests
| Test | Question | Result | Verdict |
|---|---|---|---|
| **M1** | Does vbroad excess rise with the blend term? (partial ρ_s; magnitude, colour, period, e fixed) | **+0.218 [+0.199, +0.237]** | **PASS** |
| M1s | Same, with CMD offset also fixed (A1 youth, A3 evolution) | +0.196 [+0.178, +0.215] | not explained by over-luminosity |
| **M2a** | Dark systems: does the primary's own orbital motion (K1²) broaden lines? (A5) | −0.098 [−0.157, −0.043] | **PASS** (no positive smearing). The negative sign was not predicted and is not explained |
| **M2b** | Is light needed, not just motion? ρ_s(b) − ρ_s(K1²) | **+0.125 [+0.108, +0.144]** | **PASS** |
| **M3** | Selection signature: bright companions depleted *specifically* at large RV separation (SB2 resolution) | D = 1.37 [0.69, 6.26]; log-q prior 1.97 [1.00, 8.88] | **FAIL** |
| M4 | Amplitude: ĉ (theory 4) | 1.79 [1.66, 2.05] | Inside the pre-stated window, but only at its edge (upper bound 2.05 vs window edge 2). The estimate is **half the theory value; this difference is not explained.** Not presented as a success. |
| P0 | Placebo (VB permuted) | 99th percentile of permutations \|ρ\| = 0.024 vs real 0.218 | PASS |

**Pre-stated verdict:**
- **Mechanism B (line blending): consistent with the DR3 development data.** The confirmatory test is on DR4 (H12). It is not called "confirmed" before then.
- **Selection S, as specified: not supported.**
- **Alternative A5: not supported by DR3** (M2a).

## The dose–response curve (poster centrepiece; descriptive; **label on the poster: "DR3 — development data"**, with an empty panel "DR4 — confirmatory, 2 Dec 2026" beside it)
| Blend-term decile | 0–3 | 4 | 5 | 6 | 7 | 8 | 9 |
|---|---|---|---|---|---|---|---|
| median b [(km/s)²] | 0 | 2 | 6 | 11 | 18 | 28 | 57 |
| median vbroad [km/s] | 8.6–9.0 | 9.0 | 9.2 | 9.7 | 10.6 | 11.5 | **14.6** |

Excess against light fraction β̂ (median VB, in units of the field scatter):

| β̂ | 0–0.02 | 0.02–0.05 | 0.05–0.10 | 0.10–0.15 | 0.15–0.20 | 0.20–0.30 | 0.30–0.50 |
|---|---|---|---|---|---|---|---|
| VB | 0.00 | 0.21 | 0.64 | 0.95 | **1.69** | **1.69** | 1.40 |

The excess rises with light fraction and then stops rising above β̂ ≈ 0.2, near where Gaia starts to see two sets of lines. This is descriptive, not a test.

## Exploratory (after the results, NOT pre-registered)
- **E1. Velocity matters at fixed light.** Among systems with β̂ > 0.05 (n = 2489), the velocity term adds +0.10 [+0.06, +0.14] at fixed β̂. Blending needs both light and separation.
- **E2. Why M3 failed.**
  - Bright companions (β̂ ≥ 0.2) are depleted 10–20× in **every** RV-separation bin, not only at large separation.
  - The depletion is *weakest* at large separation: 2.0% → 6.5% observed, against 37% → 44% in the model. This is the opposite of what the SB2-resolution selection predicts.
- **E3. A candidate explanation: label blindness, not catalogue removal.**
  - When the two sets of lines are unresolved, Gaia's RV follows the light-weighted centroid. a1 sin i then shrinks exactly like the photocentre, so ρ → 1, and a luminous blend looks dark. This is the A9 degeneracy (`rv_degeneracy.py`).
  - We added this to the forward model with one untuned run, using the RVS resolution of 26 km/s fixed in advance.
  - It reproduces the **trend**: the bright fraction grows 3.1× from the lowest to the highest separation bin, against 3.2× observed.
  - It does **not** reproduce the **level**: the model is still ~7–10× too high. Possible reasons are the q prior, SB2 detection at all separations, or the NSS pipeline's model choice. Unresolved.
- **Consequence for the project:** ρ labels are blind to light at small RV separation. This is an *identifiability* limit of Gaia itself, and it should be pre-registered as a DR4 prediction (v0.6).

## Power for DR4
- At 80% power and α = 0.05, the minimum detectable partial correlation is r_min ≈ 2.80/√(n − 7).
- To detect half of the DR3 M1 effect (0.109), DR4 needs **n ≥ 668 new systems with vbroad**.
- DR3 had 10 118, so DR4 should exceed this comfortably if it publishes comparable solutions.

## Validation of the M3 statistic (injection–recovery; no vbroad)
| Synthetic catalogue | D | Expected |
|---|---|---|
| Without SB2 removal | 1.13 [0.92, 1.42] | D ≈ 1 |
| With SB2 removal | 0.17 [0.13, 0.22] | D < 0.5 |

The statistic works. The real-data failure of M3 is therefore informative, not a bug.
