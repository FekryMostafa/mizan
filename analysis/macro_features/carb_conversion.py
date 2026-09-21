"""Fixed, interpretable carbohydrate feature conversions; no query-label tuning."""
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler

B = Path(__file__).resolve().parent
O = B / 'carb_conversion'
O.mkdir(exist_ok=True)
CANDIDATES = {
    'peak': ['peak_height'],
    'area': ['middle_positive_area'],
    'peak_area': ['peak_height', 'middle_positive_area'],
    'peak_area_context': ['peak_height', 'middle_positive_area', 'baseline', 'pre_slope'],
}
plan = dict(candidates=CANDIDATES, ridge_alpha=10, calibration_meals=4,
            calibration='Personal mean residual from first four meals; no target slope fitting.',
            selection='Lowest person-balanced MAE in CGMacros leave-one-person-out evaluation.',
            target='Same 65 later BIG IDEAs development meals; previously inspected, not pristine test.',
            zero_grams='Within 10 percent requires zero absolute error when true amount is zero.',
            reserved_accessed=False)
(O / 'PLAN.json').write_text(json.dumps(plan, indent=2))
d = pd.read_csv(B / 'features.csv')
d['time'] = pd.to_datetime(d.time, format='mixed')
s = d[d.dataset.eq('CGMacros')].copy()
t = d[d.dataset.eq('BIG_IDEAs_development')].copy()
assert len(s) == 652 and len(t) == 86 and set(t.pid) <= set(range(1, 9))

def evaluate(train, target, method):
    features = CANDIDATES.get(method, [])
    if features:
        scaler = StandardScaler().fit(train[features])
        counts = train.pid.value_counts()
        w = train.pid.map(lambda p: 1 / counts[p]).to_numpy()
        w *= len(w) / w.sum()
        fit = Ridge(alpha=10).fit(scaler.transform(train[features]), train.Carbs, sample_weight=w)
    rows = []
    for pid, z in target.groupby('pid'):
        z = z.sort_values('time')
        if len(z) <= 4:
            continue
        cal, queries = z.iloc[:4], z.iloc[4:]
        assert (cal.time.max() + pd.Timedelta(hours=3) < queries.time.min())
        if features:
            offset = np.mean(cal.Carbs.to_numpy() - fit.predict(scaler.transform(cal[features])))
            predictions = np.maximum(0, fit.predict(scaler.transform(queries[features])) + offset)
        else:
            predictions = np.repeat(cal.Carbs.median(), len(queries))
        for (_, q), prediction in zip(queries.iterrows(), predictions):
            row = dict(pid=int(pid), time=q.time.isoformat(), method=method,
                       actual=float(q.Carbs), predicted=float(prediction),
                       calibration_min=float(cal.Carbs.min()), calibration_max=float(cal.Carbs.max()))
            row['error_g'] = abs(row['actual'] - row['predicted'])
            row['within10'] = row['error_g'] <= .1 * row['actual'] + 1e-9
            row['outside_calibration_grams'] = not (row['calibration_min'] <= q.Carbs <= row['calibration_max'])
            rows.append(row)
    return rows

source_rows = []
for pid in sorted(s.pid.unique()):
    for method in [*CANDIDATES, 'personal_median']:
        source_rows.extend(evaluate(s[s.pid.ne(pid)], s[s.pid.eq(pid)], method))
cv = pd.DataFrame(source_rows)
scores = cv.groupby(['method', 'pid']).error_g.mean().groupby('method').mean()
selected = scores[list(CANDIDATES)].idxmin()
cv.to_csv(O / 'source_predictions.csv', index=False)
(O / 'source_selection.json').write_text(json.dumps(dict(selected=selected, person_balanced_MAE=scores.to_dict()), indent=2))
target_rows = []
for method in [*CANDIDATES, 'personal_median']:
    target_rows.extend(evaluate(s, t, method))
r = pd.DataFrame(target_rows)
assert len(r) == 325 and not r.duplicated(['pid', 'time', 'method']).any()
r.to_csv(O / 'predictions.csv', index=False)
summaries = []
for method, z in r.groupby('method'):
    summaries.append(dict(method=method, source_selected=method == selected, meals=len(z),
                          hits=int(z.within10.sum()), MAE=float(z.error_g.mean()),
                          median_error=float(z.error_g.median())))
(O / 'summary.json').write_text(json.dumps(summaries, indent=2))
chosen = r[r.method.eq(selected)].copy()
chosen['carb_bin'] = pd.cut(chosen.actual, [-.001, 20, 50, 100, np.inf], labels=['0-20', '20-50', '50-100', '>100'])
diagnostics = chosen.groupby('carb_bin', observed=True).agg(meals=('error_g', 'size'), hits=('within10', 'sum'), MAE=('error_g', 'mean'))
diagnostics.to_csv(O / 'amount_bins.csv')
chosen.sort_values('error_g', ascending=False).to_csv(O / 'ranked_cases.csv', index=False)
(O / 'manifest.json').write_text(json.dumps(dict(script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    input_sha256=hashlib.sha256((B / 'features.csv').read_bytes()).hexdigest(), selected=selected,
    source_rows=len(cv), target_rows=len(r), plan=plan), indent=2))
print(json.dumps(dict(selected=selected, source_scores=scores.to_dict(), target=summaries), indent=2))
print(diagnostics.to_string())
