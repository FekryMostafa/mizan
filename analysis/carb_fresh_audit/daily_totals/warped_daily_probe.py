"""Timing-tolerant full glucose trace matching without meal times."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'warped_daily_probe';OUT.mkdir(exist_ok=True)
(OUT/'PLAN.json').write_text(json.dumps({'scope':'Same64 earlier/44 later days, passive30h glucose traces.','distance':'Subtract each trace10th percentile, preserve amplitudes. Banded dynamic time warping: allowed clock shifts0/60/120min, squared differences, root total cost divided by120. No meal times or labels used in distance.','prediction':'Personal known-label mean plus weighted residuals of training days. Distances weight exp(-distance_squared/(2*bandwidth_squared)), bandwidth5/15/30mg/dL. Personal-only or pooled neighbors or equal blend. Pooled labels centered within person.','selection':'27 fixed configurations plus personalmean, choose33 earlier chronological validation MAP E thenMAE. All later44 retained; repeatedly inspected development data.'},indent=2))
d=pd.read_csv(ROOT/'delayed_probe/sensor_inputs.csv').reset_index(drop=True);d['row']=np.arange(len(d));g=d[[f'seq_{i:02}' for i in range(96)]+[f'nextseq_{i:02}' for i in range(24)]].to_numpy(float);assert np.isfinite(g).all();g=g-np.percentile(g,10,axis=1)[:,None];n,T=g.shape;aa,bb=np.triu_indices(n);a=g[aa];b=g[bb];distances={}
for band in [0,4,8]:
 prev=np.full((len(aa),T+1),np.inf);prev[:,0]=0
 for i in range(1,T+1):
  cur=np.full_like(prev,np.inf)
  for j in range(max(1,i-band),min(T,i+band)+1):cur[:,j]=(a[:,i-1]-b[:,j-1])**2+np.minimum(np.minimum(prev[:,j],cur[:,j-1]),prev[:,j-1])
  prev=cur
 m=np.zeros((n,n));m[aa,bb]=np.sqrt(prev[:,-1]/T);m[bb,aa]=m[aa,bb];assert np.allclose(m,m.T) and np.allclose(np.diag(m),0);distances[band]=m
 if band==0:assert np.allclose(m[aa,bb],np.sqrt(np.mean((a-b)**2,axis=1)))
 print('distance band',band,'complete',flush=True)
np.savez_compressed(OUT/'distances.npz',**{f'band{k}':v for k,v in distances.items()});h=pd.read_csv(ROOT/'delayed_probe/final_training_days.csv').merge(d,on=['pid','day']);q=d[d.split=='later'];parts=[]
for idx,r in h.iterrows():
 own=h[(h.pid==r.pid)&(pd.to_datetime(h.day)+pd.Timedelta(hours=30)<=pd.Timestamp(r.day))]
 if len(own):parts.append((pd.concat([h[h.pid!=r.pid],own]),h.loc[[idx]]))
assert len(parts)==33
settings=[dict(band=0,width=0,mix=0)]+[dict(band=b,width=w,mix=m) for b in [0,4,8] for w in [5,15,30] for m in [0,.5,1]]
def predict(tr,query,s):
 means=tr.groupby('pid').actual.mean();res=tr.actual.to_numpy()-tr.pid.map(means).to_numpy();out=[]
 for _,r in query.iterrows():
  base=means.loc[r.pid]
  if not s['width']:out.append(base);continue
  distance=distances[s['band']][int(r.row),tr.row.to_numpy(int)];logw=-distance**2/(2*s['width']**2);w=np.exp(logw-logw.max());pooled=np.dot(w,res)/w.sum();mask=tr.pid.to_numpy()==r.pid;ownlog=logw[mask];ownw=np.exp(ownlog-ownlog.max());own=np.dot(ownw,res[mask])/ownw.sum();out.append(max(0,base+s['mix']*pooled+(1-s['mix'])*own))
 return np.array(out)
def score(y,p):
 e=abs(y-p);return dict(n=len(y),hits=int((e<=.1*y).sum()),mape=float((e/y).mean()*100),mae=float(e.mean()))
rows=[]
for i,s in enumerate(settings):
 y=[];p=[]
 for tr,v in parts:y.extend(v.actual);p.extend(predict(tr,v,s))
 rows.append(dict(candidate=i,**s,**score(np.array(y),np.array(p))))
rank=pd.DataFrame(rows).sort_values(['mape','mae'],kind='stable');rank.to_csv(OUT/'validation.csv',index=False);s=settings[int(rank.iloc[0].candidate)];(OUT/'settings.json').write_text(json.dumps(s,indent=2));p=predict(h,q,s);out=q[['pid','day']].copy();out['prediction']=p;out.to_csv(OUT/'predictions_before_scoring.csv',index=False);out['actual']=q.actual;out.to_csv(OUT/'later_results.csv',index=False);assert np.array_equal(p,predict(h,q.assign(actual=999999),s));summary=dict(selected=s,validation=rank.iloc[0].to_dict(),later=score(q.actual.to_numpy(),p),all44=len(q)==44,query_labels_unused=True);(OUT/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2));print(rank.head(8).to_string(index=False))
