"""
a1_reproduce.py -- regenerates the numeric evidence of A1_geometry_report.md in a SCRATCH copy (never touches GAIA-FP/).

    python audit/a1_reproduce.py <empty_scratch_dir>            # ~3 min

Variants (each in its own subprocess, monkey-patching only the copy's modules in memory):
  h10  orig|fixed   dark_companion.h10, c = 1 and 4         (FINDING 1: K_sum_kms receives P in years)
  v2   orig|fixed   vbroad_v2.main                          (FINDING 1)
  dr3  orig|sig     dr3_study.main; sig: a0err = a0/significance (FINDING 8)
"orig" must reproduce the published results/*.json exactly (checked and printed).
"""
import os, sys, json, shutil, subprocess
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)

def child(src, what, mode, out):
    os.chdir(src); sys.path.insert(0, src)
    import numpy as np, rvs_phase_test as R
    _K = R.K_sum_kms; Kd = lambda M1, M2, P_yr, e, inc: _K(M1, M2, P_yr*365.25, e, inc)   # callers pass years
    if what == 'h10':
        import pandas as pd, dark_companion as DC
        if mode == 'fixed': DC.K_sum_kms = Kd
        fc = pd.read_csv(DC.REAL + 'dr3_field.csv'); rg = DC.D.fit_ms_ridge(fc); f = pd.read_csv(DC.REAL + 'dr3_field_vbroad.csv')
        MGf = f.phot_g_mean_mag + 5*np.log10(f.parallax/100)
        ms = (f.bp_rp >= rg['color'].min()) & (f.bp_rp <= rg['color'].max()) & (MGf > np.interp(f.bp_rp, rg['color'], rg['ridge']) - 2.0)
        cal = DC.vb_field(f[ms]); d3 = pd.read_csv(DC.REAL + 'dr3_astrospectro_all.csv'); res = {}
        for c in (1.0, 4.0):
            r, X = DC.h10(d3, fc, cal, c=c); lab = X.label.values
            mv = (lab >= 0) & np.isfinite(X.vbroad) & (X.vbroad_nb_transits >= 5) & np.isfinite(X.vb_med) & (X.vb_sig > 0)
            res[c] = dict(S1=r['vbroad_subset_auc']['S1'], S2=r['vbroad_subset_auc']['S2'], H10a=r['H10a_dAUC_S1_minus_B2'],
                          H10c=r['H10c_dAUC_S2_minus_B2'], vbLR_alone=DC.auc((X.S1 - X.CMDLR).values[mv], lab[mv]))
            if c == 1.0 and mode == 'orig':
                res['reproduces_published'] = r == json.load(open('../results/dark_companion.json'))['H10']
    elif what == 'v2':
        import vbroad_v2 as V
        if mode == 'fixed': V.K_sum_kms = Kd
        pub = json.load(open('../results/vbroad_v2.json')); V.main(); res = json.load(open('../results/vbroad_v2.json'))
        if mode == 'orig': res['reproduces_published'] = res == pub
    else:
        import dr4_pipeline as D, dr3_study as DS
        if mode == 'sig':
            _f = D.features
            def feat(cand, ridge):
                X = _f(cand, ridge); s = X['significance'].values
                X['a0err'] = np.where(np.isfinite(s) & (s > 0), X['a0'].values/np.where(s > 0, s, 1), X['a0err'].values); return X
            D.features = feat
        pub = json.load(open('../results/dr3_study.json')); os.makedirs(out, exist_ok=True); res = DS.main(out=out + '/')
        res = dict(P2=res['P2_PU_all']['auc'], P2_ci=res['P2_PU_all']['auc_ci']['GAIA-FP'], verdicts=res['counts']['verdicts'],
                   reproduces_published=(res == pub) if mode == 'orig' else None)
    print('RESULT', what, mode, json.dumps(res, default=float))

if __name__ == '__main__':
    if len(sys.argv) > 2 and sys.argv[1] == '--child':
        child(*sys.argv[2:6]); sys.exit()
    scr = os.path.abspath(sys.argv[1]); assert not scr.startswith(ROOT), 'scratch dir must be outside GAIA-FP'
    W = os.path.join(scr, 'GAIA-FP')
    if not os.path.exists(W):
        for d in ('src', 'realdata', 'results', 'data'):
            shutil.copytree(os.path.join(ROOT, d), os.path.join(W, d), ignore=shutil.ignore_patterns('__pycache__', '*PRIVATE*'))
    for what, modes in (('h10', ('orig', 'fixed')), ('v2', ('orig', 'fixed')), ('dr3', ('orig', 'sig'))):
        for m in modes:
            for d in ('results',):                                   # fresh published results for every variant
                shutil.rmtree(os.path.join(W, d)); shutil.copytree(os.path.join(ROOT, d), os.path.join(W, d))
            p = subprocess.run([sys.executable, '-B', os.path.abspath(__file__), '--child', os.path.join(W, 'src'), what, m,
                                os.path.join(scr, f'dr3_{m}')], capture_output=True, text=True, env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'))
            print(*[l for l in p.stdout.splitlines() if l.startswith('RESULT')] or [p.stderr[-2000:]], sep='\n', flush=True)
