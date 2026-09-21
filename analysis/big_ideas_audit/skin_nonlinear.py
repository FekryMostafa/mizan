"""Fixed nonlinear follow-up using existing development features, no tuning."""
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler

BASE = Path(__file__).resolve().parent
OUT = BASE/'skin_nonlinear'
OUT.mkdir(exist_ok=True)
plan = dict(algorithm='ExtraTreesRegressor', n_estimators=200, min_samples_leaf=5,
            random_state=20260908, personal_kernel_regularization=1,
            calibration_meals=4, primary='glucose_both',
            tuning=False, note='Exploratory development comparison, not fresh validation.')
(OUT/'PLAN.json').write_text(json.dumps(plan,indent=2))
f = np.load(BASE/'development_features.npz',allow_pickle=False)
s = np.load(BASE/'skin_model/features.npz',allow_pickle=False)
X,Y,G,times=f['X'],f['Y'],f['G'],f['times']
assert set(G)<=set(range(1,9))
wrist=np.c_[s['EDA'],s['TEMP']]
views=dict(glucose=X,wrist_only=wrist,glucose_both=np.c_[X,wrist])
macros=['total_carb','protein','total_fat']
rows,splits=[],[]
for pid in np.unique(G):
    order=np.flatnonzero(G==pid)
    order=order[np.argsort(times[order])]
    if len(order)<=4:
        continue
    ci,qi=order[:4],order[4:]
    tr=np.flatnonzero(G!=pid)
    assert not set(tr)&set(np.r_[ci,qi])
    assert pd.Timestamp(str(times[ci[-1]])).value+180*60*10**9<pd.Timestamp(str(times[qi[0]])).value
    splits.append(dict(pid=int(pid),training_people=np.unique(G[tr]).tolist(),
                       calibration_times=times[ci].tolist(),query_times=times[qi].tolist()))
    estimates={'no_sensor_median':np.tile(np.median(Y[ci],axis=0),(len(qi),1))}
    for name,x in views.items():
        imputer=SimpleImputer(add_indicator=True).fit(x[tr])
        xt,xc,xq=[imputer.transform(x[ix]) for ix in [tr,ci,qi]]
        scale=StandardScaler().fit(xt)
        xt,xc,xq=[scale.transform(a) for a in [xt,xc,xq]]
        counts=pd.Series(G[tr]).value_counts()
        w=np.array([1/counts[p] for p in G[tr]])
        w*=len(w)/w.sum()
        fit=ExtraTreesRegressor(n_estimators=200,min_samples_leaf=5,
                               random_state=20260908,n_jobs=1).fit(xt,Y[tr],sample_weight=w)
        residual=Y[ci]-fit.predict(xc)
        offset=residual.mean(axis=0)
        def kernel(a,b):return np.exp(-((a[:,None]-b[None])**2).mean(axis=2)/2)
        coef=np.linalg.solve(kernel(xc,xc)+np.eye(4),residual-offset)
        estimates[name]=fit.predict(xq)+offset+kernel(xq,xc)@coef
    for name,guess in estimates.items():
        guess=np.maximum(guess,0)
        for j,i in enumerate(qi):
            row=dict(pid=int(pid),time=str(times[i]),view=name,
                all_three_within10=bool((abs(guess[j]-Y[i])<=.1*Y[i]+1e-9).all()))
            for k,m in enumerate(macros):row[m+'_actual'],row[m+'_predicted']=Y[i,k],guess[j,k]
            rows.append(row)
d=pd.DataFrame(rows)
assert not d.duplicated(['pid','time','view']).any()
reference=pd.read_csv(BASE/'skin_model/predictions.csv')
reference=reference[reference.view.eq('glucose')].sort_values(['pid','time'])
summary=[]
for name,z in d.groupby('view'):
    z=z.sort_values(['pid','time'])
    assert list(zip(z.pid,z.time))==list(zip(reference.pid,reference.time))
    for m in macros:assert np.array_equal(z[m+'_actual'].to_numpy(),reference[m+'_actual'].to_numpy())
    summary.append(dict(view=name,meals=len(z),people=int(z.pid.nunique()),hits=int(z.all_three_within10.sum()),
        MAE={m:float(abs(z[m+'_predicted']-z[m+'_actual']).mean()) for m in macros}))
d.to_csv(OUT/'predictions.csv',index=False)
(OUT/'summary.json').write_text(json.dumps(summary,indent=2))
(OUT/'split_manifest.json').write_text(json.dumps(splits,indent=2))
(OUT/'run_manifest.json').write_text(json.dumps(dict(plan=plan,reserved_accessed=False,
    script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    inputs={p:hashlib.sha256((BASE/p).read_bytes()).hexdigest()
            for p in ['development_features.npz','skin_model/features.npz']}),indent=2))
print(json.dumps(summary,indent=2))
