# GAIA-FP: the problem and the pitch (for "Sabahın alimləri", ISEF and non-experts)

## One sentence
Space telescopes sometimes say "new planet!" when it is really a second star. We built a filter that catches these fakes using only the telescope's own data, and we test it blind on Gaia DR4.

## The problem, in plain words
- Gaia is ESA's ~€740 million (~$1 billion) telescope. It measures the positions of about two billion stars. When a star "wobbles", something unseen is pulling it: a planet, or another star. From far away the two look the same.
- **People have already been fooled:**
  - Of 5 Gaia DR3 planet candidates checked with a telescope, 3 were double stars (Marcussen & Albrecht 2023).
  - HD 12800's "planet" was announced and then withdrawn two years later.
  - HD 114762 b was called a planet for 30 years; it is a star (Kiefer et al. 2019).
  - Our own check: of the 44 candidates that Gaia's own dynamics can test, 42 are double stars. Caveat: these 44 come from a mass-cut subsample, **not** all Gaia candidates.
- **Why it costs:**
  - Checking each candidate needs time on the largest telescopes. At Keck only about 1 in 5 proposals gets time.
  - A night spent on a fake planet is a night taken from a real one.
  - Worse, a catalogue full of fakes gives wrong answers about how planets form.
- **Why now:** on 2 Dec 2026 Gaia DR4 publishes 5.9 million binary orbits (DR3: 443 000). Perryman et al. (2014) predicted ~20 000 giant planets from Gaia, about 3–4 times all ~6 000 planets known today. Nobody can check them one by one.

## The problem at three levels
1. **Big-data science:** when can we trust automatic discoveries (Gaia, Rubin, Euclid, PLATO, Roman)?
2. **Exoplanet demographics:** how pure is Gaia's new planet and brown-dwarf list, and does contamination distort what we learn about planet formation (the "brown-dwarf desert")?
3. **Our concrete question:** can Gaia's own data separate binary impostors from real companions, shown with a blind test fixed in advance?

## What we did
- **A physical model:** the light and the photocentre of a double star, a CMD over-luminosity term, and RVS line broadening.
- **Real DR3 development results:**
  - line broadening adds +0.044 AUC beyond the CMD;
  - the line-blending mechanism is consistent with the data;
  - "label blindness" is a limit of Gaia itself.
- **Honest self-correction:** a units bug that had produced our "selection effect" story was found by our own audit and published as an erratum.
- **Pre-registration:** the rules were frozen on OSF with DOIs **before** DR4 exists (N5H4B, TBJGY, v0.6).

## If it succeeds (to be filled on 3–5 Dec 2026; numbers unknown today)
- A public catalogue with a "probability of being fake" for every DR4 candidate.
- Blind-test result: "on data nobody had seen, the filter separated impostors with [result]".
- Population result (H15): "about [Y]% of Gaia's new substellar list is fake; corrected mass distribution …".
- Open code, a DOI and a preprint.

## Closing line
Gaia will multiply humanity's planet list in a single day. We measured how much of it is real, and built a blind-tested filter that catches fake discoveries before anyone spends a telescope night on them.

## Do NOT say
- "95% of Gaia planets are fake." The 42/44 is a selected subsample.
- "We solved this for Rubin or Euclid." Say instead: "the method can transfer".
- Any DR4 number before the run.

## Sources
- Marcussen & Albrecht 2023, arXiv:2305.08623
- HD 12800 retraction: arXiv:2603.19402
- Gaia cost: Wikipedia, Gaia (spacecraft)
- Keck proposal acceptance: keckobservatory.org
- Perryman et al. 2014, ApJ 797, 14
- Kiefer et al. 2019 (HD 114762 b)

## Wider problem (added 7 Nov 2026): impostors among ALL invisible Gaia companions
- **One method, three searches.** Gaia finds invisible companions from the wobble of a star: planets, brown dwarfs, neutron stars and black holes (Gaia BH1, BH2, BH3). In every case an "invisible" companion can secretly be a star, or a pair of stars. GAIA-FP's light-fraction test works the same for all of them.
- **Development numbers (DR3, not yet tests):**
  - companions heavier than 1.4 M☉ (neutron-star / black-hole range) with a resolved test: **80 of 81 show starlight**, so they are not compact objects;
  - "brown dwarfs" according to astrometry alone: **33 of 35 are really stars**, median true mass 273 Jupiter masses (≈ 0.26 M☉);
  - the confirmed black hole Gaia BH2 is **not** flagged (ρ = 0.92), as it should not be.
- **Always say with these numbers:** these are systems that also have a measured RV orbit, which favours heavy companions; DR4 tests them on new systems (H18, H19).
- **Do not say:** "most Gaia black holes are fake" (we tested only DR3 combined orbits, and these are development numbers).
