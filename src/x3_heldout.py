"""
x3_heldout.py — independent check of the follow-up-selection result (X3) on the HELD-OUT DR5 mocks.
Written BEFORE running (9 Oct 2026, 03:40). No parameter is tuned here; EIG code and thresholds are as in X3.

Pre-stated success criterion (same as X3): EIG-ranked RV follow-up resolves >= 1.2x as many ambiguous
candidates correctly as ambiguity-ranked RV follow-up with the same budget, with no more wrong resolutions,
in BOTH settings below.

Settings
  S1 'nominal'      : all ambiguous candidates observable; SB2 if dv > 8 km/s; metallicity -> CMD sigma 0.12
  S2 'shao_2m_like' : realistic small-telescope limits: only G <= 11.5 observable; SB2 if dv > 12 km/s
                      (R ~ 28 000 echelle); metallicity -> CMD sigma 0.25 (pessimistic)
Baselines (same budget): ambiguity-ranked, random, brightest-first, most-planet-like-first (lowest P(impostor)),
EIG-ranked (RV only), EIG per cost (free choice of option).
"""
import json, warnings, numpy as np, pandas as pd
warnings.filterwarnings('ignore')
import sim, followup, tournament as T

def run_setting(X, p, dv, sz, glim, seed, budget_frac=0.3, n_max=400):
    followup.DV_MIN, followup.SIG_Z = dv, sz
    rng = np.random.default_rng(seed)
    amb = np.where((p > 0.1) & (p < 0.9) & (X['G'].values <= glim))[0]
    if len(amb) > n_max: amb = rng.choice(amb, n_max, replace=False)
    cand = []
    for i in amb:
        e = followup.eig(X.iloc[i], p[i], T.SIG, rng)
        best = max(e.items(), key=lambda kv: kv[1][0]/kv[1][1])
        cand.append(dict(i=int(i), best=best[0], rate=best[1][0]/best[1][1], e1=e['O1_RV_3ep'][0]))
    budget = budget_frac*3*len(cand); cost = {'O1_RV_3ep': 3, 'O2_imaging': 1, 'O3_spec_1ep': 1}
    def run(order, opt):
        spent = ok = bad = used = 0
        for c in order:
            o = opt(c)
            if spent + cost[o] > budget: continue
            spent += cost[o]; used += 1; row = X.iloc[c['i']]
            pn = followup.simulate_outcome(row, o, p[c['i']], T.SIG, rng)
            if pn < 0.05 or pn > 0.95:
                ok += int(int(pn > 0.5) == int(row['y'])); bad += int(int(pn > 0.5) != int(row['y']))
        return dict(observed=used, correct=ok, wrong=bad)
    rv = lambda c: 'O1_RV_3ep'
    pol = {
        'ambiguity_RV': run(sorted(cand, key=lambda c: abs(p[c['i']]-0.5)), rv),
        'random_RV': run(list(rng.permutation(cand)), rv),
        'brightest_RV': run(sorted(cand, key=lambda c: X['G'].values[c['i']]), rv),
        'most_planet_like_RV': run(sorted(cand, key=lambda c: p[c['i']]), rv),
        'EIG_RV': run(sorted(cand, key=lambda c: -c['e1']), rv),
        'EIG_per_cost_free_option': run(sorted(cand, key=lambda c: -c['rate']), lambda c: c['best']),
    }
    return dict(n_ambiguous_observable=len(cand), budget=budget, policies=pol,
                truth_impostor_frac=float(np.mean([X['y'].values[c['i']] for c in cand])) if cand else None)

if __name__ == "__main__":
    pl5, im5 = sim.load('DR5', 4000, seed=99); im5 = im5.sample(1500, random_state=99)
    X = sim.build(pl5, im5, cfg=dict(span=3800.0, nep=(45, 86)), seed=77)
    X, L, p, _ = T.score(X)
    out = {}
    for nm, dv, sz, gl in [('S1_nominal', 8.0, 0.12, 99.0), ('S2_shao_2m_like', 12.0, 0.25, 11.5)]:
        out[nm] = run_setting(X, p, dv, sz, gl, seed=4)
        print(nm, out[nm]['n_ambiguous_observable'], {k: (v['correct'], v['wrong']) for k, v in out[nm]['policies'].items()}, flush=True)
    json.dump(out, open('../results/x3_heldout.json', 'w'), indent=1)
