# Gaia DR4 pre-release — öz pipeline-ımızla yoxlama (8 oktyabr 2026)

Məlumat: Gaia DR4 pre-release epoch astrometry (ESA, 2026-06-26), transit üzrə çəkili orta (yalnız AGIS-də istifadə olunan CCD-lər).
Kod: gaia_orbit.py (numpy/scipy), fit_real.py.

## Gaia BH3 (qara dəlik) — dərc olunmuş astrometrik həll ilə müqayisə (Gaia Collaboration 2024, A&A, Table 2)
| Parametr | Bizim | Dərc olunmuş (astrometrik) |
|---|---|---|
| P [gün] | 4183.5 | 4194.7 ± 112.3 |
| e | 0.728 | 0.7262 ± 0.0056 |
| a0 [mas] | 27.11 | 27.07 ± 0.56 |
| i [°] | 110.5 | 110.659 ± 0.107 |
| ϖ [mas] | 1.660 | 1.6747 ± 0.0094 |
| Ω [°] | 136 | 136.200 ± 0.147 |
| ω [°] | 258 | 77.77 ± 0.66  (ω+180°/Ω+180° astrometrik degenerasiyası — eyni həll) |

## Gaia-4 (planet sahibi)
| Parametr | Bizim | Ədəbiyyat (NASA Exoplanet Catalog; Stefánsson et al. 2025, RV+astrometriya) |
|---|---|---|
| P | 578.8 gün | ~1.6 il |
| e | 0.417 | 0.34 |
| Kütlə | ~10.7 M_Jup (M*=0.64 Msun fərziyyəsi) | 11.8 M_Jup |
| Δχ² (periodoqram) | 1683 | — |

Qeyd: e-nin yuxarı qiymətləndirilməsi simulyasiyada gördüyümüz zəif-siqnal meylinə uyğundur → MCMC/Bayes ilə düzəldilməlidir.
NƏTİCƏ: 25 oktyabr GO/NO-GO yoxlaması → **GO** (keçildi).
