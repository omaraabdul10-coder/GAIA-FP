"""
dr4_epoch_astrometry.py: H4 adapter (audit 31 Oct, done 6 Nov). DR4 epoch astrometry (DataLink EPOCH_ASTROMETRY) -> the
5-column per-CCD table that fit_real.load() reads: t_day_rel_J2017.5, scan_pos_angle_deg, centroid_pos_al_mas, err_mas,
parallax_factor_al.
Accepts (i) one row per FoV transit with 10-element per-CCD arrays (index 0 = sky mapper), or (ii) exploded rows with a
component_index column. Rules: drop the sky mapper (index 0); keep used_by_agis_al == True when present; time = obs_time_tcb
(ns since 2010-01-01 TCB) + obs_time_bary_corr (ns) -> days relative to J2017.5. Column names follow the pre-release data
model (audit/C_dr4_datamodel.md); any missing column stops the run.
"""
import numpy as np, pandas as pd
from dr4_adapters import parse_array, JD_2010, REF_EPOCH_JD
from dr4_schema import SchemaError

NEED = ['obs_time_tcb', 'scan_pos_angle', 'centroid_pos_al', 'centroid_pos_error_al', 'parallax_factor_al']

def explode(df):
    if 'component_index' in df.columns: return df.copy()
    rows = []
    for _, r in df.iterrows():
        arr = {c: parse_array(r[c]) if not np.isscalar(r[c]) or isinstance(r[c], str) else np.full(10, r[c], float) for c in NEED}
        used = parse_array(r['used_by_agis_al']) if 'used_by_agis_al' in df.columns else np.ones(len(arr['centroid_pos_al']))
        n = len(arr['centroid_pos_al'])
        for k in range(n):
            rows.append(dict({c: arr[c][k] if len(arr[c]) == n else arr[c][0] for c in NEED}, component_index=k, used_by_agis_al=bool(used[k]),
                             obs_time_bary_corr=float(r.get('obs_time_bary_corr', 0.0))))
    return pd.DataFrame(rows)

def to_fit_table(df, ref_epoch='J2017.5'):
    miss = [c for c in NEED if c not in df.columns]
    if miss: raise SchemaError(f'epoch astrometry: missing columns {miss}')
    E = explode(df)
    E = E[E.component_index != 0]
    if 'used_by_agis_al' in E: E = E[E.used_by_agis_al.astype(str).isin(['True', 'true', '1', 'T', '84'])]
    t = (E.obs_time_tcb.astype(float) + E.get('obs_time_bary_corr', 0.0).astype(float))/86400e9
    if not (1000 < np.median(t) < 5000): raise SchemaError(f'epoch astrometry: median time {np.median(t):.4g} d after 2010 -- wrong unit?')
    out = pd.DataFrame({'t_day_rel': t + JD_2010 - REF_EPOCH_JD[ref_epoch], 'psi_deg': E.scan_pos_angle.astype(float),
                        'w_mas': E.centroid_pos_al.astype(float), 'err_mas': E.centroid_pos_error_al.astype(float),
                        'f_plx': E.parallax_factor_al.astype(float)})
    out = out[np.isfinite(out).all(1) & (out.err_mas > 0)]
    if not ((out.psi_deg.abs() <= 360).all() and (out.f_plx.abs() <= 1.5).all()): raise SchemaError('epoch astrometry: angle or parallax factor out of range')
    return out.sort_values('t_day_rel').reset_index(drop=True)
