"""DR4 day, step 2: run after `dr4_day.py run` has finished (plan: DR4_AFTER_PLAN.md, 26 Nov 2026).

dr4_day.py is frozen and does not call the analyses registered after it. This script runs them, each with its
own registered code, and changes no score, threshold or frozen file:
  H21   baseline trap              h21_baseline.py         (H21_BASELINE_TRAP_PLAN.md)
  H22   likelihood-only AUC        h22_likelihood_only.h22 (H22_LIKELIHOOD_ONLY_PLAN.md)
  H19   desert by mass             h19_desert.py           (H19_DESERT_PLAN.md)
  scan  catalogue scan             dr4_catalogue_scan.scan (DR4_CATALOGUE_SCAN_PLAN.md)
It then writes OUT/DR4_SUMMARY.md, one table with every registered result, statuses copied as written.

Before anything runs, the catalogue's SHA-256 must equal the hash dr4_evaluate recorded at unblinding;
otherwise the script stops.

The scan's sealed-object filter (realdata/excluded_sealed_ids.csv) holds DR3 ids. DR4 ids are new, so this
script first maps those DR3 ids through the DR3->DR4 map and removes the matching DR4 rows. Without that step
the 76 evaluation objects would stay in the DR4 ranked list.

Usage (from src/):
  python dr4_after.py run    --std STD --out OUT --labels FILE --baseline-days B
  python dr4_after.py dryrun --out ../dryrun        (after `dr4_day.py dryrun --out ../dryrun`; synthetic labels)
"""
import argparse, json, os, subprocess, sys, time, traceback
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
ROOT = os.path.join(HERE, '..')
STD = dict(candidates='candidates.csv', idmap='dr3_dr4_map.csv', orbits='dr4_orbits.csv')
LOG = []


def step(name, fn):
    t0 = time.time()
    try:
        r = fn(); LOG.append(dict(step=name, status='OK', seconds=round(time.time() - t0, 1), info=r)); return r
    except Exception as e:                 # one failed analysis must not stop the others; it is logged as failed
        LOG.append(dict(step=name, status='FAILED', seconds=round(time.time() - t0, 1), error=f'{type(e).__name__}: {e}',
                        trace=traceback.format_exc()[-1200:]))
        return None


def check_hash(out):
    import dr4_evaluate as E
    ev = json.load(open(f'{out}/dr4_evaluation.json'))
    h = E.sha256(f'{out}/gaiafp_dr4_catalogue.csv')
    if h != ev['catalogue_sha256']:
        raise SystemExit(f'catalogue hash {h} != hash at unblinding {ev["catalogue_sha256"]}: stop')
    return h


def sealed_dr4_ids(idmap_path, sealed_path=os.path.join(ROOT, 'realdata', 'excluded_sealed_ids.csv')):
    """DR4 ids of the sealed evaluation objects (DR3 ids mapped through the DR3->DR4 map, all matches within 1")."""
    S = set(pd.read_csv(sealed_path, dtype=str).iloc[:, 0].str.strip())
    M = pd.read_csv(idmap_path, dtype=str)
    if 'angular_distance_arcsec' in M:
        M = M[M.angular_distance_arcsec.astype(float) <= 1.0]
    return set(M[M.dr3_source_id.str.strip().isin(S)].dr4_source_id.str.strip())


def run_h21(std, out):
    r = subprocess.run([sys.executable, 'h21_baseline.py', '--pred', '../results/dr3_candidates_scored.csv',
                        '--idmap', f'{std}/{STD["idmap"]}', '--orbits', f'{std}/{STD["orbits"]}', '--out', f'{out}/h21.json'],
                       cwd=HERE, capture_output=True, text=True)
    if r.returncode: raise RuntimeError(r.stderr[-800:])
    o = json.load(open(f'{out}/h21.json')); return dict(H21=o['H21'], counts=o['counts'])


def run_h22(std, out, labels, labels_sha, expected=None):
    import dr4_evaluate as E, h22_likelihood_only as H
    L = E.map_ids(E.load_labels(labels, labels_sha, expected or E.EXPECTED), f'{std}/{STD["idmap"]}')
    C = pd.read_csv(f'{out}/gaiafp_dr4_catalogue.csv', dtype={'source_id': str}); C['source_id'] = C.source_id.str.strip()
    D = L.merge(C, left_on='dr4_source_id', right_on='source_id', how='inner', suffixes=('_dr3', ''))
    r = H.h22(D); json.dump(r, open(f'{out}/h22.json', 'w'), indent=1, default=float)
    return r.get('status') if 'H22a' not in r else dict(status=r['status'], auc=r['H22a']['auc'], ci95=r['H22a']['ci95'],
                                                         registered_pass=r['H22a']['registered_pass'], dAUC_verdict=r['H22b']['verdict'])


def run_h19(out):
    src = f'{out}/dr4_new_scored.csv'
    if not os.path.exists(src):
        json.dump(dict(status='NOT_CONDUCTED:NO_NEW_COMBINED_ORBITS'), open(f'{out}/h19_desert.json', 'w')); return 'NOT_CONDUCTED'
    r = subprocess.run([sys.executable, 'h19_desert.py', '--dr4', src, f'{out}/h19_desert.json'], cwd=HERE, capture_output=True, text=True)
    if r.returncode: raise RuntimeError(r.stderr[-800:])
    return [dict(bin=b['bin_MJ'], n=b['n'], luminous=b['n_luminous']) for b in json.load(open(f'{out}/h19_desert.json'))['bins']]


def run_scan(std, out, baseline_days):
    import dr4_catalogue_scan as S
    C = pd.read_csv(f'{out}/gaiafp_dr4_catalogue.csv', dtype={'source_id': str}); C['source_id'] = C.source_id.str.strip()
    drop = sealed_dr4_ids(f'{std}/{STD["idmap"]}'); n_drop = int(C.source_id.isin(drop).sum())
    C = C[~C.source_id.isin(drop)]
    coords = None
    cp = f'{std}/{STD["candidates"]}'
    if os.path.exists(cp):
        K = pd.read_csv(cp, dtype={'source_id': str}); K['source_id'] = K.source_id.str.strip()
        if {'ra', 'dec'} <= set(K.columns): coords = K[['source_id', 'ra', 'dec']]
        if 'G' not in C and 'phot_g_mean_mag' in K:
            C = C.merge(K[['source_id', 'phot_g_mean_mag']].rename(columns={'phot_g_mean_mag': 'G'}), on='source_id', how='left')
    summ, top, cand = S.scan(C, baseline_days, 20, coords)
    summ['n_sealed_removed_via_dr4_map'] = n_drop
    d = f'{out}/scan'; os.makedirs(d, exist_ok=True)
    json.dump(summ, open(f'{d}/scan_summary.json', 'w'), indent=1, default=float)
    top.to_csv(f'{d}/most_suspicious.csv', index=False)
    cand[cand.baseline_trap].to_csv(f'{d}/baseline_trap_flags.csv', index=False)
    if coords is not None:
        cand[(cand.shamakhy_ok == True) & ~cand.evolved_flag].sort_values('log_lr', ascending=False).to_csv(f'{d}/shamakhy_targets.csv', index=False)
    return dict(n_candidates=summ['n_candidates_mfit_lt_80'], sealed_removed=n_drop,
                impostor_fraction_with_prior=summ['impostor_fraction_with_prior'],
                impostor_fraction_likelihood_only=summ['impostor_fraction_likelihood_only'],
                n_baseline_trap=summ['n_baseline_trap'], n_shamakhy_ok=summ['n_shamakhy_ok'])


def _load(p):
    try: return json.load(open(p))
    except Exception: return None


def _round(x):
    if isinstance(x, float): return float(f'{x:.3g}')
    if isinstance(x, dict): return {k: _round(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)): return [_round(v) for v in x]
    return x


def _fmt(x):
    if isinstance(x, float): return f'{x:.3f}'
    if isinstance(x, (list, tuple)) and len(x) == 2 and all(isinstance(v, (int, float)) for v in x): return f'[{x[0]:.3f}, {x[1]:.3f}]'
    if isinstance(x, dict):
        if set(x) == {'status'}: return str(x['status'])
        return json.dumps(_round(x), default=str)
    return str(x)


def summary(out):
    """One table. Statuses and numbers are copied from the JSON files; nothing is recomputed here."""
    rows = []
    ev = _load(f'{out}/dr4_evaluation.json') or {}
    role = dict(H1='primary (Holm 0.4)', H2='Holm 0.1', A5='Holm 0.2', H3='secondary', H5='secondary', H6='secondary')
    for k, v in ev.items():
        if not (k.startswith('H') or k == 'A5') or not isinstance(v, dict): continue
        keep = {kk: v[kk] for kk in ('auc', 'ci95', 'p', 'p_holm', 'reject', 'verdict', 'registered_pass') if kk in v}
        rows.append((k, role.get(k, 'see plan'), v.get('status', ''), '; '.join(f'{a}={_fmt(b)}' for a, b in keep.items())))
    if 'holm_family' in ev: rows.append(('Holm family', 'weights 0.4/0.2/0.2/0.1/0.1', '', _fmt(ev['holm_family'])))
    m = _load(f'{out}/dr4_mechanism.json') or {}
    if m: rows.append(('H12-H14', 'H12 Holm 0.2 if n_V >= 668', m.get('H12_status', ''), f'n_V={m.get("n_V")}; H14={_fmt(m.get("H14"))}'))
    h11 = _load(f'{out}/h11.json') or {}
    if h11: rows.append(('H11a', 'Holm 0.1', _fmt(h11.get('primary', {}).get('H11a', {}).get('status', '')), _fmt(h11.get('primary', {}).get('H11a', {}))[:200]))
    for f, name, role_ in (('H7.json', 'H7', 'secondary'), ('h17.json', 'H17', 'secondary')):
        o = _load(f'{out}/{f}')
        if o: rows.append((name, role_, o.get('status', o.get('verdict_H7', '')), ''))
    o = _load(f'{out}/h21.json')
    if o: rows.append(('H21', 'secondary', o['H21'], _fmt(o.get('primary', o.get('counts')))[:200]))
    o = _load(f'{out}/h22.json')
    if o: rows.append(('H22', 'secondary', o.get('status', ''), f'AUC={_fmt(o["H22a"]["auc"])} CI={_fmt(o["H22a"]["ci95"])} pass={o["H22a"]["registered_pass"]}; dAUC vs H1: {o["H22b"]["verdict"]}' if 'H22a' in o else ''))
    o = _load(f'{out}/h19_desert.json')
    if o: rows.append(('H19 by mass', 'reporting plan', o.get('status', 'reported'), '; '.join(f'{b["bin_MJ"]} MJ: {b["n_luminous"]}/{b["n"]} luminous' for b in o.get('bins', []))))
    o = _load(f'{out}/scan/scan_summary.json')
    if o: rows.append(('Catalogue scan', 'exploratory', 'reported', f'n={o["n_candidates_mfit_lt_80"]}; impostor fraction {_fmt(o["impostor_fraction_with_prior"]["mean"])} (prior) / {_fmt(o["impostor_fraction_likelihood_only"]["mean"])} (likelihood only); baseline-trap {o["n_baseline_trap"]}; Shamakhy-observable {o["n_shamakhy_ok"]}'))
    esc = lambda s: str(s).replace('|', '/').replace('\n', ' ')
    md = ['# GAIA-FP on Gaia DR4: results table (written by src/dr4_after.py)', '',
          f'Catalogue SHA-256: `{ev.get("catalogue_sha256", "?")}`. Labelled objects found in DR4: {ev.get("n_labelled_in_catalogue", "?")} '
          f'of {ev.get("n_labelled_registered", "?")}.', '',
          'Statuses are copied from the JSON files in this folder. NOT_CONDUCTED is not a pass and not a fail.', '',
          '| Test | Role | Status | Numbers |', '|---|---|---|---|']
    md += [f'| {esc(a)} | {esc(b)} | {esc(c)} | {esc(d)} |' for a, b, c, d in rows]
    open(f'{out}/DR4_SUMMARY.md', 'w').write('\n'.join(md) + '\n')
    return len(rows)


def after(std, out, labels, labels_sha, baseline_days, expected=None):
    h = step('check catalogue hash against the hash at unblinding', lambda: check_hash(out))
    step('H21 baseline trap', lambda: run_h21(std, out))
    step('H22 likelihood-only AUC', lambda: run_h22(std, out, labels, labels_sha, expected))
    step('H19 desert by mass', lambda: run_h19(out))
    step(f'catalogue scan (baseline {baseline_days} d)', lambda: run_scan(std, out, baseline_days))
    step('DR4_SUMMARY.md', lambda: summary(out))
    import dr4_evaluate as E
    prov = {f: E.sha256(os.path.join(out, f)) for f in ('h21.json', 'h22.json', 'h19_desert.json', 'scan/scan_summary.json', 'DR4_SUMMARY.md')
            if os.path.exists(os.path.join(out, f))}
    return h, prov


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='run --std STD --out OUT --labels FILE --baseline-days B | dryrun --out DIR')
    ap.add_argument('cmd', choices=['run', 'dryrun']); ap.add_argument('--out', default='../dryrun')
    ap.add_argument('--std'); ap.add_argument('--labels'); ap.add_argument('--baseline-days', type=float)
    a = ap.parse_args(); t0 = time.time()
    try:
        import dr4_evaluate as E
        if a.cmd == 'dryrun':
            lab = f'{a.out}/FAKE_labels.json'
            h, prov = after(a.out, a.out, lab, E.sha256(lab), a.baseline_days or 2010.0)
        else:
            if not (a.std and a.labels and a.baseline_days):
                raise SystemExit('run needs --std, --labels and --baseline-days (DR4 data span in days, from the DR4 documentation)')
            h, prov = after(a.std, a.out, a.labels, E.LABELS_V2_SHA, a.baseline_days)
        status = 'COMPLETED' if all(s['status'] == 'OK' for s in LOG) else 'COMPLETED_WITH_FAILED_STEPS'
    except BaseException as e:
        status, prov = f'STOPPED: {type(e).__name__}: {e}', {}
    json.dump(dict(command=a.cmd, status=status, total_seconds=round(time.time() - t0, 1), steps=LOG, output_sha256=prov),
              open(f'{a.out}/after_{a.cmd}_log.json', 'w'), indent=1, default=str)
    print(json.dumps(dict(status=status, steps=[(s['step'], s['status'], s.get('info') or s.get('error')) for s in LOG]), indent=1, default=str))
