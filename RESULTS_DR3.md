# H7-DR3: first real-data results (Gaia DR3 × survey SB2 catalogues)

**DATA: REAL.** Gaia DR3 plus the APOGEE, GALAH and LAMOST-MRS SB2 catalogues, run on 9 Oct 2026.
- Plan: `DR3_STUDY_PLAN.md` (hashed before the run).
- Deviations: `DR3_STUDY_DEVIATIONS.md` §1–6.
- Data: `realdata/PROVENANCE.md`.
- Raw output: `results/dr3_study.json`; per-candidate scores: `results/dr3_candidates_scored.csv`; evidence cards: `results/report_dr3.html`.
- Sealed DR4-test objects were removed before anything was stored, and a code check found 0 of them in the data.

This is **not** the DR4 test. The DR4 test is still blind.

## 1. Sample
- 2138 rows → 2119 unique sources → 2102 scored. The 17 dropped sources have no Thiele–Innes errors (deviation 5).
- Field-star main-sequence ridge: 2541 stars; median scatter σ_CMD = 0.46 mag.
- Survey SB2 matches among the candidates: APOGEE 13, GALAH 2, LAMOST 1. That gives **16 positives**.
- Only 11 candidates fall in the LAMOST-MRS multi-epoch coverage.

## 2. Pre-registered results, reported exactly as specified

| Metric | Result | Pre-registered verdict |
|---|---|---|
| **P1 (primary)**: AUC within the LAMOST-observed sample | n_pos = 1, n_neg = 10 | **UNDERPOWERED** (n_pos < 10); no success or failure claim |
| **P2** positive-unlabelled AUC (16 vs 2086) | GAIA-FP **0.643** [0.487, 0.788]<br>B1 RUWE 0.573<br>**B2 CMD-excess only 0.694 [0.568, 0.813]**<br>B3 0.540<br>B4 random 0.448 | **Not significant**: the CI includes 0.5. GAIA-FP is **not** better than the simple CMD baseline (Δ = −0.05 [−0.16, +0.06]). |
| **P3** recall of survey-SB2 objects | P ≥ 0.85: **14/16** (88%, CI 62–98%)<br>P ≥ 0.5: 16/16<br>ambiguous: 2/16 | High, but **uninformative**: 91% of all candidates are labelled "likely impostor" (see below) |

Verdict counts: likely impostor 1911, ambiguous 174, likely substellar 17. The label-free contamination estimate (mean P) is 0.94.

**Honest reading.** On real DR3 data the full GAIA-FP posterior does **not** beat the one-line CMD-excess baseline. The primary test could not be powered with current survey coverage.

## 3. Exploratory diagnosis (after unblinding; NOT pre-registered)

1. **Is the colour–magnitude calibration biased?**
   - Field stars scored against the ridge have median ΔM = −0.004 mag, and 10% lie below −1.5σ (unresolved field binaries).
   - The candidates have median ΔM = **−0.41 mag**, and **33%** lie below −1.5σ.
   - So the over-luminosity of the candidate population is **real, not a calibration artefact**. A large fraction of DR3 astrometric "substellar" candidates carry a luminous companion. This finding is model-light and label-free.
2. **The prior saturates.**
   - The EM population prior converged to π ≈ 0.94.
   - P(impostor) is ≈ 0.95 even for stars that are *under*-luminous (ΔM/σ > +1).
   - The verdict is therefore driven by the prior, not by the evidence for each star.
3. **The likelihood alone ranks the SB2 objects better than the posterior.**
   - The log-likelihood ratio (CMD term) on its own gives PU AUC 0.722 [0.584, 0.839], against 0.643 for the full posterior.
   - The a0-conditional term is ≈ 0 for all objects: DR3 candidates sit near the 80 MJ cut (median implied m2 = 63 MJ).
4. **But the survey-SB2 labels are biased toward exactly what the CMD term sees.**
   - SB2 detection needs a second, comparably bright set of lines. SB2 positives have median ΔM/σ = **−2.4**, against −0.9 for the other candidates.
   - They are also brighter (median G = 13.2 vs 14.6).
   - So P2 mostly measures the CMD term. It cannot tell whether a high prior is wrong or right.

## 4. Independent physical check (REAL data; exploratory, label rules fixed before comparison)
For the 95 **AstroSpectroSB1** candidates, Gaia also fits the primary's radial-velocity orbit (Thiele–Innes C, H, in AU). That gives the true orbit a1 regardless of light. The comparisons:
- the photocentre-to-orbit ratio **ρ = a0·sin i / (a1·sin i)**: 1 for a dark companion, below 1 for a luminous one;
- the **dynamical companion mass**.

This a0-vs-a1 idea comes from Gaia DR3 itself (Arenou et al. 2023); it is used here only as an independent label. Code: `src/astrospectro_check.py`. Data: `realdata/dr3_astrospectro_ch.csv` (Gaia TAP; transfer verified by SHA-256 of the sorted rows).

| | Result |
|---|---|
| Physically confirmed impostors (m2_dyn > 80 MJ at 97.5% **or** ρ < 0.9 at 97.5%) | **42 / 95** (39 by each criterion) |
| Consistent with a genuine substellar companion | **2 / 95**: Gaia DR3 855523714036230016 (ρ = 1.05, m2 = 71 [64–78] MJ) and 2744694491118490752 (ρ = 1.31, m2 = 46 [37–59] MJ) |
| Undetermined | 51 |
| **Frozen GAIA-FP verdicts** on the 44 determined objects | 40 of 42 impostors → *likely impostor*; 2 → *ambiguous*. Both genuine-consistent objects → *ambiguous*. **No genuine object was called an impostor.** |
| Impostor recall at P ≥ 0.85 | **40/42 = 95% [84%, 99%]** |
| AUC (only 2 negatives: indicative only) | GAIA-FP 0.96; CMD-only 0.99; RUWE 0.29 |

**Reading.**
- Among the determined AstroSpectroSB1 candidates, 42/44 = **95% [85%, 99%] are impostors**. That agrees with the label-free EM estimate (π ≈ 0.94).
- The prior saturation is therefore **supported** by independent dynamical evidence. It is **not** shown to be a defect.
- Caveat: AstroSpectroSB1 objects are biased toward large RV amplitudes, i.e. massive companions.
- Bug found and fixed before any comparison: the first run passed degrees to `np.sin`, which gave a median ρ < 0, which is impossible.

## 5. Population prior: label-free model selection (candidate for v3.2)
`src/prior_select.py` chooses the flexibility of π(x) from a fixed grid. The grid includes a constant prior. The choice is made by 5-fold held-out **observed-data likelihood**, with no labels, and ties go to the simpler model. Results are in `results/prior_eval.json`, using validation mocks only; the DR5 held-out set is not reused.

| Scenario (SIMULATED) | fixed π = 0.3 | EM C = 1 (frozen) | CV-selected |
|---|---|---|---|
| nominal | 0.960 | 0.976 | 0.976 (C = 0.3) |
| CMD scatter 0.45 | 0.909 | 0.953 | 0.953 |
| no RVS | 0.948 | 0.970 | 0.970 |
| covariates carry no information | 0.869 | 0.869 | 0.869 (**C = 0 chosen**) |
| heavy half of mocks | 0.859 | 0.915 | 0.915 |

On real DR3 the selector chose C = 0.3. It confirms the covariate prior (mean π = 0.94); the verdicts change by fewer than 1%.

## 6. Consequences: proposed pre-registration amendment v0.4, to be frozen on OSF before 1 Dec 2026
See `PREREG_AMENDMENT_v0.4.md`. In short:
1. Keep the frozen scoring. Add the label-free prior selection as a **robustness rule**: it never loses on the mocks, and it falls back to a constant prior when covariates are uninformative.
2. Add **H8**: the DR4 AstroSpectroSB1 (combined astrometric + RV) solutions supply independent dynamical labels (ρ and m2_dyn, the rules above).
3. Down-weight survey-SB2 labels to a secondary metric, because they are biased toward twins.
4. Report the CMD-only baseline next to GAIA-FP everywhere: on the current real data it is as good. GAIA-FP's added value must be shown on DR4, where the RVS and a0 terms can act.
