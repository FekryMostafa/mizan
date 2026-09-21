from pathlib import Path
import ast,json,hashlib
import numpy as np
import pandas as pd
ROOT = str(Path(__file__).resolve().parents[3])  # repo root

O=Path(__file__).resolve().parent;B=O.parent
R=Path(ROOT + '/dataset/cgmacros_clean_v1')
meals=pd.read_csv(R/'meals.csv',parse_dates=['timestamp'])
old_inputs=pd.read_csv(B/'formula_build/formula_inputs.csv',parse_dates=['time'])
train_ids=sorted(int(p) for p in old_inputs.pid.unique())
reserved_ids=train_ids.copy()
plan=dict(training_participants=train_ids,reserved_participants=reserved_ids,
 selection='Quality-eligible mixed meals strictly after both initial matched 24/66 g calibration responses finish. No recipe restriction on query meals.',
 anchors='Earliest eligible full-consumption zero-fiber breakfast at each 24/66 C,22 P,10.5 F dose, with complete uncensored baseline.',
 features='Previously verified continuous glucose and HR/activity features; exclude all coverage and food-review indicators. Training-only median imputation; no current macros, recipe, date or person ID as predictors.',
 model='Gaussian kernel ridge regression on standardized continuous observations; gamma schedule 0.01,0.1,1,10; fixed ridge 1e-8. Stop at first all-training fit within tolerance.',
 tolerance='positive carbs within 10 percent per meal; zero carbs within 1 g absolute, reported separately',
 validation='Same participants: first 70 percent of chronologically eligible meals for training, last 30 percent (at least two) reserved; at least two training meals required. Select gamma using training fit only, then evaluate later meals once.',
 caveat='Reserved for this run; this public dataset has been examined before. Not a pristine prospective validation set.')
(O/'PLAN.json').write_text(json.dumps(plan,indent=2))
data={};anchors={};eligibility=[];selected=[];source_hashes={}
def baseline_ok(d,time):
 v=d['Libre GL'].reindex(pd.date_range(time-pd.Timedelta(minutes=10),periods=10,freq='min'))
 return bool(np.isfinite(v).all() and v.gt(40).all() and v.lt(400).all())
for pid,z in meals[meals.participant_id.isin(train_ids)].groupby('participant_id'):
 path=R/'participants'/f'CGMacros-{pid:03d}.csv';source_hashes[str(path)]=hashlib.sha256(path.read_bytes()).hexdigest()
 d=pd.read_csv(path);d.columns=d.columns.str.strip();d.Timestamp=pd.to_datetime(d.Timestamp,format='mixed');d=d.set_index('Timestamp');assert d.index.is_unique;data[pid]=d
 eligible=z[z.isolated_libre_calibration_candidate].copy()
 eligible=eligible.loc[pd.Series([baseline_ok(d,t) for t in eligible.timestamp],index=eligible.index,dtype=bool)]
 refs=[]
 for dose in [24,66]:
  q=eligible[eligible.meal_type.eq('breakfast')&eligible.carbs_g.eq(dose)&eligible.protein_g.eq(22)&eligible.fat_g.eq(10.5)&eligible.fiber_g.eq(0)].sort_values('timestamp')
  if len(q):refs.append(q.iloc[0])
 if len(refs)!=2:
  eligibility.append(dict(pid=pid,split='train' if pid in train_ids else 'reserved',status='missing_eligible_anchor_pair',query_meals=0));continue
 cutoff=max(r.timestamp for r in refs)+pd.Timedelta(hours=3)
 targets=eligible[eligible.timestamp>cutoff]
 eligibility.append(dict(pid=pid,split='train' if pid in train_ids else 'reserved',status='included' if len(targets) else 'no_later_eligible_meals',query_meals=len(targets)))
 anchors[pid]=refs
 for r in targets.itertuples():selected.append(dict(record_id=r.record_id,pid=pid,time=r.timestamp,split='train' if pid in train_ids else 'reserved'))
pd.DataFrame(eligibility).to_csv(O/'participant_eligibility.csv',index=False)
selection=pd.DataFrame(selected)
parts=[]
for pid,z in selection.groupby('pid'):
 z=z.sort_values('time').copy()
 if len(z)<4: continue
 nval=max(2,int(np.ceil(.3*len(z))));cut=len(z)-nval
 z.loc[z.index[:cut],'split']='train';z.loc[z.index[cut:],'split']='reserved'
 assert z.iloc[cut].time > z.iloc[cut-1].time+pd.Timedelta(hours=3)
 parts.append(z)
selection=pd.concat(parts).reset_index(drop=True)
assert set(selection[selection.split.eq('train')].pid)==set(selection[selection.split.eq('reserved')].pid)
selection.to_csv(O/'selected_records.csv',index=False)
# Reuse only the already-verified feature functions, not the prior evaluation's
# executable selection/fitting/scoring code. Pin the dependency in the manifest.
src=B/'frozen_later_meals/evaluate.py';tree=ast.parse(src.read_text())
functions=[node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name in ['observations','inputs']]
assert len(functions)==2
exec(compile(ast.Module(body=functions,type_ignores=[]),str(src),'exec'))
for pid,refs in list(anchors.items()):anchors[pid]=[observations(pid,r.timestamp) for r in refs]
gcols=['peak','area_0_60','area_60_120','area_120_180','peak_time','rise_0_30']
floors={c:max(.25*np.median([abs(v[1][0][c]-v[0][0][c]) for pid,v in anchors.items() if pid in train_ids]),1e-6) for c in gcols}
feature_cols=[c for c in old_inputs.columns if c not in ['pid','time','actual','base','target_case','prior_food_review'] and 'coverage' not in c]
# Materialize training inputs first. Reserved labels are not used here.
train_selection=selection[selection.split.eq('train')]
train=pd.DataFrame([dict(**inputs(r.pid,r.time),record_id=r.record_id) for r in train_selection.itertuples()])
train=train[['record_id','pid','time',*feature_cols]]
labels=meals.set_index('record_id')
y=labels.loc[train.record_id,'carbs_g'].to_numpy(float)
raw=train[feature_cols].to_numpy(float)
med=np.array([np.nanmedian(v) if np.isfinite(v).any() else 0 for v in raw.T]);xx=np.where(np.isfinite(raw),raw,med);mu=xx.mean(axis=0);sd=xx.std(axis=0);sd[sd<1e-8]=1;x=(xx-mu)/sd
train.to_csv(O/'training_inputs.csv',index=False)
def distance(a,b):return np.maximum(0,(a*a).sum(axis=1)[:,None]+(b*b).sum(axis=1)[None,:]-2*a@b.T)/a.shape[1]
dist=distance(x,x);center=float(y.mean());ridge=1e-8;progress=[]
for gamma in [.01,.1,1.,10.]:
 k=np.exp(-gamma*dist);coef=np.linalg.solve(k+ridge*np.eye(len(x)),y-center);p=np.maximum(0,center+k@coef)
 err=abs(p-y);tolerance=np.where(y>0,.1*y,1.)
 progress.append(dict(gamma=gamma,n=len(y),hits=int((err<=tolerance).sum()),mae=float(err.mean()),max_error_g=float(err.max())))
 if (err<=tolerance).all():break
pd.DataFrame(progress).to_csv(O/'training_progress.csv',index=False)
train_output=train[['record_id','pid','time']].copy();train_output['actual']=y;train_output['prediction']=p;train_output['within_tolerance']=err<=tolerance;train_output.to_csv(O/'training_predictions.csv',index=False)
np.savez(O/'frozen_model.npz',x=x,coef=coef,center=center,gamma=gamma,ridge=ridge,median=med,mean=mu,scale=sd)
model_hash=hashlib.sha256((O/'frozen_model.npz').read_bytes()).hexdigest()
# Single evaluation of the reserved group, after the model is saved and frozen.
vs=selection[selection.split.eq('reserved')];assert len(vs)>0
vf=pd.DataFrame([dict(**inputs(r.pid,r.time),record_id=r.record_id) for r in vs.itertuples()]);vf=vf[['record_id','pid','time',*feature_cols]];vf.to_csv(O/'reserved_inputs.csv',index=False)
vr=vf[feature_cols].to_numpy(float);vxx=(np.where(np.isfinite(vr),vr,med)-mu)/sd
pred=np.maximum(0,center+np.exp(-gamma*distance(vxx,x))@coef)
out=vf[['record_id','pid','time']].copy();out['prediction']=pred;out.to_csv(O/'reserved_predictions_before_scoring.csv',index=False)
truth=labels.loc[out.record_id,'carbs_g'].to_numpy(float);out['actual']=truth;out['error_g']=abs(pred-truth);out['within_tolerance']=out.error_g<=np.where(truth>0,.1*truth,1.)
out=out.merge(meals[['record_id','meal_type','protein_g','fat_g','fiber_g']],on='record_id',validate='one_to_one');out.to_csv(O/'reserved_scored.csv',index=False)
summaries=[]
for name,actual,pp in [('training',y,p),('reserved',truth,pred),('reserved_training_mean_baseline',truth,np.full(len(truth),center))]:
 er=abs(actual-pp);summaries.append(dict(group=name,n=len(actual),hits=int((er<=np.where(actual>0,.1*actual,1.)).sum()),mae=float(er.mean()),zero_carb_meals=int((actual==0).sum())))
pd.DataFrame(summaries).to_csv(O/'summary.csv',index=False)
assert hashlib.sha256((O/'frozen_model.npz').read_bytes()).hexdigest()==model_hash
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in source_hashes.items())
saved=np.load(O/'frozen_model.npz');replay=np.maximum(0,float(saved['center'])+np.exp(-float(saved['gamma'])*distance(saved['x'],saved['x']))@saved['coef']);assert np.allclose(replay,p,atol=1e-6,rtol=0)
(O/'manifest.json').write_text(json.dumps(dict(feature_columns=feature_cols,source_hashes=source_hashes,extractor_sha256=hashlib.sha256(src.read_bytes()).hexdigest(),model_sha256=model_hash,training_only_floors=floors,model_reload_predictions_verified=True),indent=2))
print(pd.DataFrame(eligibility).groupby(['split','status']).agg(people=('pid','size'),meals=('query_meals','sum')).to_string())
print(pd.DataFrame(progress).to_string(index=False));print(pd.DataFrame(summaries).to_string(index=False))
