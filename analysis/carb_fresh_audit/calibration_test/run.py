from pathlib import Path
import json,hashlib
import numpy as np,pandas as pd
ROOT = str(Path(__file__).resolve().parents[3])  # repo root

O=Path(__file__).resolve().parent;B=O.parent;R=Path(ROOT + '/dataset/csv')
f=pd.read_csv(B/'libre_features.csv');gcols=list(f.columns[4:]);people=sorted(f.pid.unique());records=[]
for pid,z in f.groupby('pid'):
 d=pd.read_csv(R/f'CGMacros-{pid:03d}.csv');d.columns=d.columns.str.strip();d.Timestamp=pd.to_datetime(d.Timestamp,format='mixed')
 for r in z.itertuples():
  m=(d.Timestamp-pd.Timestamp(r.time)).dt.total_seconds()/60;v=r._asdict();v.pop('Index')
  for name,a,b in [('pre',-180,0),('early',0,60),('middle',60,120),('late',120,180)]:
   w=d[(m>=a)&(m<b)]
   for c,label in [('HR','hr'),('Calories (Activity)','activity')]:
    vals=pd.to_numeric(w[c],errors='coerce');v[name+'_'+label+'_mean']=float(vals.mean());v[name+'_'+label+'_coverage']=float(vals.notna().sum()/(b-a))
    if label=='hr':v[name+'_hr_p90']=float(vals.quantile(.9))
  records.append(v)
f=pd.DataFrame(records);f.to_csv(O/'features.csv',index=False);acols=[v for v in f if v not in ['pid','role','time','carbs',*gcols]];cols=gcols+acols
vals={};times={}
for pid in people:
 z=f[f.pid==pid].set_index('role').loc[['low_calibration','high_calibration','low_query','high_query']]
 vals[pid]=z[cols].to_numpy(float);times[pid]=z.time.tolist()
plan={'families':['CGM','CGM_activity'],'conversion':['plain','anchored'], 'alpha':[1.,10.,100.],
 'activity':'HR mean, 90th percentile and coverage, Fitbit kcal/min mean and coverage for -180:0,0:60,60:120,120:180 min',
 'missing':'training-only median imputation; coverage columns retained; entirely missing training column filled zero',
 'validation':'outer person held out, inner person-held-out alpha selection by within10 count then MAE; own earlier two calibration meals permitted',
 'anchored':'linear ridge fitted to other-person later meals with exact equality constraints at evaluated personal calibration meals',
 'plain':'same ridge without equality constraints; identical preprocessing',
 'objective':'per-meal carbohydrate grams within ±10%; continuous predictions, only lower clipping at zero',
 'scope':'52 previously inspected controlled repeat meals; no reserved data; no unseen-dose validation'}
(O/'PLAN.json').write_text(json.dumps(plan,indent=2))
def design(train,test,family):
 n=len(gcols) if family=='CGM' else len(cols)
 floor=.25*np.median([abs(vals[p][1,:len(gcols)]-vals[p][0,:len(gcols)])/2 for p in train],axis=0)
 def norm(p):
  x=vals[p][:,:n].copy();delta=(x[1,:len(gcols)]-x[0,:len(gcols)])/2
  den=np.where(delta<0,-1,1)*np.maximum(np.maximum(abs(delta),floor),1e-8)
  x[:,:len(gcols)]=(x[:,:len(gcols)]-x[:2,:len(gcols)].mean(axis=0))/den
  return x
 a=np.vstack([norm(p)[2:] for p in train]);b=norm(test)
 med=np.array([np.median(z[np.isfinite(z)]) if np.isfinite(z).any() else 0 for z in a.T])
 a=np.where(np.isfinite(a),a,med);b=np.where(np.isfinite(b),b,med)
 mu=a.mean(axis=0);sd=a.std(axis=0);sd[sd<1e-8]=1
 return np.c_[np.ones(len(a)),(a-mu)/sd],np.c_[np.ones(len(b)),(b-mu)/sd]
def fit(a,b,alpha,anchored):
 y=np.tile([-1.,1.],len(a)//2);pen=np.eye(a.shape[1])*alpha;pen[0,0]=0
 h=a.T@a+pen;coef=np.linalg.solve(h,a.T@y)
 if anchored:
  c=b[:2];target=np.array([-1.,1.]);hc=np.linalg.solve(h,c.T)
  coef=coef+hc@np.linalg.solve(c@hc,target-c@coef)
  assert np.allclose(c@coef,target,atol=1e-6)
 return np.maximum(0,45+21*(b@coef))
rows=[];selected=[];candidates=[]
for family in ['CGM','CGM_activity']:
 for anchored in [False,True]:
  for held in people:
   train=[p for p in people if p!=held]
   inn=[design([p for p in train if p!=v],v,family) for v in train]
   scores=[]
   for alpha in plan['alpha']:
    pred=np.concatenate([fit(a,b,alpha,anchored)[2:] for a,b in inn]);truth=np.tile([24.,66.],len(train));err=abs(pred-truth)
    scores.append((-int((err<=.1*truth).sum()),float(err.mean())))
   j=min(range(3),key=lambda j:scores[j]);alpha=plan['alpha'][j]
   a,b=design(train,held,family);pred=fit(a,b,alpha,anchored)
   selected.append(dict(pid=int(held),family=family,anchored=anchored,alpha=alpha,inner_hits=-scores[j][0],inner_mae=scores[j][1]))
   for k,actual in enumerate([24.,66.,24.,66.]):
    rows.append(dict(pid=int(held),time=times[held][k],role=['low_calibration','high_calibration','low_query','high_query'][k],family=family,anchored=anchored,actual=actual,predicted=float(pred[k]),error_g=float(abs(pred[k]-actual)),within10=bool(abs(pred[k]-actual)<=.1*actual)))
p=pd.DataFrame(rows);p.to_csv(O/'predictions.csv',index=False);pd.DataFrame(selected).to_csv(O/'selection.csv',index=False)
s=p.assign(stage=np.where(p.role.str.endswith('query'),'evaluation','calibration')).groupby(['family','anchored','stage']).agg(meals=('within10','size'),hits=('within10','sum'),MAE=('error_g','mean')).reset_index();s.to_csv(O/'summary.csv',index=False)
(O/'manifest.json').write_text(json.dumps({str(v):hashlib.sha256(v.read_bytes()).hexdigest() for v in [Path(__file__),B/'libre_features.csv',O/'features.csv',O/'PLAN.json']},indent=2))
print(s.to_string(index=False))
