"""
survey_xmatch.py — H7: independent validation of the frozen DR4 GAIA-FP catalogue with public spectroscopic-survey
SB2 catalogues (PREREGISTRATION v0.3 §3, H7). Runs ONLY after the catalogue is frozen and its SHA-256 is committed.

    python survey_xmatch.py --catalogue ../catalogue/gaiafp_dr4_catalogue.csv --frozen-sha <sha256> \
        --sb2 apogee_sb2.csv galah_sb2.csv lamost_sb2.csv --epochs survey_epochs.csv

Inputs (downloaded from VizieR / survey sites; versions listed in PREREGISTRATION before freezing):
  --sb2     : one CSV per SB2 catalogue, each with a column 'gaia_dr3_source_id'
  --epochs  : CSV with 'gaia_dr3_source_id', 'n_epochs' (max over surveys) for stars observed by any survey
  DR3->DR4 source_id mapping: provided by the Gaia archive (dr3_neighbourhood-style table, CHECK-ON-RELEASE);
  if absent, DR3 ids are used directly when unchanged.
Labels (fixed rules): survey-SB2 = in any SB2 catalogue; survey-single = n_epochs >= 3 and in no SB2 catalogue.
Survey RV scatter is deliberately NOT used (blended centroids mimic the planet signal; rv_degeneracy.py).
"""
import argparse, hashlib, json, numpy as np, pandas as pd
from blind_eval import roc_auc, clopper_pearson

def boot_auc(s, y, n=2000, seed=0):
    r = np.random.default_rng(seed); pos, neg = np.where(y == 1)[0], np.where(y == 0)[0]; v = []
    for _ in range(n):
        i = np.r_[r.choice(pos, len(pos)), r.choice(neg, len(neg))]; v.append(roc_auc(s[i], y[i]))
    return [float(x) for x in np.percentile(v, [2.5, 97.5])]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--catalogue', required=True); ap.add_argument('--frozen-sha', required=True)
    ap.add_argument('--sb2', nargs='+', required=True); ap.add_argument('--epochs', required=True)
    ap.add_argument('--map', default=None, help='optional CSV dr3_source_id,dr4_source_id')
    a = ap.parse_args()
    sha = hashlib.sha256(open(a.catalogue, 'rb').read()).hexdigest()
    if sha != a.frozen_sha:
        raise SystemExit(f'Catalogue hash {sha} != frozen hash: refuse to unblind.')
    cat = pd.read_csv(a.catalogue)
    sb2 = set(pd.concat([pd.read_csv(f)['gaia_dr3_source_id'] for f in a.sb2]).astype('int64'))
    ep = pd.read_csv(a.epochs).set_index('gaia_dr3_source_id')['n_epochs']
    if a.map:
        m = pd.read_csv(a.map).set_index('dr4_source_id')['dr3_source_id']; cat['dr3'] = cat['source_id'].map(m).fillna(cat['source_id']).astype('int64')
    else:
        cat['dr3'] = cat['source_id'].astype('int64')
    cat['is_sb2'] = cat['dr3'].isin(sb2); cat['n_ep'] = cat['dr3'].map(ep).fillna(0)
    lab = cat[cat['is_sb2'] | (cat['n_ep'] >= 3)].copy(); y = lab['is_sb2'].astype(int).values; p = lab['P_impostor'].values
    out = dict(frozen_sha=sha, n_matched=len(lab), n_sb2=int(y.sum()), n_single=int((y == 0).sum()))
    if y.sum() and (y == 0).sum():
        out['auc_lower_bound'] = float(roc_auc(p, y)); out['auc_ci'] = boot_auc(p, y)
    k85, k50, n1 = int(np.sum(p[y == 1] >= 0.85)), int(np.sum(p[y == 1] >= 0.5)), int(y.sum())
    out['recall_P>=0.85'] = [k85, n1, list(clopper_pearson(k85, n1))] if n1 else None
    out['recall_P>=0.5'] = [k50, n1, list(clopper_pearson(k50, n1))] if n1 else None
    out['survey_sb2_fraction_lower_bound'] = float(y.mean()) if len(y) else None
    out['gaiafp_mean_P_on_matched'] = float(p.mean()) if len(p) else None
    out['verdict_H7'] = None if 'auc_ci' not in out else ('supported' if out['auc_ci'][0] > 0.5 else 'falsified')
    json.dump(out, open('../results/H7_survey_validation.json', 'w'), indent=1); print(json.dumps(out, indent=1))

if __name__ == "__main__":
    main()
