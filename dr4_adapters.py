"""
dr4_adapters.py: convert DR4 RVS epoch products into the per-source arrays the frozen rvs_z() expects (audit 31 Oct 2026).

The exact DR4 column names are not public yet (audit/C_dr4_datamodel.md). The adapter therefore:
  * accepts Format A  (one row per transit, scalar columns),
            Format A' (one row per transit with extra per-CCD array columns: arrays are ignored),
            Format B  (one row per source, per-transit arrays as lists or as "(..)"/"[..]" strings);
  * maps column-name synonyms, and refuses (SchemaError) if a needed quantity has no unique match;
  * converts times to DAYS RELATIVE TO THE ORBIT'S REFERENCE EPOCH, the zero point of t_periastron, which the caller must
    state (DR3: J2016.0; DR4: expected J2017.5, CHECK-ON-RELEASE). Time units are declared, then checked against the data.
Gaia time conventions: both "days since 2010-01-01 TCB" (JD 2455197.5) and "ns since 2010-01-01 TCB" are handled.
"""
import ast, numpy as np, pandas as pd
from dr4_schema import SchemaError

JD_2010 = 2455197.5
REF_EPOCH_JD = {'J2016.0': 2457389.0, 'J2017.5': 2457936.875}
SYN = dict(source_id=['source_id'],
           time=['rv_obs_time', 'obs_time_tcb', 'transit_time', 'obs_time', 'rv_time'],
           width=['vbroad', 'line_broadening', 'vbroad_value', 'rv_line_broadening'],
           width_err=['vbroad_error', 'line_broadening_error', 'vbroad_uncertainty'])

def pick(cols, key):
    hits = [c for c in SYN[key] if c in cols]
    if len(hits) != 1:
        raise SchemaError(f'RVS epochs: {key} matches {hits or "nothing"} among columns {sorted(cols)}')
    return hits[0]

def parse_array(v):
    if isinstance(v, (list, tuple, np.ndarray)): return np.asarray(v, float)
    if isinstance(v, str):
        s = v.strip().replace('(', '[').replace(')', ']')
        for tok in ('NaN', 'nan', 'null', 'NULL', '--'): s = s.replace(tok, 'None')
        try: vals = ast.literal_eval(s)
        except (ValueError, SyntaxError): raise SchemaError(f'RVS epochs: cannot parse array string {v[:60]!r}')
        return np.array([np.nan if x is None else x for x in vals], float)
    raise SchemaError(f'RVS epochs: cannot parse array value of type {type(v).__name__}')

def to_rel_days(t, unit, ref_epoch):
    """t in `unit` since 2010-01-01 TCB -> days since the reference epoch of t_periastron."""
    t = np.asarray(t, float)
    if unit == 'ns_since_2010': d = t/86400e9
    elif unit == 'days_since_2010': d = t
    elif unit == 'jd': d = t - JD_2010
    else: raise SchemaError(f'unknown time unit {unit!r}')
    fin = d[np.isfinite(d)]
    # the DR4 baseline (2014-07-25 .. 2020-01-20) is 1666..3671 days after 2010-01-01; allow a wide margin
    if len(fin) and not (1000 < np.median(fin) < 5000):
        raise SchemaError(f'RVS epoch times: median {np.median(fin):.4g} days after 2010-01-01 is outside the mission: wrong time unit?')
    return d + JD_2010 - REF_EPOCH_JD[ref_epoch]

def standardise(df, time_unit, ref_epoch):
    """Return {source_id(str): dict(t=days rel. to ref epoch, width=km/s, width_err=km/s)}."""
    cols = set(df.columns); sid = pick(cols, 'source_id'); tc, wc, ec = pick(cols, 'time'), pick(cols, 'width'), pick(cols, 'width_err')
    first = df[tc].dropna().iloc[0] if df[tc].notna().any() else None
    is_b = first is not None and not np.isscalar(first) or isinstance(first, str)
    out = {}
    if is_b:                                                     # Format B
        for _, r in df.iterrows():
            t, w, e = parse_array(r[tc]), parse_array(r[wc]), parse_array(r[ec])
            if not (len(t) == len(w) == len(e)): raise SchemaError(f'RVS epochs: array lengths differ for {r[sid]}')
            out[str(r[sid]).strip()] = (t, w, e)
    else:                                                        # Format A / A'
        for s, g in df.groupby(df[sid].astype(str).str.strip()):
            out[s] = (g[tc].values.astype(float), pd.to_numeric(g[wc], errors='coerce').values, pd.to_numeric(g[ec], errors='coerce').values)
    res = {}
    for s, (t, w, e) in out.items():
        ok = np.isfinite(t) & np.isfinite(w) & np.isfinite(e) & (e > 0)
        if (w[np.isfinite(w)] < 0).any(): raise SchemaError(f'RVS epochs: negative line width for {s}')
        res[s] = dict(t=to_rel_days(t[ok], time_unit, ref_epoch), width=w[ok], width_err=e[ok])
    return res
