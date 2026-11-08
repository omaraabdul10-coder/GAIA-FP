"""
dr4_release_map.py: map DR4 release tables to the internal (DR3-convention) schema, from ESA's DRAFT DR4 data model
(gaia-dr4-prerelease-draft-data-model_2026-06-26, read 7 Nov 2026; copy in docs/dr4_datamodel/). Differences that would
have broken a DR3-era pipeline, each handled here and checked by tests/test_dr4_release_map.py:

 1. nss_two_body_orbit.solution_type   (DR3: nss_solution_type)                          -> renamed
 2. NO c_thiele_innes / h_thiele_innes in DR4; combined solutions give semi_amplitude_primary (km/s) instead.
    a1 sin i [AU] = K1 * P[d] * 86400 * sqrt(1-e^2) / (2 pi AU_km). Our code only uses hypot(C, H) = a1 sin i, so
    C := a1 sin i, H := 0; sigma_C from K1 and P errors (first order); sigma_H := 0.
 3. dr3_neighbourhood: DR4 id is `source_id`, DR3 id `dr3_source_id`, angular_distance in MILLI-arcsec (not arcsec).
 4. rvs_epoch_parameters_single: time = obs_time_rv [days since 2010-01-01 TCB, at Gaia] + obs_time_bary_corr [ns];
    only transits with vbroad_validity_flag == True are used.
 5. t_periastron is relative to gaia_source.ref_epoch (expected J2017.5; checked at fetch time).
Solution-type names in DR4 include Orbital, OrbitalTargetedSearch, AstroSpectroSB1, OrbitalAlternative*,
OrbitalPoorlyConstrained; the frozen candidate rule keeps the DR3 types only (dr4_pipeline.SELECTION) and every other
type is counted and reported, not silently added.
"""
import numpy as np, pandas as pd
from dr4_schema import SchemaError

AU_KM = 1.495978707e8

def _need(df, cols, name):
    miss = [c for c in cols if c not in df.columns]
    if miss: raise SchemaError(f'{name}: missing DR4 columns {miss} (data model may have changed)')

def nss(df):
    _need(df, ['source_id', 'solution_type', 'period', 'eccentricity'], 'nss_two_body_orbit')
    O = df.rename(columns={'solution_type': 'nss_solution_type'}).copy()
    if 'c_thiele_innes' not in O.columns:
        K = O.get('semi_amplitude_primary'); sK = O.get('semi_amplitude_primary_error')
        e = O.eccentricity.fillna(0).clip(0, 0.99); P = O.period
        if K is not None:
            a1 = K*P*86400*np.sqrt(1 - e**2)/(2*np.pi*AU_KM)
            se = O['eccentricity_error'].fillna(0) if 'eccentricity_error' in O else 0.0     # 8 Nov: e term added (audit)
            rel = np.sqrt((sK/K)**2 + (O.period_error/P)**2 + (e*se/(1 - e**2))**2) if sK is not None else np.nan
            O['c_thiele_innes'] = a1; O['h_thiele_innes'] = np.where(np.isfinite(a1), 0.0, np.nan)
            O['c_thiele_innes_error'] = np.abs(a1)*rel; O['h_thiele_innes_error'] = np.where(np.isfinite(a1), 0.0, np.nan)
    return O

def neighbourhood(df):
    _need(df, ['source_id', 'dr3_source_id', 'angular_distance'], 'dr3_neighbourhood')
    return pd.DataFrame(dict(dr3_source_id=df.dr3_source_id.astype(str).str.strip(), dr4_source_id=df.source_id.astype(str).str.strip(),
                             angular_distance_arcsec=df.angular_distance.astype(float)/1000.0))     # mas -> arcsec

def rvs_epochs(df):
    _need(df, ['source_id', 'obs_time_rv', 'vbroad', 'vbroad_error'], 'rvs_epoch_parameters_single')
    E = df.copy()
    if 'vbroad_validity_flag' in E: E = E[E.vbroad_validity_flag.astype(str).isin(['True', 'true', '1', 'T', '84'])]
    t = E.obs_time_rv.astype(float) + (E.obs_time_bary_corr.astype(float)/86400e9 if 'obs_time_bary_corr' in E else 0.0)
    return pd.DataFrame(dict(source_id=E.source_id.astype(str).str.strip(), rv_obs_time=t, vbroad=E.vbroad, vbroad_error=E.vbroad_error))

def epoch_photometry(df):
    """H17 input. DATAMODEL_GAIA (data model 11.1: g_obs_time, g_flux, g_flux_error, g_n_obs; one row per transit) or
    DATAMODEL_STANDARD (band, time, flux, flux_error, optional rejected_by_* flags). Returns source_id, g_obs_time, g_flux,
    g_flux_error with only G transits that have >= 1 accepted CCD and a positive finite flux."""
    if 'g_obs_time' in df.columns:
        _need(df, ['source_id', 'g_obs_time', 'g_flux', 'g_flux_error'], 'epoch_photometry')
        E = df[df.g_n_obs > 0] if 'g_n_obs' in df else df
    else:
        _need(df, ['source_id', 'band', 'time', 'flux', 'flux_error'], 'epoch_photometry (standard)')
        E = df[df.band.astype(str).str.strip().str.upper() == 'G']
        for c in ('rejected_by_photometry', 'rejected_by_variability'):
            if c in E: E = E[~E[c].astype(str).isin(['True', 'true', '1', 'T'])]
        E = E.rename(columns=dict(time='g_obs_time', flux='g_flux', flux_error='g_flux_error'))
    E = E[np.isfinite(E.g_flux.astype(float)) & (E.g_flux.astype(float) > 0)]
    return pd.DataFrame(dict(source_id=E.source_id.astype(str).str.strip(), g_obs_time=E.g_obs_time.astype(float),
                             g_flux=E.g_flux.astype(float), g_flux_error=E.g_flux_error.astype(float)))
