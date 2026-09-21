"""Fixed matched comparison of glucose, heart rate and their combination."""
from pathlib import Path
import json, hashlib
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.ensemble import ExtraTreesRegressor

BASE = Path(__file__).resolve().parent
OUT = BASE / 'hr_model'; OUT.mkdir(exist_ok=True)
s = np.load(BASE / 'source_features.npz', allow_pickle=False)
t = np.load(BASE / 'development_features.npz', allow_pickle=False)
h = np.load(BASE / 'hr_features.npz', allow_pickle=False)
Y, G = s['Y'], s['G']
y, g, times = t['Y'], t['G'], t['times']
assert set(g) <= set(range(1, 9))
counts = pd.Series(G).value_counts()
w = np.array([1 / counts[p] for p in G]); w *= len(w) / w.sum()
rows = []
views = dict(glucose=(s['X'], t['X']), heart_rate=(h['source'], h['target']),
             combined=(np.c_[s['X'], h['source']], np.c_[t['X'], h['target']]))
for view, (source, target) in views.items():
    imputer = SimpleImputer(add_indicator=True).fit(source)
    train, target = imputer.transform(source), imputer.transform(target)
    scale = StandardScaler().fit(train)
    train, target = scale.transform(train), scale.transform(target)
    model = ExtraTreesRegressor(n_estimators=200, min_samples_leaf=5, random_state=20260908, n_jobs=1)
    model.fit(train, Y, sample_weight=w)
    for pid in np.unique(g):
        order = np.flatnonzero(g == pid); order = order[np.argsort(times[order])]
        if len(order) <= 4:
            continue
        ci, qi = order[:4], order[4:]
        assert pd.Timestamp(str(times[ci[-1]])).value + 180*60*10**9 < pd.Timestamp(str(times[qi[0]])).value
        residual = y[ci] - model.predict(target[ci]); offset = residual.mean(axis=0)
        def kernel(a, b):
            return np.exp(-((a[:, None] - b[None]) ** 2).mean(axis=2) / 2)
        coef = np.linalg.solve(kernel(target[ci], target[ci]) + np.eye(4), residual - offset)
        guess = np.maximum(model.predict(target[qi]) + offset + kernel(target[qi], target[ci]) @ coef, 0)
        for j, i in enumerate(qi):
            row = dict(pid=int(pid), time=times[i], view=view,
                       all_three_within10=bool((abs(guess[j] - y[i]) <= .1*y[i]+1e-9).all()))
            for k, m in enumerate(['Carbs','Protein','Fat']):
                row[m+'_actual'], row[m+'_predicted'] = y[i,k], guess[j,k]
            rows.append(row)
    print(view, 'completed', flush=True)
d = pd.DataFrame(rows); d.to_csv(OUT / 'predictions.csv', index=False)
summary = []
for view, z in d.groupby('view'):
    summary.append(dict(view=view, meals=len(z), people=int(z.pid.nunique()), hits=int(z.all_three_within10.sum()),
        MAE={m: float(abs(z[m+'_actual']-z[m+'_predicted']).mean()) for m in ['Carbs','Protein','Fat']}))
(OUT / 'summary.json').write_text(json.dumps(summary, indent=2))
old = pd.read_csv(BASE / 'transfer_model/predictions.csv')
old = old[old.method=='trees5/kernel'].sort_values(['pid','time'])
now = d[d.view=='glucose'].sort_values(['pid','time'])
assert list(zip(old.pid,old.time)) == list(zip(now.pid,now.time))
for m in ['Carbs','Protein','Fat']:
    assert np.allclose(old[m+'_predicted'], now[m+'_predicted'], atol=1e-10)
(OUT / 'run_manifest.json').write_text(json.dumps(dict(primary='combined', reserved_accessed=False,
    original_glucose_predictions_reproduced=True, script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    hr_features_sha256=hashlib.sha256((BASE/'hr_features.npz').read_bytes()).hexdigest(),
    note='Fixed development comparison; training-only imputation/scaling; no query removed for missing heart rate.'), indent=2))
print(json.dumps(summary, indent=2))
