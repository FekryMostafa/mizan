from pathlib import Path
import numpy as np
import pandas as pd
import json,hashlib

O=Path(__file__).resolve().parent;B=O.parent;D=B/'diverse_fit'
t=pd.read_csv(D/'training_inputs.csv',parse_dates=['time']).merge(pd.read_csv(D/'training_predictions.csv')[['record_id','actual']],on='record_id',validate='one_to_one')
anchors=pd.read_csv(B/'calibration_gap/anchor_inputs.csv',parse_dates=['time'])
assign=pd.read_csv(B/'rolling_validation/fold_assignments.csv');cols=json.loads((D/'manifest.json').read_text())['feature_columns']
families={'shape':['shape_start','shape_minimum'],'glucose':[c for c in cols if '_hr' not in c and 'activity' not in c],'glucose_activity':cols}
plan=dict(model='Independent kernel regressions per person. Zero observation regularization on the two initial known anchors enforces their labels exactly; ridge regularization applies only to other earlier meals.',families=families,gamma=[.01,.1,1.,10.],ridge=[.001,.1,1.,10.],selection='Same three earlier rolling windows; equal-weight dose-band hit rate, then equal-band MAE. No later answers used for selection.',validation='Known people, later meals. Reused development holdout, not fresh validation.')
(O/'PLAN.json').write_text(json.dumps(plan,indent=2))
def band(v):return 'zero' if v==0 else ('low' if v<=30 else ('medium' if v<=70 else 'high'))
counts=assign[assign.role.eq('validate')].record_id.value_counts()
def fit_person(history,ref,query,features,gamma,ridge):
 history=history.sort_values('time');ref=ref.sort_values('actual');allrows=pd.concat([ref,history],ignore_index=True)
 raw=allrows[features].to_numpy(float);med=np.array([np.nanmedian(v) if np.isfinite(v).any() else 0 for v in raw.T]);x=np.where(np.isfinite(raw),raw,med);mu=x.mean(axis=0);sd=x.std(axis=0);sd[sd<1e-8]=1;x=(x-mu)/sd
 q=query[features].to_numpy(float);q=(np.where(np.isfinite(q),q,med)-mu)/sd
 def kernel(a,b):return np.exp(-gamma*np.maximum(0,(a*a).sum(1)[:,None]+(b*b).sum(1)[None,:]-2*a@b.T)/len(features))
 k=kernel(x,x);pen=np.full(len(x),ridge);pen[:2]=0
 center=float(allrows.actual.mean());coef=np.linalg.solve(k+np.diag(pen),allrows.actual.to_numpy()-center)
 replay=center+k[:2]@coef;assert np.allclose(replay,ref.actual,atol=1e-5,rtol=0)
 pred=np.maximum(0,center+kernel(q,x)@coef)
 state=dict(record_ids=allrows.record_id.tolist(),x=x.tolist(),coef=coef.tolist(),center=center,median=med.tolist(),mean=mu.tolist(),scale=sd.tolist(),anchor_predictions=replay.tolist())
 return pred,state
results=[];scores=[]
for family,features in families.items():
 for gamma in plan['gamma']:
  for ridge in plan['ridge']:
   rows=[]
   for fold,fa in assign.groupby('fold'):
    for pid,part in fa.groupby('pid'):
     history=t[t.record_id.isin(part[part.role.eq('fit')].record_id)];query=t[t.record_id.isin(part[part.role.eq('validate')].record_id)];ref=anchors[anchors.pid==pid]
     pred,_=fit_person(history,ref,query,features,gamma,ridge)
     for r,p in zip(query.itertuples(),pred):
      er=abs(p-r.actual);rows.append(dict(record_id=r.record_id,pid=pid,fold=fold,actual=r.actual,prediction=p,band=band(r.actual),weight=1/counts[r.record_id],hit=er<=(.1*r.actual if r.actual>0 else 1.),error=er))
   frame=pd.DataFrame(rows);br=[]
   for _,z in frame.groupby('band'):br.append((np.average(z.hit,weights=z.weight),np.average(z.error,weights=z.weight)))
   score=dict(family=family,gamma=gamma,ridge=ridge,balanced_hits=float(np.mean([v[0] for v in br])),balanced_mae=float(np.mean([v[1] for v in br])))
   scores.append(score);results.append(rows)
bestindex=min(range(len(scores)),key=lambda i:(-scores[i]['balanced_hits'],scores[i]['balanced_mae'],len(families[scores[i]['family']]),-scores[i]['ridge'],scores[i]['gamma']))
best=scores[bestindex];pd.DataFrame(scores).to_csv(O/'candidates.csv',index=False);pd.DataFrame(results[bestindex]).to_csv(O/'selected_rolling_predictions.csv',index=False);(O/'selected_settings.json').write_text(json.dumps(best,indent=2))
later=pd.read_csv(D/'reserved_inputs.csv',parse_dates=['time']);rows=[];states={};features=families[best['family']]
for pid,query in later.groupby('pid'):
 history=t[t.pid==pid];ref=anchors[anchors.pid==pid];assert history.time.max()+pd.Timedelta(hours=3)<query.time.min()
 pred,state=fit_person(history,ref,query,features,best['gamma'],best['ridge']);states[str(pid)]=state
 for r,p in zip(query.itertuples(),pred):rows.append(dict(record_id=r.record_id,pid=pid,time=r.time,prediction=p))
model=dict(settings=best,features=features,people=states)
(O/'frozen_model.json').write_text(json.dumps(model,indent=2))
out=pd.DataFrame(rows);out.to_csv(O/'predictions_before_scoring.csv',index=False)
out=out.merge(pd.read_csv(D/'reserved_scored.csv')[['record_id','actual','meal_type']],on='record_id',validate='one_to_one');out['error_g']=abs(out.prediction-out.actual);out['within_tolerance']=out.error_g<=np.where(out.actual>0,.1*out.actual,1.);out['band']=[band(v) for v in out.actual];out.to_csv(O/'later_results.csv',index=False)
summary=out.groupby('band').agg(n=('actual','size'),hits=('within_tolerance','sum'),mae=('error_g','mean'));summary.to_csv(O/'band_scores.csv')
# Verify the serialized per-person models directly, rather than retraining them.
loaded=json.loads((O/'frozen_model.json').read_text());replayed=[]
for r in later.itertuples():
 s=loaded['people'][str(r.pid)];q=later[later.record_id==r.record_id][features].to_numpy(float)[0];q=(np.where(np.isfinite(q),q,s['median'])-s['mean'])/s['scale'];x=np.array(s['x']);k=np.exp(-best['gamma']*np.sum((x-q)**2,axis=1)/len(features));replayed.append(dict(record_id=r.record_id,replay=max(0,s['center']+k@np.array(s['coef']))))
check=out.merge(pd.DataFrame(replayed),on='record_id',validate='one_to_one');assert np.allclose(check.replay,check.prediction,atol=1e-8,rtol=0)
manifest=json.loads((D/'manifest.json').read_text());assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in manifest['source_hashes'].items())
(O/'VERIFICATION.json').write_text(json.dumps(dict(anchor_count=52,anchors_exact=True,saved_models_replay=True,source_hashes_unchanged=True,later_n=len(out),later_hits=int(out.within_tolerance.sum()),later_mae=float(out.error_g.mean())),indent=2))
print(best);print(summary.to_string());print('ALL',len(out),out.within_tolerance.sum(),out.error_g.mean())
