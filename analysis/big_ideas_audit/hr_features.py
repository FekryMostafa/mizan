"""Align heart rate to the existing source/development meals, without labels."""
from pathlib import Path
import json
import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[1]
SOURCE = np.load(BASE / 'source_features.npz', allow_pickle=False)
TARGET = np.load(BASE / 'development_features.npz', allow_pickle=False)
events = pd.read_csv(ROOT / 'analysis/cgm_fat_audit/full_audit/events_and_features.csv', parse_dates=['time']).set_index('id')
windows = [(-30, 0), (0, 60), (60, 120), (120, 180)]
quality = []

def summarize(series, t):
    out = []
    for start, end in windows:
        grid = pd.date_range(t + pd.Timedelta(minutes=start), periods=end-start, freq='min')
        values = series.reindex(grid)
        coverage = float(values.notna().mean())
        out.extend([float(values.mean()) if coverage >= .5 else np.nan,
                    float(values.std()) if coverage >= .5 else np.nan, coverage])
    return out

source_hr = np.full((len(SOURCE['G']), 12), np.nan)
for pid in np.unique(SOURCE['G']):
    f = ROOT / f'dataset/csv/CGMacros-{pid:03}.csv'
    raw = pd.read_csv(f, usecols=['Timestamp', 'HR'], parse_dates=['Timestamp'])
    series = raw.set_index('Timestamp').HR.resample('1min').median()
    for i in np.flatnonzero(SOURCE['G'] == pid):
        source_hr[i] = summarize(series, events.loc[str(SOURCE['ids'][i]), 'time'])
    quality.append(dict(dataset='CGMacros', pid=int(pid), minimum_time=str(series.index.min()), maximum_time=str(series.index.max()),
                        minute_coverage=float(series.notna().mean())))
target_hr = np.full((len(TARGET['G']), 12), np.nan)
for pid in np.unique(TARGET['G']):
    assert pid <= 8
    f = ROOT / f'dataset/big_ideas_1_1_3/{pid:03}/HR_{pid:03}.csv'
    raw = pd.read_csv(f)
    raw.columns = raw.columns.str.strip()
    if {'datetime', 'hr'} <= set(raw.columns):
        raw = raw.rename(columns={'datetime': 'Timestamp', 'hr': 'Value'})
    assert {'Timestamp', 'Value'} <= set(raw.columns), raw.columns.tolist()
    raw['Timestamp'] = pd.to_datetime(raw.Timestamp, errors='raise')
    series = raw.set_index('Timestamp').Value.resample('1min').median()
    for i in np.flatnonzero(TARGET['G'] == pid):
        target_hr[i] = summarize(series, pd.Timestamp(str(TARGET['times'][i])))
    quality.append(dict(dataset='BIG IDEAs', pid=int(pid), minimum_time=str(series.index.min()), maximum_time=str(series.index.max()),
                        minute_coverage=float(series.notna().mean())))
np.savez(BASE / 'hr_features.npz', source=source_hr, target=target_hr)
(BASE / 'hr_quality.json').write_text(json.dumps(quality, indent=2))
print('HR features exported. Source meals:', len(source_hr), 'target development meals:', len(target_hr))
print('Mean window coverage:', np.nanmean(source_hr[:, 2::3], axis=0), np.nanmean(target_hr[:, 2::3], axis=0))
