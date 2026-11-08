# Identifiability analysis — when can a planet and a twin-binary impostor be told apart?

- **Code:** `src/identifiability.py`, `src/realism.py`.
- **Output:** `results/identifiability.json`, `results/realism.json`.
- **Nature of the results:** simulation and analytic only.

## 0. The core degeneracy (exact)

An unresolved pair with mass ratio q and light fraction β moves its photocentre by a0 = a_rel·(q/(1+q) − β)·ϖ. A near-equal pair (q ≈ 0.9–0.99) therefore produces the same small, Keplerian photocentre orbit as a star with a dark substellar companion. **Astrometry alone cannot separate them.** P, e, i, ω and a0 are shared, and the inferred "planet mass" is just a re-parameterisation of a0.

**Blended-line RV centroids do not break this degeneracy.** They move as K_sum·(q/(1+q) − f_RVS)·g(t). This reproduces the photocentre velocity up to a colour factor of about 0.80–0.90 (`rv_degeneracy.py`). The point is essentially known: Marcussen & Albrecht 2023 note the "dimming in proportion" of both signals.

Only **extra light** (CMD over-luminosity) and **extra line width that varies with orbital phase** carry independent information in Gaia data.

## 1. CMD evidence alone (map A, analytic)

The table gives the AUC for separating impostors from planets as a function of the true q and the CMD scatter σ, with the G-band slope n marginalised over U(2, 6).

| q \ σ [mag] | 0.10 | 0.20 | 0.30 | 0.40 | 0.50 | 0.60 |
|---|---|---|---|---|---|---|
| 0.80 | 0.991 | 0.901 | 0.810 | 0.747 | 0.703 | 0.672 |
| 0.90 | 1.000 | 0.972 | 0.901 | 0.833 | 0.781 | 0.741 |
| 0.95 | 1.000 | 0.989 | 0.936 | 0.873 | 0.820 | 0.777 |
| 0.99 | 1.000 | 0.995 | 0.958 | 0.902 | 0.849 | 0.802 |

**Conclusion.** The CMD separates twins well if σ ≲ 0.2 mag. At the field-star main-sequence width (σ ≈ 0.3–0.4 mag, dominated by metallicity and age) a CMD-only verdict is **unreliable for individual stars**: AUC 0.81–0.96 means that roughly 5–20% of impostors overlap planet hosts. **The CMD scatter σ is the single most important nuisance parameter.** It must be measured from DR4 field stars in the same colour bin.

## 2. RVS phase-locked width test (maps B, C)

The table gives the detection power at 1% false alarm for a twin with q = 0.95, M1 = 0.5 M☉, e = 0.3, i = 60°, and 40 epochs over 2000 d.

| P [d] (K_sum km/s) \ G | 8 | 9 | 10 | 11 | 12 | 13 |
|---|---|---|---|---|---|---|
| 50 (52) | 0.39 | 0.33 | 0.41 | 0.30 | 0.29 | 0.30 |
| 150 (36) | 0.76 | 0.81 | 0.76 | 0.73 | 0.63 | 0.34 |
| 400 (26) | 0.99 | 0.95 | 0.91 | 0.69 | 0.52 | 0.23 |
| 800 (21) | 0.99 | 0.86 | 0.75 | 0.47 | 0.25 | 0.07 |
| 1500 (17) | 0.92 | 0.74 | 0.54 | 0.29 | 0.13 | 0.07 |
| 2500 (14) | 0.73 | 0.43 | 0.34 | 0.12 | 0.07 | 0.07 |
| 4000 (12) | 0.40 | 0.25 | 0.11 | 0.11 | 0.07 | 0.03 |

The power **increases with the number of epochs** (P = 500 d, G = 11):

| Epochs | 10 | 20 | 40 | 80 |
|---|---|---|---|---|
| Power | 0.06–0.37 | 0.24–0.56 | 0.52–0.80 | 0.79–0.94 |

The power depends only weakly on e: eccentric orbits help slightly through sharper line separation near periastron.

**The short-period dip is an artefact of our assumption.** The template uses an orbit with σ_P/P = 1%. At P = 50 d this decorrelates the phase over 40 cycles. With σ_P/P = 0.1%, which is realistic for well-sampled short orbits, the power rises from 0.33 to 0.96 (R2 in `realism.json`). The fix is to use each candidate's posterior σ_P in the template. This is listed as future work and has **not** been applied, so current numbers are conservative at short P.

**Uninformative region for RVS:** G ≳ 12.5, or P ≳ 1500 d (K_sum < 17 km/s, and less than about 1.3 orbits covered), or fewer than about 20 epochs. In this region the method falls back to the CMD alone.

## 3. Astrometric noise (map D)

AUC of the joint a0 | CMD likelihood vs the CMD-only likelihood, by a0 S/N from 3 to 50:

| σ | Joint, range over S/N | CMD-only |
|---|---|---|
| 0.2 | 0.987–0.991 | ≈ identical |
| 0.3 | 0.934–0.954 | ≈ identical |
| 0.45 | 0.838–0.870 | ≈ identical |

**Finding (negative for discrimination).** Coupling a0 to the CMD through q does **not** improve ranking, and the precision of a0 does not matter. The reason is that every planet-mimicking impostor is forced to q ≈ 0.9–1, so the predicted over-luminosity is nearly the same for all of them. The real value of the joint term is **calibration**: E_planet[LR] goes from 0.88 to 1.05 and E_imp[1/LR] from 0.31 to 0.99. That is what makes the label-free contamination estimate possible.

## 4. Angular resolution (map E)

The table gives the relative-orbit semimajor axis in mas for planet-mimicking twins (M = 0.5 + 0.475 M☉).

| P \ d | 10 pc | 25 pc | 50 pc | 100 pc | 200 pc |
|---|---|---|---|---|---|
| 100 d | 42 | 17 | 8 | 4 | 2 |
| 300 d | 87 | 35 | 17 | 9 | 4 |
| 1000 d | 194 | 78 | 39 | 19 | 10 |
| 3000 d | 404 | 162 | 81 | 40 | 20 |

**Gaia never resolves these pairs**: it needs ≳ 100–200 mas. Speckle or AO imaging (≈ 30–50 mas) can help only for nearby, long-period systems. This is why imaging rarely wins in the EIG ranking.

## 5. Competing astrophysical explanation: planet host plus wide companion (H_pw) vs twin (H_t)

| Evidence | AUC, H_pw vs H_t |
|---|---|
| CMD, σ = 0.1 | 0.90 |
| CMD, σ = 0.3 | 0.79 |
| RVS phase test (G = 10, P = 500 d) | 0.99 |

**Without RVS epoch widths, H_pw and H_t are not identifiable.** Both add light. Their only CMD difference is the broader q_w distribution, and their priors are unknown. GAIA-FP therefore reports P(H_pw) separately and never calls such a star an impostor with high confidence on CMD evidence alone. With RVS, the absence of phase-locked broadening separates them.

## 6. Scan cadence realism (R1)

Using the **real** DR4 pre-release transit times of Gaia-4 and BH3 (40-epoch subsets) instead of uniform random times changes the RVS power by at most about ±0.1:

| P [d] | Real Gaia-4 | Real BH3 | Uniform |
|---|---|---|---|
| 150 | 0.87 | 0.88 | 0.71 |
| 400 | 0.70 | 0.66 | 0.71 |
| 800 | 0.47 | 0.42 | 0.50–0.53 |
| 1500 | 0.19 | 0.27 | 0.24 |

The uniform-cadence simulation is adequate at the level needed.

## 7. Astrometric noise model (R3)

The real per-transit errors in the pre-release data are about 0.028 mas, while the simple error model used for the RUWE proxy gives about 0.11 mas. This affects only the RUWE baseline, which is uninformative by construction (impostors mimic the planet's wobble). The injection–recovery map already uses the real errors.

## Summary: decisive vs ambiguous regions

| Region | Status |
|---|---|
| G ≲ 12, P ≈ 150–1500 d, ≥ 30 RVS epochs | Decisive (RVS and CMD) |
| CMD σ ≲ 0.2 mag (e.g. metallicity known) | Decisive on the CMD even without RVS |
| G ≳ 13 (no RVS) and σ ≈ 0.3–0.4 | **Ambiguous for a sizeable minority.** The abstention rule sends these to "follow-up needed". |
| P ≳ 2 × baseline | RVS weak; rely on the CMD |
| Third-light planet hosts without RVS | **Not identifiable** from impostors; reported as such |
