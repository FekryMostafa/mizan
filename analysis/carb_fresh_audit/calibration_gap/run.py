from pathlib import Path
import ast,json,hashlib
import numpy as np
import pandas as pd
ROOT = str(Path(__file__).resolve().parents[3])  # repo root

O=Path(__file__).resolve().parent;B=O.parent;D=B/'diverse_fit';V=B/'rolling_validation'
R=Path(ROOT + '/dataset/cgmacros_clean_v1')
meals=pd.read_csv(R/'meals.csv',parse_dates=['timestamp']);tr=pd.read_csv(D/'training_inputs.csv',parse_dates=['time']);later=pd.read_csv(D/'reserved_inputs.csv',parse_dates=['time'])
labels=pd.read_csv(D/'training_predictions.csv')[['record_id','actual']];tr=tr.merge(labels,on='record_id',validate='one_to_one')
manifest=json.loads((D/'manifest.json').read_text());cols=manifest['feature_columns'];floors=manifest['training_only_floors'];gcols=list(floors)
source=B/'frozen_later_meals/evaluate.py';tree=ast.parse(source.read_text());nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['observations','inputs']];exec(compile(ast.Module(body=nodes,type_ignores=[]),str(source),'exec'))
data={};anchors={};anchor_rows=[]
for pid in sorted(tr.pid.unique()):
 d=pd.read_csv(R/'participants'/f'CGMacros-{pid:03d}.csv');d.columns=d.columns.str.strip();d.Timestamp=pd.to_datetime(d.Timestamp,format='mixed');d=d.set_index('Timestamp');data[pid]=d
 z=meals[(meals.participant_id==pid)&meals.isolated_libre_calibration_candidate]
 z=z[z.meal_type.eq('breakfast')&z.protein_g.eq(22)&z.fat_g.eq(10.5)&z.fiber_g.eq(0)]
 refs=[]
 for dose in [24,66]:
  q=z[z.carbs_g.eq(dose)].sort_values('timestamp')
  for r in q.itertuples():
   pre=d['Libre GL'].reindex(pd.date_range(r.timestamp-pd.Timedelta(minutes=10),periods=10,freq='min'))
   if np.isfinite(pre).all() and pre.gt(40).all() and pre.lt(400).all():refs.append(r);break
 assert len(refs)==2
 anchors[pid]=[observations(pid,r.timestamp) for r in refs]
 for r in refs:
  assert r.timestamp+pd.Timedelta(hours=3)<tr[tr.pid==pid].time.min()
  anchor_rows.append(dict(**inputs(pid,r.timestamp),record_id=r.record_id,actual=r.carbs_g))
an=pd.DataFrame(anchor_rows)[['record_id','pid','time',*cols,'actual']];an.to_csv(O/'anchor_inputs.csv',index=False)
assert len(an)==52 and set(an.record_id).isdisjoint(set(tr.record_id)|set(later.record_id))
# Validate that rehydrated calibration references recreate earlier model inputs.
replay=pd.DataFrame([inputs(r.pid,r.time) for r in tr.itertuples()]);assert np.allclose(replay[cols].to_numpy(),tr[cols].to_numpy(),equal_nan=True,atol=1e-8,rtol=0)
saved=np.load(V/'frozen_model.npz');gamma=float(saved['gamma']);ridge=float(saved['ridge'])
def transform(frame):
 v=frame[cols].to_numpy(float);return (np.where(np.isfinite(v),v,saved['median'])-saved['mean'])/saved['scale']
def dist(a,b):return np.maximum(0,(a*a).sum(axis=1)[:,None]+(b*b).sum(axis=1)[None,:]-2*a@b.T)/a.shape[1]
ax=transform(an);vx=transform(later)
old_anchor=np.maximum(0,float(saved['center'])+np.exp(-gamma*dist(ax,saved['x']))@saved['coef'])
plan=dict(change='Add 52 known calibration meals as labeled training examples; no changes to gamma, ridge, input features or preprocessing statistics.',
 gamma=gamma,ridge=ridge,old_training=211,new_training=263,final_later=107,
 caveat='Controlled development ablation motivated after inspecting previous outcomes; not a fresh validation or proof of root cause.')
(O/'PLAN.json').write_text(json.dumps(plan,indent=2))
expanded=pd.concat([tr,an],ignore_index=True);x=transform(expanded);y=expanded.actual.to_numpy();center=y.mean();k=np.exp(-gamma*dist(x,x));coef=np.linalg.solve(k+ridge*np.eye(len(x)),y-center)
np.savez(O/'frozen_model.npz',x=x,coef=coef,center=center,gamma=gamma,ridge=ridge,median=saved['median'],mean=saved['mean'],scale=saved['scale'])
new_anchor=np.maximum(0,center+np.exp(-gamma*dist(ax,x))@coef);pred=np.maximum(0,center+np.exp(-gamma*dist(vx,x))@coef)
ac=an[['record_id','pid','actual']].copy();ac['before']=old_anchor;ac['after']=new_anchor;ac.to_csv(O/'anchor_predictions.csv',index=False)
out=later[['record_id','pid','time']].copy();out['prediction']=pred;out.to_csv(O/'predictions_before_scoring.csv',index=False)
old=pd.read_csv(V/'later_results.csv')[['record_id','actual','prediction']].rename(columns={'prediction':'before'})
out=out.merge(old,on='record_id',validate='one_to_one');out['error_g']=abs(out.prediction-out.actual);out['within_tolerance']=out.error_g<=np.where(out.actual>0,.1*out.actual,1.);out.to_csv(O/'later_results.csv',index=False)
# Neighborhood inspection: same-person historical meals incl. both initial anchors.
neighbors=[]
for i,r in later.iterrows():
 ix=np.flatnonzero(expanded.pid.to_numpy()==r.pid);ds=dist(vx[i:i+1],x[ix])[0];order=np.argsort(ds)[:3]
 for rank,q in enumerate(order,1):
  h=expanded.iloc[ix[q]];neighbors.append(dict(record_id=r.record_id,pid=r.pid,rank=rank,earlier_record_id=h.record_id,earlier_carbs=h.actual,distance=float(ds[q]),is_initial_anchor=h.record_id in set(an.record_id)))
n=pd.DataFrame(neighbors);n.to_csv(O/'same_person_neighbors.csv',index=False)
first=n[n['rank']==1].merge(out[['record_id','actual']],on='record_id');first['match_within_tolerance']=abs(first.earlier_carbs-first.actual)<=np.where(first.actual>0,.1*first.actual,1.)
summaries=[]
for name,yy,pp in [('anchors_before',an.actual.to_numpy(),old_anchor),('anchors_after',an.actual.to_numpy(),new_anchor),('later_before',out.actual.to_numpy(),out.before.to_numpy()),('later_after',out.actual.to_numpy(),pred)]:
 er=abs(yy-pp);summaries.append(dict(group=name,n=len(yy),hits=int((er<=np.where(yy>0,.1*yy,1.)).sum()),mae=float(er.mean())))
pd.DataFrame(summaries).to_csv(O/'summary.csv',index=False)
first.to_csv(O/'nearest_history_label_agreement.csv',index=False)
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in manifest['source_hashes'].items())
print(pd.DataFrame(summaries).to_string(index=False));print('NEAREST PERSONAL HISTORY LABEL AGREEMENT',first.match_within_tolerance.sum(),'/',len(first));print(ac.groupby('actual')[['before','after']].agg(['min','max']).to_string())
