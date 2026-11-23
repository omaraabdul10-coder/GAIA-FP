"""Photocentre bench: measure the wobble radius of a blended two-LED 'binary' from a video.

Usage:
  python photocentre_track.py VIDEO.mp4 --d-mm 60 --mm-per-px 0.25 [--roi x,y,w,h] [--thresh 0.15]

What it does:
  1. For every frame, takes the light-weighted centroid (first moment) of the bright blob,
     after subtracting the median background. This is what Gaia measures: one photocentre.
  2. Fits a circle to the centroid track (algebraic least squares, then geometric refinement).
  3. Reports the radius a0 (px and mm) and, if --d-mm is given, a0/d = |B - beta|.

The LEDs must be UNRESOLVED (defocus the camera until both LEDs merge into one blob), otherwise
you measure two separate stars, not a photocentre.
"""
import argparse, json, sys
import numpy as np


def centroid(frame, thresh):
    g = frame.astype(float)
    if g.ndim == 3:
        g = g.mean(axis=2)
    g = g - np.median(g)
    g[g < thresh * g.max()] = 0.0
    s = g.sum()
    if s <= 0:
        return np.nan, np.nan
    yy, xx = np.indices(g.shape)
    return (g * xx).sum() / s, (g * yy).sum() / s


def fit_circle(x, y):
    """Kasa algebraic fit, refined with Gauss-Newton on geometric distances."""
    A = np.c_[2 * x, 2 * y, np.ones_like(x)]
    b = x ** 2 + y ** 2
    cx, cy, c = np.linalg.lstsq(A, b, rcond=None)[0]
    r = np.sqrt(c + cx ** 2 + cy ** 2)
    p = np.array([cx, cy, r])
    for _ in range(50):
        dx, dy = x - p[0], y - p[1]
        di = np.hypot(dx, dy)
        res = di - p[2]
        J = np.c_[-dx / di, -dy / di, -np.ones_like(di)]
        step = np.linalg.lstsq(J, -res, rcond=None)[0]
        p += step
        if np.abs(step).max() < 1e-9:
            break
    res = np.hypot(x - p[0], y - p[1]) - p[2]
    # radius uncertainty from scatter (independent points)
    sig_r = res.std(ddof=3) / np.sqrt(len(x))
    return p, sig_r, res.std(ddof=3)


def _gray(f):
    g = f.astype(float)
    return g.mean(axis=2) if g.ndim == 3 else g


def track(frames, thresh=0.15, roi=None, ap_sigma=4.0):
    """Two passes. Pass 1: thresholded centroids, only to find where the blob is and how big.
    Pass 2: first moment inside ONE fixed circular aperture that covers the whole orbit, with no
    threshold. A threshold or a moving aperture clips the faint wing asymmetrically and biases the
    photocentre toward the brighter LED, so neither is used for the measurement."""
    frames = [(_gray(f[roi[1]:roi[1] + roi[3], roi[0]:roi[0] + roi[2]]) if roi else _gray(f)) for f in frames]
    p1, sizes = [], []
    for g in frames:
        g = g - np.median(g)
        m = g.copy(); m[m < thresh * m.max()] = 0
        s = m.sum()
        if s <= 0:
            continue
        yy, xx = np.indices(g.shape)
        cx, cy = (m * xx).sum() / s, (m * yy).sum() / s
        p1.append((cx, cy)); sizes.append(np.sqrt((m * ((xx - cx) ** 2 + (yy - cy) ** 2)).sum() / s / 2))
    p1 = np.array(p1)
    c0 = np.median(p1, axis=0)
    rad = np.max(np.hypot(*(p1 - c0).T)) + ap_sigma * np.median(sizes) * 1.6  # thresholded size underestimates sigma
    yy, xx = np.indices(frames[0].shape)
    mask = np.hypot(xx - c0[0], yy - c0[1]) <= rad
    if (np.hypot(xx - c0[0], yy - c0[1]) > rad).sum() < 100:
        raise SystemExit('aperture fills the frame: zoom out or crop less')
    pts = []
    for g in frames:
        bg = np.median(g[~mask])
        w = (g - bg) * mask
        s = w.sum()
        pts.append(((w * xx).sum() / s, (w * yy).sum() / s) if s > 0 else (np.nan, np.nan))
    pts = np.array(pts)
    return pts[np.isfinite(pts).all(axis=1)]


def read_video(path):
    import cv2
    cap = cv2.VideoCapture(path)
    while True:
        ok, f = cap.read()
        if not ok:
            break
        yield f
    cap.release()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('video')
    ap.add_argument('--d-mm', type=float, help='LED separation on the arm in mm')
    ap.add_argument('--mm-per-px', type=float, help='image scale (from a ruler in the frame)')
    ap.add_argument('--roi', help='x,y,w,h crop around the blob')
    ap.add_argument('--thresh', type=float, default=0.15)
    a = ap.parse_args()
    roi = tuple(int(v) for v in a.roi.split(',')) if a.roi else None
    pts = track(read_video(a.video), a.thresh, roi)
    if len(pts) < 20:
        sys.exit('too few frames with a detected blob')
    (cx, cy, r), sr, scatter = fit_circle(pts[:, 0], pts[:, 1])
    out = dict(n_frames=len(pts), radius_px=r, radius_err_px=sr, point_scatter_px=scatter)
    if a.mm_per_px:
        out.update(radius_mm=r * a.mm_per_px, radius_err_mm=sr * a.mm_per_px)
        if a.d_mm:
            out['abs_B_minus_beta'] = r * a.mm_per_px / a.d_mm
    print(json.dumps(out, indent=1))


if __name__ == '__main__':
    main()
