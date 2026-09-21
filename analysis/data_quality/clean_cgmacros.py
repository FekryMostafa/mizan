"""Conservative CGMacros quality preparation; no physiological transformations."""
from pathlib import Path
import hashlib
import json
import zipfile
import numpy as np
import pandas as pd
ROOT = str(Path(__file__).resolve().parents[2])  # repo root

ROOT = Path(ROOT + '')
SOURCE = ROOT / 'dataset/csv'
OUT = ROOT / 'dataset/cgmacros_clean_v1'
OUT.mkdir(exist_ok=True)
(OUT / 'participants').mkdir(exist_ok=True)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

manifest = {'version': 1, 'sources': {}, 'archive_csv_matches': {},
            'script_sha256': sha(Path(__file__)), 'source_files_unchanged': False}
meals, issues, counts = [], [], []
archive = zipfile.ZipFile(ROOT / 'dataset/cgmacros_raw/CGMacros_dateshifted365.zip')
for path in sorted(SOURCE.glob('CGMacros-*.csv')):
    digest = sha(path)
    manifest['sources'][str(path)] = digest
    member = f'CGMacros/{path.stem}/{path.name}'
    manifest['archive_csv_matches'][path.name] = hashlib.sha256(archive.read(member)).hexdigest() == digest
    assert manifest['archive_csv_matches'][path.name], path
    # Retain every original cell as text, including source header spellings.
    raw = pd.read_csv(path, dtype=str, keep_default_na=False)
    d = raw.copy()
    d.columns = d.columns.str.strip()
    assert d.columns.is_unique
    n = len(d)
    pid = int(path.stem.split('-')[1])
    t = pd.to_datetime(d.Timestamp, format='mixed', errors='coerce')
    numeric = {}
    for col in ['Libre GL', 'Dexcom GL', 'HR', 'Calories (Activity)', 'METs', 'Intensity',
                'Calories', 'Carbs', 'Protein', 'Fat', 'Fiber', 'Amount Consumed']:
        s = d[col] if col in d else pd.Series('', index=d.index)
        numeric[col] = pd.to_numeric(s, errors='coerce')
    v = pd.DataFrame(numeric)
    is_meal = d['Meal Type'].str.strip().ne('') | v.Calories.gt(0) | v[['Carbs','Protein','Fat','Fiber']].gt(0).any(axis=1)
    flags = [[] for _ in range(n)]
    def flag(mask, code, field='', action='retained_flagged'):
        for idx in np.flatnonzero(np.asarray(mask, dtype=bool)):
            flags[idx].append(code)
            issues.append({'source_file':path.name, 'source_row':int(idx+2),
                           'timestamp':d.Timestamp.iloc[idx], 'field':field, 'issue':code,
                           'original_value':d[field].iloc[idx] if field in d else '', 'action':action})
    flag(t.isna(), 'timestamp_unparseable', 'Timestamp')
    flag(t.duplicated(keep=False) & t.notna(), 'timestamp_duplicate', 'Timestamp')
    flag(t.diff().dt.total_seconds().lt(0), 'timestamp_out_of_order', 'Timestamp')
    flag(t.diff().dt.total_seconds().gt(60), 'timestamp_gap_before', 'Timestamp')
    for col in v:
        if col in d:
            flag(d[col].str.strip().ne('') & (v[col].isna() | ~np.isfinite(v[col])), 'numeric_invalid', col)
    for col in ['Libre GL', 'Dexcom GL']:
        flag(v[col].lt(40) | v[col].gt(400), 'glucose_outside_device_range', col)
        flag(v[col].eq(40), 'glucose_at_lower_bound', col)
        flag(v[col].eq(400), 'glucose_at_upper_bound', col)
    flag(v.HR.notna() & (v.HR.lt(30) | v.HR.gt(176)), 'hr_outside_dictionary_range', 'HR')
    flag(v['Calories (Activity)'].lt(0), 'negative_activity', 'Calories (Activity)')
    flag(v['Amount Consumed'].notna() & (v['Amount Consumed'].lt(0) | v['Amount Consumed'].gt(100)) & is_meal,
         'consumption_outside_percent_range', 'Amount Consumed', 'normalized_percent_unavailable')
    flag(v['Amount Consumed'].gt(0) & v['Amount Consumed'].lt(10) & is_meal,
         'consumption_units_ambiguous', 'Amount Consumed', 'normalized_percent_unavailable')
    flag(v['Amount Consumed'].isna() & is_meal, 'consumption_missing', 'Amount Consumed')
    macro_cols = ['Carbs','Protein','Fat','Fiber']
    zero = v[macro_cols].eq(0).all(axis=1)
    flag(is_meal & zero, 'all_macros_zero_unresolved', 'Carbs', 'normalized_macros_unavailable')
    flag(is_meal & zero & v.Calories.gt(0), 'positive_calories_zero_macros', 'Calories')
    flag(is_meal & v[macro_cols].isna().any(axis=1), 'macro_missing', 'Carbs')
    flag(is_meal & v[macro_cols].lt(0).any(axis=1), 'macro_negative', 'Carbs')
    flag(is_meal & v['Amount Consumed'].eq(0) & v[macro_cols].gt(0).any(axis=1),
         'zero_consumption_positive_macros', 'Amount Consumed')
    flag(is_meal & v.Calories.lt(0), 'negative_meal_calories', 'Calories')
    clean = raw.copy()
    clean['qc_source_file'] = path.name
    clean['qc_source_row'] = np.arange(n) + 2
    clean['qc_timestamp_iso'] = t.dt.strftime('%Y-%m-%dT%H:%M:%S').fillna('')
    clean['qc_flags'] = [';'.join(sorted(set(fs))) for fs in flags]
    # Explicit missingness, without treating existing interpolated points as native samples.
    clean['qc_hr_missing'] = v.HR.isna()
    clean['qc_libre_missing'] = v['Libre GL'].isna()
    clean['qc_activity_missing'] = v['Calories (Activity)'].isna()
    clean['qc_is_meal_record'] = is_meal
    # The clean copy must reproduce every original cell exactly on readback.
    dest = OUT / 'participants' / path.name
    clean.to_csv(dest, index=False)
    check = pd.read_csv(dest, dtype=str, keep_default_na=False)
    assert check[raw.columns].equals(raw), path

    ordered = pd.DatetimeIndex(t.dropna().sort_values())
    invalid_timestamps = t.isna().any()
    for idx in np.flatnonzero(is_meal):
        row = d.iloc[idx]; tm = t.iloc[idx]; mf = list(flags[idx])
        mt = row['Meal Type'].strip().lower()
        if mt in ['snacks','snack 1']: mt = 'snack'
        if mt not in ['breakfast','lunch','dinner','snack']: mf.append('meal_type_unrecognized')
        pct = v['Amount Consumed'].iloc[idx]
        pct_valid = pd.notna(pct) and (pct == 0 or 10 <= pct <= 100)
        macros_valid = np.isfinite(v.loc[idx,macro_cols]).all() and (v.loc[idx,macro_cols]>=0).all() and not zero.iloc[idx]
        label_ok = macros_valid and pct_valid and pct == 100 and pd.notna(tm) and not t.duplicated(keep=False).iloc[idx] and v.Calories.iloc[idx] >= 0
        rec = {'record_id':f'{path.stem}:{idx+2}', 'participant_id':pid, 'source_file':path.name,
               'source_row':int(idx+2), 'timestamp':tm.isoformat() if pd.notna(tm) else '',
               'meal_type':mt, 'meal_type_reported':row['Meal Type'],
               'consumption_reported':row.get('Amount Consumed',''),
               'consumption_pct':pct if pct_valid else np.nan,
               'carbs_reported':row.Carbs, 'protein_reported':row.Protein,
               'fat_reported':row.Fat, 'fiber_reported':row.Fiber, 'calories_reported':row.Calories,
               'image_path_reported':row.get('Image path',''),
               'label_status':'eligible_full_consumption' if label_ok else 'needs_review',
               'timestamp_accuracy':'unverified_source_timestamp',
               'carbs_g':v.Carbs.iloc[idx] if macros_valid else np.nan,
               'protein_g':v.Protein.iloc[idx] if macros_valid else np.nan,
               'fat_g':v.Fat.iloc[idx] if macros_valid else np.nan,
               'fiber_g':v.Fiber.iloc[idx] if macros_valid else np.nan}
        for period, start, stop, size in [('pre24h',-1440,0,1440),('response3h',0,181,181)]:
            if pd.isna(tm):
                for key in ['grid_complete','libre_complete','hr_complete','activity_complete','libre_bound_present']:
                    rec[f'{period}_{key}'] = False
                mf.append(f'{period}_timestamp_unavailable')
                continue
            mask = (t >= tm+pd.Timedelta(minutes=start)) & (t < tm+pd.Timedelta(minutes=stop))
            expected = pd.date_range(tm+pd.Timedelta(minutes=start), periods=size, freq='min')
            actual = pd.DatetimeIndex(t[mask])
            grid = len(actual)==size and not actual.has_duplicates and actual.sort_values().equals(expected)
            rec[f'{period}_grid_complete'] = grid
            for col,key in [('Libre GL','libre'),('HR','hr'),('Calories (Activity)','activity')]:
                rec[f'{period}_{key}_complete'] = bool(grid and np.isfinite(v.loc[mask,col]).all())
            rec[f'{period}_libre_bound_present'] = bool(v.loc[mask,'Libre GL'].le(40).any() or v.loc[mask,'Libre GL'].ge(400).any())
            for channel in ['libre','hr','activity']:
                if not rec[f'{period}_{channel}_complete']: mf.append(f'{period}_{channel}_incomplete')
            if rec[f'{period}_libre_bound_present']: mf.append(f'{period}_libre_bound_present')
        if pd.notna(tm):
            others = is_meal & (t > tm) & (t <= tm+pd.Timedelta(hours=3))
            rec['other_meal_record_within3h'] = bool(others.any())
            if others.any(): mf.append('other_meal_record_within3h')
        else: rec['other_meal_record_within3h'] = True
        rec['isolated_libre_calibration_candidate'] = bool(label_ok and rec['response3h_libre_complete'] and not rec['response3h_libre_bound_present'] and not rec['other_meal_record_within3h'] and not invalid_timestamps)
        rec['quality_flags'] = ';'.join(sorted(set(mf)))
        meals.append(rec)
    counts.append({'source_file':path.name,'rows':n,'meal_records':int(is_meal.sum()),
                   'rows_flagged':sum(bool(x) for x in flags),'hr_missing_rows':int(v.HR.isna().sum()),
                   'libre_missing_rows':int(v['Libre GL'].isna().sum())})
archive.close()

m = pd.DataFrame(meals)
# Keep ambiguous food events in history: removing them would invent a fasting interval.
m['pre24h_food_record_needs_review'] = False
for pid, z in m.groupby('participant_id'):
    times = pd.to_datetime(z.timestamp, errors='coerce')
    for idx, tm in times.items():
        if pd.isna(tm): m.loc[idx,'pre24h_food_record_needs_review'] = True
        else:
            prior = (times >= tm-pd.Timedelta(hours=24)) & (times < tm)
            m.loc[idx,'pre24h_food_record_needs_review'] = bool(z.loc[prior,'label_status'].ne('eligible_full_consumption').any())
m.to_csv(OUT/'meals.csv', index=False)
m[m.isolated_libre_calibration_candidate].to_csv(OUT/'calibration_candidates.csv', index=False)
m[m.label_status.eq('needs_review')].to_csv(OUT/'meals_needing_review.csv', index=False)
pd.DataFrame(issues).to_csv(OUT/'issues.csv', index=False)
pd.DataFrame(counts).to_csv(OUT/'file_summary.csv', index=False)
for name in ['bio.csv','gut_health_test.csv','microbes.csv']:
    p = SOURCE/name
    manifest['sources'][str(p)] = sha(p)
    # Copy auxiliary data unchanged; baseline metadata is not a meal-time measurement.
    (OUT/name).write_bytes(p.read_bytes())
manifest['source_files_unchanged'] = all(sha(Path(p))==h for p,h in manifest['sources'].items())
assert manifest['source_files_unchanged']
assert m.record_id.is_unique and len(m)==sum(x['meal_records'] for x in counts)
assert not m[m.label_status.eq('eligible_full_consumption')].consumption_pct.ne(100).any()
summary = {'participant_files':len(counts),'sensor_rows':sum(x['rows'] for x in counts),
           'meal_records':len(m),'labels_needing_review':int(m.label_status.eq('needs_review').sum()),
           'full_consumption_labels':int(m.label_status.eq('eligible_full_consumption').sum()),
           'isolated_libre_calibration_candidates':int(m.isolated_libre_calibration_candidate.sum()),
           'meal_flag_counts':m.quality_flags.str.split(';').explode().loc[lambda s:s.ne('')].value_counts().to_dict()}
(OUT/'summary.json').write_text(json.dumps(summary, indent=2))
manifest['outputs'] = {str(p.relative_to(OUT)):sha(p) for p in OUT.rglob('*.csv')}
(OUT/'manifest.json').write_text(json.dumps(manifest, indent=2))
print(json.dumps(summary,indent=2))
