"""CGM-only chronological learning; earlier true meal labels are required."""
from pathlib import Path
import hashlib,json
import numpy as np
import pandas as pd
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.preprocessing import StandardScaler

B=Path(__file__).resolve().parent
O=B/'rolling_cgm';O.mkdir(exist_ok=True)
plan=dict(primary='rolling_kernel',population='CGMacros ExtraTrees 200 trees, leaf 5, seed 20260908',
          personal_kernel_regularization=1,initial_calibration=4,
          label_availability='Every earlier eligible meal label becomes available after its 3-hour response.',
          inputs='CGM only plus earlier recorded macro labels; no food identity or query macros.',
          interpretation='Extra supervised calibration, not automatic learning from unlabeled meals.',
          tuning=False,reserved_accessed=False)
(O/'PLAN.json').write_text(json.dumps(plan,indent=2))
s=np.load(B/'source_features.npz',allow_pickle=False)
t=np.load(B/'development_features.npz',allow_pickle=False)
X,Y,G,times=t['X'],t['Y'],t['G'],t['times']
assert set(G)<=set(range(1,9))
stamp=pd.to_datetime(times).astype('int64').to_numpy()
scaler=StandardScaler().fit(s['X']);train=scaler.transform(s['X']);x=scaler.transform(X)
counts=pd.Series(s['G']).value_counts();w=np.array([1/counts[p] for p in s['G']]);w*=len(w)/w.sum()
model=ExtraTreesRegressor(n_estimators=200,min_samples_leaf=5,random_state=20260908,n_jobs=1)
model.fit(train,s['Y'],sample_weight=w);population=model.predict(x)
def kernel(a,b):return np.exp(-((a[:,None]-b[None])**2).mean(axis=2)/2)
def calibrated(i,ci):
    residual=Y[ci]-population[ci];offset=residual.mean(axis=0)
    weights=np.linalg.solve(kernel(x[ci],x[ci])+np.eye(len(ci)),residual-offset)
    return population[i]+offset+(kernel(x[[i]],x[ci])@weights)[0]
rows,history=[],[]
for pid in np.unique(G):
    order=np.flatnonzero(G==pid);order=order[np.argsort(stamp[order])]
    if len(order)<=4:continue
    fixed=order[:4]
    for i in order[4:]:
        ci=order[stamp[order]+180*60*10**9<stamp[i]]
        assert len(ci)>=4 and i not in ci and set(fixed)<=set(ci)
        history.append(dict(pid=int(pid),query_time=str(times[i]),calibration_times=times[ci].tolist()))
        nearest=ci[((x[ci]-x[i])**2).mean(axis=1).argmin()]
        versions=dict(fixed_kernel=calibrated(i,fixed),rolling_kernel=calibrated(i,ci),
                      rolling_median=np.median(Y[ci],axis=0),rolling_nearest=Y[nearest])
        # Familiarity is evaluation metadata, never a model input.
        familiar=bool(np.isclose(Y[ci],Y[i],atol=1e-8,rtol=0).all(axis=1).any())
        for method,guess in versions.items():
            guess=np.maximum(guess,0)
            row=dict(pid=int(pid),time=str(times[i]),method=method,earlier_meals=len(ci),
                     familiar_earlier_macros=familiar,
                     all_three_within10=bool((abs(guess-Y[i])<=.1*Y[i]+1e-9).all()))
            for k,m in enumerate(['Carbs','Protein','Fat']):row[m+'_actual'],row[m+'_predicted']=Y[i,k],guess[k]
            rows.append(row)
d=pd.DataFrame(rows);assert not d.duplicated(['pid','time','method']).any()
old=pd.read_csv(B/'transfer_model/predictions.csv');old=old[old.method.eq('trees5/kernel')].sort_values(['pid','time'])
now=d[d.method.eq('fixed_kernel')].sort_values(['pid','time'])
assert list(zip(old.pid,old.time))==list(zip(now.pid,now.time))
for m in ['Carbs','Protein','Fat']:assert np.allclose(old[m+'_predicted'],now[m+'_predicted'],atol=1e-8,rtol=0)
summary=[]
for method,z in d.groupby('method'):
    for scope,sub in [('all',z),('unfamiliar_macros',z[~z.familiar_earlier_macros])]:
        summary.append(dict(method=method,scope=scope,meals=len(sub),hits=int(sub.all_three_within10.sum()),
          MAE={m:float(abs(sub[m+'_predicted']-sub[m+'_actual']).mean()) for m in ['Carbs','Protein','Fat']}))
d.to_csv(O/'predictions.csv',index=False)
(O/'summary.json').write_text(json.dumps(summary,indent=2))
(O/'history_manifest.json').write_text(json.dumps(history,indent=2))
(O/'run_manifest.json').write_text(json.dumps(dict(plan=plan,fixed_predictions_reproduced=True,
    script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    inputs={n:hashlib.sha256((B/n).read_bytes()).hexdigest() for n in ['source_features.npz','development_features.npz']}),indent=2))
print(json.dumps(summary,indent=2))
