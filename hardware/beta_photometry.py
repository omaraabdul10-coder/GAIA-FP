"""beta from two short videos of the STOPPED arm: LED1 alone, then LED2 alone (same camera settings).
Usage: python beta_photometry.py led1_only.mp4 led2_only.mp4
beta = S2/(S1+S2); S = background-subtracted light inside one fixed circular aperture, averaged over frames."""
import sys, json, numpy as np
from photocentre_track import read_video, _gray

def flux(path, ap_frac=0.45):
    fr = [_gray(f) for f in read_video(path)]
    g = np.mean(fr, axis=0)
    h, w = g.shape
    yy, xx = np.indices(g.shape)
    cy, cx = np.unravel_index(np.argmax(g), g.shape)
    r = ap_frac * min(h, w)
    m = np.hypot(xx - cx, yy - cy) <= r
    bg = np.median(g[~m])
    per = [(_f - bg)[m].sum() for _f in fr]
    return float(np.mean(per)), float(np.std(per) / np.sqrt(len(per))), float(g.max())

if __name__ == '__main__':
    s1, e1, p1 = flux(sys.argv[1]); s2, e2, p2 = flux(sys.argv[2])
    beta = s2 / (s1 + s2)
    err = np.hypot(s1 * e2, s2 * e1) / (s1 + s2) ** 2
    print(json.dumps(dict(S1=s1, S2=s2, beta=beta, beta_err=err, peak1=p1, peak2=p2,
                          warning=('peak >= 250: saturated, lower exposure' if max(p1, p2) >= 250 else None)), indent=1))
