"""Nested evaluation of calibrated recipe discrimination: raw, temporal, shape and context.
Closed four-recipe menu: exact recipe selection gives macro grams, but does not prove
continuous-dose estimation. All choices made on training participants only.
"""
from pathlib import Path
import json,itertools,os
import numpy as np,pandas as pd
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.svm import SVC
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.model_selection import GroupKFold
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'analysis/cgm_fat_audit/shape_probe';OUT.mkdir(exist_ok=True)
if os.getenv('SHAPE_CONTEXT_RECHECK'):
 OUT=ROOT/'analysis/cgm_fat_audit/shape_probe_context_verified';OUT.mkdir(exist_ok=True)
REC=['reference','carb_low','protein_high','fat_high'];TARGET=np.array([[66,22,10.5],[24,22,10.5],[66,66,10.5],[66,22,42]])
events=pd.read_csv(ROOT/'analysis/cgm_fat_audit/full_audit/events_and_features.csv',parse_dates=['time']).set_index('id')
matches=pd.read_csv(ROOT/'analysis/cgm_fat_audit/separability/repeat_matches.csv');matches=matches[(matches.baseline=='pre10')&(matches.minutes==180)]
calibration_lookup={}
if os.getenv('SHAPE_EXPAND'):
 expanded=[]
 for sensor in ['Libre GL','Dexcom GL']:
  valid=events[(events['Amount Consumed']==100)&events.recipe.isin(REC)&events[sensor+'_valid180']]
  for pid,x in valid.groupby('pid'):
   if not set(REC).issubset(set(x.recipe)):continue
   first=x.sort_values('time').groupby('recipe').head(1);end=first.time.max()
   calibration_lookup[sensor,pid]={r:first[first.recipe==r].index[0] for r in REC}
   for id,r in x[x.time>end].iterrows():expanded.append(dict(sensor=sensor,pid=pid,recipe=r.recipe,query_id=id))
 matches=pd.DataFrame(expanded)
bio=pd.read_csv(ROOT/'dataset/csv/bio.csv').set_index('subject')
def dtw(a,b):
 n=len(a);d=np.full((n+1,n+1),np.inf);d[0,0]=0
 for i in range(1,n+1):
  for j in range(max(1,i-2),min(n,i+2)+1):d[i,j]=(a[i-1]-b[j-1])**2+min(d[i-1,j],d[i,j-1],d[i-1,j-1])
 return np.sqrt(d[n,n]/n)
def desc(y):
 return np.r_[y.mean(),y.max(),y.min(),np.argmax(y)/max(len(y)-1,1),y[-1],np.std(y),np.mean(np.diff(y)**2)**.5]
def estimator(name):
 if name=='lda':m=LinearDiscriminantAnalysis(solver='lsqr',shrinkage='auto')
 elif name.startswith('tree'):m=ExtraTreesClassifier(n_estimators=100,min_samples_leaf=int(name[4:]),random_state=200,n_jobs=1)
 else:m=SVC(C=float(name.split('_')[1]),kernel='linear' if name.startswith('linear') else 'rbf')
 return make_pipeline(SimpleImputer(add_indicator=True),StandardScaler(),m)
allpred=[];choices=[];scores=[]
for sensor,ss in matches.groupby('sensor'):
 feats={};nearest={};ys=[];groups=[];ids=[]
 for pid,x in ss.groupby('pid'):
  raw=pd.read_csv(ROOT/f'dataset/csv/CGMacros-{pid:03}.csv',parse_dates=['Timestamp']);raw.columns=raw.columns.str.strip();raw=raw.set_index('Timestamp')
  def signal(id):
   r=events.loc[id];grid=r.time+pd.to_timedelta(np.arange(0,181,15),unit='m');y=raw[sensor].reindex(grid).to_numpy(float)-r[sensor+'_base']
   hr=raw.HR.reindex(grid)
   # Dictionary defines METs x10; Intensity has no verified equivalent units.
   # Unknown activity units are missing, not mixed into the METs feature.
   act=r.activity_median_3h/10 if r.activity_column=='METs' else np.nan
   coverage=r.activity_coverage_3h if r.activity_column=='METs' else 0
   context=np.r_[r[sensor+'_base'],r[sensor+'_slope30'],hr.mean(),hr.isna().mean(),act,coverage]
   return y,context,r.time
  calids=[calibration_lookup[sensor,pid][rec] if os.getenv('SHAPE_EXPAND') else x[x.recipe==rec].iloc[0].calibration_id for rec in REC];cal=[signal(id) for id in calids]
  ac=np.array([z[1] for z in cal]);amax=max(z[2] for z in cal)
  for _,r in x.iterrows():
   y,ctx,t=signal(r.query_id);assert amax<t
   ys.append(REC.index(r.recipe));groups.append(pid);ids.append(r.query_id)
   for h in [60,120,180]:
    n=h//15+1;b=y[:n];a=np.array([z[0][:n] for z in cal]);scale=max(a.std(),1);mu=a.mean(axis=0)
    an=a/np.maximum(np.linalg.norm(a,axis=1,keepdims=True),1);bn=b/max(np.linalg.norm(b),1)
    distances=np.sqrt(((a-b)**2).mean(axis=1))/scale
    shape=np.sqrt(((an-bn)**2).mean(axis=1));warp=np.array([dtw(row,b) for row in a])/scale
    # Scale/time features retain absolute response and its location relative to calibration.
    basic=np.r_[b,(b-mu)/scale,distances,shape,warp,desc(b),np.array([desc(row) for row in a]).flatten()/scale]
    rich=np.r_[basic,((b-a)/scale).flatten(),np.diff(b)/scale]
    shapeonly=np.r_[bn,shape,np.diff(bn),np.array([dtw(row,bn) for row in an])]
    context=np.r_[rich,ctx,ctx-ac.mean(axis=0),bio.loc[pid,['Age','BMI','A1c PDL (Lab)']].to_numpy(float)]
    for name,v in [('basic',basic),('rich',rich),('shape',shapeonly),('context',context)]:feats.setdefault(f'{name}_{h}',[]).append(v)
    for name,dist in [('euclidean',distances),('shape',shape),('dtw',warp)]:nearest.setdefault(f'{name}_{h}',[]).append(int(dist.argmin()))
 X={k:np.array(v) for k,v in feats.items()};Y=np.array(ys);G=np.array(groups);ids=np.array(ids)
 np.savez(OUT/('expanded_' if os.getenv('SHAPE_EXPAND') else 'balanced_').__add__(sensor.split()[0]+'.npz'),**X,Y=Y,G=G,ids=ids)
 if os.getenv('SHAPE_FEATURES_ONLY'):continue
 # A bounded, explicit sweep. Context is evaluated separately from glucose-only.
 configs=[(rep,alg) for rep in X for alg in ['lda','linear_0.1','rbf_1','rbf_10','tree1','tree4']]
 if os.getenv('SHAPE_CONTEXT_RECHECK'):configs=[(r,a) for r,a in configs if r.startswith('context')]
 outer_predictions={f'{r}/{a}':np.zeros(len(Y),int) for r,a in configs}
 selected=np.zeros(len(Y),int);selected_glucose=np.zeros(len(Y),int)
 for pid in np.unique(G):
  tr=np.flatnonzero(G!=pid);te=np.flatnonzero(G==pid);inner={}
  folds=list(GroupKFold(4).split(tr,Y[tr],G[tr]))
  for rep,alg in configs:
   name=f'{rep}/{alg}';xx=X[rep];ivpred=np.zeros(len(tr),int)
   for it,iv in folds:
    model=estimator(alg);model.fit(xx[tr[it]],Y[tr[it]]);ivpred[iv]=model.predict(xx[tr[iv]])
   inner[name]=float((ivpred==Y[tr]).mean())
   model=estimator(alg);model.fit(xx[tr],Y[tr]);outer_predictions[name][te]=model.predict(xx[te])
  # Include simple personal distance choices in training-only selection.
  for name,pred in nearest.items():inner['personal/'+name]=float((np.array(pred)[tr]==Y[tr]).mean())
  best=max(inner,key=inner.get);bg=max((k for k in inner if not k.startswith('context')),key=inner.get)
  def pick(name):return np.array(nearest[name.split('/')[1]])[te] if name.startswith('personal/') else outer_predictions[name][te]
  selected[te]=pick(best);selected_glucose[te]=pick(bg)
  choices.append({'sensor':sensor,'pid':int(pid),'best':best,'best_glucose_only':bg,'inner_scores':inner})
  print(sensor,'held out',pid,'selected',best,flush=True)
 preds={**outer_predictions,**{'personal/'+k:np.array(v) for k,v in nearest.items()},'nested_selected':selected,'nested_glucose_only':selected_glucose,'no_sensor_reference':np.zeros(len(Y),int)}
 for name,pred in preds.items():
  ae=abs(TARGET[pred]-TARGET[Y]);hits=(ae<=.1*TARGET[Y]+1e-9)
  scores.append({'sensor':sensor,'method':name,'meals':len(Y),'all_three_within10':int(hits.all(axis=1).sum()),'MAE':ae.mean(axis=0).tolist(),'macro_hits':hits.sum(axis=0).tolist()})
  for i,id in enumerate(ids):allpred.append({'sensor':sensor,'pid':int(G[i]),'id':id,'method':name,'actual_recipe':REC[Y[i]],'predicted_recipe':REC[pred[i]],'actual_C':TARGET[Y[i],0],'actual_P':TARGET[Y[i],1],'actual_F':TARGET[Y[i],2],'predicted_C':TARGET[pred[i],0],'predicted_P':TARGET[pred[i],1],'predicted_F':TARGET[pred[i],2],'all_three_within10':bool(hits[i].all())})
 pd.DataFrame(allpred).to_csv(OUT/'predictions.csv',index=False);(OUT/'summary.json').write_text(json.dumps(scores,indent=2));(OUT/'selection.json').write_text(json.dumps(choices,indent=2))
print(json.dumps([x for x in scores if x['method'].startswith('nested')],indent=2))
