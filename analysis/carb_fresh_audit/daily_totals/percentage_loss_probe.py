"""Direct relative-error loss with leave-own-label-out personal context."""
from pathlib import Path
import json,pickle
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'percentage_loss_probe';OUT.mkdir(exist_ok=True)
d=pd.read_csv(ROOT/'delayed_probe/sensor_inputs.csv');h=pd.read_csv(ROOT/'delayed_probe/final_training_days.csv').merge(d,on=['pid','day']);q=d[d.split=='later']
families={'glucose':[c for c in d if c.startswith('g_') or c.startswith('next_glucose')],'context':[c for c in d if c.startswith(('g_','ctx_','next_'))]}
(OUT/'PLAN.json').write_text(json.dumps({'scope':'Same64 training/44 later days, sensors through next06:00, no query food information.','model':'100 boosting rounds, L2=1, learning_rate0.05, leaves3 or7, min_leaf5. Raw sensor features plus personal sensor deviations and personal earlier mean intake. Each training row personal mean excludes its own target; singleton uses other-person pooled mean.','objective':'absolute_error weighted1/actual minimizes empirical absolute percentage error; squared_error unweighted is paired control. Predict residual to personal mean.','selection':'33 earlier chronological validation days. Eight model configurations and mean/weighted-median personal baselines. MAPE thenMAE. No later-label tuning.'},indent=2))
def prep(tr,rows,cols,training=False):
 centers=tr.groupby('pid')[cols].mean();a=rows[cols].to_numpy(float);delta=a-centers.loc[rows.pid].to_numpy();means=tr.groupby('pid').actual.mean()
 if training:
  sums=tr.groupby('pid').actual.sum();counts=tr.groupby('pid').actual.count();n=tr.pid.map(counts).to_numpy()-1;base=np.divide(tr.pid.map(sums).to_numpy()-tr.actual,n,out=(tr.actual.sum()-tr.actual.to_numpy())/(len(tr)-1),where=n>0)
 else:base=rows.pid.map(means).to_numpy()
 return np.column_stack([a,delta,base]),base

def fit(tr,s):
 if s['family']=='baseline':return tr[['pid','actual']].copy()
 x,base=prep(tr,tr,families[s['family']],True);m=HistGradientBoostingRegressor(loss=s['loss'],max_iter=100,max_leaf_nodes=s['leaves'],min_samples_leaf=5,l2_regularization=1,learning_rate=.05,early_stopping=False,random_state=20260908);w=1/tr.actual.to_numpy() if s['loss']=='absolute_error' else None
 if w is not None:w=w/w.mean()
 m.fit(x,tr.actual.to_numpy()-base,sample_weight=w);return m

def predict(tr,query,s,m):
 if s['family']=='baseline':
  values={}
  for pid,g in tr.groupby('pid'):
   y=np.sort(g.actual.to_numpy());w=1/y;values[pid]=y[np.searchsorted(np.cumsum(w),w.sum()/2)] if s['loss']=='weighted_median' else y.mean()
  return query.pid.map(values).to_numpy()
 x,base=prep(tr,query,families[s['family']]);return np.maximum(0,base+m.predict(x))
def score(y,p):
 e=abs(y-p);return dict(n=len(y),hits=int((e<=.1*y).sum()),mape=float((e/y).mean()*100),mae=float(e.mean()))
parts=[]
for idx,r in h.iterrows():
 own=h[(h.pid==r.pid)&(pd.to_datetime(h.day)+pd.Timedelta(hours=30)<=pd.Timestamp(r.day))]
 if len(own):parts.append((pd.concat([h[h.pid!=r.pid],own]),h.loc[[idx]]))
assert len(parts)==33
settings=[dict(family='baseline',loss=l,leaves=0) for l in ['mean','weighted_median']]+[dict(family=f,loss=l,leaves=n) for f in families for l in ['squared_error','absolute_error'] for n in [3,7]];rows=[]
for i,s in enumerate(settings):
 y=[];p=[]
 for tr,v in parts:y.extend(v.actual);p.extend(predict(tr,v,s,fit(tr,s)))
 rows.append(dict(candidate=i,**s,**score(np.array(y),np.array(p))))
 print(i,'complete',flush=True)
rank=pd.DataFrame(rows).sort_values(['mape','mae'],kind='stable');rank.to_csv(OUT/'validation.csv',index=False);s=settings[int(rank.iloc[0].candidate)];(OUT/'settings.json').write_text(json.dumps(s,indent=2));m=fit(h,s);p=predict(h,q,s,m);out=q[['pid','day']].copy();out['prediction']=p;out.to_csv(OUT/'predictions_before_scoring.csv',index=False);out['actual']=q.actual;out.to_csv(OUT/'later_results.csv',index=False)
(OUT/'model.pkl').write_bytes(pickle.dumps(m));assert np.array_equal(p,predict(h,q.assign(actual=999999),s,pickle.loads((OUT/'model.pkl').read_bytes())))
# Changing a row's target must not change its personal-mean input.
probe=h.copy();probe.loc[probe.index[0],'actual']+=10000
assert abs(prep(h,h,families['glucose'],True)[1][0]-prep(probe,probe,families['glucose'],True)[1][0])<1e-8
summary=dict(selected=s,validation=rank.iloc[0].to_dict(),later=score(q.actual.to_numpy(),p),all44=len(out)==44,query_labels_unused=True,own_label_excluded_from_personal_input=True);(OUT/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2));print(rank.to_string(index=False))
