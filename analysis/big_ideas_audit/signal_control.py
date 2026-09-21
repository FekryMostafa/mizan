"""Fixed-model ablations; diagnostic permutations are not accuracy tuning."""
from pathlib import Path
import json, hashlib
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import ExtraTreesRegressor

BASE = Path(__file__).resolve().parent
OUT = BASE / 'signal_control'
OUT.mkdir(exist_ok=True)
s = np.load(BASE / 'source_features.npz', allow_pickle=False)
t = np.load(BASE / 'development_features.npz', allow_pickle=False)
X, Y, G = s['X'], s['Y'], s['G']
x, y, g, times = t['X'], t['Y'], t['G'], t['times']
assert set(g) <= set(range(1, 9))
counts = pd.Series(G).value_counts()
w = np.array([1 / counts[p] for p in G]); w *= len(w) / w.sum()
rng = np.random.default_rng(20260909)
rows = []
for view, cols in [('full_signal', np.arange(15)), ('premeal_only', np.arange(13, 15))]:
    scale = StandardScaler().fit(X[:, cols])
    train, target = scale.transform(X[:, cols]), scale.transform(x[:, cols])
    model = ExtraTreesRegressor(n_estimators=200, min_samples_leaf=5, random_state=20260908, n_jobs=1)
    model.fit(train, Y, sample_weight=w)
    for pid in np.unique(g):
        order = np.flatnonzero(g == pid)
        order = order[np.argsort(times[order])]
        if len(order) <= 4:
            continue
        ci, qi = order[:4], order[4:]
        cal = target[ci]
        residual = y[ci] - model.predict(cal)
        offset = residual.mean(axis=0)
        def kernel(a, b):
            return np.exp(-((a[:, None] - b[None]) ** 2).mean(axis=2) / 2)
        coef = np.linalg.solve(kernel(cal, cal) + np.eye(4), residual - offset)
        for rep in range(-1, 50 if view == 'full_signal' else 0):
            query = target[qi].copy()
            if rep >= 0:
                # Only swap postmeal curves; actual premeal state and labels stay fixed.
                query[:, :13] = target[rng.permutation(qi), :13]
            guess = np.maximum(model.predict(query) + offset + kernel(query, cal) @ coef, 0)
            for j, i in enumerate(qi):
                row = dict(pid=int(pid), time=times[i], view=view, permutation=rep,
                           all_three_within10=bool((abs(guess[j] - y[i]) <= .1 * y[i] + 1e-9).all()))
                for k, m in enumerate(['Carbs', 'Protein', 'Fat']):
                    row[m + '_actual'], row[m + '_predicted'] = y[i, k], guess[j, k]
                rows.append(row)
d = pd.DataFrame(rows)
d.to_csv(OUT / 'predictions.csv', index=False)
summary = []
for (view, rep), z in d.groupby(['view', 'permutation']):
    summary.append(dict(view=view, permutation=int(rep), meals=len(z), hits=int(z.all_three_within10.sum()),
        MAE={m: float(abs(z[m + '_actual'] - z[m + '_predicted']).mean()) for m in ['Carbs','Protein','Fat']}))
(OUT / 'summary.json').write_text(json.dumps(summary, indent=2))
# Verify the original frozen model was reproduced before interpreting ablations.
old = pd.read_csv(BASE / 'transfer_model/predictions.csv')
old = old[old.method == 'trees5/kernel'].sort_values(['pid', 'time'])
full = d[(d.view == 'full_signal') & (d.permutation == -1)].sort_values(['pid', 'time'])
assert list(zip(old.pid, old.time)) == list(zip(full.pid, full.time))
for m in ['Carbs', 'Protein', 'Fat']:
    assert np.allclose(old[m + '_predicted'], full[m + '_predicted'], atol=1e-10)
no = d[(d.view == 'premeal_only') & (d.permutation == -1)].sort_values(['pid', 'time'])
people = np.unique(full.pid)
intervals = {}
for m in ['Carbs','Protein','Fat']:
    delta = pd.DataFrame(dict(pid=full.pid.to_numpy(), improvement=
        abs(no[m + '_actual'].to_numpy() - no[m + '_predicted'].to_numpy()) -
        abs(full[m + '_actual'].to_numpy() - full[m + '_predicted'].to_numpy())))
    bootstrap = []
    for _ in range(2000):
        sample = rng.choice(people, len(people), replace=True)
        bootstrap.append(np.concatenate([delta[delta.pid == p].improvement for p in sample]).mean())
    intervals[m] = dict(mean_MAE_improvement_with_postmeal=float(delta.improvement.mean()),
        descriptive_participant_bootstrap_95_percent=np.quantile(bootstrap, [.025,.975]).tolist())
(OUT / 'paired_uncertainty.json').write_text(json.dumps(intervals, indent=2))
(OUT / 'run_manifest.json').write_text(json.dumps(dict(script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    reproduced_original_predictions=True, permutations=50, reserved_accessed=False,
    limitations='Five development people; post-hoc controls. Permutations break curve/premeal-state consistency; not a causal test or proof of absent information.'), indent=2))
print(json.dumps([r for r in summary if r['permutation'] == -1], indent=2))
print(json.dumps(intervals, indent=2))
permuted = [r for r in summary if r['permutation'] >= 0]
print('Mean shuffled MAE:', {m: np.mean([r['MAE'][m] for r in permuted]) for m in ['Carbs','Protein','Fat']})
