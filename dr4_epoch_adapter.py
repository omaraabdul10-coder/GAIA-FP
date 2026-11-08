"""
dr4_epoch_adapter.py — config-driven adapter for Gaia epoch astrometry (task H4 groundwork).

NOT bound to any DR4 schema.  The final DR4 epoch-astrometry column names are unpublished, so EVERY column name comes from a
mapping the user supplies (see configs/dr4_epoch_astrometry_mapping.template.json); placeholders are rejected.  Nothing here validates
DR4: it only normalises a table to arrays the orbit code can use, and is unit-tested on SYNTHETIC fixtures (tests/test_dr4_epoch_adapter.py).

Features
  time        : ns_since_2010_tcb | days_since_2010_tcb | jd | jyear -> days relative to the orbit reference epoch (J2016.0, J2017.5 or a number, jyear)
  CCD         : optional selection by CCD id, from a per-observation column (rows layout) or from per-CCD arrays (array layout)
  missing     : NaN/None/masked/user sentinels, optional validity flag; dropped observations are COUNTED and reported
  uncertainty : sigma | variance | inverse_variance -> sigma [mas]; scale, floor and extra noise (quadrature) are explicit options;
                non-positive or non-finite uncertainties are dropped (never silently replaced)
Layouts: 'rows_per_observation' (one row per observation) and 'arrays_per_source' (one row per source; list/ndarray cells, or '[..]' strings).
Output: dict source_id -> EpochSet (t_days, al_mas, sigma_mas, + optional scan_angle, parallax_factor, ccd) and a per-source QC dict.
"""
from __future__ import annotations
import ast, json
from dataclasses import dataclass, field
import numpy as np, pandas as pd

JD_2010 = 2455197.5                      # 2010-01-01 00:00 TCB as used in Gaia time stamps (as in dr4_adapters.JD_2010)
REF_EPOCH_JD = {'J2016.0': 2457389.0, 'J2017.5': 2457936.875}
PLACEHOLDER = 'FILL_FROM_RELEASED_DR4_DATAMODEL'
TIME_UNITS = ('ns_since_2010_tcb', 'days_since_2010_tcb', 'jd', 'jyear')
UNC_KINDS = ('sigma', 'variance', 'inverse_variance')

class EpochAdapterError(ValueError): pass

@dataclass
class EpochSet:
    source_id: str
    t_days: np.ndarray
    al_mas: np.ndarray
    sigma_mas: np.ndarray
    scan_angle: np.ndarray | None = None
    parallax_factor: np.ndarray | None = None
    ccd: np.ndarray | None = None
    qc: dict = field(default_factory=dict)

def ref_epoch_jd(ref):
    if isinstance(ref, str):
        if ref in REF_EPOCH_JD: return REF_EPOCH_JD[ref]
        raise EpochAdapterError(f'unknown reference epoch label {ref!r}; use one of {sorted(REF_EPOCH_JD)} or a number (Julian year)')
    r = float(ref)
    if not 2000 < r < 2040: raise EpochAdapterError(f'implausible reference epoch {r} (Julian year expected)')
    return 2451545.0 + (r - 2000.0) * 365.25

def to_relative_days(t, unit, ref):
    t = np.asarray(t, float)
    if unit == 'ns_since_2010_tcb': jd = JD_2010 + t / 86400e9
    elif unit == 'days_since_2010_tcb': jd = JD_2010 + t
    elif unit == 'jd': jd = t
    elif unit == 'jyear': jd = 2451545.0 + (t - 2000.0) * 365.25
    else: raise EpochAdapterError(f'time_unit {unit!r} not in {TIME_UNITS}')
    return jd - ref_epoch_jd(ref), jd

def sigma_from(u, kind, scale=1.0, floor=0.0, extra=0.0):
    u = np.asarray(u, float)
    with np.errstate(divide='ignore', invalid='ignore'):
        if kind == 'sigma': s = u.copy()
        elif kind == 'variance': s = np.where(u > 0, np.sqrt(u), np.nan)
        elif kind == 'inverse_variance': s = np.where(u > 0, 1.0 / np.sqrt(u), np.nan)
        else: raise EpochAdapterError(f'uncertainty_kind {kind!r} not in {UNC_KINDS}')
    s = np.where(s > 0, s, np.nan) * scale
    s = np.sqrt(s**2 + extra**2)
    return np.where(np.isfinite(s), np.maximum(s, floor), np.nan)

def load_mapping(src):
    m = json.load(open(src)) if isinstance(src, str) else dict(src)
    cols = m.get('columns') or {}
    for k in ('source_id', 'time', 'along_scan', 'uncertainty'):
        if not cols.get(k): raise EpochAdapterError(f'mapping.columns.{k} is required')
    bad = [k for k, v in cols.items() if v == PLACEHOLDER]
    if bad: raise EpochAdapterError(f'mapping still contains placeholders for {bad}: fill them from the released DR4 data model')
    if m.get('layout', 'rows_per_observation') not in ('rows_per_observation', 'arrays_per_source'): raise EpochAdapterError('layout must be rows_per_observation or arrays_per_source')
    if m.get('time_unit') not in TIME_UNITS: raise EpochAdapterError(f'time_unit must be one of {TIME_UNITS}')
    if m.get('ref_epoch') is None: raise EpochAdapterError('ref_epoch is required (the zero point of t_periastron; DR3: J2016.0, DR4 expected J2017.5, CHECK-ON-RELEASE)')
    if m.get('uncertainty_kind', 'sigma') not in UNC_KINDS: raise EpochAdapterError(f'uncertainty_kind must be one of {UNC_KINDS}')
    return m

def _as_array(v):
    if isinstance(v, str):
        s = v.strip().replace('(', '[').replace(')', ']')
        for tok in ('NaN', 'nan', 'null', 'NULL', '--'): s = s.replace(tok, 'None')
        try: v = ast.literal_eval(s)
        except (ValueError, SyntaxError): raise EpochAdapterError(f'cannot parse array string {v[:50]!r}')
    if np.ma.isMaskedArray(v): v = v.astype(float).filled(np.nan)
    return np.array([np.nan if x is None else x for x in np.atleast_1d(v)], float)

def _gather(g, cols, layout):
    """Return dict of equal-length 1-D float arrays for one source."""
    out = {}
    for key, c in cols.items():
        if c is None: continue
        if c not in g.columns: raise EpochAdapterError(f'mapped column {c!r} (for {key}) not in table; have {sorted(g.columns)}')
        if layout == 'rows_per_observation': out[key] = pd.to_numeric(g[c], errors='coerce').to_numpy(float)
        else:
            if len(g) != 1: raise EpochAdapterError('arrays_per_source needs exactly one row per source_id')
            out[key] = _as_array(g[c].iloc[0])
    n = {len(v) for k, v in out.items() if k != 'source_id'}
    if len(n) != 1: raise EpochAdapterError(f'array lengths differ across mapped columns: { {k: len(v) for k, v in out.items()} }')
    return out

def adapt(df: pd.DataFrame, mapping, source_ids=None):
    m = load_mapping(mapping); cols = m['columns']; layout = m.get('layout', 'rows_per_observation')
    sid_col = cols['source_id']
    if sid_col not in df.columns: raise EpochAdapterError(f'source_id column {sid_col!r} missing')
    keys = df[sid_col].astype(str).str.strip(); res, qc_all = {}, {}
    sel = m.get('ccd_select'); sel = None if sel is None else set(np.atleast_1d(sel).tolist())
    if sel is not None and not cols.get('ccd'): raise EpochAdapterError('ccd_select given but columns.ccd is not mapped')
    sentinels = [float(x) for x in m.get('missing_sentinels', [])]
    for sid, g in df.groupby(keys, sort=False):
        if source_ids is not None and sid not in source_ids: continue
        raw = {k: np.array(v, float) for k, v in _gather(g, {k: v for k, v in cols.items() if k != 'source_id'}, layout).items()}   # writable copies
        t_raw, al, un = raw['time'], raw['along_scan'], raw['uncertainty']; n0 = len(t_raw); qc = dict(n_input=n0)
        for s in sentinels:
            for a in (t_raw, al, un): a[a == s] = np.nan
        sig = sigma_from(un, m.get('uncertainty_kind', 'sigma'), m.get('uncertainty_scale', 1.0), m.get('uncertainty_floor_mas', 0.0), m.get('extra_noise_mas', 0.0))
        t, jd = to_relative_days(t_raw, m['time_unit'], m['ref_epoch'])
        ok = np.isfinite(t) & np.isfinite(al) & np.isfinite(sig); qc['n_missing_or_bad_uncertainty'] = int(n0 - ok.sum())
        if cols.get('valid_flag'):
            good = raw['valid_flag'] == m.get('valid_flag_true_value', 1); qc['n_flagged_invalid'] = int((ok & ~good).sum()); ok &= good
        if sel is not None:
            inc = np.isin(raw['ccd'], list(sel)); qc['n_other_ccd'] = int((ok & ~inc).sum()); ok &= inc
        if ok.sum() < m.get('min_observations', 5):
            qc['n_kept'] = int(ok.sum()); qc['dropped_source'] = f"fewer than {m.get('min_observations', 5)} valid observations"; qc_all[sid] = qc; continue
        # sanity: Gaia mission window 2014-07..2025-01 (JD 2456800..2460700), catches ns/day/s unit mix-ups
        med = float(np.median(jd[ok]))
        if m['time_unit'] != 'jyear' and not 2456500 < med < 2461500:
            raise EpochAdapterError(f'{sid}: median observation time JD {med:.1f} outside the Gaia mission window; wrong time_unit?')
        o = np.argsort(t[ok]); idx = np.where(ok)[0][o]
        es = EpochSet(sid, t[idx], al[idx], sig[idx], scan_angle=raw['scan_angle'][idx] if 'scan_angle' in raw else None,
                      parallax_factor=raw['parallax_factor'][idx] if 'parallax_factor' in raw else None, ccd=raw['ccd'][idx] if 'ccd' in raw else None)
        qc['n_kept'] = int(len(idx)); es.qc = qc; res[sid] = es; qc_all[sid] = qc
    return res, qc_all
