# GAIA-FP architecture and data flow

This diagram describes the code that actually exists in `src/`. Simulated and real data paths are kept separate.

```mermaid
flowchart LR
  subgraph REAL["REAL public data"]
    GA[(Gaia DR3/DR4 archive<br/>nss_two_body_orbit, binary_masses,<br/>gaia_source, dr2_neighbourhood)]
    FS[(Gaia field stars)]
    SV[(Survey SB2 catalogues<br/>APOGEE · GALAH · LAMOST-MRS<br/>+ LAMOST coverage)]
    PR[(DR4 pre-release epoch astrometry<br/>Gaia-4, BH3)]
  end
  subgraph SIM["SIMULATED data"]
    LW[(Lammers & Winn mocks<br/>DR4 / DR5)]
    SM[sim.py observation model]
  end
  GA --> FE[dr4_pipeline.features<br/>Thiele–Innes → a0, P, e, i, ω;<br/>m1; CMD excess ΔM_G]
  FS --> RG[fit_ms_ridge<br/>main-sequence ridge + σ_CMD]
  RG --> FE
  FE --> LK[lik.py / joint_lr.py<br/>log LR: a0 | CMD (+ RVS phase in DR4)]
  LK --> EM[hier_em.py<br/>label-free EM prior π(x)]
  EM --> DEC[three-way verdict<br/>t = 0.15 · P(impostor)]
  DEC --> FU[followup.py<br/>EIG per cost for ambiguous]
  DEC --> CAT[(catalogue CSV + SHA-256)]
  CAT --> XM[dr3_study.py / survey_xmatch.py<br/>PM-propagated matching,<br/>ambiguity flags, labels]
  SV --> XM
  XM --> EV[metrics: AUC + bootstrap CI,<br/>PU lower bound, recall,<br/>paired diff vs baselines]
  CAT --> RP[report.py<br/>per-candidate evidence cards,<br/>data label on every page]
  FT[tools/fetch_realdata.py<br/>public TAP queries + provenance] --> GA
  PR --> OF[gaia_orbit / mcmc_orbit<br/>pipeline validation]
  LW --> SM --> LK
  SM --> TO[tournament.py, identifiability.py,<br/>x3_heldout.py (simulation only)]
  SEAL[(sealed labels<br/>private; only hashes public)] -. blind test after DR4 .-> EV
```

**Integrity guards in the code**

| Guard | Where |
|---|---|
| Sealed objects are dropped before any feature is computed | `dr3_study.py`, `excluded_sealed_ids.csv` |
| The cross-match refuses to run if the catalogue hash differs from the frozen hash | `survey_xmatch.py` |
| Simulation outputs and real-data outputs are written to differently named result files | `results/` |
| Every report page carries a mandatory data label (REAL / SIMULATED) | `report.py --label` |
| Sealed rows are dropped before the real data are saved | `tools/fetch_realdata.py` |
