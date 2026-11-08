# What do real binary impostors look like? (EXPLORATORY, Gaia DR3, 6 Nov 2026)

**Labels:** Gaia's own dynamics (ρ = a0 sin i / a1 sin i, H10 rules). They use **neither the CMD nor vbroad**, so the properties below are independent of how the labels were made.
**Sample:** 1186 luminous-companion binaries (impostor type) and 2060 dark-consistent systems. **Code:** `src/fp_characterization.py` → `results/fp_characterization.json`.

| Property | Luminous (impostor type) | Dark-consistent |
|---|---|---|
| Median mass ratio q | 0.58 | 0.36 |
| Median light fraction β̂ | 0.15 | 0.00 |
| Over-luminous (ΔM_G < −0.3 mag) | **89%** | 57% |
| Median vbroad (km/s) | **14.9** | 8.1 |
| RUWE > 1.4 | 100% | 100% |
| Median RUWE | 3.2 | 4.8 |
| Median period (d) | 434 | 446 |

## How a stellar binary masquerades as a substellar companion
An astrometry-only analysis assumes the companion is dark and infers its mass from the photocentre orbit a0. A luminous companion pulls the photocentre back by the factor (B − β)/B, so the inferred mass is too small.

| Light fraction β̂ | n | Median factor by which the companion mass is under-estimated |
|---|---|---|
| 0.00–0.05 | 4 | 1.6× |
| 0.05–0.10 | 243 | 1.8× |
| 0.10–0.20 | 644 | 2.3× |
| 0.20–0.50 | 278 | **3.9×** |

- **Overall:** the median under-estimate is **2.4×**.
- **Masquerade:** 37 of the 1186 luminous binaries would look substellar (< 80 MJ) to an astrometry-only analysis, although their companion is a star.

## What this says (and does not say)
- **CMD over-luminosity and line broadening are real signatures of impostors.** Both were measured with labels that do not use them.
- **RUWE does not separate the two classes** in this sample. Every system has RUWE > 1.4, and the dark-consistent systems have *higher* RUWE. A RUWE cut is therefore not a substitute for this method.
- **57% of the dark-consistent systems are also over-luminous** (ΔM_G < −0.3). Over-luminosity alone is therefore not proof of an impostor. Possible causes are evolved primaries, the ridge reference, and label blindness (A16). This is not explained here.
- **Limitations:**
  - This is development data, and exploratory.
  - The labels are blind to light at small RV separation (A16), so some "dark-consistent" systems may be hidden blends.
  - These are AstroSpectroSB1 systems; the substellar candidate list itself is a mass-cut subsample.
