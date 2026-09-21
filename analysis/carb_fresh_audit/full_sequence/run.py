from pathlib import Path
import json,hashlib
import numpy as np
import pandas as pd
ROOT = str(Path(__file__).resolve().parents[3])  # repo root

O=Path(__file__).resolve().parent;B=O.parent;D=B/'diverse_fit';R=Path(ROOT + '/dataset/cgmacros_clean_v1/participants')
t=pd.read_csv(D/'training_inputs.csv',parse_dates=['time']).merge(pd.read_csv(D/'training_predictions.csv')[['record_id','actual']],on='record_id',validate='one_to_one')
a=pd.read_csv(B/'calibration_gap/anchor_inputs.csv',parse_dates=['time']);v=pd.read_csv(D/'reserved_inputs.csv',parse_dates=['time']);assignment=pd.read_csv(B/'rolling_validation/fold_assignments.csv')
plan=dict(representation='37 baseline-relative Libre readings at 5-minute spacing, 0–180 minutes; baseline mean at -10/-5 min. These are published interpolated observations, not independent native samples.',
 weights=[0.,.25,1.],warp_bins=[0,3,6],k=[1,3],distance='Shape is curve divided by its RMS. Mixture combines shape and raw-amplitude squared differences scaled by median earlier personal curve RMS. Constrained dynamic time warping up to 0/15/30 minutes.',
 selection='Earlier rolling windows only; equal dose-band hit rate then MAE with inverse repeat weights. All matched examples are earlier meals of the same person, including initial anchors.',
 limitation='Copying/averaging historical labels cannot extrapolate past their range; this tests representation, not the full goal by itself.')
(O/'PLAN.json').write_text(json.dumps(plan,indent=2))
allrows=pd.concat([t,a,v],ignore_index=True).drop_duplicates('record_id');curves={};checks=[]
for pid,z in allrows.groupby('pid'):
 path=R/f'CGMacros-{pid:03d}.csv';d=pd.read_csv(path);d.columns=d.columns.str.strip();d.Timestamp=pd.to_datetime(d.Timestamp,format='mixed');d=d.set_index('Timestamp')
 for r in z.itertuples():
  g=d['Libre GL'].reindex(pd.date_range(r.time-pd.Timedelta(minutes=10),r.time+pd.Timedelta(minutes=180),freq='5min')).to_numpy(float);assert len(g)==39 and np.isfinite(g).all()
  curves[r.record_id]=g[2:]-g[:2].mean()
np.savez(O/'curves.npz',**curves)
def band(y):return 'zero' if y==0 else ('low' if y<=30 else ('medium' if y<=70 else 'high'))
def dtw(cost,w):
 if w==0:return float(np.trace(cost)/len(cost))
 n=len(cost);prev=np.full(n+1,np.inf);prev[0]=0
 for i in range(n):
  curr=np.full(n+1,np.inf)
  for j in range(max(0,i-w),min(n,i+w+1)):curr[j+1]=cost[i,j]+min(prev[j],prev[j+1],curr[j])
  prev=curr
 return float(prev[n]/n)
# Cache pairwise costs, not labels. Scaling is supplied from the earlier history.
cache={}
def distance(left,right,weight,warp,scale):
 key=(left,right,weight,warp,scale)
 if key not in cache:
  x=curves[left];y=curves[right];sx=x/max(np.sqrt(np.mean(x*x)),1e-8);sy=y/max(np.sqrt(np.mean(y*y)),1e-8)
  cost=(1-weight)*(sx[:,None]-sy[None,:])**2+weight*((x[:,None]-y[None,:])/scale)**2
  cache[key]=np.sqrt(dtw(cost,warp))
 return cache[key]
def predict(h,q,weight,warp,k):
 scale=max(float(np.median([np.sqrt(np.mean(curves[r]**2)) for r in h.record_id])),1.)
 predictions=[];neighbors=[]
 for r in q.itertuples():
  ds=np.array([distance(r.record_id,rr,weight,warp,scale) for rr in h.record_id]);order=np.argsort(ds,kind='stable')[:k];ww=1/np.maximum(ds[order],.05);p=float(np.average(h.iloc[order].actual,weights=ww));predictions.append(p)
  for rank,i in enumerate(order,1):neighbors.append(dict(record_id=r.record_id,rank=rank,history_record_id=h.iloc[i].record_id,history_carbs=h.iloc[i].actual,distance=ds[i]))
 return predictions,neighbors
counts=assignment[assignment.role.eq('validate')].record_id.value_counts();scores=[];saved=[]
for weight in plan['weights']:
 for warp in plan['warp_bins']:
  for k in plan['k']:
   rows=[]
   for fold,fa in assignment.groupby('fold'):
    for pid,pa in fa.groupby('pid'):
     h=pd.concat([a[a.pid==pid],t[t.record_id.isin(pa[pa.role.eq('fit')].record_id)]]).sort_values('time');q=t[t.record_id.isin(pa[pa.role.eq('validate')].record_id)]
     pp,_=predict(h,q,weight,warp,k)
     for r,p in zip(q.itertuples(),pp):
      er=abs(p-r.actual);rows.append(dict(record_id=r.record_id,fold=fold,pid=pid,actual=r.actual,prediction=p,band=band(r.actual),weight=1/counts[r.record_id],hit=er<=(.1*r.actual if r.actual>0 else 1.),error=er))
   rr=pd.DataFrame(rows);br=[(np.average(z.hit,weights=z.weight),np.average(z.error,weights=z.weight)) for _,z in rr.groupby('band')]
   scores.append(dict(amplitude_weight=weight,warp_bins=warp,k=k,balanced_hits=float(np.mean([v[0] for v in br])),balanced_mae=float(np.mean([v[1] for v in br]))));saved.append(rows)
bestidx=min(range(len(scores)),key=lambda i:(-scores[i]['balanced_hits'],scores[i]['balanced_mae'],scores[i]['warp_bins'],scores[i]['k']));best=scores[bestidx]
pd.DataFrame(scores).to_csv(O/'candidates.csv',index=False);pd.DataFrame(saved[bestidx]).to_csv(O/'rolling_predictions.csv',index=False);(O/'selected_settings.json').write_text(json.dumps(best,indent=2))
rows=[];neighbors=[]
for pid,q in v.groupby('pid'):
 h=pd.concat([a[a.pid==pid],t[t.pid==pid]]).sort_values('time');assert h.time.max()+pd.Timedelta(hours=3)<q.time.min()
 pp,dd=predict(h,q,best['amplitude_weight'],best['warp_bins'],best['k']);neighbors.extend(dd)
 for r,p in zip(q.itertuples(),pp):rows.append(dict(record_id=r.record_id,pid=pid,time=r.time,prediction=p))
out=pd.DataFrame(rows);out.to_csv(O/'predictions_before_scoring.csv',index=False);pd.DataFrame(neighbors).to_csv(O/'neighbors.csv',index=False)
out=out.merge(pd.read_csv(D/'reserved_scored.csv')[['record_id','actual','meal_type']],on='record_id',validate='one_to_one');out['band']=[band(y) for y in out.actual];out['error_g']=abs(out.prediction-out.actual);out['within_tolerance']=out.error_g<=np.where(out.actual>0,.1*out.actual,1.);out.to_csv(O/'later_results.csv',index=False)
bs=out.groupby('band').agg(n=('actual','size'),hits=('within_tolerance','sum'),mae=('error_g','mean'));bs.to_csv(O/'band_scores.csv')
assert dtw(np.zeros((37,37)),0)==0 and dtw(np.zeros((37,37)),3)==0
manifest=json.loads((D/'manifest.json').read_text());assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in manifest['source_hashes'].items())
summary=dict(n=len(out),hits=int(out.within_tolerance.sum()),mae=float(out.error_g.mean()),sources_unchanged=True)
(O/'summary.json').write_text(json.dumps(summary,indent=2));print(best);print(summary);print(bs.to_string())
