from pathlib import Path
import json,hashlib,ast
import numpy as np
import pandas as pd

O=Path(__file__).resolve().parent;B=O.parent;D=B/'diverse_fit'
train=pd.read_csv(D/'training_inputs.csv',parse_dates=['time']).merge(pd.read_csv(D/'training_predictions.csv')[['record_id','actual']],on='record_id',validate='one_to_one')
previous_plan=json.loads((B/'regularization/PLAN.json').read_text());families=previous_plan['families']
plan=dict(origins=[.4,.6,.8],window='Next 20% of each person’s earlier-meal sequence, at least one observation; expanding fit prefix with at least two meals.',
 bins={'zero':'0 g; ±1 g tolerance','low':'0 < carbs <=30 g','medium':'30 < carbs <=70 g','high':'carbs >70 g'},
 selection='Maximize equal-weight mean of per-band within-tolerance rates across pooled rolling predictions. Repeated validation records have inverse multiplicity weights. Tie by equal-band MAE, then fewer inputs, stronger regularization, smaller gamma.',
 gamma=previous_plan['gamma'],ridge=previous_plan['ridge'],families=families,
 heldout='107 later meals excluded from selection; score once after saving model. These are previously exposed development outcomes, not a new independent trial.')
(O/'PLAN.json').write_text(json.dumps(plan,indent=2))
# Reuse only preprocessing/distance definitions, not previous run’s executable work.
source=B/'regularization/run.py';tree=ast.parse(source.read_text());nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['prep','dist']]
assert len(nodes)==2;exec(compile(ast.Module(body=nodes,type_ignores=[]),str(source),'exec'))
folds=[];assignment=[]
for fold,origin in enumerate(plan['origins']):
 fit=[];val=[]
 for pid,z in train.groupby('pid'):
  z=z.sort_values('time');start=max(2,int(np.floor(origin*len(z))));stop=min(len(z),max(start+1,int(np.ceil((origin+.2)*len(z)))))
  if start>=len(z):continue
  fi=z.index[:start].tolist();vi=z.index[start:stop].tolist();fit.extend(fi);val.extend(vi)
  assert train.loc[vi,'time'].min()>train.loc[fi,'time'].max()+pd.Timedelta(hours=3)
  for role,ix in [('fit',fi),('validate',vi)]:
   for i in ix:assignment.append(dict(fold=fold,origin=origin,role=role,record_id=train.loc[i,'record_id'],pid=int(pid),time=train.loc[i,'time']))
 folds.append((fit,val))
pd.DataFrame(assignment).to_csv(O/'fold_assignments.csv',index=False)
counts=pd.Series([i for _,v in folds for i in v]).value_counts()
def band(y):return np.where(y==0,'zero',np.where(y<=30,'low',np.where(y<=70,'medium','high')))
def score(frame):
 rows=[]
 for group,z in frame.groupby('band'):
  rows.append(dict(band=group,weighted_hit_rate=float(np.average(z.hit,weights=z.weight)),weighted_mae=float(np.average(z.error,weights=z.weight)),predictions=len(z),unique_records=z.row.nunique()))
 return rows,float(np.mean([r['weighted_hit_rate'] for r in rows])),float(np.mean([r['weighted_mae'] for r in rows]))
candidates=[];band_rows=[];all_predictions=[]
for family,cols in families.items():
 cache=[]
 for fold,(fit,val) in enumerate(folds):
  tr=train.loc[fit];va=train.loc[val];x,vx,_,_,_=prep(tr,va,cols);cache.append((fold,fit,val,x,vx,dist(x,x),dist(vx,x)))
 for gamma in plan['gamma']:
  for ridge in plan['ridge']:
   records=[]
   for fold,fit,val,x,vx,dd,vd in cache:
    y=train.loc[fit,'actual'].to_numpy();truth=train.loc[val,'actual'].to_numpy();center=y.mean();k=np.exp(-gamma*dd);coef=np.linalg.solve(k+ridge*np.eye(len(x)),y-center);pred=np.maximum(0,center+np.exp(-gamma*vd)@coef)
    for i,actual,p,bb in zip(val,truth,pred,band(truth)):
     er=abs(actual-p);records.append(dict(row=i,record_id=train.loc[i,'record_id'],fold=fold,band=bb,actual=actual,prediction=p,error=er,hit=er<=(.1*actual if actual>0 else 1.),weight=1/counts[i]))
   frame=pd.DataFrame(records);bands,balanced,mae=score(frame)
   settings=dict(family=family,feature_count=len(cols),gamma=gamma,ridge=ridge)
   candidates.append(dict(**settings,balanced_hit_rate=balanced,balanced_mae=mae))
   band_rows.extend([dict(**settings,**r) for r in bands]);all_predictions.extend([dict(**settings,**r) for r in records])
c=pd.DataFrame(candidates);c.to_csv(O/'candidates.csv',index=False);pd.DataFrame(band_rows).to_csv(O/'candidate_band_scores.csv',index=False)
best=min(candidates,key=lambda r:(-r['balanced_hit_rate'],r['balanced_mae'],r['feature_count'],-r['ridge'],r['gamma']))
(O/'selected_settings.json').write_text(json.dumps(best,indent=2))
chosen=pd.DataFrame(all_predictions);chosen=chosen[(chosen.family==best['family'])&(chosen.gamma==best['gamma'])&(chosen.ridge==best['ridge'])];chosen.to_csv(O/'selected_rolling_predictions.csv',index=False)
# Fit on all earlier meals, and freeze before loading later answers.
later=pd.read_csv(D/'reserved_inputs.csv',parse_dates=['time']);cols=families[best['family']]
x,vx,med,mu,sd=prep(train,later,cols);y=train.actual.to_numpy();center=y.mean();gamma=best['gamma'];ridge=best['ridge'];k=np.exp(-gamma*dist(x,x));coef=np.linalg.solve(k+ridge*np.eye(len(x)),y-center)
np.savez(O/'frozen_model.npz',x=x,coef=coef,center=center,gamma=gamma,ridge=ridge,median=med,mean=mu,scale=sd)
prediction=np.maximum(0,center+np.exp(-gamma*dist(vx,x))@coef)
out=later[['record_id','pid','time']].copy();out['prediction']=prediction;out.to_csv(O/'predictions_before_scoring.csv',index=False)
answers=pd.read_csv(D/'reserved_scored.csv')[['record_id','actual','meal_type']];out=out.merge(answers,on='record_id',validate='one_to_one');out['band']=band(out.actual.to_numpy());out['error_g']=abs(out.prediction-out.actual);out['within_tolerance']=out.error_g<=np.where(out.actual>0,.1*out.actual,1.);out.to_csv(O/'later_results.csv',index=False)
summaries=[]
for name,p in [('rolling_selected',prediction),('previous_single_window',pd.read_csv(B/'regularization/later_results.csv').set_index('record_id').loc[out.record_id,'prediction'].to_numpy()),('training_mean',np.full(len(out),center))]:
 err=abs(p-out.actual.to_numpy());summaries.append(dict(model=name,n=len(out),hits=int((err<=np.where(out.actual>0,.1*out.actual,1.)).sum()),mae=float(err.mean())))
pd.DataFrame(summaries).to_csv(O/'summary.csv',index=False)
bs=out.groupby('band').agg(n=('record_id','size'),hits=('within_tolerance','sum'),mae=('error_g','mean'));bs.to_csv(O/'later_band_scores.csv')
saved=np.load(O/'frozen_model.npz');replay=np.maximum(0,float(saved['center'])+np.exp(-float(saved['gamma'])*dist(vx,saved['x']))@saved['coef']);assert np.allclose(replay,prediction,atol=1e-8,rtol=0)
original=json.loads((D/'manifest.json').read_text());assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in original['source_hashes'].items())
(O/'VERIFICATION.json').write_text(json.dumps(dict(rolling_validation_unique_meals=len(counts),rolling_prediction_count=sum(len(v) for _,v in folds),feature_columns=cols,model_replay_verified=True,source_hashes_unchanged=True,model_sha256=hashlib.sha256((O/'frozen_model.npz').read_bytes()).hexdigest()),indent=2))
print('SELECTED',best);print(pd.DataFrame(summaries).to_string(index=False));print(bs.to_string());print('ROLLING BANDS',score(chosen)[0])
