"""Sintetik populyasiyada metodun MEXANİZMİNİ yoxlayır (real performans deyil!)."""
import numpy as np, json, csv
from fp_score import predicted_a0, mass_lum_beta, p_binary, SIG_CMD
from blind_eval import *
rng = np.random.default_rng(42)
MJ = 9.546e-4

def make_population(n):
    rows = []
    while len(rows) < n:
        is_bin = rng.random() < 0.4
        M1 = rng.uniform(0.3, 1.2); P = np.exp(rng.uniform(np.log(200), np.log(1500))); plx = rng.uniform(5, 30)
        if is_bin:
            q = rng.uniform(0.8, 1.0); beta = mass_lum_beta(q); dMG = -2.5*np.log10(1+q**4)
        else:
            q = np.exp(rng.uniform(np.log(1), np.log(80)))*MJ/M1; beta = 0.0; dMG = 0.0
        a0 = abs(predicted_a0(P, M1, q, plx, beta))
        # seçim: astrometriya qaranlıq-yoldaş fərziyyəsi ilə < 80 M_Jup göstərir (yəni "substellar namizəd")
        a_star_au = a0/plx; a_rel = (M1*(P/365.25)**2)**(1/3)
        if a_star_au/a_rel*M1/MJ > 80 or a0 < 0.05: continue
        a0_err = 0.1*a0 + 0.02
        bright = rng.random() < 0.5
        r = None; n_rvs = 0
        if bright:
            n_rvs = int(rng.integers(15, 40)); se = 1/np.sqrt(n_rvs-3)
            z_true = np.arctanh(rng.uniform(0.3, 0.9)) if is_bin else 0.0
            r = float(np.tanh(rng.normal(z_true, se)))
        rows.append(dict(a0_obs=a0+rng.normal(0,a0_err), a0_err=a0_err, P_day=P, plx=plx,
                         M1=M1+rng.normal(0,0.05), M1_err=0.05, dMG_obs=dMG+rng.normal(0,SIG_CMD),
                         r_rvs=r, n_rvs=n_rvs, label=int(is_bin)))
    return rows

for N in (40, 2000):
    pop = make_population(N)
    feats = [{k:v for k,v in r.items() if k!='label'} for r in pop]
    json.dump([r['label'] for r in pop], open(f'labels_{N}.json','w'))
    entry = freeze(['fp_score.py','blind_eval.py'], dict(prior_binary=0.3, version='v0'), f'labels_{N}.json', f'freeze_{N}.json')
    s = np.array([p_binary(f, prior_binary=0.3, n_mc=2000, rng=np.random.default_rng(i)) for i,f in enumerate(feats)])
    y = np.array(json.load(open(f'labels_{N}.json')))   # unblind
    auc = roc_auc(s,y); ci = bootstrap_ci(roc_auc, s, y, n=1000)
    op = operating_point(s, y, 0.90); cal, brier = calibration(s, y)
    print(f"\n=== N={N} (binar {y.sum()}, planet {len(y)-y.sum()}) ===")
    print(f"AUC = {auc:.3f}  95% CI [{ci[0]:.3f}, {ci[1]:.3f}]   Brier = {brier:.3f}")
    kp, npl, cip = op['planet_retention']; kb, nb, cib = op['binary_rejection']
    print(f"Isci noqte: planet saxlama {kp}/{npl} ({kp/npl:.0%}, CI {cip[0]:.0%}-{cip[1]:.0%}); "
          f"binar atilma {kb}/{nb} ({kb/nb:.0%}, CI {cib[0]:.0%}-{cib[1]:.0%})")
    print("Kalibrleme (bin, say, orta P, faktiki binar payi):", [(c[0],c[2],round(c[3],2),round(c[4],2)) for c in cal])
    # ablasiya: RVS olmadan
    s2 = np.array([p_binary(dict(f, r_rvs=None), n_mc=2000, rng=np.random.default_rng(i)) for i,f in enumerate(feats)])
    print(f"Ablasiya (RVS-siz): AUC = {roc_auc(s2,y):.3f}")
