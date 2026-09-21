"""Empirical macro-to-glucose model, personally calibrated, inverted for grams.

Polynomial interactions are a model assumption, not a physiological law.
All settings fixed before execution. Target participants are development only.
"""
from pathlib import Path
import json, hashlib
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler, PolynomialFeatures
from sklearn.linear_model import Ridge
from scipy.optimize import least_squares

BASE = Path(__file__).resolve().parent
OUT = BASE / 'forward_inverse'
OUT.mkdir(exist_ok=True)
s = np.load(BASE / 'source_features.npz', allow_pickle=False)
t = np.load(BASE / 'development_features.npz', allow_pickle=False)
X, Y, G = s['X'], s['Y'], s['G']
x, y, g, times = t['X'], t['Y'], t['G'], t['times']
assert set(g) <= set(range(1, 9))
macro_scale = np.array([50., 25., 20.])
inputs = np.c_[Y / macro_scale, X[:, 13:]]
scaler = StandardScaler().fit(inputs)
poly = PolynomialFeatures(degree=2, include_bias=False)
design = poly.fit_transform(scaler.transform(inputs))
counts = pd.Series(G).value_counts()
w = np.array([1 / counts[p] for p in G]); w *= len(w) / w.sum()
model = Ridge(alpha=100).fit(design, X[:, :13], sample_weight=w)

def forward(macros, state):
    a = np.c_[np.atleast_2d(macros) / macro_scale, np.atleast_2d(state)]
    return model.predict(poly.transform(scaler.transform(a)))

upper = np.maximum(Y.max(axis=0) * 1.25, [200, 100, 100]) / macro_scale
rows, manifest = [], []
for pid in np.unique(g):
    order = np.flatnonzero(g == pid)
    order = order[np.argsort(times[order])]
    if len(order) <= 4:
        continue
    ci, qi = order[:4], order[4:]
    assert pd.Timestamp(str(times[ci[-1]])).value + 180 * 60 * 10**9 < pd.Timestamp(str(times[qi[0]])).value
    cal_prediction = forward(y[ci], x[ci, 13:])
    centered_pred = cal_prediction - cal_prediction.mean(axis=0)
    centered_observed = x[ci, :13] - x[ci, :13].mean(axis=0)
    gain = float(np.clip((centered_pred * centered_observed).sum() / max((centered_pred ** 2).sum(), 1e-9), .1, 10))
    offset = (x[ci, :13] - gain * cal_prediction).mean(axis=0)
    prior = np.median(y[ci], axis=0) / macro_scale
    starts = [np.clip(prior, 1e-6, upper - 1e-6), np.minimum([1, 1, 1], upper - 1e-6), np.minimum([2, 2, 2], upper - 1e-6)]
    manifest.append(dict(pid=int(pid), gain=gain, calibration_times=times[ci].tolist(), query_times=times[qi].tolist()))
    for i in qi:
        for lam in [0., .1, 1.]:
            def residual(z):
                curve = gain * forward(z * macro_scale, x[i, 13:])[0] + offset
                return np.r_[(curve - x[i, :13]) / (20 * np.sqrt(13)), np.sqrt(lam) * (z - prior)]
            fits = [least_squares(residual, start, bounds=(np.zeros(3), upper), max_nfev=150,
                                  ftol=1e-7, xtol=1e-7, gtol=1e-7) for start in starts]
            best = min(fits, key=lambda fit: np.square(fit.fun).sum())
            guess = best.x * macro_scale
            predicted_curve = gain * forward(guess, x[i, 13:])[0] + offset
            # True grams are used ONLY here, after decoding, for diagnosis/evaluation.
            true_curve = gain * forward(y[i], x[i, 13:])[0] + offset
            row = dict(pid=int(pid), time=times[i], prior_strength=lam, converged=bool(best.success),
                       all_three_within10=bool((abs(guess - y[i]) <= .1 * y[i] + 1e-9).all()),
                       decoded_curve_RMSE=float(np.sqrt(np.mean((predicted_curve - x[i, :13]) ** 2))),
                       true_grams_curve_RMSE=float(np.sqrt(np.mean((true_curve - x[i, :13]) ** 2))),
                       objective=float(np.square(best.fun).sum()))
            for k, m in enumerate(['Carbs','Protein','Fat']):
                row[m + '_actual'], row[m + '_predicted'] = y[i, k], guess[k]
            rows.append(row)
    print('Participant', pid, 'completed', flush=True)
d = pd.DataFrame(rows)
d.to_csv(OUT / 'predictions.csv', index=False)
summary = []
for lam, z in d.groupby('prior_strength'):
    summary.append(dict(prior_strength=float(lam), meals=len(z), people=int(z.pid.nunique()),
                        hits=int(z.all_three_within10.sum()), converged=int(z.converged.sum()),
                        MAE={m: float(abs(z[m + '_actual'] - z[m + '_predicted']).mean()) for m in ['Carbs','Protein','Fat']},
                        median_decoded_curve_RMSE=float(z.decoded_curve_RMSE.median()),
                        median_true_grams_curve_RMSE=float(z.true_grams_curve_RMSE.median())))
(OUT / 'summary.json').write_text(json.dumps(summary, indent=2))
(OUT / 'split_manifest.json').write_text(json.dumps(manifest, indent=2))
(OUT / 'run_manifest.json').write_text(json.dumps(dict(primary_prior_strength=.1, source_meals=len(Y), source_people=len(np.unique(G)),
    reserved_accessed=False, script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    hypothesis='Quadratic empirical macro effects with personal gain and curve offset; not mechanistic physiology.'), indent=2))
print(json.dumps(summary, indent=2))
