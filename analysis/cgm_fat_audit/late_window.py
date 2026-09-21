"""Matched 3h versus 5h test. Fixed models; no outcome-based selection."""
from pathlib import Path
import json
import hashlib
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[1]
OUT = BASE / 'late_window'
OUT.mkdir(exist_ok=True)
REC = ['reference', 'carb_low', 'protein_high', 'fat_high']
MAC = ['Carbs', 'Protein', 'Fat']
e = pd.read_csv(BASE / 'full_audit/events_and_features.csv', parse_dates=['time']).set_index('id')
rows, manifests = [], []
for sensor in ['Libre GL', 'Dexcom GL']:
    v = e[(e['Amount Consumed'] == 100) & e[sensor + '_valid300'] & (e.Calories > 0) &
          (e.Fiber <= e.Carbs) & (abs(e.kcal_difference / e.Calories) <= .2)]
    traces = {}
    for pid, x in v.groupby('pid'):
        raw = pd.read_csv(ROOT / f'dataset/csv/CGMacros-{pid:03}.csv', parse_dates=['Timestamp']).set_index('Timestamp')
        for rid, r in x.iterrows():
            signal = raw[sensor].reindex(r.time + pd.to_timedelta(np.arange(0, 301, 15), unit='m')).to_numpy(float) - r[sensor + '_base']
            if np.isfinite(signal).all() and np.isfinite(r[sensor + '_slope30']):
                traces[rid] = signal
    ids = list(traces)
    v = v.loc[ids]
    g = v.pid.to_numpy()
    y = v[MAC].to_numpy(float)
    for pid, x in v.groupby('pid'):
        x = x.sort_values('time')
        c = x[x.recipe.isin(REC)].groupby('recipe', sort=False).head(1)
        if c.recipe.nunique() != 4:
            continue
        q = x[x.time > c.time.max()]
        if q.empty:
            continue
        tr = np.flatnonzero(g != pid)
        ci = np.array([ids.index(r) for r in c.index])
        qi = np.array([ids.index(r) for r in q.index])
        assert not set(tr) & set(np.r_[ci, qi])
        assert c.time.max() < q.time.min()
        manifests.append(dict(sensor=sensor, pid=int(pid), calibration_ids=list(c.index),
                              query_ids=list(q.index), training_ids=[ids[i] for i in tr]))
        for h in [180, 300]:
            z = np.array([np.r_[traces[r][:h // 15 + 1], v.loc[r, sensor + '_base'], v.loc[r, sensor + '_slope30']] for r in ids])
            scale = StandardScaler().fit(z[tr])
            xt, xc, xq = [scale.transform(z[a]) for a in [tr, ci, qi]]
            counts = pd.Series(g[tr]).value_counts()
            w = np.array([1 / counts[p] for p in g[tr]])
            w *= len(w) / w.sum()
            model = Ridge(alpha=100).fit(xt, y[tr], sample_weight=w)
            pooled = model.predict(xq)
            adapt = Ridge(alpha=10).fit(xc, y[ci] - model.predict(xc))
            # Nearest menu control uses only signals, not query labels.
            a = np.array([traces[ids[i]][:h // 15 + 1] for i in ci])
            b = np.array([traces[ids[i]][:h // 15 + 1] for i in qi])
            closest = ((b[:, None] - a[None]) ** 2).mean(axis=2).argmin(axis=1)
            preds = dict(population_linear=pooled, personal_linear_10=pooled + adapt.predict(xq),
                         nearest_calibrated_menu=y[ci[closest]],
                         no_sensor_median=np.tile(np.median(y[ci], axis=0), (len(qi), 1)))
            for method, guesses in preds.items():
                for j, i in enumerate(qi):
                    truth = y[i]
                    estimate = np.maximum(guesses[j], 0)
                    seen = bool(np.isclose(y[ci], truth).all(axis=1).any())
                    row = dict(sensor=sensor, pid=int(pid), id=ids[i], minutes=h, method=method,
                               calibrated_macros=seen, all_three_within10=bool((abs(estimate - truth) <= .1 * truth + 1e-9).all()))
                    for k, m in enumerate(MAC):
                        row[m + '_actual'], row[m + '_predicted'] = truth[k], estimate[k]
                    rows.append(row)
d = pd.DataFrame(rows)
assert not d.duplicated(['sensor', 'id', 'minutes', 'method']).any()
for (s, method), x in d.groupby(['sensor', 'method']):
    assert set(x[x.minutes == 180].id) == set(x[x.minutes == 300].id)
d.to_csv(OUT / 'predictions.csv', index=False)
summary = []
for (s, h, method), x in d.groupby(['sensor', 'minutes', 'method']):
    for scope, sub in [('all', x), ('calibrated', x[x.calibrated_macros]), ('unfamiliar', x[~x.calibrated_macros])]:
        if len(sub):
            summary.append(dict(sensor=s, minutes=int(h), method=method, scope=scope, meals=len(sub),
                                people=int(sub.pid.nunique()), hits=int(sub.all_three_within10.sum()),
                                MAE={m: float(abs(sub[m + '_actual'] - sub[m + '_predicted']).mean()) for m in MAC}))
(OUT / 'summary.json').write_text(json.dumps(summary, indent=2))
(OUT / 'split_manifest.json').write_text(json.dumps(manifests, indent=2))
(OUT / 'run_manifest.json').write_text(json.dumps(dict(script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    primary='personal_linear_10', tuned_on_test=False, matched_query_sets=True,
    limitation='Small retrospective selected subset. Meal timing and five-hour isolation obtained from logs.'), indent=2))
print(json.dumps([s for s in summary if s['method'] == 'personal_linear_10'], indent=2))
