# Photocentre bench: a tabletop test of the impostor equation

Status: hardware add-on, planned 23 Nov 2026. It is not part of the OSF registration (n6jzx) and changes no registered test. The predictions below are written before the bench is built.

## What it tests

GAIA-FP rests on one equation. If a binary is unresolved, Gaia measures the light-weighted centre (the photocentre), and its orbit has semi-major axis

a0 = a_rel · |B − β|,  B = m2/(m1+m2),  β = L2/(L1+L2).

A dark companion (β = 0) gives a0 = a_rel·B. A luminous companion makes a0 smaller, so whoever assumes the companion is dark infers too small a mass. When β = B (in practice, near-twins), the photocentre does not move at all: that is the blind spot in NOTE_BLIND_SPOT_MAP.md.

The bench makes this measurable on a table:
- Two LEDs sit on a rotating arm. The pivot is the barycentre.
- B is set mechanically: B = (distance from LED1 to the pivot) / (LED separation d).
- β is set with resistors and measured photometrically.
- A camera, deliberately defocused so the two LEDs merge into one blob, plays the role of Gaia.
- `photocentre_track.py` measures the radius of the blob's centroid track.

## Parts (approximate prices; check local shops)

| Part | Use | Approx. |
|---|---|---|
| Arduino Nano | motor control | $5–10 |
| 28BYJ-48 stepper + ULN2003 driver | slow, steady rotation (~4 rpm) | $3–5 |
| Rigid arm, 60–80 mm (aluminium strip or 3D print), holes every 1–2 mm | sets d and B | $2 |
| 2 × 5 mm LEDs, same type and colour | the two "stars" | $1 |
| 2 × 10 kΩ trimmers + 2 × 100 Ω resistors + 2 small switches | brightness of each LED; turn each on/off | $2 |
| 2×AAA holder on the arm | powers the LEDs, so no slip ring | $2 |
| Phone or webcam with manual focus and exposure, tripod | the "telescope" | own |
| Matte black card, ruler | background; image scale (mm per pixel) | $1 |

Dim the LEDs with the trimmers, never with PWM. PWM flicker beats with the camera's rolling shutter and moves the measured centre.

## Set-up

1. Mount the LEDs d = 20 mm apart and put the pivot 6 mm from LED1, so B = 0.30. Measure the distances with calipers. Their error goes straight into B.
2. Place the camera 1–2 m away. Turn off auto-exposure and auto-focus, and fix ISO and shutter. Defocus until the two LEDs form one round blob. Check that no pixel saturates.
3. Put a ruler in the plane of the arm and film it once to get mm per pixel.
4. **Photometry for β:** with the arm still, film LED1 alone, then LED2 alone, with the same settings. β = S2/(S1+S2), where S is the background-subtracted sum of counts in the same aperture. (Option: a BH1750 light sensor gives a second, independent β.)

## Runs and written predictions (d = 20 mm, B = 0.30)

Film at least two full turns per setting. Then run

```
python photocentre_track.py run.mp4 --d-mm 20 --mm-per-px <scale>
```

| β | Predicted radius (mm) | B inferred if you assume a dark companion | Mass underestimate |
|---|---|---|---|
| 0.00 | 6.0 | 0.30 | none |
| 0.10 | 4.0 | 0.20 | 1.5× |
| 0.20 | 2.0 | 0.10 | 3× |
| 0.30 | 0.0 | 0.00 | blind spot |
| 0.40 | 2.0 | 0.10 | 3× |
| 0.50 | 4.0 | 0.20 | 1.5× |

Full table: `bench_predictions.json`.

**Pass criteria (set now):**
1. A V-shaped fit of radius against β gives slope magnitude d within 5%.
2. The fitted zero point β0 agrees with the mechanical B within 0.03.
3. The radius at β = B is below 0.3 mm. That is 5% of the dark-companion radius.

For β > B the photocentre follows the fainter, lighter LED instead of the brighter one. Its phase relative to the arm jumps by 180°. Note this in the log. Gaia cannot see that phase, because it has no reference for where the stars really are.

## Optional run: the baseline trap (H21)

Film only one third of a turn, as Gaia DR3 saw only part of long orbits. Fit a circle to that arc and compare its radius and centre with a full-turn fit. The short arc should give a less certain and usually smaller orbit. It is the bench version of RESULTS_1878822452815621120.md.

## Software check already done

`synthetic_check.py` makes artificial camera frames: two blended Gaussian LEDs, 8-bit, with noise. It runs them through the tracker. It recovers d·|B − β| to within 0.003 mm for β = 0–0.5. At β = B it gives 0.04 mm instead of 0. That small positive value is the noise floor of a circle fit. A real run will have a larger floor (vibration, air, camera), so measure it with both LEDs at equal brightness on a stopped arm.

One lesson from that check is now part of the code: a centroid with a brightness threshold, or an aperture that moves with the blob, clips the faint LED's light. That pulls the centre toward the bright LED and in the synthetic test gave radii 1–1.5 mm too large (60% too large at β = 0.2). The tracker therefore uses one fixed aperture with no threshold.

## Limits (say these at the stand)

- LEDs of the same colour make β the same at every wavelength. Real stars have different colours, so β depends on the band (Gaia G versus RVS). The bench does not test that.
- The bench checks the geometry of the photocentre, not Gaia's scanning law, its noise model or its period search.
- B is a lever-arm ratio, not a gravitational mass ratio. In a real binary they are the same thing because the barycentre is where the pivot is; on the bench we put it there by hand.
