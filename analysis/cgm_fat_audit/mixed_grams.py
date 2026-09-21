"""Train gram estimators on all usable post-calibration meals of other people."""
from pathlib import Path
import json
import numpy as np,pandas as pd
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.ensemble import ExtraTreesRegressor,HistGradientBoostingRegressor
from sklearn.multioutput import MultiOutputRegressor
from sklearn.model_selection import GroupKFold
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'analysis/cgm_fat_audit/mixed_grams';OUT.mkdir(exist_ok=True)
e=pd.read_csv(ROOT/'analysis/cgm_fat_audit/full_audit/events_and_features.csv',parse_dates=['time']).set_index('id');m=pd.read_csv(ROOT/'analysis/cgm_fat_audit/separability/repeat_matches.csv');m=m[(m.baseline=='pre10')&(m.minutes==180)]
REC=['reference','carb_low','protein_high','fat_high'];MAC=['Carbs','Protein','Fat'];names=['ridge','tree1','tree5','absolute7','absolute15']
def model(name):
 if name=='ridge':est=Ridge(alpha=100)
 elif name.startswith('tree'):est=ExtraTreesRegressor(n_estimators=100,min_samples_leaf=int(name[4:]),random_state=400,n_jobs=1)
 else:est=MultiOutputRegressor(HistGradientBoostingRegressor(loss='absolute_error',max_iter=100,max_leaf_nodes=int(name[8:]),min_samples_leaf=12,l2_regularization=2,random_state=400))
 return make_pipeline(SimpleImputer(add_indicator=True),StandardScaler(),est)
outputs=[];stats=[];selection=[]
for s in ['Libre GL','Dexcom GL']:
 valid=e[(e['Amount Consumed']==100)&e[s+'_valid180']&(e.Calories>0)&(e.Fiber<=e.Carbs)&(abs(e.kcal_difference/e.Calories)<=.2)]
 X=[];Y=[];G=[];ids=[]
 for pid,x in valid.groupby('pid'):
  cal=x[x.recipe.isin(REC)].sort_values('time').groupby('recipe').head(1)
  if not set(REC).issubset(set(cal.recipe)):continue
  end=cal.time.max();raw=pd.read_csv(ROOT/f'dataset/csv/CGMacros-{pid:03}.csv',parse_dates=['Timestamp']).set_index('Timestamp')
  def signal(r):return raw[s].reindex(r.time+pd.to_timedelta(np.arange(0,181,15),unit='m')).to_numpy(float)-r[s+'_base']
  a=np.array([signal(cal[cal.recipe==r].iloc[0]) for r in REC]);mu=a.mean(axis=0);scale=max(a.std(),1)
  for id,r in x[x.time>end].iterrows():
   b=signal(r);dist=np.sqrt(((a-b)**2).mean(axis=1))/scale
   feat=np.r_[b,(b-mu)/scale,dist,((b-a)/scale).flatten(),np.diff(b)/scale,r[s+'_base'],r[s+'_slope30']]
   assert np.isfinite(feat).all();X.append(feat);Y.append(r[MAC].to_numpy(float));G.append(pid);ids.append(id)
 X=np.array(X);Y=np.array(Y);G=np.array(G);ids=np.array(ids);tests=set(m[m.sensor==s].query_id);assert tests.issubset(set(ids))
 stats.append(dict(sensor=s,available_people=len(np.unique(G)),available_postcalibration_meals=len(Y),evaluation_meals=len(tests)))
 for pid in sorted(m[m.sensor==s].pid.unique()):
  tr=np.flatnonzero(G!=pid);te=np.flatnonzero((G==pid)&np.isin(ids,list(tests)));scores={};pred={}
  for name in names:
   pp=np.zeros_like(Y[tr])
   for a,b in GroupKFold(4).split(tr,Y[tr],G[tr]):
    fit=model(name);fit.fit(X[tr[a]],Y[tr[a]]);pp[b]=np.maximum(fit.predict(X[tr[b]]),0)
   scores[name]=float((abs(pp-Y[tr])/np.array([42,44,31.5])).mean())
   fit=model(name);fit.fit(X[tr],Y[tr]);pred[name]=np.maximum(fit.predict(X[te]),0)
  best=min(scores,key=scores.get);pred['nested_selected']=pred[best];selection.append(dict(sensor=s,pid=int(pid),selected=best,inner_scores=scores))
  for name,pr in pred.items():
   for j,i in enumerate(te):
    row=dict(sensor=s,pid=int(pid),id=ids[i],method=name,all_three_within10=bool((abs(pr[j]-Y[i])<=Y[i]*.1+1e-9).all()))
    for k,macro in enumerate(MAC):row[macro+'_actual']=Y[i,k];row[macro+'_predicted']=pr[j,k]
    outputs.append(row)
 print(s,'done',flush=True)
d=pd.DataFrame(outputs);d.to_csv(OUT/'predictions.csv',index=False);res=[]
for (s,method),x in d.groupby(['sensor','method']):res.append(dict(sensor=s,method=method,meals=len(x),hits=int(x.all_three_within10.sum()),MAE=[float(abs(x[z+'_predicted']-x[z+'_actual']).mean()) for z in MAC]))
(OUT/'summary.json').write_text(json.dumps(res,indent=2));(OUT/'selection.json').write_text(json.dumps(selection,indent=2));(OUT/'data_counts.json').write_text(json.dumps(stats,indent=2));print(json.dumps(res,indent=2))
