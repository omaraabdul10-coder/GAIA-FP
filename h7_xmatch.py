"""
h7_xmatch.py: H7 survey-SB2 validation with STRING source ids (audit A1, outside-scope note: survey_xmatch.py:38 maps the
DR3->DR4 ids through float64 when the map is partial, which corrupts 19-digit ids, e.g. ...097 -> ...096).
Same rules as the frozen survey_xmatch.main (labels, metrics, hash refusal); only the id handling differs, and the DR3->DR4
map is required (DR4 ids are independent of DR3 ids).
"""
import argparse, hashlib, json, numpy as np, pandas as pd
from blind_eval import clopper_pearson
from dr4_evaluate import auc, strat_boot

def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--catalogue', required=True); ap.add_argument('--frozen-sha', required=True)
    ap.add_argument('--sb2', nargs='+', required=True); ap.add_argument('--epochs', required=True); ap.add_argument('--map', required=True)
    ap.add_argument('--out', default='../results/H7_survey_validation.json')
    a = ap.parse_args(argv)
    sha = hashlib.sha256(open(a.catalogue, 'rb').read()).hexdigest()
    if sha != a.frozen_sha: raise SystemExit(f'Catalogue hash {sha} != frozen hash: refuse to unblind.')
    s = lambda x: x.astype(str).str.strip()
    cat = pd.read_csv(a.catalogue, dtype={'source_id': str}); cat['source_id'] = s(cat.source_id)
    sb2 = set(pd.concat([s(pd.read_csv(f, dtype={'gaia_dr3_source_id': str})['gaia_dr3_source_id']) for f in a.sb2]))
    ep = pd.read_csv(a.epochs, dtype={'gaia_dr3_source_id': str}); ep = ep.set_index(s(ep.gaia_dr3_source_id))['n_epochs']
    m = pd.read_csv(a.map, dtype=str); m = m[m.angular_distance_arcsec.astype(float) <= 1.0].sort_values('angular_distance_arcsec')
    m = m.drop_duplicates('dr4_source_id').set_index(s(m.dr4_source_id))['dr3_source_id'].str.strip()
    cat['dr3'] = cat.source_id.map(m)
    cat['is_sb2'] = cat.dr3.isin(sb2); cat['n_ep'] = cat.dr3.map(ep).fillna(0)
    lab = cat[cat.dr3.notna() & (cat.is_sb2 | (cat.n_ep >= 3))]; y = lab.is_sb2.astype(int).values; p = lab.P_impostor.values
    out = dict(frozen_sha=sha, n_matched=len(lab), n_sb2=int(y.sum()), n_single=int((y == 0).sum()), n_without_dr3_counterpart=int(cat.dr3.isna().sum()))
    if min(y.sum(), (y == 0).sum()) >= 10:
        bs = strat_boot(lambda i: auc(p[i], y[i]), y)
        out['auc_lower_bound'] = auc(p, y); out['auc_ci'] = [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))]
        out['verdict_H7'] = 'PASS' if out['auc_ci'][0] > 0.5 else 'FAIL'
    else:
        out['verdict_H7'] = 'NOT_CONDUCTED:BELOW_MIN_N'
    n1 = int(y.sum()); k85, k50 = int(np.sum(p[y == 1] >= 0.85)), int(np.sum(p[y == 1] >= 0.5))
    out['recall_P>=0.85'] = [k85, n1, list(clopper_pearson(k85, n1))] if n1 else None
    out['recall_P>=0.5'] = [k50, n1, list(clopper_pearson(k50, n1))] if n1 else None
    json.dump(out, open(a.out, 'w'), indent=1, default=float); print(json.dumps(out, indent=1, default=float)); return out

if __name__ == '__main__':
    main()
