"""
report.py — human-readable evidence report for a scored GAIA-FP catalogue (DR3 study or DR4 catalogue).

    python report.py ../results/dr3_candidates_scored.csv --out ../results/report_dr3.html --top 60 --label "REAL DATA: Gaia DR3"

For every candidate it shows: the evidence used (astrometric amplitude, CMD excess relative to the measured main-sequence
scatter, RVS phase statistic if present), P(impostor) and the three-way verdict, the alternative explanation that cannot
be excluded, the recommended next observation (ambiguous cases), and the known limitations. The data label passed with
--label is printed on every page so simulated and real outputs cannot be confused.
"""
import argparse, html, numpy as np, pandas as pd

def explain(r):
    s = []
    sig = r.get('sig_cmd', np.nan); dm = r.get('dm', np.nan)
    if np.isfinite(dm) and np.isfinite(sig):
        k = dm/sig
        s.append(f"CMD: ΔM_G = {dm:+.2f} mag ({k:+.1f}σ of the local main sequence, σ = {sig:.2f}). "
                 + ("Over-luminous, as an unresolved near-twin pair would be." if k < -1.5 else
                    "Consistent with a single main-sequence star." if abs(k) < 1.5 else "Under-luminous (metal-poor or photometric issue)."))
    if 'a0' in r and np.isfinite(r['a0']):
        s.append(f"Astrometry: photocentre semimajor axis a0 = {r['a0']:.3f} mas, implied dark-companion mass ≈ {r.get('mfit', np.nan):.1f} M_J.")
    z = r.get('z', np.nan)
    if np.isfinite(z):
        s.append(f"RVS: phase-locked line-width statistic z = {z:+.1f} over {int(r.get('nep', 0))} epochs "
                 + ("(evidence for a second set of lines moving with the orbit)." if z > 2.3 else "(no phase-locked broadening detected)."))
    else:
        s.append("RVS: no epoch line widths available — the spectroscopic test could not be applied.")
    return s

def caveats(r):
    c = ["A wide, non-orbiting stellar companion (third light) also makes a star over-luminous; without RVS epochs it is "
         "not distinguishable from a twin impostor (IDENTIFIABILITY_ANALYSIS.md §5)."]
    if r.get('verdict') == 'likely_substellar':
        c.append("A 'likely substellar' verdict is not a planet confirmation: radial-velocity follow-up is still required.")
    if r.get('ruwe', 1) > 3:
        c.append("High RUWE: the astrometric solution may be affected by additional unmodelled motion.")
    return c

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('csv'); ap.add_argument('--out', default='report.html')
    ap.add_argument('--top', type=int, default=50); ap.add_argument('--label', required=True)
    a = ap.parse_args(); X = pd.read_csv(a.csv)
    X = X.assign(_amb=np.abs(X['P_impostor']-0.5)).sort_values('_amb').head(a.top)
    cards = []
    for _, r in X.iterrows():
        col = {'likely_impostor': '#c0392b', 'likely_substellar': '#1e8449', 'ambiguous_followup_needed': '#b9770e'}.get(r['verdict'], '#555')
        ev = ''.join(f'<li>{html.escape(x)}</li>' for x in explain(r)); cv = ''.join(f'<li>{html.escape(x)}</li>' for x in caveats(r))
        fu = r.get('best_followup', '') if isinstance(r.get('best_followup', ''), str) else ''
        cards.append(f"""<section><h3>Gaia {int(r['source_id'])}</h3>
<p><b style="color:{col}">{r['verdict'].replace('_', ' ')}</b> · P(impostor) = {r['P_impostor']:.2f} · G = {r['G']:.2f} · P = {r['P']:.0f} d</p>
<h4>Evidence</h4><ul>{ev}</ul><h4>Cannot be excluded</h4><ul>{cv}</ul>
{'<h4>Recommended next observation</h4><p>'+html.escape(fu)+'</p>' if fu else ''}</section>""")
    page = f"""<!doctype html><meta charset="utf-8"><title>GAIA-FP evidence report</title>
<style>body{{font:15px/1.5 system-ui,sans-serif;max-width:900px;margin:auto;padding:16px}}section{{border:1px solid #ccc;border-radius:8px;padding:12px;margin:12px 0}}
.banner{{background:#222;color:#fff;padding:8px 12px;border-radius:6px}}</style>
<p class="banner">DATA: {html.escape(a.label)} · {len(X)} candidates shown (most ambiguous first)</p>
<h1>GAIA-FP evidence report</h1>
<p>Probabilities come from Gaia observables only. Verdict thresholds (t = 0.15) were fixed on validation data before any real data were scored.</p>
{''.join(cards)}"""
    open(a.out, 'w').write(page); print('wrote', a.out)

if __name__ == '__main__':
    main()
