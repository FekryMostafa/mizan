"""Nested participant validation of personalized gram predictions on repeated breakfasts.
All settings fixed before running. This remains exploratory because the dataset was audited.
"""
from pathlib import Path
import json
import numpy as np,pandas as pd
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.compose import TransformedTargetRegressor
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'analysis/cgm_fat_audit/grams_probe';OUT.mkdir(exist_ok=True)
REC=['reference','carb_low','protein_high','fat_high'];MAC=['Carbs','Protein','Fat']
e=pd.read_csv(ROOT/'analysis/cgm_fat_audit/full_audit/events_and_features.csv',parse_dates=['time'])
matches=pd.read_csv(ROOT/'analysis/cgm_fat_audit/separability/repeat_matches.csv')
matches=matches[(matches.baseline=='pre10')&(matches.minutes==180)]
candidates=['ridge_0.1','ridge_1','ridge_10','ridge_100','trees_1','trees_4']
def model(name):
 if name.startswith('ridge'):
  return TransformedTargetRegressor(regressor=make_pipeline(StandardScaler(),Ridge(alpha=float(name.split('_')[1]))),transformer=StandardScaler())
 return ExtraTreesRegressor(n_estimators=100,min_samples_leaf=int(name.split('_')[1]),max_features=1.0,random_state=100,n_jobs=1)
def loss(y,p):return float(np.mean(abs(y-p)/y))
outputs=[];selection=[];manifests=[]
for sensor,ss in matches.groupby('sensor'):
 X=[];Y=[];P=[];ids=[];priors=[];medians=[];nearest=[]
 for pid,xx in ss.groupby('pid'):
  raw=pd.read_csv(ROOT/f'dataset/csv/CGMacros-{pid:03}.csv',parse_dates=['Timestamp']).set_index('Timestamp')
  calibration=[];targets=[];calids=[];times=[]
  for rec in REC:
   r=e[e.id==xx[xx.recipe==rec].iloc[0].calibration_id].iloc[0]
   y=raw[sensor].reindex(r.time+pd.to_timedelta(np.arange(0,181,15),unit='m')).to_numpy(float)-r[sensor+'_base']
   calibration.append(y);targets.append(r[MAC].to_numpy(float));calids.append(r.id);times.append(r.time)
  a=np.array(calibration);target=np.array(targets);mu=a.mean(axis=0);scale=max(float(a.std()),1)
  for _,m in xx.iterrows():
   r=e[e.id==m.query_id].iloc[0]; assert max(times)<r.time
   b=raw[sensor].reindex(r.time+pd.to_timedelta(np.arange(0,181,15),unit='m')).to_numpy(float)-r[sensor+'_base']
   dist=np.sqrt(((a-b)**2).mean(axis=1))
   # Inputs: query glucose, differences from four labeled calibration curves, pre-meal state.
   # No current recipe, study day, current macros, calories or food name is an input.
   features=np.r_[b,(b-mu)/scale,dist/scale,((b-a)/scale).flatten(),r[sensor+'_base'],r[sensor+'_slope30']]
   assert np.isfinite(features).all()
   X.append(features);Y.append(r[MAC].to_numpy(float));P.append(pid);ids.append(r.id)
   priors.append(target.mean(axis=0));medians.append(np.median(target,axis=0));nearest.append(target[dist.argmin()])
   manifests.append(dict(sensor=sensor,pid=pid,query_id=r.id,calibration_ids='|'.join(calids),last_calibration=str(max(times)),query_time=str(r.time)))
 X=np.array(X);Y=np.array(Y);P=np.array(P);priors=np.array(priors);medians=np.array(medians);nearest=np.array(nearest)
 for pid in np.unique(P):
  test=P==pid;train=~test;assert not set(P[test])&set(P[train])
  losses={}
  for name in candidates:
   inner=np.zeros_like(Y[train]); xx=X[train];yy=Y[train];gg=P[train]
   for it,iv in GroupKFold(n_splits=4).split(xx,yy,gg):
    fit=model(name);fit.fit(xx[it],yy[it]);inner[iv]=np.maximum(fit.predict(xx[iv]),0)
   losses[name]=loss(yy,inner)
  best=min(losses,key=losses.get);selection.append(dict(sensor=sensor,pid=int(pid),selected=best,inner_losses=losses))
  preds={'calibration_mean':priors[test],'calibration_median':medians[test],'nearest_personal_curve':nearest[test]}
  # Separate fixed candidates reported too; only nested_selected chooses using inner data.
  for name in candidates:
   fit=model(name);fit.fit(X[train],Y[train]);preds[name]=np.maximum(fit.predict(X[test]),0)
  preds['nested_selected']=preds[best]
  for mode,pr in preds.items():
   for j,idx in enumerate(np.flatnonzero(test)):
    row=dict(sensor=sensor,pid=int(pid),id=ids[idx],method=mode)
    for k,macro in enumerate(MAC):
     row[macro+'_actual']=Y[idx,k];row[macro+'_predicted']=pr[j,k];row[macro+'_absolute_error']=abs(pr[j,k]-Y[idx,k]);row[macro+'_within10']=bool(abs(pr[j,k]-Y[idx,k])<=.1*Y[idx,k]+1e-9)
    row['all_three_within10']=all(row[m+'_within10'] for m in MAC);outputs.append(row)
 print(sensor,'completed',len(np.unique(P)),'outer participants',flush=True)
d=pd.DataFrame(outputs);d.to_csv(OUT/'all_meal_predictions.csv',index=False)
pd.DataFrame(manifests).to_csv(OUT/'calibration_manifest.csv',index=False)
(OUT/'model_selection.json').write_text(json.dumps(selection,indent=2))
summary=[]
for (sensor,method),x in d.groupby(['sensor','method']):
 row=dict(sensor=sensor,method=method,people=int(x.pid.nunique()),meals=len(x),all_three_within10=int(x.all_three_within10.sum()))
 for macro in MAC:
  row[macro+'_MAE_g']=float(x[macro+'_absolute_error'].mean());row[macro+'_within10']=int(x[macro+'_within10'].sum())
 summary.append(row)
(OUT/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
