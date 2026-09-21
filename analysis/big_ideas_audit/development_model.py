"""Development-only continuous prediction with four chronological onboarding meals."""
from pathlib import Path
import json, hashlib, os
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge

ROOT = Path(__file__).resolve().parents[2]
BASE = Path(__file__).resolve().parent
CALIBRATION = int(os.environ.get('BIG_IDEAS_CALIBRATION', '4'))
QUERY_START = int(os.environ.get('BIG_IDEAS_QUERY_START', str(CALIBRATION)))
assert 4 <= CALIBRATION <= QUERY_START
OUT = BASE / ('development_model' if CALIBRATION == QUERY_START == 4 else f'calibration_{CALIBRATION}_after_{QUERY_START}')
OUT.mkdir(exist_ok=True)
DATA = ROOT / 'dataset/big_ideas_1_1_3'
split = json.loads((DATA / 'RESERVED_SPLIT.json').read_text())
e = pd.read_csv(BASE / 'development_meals.csv', parse_dates=['time'])
assert set(e.pid).issubset(split['development_participants'])
e = e[e.eligible_3h].copy()
mac = ['total_carb', 'protein', 'total_fat']
features, records = [], []
for pid, meals in e.groupby('pid'):
    assert pid in split['development_participants']
    raw = pd.read_csv(DATA / f'{pid:03}/Dexcom_{pid:03}.csv')
    raw = raw[raw['Event Type'] == 'EGV'].copy()
    raw['t'] = pd.to_datetime(raw['Timestamp (YYYY-MM-DDThh:mm:ss)'], errors='coerce')
    raw['v'] = pd.to_numeric(raw['Glucose Value (mg/dL)'], errors='coerce')
    raw = raw.dropna(subset=['t', 'v']).sort_values('t')
    gt = raw.t.astype('int64').to_numpy() / 1e9
    assert (np.diff(gt) > 0).all()
    for _, r in meals.iterrows():
        times = r.time.value / 1e9 + np.r_[-10, -5, np.arange(0, 181, 15)] * 60
        ix = np.searchsorted(gt, times)
        assert (ix > 0).all() and (ix < len(gt)).all()
        assert ((gt[ix] - gt[ix - 1]) <= 601).all()
        glucose = np.interp(times, gt, raw.v)
        base = np.median(glucose[:2])
        # Only glucose and premeal glucose state are predictors.
        features.append(np.r_[glucose[2:] - base, base, (glucose[1] - glucose[0]) / 5])
        records.append(r)
e = pd.DataFrame(records).reset_index(drop=True)
X = np.array(features)
Y = e[mac].to_numpy(float)
G = e.pid.to_numpy()
if os.environ.get('BIG_IDEAS_EXPORT_ONLY') == '1':
    np.savez(BASE / 'development_features.npz', X=X, Y=Y, G=G, times=e.time.astype(str).to_numpy(dtype=str))
    print('Exported development features only; reserved participants not opened.')
    raise SystemExit(0)
rows, manifests = [], []
for pid in np.unique(G):
    chronological = e[e.pid == pid].sort_values('time').index.to_numpy()
    if len(chronological) <= QUERY_START:
        continue
    ci, qi = chronological[:CALIBRATION], chronological[QUERY_START:]
    tr = np.flatnonzero(G != pid)
    assert not set(tr) & set(np.r_[ci, qi])
    assert pd.Timestamp(e.loc[ci, 'time'].max()) + pd.Timedelta(hours=3) < pd.Timestamp(e.loc[qi, 'time'].min())
    scaler = StandardScaler().fit(X[tr])
    xt, xc, xq = [scaler.transform(X[i]) for i in [tr, ci, qi]]
    counts = pd.Series(G[tr]).value_counts()
    w = np.array([1 / counts[p] for p in G[tr]])
    w *= len(w) / w.sum()
    fit = Ridge(alpha=100).fit(xt, Y[tr], sample_weight=w)
    pooled = fit.predict(xq)
    residual = Y[ci] - fit.predict(xc)
    local = Ridge(alpha=10).fit(xc, residual)
    def kernel(a, b):
        return np.exp(-((a[:, None] - b[None]) ** 2).mean(axis=2) / 2)
    offset = residual.mean(axis=0)
    weights = np.linalg.solve(kernel(xc, xc) + np.eye(len(ci)), residual - offset)
    nearest = ((xq[:, None] - xc[None]) ** 2).mean(axis=2).argmin(axis=1)
    estimates = dict(population_ridge=pooled, personal_offset=pooled + offset,
                     personal_linear_10=pooled + local.predict(xq),
                     personal_kernel_1=pooled + offset + kernel(xq, xc) @ weights,
                     nearest_onboarding=Y[ci[nearest]],
                     no_sensor_median=np.tile(np.median(Y[ci], axis=0), (len(qi), 1)))
    manifests.append(dict(pid=int(pid), training_people=[int(x) for x in np.unique(G[tr])],
                          calibration_times=e.loc[ci, 'time'].astype(str).tolist(),
                          query_times=e.loc[qi, 'time'].astype(str).tolist(),
                          calibration_macro_rank=int(np.linalg.matrix_rank(Y[ci][1:] - Y[ci][0]))))
    for method, pred in estimates.items():
        for j, i in enumerate(qi):
            guess = np.maximum(pred[j], 0)
            err = abs(guess - Y[i])
            row = dict(pid=int(pid), time=str(e.loc[i, 'time']), method=method,
                       familiar_macros=bool(np.isclose(Y[ci], Y[i]).all(axis=1).any()),
                       all_three_within10=bool((err <= .1 * Y[i] + 1e-9).all()))
            for k, m in enumerate(mac):
                row[m + '_actual'], row[m + '_predicted'] = Y[i, k], guess[k]
            rows.append(row)
d = pd.DataFrame(rows)
assert not d.duplicated(['pid', 'time', 'method']).any()
d.to_csv(OUT / 'predictions.csv', index=False)
summary = []
for method, x in d.groupby('method'):
    for scope, sub in [('all', x), ('unfamiliar_macros', x[~x.familiar_macros])]:
        summary.append(dict(method=method, scope=scope, meals=len(sub), people=int(sub.pid.nunique()),
                            hits=int(sub.all_three_within10.sum()),
                            MAE={m: float(abs(sub[m + '_actual'] - sub[m + '_predicted']).mean()) for m in mac}))
(OUT / 'summary.json').write_text(json.dumps(summary, indent=2))
(OUT / 'split_manifest.json').write_text(json.dumps(manifests, indent=2))
(OUT / 'run_manifest.json').write_text(json.dumps(dict(primary='personal_kernel_1',
    script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    reserved_participants_accessed=False, hyperparameters_selected_from_test=False,
    calibration_meals=CALIBRATION, query_start=QUERY_START,
    note='Fixed exploratory methods on development participants only; no independent validation claimed.'), indent=2))
print(json.dumps(summary, indent=2))
