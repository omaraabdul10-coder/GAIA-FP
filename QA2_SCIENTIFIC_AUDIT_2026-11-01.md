# GAIA-FP v0.6 / QA2 — scientific and reproducibility audit

**Audit date:** 1 November 2026  
**Scope:** local project snapshot, archived DR3 outputs, reproducibility tests, and supplementary statistical diagnostics.  
**This is an audit addendum, not a new preregistration and not a claim of Gaia DR4 validation.**

## Executive result

The working project is materially more reproducible than the previously supplied QA2 snapshot. The primary software test suite passes 112 tests; the separate geometry/statistics audit passes 65 tests with 35 expected xfails. We recovered the local H6 source preregistration, reproduced the H11 control group, completed 10,000-replicate synthetic null-calibration audits for AUC and paired ΔAUC, and quantified seed sensitivity in the 95-object DR3 dynamical-label sample.

The most important scientific caution is unchanged: the DR3 survey-SB2 test was underpowered and did not show GAIA-FP beating the simple CMD baseline; the 95-object dynamic sample is selected and small; simulation does not substitute for real DR4 validation.

## 1. Software and numerical test suite

| Check | Result | Meaning |
|---|---:|---|
| `PYTHONPATH=src pytest -q` | **112 passed** | Main tests, including the QA2 guard, H12 preparation, H6 mechanics and offline fetch-contract tests. |
| `PYTHONPATH=src pytest -q audit/tests_geometry.py audit/tests_stats.py` | **65 passed; 35 expected xfails; 14 warnings** | Separate geometry/statistics audit suite. The xfails are documented edge cases; warnings are emitted by degenerate-input guards. |
| H11 control seed-11 reproduction | **Exact** | Reconstructed control CSV matches archived result byte-for-byte. |
| H8/A3 historical 400-draw reproduction | **Exact for seed 0** | The seed-sweep runner reproduces the historical label CSV without overwriting it. |

The two pytest suites completed separately. They are not added into a single combined test count.

## 2. H11 DR3 control-group reproduction and balance sensitivity

The registered local DR3→DR4 plan defines a control group from DR3 `nss_two_body_orbit` `Orbital` and `AstroSpectroSB1` solutions with implied dark-companion mass between 80 and 300 Jupiter masses. Every one of the 2,102 candidates is matched to one control by nearest neighbour in `(G, log P, significance)`, without replacement, with registered seed 11.

Reconstruction from the supplied raw DR3 table:

- Raw source rows: **71,759**.
- Eligible control pool after the plan's cuts: **31,349**.
- Candidate sample: **2,102**.
- Matched controls: **2,102**, all unique.
- Candidate/control overlap: **0**.
- Sealed-ID/control overlap: **0**.
- Registered seed 11: exact row-level reproduction of archived control CSV.

Random-order sensitivity over seeds 1–12 retained small standardized mean differences:

| Covariate | SMD range |
|---|---:|
| G magnitude | 0.02872 to 0.02987 |
| log10(period) | −0.01359 to −0.01058 |
| significance | 0.01176 to 0.01463 |

**Interpretation:** observed-covariate matching is balanced and reproducible. However, the 80–300 MJ selection relies on an approximate first-order mass proxy, not a verified dynamical mass label. This is a matched DR3 control preparation for the time-separated DR4 stability analysis; it is not a DR4 outcome or a measurement of single-star false-positive rate.

Artifacts: `tools/qa_audits/audit_h11_control_matching.py`, `results/qa2/h11_matching_sensitivity.json`.

## 3. H8 / independent dynamical labels: seed stability

The historical 95-object DR3 check contains 42 dynamical impostor labels, 2 dark-companion-compatible labels, and 51 indeterminate objects. A five-seed audit with the existing 400-draw A3 procedure produced:

| Seed | Impostor | Dark-compatible | Indeterminate | Agreement with historical seed 0 |
|---:|---:|---:|---:|---:|
| 0 | 42 | 2 | 51 | 100.0% |
| 1 | 42 | 2 | 51 | 97.9% |
| 2 | 42 | 2 | 51 | 93.7% |
| 3 | 43 | 2 | 50 | 98.9% |
| 4 | 40 | 2 | 53 | 97.9% |

**88/95** objects had labels unchanged across all five seeds; **7** were seed-sensitive. In this small labelled subset, the GAIA-FP posterior AUC was about 0.963–0.965, while B2 CMD AUC was about 0.976–0.988. This does not support a claim that GAIA-FP beats the CMD baseline on this DR3 subset.

### Higher-draw sensitivity diagnostic

A separate, supplementary diagnostic used 50,000 draws for both the dynamical-ratio and mass calculations, across seeds 0, 1 and 17:

- Counts: seed 0 = 42 / 2 / 51; seed 1 = 42 / 2 / 51; seed 17 = 41 / 2 / 52.
- **94/95** labels agree across all three high-draw seeds; one object is seed-sensitive.
- Relative to the historical 400-draw labels, 2, 2 and 3 labels change for seeds 0, 1 and 17 respectively.
- Vectorized mass-root bisection was checked against `scipy.brentq` on 1,000 random parameter tuples; maximum relative difference was `1.09 × 10⁻¹⁰`.

Code inspection found that the historical A3 implementation samples `rho` using all configured draws but calculates the companion-mass interval from only the first 150 draws. The high-draw diagnostic uses all draws for both quantities and is intentionally kept separate. It assumes independent marginal errors because full covariance matrices are not present in the supplied export.

**Action:** historical A3 outputs and labels were not overwritten. The 50,000-draw result is sensitivity evidence, not the registered primary A3 result. A future amendment should define the corrected mass-draw implementation before any confirmatory use.

Artifacts: `tools/qa_audits/audit_h8_seed_stability.py`, `tools/qa_audits/audit_astrospectro_mc_precision.py`, `results/qa2/h8_seed_sweep/`, `results/qa2/astrospectro_mc_precision/`.

## 4. 10,000-replicate bootstrap null calibration

Two synthetic null families were generated, each with **10,000 outer replicates** and **2,000 stratified bootstrap resamples per outer replicate**. The AUC setting uses the registered 39-positive / 26-negative class sizes. The paired ΔAUC setting uses two correlated null score vectors (`rho = 0.7`). P-values follow the project's percentile bootstrap logic and plus-one correction.

| Synthetic null statistic | Nominal α | Rejections / 10,000 | Rate | Wilson 95% interval |
|---|---:|---:|---:|---:|
| AUC | 0.050 | 490 | 4.90% | 4.49–5.34% |
| AUC | 0.025 | 241 | 2.41% | 2.13–2.73% |
| Paired ΔAUC | 0.050 | 502 | 5.02% | 4.61–5.47% |
| Paired ΔAUC | 0.025 | 243 | 2.43% | 2.15–2.75% |

Uniformity checks on the synthetic null p-values gave KS p = 0.475 (AUC) and 0.714 (paired ΔAUC).

**Interpretation:** for these two specified Gaussian-style synthetic null families, empirical rejection frequencies are close to nominal. This is not a proof of calibration under real Gaia score distributions, severe class imbalance beyond this setup, correlated catalogue structure, domain shift, or all model-training workflows. It is not evidence that GAIA-FP discriminates real objects. The 10,000 outer replicates are now complete for these two diagnostic families only; they do not replace the remaining spatially structured and empirically calibrated null tests.

Artifacts: `tools/qa_audits/run_null_bootstrap_10k.py`, `tools/qa_audits/summarize_null_calibration_10k.py`, `results/qa2/null_calibration_10k/`.

## 5. H6 rule reconciliation

The recovered local `PREREGISTRATION.md` (v0.3 DRAFT, 9 Oct 2026) defines H6 as the paired-bootstrap difference `AUC_ML − AUC_GAIA-FP`, with H6 falsified if the interval lies entirely above zero. The current v0.6 ledger and code implement the same comparison. The earlier `−0.01` note uses a different description and is not the H6 endpoint in this recovered source.

No code or threshold was changed. The immutable OSF registration was not independently retrieved; if its text differs from the local recovered draft, it controls. See `H6_RULE_RECONCILIATION_2026-11-01.md` and the retained historical `H6_RULE_DISCREPANCY.md`.

## 6. Previously archived DR3 scientific results — retained, not rerun here

- DR3 survey-SB2 study: 2,102 candidates; only 16 SB2 positives. The primary LAMOST-observed P1 endpoint was underpowered (1 positive); the P2 GAIA-FP AUC was 0.643 [0.487, 0.788], and CMD baseline was 0.694 [0.568, 0.813]. GAIA-FP did not beat CMD in this test.
- H10: on 1,927 DR3 AstroSpectroSB1 systems, recorded AUC was 0.732 for CMD and 0.800 for CMD+`vbroad`, paired ΔAUC +0.068 [0.042, 0.095]. This is a DR3 development result, not full DR4 validation.
- Independent dynamic check: 95 selected AstroSpectroSB1 systems; historical 400-draw result 42 impostors, 2 dark-compatible, 51 indeterminate; GAIA-FP flagged 40/42 historical impostors and did not flag the two dark-compatible cases. The selection is not representative of all Gaia candidates.
- Synthetic population comparison: previous archived AUC 0.978 vs 0.971 remains simulation-only.

These historical outcomes were not recalculated in this audit except the explicitly identified seed and high-draw sensitivity checks.

## 7. What still blocks scientific completion

1. `realdata/dr3_astrospectro_all.csv` is absent. The 95-row `dr3_astrospectro_ch.csv` is not an acceptable substitute.
2. `realdata/lamost_cov.csv` (full positional coverage source table) is absent; a corrected fetcher and offline contract tests exist, but outbound DNS/network prevented live retrieval in this runtime.
3. The official DR3–DR4 source-ID neighbourhood map is absent.
4. Required full DR4 candidate orbit, field CMD and field-`vbroad` inputs do not exist yet.
5. Actual DR4 schema and units must be checked against the official release tables before scoring; the adapter is prepared but not schema-verified on the released catalogue.
6. The live Gaia TAP smoke test was not completed from this runtime; the local network resolution failure does not imply an ESA server outage.
7. The current Monte Carlo diagnostic covers two synthetic null families. Spatially clustered backgrounds, realistic scanning-law injection/recovery, empirical false-alarm calibration, and model-domain-shift tests remain.
8. H11 control mass selection uses a proxy. Its mass interpretation and any future DR4 identity matching must be validated, and the official neighbourhood table or a preregistered positional fallback must be used.
9. The v0.6 freeze manifest is historical. This addendum and its files are tracked in a separate supplemental manifest; the frozen manifest was not silently rewritten.

## 8. Next operational gate

ESA's published schedule places the full Gaia DR4 release at **2 December 2026, 12:00 CET** (15:00 in Azerbaijan). The Gaia Archive is scheduled for downtime beginning **25 November 2026, 12:00 CET**. On release, first verify schema/tables/units and the official source-ID cross-match; only then fetch and hash data, run the pre-frozen pipelines, preserve failed/NOT_CONDUCTED outputs, and evaluate the registered hypotheses. No post-outcome threshold tuning.

---

**Final status:** engineering and several DR3 reproducibility/robustness audits advanced; synthetic null calibration diagnostic completed for two defined families; real DR4 validation remains pending official data and schema. No new astrophysical discovery is claimed by this addendum.

### H6 mechanics self-test

The final H6 runner self-test also completed on a deliberately synthetic balanced set (`n=80`, 40/40; 2,000 paired bootstrap replicates; seed 7). It returned `AUC_ML=0.7525`, `AUC_GAIA-FP=0.6100`, difference `0.1425`, CI `[-0.0275, 0.3163]`, and did not falsify H6 because the interval is not entirely above zero. The output is explicitly tagged `SYNTHETIC SELFTEST - NOT A SCIENTIFIC RESULT`; it validates runner mechanics only.
