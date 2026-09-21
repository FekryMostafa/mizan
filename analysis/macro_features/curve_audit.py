"""Descriptive same-person curve comparisons; no fitted gram predictor."""
from pathlib import Path
import json
import hashlib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

B = Path(__file__).resolve().parent
ROOT = B.parents[1]
O = B / 'curve_audit'
O.mkdir(exist_ok=True)
f = pd.read_csv(B / 'features.csv')
f['time'] = pd.to_datetime(f.time, format='mixed')
grid = np.r_[-10, -5, np.arange(0, 181, 5)]
curves = []
for (dataset, pid), meals in f.groupby(['dataset', 'pid'], sort=False):
    if dataset == 'CGMacros':
        raw = pd.read_csv(ROOT / f'dataset/csv/CGMacros-{pid:03}.csv', usecols=['Timestamp', 'Dexcom GL'])
        stamps = pd.to_datetime(raw.Timestamp).astype('int64').to_numpy()
        values = raw['Dexcom GL'].to_numpy(float)
    else:
        assert pid <= 8
        raw = pd.read_csv(ROOT / f'dataset/big_ideas_1_1_3/{pid:03}/Dexcom_{pid:03}.csv')
        raw = raw[raw['Event Type'].eq('EGV')]
        stamps = pd.to_datetime(raw['Timestamp (YYYY-MM-DDThh:mm:ss)']).astype('int64').to_numpy()
        values = pd.to_numeric(raw['Glucose Value (mg/dL)'], errors='coerce').to_numpy(float)
    good = np.isfinite(values)
    stamps, values = stamps[good], values[good]
    assert (np.diff(stamps) > 0).all()
    for idx, row in meals.iterrows():
        target = row.time.value + grid * 60 * 10**9
        ix = np.searchsorted(stamps, target)
        if dataset == 'CGMacros':
            assert (ix < len(stamps)).all() and np.array_equal(stamps[ix], target)
            v = values[ix]
        else:
            assert (ix > 0).all() and (ix < len(stamps)).all()
            assert ((stamps[ix] - stamps[ix-1]) <= 601 * 10**9).all()
            v = np.interp((target-stamps[0])/1e9, (stamps-stamps[0])/1e9, values)
        v = v[2:] - np.median(v[:2])
        assert abs(v.max() - row.peak_height) < 1e-6
        curves.append((idx, v))
x = np.array([v for _, v in sorted(curves)])
assert x.shape == (738, 37)
np.savez_compressed(O / 'curves.npz', X=x, minutes=grid[2:])
pair_rows = []
for (dataset, pid), z in f.groupby(['dataset', 'pid']):
    for pos, i in enumerate(z.index):
        for j in z.index[:pos]:
            a, b = f.loc[i], f.loc[j]
            record = dict(dataset=dataset, pid=int(pid), i=int(i), j=int(j),
                          time_a=a.time.isoformat(), time_b=b.time.isoformat(),
                          curve_rmse=float(np.sqrt(np.mean((x[i]-x[j])**2))),
                          peak_difference=abs(a.peak_height-b.peak_height),
                          peak_time_difference=abs(a.peak_minute-b.peak_minute))
            record['exact_macro_repeat'] = bool(np.array_equal(a[['Carbs','Protein','Fat']].to_numpy(), b[['Carbs','Protein','Fat']].to_numpy()))
            for macro in ['Carbs', 'Protein', 'Fat']:
                record[macro+'_a'], record[macro+'_b'] = float(a[macro]), float(b[macro])
                # No single estimate can satisfy both +/-10% intervals if disjoint.
                record[macro+'_disjoint10'] = bool(.9 * max(a[macro], b[macro]) > 1.1 * min(a[macro], b[macro]) + 1e-9)
            pair_rows.append(record)
p = pd.DataFrame(pair_rows)
p.to_csv(O / 'same_person_pairs.csv', index=False)
f['late_fraction'] = f.late_positive_area / (f.early_positive_area + f.middle_positive_area + f.late_positive_area).replace(0, np.nan)
diagnostics = []
for dataset, z in p.groupby('dataset'):
    z = z[z.peak_difference.le(10) & z.Carbs_disjoint10]
    for feature in ['late_positive_area', 'tail_mean', 'peak_minute', 'late_fraction']:
        delta = f.loc[z.i, feature].to_numpy() - f.loc[z.j, feature].to_numpy()
        dc = z.Carbs_a.to_numpy() - z.Carbs_b.to_numpy()
        good = np.isfinite(delta) & (delta != 0)
        agreement = delta[good] * dc[good] > 0
        persons = pd.DataFrame(dict(pid=z.pid.to_numpy()[good], agreement=agreement))
        diagnostics.append(dict(dataset=dataset, feature=feature, pairs=int(good.sum()),
                                agreement=float(agreement.mean()),
                                person_balanced_agreement=float(persons.groupby('pid').agreement.mean().mean()),
                                people=int(persons.pid.nunique())))
pd.DataFrame(diagnostics).to_csv(O / 'similar_peak_diagnostics.csv', index=False)
summaries = []
for dataset, z in p.groupby('dataset'):
    repeats = z[z.exact_macro_repeat]
    threshold = float(repeats.curve_rmse.median())
    nearby = z[z.curve_rmse.le(threshold)]
    summaries.append(dict(dataset=dataset, pairs=len(z), repeat_pairs=len(repeats),
                          repeat_median_curve_rmse=threshold, nearby_pairs=len(nearby),
                          nearby_disjoint10_counts={m:int(nearby[m+'_disjoint10'].sum()) for m in ['Carbs','Protein','Fat']}))
(O / 'summary.json').write_text(json.dumps(summaries, indent=2))
example = f[f.dataset.eq('BIG_IDEAs_development') & f.pid.eq(6) & f.time.isin(pd.to_datetime(['2020-03-05 23:30', '2020-03-02 22:00', '2020-03-04 08:25']))]
assert len(example) == 3
fig, ax = plt.subplots(figsize=(9, 5))
for i, row in example.iterrows():
    ax.plot(grid[2:], x[i], label=f'{row.time:%b %d %H:%M}: {row.Carbs:g} g carbs')
ax.axhline(0, color='grey', lw=.6)
ax.set(xlabel='Minutes after recorded meal', ylabel='Glucose change from premeal baseline (mg/dL)', title='Same person: similar peaks can hide different curve timing')
ax.legend(); fig.tight_layout(); fig.savefig(O / 'carbohydrate_examples.png', dpi=150)
example.to_csv(O / 'example_features.csv', index=False)
example_pairs = p[p.i.isin(example.index) & p.j.isin(example.index)]
example_pairs.to_csv(O / 'example_pairs.csv', index=False)
(O / 'manifest.json').write_text(json.dumps(dict(input_sha256=hashlib.sha256((B/'features.csv').read_bytes()).hexdigest(),
    script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), rows=len(f), reserved_accessed=False,
    interpretation='Descriptive dependent pairs. Repeat median is a reference, not a sensor noise bound or a universal decision threshold.'), indent=2))
print(json.dumps(summaries, indent=2))
print(example[['time','Carbs','Protein','Fat','peak_minute','early_positive_area','middle_positive_area','late_positive_area']].to_string(index=False))
print(example_pairs[['Carbs_a','Carbs_b','curve_rmse','peak_time_difference']].to_string(index=False))
