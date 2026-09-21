"""Exploratory signal model. Gram outputs are conditional scenarios, not validation."""
from pathlib import Path
import argparse, csv, hashlib, json
import numpy as np
import openpyxl
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
SOURCE = ROOT / 'dataset/sweat/lipid_study/source-figure4.xlsx'
LABELS = {'4e': 'Fasting', '4f': 'Bacon and eggs', '4g': 'Pizza',
          '4h': 'Ground beef', '4i': 'Milkshake'}

def read_record(sheet):
    rows = list(sheet.values)
    headers = rows[2]
    ti = headers.index('Time (s)')
    ai = headers.index('Time (min)')
    si = len(headers) - 2
    def pairs(indices):
        return np.array([[r[i] for i in indices] for r in rows[3:]
                         if all(isinstance(r[i], (int, float)) for i in indices)], float)
    x = pairs([ti, ti+1, ti+2, ti+3, ti+4])
    assert len(x) > 0 and np.isfinite(x).all()
    assert np.all(np.diff(x[:, 0]) > 0), 'Time duplicated or reversed'
    return {'raw': x, 'atp': pairs([ai, ai+1]), 'sr': pairs([si, si+1]),
            'pH_voltage_header': headers[ti+4]}

def features(y, fasting, grid, mode):
    # y and fasting contain only sensor values. No meal names or macro labels.
    if mode == 'fasting_excess':
        z = np.maximum(y - fasting, 0)
    elif mode == 'within_record_rise':
        z = np.maximum(y - np.median(y[:5], axis=0), 0)
    elif mode == 'raw_level':
        z = y
    else:
        raise ValueError(mode)
    return np.trapezoid(z, x=grid, axis=0) / (grid[-1] - grid[0])

def write_csv(name, rows):
    with (OUT / name).open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--reference-carbs', type=float, default=60)
    ap.add_argument('--reference-fat', type=float, default=25)
    args = ap.parse_args()
    assert args.reference_carbs > 0 and args.reference_fat > 0
    w = openpyxl.load_workbook(SOURCE, read_only=True, data_only=True)
    records = {k: read_record(w[k]) for k in LABELS}
    # Shared fixed window chosen from observed coverage, no meal-dependent optimization.
    end = np.floor(min(r['raw'][-1, 0] for r in records.values()) / 60)
    grid = np.arange(1, end + 1, dtype=float)
    processed = {k: np.column_stack([np.interp(grid*60, r['raw'][:, 0], r['raw'][:, j])
                                     for j in range(1, 4)]) for k, r in records.items()}
    qc, detail = [], []
    for k, r in records.items():
        x = r['raw']
        qc.append({'sheet': k, 'meal': LABELS[k], 'n_timepoints': len(x),
                   'first_second': x[0, 0], 'last_second': x[-1, 0],
                   'max_step_seconds': np.max(np.diff(x[:, 0])),
                   'ATP_points': len(r['atp']), 'sweat_rate_points': len(r['sr']),
                   'pH_voltage_header': r['pH_voltage_header']})
        for j, channel in enumerate(['glucose', 'cholesterol', 'TG_related']):
            a = processed[k][:, j]
            detail.append({'sheet': k, 'meal': LABELS[k], 'channel': channel,
                           'start_nA': a[0], 'end_nA': a[-1], 'mean_nA': np.mean(a),
                           'peak_nA': np.max(a), 'peak_recording_min': grid[np.argmax(a)],
                           'net_change_nA': a[-1]-a[0]})
    modes = ['fasting_excess', 'within_record_rise', 'raw_level']
    results, ratios_by_mode = [], {}
    for mode in modes:
        f = {k: features(v, processed['4e'], grid, mode) for k, v in processed.items()}
        assert np.all(f['4g'] > 0)
        ratios = {k: v/f['4g'] for k, v in f.items()}
        ratios_by_mode[mode] = ratios
        for k, ratio in ratios.items():
            results.append({'mode': mode, 'sheet': k, 'meal': LABELS[k],
                            'glucose_ratio_to_reference': ratio[0],
                            'TG_ratio_to_reference': ratio[2],
                            'cholesterol_ratio_to_reference': ratio[1],
                            'conditional_carbs_g': ratio[0]*args.reference_carbs,
                            'conditional_fat_g_TG': ratio[2]*args.reference_fat,
                            'conditional_fat_g_CH_alternative': ratio[1]*args.reference_fat})
    # Sanity checks: identical input gives identical output; reference yields specified scale.
    assert np.allclose(features(processed['4g'].copy(), processed['4e'], grid, modes[0]),
                       features(processed['4g'], processed['4e'], grid, modes[0]))
    assert np.allclose(ratios_by_mode[modes[0]]['4g'], 1)
    assert np.allclose(ratios_by_mode[modes[0]]['4e'], 0)
    # Window ablation exposes sensitivity to missing early or late responses.
    window_rows = []
    for lo, hi in [(1, end), (5, end), (10, end), (1, 30), (20, end)]:
        keep = (grid >= lo) & (grid <= hi)
        ref = features(processed['4g'][keep], processed['4e'][keep], grid[keep], modes[0])
        for k, v in processed.items():
            rr = features(v[keep], processed['4e'][keep], grid[keep], modes[0])/ref
            window_rows.append({'meal': LABELS[k], 'start_min': lo, 'end_min': hi,
                                'carbs_g_conditional': rr[0]*args.reference_carbs,
                                'fat_g_conditional': rr[2]*args.reference_fat})
    write_csv('quality_checks.csv', qc); write_csv('signal_features.csv', detail)
    write_csv('conditional_outputs.csv', results); write_csv('window_sensitivity.csv', window_rows)
    colors = ['#7b8493', '#d18324', '#2761a7', '#43865c', '#a25183']
    fig, axes = plt.subplots(3, 2, figsize=(13, 11))
    for k, color in zip(LABELS, colors):
        r = records[k]; x = r['raw']
        for j in range(3):
            axes.flat[j].plot(x[:,0]/60, x[:,j+1], label=LABELS[k], color=color, lw=1.7)
        axes.flat[3].plot(x[:,0]/60, x[:,4], color=color)
        axes.flat[4].plot(r['atp'][:,0], r['atp'][:,1], '.-', color=color)
        axes.flat[5].plot(r['sr'][:,0]/60, r['sr'][:,1], '.-', color=color)
    for ax, title, unit in zip(axes.flat,
             ['Glucose current', 'Cholesterol current', 'TG-related current',
              'pH electrode voltage', 'ATP cofactor', 'Local sweat rate'],
             ['nA','nA','nA','Source voltage values*','µM','µL/min']):
        ax.set(title=title, xlabel='Minutes on source recording axis', ylabel=unit)
        ax.grid(alpha=.18)
    axes.flat[0].legend(fontsize=9)
    fig.suptitle('Published meal source data: one participant, five conditions', fontsize=16)
    fig.text(.05,.012,'*Bacon/eggs voltage header says V; other sheets say mV. Values preserved.\n'
             'Meal consumed ~30 min before patch placement; recording starts after sweat induction/filling.', fontsize=9)
    fig.tight_layout(rect=[0,.05,1,.96]); fig.savefig(OUT/'raw_signals.png',dpi=150); plt.close(fig)
    fig, axes = plt.subplots(1,2,figsize=(12,4.8))
    names = list(LABELS.values())[1:]; xx = np.arange(4)
    for ax, j, scale, title in [(axes[0],0,args.reference_carbs,'Carbohydrate scenario'),
                                (axes[1],2,args.reference_fat,'Fat scenario from TG-related current')]:
        for n, mode in enumerate(modes):
            vals = [ratios_by_mode[mode][k][j]*scale for k in list(LABELS)[1:]]
            ax.bar(xx+(n-1)*.24,vals,.24,label=mode.replace('_',' '))
        ax.set(xticks=xx,xticklabels=names,title=title,ylabel='Conditional grams (assumed scale)')
        ax.tick_params(axis='x',labelsize=9); ax.grid(axis='y',alpha=.2)
    axes[0].legend(fontsize=8)
    fig.suptitle(f'Assume pizza = {args.reference_carbs:g} g carbs / {args.reference_fat:g} g fat; not measured intake')
    fig.tight_layout(); fig.savefig(OUT/'model_sensitivity.png',dpi=150); plt.close(fig)
    metadata = {'source_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
                'window_recording_minutes': [1, float(end)], 'resampling_seconds': 60,
                'reference_carbs_g_ASSUMED': args.reference_carbs,
                'reference_fat_g_ASSUMED': args.reference_fat,
                'trained_on_measured_macros': False, 'ATP_correction_applied': False,
                'independent_meal_validation': False,
                'same_ATP_profiles': [[a,b] for i,a in enumerate(records) for b in list(records)[i+1:]
                                      if np.array_equal(records[a]['atp'],records[b]['atp'])]}
    (OUT/'metadata.json').write_text(json.dumps(metadata,indent=2))
    print(json.dumps(metadata,indent=2))
    for r in results:
        print(r['mode'],r['meal'],*[round(r[v],2) for v in ['conditional_carbs_g','conditional_fat_g_TG','conditional_fat_g_CH_alternative']])

if __name__ == '__main__':
    main()
