"""Fixed matched development-only test of EDA/temperature additions."""
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[1]
OUT = BASE / 'skin_model'
DATA = ROOT / 'dataset/big_ideas_1_1_3'
f = np.load(BASE / 'development_features.npz', allow_pickle=False)
X, Y, G, times = f['X'], f['Y'], f['G'], f['times']
assert set(G) <= set(range(1, 9))
hashes = {r.split()[1]: r.split()[0] for r in (DATA/'SHA256SUMS.txt').read_text().splitlines()}
extra, quality = {}, []
for modality in ['EDA', 'TEMP']:
    z = np.full((len(G), 12), np.nan)
    for pid in np.unique(G):
        path = f'{pid:03}/{modality}_{pid:03}.csv'
        rawfile = DATA/path
        assert hashlib.sha256(rawfile.read_bytes()).hexdigest() == hashes[path]
        raw = pd.read_csv(rawfile)
        raw.columns = raw.columns.str.strip().str.lower()
        assert {'datetime', modality.lower()} <= set(raw.columns), raw.columns
        raw['datetime'] = pd.to_datetime(raw['datetime'], errors='raise')
        raw[modality.lower()] = pd.to_numeric(raw[modality.lower()], errors='raise')
        assert np.isfinite(raw[modality.lower()]).all()
        assert raw.datetime.is_monotonic_increasing
        series = raw.set_index('datetime')[modality.lower()].resample('1min').median()
        quality.append(dict(pid=int(pid), modality=modality, rows=len(raw),
                            first_time=str(series.index.min()), last_time=str(series.index.max()),
                            minimum=float(raw[modality.lower()].min()), maximum=float(raw[modality.lower()].max())))
        for i in np.flatnonzero(G == pid):
            t = pd.Timestamp(str(times[i]))
            v = []
            for a, b in [(-30,0), (0,60), (60,120), (120,180)]:
                index = pd.date_range(t + pd.Timedelta(minutes=a), periods=b-a, freq='min')
                values = series.reindex(index)
                coverage = float(values.notna().mean())
                v.extend([float(values.mean()) if coverage >= .5 else np.nan,
                          float(values.std()) if coverage >= .5 else np.nan, coverage])
            z[i] = v
        print('extracted', pid, modality, flush=True)
    extra[modality] = z
np.savez(OUT/'features.npz', **extra)
(OUT/'quality.json').write_text(json.dumps(quality, indent=2))
views = {'glucose': X, 'glucose_eda': np.c_[X, extra['EDA']],
         'glucose_temperature': np.c_[X, extra['TEMP']],
         'glucose_both': np.c_[X, extra['EDA'], extra['TEMP']]}
rows, splits = [], []
macros = ['total_carb','protein','total_fat']
for pid in np.unique(G):
    order = np.flatnonzero(G == pid)
    order = order[np.argsort(times[order])]
    if len(order) <= 4:
        continue
    ci, qi = order[:4], order[4:]
    tr = np.flatnonzero(G != pid)
    assert pd.Timestamp(str(times[ci[-1]])).value+180*60*10**9 < pd.Timestamp(str(times[qi[0]])).value
    assert not set(tr) & set(np.r_[ci,qi])
    splits.append(dict(pid=int(pid), training_people=[int(p) for p in np.unique(G[tr])],
                       calibration_times=times[ci].tolist(), query_times=times[qi].tolist()))
    estimates = {'no_sensor_median': np.tile(np.median(Y[ci], axis=0), (len(qi),1))}
    for view, x in views.items():
        imputer = SimpleImputer(add_indicator=True).fit(x[tr])
        xt, xc, xq = [imputer.transform(x[ix]) for ix in [tr,ci,qi]]
        scaler = StandardScaler().fit(xt)
        xt, xc, xq = [scaler.transform(z) for z in [xt,xc,xq]]
        counts = pd.Series(G[tr]).value_counts()
        weights = np.array([1/counts[p] for p in G[tr]])
        weights *= len(weights)/weights.sum()
        model = Ridge(alpha=100).fit(xt, Y[tr], sample_weight=weights)
        residual = Y[ci]-model.predict(xc)
        offset = residual.mean(axis=0)
        def kernel(a,b):
            return np.exp(-((a[:,None]-b[None])**2).mean(axis=2)/2)
        coef = np.linalg.solve(kernel(xc,xc)+np.eye(len(ci)), residual-offset)
        estimates[view] = model.predict(xq)+offset+kernel(xq,xc)@coef
    for view, guesses in estimates.items():
        for j,i in enumerate(qi):
            guess = np.maximum(guesses[j], 0)
            r = dict(pid=int(pid), time=str(times[i]), view=view,
                     all_three_within10=bool((abs(guess-Y[i])<=.1*Y[i]+1e-9).all()))
            for k,m in enumerate(macros):
                r[m+'_actual'],r[m+'_predicted']=Y[i,k],guess[k]
            rows.append(r)
d = pd.DataFrame(rows)
assert not d.duplicated(['pid','time','view']).any()
old = pd.read_csv(BASE/'development_model/predictions.csv')
old = old[old.method.eq('personal_kernel_1')].sort_values(['pid','time'])
now = d[d.view.eq('glucose')].sort_values(['pid','time'])
assert list(zip(old.pid,old.time)) == list(zip(now.pid,now.time))
for m in macros:
    assert np.allclose(old[m+'_predicted'],now[m+'_predicted'],atol=1e-8,rtol=0)
summaries = []
for view,z in d.groupby('view'):
    assert len(z)==65 and z.pid.nunique()==5
    a = z[[m+'_actual' for m in macros]].to_numpy()
    b = z[[m+'_predicted' for m in macros]].to_numpy()
    assert np.array_equal((abs(a-b)<=.1*a+1e-9).all(axis=1), z.all_three_within10)
    summaries.append(dict(view=view, meals=len(z), hits=int(z.all_three_within10.sum()),
                          MAE={m:float(abs(z[m+'_actual']-z[m+'_predicted']).mean()) for m in macros}))
d.to_csv(OUT/'predictions.csv',index=False)
(OUT/'summary.json').write_text(json.dumps(summaries,indent=2))
(OUT/'split_manifest.json').write_text(json.dumps(splits,indent=2))
(OUT/'run_manifest.json').write_text(json.dumps(dict(primary='glucose_both',
    script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    raw_hashes_verified=True, original_glucose_reproduced=True,
    reserved_participants_accessed=False, heldout_meals=65,
    feature_cache_sha256=hashlib.sha256((BASE/'development_features.npz').read_bytes()).hexdigest()),indent=2))
print(json.dumps(summaries,indent=2))
