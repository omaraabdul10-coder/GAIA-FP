"""
dr4_schema.py: schema and unit guard for the DR4 day-1 run (amendment v0.6 A22). Every table is checked BEFORE any score is
computed; any problem raises SchemaError and the run stops. Nothing is silently renamed or converted.

Checks per column: presence, numeric dtype, finite fraction, and a physical range that catches unit mistakes
(e.g. Thiele-Innes A in mas vs arcsec, C/H in AU vs km, period in days vs years, angles in degrees vs radians).
Ranges are deliberately wide: they flag unit errors, not astrophysical outliers.
"""
import numpy as np, pandas as pd

class SchemaError(RuntimeError):
    pass

# column -> (lo, hi, min finite fraction, meaning/unit)
ORBIT = {
    'source_id': None,
    'nss_solution_type': None,
    'period': (0.1, 1e5, 1.0, 'days'),
    'period_error': (0.0, 1e5, 0.9, 'days'),
    'eccentricity': (0.0, 1.0, 0.5, 'dimensionless, < 1'),
    't_periastron': (-1e5, 1e5, 0.9, 'days from the release reference epoch (CHECK-ON-RELEASE: J2016.0 in DR3)'),
    'a_thiele_innes': (-1e4, 1e4, 0.9, 'mas'), 'b_thiele_innes': (-1e4, 1e4, 0.9, 'mas'),
    'f_thiele_innes': (-1e4, 1e4, 0.9, 'mas'), 'g_thiele_innes': (-1e4, 1e4, 0.9, 'mas'),
    'a_thiele_innes_error': (0.0, 1e4, 0.9, 'mas'), 'b_thiele_innes_error': (0.0, 1e4, 0.9, 'mas'),
    'f_thiele_innes_error': (0.0, 1e4, 0.9, 'mas'), 'g_thiele_innes_error': (0.0, 1e4, 0.9, 'mas'),
    'parallax': (0.0, 1e3, 1.0, 'mas, > 0 after the candidate cut'),
    'parallax_error': (0.0, 10.0, 1.0, 'mas'),
}
COMBINED = {'c_thiele_innes': (-1e3, 1e3, 0.9, 'AU'), 'h_thiele_innes': (-1e3, 1e3, 0.9, 'AU'),
            'c_thiele_innes_error': (0.0, 1e3, 0.9, 'AU'), 'h_thiele_innes_error': (0.0, 1e3, 0.9, 'AU')}
SOURCE = {'source_id': None, 'phot_g_mean_mag': (2.0, 22.0, 0.99, 'mag'), 'bp_rp': (-1.0, 7.0, 0.9, 'mag'),
          'ruwe': (0.5, 1e3, 0.9, 'dimensionless')}
VBROAD = {'vbroad': (0.0, 600.0, 0.3, 'km/s'), 'vbroad_error': (0.0, 600.0, 0.3, 'km/s'),
          'vbroad_nb_transits': (0, 1e4, 0.3, 'count'), 'grvs_mag': (0.0, 20.0, 0.3, 'mag')}
IDMAP = {'dr3_source_id': None, 'dr4_source_id': None, 'angular_distance_arcsec': (0.0, 60.0, 1.0, 'arcsec')}
RVS_EPOCH = {'source_id': None, 't': (-1e4, 1e4, 1.0, 'days, same zero point as t_periastron'),
             'width': (0.0, 600.0, 0.9, 'km/s'), 'width_err': (0.0, 600.0, 0.9, 'km/s')}

def check(df, spec, name, strict_ranges=True):
    problems = []
    if df is None or len(df) == 0:
        raise SchemaError(f'{name}: table is empty or missing')
    for col, rule in spec.items():
        if col not in df.columns:
            problems.append(f'{name}: missing column {col!r}'); continue
        if rule is None:
            if df[col].isna().any(): problems.append(f'{name}: {col} has missing values')
            continue
        lo, hi, minfin, unit = rule
        x = pd.to_numeric(df[col], errors='coerce')
        if x.isna().sum() > df[col].isna().sum():
            problems.append(f'{name}: {col} has non-numeric entries')
        fin = np.isfinite(x)
        if fin.mean() < minfin:
            problems.append(f'{name}: {col} finite fraction {fin.mean():.3f} < {minfin} ({unit})')
        bad = fin & ((x < lo) | (x > hi))
        if strict_ranges and bad.any():
            problems.append(f'{name}: {col} has {int(bad.sum())} values outside [{lo}, {hi}] {unit} '
                            f'(e.g. {x[bad].iloc[0]!r}); unit error?')
    if 'source_id' in spec and 'source_id' in df.columns:
        sid = df['source_id'].astype(str).str.strip()
        if not sid.str.fullmatch(r'\d{1,19}').all():
            problems.append(f'{name}: source_id not all 1-19 digit integers (float-mangled ids?)')
    if problems:
        raise SchemaError('\n'.join(problems))
    return True

def check_unit_plausibility(orbits):
    """Cross-column checks that catch unit errors range checks miss."""
    problems = []
    med_ti = np.nanmedian(np.abs(orbits[['a_thiele_innes', 'b_thiele_innes', 'f_thiele_innes', 'g_thiele_innes']].values))
    if not (0.01 < med_ti < 100):
        problems.append(f'median |Thiele-Innes| = {med_ti:.3g}: not mas-like (expected 0.01-100 mas)')
    med_p = np.nanmedian(orbits['period'])
    if not (5 < med_p < 5000):
        problems.append(f'median period = {med_p:.3g}: not days-like')
    if problems:
        raise SchemaError('\n'.join(problems))
    return True
