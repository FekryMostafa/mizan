from pathlib import Path
import json,hashlib
import numpy as np
import pandas as pd

O=Path(__file__).resolve().parent;B=O.parent;D=B/'diverse_fit'
t=pd.read_csv(D/'training_inputs.csv',parse_dates=['time']).merge(pd.read_csv(D/'training_predictions.csv')[['record_id','actual']],on='record_id',validate='one_to_one')
anchors=pd.read_csv(B/'calibration_gap/anchor_inputs.csv',parse_dates=['time']);assign=pd.read_csv(B/'rolling_validation/fold_assignments.csv')
manifest=json.loads((D/'manifest.json').read_text());cols=manifest['feature_columns']
families={'shape':['shape_start','shape_minimum'],'glucose':[c for c in cols if '_hr' not in c and 'activity' not in c],'glucose_activity':cols}
plan=dict(model='Same-person nearest-history retrieval, including the two initial known calibration meals.',families=families,neighbors=[1,3,5],scaling=['pooled_earlier','personal_earlier'],
 selection='Same three earlier chronological validation windows, inverse repeat weights, equal-band hit rate then equal-band MAE. No later answers select settings.',prediction='One neighbor returns its recorded grams; 3/5 neighbors use inverse-distance weighted mean, distance floor 0.05. No rounding to 24/66.',
 caveat='Reused development evaluation. Retrieval tests matching known examples; it does not by itself establish novel-dose inference.')
(O/'PLAN.json').write_text(json.dumps(plan,indent=2))
count=assign[assign.role.eq('validate')].record_id.value_counts()
def band(y):return 'zero' if y==0 else ('low' if y<=30 else ('medium' if y<=70 else 'high'))
def prepare(history,features):
 raw=history[features].to_numpy(float);med=np.array([np.nanmedian(v) if np.isfinite(v).any() else 0 for v in raw.T]);x=np.where(np.isfinite(raw),raw,med);mu=x.mean(0);sd=x.std(0);sd[sd<1e-8]=1
 return med,mu,sd
def transform(frame,features,stats):
 med,mu,sd=stats;v=frame[features].to_numpy(float);return (np.where(np.isfinite(v),v,med)-mu)/sd
def retrieve(history,query,features,stats,k):
 x=transform(history,features,stats);q=transform(query,features,stats);out=[];details=[]
 for row,z in zip(query.itertuples(),q):
  distances=np.sqrt(np.mean((x-z)**2,axis=1));order=np.argsort(distances,kind='stable')[:min(k,len(x))];weights=1/np.maximum(distances[order],.05);p=float(np.average(history.iloc[order].actual,weights=weights));out.append(p)
  for rank,ix in enumerate(order,1):
   r=history.iloc[ix];details.append(dict(record_id=row.record_id,pid=row.pid,rank=rank,earlier_record_id=r.record_id,earlier_carbs=r.actual,distance=float(distances[ix])))
 return out,details
scores=[];allrows=[]
for family,features in families.items():
 for scaling in plan['scaling']:
  for k in plan['neighbors']:
   rows=[]
   for fold,fa in assign.groupby('fold'):
    pool=pd.concat([anchors,t[t.record_id.isin(fa[fa.role.eq('fit')].record_id)]],ignore_index=True);pooled_stats=prepare(pool,features)
    for pid,pa in fa.groupby('pid'):
     h=pool[pool.pid==pid].sort_values('time');q=t[t.record_id.isin(pa[pa.role.eq('validate')].record_id)]
     stats=pooled_stats if scaling=='pooled_earlier' else prepare(h,features)
     pred,_=retrieve(h,q,features,stats,k)
     for r,p in zip(q.itertuples(),pred):
      er=abs(p-r.actual);rows.append(dict(record_id=r.record_id,pid=pid,fold=fold,band=band(r.actual),actual=r.actual,prediction=p,error=er,hit=er<=(.1*r.actual if r.actual>0 else 1.),weight=1/count[r.record_id]))
   df=pd.DataFrame(rows);br=[(np.average(z.hit,weights=z.weight),np.average(z.error,weights=z.weight)) for _,z in df.groupby('band')]
   scores.append(dict(family=family,scaling=scaling,k=k,balanced_hits=float(np.mean([v[0] for v in br])),balanced_mae=float(np.mean([v[1] for v in br]))));allrows.append(rows)
bestindex=min(range(len(scores)),key=lambda i:(-scores[i]['balanced_hits'],scores[i]['balanced_mae'],scores[i]['k'],len(families[scores[i]['family']])));best=scores[bestindex]
pd.DataFrame(scores).to_csv(O/'candidates.csv',index=False);pd.DataFrame(allrows[bestindex]).to_csv(O/'rolling_predictions.csv',index=False);(O/'selected_settings.json').write_text(json.dumps(best,indent=2))
later=pd.read_csv(D/'reserved_inputs.csv',parse_dates=['time']);pool=pd.concat([anchors,t],ignore_index=True);features=families[best['family']];pooled_stats=prepare(pool,features)
rows=[];details=[]
for pid,q in later.groupby('pid'):
 h=pool[pool.pid==pid].sort_values('time');assert h.time.max()+pd.Timedelta(hours=3)<q.time.min()
 stats=pooled_stats if best['scaling']=='pooled_earlier' else prepare(h,features)
 pred,dd=retrieve(h,q,features,stats,best['k']);details.extend(dd)
 for r,p in zip(q.itertuples(),pred):rows.append(dict(record_id=r.record_id,pid=pid,time=r.time,prediction=p))
out=pd.DataFrame(rows);out.to_csv(O/'predictions_before_scoring.csv',index=False);pd.DataFrame(details).to_csv(O/'neighbors.csv',index=False)
out=out.merge(pd.read_csv(D/'reserved_scored.csv')[['record_id','actual','meal_type']],on='record_id',validate='one_to_one');out['error_g']=abs(out.prediction-out.actual);out['within_tolerance']=out.error_g<=np.where(out.actual>0,.1*out.actual,1.);out['band']=[band(v) for v in out.actual]
# These are hindsight coverage ceilings on this retrieval family, not predictions.
for i,r in out.iterrows():
 values=pool[pool.pid==r.pid].actual.to_numpy();tol=.1*r.actual if r.actual>0 else 1.
 out.loc[i,'any_personal_label_within_tolerance']=bool((abs(values-r.actual)<=tol).any())
 out.loc[i,'personal_label_range_can_reach_tolerance']=bool(values.min()<=r.actual+tol and values.max()>=r.actual-tol)
out.to_csv(O/'later_results.csv',index=False);bands=out.groupby('band').agg(n=('actual','size'),hits=('within_tolerance','sum'),mae=('error_g','mean'));bands.to_csv(O/'band_scores.csv')
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in manifest['source_hashes'].items())
report=dict(later_n=len(out),later_hits=int(out.within_tolerance.sum()),later_mae=float(out.error_g.mean()),nearest_one_oracle_label_ceiling=int(out.any_personal_label_within_tolerance.sum()),convex_combination_oracle_ceiling=int(out.personal_label_range_can_reach_tolerance.sum()),source_hashes_unchanged=True)
(O/'summary.json').write_text(json.dumps(report,indent=2));print(best);print(report);print(bands.to_string())
