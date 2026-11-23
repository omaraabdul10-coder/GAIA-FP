"""Check photocentre_track.py on synthetic camera frames before building anything.
Two Gaussian 'LEDs' (blended: PSF sigma > separation) orbit their barycentre.
Expected photocentre radius: d * |B - beta|, B = m2/(m1+m2) (pivot position), beta = L2/(L1+L2)."""
import numpy as np, json
from photocentre_track import track, fit_circle
rng = np.random.default_rng(1)
H = W = 400; px_per_mm = 2.0           # 0.5 mm per pixel
d_mm, B, sig_px = 20.0, 0.30, 14.0     # 20 mm arm, pivot at B=0.3, defocused PSF (sigma 7 mm > d)
yy, xx = np.indices((H, W))
def frame(phi, beta, peak=200.0, noise=2.0):
    r1, r2 = d_mm * B * px_per_mm, d_mm * (1 - B) * px_per_mm
    c = np.array([W / 2, H / 2])
    p1 = c + r1 * np.array([np.cos(phi), np.sin(phi)])
    p2 = c - r2 * np.array([np.cos(phi), np.sin(phi)])
    img = ((1 - beta) * np.exp(-((xx - p1[0])**2 + (yy - p1[1])**2) / (2 * sig_px**2))
           + beta * np.exp(-((xx - p2[0])**2 + (yy - p2[1])**2) / (2 * sig_px**2)))
    img = 10 + peak * img / img.max() + rng.normal(0, noise, img.shape)
    return np.clip(np.round(img), 0, 255).astype(np.uint8)
rows = []
for beta in [0.0, 0.1, 0.2, 0.3, 0.4, 0.5]:
    frames = [frame(phi, beta) for phi in np.linspace(0, 4 * np.pi, 240)]
    pts = track(frames, thresh=0.15)
    (cx, cy, r), sr, sc = fit_circle(pts[:, 0], pts[:, 1])
    rows.append(dict(beta=beta, expected_mm=round(d_mm * abs(B - beta), 3),
                     measured_mm=round(r / px_per_mm, 3), err_mm=round(sr / px_per_mm, 3)))
print(json.dumps(rows, indent=1))
