from pathlib import Path
import json,hashlib
import numpy as np
import pandas as pd

O=Path(__file__).resolve().parent;D=O.parent/'diverse_fit'
train=pd.read_csv(D/'training_inputs.csv',parse_dates=['time'])
labels=pd.read_csv(D/'training_predictions.csv')[['record_id','actual']]
train=train.merge(labels,on='record_id',validate='one_to_one')
manifest=json.loads((D/'manifest.json').read_text());allcols=manifest['feature_columns']
families={'glucose_only':[c for c in allcols if '_hr' not in c and 'activity' not in c], 'glucose_hr_activity':allcols}
plan=dict(inner_split='Per person: earliest 70% of the 211 training meals for fitting, latest 30% (at least one) for selection. Final 107 later meals remain excluded from model selection.',
 families=families,gamma=[.001,.01,.1,1.,10.],ridge=[1e-8,.0001,.01,.1,1.,10.,100.],
 objective='Maximize inner-validation meals within tolerance, then minimize MAE. Tie by fewer features, stronger ridge, smaller gamma.',
 tolerance='Positive carbs ±10%; zero carbs ±1g, reported separately.',
 final='Refit chosen settings on all 211 training meals, then evaluate the same 107 later meals once.',
 caveat='Development holdout already exposed in prior run; no fresh prospective validation claim.')
(O/'PLAN.json').write_text(json.dumps(plan,indent=2))
inner=np.zeros(len(train),bool)
for pid,z in train.groupby('pid'):
 z=z.sort_values('time');nval=max(1,int(np.ceil(.3*len(z))));assert len(z)>nval
 fit_idx=z.index[:-nval];val_idx=z.index[-nval:];inner[fit_idx]=True
 assert train.loc[val_idx,'time'].min()>train.loc[fit_idx,'time'].max()+pd.Timedelta(hours=3)
split=train[['record_id','pid','time']].copy();split['inner_role']=np.where(inner,'fit','selection');split.to_csv(O/'inner_split.csv',index=False)
def prep(a,b,cols):
 raw=a[cols].to_numpy(float);med=np.array([np.nanmedian(v) if np.isfinite(v).any() else 0 for v in raw.T])
 filled=np.where(np.isfinite(raw),raw,med);mu=filled.mean(axis=0);sd=filled.std(axis=0);sd[sd<1e-8]=1
 br=b[cols].to_numpy(float)
 return (filled-mu)/sd,(np.where(np.isfinite(br),br,med)-mu)/sd,med,mu,sd
def dist(a,b):return np.maximum(0,(a*a).sum(axis=1)[:,None]+(b*b).sum(axis=1)[None,:]-2*a@b.T)/a.shape[1]
def metrics(y,p):
 err=abs(y-p);return dict(n=len(y),hits=int((err<=np.where(y>0,.1*y,1.)).sum()),mae=float(err.mean()),median_error_g=float(np.median(err)))
tr=train[inner];va=train[~inner];y=tr.actual.to_numpy();yv=va.actual.to_numpy();candidates=[]
for family,cols in families.items():
 x,vx,_,_,_=prep(tr,va,cols);dd=dist(x,x);vd=dist(vx,x);center=y.mean()
 for gamma in plan['gamma']:
  k=np.exp(-gamma*dd);vk=np.exp(-gamma*vd)
  for ridge in plan['ridge']:
   coef=np.linalg.solve(k+ridge*np.eye(len(x)),y-center);p=np.maximum(0,center+vk@coef)
   candidates.append(dict(family=family,feature_count=len(cols),gamma=gamma,ridge=ridge,**metrics(yv,p)))
c=pd.DataFrame(candidates);c.to_csv(O/'candidates.csv',index=False)
best=min(candidates,key=lambda r:(-r['hits'],r['mae'],r['feature_count'],-r['ridge'],r['gamma']))
(O/'selected_settings.json').write_text(json.dumps(best,indent=2))
# Only now load the held-out later inputs; do not load their answers until predictions saved.
later=pd.read_csv(D/'reserved_inputs.csv',parse_dates=['time']);cols=families[best['family']]
x,vx,med,mu,sd=prep(train,later,cols);y=train.actual.to_numpy();center=y.mean();gamma=best['gamma'];ridge=best['ridge']
k=np.exp(-gamma*dist(x,x));coef=np.linalg.solve(k+ridge*np.eye(len(x)),y-center)
np.savez(O/'frozen_model.npz',x=x,coef=coef,center=center,gamma=gamma,ridge=ridge,median=med,mean=mu,scale=sd)
pred=np.maximum(0,center+np.exp(-gamma*dist(vx,x))@coef);trainpred=np.maximum(0,center+k@coef)
out=later[['record_id','pid','time']].copy();out['prediction']=pred;out.to_csv(O/'predictions_before_scoring.csv',index=False)
old=pd.read_csv(D/'reserved_scored.csv')[['record_id','actual','prediction','meal_type']].rename(columns={'prediction':'previous_prediction'})
out=out.merge(old,on='record_id',validate='one_to_one');out['error_g']=abs(out.prediction-out.actual);out['previous_error_g']=abs(out.previous_prediction-out.actual);out['within_tolerance']=out.error_g<=np.where(out.actual>0,.1*out.actual,1.);out.to_csv(O/'later_results.csv',index=False)
truth=out.actual.to_numpy();summaries=[]
for name,yy,pp in [('regularized_training',y,trainpred),('regularized_later',truth,pred),('previous_later',truth,out.previous_prediction.to_numpy()),('training_mean_later',truth,np.full(len(truth),center))]:summaries.append(dict(group=name,**metrics(yy,pp)))
pd.DataFrame(summaries).to_csv(O/'summary.csv',index=False)
# Saved-model reconstruction and source integrity are checks, not tuning.
saved=np.load(O/'frozen_model.npz');replay=np.maximum(0,float(saved['center'])+np.exp(-float(saved['gamma'])*dist(vx,saved['x']))@saved['coef']);assert np.allclose(replay,pred,atol=1e-8,rtol=0)
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in manifest['source_hashes'].items())
(O/'VERIFICATION.json').write_text(json.dumps(dict(inner_fit=len(tr),inner_selection=len(va),final_training=len(train),final_later=len(later),selected_features=cols,saved_model_replay=True,source_hashes_unchanged=True,model_sha256=hashlib.sha256((O/'frozen_model.npz').read_bytes()).hexdigest()),indent=2))
print('SELECTED',best);print(pd.DataFrame(summaries).to_string(index=False));print('INNER',len(tr),len(va))
