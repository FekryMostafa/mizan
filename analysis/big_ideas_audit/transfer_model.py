"""Train on CGMacros; calibrate and evaluate on BIG IDEAs development only."""
from pathlib import Path
import json, hashlib, os
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from sklearn.ensemble import ExtraTreesRegressor, HistGradientBoostingRegressor
from sklearn.multioutput import MultiOutputRegressor

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[1]
OUT = BASE / 'transfer_model'
OUT.mkdir(exist_ok=True)
source = pd.read_csv(ROOT / 'analysis/cgm_fat_audit/full_audit/events_and_features.csv', parse_dates=['time'])
sensor = 'Dexcom GL'
source = source[(source['Amount Consumed'] == 100) & source[sensor + '_valid180'] &
                (source.Calories > 0) & (source.Fiber <= source.Carbs) &
                (abs(source.kcal_difference / source.Calories) <= .2)]
features, labels, people, ids = [], [], [], []
for pid, meals in source.groupby('pid'):
    raw = pd.read_csv(ROOT / f'dataset/csv/CGMacros-{pid:03}.csv', parse_dates=['Timestamp']).set_index('Timestamp')
    for r in meals.itertuples(index=False):
        times = r.time + pd.to_timedelta(np.r_[-10, -5, np.arange(0, 181, 15)], unit='m')
        glucose = raw[sensor].reindex(times).to_numpy(float)
        if not np.isfinite(glucose).all():
            continue
        base = np.median(glucose[:2])
        features.append(np.r_[glucose[2:] - base, base, (glucose[1] - glucose[0]) / 5])
        labels.append([r.Carbs, r.Protein, r.Fat])
        people.append(pid)
        ids.append(r.id)
xs, ys, gs = np.array(features), np.array(labels), np.array(people)
if os.environ.get('TRANSFER_EXPORT_ONLY') == '1':
    np.savez(BASE / 'source_features.npz', X=xs, Y=ys, G=gs, ids=np.array(ids, dtype=str))
    print('Exported CGMacros source features; no target data opened.')
    raise SystemExit(0)
data = np.load(BASE / 'development_features.npz', allow_pickle=False)
x, y, g, times = [data[k] for k in ['X', 'Y', 'G', 'times']]
split = json.loads((ROOT / 'dataset/big_ideas_1_1_3/RESERVED_SPLIT.json').read_text())
assert set(g) <= set(split['development_participants'])
assert xs.shape[1] == x.shape[1] == 15
scale = StandardScaler().fit(xs)
xs, x = scale.transform(xs), scale.transform(x)
counts = pd.Series(gs).value_counts()
w = np.array([1 / counts[p] for p in gs]); w *= len(w) / w.sum()
models = dict(ridge100=Ridge(alpha=100),
              trees5=ExtraTreesRegressor(n_estimators=200, min_samples_leaf=5, random_state=20260908, n_jobs=1),
              median_boost=MultiOutputRegressor(HistGradientBoostingRegressor(loss='absolute_error', max_iter=100,
                  max_leaf_nodes=7, min_samples_leaf=15, l2_regularization=2, random_state=20260908)))
rows, manifest = [], []
for name, model in models.items():
    model.fit(xs, ys, sample_weight=w)
    predictions = model.predict(x)
    for pid in np.unique(g):
        order = np.flatnonzero(g == pid)
        order = order[np.argsort(times[order])]
        if len(order) <= 4:
            continue
        ci, qi = order[:4], order[4:]
        assert pd.Timestamp(str(times[ci[-1]])).value + 180 * 60 * 10**9 < pd.Timestamp(str(times[qi[0]])).value
        residual = y[ci] - predictions[ci]
        offset = residual.mean(axis=0)
        def kernel(a, b):
            return np.exp(-((a[:, None] - b[None]) ** 2).mean(axis=2) / 2)
        weights = np.linalg.solve(kernel(x[ci], x[ci]) + np.eye(4), residual - offset)
        versions = dict(population=predictions[qi], offset=predictions[qi] + offset,
                        kernel=predictions[qi] + offset + kernel(x[qi], x[ci]) @ weights)
        if name == 'ridge100':
            manifest.append(dict(pid=int(pid), calibration_times=times[ci].tolist(), query_times=times[qi].tolist()))
        for variant, guesses in versions.items():
            for j, i in enumerate(qi):
                guess = np.maximum(guesses[j], 0)
                row = dict(pid=int(pid), time=times[i], method=name + '/' + variant,
                           all_three_within10=bool((abs(guess - y[i]) <= .1 * y[i] + 1e-9).all()))
                for k, m in enumerate(['Carbs', 'Protein', 'Fat']):
                    row[m + '_actual'], row[m + '_predicted'] = y[i, k], guess[k]
                rows.append(row)
    print(name, 'completed', flush=True)
d = pd.DataFrame(rows)
assert not d.duplicated(['pid', 'time', 'method']).any()
d.to_csv(OUT / 'predictions.csv', index=False)
summary = []
for method, z in d.groupby('method'):
    summary.append(dict(method=method, meals=len(z), people=int(z.pid.nunique()), hits=int(z.all_three_within10.sum()),
                        MAE={m: float(abs(z[m + '_actual'] - z[m + '_predicted']).mean()) for m in ['Carbs','Protein','Fat']}))
(OUT / 'summary.json').write_text(json.dumps(summary, indent=2))
(OUT / 'split_manifest.json').write_text(json.dumps(dict(source_dataset='CGMacros', source_people=len(np.unique(gs)),
    source_rows=len(ys), source_ids=ids, target_dataset='BIG IDEAs development participants only', calibration=manifest), indent=2))
(OUT / 'run_manifest.json').write_text(json.dumps(dict(primary='trees5/kernel',
    script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    target_features_sha256=hashlib.sha256((BASE / 'development_features.npz').read_bytes()).hexdigest(),
    reserved_participants_accessed=False, tuned_on_target_results=False,
    caveat='Source and development cohorts already inspected. Fixed exploratory comparisons, not untouched validation.'), indent=2))
print(json.dumps(summary, indent=2))
