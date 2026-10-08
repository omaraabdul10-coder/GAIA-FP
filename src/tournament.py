"""
tournament.py — runs the pre-registered improvement tournament (GAIA-FP/TOURNAMENT_PLAN.md).
Stages: python tournament.py val   -> VALIDATION experiments X1..X5 (writes results/tournament_val.json)
        python tournament.py final -> one-time HELD-OUT (DR5) evaluation      (writes results/tournament_heldout.json)
SIMULATED DATA ONLY.
"""
import sys, json, warnings, time, numpy as np, pandas as pd
warnings.filterwarnings('ignore')
from scipy.special import expit, logit
from sklearn.ensemble import HistGradientBoostingClassifier
import sim, lik, followup
from hier_em import em, phi
from blind_eval import roc_auc, clopper_pearson

OUT = sys.argv[2] if len(sys.argv) > 2 else '../results/'
SIG = 0.30
COLS = ['P', 'e', 'mfit', 'd', 'G', 'dm', 'z']

def rej95(s, y):
    thr = np.quantile(s[y == 0], 0.95); return float(np.mean(s[y == 1] > thr))

def splits():
    pl, im = sim.load('DR4', 6000, seed=3)
    im = im.sample(frac=1, random_state=11).reset_index(drop=True); h = len(im)//2
    return (pl.iloc[:3000], im.iloc[:h]), (pl.iloc[3000:], im.iloc[h:])

def score(X, sig=SIG, seed=0, w=0.0, em_fit=True):
    Lt, r = lik.llr_t(X, sig, seed)
    X = X.assign(llr_cmd=Lt - r)
    Lw = lik.llr_w(X, sig) if w > 0 else None
    L = lik.effective_llr(Lt, Lw, w)
    if em_fit:
        p, pi = em(L, phi(X))
    else:
        p, pi = lik.posterior(L, 0.3), np.full(len(L), 0.3)
    return X, L, p, pi

def ml_model(train):
    Xtr = sim.build(*train, seed=7)
    return HistGradientBoostingClassifier(max_iter=300, learning_rate=0.05).fit(Xtr[COLS].values, Xtr['y'].values)

def metrics(s, y):
    return dict(auc=float(roc_auc(s, y)), rej95=rej95(s, y))

# ------------------------------------------------------------------ X2 abstention
def abstain_curve(p, y, ts=np.linspace(0.01, 0.5, 50)):
    rows = []
    for t in ts:
        dec = (p <= t) | (p >= 1-t); pred = (p >= 1-t).astype(int)
        n = int(dec.sum()); err = int(np.sum(pred[dec] != y[dec]))
        rows.append(dict(t=float(t), coverage=float(dec.mean()), n_dec=n, errors=err, err_rate=err/max(n, 1),
                         err_ci=list(clopper_pearson(err, max(n, 1)))))
    return rows

# ------------------------------------------------------------------ X3 follow-up policies
def followup_experiment(X, p, seed=0, budget_frac=0.3):
    rng = np.random.default_rng(seed)
    amb = np.where((p > 0.1) & (p < 0.9))[0]
    if len(amb) > 300: amb = rng.choice(amb, 300, replace=False)
    cand = []
    for i in amb:
        row = X.iloc[i]; e = followup.eig(row, p[i], SIG, rng)
        best = max(e.items(), key=lambda kv: kv[1][0]/kv[1][1])
        cand.append(dict(i=int(i), best=best[0], best_rate=best[1][0]/best[1][1], eig_O1=e['O1_RV_3ep'][0],
                         eigs={k: v[0] for k, v in e.items()}))
    budget = budget_frac*3*len(amb); cost = {'O1_RV_3ep': 3, 'O2_imaging': 1, 'O3_spec_1ep': 1}

    def run(order, option_of):
        spent, ok, bad, used = 0.0, 0, 0, 0
        for c in order:
            o = option_of(c)
            if spent + cost[o] > budget: continue
            spent += cost[o]; used += 1; row = X.iloc[c['i']]
            pn = followup.simulate_outcome(row, o, p[c['i']], SIG, rng)
            if pn < 0.05 or pn > 0.95:
                if int(pn > 0.5) == int(row['y']): ok += 1
                else: bad += 1
        return dict(observed=used, resolved_correct=ok, resolved_wrong=bad, cost=spent)

    pol = {}
    pol['EIG_per_cost'] = run(sorted(cand, key=lambda c: -c['best_rate']), lambda c: c['best'])
    pol['ambiguity_RV'] = run(sorted(cand, key=lambda c: abs(p[c['i']]-0.5)), lambda c: 'O1_RV_3ep')
    pol['random_RV'] = run(list(rng.permutation(cand)), lambda c: 'O1_RV_3ep')
    pol['EIG_RV_only'] = run(sorted(cand, key=lambda c: -c['eig_O1']), lambda c: 'O1_RV_3ep')
    choice = pd.Series([c['best'] for c in cand]).value_counts().to_dict()
    return dict(n_ambiguous=len(amb), budget=budget, policies=pol, eig_choice=choice)

# ------------------------------------------------------------------ X4 contamination estimators
def em_const(L, pi=0.3):
    for _ in range(1000):
        pi = float(np.clip(np.mean(expit(L + logit(pi))), 1e-5, 1-1e-5))
    return pi

def profile_ci(L):
    g = np.linspace(0.001, 0.8, 800); ll = np.array([np.sum(np.logaddexp(np.log(x) + L, np.log1p(-x))) for x in g])
    ok = ll >= ll.max() - 1.92; return [float(g[ok].min()), float(g[ok].max())]

def contamination(X, L, F, c_true, rng):
    y = X['y'].values; pi_, ii_ = np.where(y == 0)[0], np.where(y == 1)[0]
    n_i = len(ii_); n_p = int(round(n_i*(1-c_true)/c_true))
    if n_p > len(pi_): n_p = len(pi_); n_i = int(round(n_p*c_true/(1-c_true)))
    idx = np.r_[rng.choice(pi_, n_p, replace=False), rng.choice(ii_, n_i, replace=False)]
    r, _ = em(L[idx], F[idx])
    return dict(true=float(y[idx].mean()), em_het=float(r.mean()), em_const=em_const(L[idx]), profile_ci=profile_ci(L[idx]))

# ------------------------------------------------------------------ stages
def stage_val():
    t0 = time.time(); R = {}
    train, val = splits(); ml = ml_model(train)
    Xv = sim.build(*val, seed=21); y = Xv['y'].values
    Xv, L0, p0, pi0 = score(Xv)
    R['B0_validation'] = dict(v3_fixed=metrics(lik.posterior(L0, .3), y), v3_EM=metrics(p0, y), ML=metrics(ml.predict_proba(Xv[COLS].values)[:, 1], y),
                              brier_EM=float(np.mean((p0-y)**2)), brier_fixed=float(np.mean((lik.posterior(L0, .3)-y)**2)))
    print('B0', R['B0_validation'], f'{time.time()-t0:.0f}s', flush=True)

    # X1 competing hypothesis
    Xw = sim.build(*val, cfg=dict(wide_frac=0.10), seed=23); yw = Xw['y'].values; isw = (Xw['cls'] == 'w').values
    x1 = {}
    for name, w in [('B0', 0.0), ('X1_w0.05', 0.05), ('X1_w0.02', 0.02), ('X1_w0.20', 0.20)]:
        _, _, pw, _ = score(Xw, w=w)
        _, _, pc, _ = score(Xv, w=w)
        hasr = (Xw['nep'] > 0).values
        x1[name] = dict(auc_with_wide=float(roc_auc(pw, yw)), auc_clean=float(roc_auc(pc, y)),
                        false_imp_wide_rvs=float(np.mean(pw[isw & hasr] > 0.5)), false_imp_wide_norvs=float(np.mean(pw[isw & ~hasr] > 0.5)),
                        false_imp_plain_planets=float(np.mean(pw[(Xw['cls'] == 'p').values] > 0.5)),
                        imp_detect=float(np.mean(pw[yw == 1] > 0.5)), n_wide_rvs=int((isw & hasr).sum()), n_wide_norvs=int((isw & ~hasr).sum()))
        print('X1', name, x1[name], flush=True)
    R['X1'] = x1

    # X2 abstention
    curve = abstain_curve(p0, y); ok = [c for c in curve if c['err_rate'] <= 0.02]
    t_star = max(ok, key=lambda c: c['t'])['t'] if ok else None
    R['X2'] = dict(curve=curve, t_star=t_star, at_t_star=[c for c in curve if c['t'] == t_star])
    print('X2 t*', t_star, R['X2']['at_t_star'], flush=True)

    # X3 follow-up
    R['X3'] = followup_experiment(Xv, p0, seed=4)
    print('X3', json.dumps(R['X3'])[:600], flush=True)

    # X4 contamination
    rng = np.random.default_rng(8); F = phi(Xv); x4 = {}
    scen = {'nominal': (Xv, L0, F)}
    for nm, cfg, sig_assumed in [('sig_true_0.36', dict(sig_cmd=0.36), 0.30), ('sig_true_0.24', dict(sig_cmd=0.24), 0.30),
                                  ('rvs_noise_x2_unmodelled', dict(rvs_noise=2.0), 0.30), ('wide_10pct_unmodelled', dict(wide_frac=0.10), 0.30)]:
        Xs = sim.build(*val, cfg=cfg, seed=31)
        if 'rvs_noise' in cfg: Xs['srv'] = Xs['srv']/2.0          # analyst assumes nominal precision
        Xs, Ls, _, _ = score(Xs, sig=sig_assumed, em_fit=False)
        scen[nm] = (Xs, Ls, phi(Xs))
    for nm, (Xs, Ls, Fs) in scen.items():
        x4[nm] = [contamination(Xs, Ls, Fs, c, rng) for c in (0.05, 0.15, 0.30, 0.45)]
        print('X4', nm, [(round(r['true'], 3), round(r['em_het'], 3), round(r['em_const'], 3)) for r in x4[nm]], flush=True)
    R['X4'] = x4

    # X5 shifts
    x5 = {}
    def evals(Xs, sig=SIG):
        ys = Xs['y'].values; Xs2, Ls, ps, _ = score(Xs, sig=sig)
        return dict(v3_fixed=metrics(lik.posterior(Ls, .3), ys), v3_EM=metrics(ps, ys), ML=metrics(ml.predict_proba(Xs2[COLS].values)[:, 1], ys), n=len(ys), frac_imp=float(ys.mean()))
    base = dict(v3_fixed=R['B0_validation']['v3_fixed'], v3_EM=R['B0_validation']['v3_EM'], ML=R['B0_validation']['ML'])
    x5['nominal'] = base
    sub = lambda m: Xv[m].reset_index(drop=True)
    x5['G<12'] = evals(sub(Xv['G'] < 12)); x5['G>14'] = evals(sub(Xv['G'] > 14)); x5['d<60pc'] = evals(sub(Xv['d'] < 60))
    x5['cmd_scatter_0.45'] = evals(sim.build(*val, cfg=dict(sig_cmd=0.45), seed=41), sig=0.45)
    Xn = sim.build(*val, cfg=dict(rvs_noise=2.0), seed=42); x5['rvs_noise_x2'] = evals(Xn)
    x5['rvs_10_20_epochs'] = evals(sim.build(*val, cfg=dict(nep=(10, 21)), seed=43))
    x5['rvs_missing'] = evals(sim.build(*val, cfg=dict(drop_rvs=True), seed=44))
    for c in (0.05, 0.50):
        rs = np.random.default_rng(5); yv = Xv['y'].values; pi_, ii_ = np.where(yv == 0)[0], np.where(yv == 1)[0]
        n_i = len(ii_); n_p = int(round(n_i*(1-c)/c))
        if n_p > len(pi_): n_p = len(pi_); n_i = int(round(n_p*c/(1-c)))
        idx = np.r_[rs.choice(pi_, n_p, replace=False), rs.choice(ii_, n_i, replace=False)]
        x5[f'contamination_{c:.2f}'] = evals(Xv.iloc[idx].reset_index(drop=True))
    for k, v in x5.items():
        print('X5', k, {m: (round(v[m]['auc'], 3), round(v[m]['rej95'], 2)) for m in ('v3_fixed', 'v3_EM', 'ML')}, flush=True)
    R['X5'] = x5
    json.dump(R, open(OUT+'tournament_val.json', 'w'), indent=1, default=float)
    print(f'done {time.time()-t0:.0f}s')

def stage_final(t_star, w_final):
    R = {}
    train, _ = splits(); ml = ml_model(train)
    pl5, im5 = sim.load('DR5', 4000, seed=99); im5 = im5.sample(1500, random_state=99)
    cfg = dict(span=3800.0, nep=(45, 86))
    X = sim.build(pl5, im5, cfg=cfg, seed=77); y = X['y'].values
    X, L, p_b0, _ = score(X, w=0.0)
    out = dict(B0_v3_EM=metrics(p_b0, y), v3_fixed=metrics(lik.posterior(L, .3), y), ML_trained_DR4=metrics(ml.predict_proba(X[COLS].values)[:, 1], y),
               CMD_only=metrics(X['llr_cmd'].values, y), brier_B0=float(np.mean((p_b0-y)**2)))
    if w_final > 0:
        _, _, p_f, _ = score(X, w=w_final); out['final_v3_EM_Hpw'] = metrics(p_f, y); out['brier_final'] = float(np.mean((p_f-y)**2))
    else:
        p_f = p_b0
    dec = (p_f <= t_star) | (p_f >= 1-t_star); err = int(np.sum((p_f[dec] >= 1-t_star).astype(int) != y[dec]))
    out['abstention'] = dict(t=t_star, coverage=float(dec.mean()), n_dec=int(dec.sum()), errors=err, err_rate=err/max(dec.sum(), 1),
                             err_ci=list(clopper_pearson(err, int(dec.sum()))))
    rng = np.random.default_rng(3); r, _ = em(L, phi(X))
    out['contamination'] = dict(true=float(y.mean()), em_het=float(r.mean()), em_const=em_const(L), profile_ci=profile_ci(L))
    out['n'] = dict(planets=int((y == 0).sum()), impostors=int(y.sum()), rvs_frac=float((X['nep'] > 0).mean()))
    # where does it fail? worst errors
    wrong = np.argsort(-np.abs(p_f - y))[:15]
    out['worst_cases'] = X.iloc[wrong][['y', 'G', 'P', 'e', 'mfit', 'd', 'dm', 'z', 'nep']].assign(p=p_f[wrong]).round(3).to_dict('records')
    R['heldout_DR5'] = out
    print(json.dumps(out, indent=1, default=float)[:3000])
    json.dump(R, open(OUT+'tournament_heldout.json', 'w'), indent=1, default=float)

if __name__ == "__main__":
    if sys.argv[1] == 'val': stage_val()
    else: stage_final(float(sys.argv[3]), float(sys.argv[4]))
