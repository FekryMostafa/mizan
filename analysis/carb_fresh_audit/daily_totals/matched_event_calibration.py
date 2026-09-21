"""Prespecified context-matched personal residual correction."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'matched_event_calibration';OUT.mkdir(exist_ok=True)
(OUT/'PLAN.json').write_text(json.dumps({'scope':'Same CGMacros 44 development days. Known meal times, not passive.','method':'For each query use only earlier nonoverlapping same-person out-of-sample residuals. Three nearest events, Gaussian similarity weights, two zero-residual pseudo-events. No later-label selection.','distances':'Equal mean across feature blocks: clock sin/cos scale1; relative glucose and prebaseline scale20 mg/dL; HR scale20 bpm; activity scale1 kcal/min. Missing pairs omitted; require half block coordinates available; unavailable blocks ignored.','arms':['clock','glucose','context','glucose_context'],'validation':'Earlier event MAE on events with >=3 eligible prior residuals; compares identical events. Later scores remain all44 days.'},indent=2))
d=pd.read_csv(ROOT/'event_activity_probe/event_inputs.csv',float_precision='round_trip');old=pd.read_csv(ROOT/'personal_event_calibration/earlier_predictions.csv');later=pd.read_csv(ROOT/'personal_event_calibration/event_predictions.csv');days=pd.read_csv(ROOT/'delayed_probe/later_results.csv')
keys=['pid','day','timestamp'];features=d.drop(columns=['target','role']);hist=old[old.arm=='plus_hr_activity'].merge(features,on=keys,validate='one_to_one');query=later[keys+['target','plus_hr_activity']].rename(columns={'plus_hr_activity':'prediction'}).merge(features,on=keys,validate='one_to_one')
blocks={'clock':(['clock_sin','clock_cos'],1),'glucose':([c for c in d if c.startswith('relative_')]+['pre_glucose'],20),'hr':([c for c in d if c.startswith('hr_')],20),'activity':([c for c in d if c.startswith('activity_')],1)}
arms={'clock':['clock'],'glucose':['glucose'],'context':['clock','hr','activity'],'glucose_context':['clock','glucose','hr','activity']}
def correct(r,pool,groups):
 distances=[]
 for group in groups:
  cols,scale=blocks[group];a=pool[cols].to_numpy(float);b=r[cols].to_numpy(float);valid=np.isfinite(a)&np.isfinite(b);n=valid.sum(axis=1);v=np.where(valid,((a-b)/scale)**2,0).sum(axis=1)/np.maximum(n,1);v[n<len(cols)/2]=np.nan;distances.append(v)
 z=np.asarray(distances);n=np.isfinite(z).sum(axis=0);dist=np.nansum(z,axis=0)/np.maximum(n,1);dist[n==0]=np.inf
 ix=np.argsort(dist,kind='stable')[:3];w=np.exp(-dist[ix]/2);res=(pool.target-pool.prediction).to_numpy()[ix];offset=float(np.dot(w,res)/(w.sum()+2));return max(0,float(r.prediction)+offset),';'.join(pool.timestamp.iloc[ix].astype(str))
outputs={};neighbors=[]
for phase,queries in [('earlier',hist),('later',query)]:
 rows=[]
 for _,r in queries.iterrows():
  pool=hist[(hist.pid==r.pid)&(pd.to_datetime(hist.timestamp)+pd.Timedelta(hours=4)<pd.Timestamp(r.timestamp)-pd.Timedelta(hours=1))]
  if phase=='earlier' and len(pool)<3:continue
  row={k:r[k] for k in keys+['target','prediction']};row['n_history']=len(pool)
  for arm,groups in arms.items():
   value,used=correct(r,pool,groups);row[arm]=value;neighbors.append(dict(phase=phase,pid=r.pid,timestamp=r.timestamp,arm=arm,neighbors=used))
  rows.append(row)
 outputs[phase]=pd.DataFrame(rows);outputs[phase].to_csv(OUT/f'{phase}_event_predictions.csv',index=False)
summary={'earlier':{},'later':{}};out=days[['pid','day','actual']].copy()
for name in ['prediction']+list(arms):
 a=outputs['earlier'];summary['earlier'][name]={'n':len(a),'mae':float(abs(a.target-a[name]).mean())}
 sums=outputs['later'].groupby(['pid','day'])[name].sum();out[name]=[sums.loc[(r.pid,r.day)] for _,r in out.iterrows()];e=abs(out.actual-out[name]);summary['later'][name]={'n':len(out),'hits':int((e<=out.actual*.1).sum()),'mape':float((e/out.actual).mean()*100),'mae':float(e.mean())}
assert len(out)==44 and len(outputs['later'])==189
assert np.allclose(out.prediction,pd.read_csv(ROOT/'event_activity_probe/daily_predictions.csv').plus_hr_activity,atol=1e-8,rtol=0)
pd.DataFrame(neighbors).to_csv(OUT/'neighbors.csv',index=False);out.to_csv(OUT/'daily_predictions.csv',index=False);(OUT/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
