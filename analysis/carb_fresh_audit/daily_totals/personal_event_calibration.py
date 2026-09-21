"""Earlier-only out-of-sample personal event calibration; supplied meal times."""
from pathlib import Path
import json,pickle
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'personal_event_calibration';OUT.mkdir(exist_ok=True)
d=pd.read_csv(ROOT/'event_activity_probe/event_inputs.csv',float_precision='round_trip')
h=d[d.role=='train'].copy();q=d[d.role=='later'].copy()
days=pd.read_csv(ROOT/'delayed_probe/later_results.csv')
(OUT/'PLAN.json').write_text(json.dumps({'scope':'Same 44 development days, supplied meal times; not passive','arms':['reference','plus_hr_activity'],'calibration':'For each earlier day of evaluation people, refit pooled model excluding that persons current and later days and overlapping earlier 4h response windows. Other participants earlier training rows retained. Residuals therefore exclude own target. Use fixed shrinkage of 5 pseudo-events: additive mean residual or multiplicative ratio of observed to predicted sums with 5 mean-prediction pseudo-events. No later-label tuning.','limits':'Same repeatedly inspected development outcomes; no independent validation. Calibration estimates average bias, not individual meal absorption.'},indent=2))
records=[];result=days[['pid','day','actual']].copy();events=q[['pid','day','timestamp','target']].copy()
def model():return HistGradientBoostingRegressor(loss='poisson',max_iter=80,max_leaf_nodes=7,min_samples_leaf=20,l2_regularization=1,early_stopping=False,random_state=20260908)
def score(y,p):
 e=np.abs(y-p);return {'hits':int((e<=.1*y).sum()),'n':len(y),'mape':float(np.mean(e/y)*100),'mae':float(np.mean(e))}
summary={};calibrations=[]
for arm in ['reference','plus_hr_activity']:
 saved=pickle.loads((ROOT/f'event_activity_probe/{arm}_model.pkl').read_bytes());cols=list(saved.feature_names_in_);oof=[]
 for pid in sorted(q.pid.unique()):
  for day,g in h[h.pid==pid].groupby('day'):
   cutoff=pd.Timestamp(g.timestamp.min())-pd.Timedelta(hours=1)
   keep=(h.pid!=pid)|(pd.to_datetime(h.timestamp)+pd.Timedelta(hours=4)<cutoff)
   train=h[keep]
   assert set(train.index).isdisjoint(g.index)
   p=model().fit(train[cols],train.target).predict(g[cols]);z=g[['pid','day','timestamp','target']].copy();z['prediction']=p;z['arm']=arm;oof.append(z)
 oof=pd.concat(oof);records.append(oof)
 pred=saved.predict(q[cols]);assert np.array_equal(pred,saved.predict(q.assign(target=999999)[cols]))
 events[arm]=pred
 for method in ['additive','ratio']:
  adjusted=pred.copy()
  for pid in sorted(q.pid.unique()):
   hist=oof[oof.pid==pid];mask=q.pid.to_numpy()==pid;n=len(hist)
   offset=float((hist.target-hist.prediction).sum()/(n+5))
   ratio=float((hist.target.sum()+5*hist.prediction.mean())/(hist.prediction.sum()+5*hist.prediction.mean()))
   adjusted[mask]=np.maximum(0,pred[mask]+offset) if method=='additive' else pred[mask]*ratio
   calibrations.append(dict(arm=arm,method=method,pid=int(pid),n=n,offset=offset,ratio=ratio))
  events[f'{arm}_{method}']=adjusted
 print(arm,'finished',len(oof),'earlier predictions',flush=True)
for name in events.columns[4:]:
 sums=events.groupby(['pid','day'])[name].sum();result[name]=[sums.loc[(r.pid,r.day)] for _,r in result.iterrows()];summary[name]=score(result.actual.to_numpy(),result[name].to_numpy())
assert len(result)==44 and len(events)==189
pd.concat(records).to_csv(OUT/'earlier_predictions.csv',index=False);pd.DataFrame(calibrations).to_csv(OUT/'calibration.csv',index=False);events.to_csv(OUT/'event_predictions.csv',index=False);result.to_csv(OUT/'daily_predictions.csv',index=False)
(OUT/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
