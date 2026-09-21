"""Fixed, person-held-out continuous gram models on ALL later eligible meals.

No query meal labels, meal type, calories, study day or participant ID are features.
Four earlier labeled calibration meals adjust the population predictor.
Primary method was specified before execution: personal_linear_10.
Other methods are sensitivity comparisons, not a selected final model.
"""
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).with_suffix('')
OUT.mkdir(exist_ok=True)
MAC = ['Carbs', 'Protein', 'Fat']
REC = ['reference', 'carb_low', 'protein_high', 'fat_high']
EVENTS = ROOT / 'analysis/cgm_fat_audit/full_audit/events_and_features.csv'


def run():
    e = pd.read_csv(EVENTS, parse_dates=['time']).set_index('id')
    rows, manifests, coverage = [], [], []
    for sensor in ['Libre GL', 'Dexcom GL']:
        valid = e[(e['Amount Consumed'] == 100) & e[sensor + '_valid180'] &
                  (e.Calories > 0) & (e.Fiber <= e.Carbs) &
                  (abs(e.kcal_difference / e.Calories) <= .2)].copy()
        feats = []
        for pid, group in valid.groupby('pid'):
            raw = pd.read_csv(ROOT / f'dataset/csv/CGMacros-{pid:03}.csv',
                              parse_dates=['Timestamp']).set_index('Timestamp')
            for rid, r in group.iterrows():
                signal = raw[sensor].reindex(r.time + pd.to_timedelta(
                    np.arange(0, 181, 15), unit='m')).to_numpy(float) - r[sensor + '_base']
                f = np.r_[signal, r[sensor + '_base'], r[sensor + '_slope30']]
                if np.isfinite(f).all():
                    feats.append((rid, f))
        ids = [x[0] for x in feats]
        valid = valid.loc[ids]
        X = np.array([x[1] for x in feats])
        Y = valid[MAC].to_numpy(float)
        G = valid.pid.to_numpy()
        for pid in np.unique(G):
            personal = valid[valid.pid == pid].sort_values('time')
            cal = personal[personal.recipe.isin(REC)].groupby('recipe', sort=False).head(1)
            if set(cal.recipe) != set(REC):
                continue
            cal = cal.set_index('recipe', drop=False).loc[REC].reset_index(drop=True)
            # Recover IDs explicitly from the chronological personal table.
            cal_ids = [personal[personal.recipe == r].index[0] for r in REC]
            cal = valid.loc[cal_ids]
            query = personal[personal.time > cal.time.max()]
            if query.empty:
                continue
            tr = np.flatnonzero(G != pid)
            ci = np.array([ids.index(i) for i in cal_ids])
            qi = np.array([ids.index(i) for i in query.index])
            assert not set(tr) & set(np.r_[ci, qi])
            assert cal.time.max() < query.time.min()
            scale = StandardScaler().fit(X[tr])
            xt, xc, xq = [scale.transform(X[a]) for a in [tr, ci, qi]]
            # Equal population weight per person, normalized to total training rows.
            counts = pd.Series(G[tr]).value_counts()
            w = np.array([1 / counts[p] for p in G[tr]])
            w *= len(w) / w.sum()
            shared = Ridge(alpha=100).fit(xt, Y[tr], sample_weight=w)
            base = shared.predict(xq)
            residual = Y[ci] - shared.predict(xc)
            pred = {'population_linear': base,
                    'personal_offset': base + residual.mean(axis=0),
                    'no_sensor_calibration_median': np.tile(np.median(Y[ci], axis=0), (len(qi), 1))}
            for lam in [1, 10, 100]:
                adapt = Ridge(alpha=lam).fit(xc, residual)
                pred[f'personal_linear_{lam}'] = base + adapt.predict(xq)
            # Fixed kernel residual adaptation tests nonlinear local similarity.
            def kernel(a, b):
                return np.exp(-((a[:, None] - b[None]) ** 2).mean(axis=2) / 2)
            offset = residual.mean(axis=0)
            coefficients = np.linalg.solve(kernel(xc, xc) + np.eye(4), residual - offset)
            pred['personal_kernel_1'] = base + offset + kernel(xq, xc) @ coefficients
            manifests.append(dict(sensor=sensor, pid=int(pid), calibration_ids=cal_ids,
                                  latest_calibration=str(cal.time.max()), query_ids=list(query.index),
                                  earliest_query=str(query.time.min()),
                                  training_people=[int(p) for p in np.unique(G[tr])],
                                  training_rows=len(tr)))
            for j, (rid, r) in enumerate(query.iterrows()):
                truth = Y[qi[j]]
                seen = bool(np.isclose(Y[ci], truth, atol=1e-8).all(axis=1).any())
                # Exact convex hull of the four onboarding macro vectors.
                weights = (truth - np.array([66, 22, 10.5])) / np.array([-42, 44, 31.5])
                hull = bool((weights >= -1e-9).all() and weights.sum() <= 1 + 1e-9)
                coverage.append(dict(sensor=sensor, id=rid, pid=int(pid), meal_type=r.meal_type,
                                     recipe=r.recipe, calibrated_macros=seen, within_calibration_hull=hull,
                                     **dict(zip(MAC, truth))))
                for name, guesses in pred.items():
                    estimate = np.maximum(guesses[j], 0)
                    errors = abs(estimate - truth)
                    row = dict(sensor=sensor, pid=int(pid), id=rid, method=name,
                               calibrated_macros=seen, within_calibration_hull=hull,
                               all_three_within10=bool((errors <= .1 * truth + 1e-9).all()))
                    for k, macro in enumerate(MAC):
                        row[macro + '_actual'] = truth[k]
                        row[macro + '_predicted'] = estimate[k]
                    rows.append(row)
        print(sensor, 'completed', flush=True)
    d = pd.DataFrame(rows)
    assert not d.duplicated(['sensor', 'id', 'method']).any()
    d.to_csv(OUT / 'predictions.csv', index=False)
    c = pd.DataFrame(coverage)
    c.to_csv(OUT / 'coverage.csv', index=False)
    (OUT / 'split_manifest.json').write_text(json.dumps(manifests, indent=2))
    summaries = []
    for (sensor, method), group in d.groupby(['sensor', 'method']):
        for scope, x in [('all_later', group), ('calibrated_macros', group[group.calibrated_macros]),
                         ('unfamiliar_macros', group[~group.calibrated_macros])]:
            if x.empty:
                continue
            summaries.append(dict(sensor=sensor, method=method, scope=scope, meals=len(x),
                                  people=int(x.pid.nunique()), hits=int(x.all_three_within10.sum()),
                                  MAE={m: float(abs(x[m + '_actual'] - x[m + '_predicted']).mean()) for m in MAC}))
    (OUT / 'summary.json').write_text(json.dumps(summaries, indent=2))
    (OUT / 'run_manifest.json').write_text(json.dumps(dict(
        primary_method='personal_linear_10',
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        event_sha256=hashlib.sha256(EVENTS.read_bytes()).hexdigest(),
        parameters_selected_using_test_results=False,
        caveat='Retrospective development dataset already inspected. Meal times and isolation use logs. '
               'No detection or daily-total validation. Zero gram labels require zero prediction for relative tolerance.'
    ), indent=2))
    print(json.dumps([s for s in summaries if s['method'] == 'personal_linear_10'], indent=2))


if __name__ == '__main__':
    run()
