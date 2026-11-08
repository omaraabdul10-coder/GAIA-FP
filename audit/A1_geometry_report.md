# A1 — Orbital geometry, kinematics, units and angles: independent audit of GAIA-FP

Auditor A1, 31 Oct 2026. Scope: geometry, kinematics, units, angles. Files written: `audit/A1_geometry_report.md`, `audit/tests_geometry.py`, `audit/a1_reproduce.py`. Nothing else under GAIA-FP was created, changed or deleted.

**Snapshot.** At the start I hashed 138 files (scratch file `a1_work/pre_hashes.txt`, outside GAIA-FP). While I worked, other processes edited AUDIT.md, README.md, RESULTS_*.md, index.html and `src/dr4_mechanism.py`, added `src/dr4_{schema,dynamical,evaluate,adapters,run,day}.py`, `src/h11_*.py`, `src/erratum_k_units.py` and new tests, and wrote `.pyc` files into `src/__pycache__`. None of these changes are mine. All my runs used `PYTHONDONTWRITEBYTECODE=1`, ran `pytest -p no:cacheprovider` and worked on a copy.

I audited the frozen versions of the listed files. Of the new files I read only the geometry-relevant ones, from snapshot copies: `dr4_schema.py` c82b99…, `dr4_dynamical.py` 4b3318…, `h11_outcomes.py` 508017…

**Re-runs.** All re-runs were done in a scratch copy:
- The unmodified re-runs reproduce `results/dr3_study.json`, `results/vbroad_v2.json` and `results/dark_companion.json` H10 digit for digit.
- They also reproduce the frozen prediction file SHA-256 141734677a64942e…
- To reproduce everything: `python audit/a1_reproduce.py <scratch_dir>` (about 2 minutes).
- The lead auditor's `results/erratum_k_units.json` agrees with my FINDING 1 numbers to all digits.

---
## (a) Derivations and comparison with the code

**Notation:**
- (a, i, ω, Ω) are the Campbell elements of the photocentre orbit.
- X = cos E − e and Y = √(1−e²) sin E.
- B ≡ q/(1+q), with q = M2/M1.
- β = L2/(L1+L2).
- ϖ is the parallax in mas.

### a1. Thiele–Innes ↔ Campbell
**Derivation:**
- A = a(cosω cosΩ − sinω sinΩ cos i), B = a(cosω sinΩ + sinω cosΩ cos i), F = −a(sinω cosΩ + cosω sinΩ cos i), G = −a(sinω sinΩ − cosω cosΩ cos i).
- The sky offsets are Δδ = AX + FY (north) and Δα* = BX + GY (east). This equals r[cos(ν+ω)cosΩ − sin(ν+ω)sinΩ cos i] and r[cos(ν+ω)sinΩ + sin(ν+ω)cosΩ cos i], using r cos ν = aX and r sin ν = aY.
- Adding and subtracting: A+G = a(1+cos i)cos(ω+Ω), B−F = a(1+cos i)sin(ω+Ω), A−G = a(1−cos i)cos(ω−Ω), B+F = −a(1−cos i)sin(ω−Ω).
- Hence, with r± = |(A±G, B∓F)| = a(1 ± cos i):
  - **a0 = (r₊+r₋)/2**;
  - **tan⁴(i/2) = r₋²/r₊²**;
  - ω+Ω = atan2(B−F, A+G);
  - ω−Ω = atan2(−(B+F), A−G).
- Equivalently, u = (A²+B²+F²+G²)/2 = (r₊²+r₋²)/4 and v = AG−BF = a² cos i, so u + √(u²−v²) = a².
- The pairs (ω, Ω) and (ω+π, Ω+π) give identical TI constants. Astrometry alone cannot resolve this.

**Code:**
- `dr4_pipeline.campbell` (dr4_pipeline.py:70–75): **OK**.
  - The TI round trip over 20 000 random geometries, including i = 0, 10⁻⁷, 90 and 180°, agrees to 4×10⁻¹¹.
  - Inclination is correct to 3×10⁻⁷° and covers retrograde orbits.
  - The output (ω, Ω) pair is always one of the two valid pairs.
- `gaia_orbit.campbell` (gaia_orbit.py:94–104): **WRONG (FINDING 7)**.
  - It returns Ω mod 180 without shifting ω by 180, so 49.9% of outputs reconstruct to −(A,B,F,G).
  - It does not clip (u+v)(u−v), so a0 is NaN for 156/2000 exactly face-on orbits.
  - The arccos inclination returns 0 for i < 0.01°.
  - a0 and i are otherwise correct.
- `gaia_orbit.thiele_innes`: **OK**.

**Empirical check on 33 463 real DR3 AstroSpectroSB1 solutions:**
- The astrometric ω and the spectroscopic ω = atan2(C, H) agree modulo 180°. The median |Δ| is 3.2° for a0 S/N > 20 and 4.6° for all.
- The 0°/180° split is 51/49, as expected from the π ambiguity.
- Using AG − BF = a0² cos i to cross-check the inclination gives agreement to 3×10⁻¹¹°.

### a2. a0 error (dr4_pipeline.py:92, also dark_companion.py:122)
**Derivation:**
- The gradient is ∂a0/∂(A,B,F,G) = ½[(A+G)/r₊ + (A−G)/r₋, (B−F)/r₊ + (B+F)/r₋, −(B−F)/r₊ + (B+F)/r₋, (A+G)/r₊ − (A−G)/r₋].
- Its norm is |∇a0| = 1 identically, so σ_a0² = ∇ᵀΣ∇.
- The code's rms(σ_A, σ_B, σ_F, σ_G) is exact only when Σ = σ²I. TI errors are strongly correlated (orientation errors lie orthogonal to ∇), so for real data the rms overstates σ_a0.

**Code:** **APPROXIMATION, error large (FINDING 8).**
- DR3 publishes `significance` = a0/σ_a0 from the full covariance. Its minimum is 5.17 across all solution types, consistent with the DR3 acceptance cut s > 5.
- The ratio (a0/a0err_code)/significance has median 0.39 (5–95%: 0.10–1.13). So the code's σ_a0 is a median 2.6× too large, and 10× too large for 5% of candidates.
- For 284 of 2102 candidates the code's S/N is below 3 while Gaia's is above 5.
- Diagonal-only Jacobian propagation versus rms: 0.81–2.28 (5–95%).

### a3. Astrometric epoch model (gaia_orbit.py:36–58, fit_real.py, mcmc_orbit.py)
**Along-scan model:**
- w = (Δα*₀ + μα* t)sinψ + (Δδ₀ + μδ t)cosψ + ϖ f_ϖ + (BX+GY)sinψ + (AX+FY)cosψ.
- t is in Julian years from the reference epoch (the data files are relative to J2017.5).
- The model is linear in the 5 + 4 parameters given (P, e, T0).

**Code checks:**
- `design_single` and `design_orbit` (column order A↔cX, B↔sX, F↔cY, G↔sY): **OK**. Verified against an independent r, ν, Ω, ω, i sky projection to 10⁻¹².
- A noise-free fit at the true (P, e, T0) recovers ϖ, μ, a0 and i exactly.
- `fit_real.load` converts ψ from degrees to radians: **OK**.
- MCMC marginal likelihood: ∫e^{−χ²/2} dθ_lin ∝ e^{−χ²_min/2}|WᵀW|^{−½} for a flat prior: **OK**.
- The dof count n − 12 is **OK**.
- Parallax factor in `gaia_orbit.simulate` (gaia_orbit.py:118–124): **cosmetic**.
  - Theory: Δα* = ϖ(X sinα − Y cosα), Δδ = ϖ(X cosα sinδ + Y sinα sinδ − Z cosδ), where (X, Y, Z) is the observer's barycentric position.
  - The code inserts the Sun's geocentric direction, which is −observer. That flips the sign, which is equivalent to shifting the arbitrary phase constant (1.0) by π.
  - It is used only for simulations; real data carry their own f_ϖ.

### a4. Kepler equation and anomalies (gaia_orbit.py:20–33, rvs_phase_test.py:22–24)
- The solver uses Newton's method on E − e sin E = M, starting from E₀ = M for e < 0.8 and from π otherwise. ν = 2 atan2(√(1+e) sin(E/2), √(1−e) cos(E/2)).
- **OK**: max |E − e sinE − M| = 8.9×10⁻¹⁶ for e up to 0.999, and the solver agrees with a bracketing solver to 10⁻¹⁰.
- The cos ν and sin ν identities hold to 10⁻¹².
- NaN e gives NaN (loud).

### a5. Kepler III, K, and companion masses
**Kepler III:**
- a³ [AU] = (M1+M2) P²[yr]. The code uses yr = 365.25 d, while the Gaussian year is 365.2569 d. The resulting error in a is 1.3×10⁻⁵: **OK**.

**K_sum_kms** (rvs_phase_test.py:26–28):
- a = (k²M P²/4π²)^{1/3} with P in days, K1+K2 = 2πa sin i/(P√(1−e²)), and 1 AU/d = 1731.457 km/s. **OK.**
- Earth–Sun gives 29.79 km/s. Solar reflex from Jupiter gives 12.47 m/s.
- `mechanism.VKMS` = 29.7847 km/s is 2π AU per *sidereal* year, but it is divided by P/365.25 (Julian). The inconsistency is 1.7×10⁻⁵: **cosmetic**.

**Callers of K_sum_kms:**
- Correct (pass P in days): rvs_predict.py:27, followup.py:49/82/94, benchmark.py:58, sim.py:47, identifiability.py:31/83.
- **WRONG** (pass P in years): dark_companion.py:89 and vbroad_v2.py:20. See **FINDING 1**.

**Primary RV amplitude** (mechanism.py:43, 87): K1 = 2π a1 sin i/(P√(1−e²)) with a1 sin i = √(C²+H²), and K_sum = K1/B. **OK.**

**First-order companion mass** (dr4_pipeline.py:99–100, the DR3 ADQL query, h11_outcomes.mass_bounds):
- Exact: a1 = a_rel m2/(M1+m2) with a_rel ∝ (M1+m2)^{1/3}, so a1 = m2 P^{2/3}(M1+m2)^{−2/3}.
- The code computes m2_fo = a1 M1^{2/3} P^{−2/3} = **m2 (1+m2/M1)^{−2/3}**.
- **APPROXIMATION, error 8–24% at the 80 MJ cut (FINDING 3).**

**Exact mass solvers:**
- `astrospectro_check.m2_from_a1` and `mechanism.solve_m2` solve m2³ − (a1³/P²)(M1+m2)² = 0 exactly. **OK** (round trips to 10⁻⁶).
- `solve_m2` silently returns 10⁻⁵ M☉ for NaN or negative input and caps at 200 M☉. See FINDING 9.
- No spectroscopic mass function f(M) exists anywhere in src/ (checked by grep).

### a6. Photocentre and blend photometry (joint_lr.py:20–37, dark_companion.py:78–84, followup.py:25–34, mechanism.py:85–89)
**Derivation:**
- Positions relative to the barycentre are x1 = −a_rel B and x2 = a_rel(1−B).
- The photocentre is (1−β)x1 + βx2 = a_rel(β − B), so **a0 = a_rel|B − β|·ϖ** (AU × mas = mas).
- With L ∝ Mⁿ: β = qⁿ/(1+qⁿ) and ΔM_G = −2.5 log10(1+qⁿ).
- The blend photometric mass satisfies M_phot^n = M1^n(1+qⁿ), so M1 = M_phot(1+qⁿ)^{−1/n}.
- a_rel = (M1(1+q) P_yr²)^{1/3}.
- Limits: q = 1 gives β = B = ½ and a0 = 0; q → 0 gives a0 → a_rel q ϖ, the dark-companion limit.

**Code: OK.**
- `llr_a0_cmd` was checked against an independent quadrature built from luminosity-weighted component positions (with M1 found by root-finding). It agrees to 0.03 in log LR for ΔM = +0.1, −0.4 and −0.75.
- `q_weights` peaks at the true q on the falling branch.
- Twin limit: the weights collapse to q = 1 for every n.
- Note: a0(q) rises and then falls, so a0 alone is bimodal in q. This is physics, not a bug.

### a7. Line blending (rvs_phase_test.py:30–46, dark_companion.py:70–93, vbroad_v2.py:11–30)
**Derivation:**
- Two lines of variance σ₀², with weights 1−f and f, separated by Δv, give a blend variance σ₀² + f(1−f)Δv².
- Δv = v2 − v1 = (K1+K2)(cos(ν+ω) + e cos ω). The sign of ω (π shift) drops out once squared.
- Time-average closed form, with s = √(1−e²):
  - ⟨sin²ν⟩_t = s²/(1+s), using ∫sin²E/(1−e cosE)dE = 2π(1−s)/e²;
  - ⟨(e+cosν)²⟩_t = s³/(1+s);
  - the cross term is 0;
  - hence **⟨(cos(ν+ω)+e cosω)²⟩_t = s²(sin²ω + s cos²ω)/(1+s)**.
- Maximum separation shape: **1 + e|cos ω|**.

**Code:**
- The formulas are **OK**.
- `phase_avg` and `maxsep_shape` sample 64 uniform mean anomalies: **APPROXIMATION (FINDING 6)**.
  - phase_avg: error below 0.7% for e ≤ 0.8, but +30% at e = 0.9 and +172% at e = 0.95.
  - maxsep_shape: error −8% at e = 0.8 and −34% at e = 0.95.
- `rvs_z` and `phase_stat` use Fisher z = atanh(r)√(n−3): **OK**. However, t and T0 must share a zero point, and nothing enforces this (**FINDING 2**).
- Every consumer of ω is invariant under ω → ω+π, as it must be: rvs_z, phase_stat, phase_avg, maxsep_shape, `_sep_kms`, and ρ under (C,H) → −(C,H). Tested.

### a8. ρ, β̂, AMRF and dynamical labels (dark_companion.py:96–105, astrospectro_check.py:36–43, mechanism.py:26–49, dr4_dynamical.py)
**Derivation:**
- C = a1 sin i sin ω and H = a1 sin i cos ω, in AU.
- ρ = (a0/ϖ) sin i/√(C²+H²) = a_ph/a1 = |1 − β/B|. A dark companion gives ρ = 1.
- β̂ = B(1−ρ).
- AMRF = (a0/ϖ) M1^{−1/3} P_yr^{−2/3}.

**Code: OK.**
- Empirically, the real-data median ρ is 0.977, which confirms that C and H are in AU.
- A Monte Carlo with known truth (6000 real error sets) gives a false "luminous" label rate of 0.4% at ρ = 1. With ρ = 0.7, 49% are labelled luminous and 0.5% dark.
- Face-on orbits give NaN, which is labelled undetermined (−1). This is correct.
- A negative parallax produces a "luminous" label (FINDING 9).

### a9. Photometry and sky angles
- M_G = G + 5 log10(ϖ[mas]/100) and d = 1000/ϖ: **OK**.
- The ridge is evaluated with np.interp, which clamps outside the colour range (**FINDING 5**).
- `dr3_study.propagate`: Δδ = μδΔt/3.6×10⁶ deg, Δα = μα*Δt/(3.6×10⁶ cos δ). **OK.**
- `sep_arcsec` (2 arcsin(chord/2)) and the chord radius: **OK**.

### a10. Time conventions
- DR3 `t_periastron` is in days relative to J2016.0 (JD 2457389.0). Empirically t_peri/P ∈ (−0.50, +0.50), i.e. reduced to the periastron nearest the epoch.
- The DR4 pre-release epoch files use J2017.5.
- The code never converts any time. This only matters where real epochs meet T0, which happens in `rvs_z` (FINDING 2).

---
## (b) Units table

| Quantity | Unit in code | Where produced / converted (file:line) | Status |
|---|---|---|---|
| A, B, F, G | mas (photocentre) | read dr4_pipeline.py:90, dark_companion.py:99, astrospectro_check.py:36, mechanism.py:29; mas→AU via /ϖ at dr4_pipeline.py:100, dark_companion.py:102, 124, astrospectro_check.py:41, mechanism.py:32 | OK |
| C, H | AU (primary SB1 orbit) | dark_companion.py:100–102, astrospectro_check.py:37–40, mechanism.py:30–32, 38; dr4_schema.py:29 | OK (empirical ρ ≈ 0.98) |
| a0 | mas | dr4_pipeline.py:71; predicted as AU×mas at joint_lr.py:30, dark_companion.py:82, mechanism.py:86, benchmark.py:43, followup.py:30, inj_rec.py:31, identifiability.py:51 | OK |
| σ_a0 | mas | dr4_pipeline.py:92, dark_companion.py:122 | approximate, too large (F8) |
| ϖ | mas | d = 1000/ϖ pc: dr4_pipeline.py:93, joint_lr.py:21 (inverse), followup.py:29, sim.py:78, benchmark.py:43; M_G at dr4_pipeline.py:79, 94, dark_companion.py:113, 184, dr4_mechanism.py:42; ADQL ϖ > 1000/500 at dr4_pipeline.py:48 | OK |
| P | day | ÷365.25 → yr: dr4_pipeline.py:99, joint_lr.py:29, dark_companion.py:82, 124, astrospectro_check.py:42, mechanism.py:37, 83, benchmark.py:43, followup.py:29, inj_rec.py:31, mcmc_orbit.py:47, identifiability.py:51. Days into K_sum_kms: rvs_predict.py:27, followup.py:49, 82, 94, benchmark.py:58, sim.py:47 | OK |
| P into K_sum_kms | **yr passed, day expected** | **dark_companion.py:89, vbroad_v2.py:20** | **WRONG (F1)** |
| σ_P | fractional | dr4_pipeline.py:101, rvs_phase_test.py:45 | OK |
| t, T0 | day | (t−T0)/P at gaia_orbit.py:31, rvs_phase_test.py:23; t/365.25 yr for proper motion at gaia_orbit.py:37; data/*.csv relative to J2017.5; DR3 T0 relative to J2016.0; rvs_z at dr4_pipeline.py:110–113 has **no zero-point handling** | **F2** |
| K, K1, K_sum | km/s | rvs_phase_test.py:19–20, 26–28 (AU/d × 1731.456); mechanism.py:15, 43, 87 (2π AU/yr = 29.7847, sidereal) | OK (1.7×10⁻⁵ cosmetic) |
| vbroad, widths, DVMAX | km/s | dark_companion.py:90–93, vbroad_v2.py:23–30, rvs_predict.py:16, 29, simulate_stat σ₀ = 11 | OK |
| Masses | M☉; MJ = 9.546×10⁻⁴ or 1/1047.6 | dr4_pipeline.py:23, 100; joint_lr.py:16; dark_companion.py:27; astrospectro_check.py:22, 43; benchmark.py:22, 43; mcmc_orbit.py:46–47; inj_rec.py:23; ADQL factor 1047.6 | OK (within 2×10⁻⁴ of IAU) |
| G (gravitational constant) | AU³ M☉⁻¹ d⁻² = k² | rvs_phase_test.py:19, sim.py:23, followup.py:20, identifiability.py (G_) | OK |
| Proper motion | mas/yr → deg | dr3_study.py:30–31; arcsec at dr3_study.py:40, 46 | OK |
| ΔM_G, dm | mag | joint_lr.py:35, dark_companion.py:68, dr4_pipeline.py:94–95 | OK (clamp, F5) |

## (c) Angle inventory

| Function (file:line) | Angle in | Angle out | Callers pass the right unit? |
|---|---|---|---|
| dr4_pipeline.campbell (70) | — | inc ∈ [0,180] deg; ω, Ω ∈ [0,360) deg | yes: features :91; rho_labels :101 and h10 :120 (np.radians); astrospectro_check :39; mechanism.rho_sigma :31; dr4_dynamical :110; h11_outcomes :38 |
| gaia_orbit.campbell (94) | — | inc deg, ω [0,360), Ω [0,180) deg | yes: fit_keplerian :92, mcmc_orbit (a0 and inc only). Inconsistent (ω, Ω) pair: F7 |
| gaia_orbit.thiele_innes (132) | inc, ω, Ω deg | — | yes: simulate :127, inj_rec :32 |
| gaia_orbit.solve_kepler (20) | M rad | E rad | yes: orbit_XY :32, true_anomaly, realism |
| gaia_orbit.design_single/design_orbit (36/40) | sin ψ, cos ψ | — | yes: fit_real.load :4 converts ψ deg→rad; simulate ψ rad |
| gaia_orbit.simulate (107) | ra, dec, ε deg→rad (:119); orbit angles deg | — | yes |
| rvs_phase_test.true_anomaly (22) | — | ν rad | yes |
| rvs_phase_test.K_sum_kms (26) | inc deg | — | yes everywhere (inclination from campbell or catalogue, in deg); the period-unit error is F1 |
| rvs_phase_test.phase_stat (30), simulate_stat (37) | ω deg (+10° noise) | — | yes: rvs_predict :31 row['om'], benchmark :63, sim :185, identifiability |
| dr4_pipeline.rvs_z (110) | ω deg | — | yes: score :127 |
| dark_companion.phase_avg (70), vbroad_v2.maxsep_shape (11) | ω deg | — | yes: h10 :130, mechanism.physics :44, lr_v2 :21 |
| dark_companion.lr_vbroad (86), vbroad_v2.lr_v2 (16) | inc deg | — | yes |
| dark_companion.rho_labels (96), mechanism.physics/forward (35/78), astrospectro_check :39 | inc deg (np.radians) | — | yes |
| followup._sep_kms (36), _rho_proj (40) | ω deg / inc deg; internal ω rad | — | yes |
| dr4_pipeline.selftest (161) | sim degrees → np.radians; Ω drawn in rad | — | yes |
| dr3_study.propagate/_unit/sep_arcsec/positional_match (26–53) | ra, dec deg; radius arcsec | separation arcsec | yes |

No function receives degrees where it expects radians, or vice versa. Bug (2) is fixed and has not recurred.

---
## (d) Findings

Severity scale: critical = a published result or conclusion is wrong; major = a DR4-day failure, or a materially wrong quantity; minor = an edge case or a small approximation; cosmetic = no effect.

### FINDING 1 — CRITICAL: K_sum_kms receives P in years (dark_companion.py:89, vbroad_v2.py:20)
**What is wrong:**
- `K_sum_kms` expects P in days (G in AU³ M☉⁻¹ d⁻²).
- Both callers pass `period/365.25`. K scales as P^{−1/3}, so K_sum is 365.25^{1/3} = **7.148× too large**, and K² is 51× too large.

**Evidence:**
- Tests `test_lr_vbroad_uses_physical_K` and `test_lr_v2_uses_physical_K` (xfail).
- `test_lr_vbroad_favours_blend_when_vbroad_matches_physics`: a blend whose vbroad equals the physical prediction gets log LR = **−682**, i.e. it is scored as dark.
- For DR3 luminous systems (q = 0.8, n = 4, c = 1), the median predicted vbroad is **80.7 km/s with the bug and 14.7 km/s fixed**. The observed median is **14.9 km/s**.

**Effect on published results** (my re-run is identical to `results/erratum_k_units.json`):

| Quantity | Published | With the fix |
|---|---|---|
| H10 v1 vbroad-LR alone (c = 1) | 0.444 | **0.736** |
| S1 | 0.800 [0.780, 0.820] | 0.776 [0.755, 0.797] |
| H10a ΔAUC | +0.068 [+0.042, +0.095] | +0.044 [+0.033, +0.055] (still PASS) |
| S2 | 0.779 | **0.832** [0.814, 0.850] |
| H10c ΔAUC | +0.047 | +0.100 [+0.086, +0.116] |
| c = 4: S1 | 0.789 | 0.807 |
| c = 4: vbroad-LR alone | 0.396 | 0.732 |

vbroad_v2 with the fix:
- c* is still 4.
- V1: 0.759 → 0.745 [0.712, 0.776].
- V2: +0.048 → +0.039.
- **V3 still FAILS**: −0.016 → −0.025 [−0.039, −0.009]. The decision in A7 (empirical RVS score primary) therefore stands.

Conclusions that are wrong:
- On v2's TEST half, the *uncorrected-for-selection* v1 physics gives AUC **0.724 [0.692, 0.755]** once the units are fixed (0.430 with the bug).
- So the following are artefacts of this unit error, not of SB1 selection:
  - the claim in RESULTS_DARK_COMPANION.md ("the physical prediction fails: a selection effect");
  - the "Why" item 2 of PREREG_AMENDMENT_v0.5 and the motivation for A6;
  - VBROAD_V2_PLAN's "problem found";
  - pre-identified bug (4).
- SB1 truncation adds at most about 0.02 AUC, with overlapping CIs.
- "c* = 4 matches theory" is coincidental: c* sits at the edge of the grid and is fitted against a mis-scaled K.

Not affected:
- The DR4 RVS physics (rvs_predict, which passes days).
- `mechanism.py`, which computes K independently from C, H and VKMS correctly. Its M4 value ĉ ≈ 1.8 is the physically meaningful amplitude.

**Fix:** pass days (drop the /365.25), or give K_sum_kms an explicit unit argument.

### FINDING 2 — MAJOR: no time zero-point handling between RVS epoch times and T0 (dr4_pipeline.py:110–128)
**What is wrong:**
- `rvs_z(t, …, T0)` takes epoch times and `t_periastron` as given.
- Gaia epoch products are typically in BJD(TCB) − 2455197.5 (J2010). DR3 T0 is in days from J2016.0, and DR4 is likely relative to J2017.5 (as in the pre-release files).
- A zero-point offset Δ shifts the phase by Δ/P mod 1.
- Nothing converts or checks this. The new `dr4_schema.RVS_EPOCH` only checks that t lies in [−10⁴, 10⁴] d, which J2010-based times (about 1700–3700 d) pass.

**Evidence:**
- Test `test_rvs_z_robust_to_gaia_time_conventions` (xfail): z falls from 7.78 to 1.72.
- In 400 simulated twins:

| Time convention | Median z | Fraction with z > 2.33 |
|---|---|---|
| Consistent | 5.97 | 1.00 |
| Offset 2191.5 d (J2010 → J2016) | −0.56 | 0.19 |
| Offset 2739.4 d (J2010 → J2017.5) | −0.31 | 0.19 |

**Effect:** none on DR3 (no epoch RVS). On DR4 it would silently null the RVS evidence: H2, the A7 primary score, H11-O5, and llr_rvs inside P(impostor).

**Fix:**
- The adapter converts both times to days from the release reference epoch.
- Assert that the median of (t − t_ref) lies within the mission window, or pass t_ref explicitly.

### FINDING 3 — MAJOR (definition/interpretation): first-order companion mass at the 80 MJ cut (dr4_pipeline.py:99–100; DR3 ADQL; h11_outcomes.mass_bounds)
**What is wrong:** m2_fo = m2(1+m2/M1)^{−2/3}. For a true 80 MJ companion:

| M1 [M☉] | First-order m2 [MJ] | Largest true m2 admitted by the "80 MJ" cut [MJ] |
|---|---|---|
| 0.15 | 60.8 | 115.5 |
| 0.3 | 68.8 | 95.5 |
| 0.6 | 73.9 | 87.2 |

**Evidence:**
- Tests `test_first_order_mass_at_selection_boundary[0.15/0.3/0.6]` (xfail).
- On the DR3 sample, m2_fo/m2_exact has 5/50/95 percentiles 0.818/0.922/0.967 (minimum 0.685).
- **565 of 2102 (27%) scored DR3 candidates have an exact dark-companion m2 > 80 MJ**, and 79 exceed 90 MJ.

**Effect:**
- The published DR3 verdicts are unchanged. Those 565 are 545 likely_impostor and 20 ambiguous; none of the 17 likely_substellar is among them.
- But the "substellar candidate" set is mis-described.
- The same formula defines the DR4 sample and H11 O2/D. Meanwhile the A3/H8 dynamical labels (astrospectro_check, dr4_dynamical) use the exact Kepler solution, so two different "80 MJ" definitions coexist in one test. 7 of the 42 A3 impostors have an exact a0-based m2 > 80 MJ.

**Fix:** solve the exact cubic (m2_from_a1 already exists), or state "first-order" explicitly in the pre-registered text.

### FINDING 4 — MAJOR (DR4 operational): the DR4 CLI scoring path has no finite-input guard (dr4_pipeline.py:131, 190–192)
**What is wrong:**
- The fix for bug (5) lives only in dr3_study.py:132. `python dr4_pipeline.py score` runs `select_candidates(features(...))` and then `score` directly.
- Replaying the DR4 CLI on the DR3 table (17/2119 rows with NaN g-error) **crashes**: `ValueError: Probabilities contain NaN` in followup.q_post. The em step fails similarly with "sample_weight contains NaN".
- A NaN `bp_rp` makes sig_cmd NaN. The groupby at :131 then drops the row, so its log LR stays **0** (finite and silent) and P = prior. If the row is ambiguous, it instead crashes in eig.

**Evidence:** tests `test_dr4_cli_path_drops_or_flags_missing_ti_errors` and `test_score_nan_colour_is_not_silently_finite` (xfail).

**Effect:** none on DR3. The DR4 release-day run will fail if any candidate lacks a TI error, which was 0.8% of DR3.

**Fix:** filter or flag in select_candidates with a logged count, and make score raise on non-finite inputs.

### FINDING 5 — MINOR: colours outside the ridge range are clamped (dr4_pipeline.py:95)
- `np.interp` extrapolates flat, so dm is computed against the ridge at the edge colour.
- In DR3, **45/2102** scored candidates are affected: 43 redder than 3.64 and 2 bluer than 0.50.
- All 45 are likely_impostor or ambiguous; the prior of about 0.94 dominates.
- h10 cuts these objects, but the pipeline does not.
- Test `test_features_colour_outside_ridge_is_flagged` (xfail).

### FINDING 6 — MINOR: phase_avg and maxsep_shape use 64-point sampling (dark_companion.py:70–73, vbroad_v2.py:11–14)
- The errors are given in a7. Exact closed forms exist.
- On the DR3 mechanism sample (n = 10 118):
  - smax error > 1% for 7.6% of systems (maximum 42%);
  - pavg error > 1% for 1.8% (maximum 160%);
  - 62 systems change H13 bin;
  - the H13 development value moves from 2.66 [1.80, 4.08] to 2.59 [1.75, 3.98] with the exact smax.
- In h10, phase_avg clips e at 0.95 for ν but not in the template (11 systems with e > 0.95).
- Tests `test_phase_avg_closed_form_high_e` and `test_maxsep_closed_form_high_e` (xfail).

### FINDING 7 — MINOR: gaia_orbit.campbell (gaia_orbit.py:94–104)
- The (ω, Ω mod 180) pair is inconsistent in 50% of cases, so the TI sign flips.
- a0 is NaN exactly face-on.
- i < 0.01° is returned as 0.
- Only a0 and inc are used downstream (fit_real and mcmc printouts, H4), so there is **no effect on results**.
- Tests `test_gaia_orbit_campbell_roundtrip` and `test_gaia_orbit_campbell_face_on_not_nan` (xfail).

### FINDING 8 — MAJOR: σ_a0 from the rms of TI errors ignores covariances (dr4_pipeline.py:92)
- The code's σ_a0 is a median **2.6× larger** than DPAC's full-covariance value (a0/`significance`); see a2.
- **Effect on DR3**, re-run with σ_a0 = a0/significance (the 17 NaN-error rows are now kept, n = 2119):
  - P2 AUC: 0.643 → 0.652 (CI [0.492, 0.792]);
  - verdicts: likely_substellar 17 → **26**, ambiguous 174 → 218, likely_impostor 1911 → 1875;
  - 70 of 2102 verdicts change; mean P goes from 0.940 to 0.925.
- The frozen DR3 predictions (H11) carry this inflation.
- **Fix for DR4:** use `significance`, which is already fetched, or the corr_vec covariance.

### FINDING 9 — MINOR: no input validation, giving silent finite wrong values
- `mechanism.solve_m2` returns 1×10⁻⁵ M☉ for NaN or negative input and caps at 200 M☉.
- `K_sum_kms(P < 0)` returns a negative K.
- `rho_labels` with ϖ < 0 returns the label "luminous".
- No effect on published results, because inputs are filtered upstream.
- Tests `test_solve_m2_nan_input_is_nan`, `test_k_sum_rejects_nonpositive_period` and `test_rho_labels_negative_parallax_not_luminous` (xfail).

### FINDING 10 — COSMETIC
- The parallax-factor sign in gaia_orbit.simulate (a3).
- VKMS uses the sidereal year (a5).
- 365.25 d versus the Gaussian year (a5).
- `lr_v2`'s all-truncated fallback (vbroad_v2.py:25) can never trigger, because draws with qⁿ < 0.2 are never truncated.

### Outside my scope, noticed in passing
- **survey_xmatch.py:38 (major for H7).** `map(...).fillna(source_id).astype('int64')` goes through float64 whenever any id is unmapped, so 19-digit ids are corrupted. Demonstrated: 402252377651956097 → …096.
- **DR4 primary mass.** The DR4 `adql_candidates` does not fetch m1, so DR4 uses the approximate `mass_from_MG`, while DR3 used binary_masses m1. a_rel and mfit are therefore not defined the same way in the two releases.
- **Inconsistent q prior.** `rvs_predict` draws q ~ U(0.5, 1) while `joint_lr` uses U(0.1, 1).

---
## (e) Checked with no error found / not checked

**Checked, no error:**
- dr4_pipeline: campbell, fit_ms_ridge (M_G units), features apart from F3/F5/F8 (d, M_G, a_rel, units), rvs_z statistic, selftest TI construction.
- rvs_phase_test: solve_kepler, true_anomaly, K_sum_kms, phase_stat, simulate_stat.
- gaia_orbit (apart from F7), fit_real, mcmc_orbit: the epoch model and TI linearisation, parallax-factor use, proper-motion time unit (Julian yr), marginal likelihood.
- joint_lr and lik: photocentre a0_pred, a_rel(M1, q, P), M1 = M_phot/(1+qⁿ)^{1/n}, ΔM_G, the conditional p(dM|a0) construction.
- dark_companion: rho_labels formula and label estimator (truth simulation), q_weights, AMRF, phase_avg formula; lr_vbroad formula apart from F1.
- astrospectro_check: ρ, m2_dyn, m2_from_a1.
- mechanism: solve_m2 (finite inputs), physics (K1, K_sum, β̂, b, k), forward.
- vbroad_v2: maxsep definition, truncation logic.
- rv_degeneracy: centroid algebra v_c = K_sum(B−f)g.
- rvs_predict: units, A6 truncation as registered.
- benchmark.a0_mas, sim.py, inj_rec.py (isotropic inclination, TI), followup (_rho_proj, _sep_kms, q_post).
- dr3_study sky angles.
- New files dr4_dynamical (same formulas as astrospectro_check) and h11_outcomes.mass_bounds (first order, F3).
- The DR3 conventions themselves, empirically: TI in mas, C/H in AU, ω shared modulo π, t_periastron relative to J2016.0.
- ω → ω+π invariance everywhere it is required.

**Not checked:**
- The mass–luminosity table and isochrones, extinction, and ridge statistics.
- The EM prior and the hier_em/LogisticRegression logic.
- Bootstrap and AUC statistics.
- The tournament, x3, identifiability simulations beyond their units, realism.py and fp_score.py (v0.1 history).
- The physical validity of vbroad as a Gaussian σ (the c constant).
- The real DR4 data model, which has not been released: the RVS epoch time convention and the t_periastron reference epoch must be confirmed on release.
- New files other than dr4_schema, dr4_dynamical and h11_outcomes, which were still changing.
- The full-covariance (corr_vec) treatment of TI errors, since corr_vec was not downloaded.

---
## Tests (`audit/tests_geometry.py`)
Run with:
`PYTHONDONTWRITEBYTECODE=1 python -m pytest -p no:cacheprovider -q audit/tests_geometry.py`

Result: **48 passed, 17 xfailed (strict, raises=AssertionError), 0 failed**, in 2.4 s.

With `--runxfail`, each xfail fails for its stated reason:
- log LR −682 (F1);
- m2 = 60.8 / 68.8 / 73.9 MJ (F3);
- z 1.72 versus 7.78 (F2);
- finite log LR = 0 (F4);
- and so on for the rest.

The suite covers:
- campbell → TI → campbell round trips, including i = 0, 90 and 180°;
- the π-ambiguity symmetry;
- Kepler M → E → M for e up to 0.99;
- the TI epoch model against a direct sky projection;
- linear-fit recovery;
- Earth–Sun K, Jupiter reflex and Jupiter a0 at 10 pc;
- unit constants;
- the q = 1 twin limit and the photocentre against independent quadrature;
- ρ for dark, luminous, face-on and ω+π cases;
- closed-form phase averages;
- invariance under ω+π;
- time-shift invariance of rvs_z;
- edge cases: NaN, zero and negative parallax, e ≥ 1, negative P.
