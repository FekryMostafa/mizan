"""NONDEPLOYABLE diagnostic: give true other macros, predict the remaining one.

Never combine these separate oracle predictions into a wearable accuracy claim.
"""
from pathlib import Path
import json, hashlib
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import ExtraTreesRegressor

BASE = Path(__file__).resolve().parent
OUT = BASE / 'oracle_macro'; OUT.mkdir(exist_ok=True)
s = np.load(BASE / 'source_features.npz', allow_pickle=False)
t = np.load(BASE / 'development_features.npz', allow_pickle=False)
X, Y, G = s['X'], s['Y'], s['G']
x, y, g, times = t['X'], t['Y'], t['G'], t['times']
assert set(g) <= set(range(1,9))
names = ['Carbs','Protein','Fat']
counts = pd.Series(G).value_counts()
w = np.array([1/counts[p] for p in G]); w *= len(w)/w.sum()
rows = []
for k, macro in enumerate(names):
    other = [i for i in range(3) if i != k]
    for view in ['known_other_macros', 'known_other_macros_plus_glucose']:
        a, b = Y[:,other], y[:,other]
        if view.endswith('plus_glucose'):
            a, b = np.c_[a,X], np.c_[b,x]
        scale = StandardScaler().fit(a)
        a, b = scale.transform(a), scale.transform(b)
        fit = ExtraTreesRegressor(n_estimators=200,min_samples_leaf=5,random_state=20260908,n_jobs=1)
        fit.fit(a,Y[:,k],sample_weight=w)
        for pid in np.unique(g):
            order = np.flatnonzero(g==pid); order=order[np.argsort(times[order])]
            if len(order)<=4:
                continue
            ci, qi = order[:4], order[4:]
            assert pd.Timestamp(str(times[ci[-1]])).value+180*60*10**9 < pd.Timestamp(str(times[qi[0]])).value
            residual = y[ci,k]-fit.predict(b[ci]); offset=residual.mean()
            def kernel(a,b):
                return np.exp(-((a[:,None]-b[None])**2).mean(axis=2)/2)
            weights=np.linalg.solve(kernel(b[ci],b[ci])+np.eye(4),residual-offset)
            guess=np.maximum(fit.predict(b[qi])+offset+kernel(b[qi],b[ci])@weights,0)
            for j,i in enumerate(qi):
                rows.append(dict(pid=int(pid),time=times[i],target_macro=macro,view=view,
                    actual=float(y[i,k]),predicted=float(guess[j]),within10=bool(abs(guess[j]-y[i,k])<=.1*y[i,k]+1e-9),
                    supplied_macro_1=names[other[0]],supplied_grams_1=float(y[i,other[0]]),
                    supplied_macro_2=names[other[1]],supplied_grams_2=float(y[i,other[1]])))
    print(macro,'completed',flush=True)
d=pd.DataFrame(rows);d.to_csv(OUT/'predictions.csv',index=False)
summary=d.groupby(['target_macro','view']).apply(lambda z:pd.Series(dict(meals=len(z),hits=int(z.within10.sum()),
    MAE=float(abs(z.actual-z.predicted).mean()))),include_groups=False).reset_index()
summary.to_csv(OUT/'summary.csv',index=False)
(OUT/'run_manifest.json').write_text(json.dumps(dict(non_deployable=True,
    query_other_macro_labels_supplied=True,query_target_macro_not_supplied=True,reserved_accessed=False,
    script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    caveat='Diagnostic conditional prediction under fixed models; not a theoretical upper bound or verified wearable.'),indent=2))
print(summary.to_string(index=False))
