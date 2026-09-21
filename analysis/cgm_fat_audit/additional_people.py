"""Freeze choices from balanced-cohort results, evaluate additional people once."""
from pathlib import Path
import json
import numpy as np,pandas as pd
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.svm import SVC
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.ensemble import ExtraTreesClassifier
ROOT=Path(__file__).resolve().parents[2];P=ROOT/'analysis/cgm_fat_audit/shape_probe';OUT=P/'additional_people';OUT.mkdir(exist_ok=True)
T=np.array([[66,22,10.5],[24,22,10.5],[66,66,10.5],[66,22,42]])
def model(alg):
 if alg=='lda':m=LinearDiscriminantAnalysis(solver='lsqr',shrinkage='auto')
 elif alg.startswith('tree'):m=ExtraTreesClassifier(n_estimators=100,min_samples_leaf=int(alg[4:]),random_state=200,n_jobs=1)
 else:m=SVC(C=float(alg.split('_')[1]),kernel='linear' if alg.startswith('linear') else 'rbf')
 return make_pipeline(SimpleImputer(add_indicator=True),StandardScaler(),m)
summary=json.load(open(P/'summary.json'));predictions=[];results=[]
for sensor in ['Libre GL','Dexcom GL']:
 old=np.load(P/('balanced_'+sensor.split()[0]+'.npz'));data=np.load(P/('expanded_'+sensor.split()[0]+'.npz'))
 test=~np.isin(data['G'],old['G']);assert not set(data['G'][test])&set(old['G'])
 candidates=[s for s in summary if s['sensor']==sensor and '/' in s['method'] and not s['method'].startswith('personal')]
 for mode in ['all_inputs','glucose_only','no_sensor']:
  options=[s for s in candidates if mode!='glucose_only' or not s['method'].startswith('context')]
  best=max(options,key=lambda x:x['all_three_within10']);name=best['method'];rep,alg=name.split('/')
  if mode=='no_sensor':pred=np.zeros(test.sum(),int);name='reference'
  else:fit=model(alg);fit.fit(old[rep],old['Y']);pred=fit.predict(data[rep][test])
  y=data['Y'][test];error=abs(T[pred]-T[y]);hit=(error<=.1*T[y]+1e-9)
  results.append(dict(sensor=sensor,mode=mode,frozen_method=name,people=len(np.unique(data['G'][test])),meals=len(y),all_three_within10=int(hit.all(axis=1).sum()),MAE=error.mean(axis=0).tolist()))
  for j,id in enumerate(data['ids'][test]):predictions.append(dict(sensor=sensor,mode=mode,id=id,pid=int(data['G'][test][j]),actual_C=T[y[j],0],actual_P=T[y[j],1],actual_F=T[y[j],2],predicted_C=T[pred[j],0],predicted_P=T[pred[j],1],predicted_F=T[pred[j],2],all_three_within10=bool(hit[j].all())))
pd.DataFrame(predictions).to_csv(OUT/'predictions.csv',index=False);(OUT/'summary.json').write_text(json.dumps(results,indent=2));print(json.dumps(results,indent=2))
