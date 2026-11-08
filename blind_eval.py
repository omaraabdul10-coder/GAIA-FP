"""
blind_eval.py — kor test protokolu + statistik qiymətləndirmə.

Addımlar (sıra pozula bilməz):
  1. freeze  : metod faylının və konfiqurasiyanın SHA-256 hash-i + etiket faylının hash-i log-a yazılır
               (etiket faylı OXUNMUR, yalnız hash-i alınır). Log GitHub-a commit edilir => zaman möhürü.
  2. score   : yalnız xüsusiyyət (feature) faylı ilə P(binary) hesablanır və saxlanılır.
  3. unblind : yalnız indi etiketlər açılır; ROC/AUC, işçi nöqtə, kalibrləmə, bootstrap CI.
"""
import hashlib, json, sys, numpy as np
from scipy.stats import beta as beta_dist

def sha256(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()

def freeze(method_files, config, label_file, log="freeze_log.json"):
    entry = dict(method={f: sha256(f) for f in method_files},
                 config=config, label_file_sha256=sha256(label_file))
    json.dump(entry, open(log, "w"), indent=2)
    return entry

# ------------------------------------------------------------- metrikalar
def roc_auc(score, y):
    """y=1: binar (impostor), score = P(binary). Mann–Whitney ilə AUC."""
    pos, neg = score[y == 1], score[y == 0]
    return (np.sum(pos[:, None] > neg[None, :]) + 0.5 * np.sum(pos[:, None] == neg[None, :])) / (len(pos) * len(neg))

def bootstrap_ci(fn, score, y, n=2000, seed=0):
    rng = np.random.default_rng(seed); vals = []
    for _ in range(n):
        i = rng.integers(0, len(y), len(y))
        if 0 < y[i].sum() < len(y):
            vals.append(fn(score[i], y[i]))
    return np.percentile(vals, [2.5, 97.5])

def clopper_pearson(k, n, a=0.05):
    lo = beta_dist.ppf(a / 2, k, n - k + 1) if k > 0 else 0.0
    hi = beta_dist.ppf(1 - a / 2, k + 1, n - k) if k < n else 1.0
    return lo, hi

def operating_point(score, y, planet_retention=0.90):
    """Planetlərin >= retention hissəsini saxlayan ən sərt hədd; neçə binar atılır?"""
    thr = np.quantile(score[y == 0], planet_retention)          # bu həddən yuxarı => 'binar' kimi at
    kept_planets = np.sum(score[y == 0] <= thr); n_p = np.sum(y == 0)
    rejected_bin = np.sum(score[y == 1] > thr); n_b = np.sum(y == 1)
    return dict(threshold=thr, planet_retention=(kept_planets, n_p, clopper_pearson(kept_planets, n_p)),
                binary_rejection=(rejected_bin, n_b, clopper_pearson(rejected_bin, n_b)))

def calibration(score, y, bins=5):
    edges = np.linspace(0, 1, bins + 1); out = []
    for a, b in zip(edges[:-1], edges[1:]):
        m = (score >= a) & (score < b if b < 1 else score <= b)
        if m.sum():
            out.append((round(a, 2), round(b, 2), int(m.sum()), float(score[m].mean()), float(y[m].mean())))
    return out, float(np.mean((score - y) ** 2))      # (bin cədvəli, Brier skoru)
