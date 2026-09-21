"""Post-hoc diagnosis of verified predictions; no model selection or refitting."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[1]
OUT = BASE / 'failure_analysis'
OUT.mkdir(exist_ok=True)
events = pd.read_csv(BASE / 'full_audit/events_and_features.csv', parse_dates=['time']).set_index('id')
pred = pd.read_csv(BASE / 'shape_probe_verified/predictions.csv')
pred = pred[pred.method == 'nested_selected'].copy()
matches = pd.read_csv(BASE / 'separability/repeat_matches.csv')
matches = matches[(matches.baseline == 'pre10') & (matches.minutes == 180)]
d = pred.merge(matches, left_on=['sensor', 'pid', 'id'], right_on=['sensor', 'pid', 'query_id'], validate='one_to_one')
for field in ['time', 'prev_min', 'next_min', 'meal_type']:
    d[field] = d.id.map(events[field])
for field in ['base', 'slope30', 'mean180', 'peak180', 'peak_time180']:
    d[field] = [events.loc[r.id, r.sensor + '_' + field] for r in d.itertuples()]
    d['cal_' + field] = [events.loc[r.calibration_id, r.sensor + '_' + field] for r in d.itertuples()]
    d['abs_shift_' + field] = abs(d[field] - d['cal_' + field])
d['wrong_recipe_closer'] = d.nearest_other_RMSE < d.same_recipe_RMSE
d.to_csv(OUT / 'case_diagnostics.csv', index=False)
stats = {}
for sensor, x in d.groupby('sensor'):
    st = {}
    st['by_recipe'] = x.groupby('actual_recipe').agg(meals=('id', 'size'), hits=('all_three_within10', 'sum')).to_dict('index')
    st['confusion'] = pd.crosstab(x.actual_recipe, x.predicted_recipe).to_dict('index')
    st['passed_failed'] = {}
    for passed, sub in x.groupby('all_three_within10'):
        st['passed_failed'][str(passed)] = dict(n=len(sub), wrong_recipe_closer=int(sub.wrong_recipe_closer.sum()),
            **{f: float(sub[f].median()) for f in ['same_recipe_RMSE', 'nearest_other_RMSE',
              'abs_shift_base', 'abs_shift_slope30', 'abs_shift_mean180', 'abs_shift_peak_time180', 'prev_min', 'next_min']})
    st['per_macro'] = {m: dict(hits=int((abs(x['actual_' + m] - x['predicted_' + m]) <= .1 * x['actual_' + m] + 1e-9).sum()),
                             MAE=float(abs(x['actual_' + m] - x['predicted_' + m]).mean())) for m in ['C', 'P', 'F']}
    stats[sensor] = st
paired = d[d.sensor == 'Libre GL'].merge(d[d.sensor == 'Dexcom GL'], on='id', suffixes=('_L', '_D'))
stats['paired_devices'] = dict(meals=len(paired), both_correct=int((paired.all_three_within10_L & paired.all_three_within10_D).sum()),
    both_wrong=int((~paired.all_three_within10_L & ~paired.all_three_within10_D).sum()),
    only_Libre_correct=int((paired.all_three_within10_L & ~paired.all_three_within10_D).sum()),
    only_Dexcom_correct=int((~paired.all_three_within10_L & paired.all_three_within10_D).sum()),
    same_prediction=int((paired.predicted_recipe_L == paired.predicted_recipe_D).sum()))
paired.to_csv(OUT / 'paired_device_cases.csv', index=False)

# Same-person high-fat success vs reference failure (or the reverse), chosen by ID.
libre = d[d.sensor == 'Libre GL']
contrast = []
for pid, group in libre.groupby('pid'):
    f = group[group.actual_recipe == 'fat_high']
    r = group[group.actual_recipe == 'reference']
    if len(f) and len(r) and bool(f.iloc[0].all_three_within10) != bool(r.iloc[0].all_three_within10):
        contrast = [f.iloc[0], r.iloc[0]]
        break
selected = list(contrast)
for recipe, passed in [('fat_high', False), ('fat_high', True), ('protein_high', False), ('carb_low', False)]:
    candidates = libre[(libre.actual_recipe == recipe) & (libre.all_three_within10 == passed)]
    candidates = candidates[~candidates.id.isin([r.id for r in selected])].sort_values('id')
    if len(candidates):
        selected.append(candidates.iloc[0])
selected = pd.DataFrame(selected)
selected.to_csv(OUT / 'illustrative_cases.csv', index=False)
fig, axes = plt.subplots(3, 2, figsize=(12, 12), sharex=True)
for ax, (_, r) in zip(axes.flat, selected.iterrows()):
    raw = pd.read_csv(ROOT / f'dataset/csv/CGMacros-{int(r.pid):03}.csv', parse_dates=['Timestamp']).set_index('Timestamp')
    wrongcal = matches[(matches.sensor == r.sensor) & (matches.pid == r.pid) & (matches.recipe == r.predicted_recipe)]
    lines = [(r.id, 'Later meal', '#151515'), (r.calibration_id, 'Same recipe during onboarding', '#228833')]
    if r.predicted_recipe != r.actual_recipe and len(wrongcal):
        lines.append((wrongcal.iloc[0].calibration_id, 'Recipe the model predicted', '#cc6633'))
    for rid, label, color in lines:
        ev = events.loc[rid]
        t = np.arange(0, 181, 15)
        y = raw[r.sensor].reindex(ev.time + pd.to_timedelta(t, unit='m')).to_numpy(float) - ev[r.sensor + '_base']
        ax.plot(t, y, label=label, color=color)
    actual = '/'.join(f'{r["actual_" + m]:g}' for m in ['C', 'P', 'F'])
    guess = '/'.join(f'{r["predicted_" + m]:g}' for m in ['C', 'P', 'F'])
    ax.set_title(f'P{int(r.pid)} {r.actual_recipe}: {"PASS" if r.all_three_within10 else "FAIL"}\nActual C/P/F {actual} g; predicted {guess} g', fontsize=10)
    ax.set_ylabel('Glucose change (mg/dL)')
    ax.set_xlabel('Minutes after logged meal')
    ax.legend(fontsize=7)
    ax.grid(alpha=.2)
fig.suptitle('Illustrative cases, selected after evaluation; Libre, 15-minute samples')
fig.tight_layout(rect=[0, 0, 1, .97])
fig.savefig(OUT / 'cases.png', dpi=150)
plt.close(fig)

coverage = pd.read_csv(BASE / 'personal_grams/coverage.csv')
stats['dose_coverage'] = {}
for sensor, x in coverage.groupby('sensor'):
    unseen = x[~x.calibrated_macros]
    stats['dose_coverage'][sensor] = dict(total=len(x), unfamiliar=len(unseen),
        unfamiliar_inside_calibration_hull=int(unseen.within_calibration_hull.sum()),
        unfamiliar_outside_calibration_hull=int((~unseen.within_calibration_hull).sum()),
        by_meal_type=x.groupby('meal_type').size().to_dict())
(OUT / 'summary.json').write_text(json.dumps(stats, indent=2))
print(json.dumps(stats, indent=2))
