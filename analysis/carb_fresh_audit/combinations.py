from pathlib import Path
from itertools import combinations
import json, hashlib
import numpy as np
import pandas as pd

B=Path(__file__).resolve().parent;O=B/'combinations';O.mkdir(exist_ok=True)
f=pd.read_csv(B/'libre_features.csv')
cols=list(f.columns[4:]);people=sorted(f.pid.unique())
core=['peak','area_60_120','area_centroid']
groups=[list(c) for n in [1,2,3] for c in combinations(core,n)]+[cols]
candidates=[(g,degree,alpha) for g in groups for degree in [1,2] for alpha in [1.,10.,100.]]
plan={'candidates':48,'features':groups,'degree':[1,2],'ridge_alpha':[1,10,100],
 'selection':'inner leave-one-person-out fraction within 10%, then MAE',
 'outer':'leave-one-person-out; both later meals held out together',
 'calibration':'own first low/high meals available; other-person later meals train population conversion',
 'normalization':'personal midpoint and contrast; contrast magnitude floor 25% of training-person median absolute calibration contrast',
 'output':'continuous grams clipped only at zero; no snapping to recipe doses',
 'scope':'controlled 24/66 g dose repeats, previously inspected development data; no new-dose accuracy claim',
 'reserved_accessed':False}
(O/'PLAN.json').write_text(json.dumps(plan,indent=2))
cal={};qry={};keys={}
for pid in people:
 z=f[f.pid==pid].set_index('role')
 cal[pid]=z.loc[['low_calibration','high_calibration'],cols].to_numpy(float)
 qry[pid]=z.loc[['low_query','high_query'],cols].to_numpy(float)
 keys[pid]=z.loc[['low_query','high_query'],'time'].tolist()
assert all(np.isfinite(v).all() for v in [*cal.values(),*qry.values()])
def data(train,test):
 pool=np.median(np.array([abs(cal[p][1]-cal[p][0])/2 for p in train]),axis=0)
 def one(p):
  d=(cal[p][1]-cal[p][0])/2
  den=np.where(d<0,-1,1)*np.maximum(np.maximum(abs(d),.25*pool),1e-8)
  return (qry[p]-cal[p].mean(axis=0))/den
 return np.vstack([one(p) for p in train]),np.vstack([one(p) for p in test])
def design(a,g,degree):
 z=a[:,[cols.index(v) for v in g]]
 if degree==2:z=np.column_stack([z,*[z[:,i]*z[:,j] for i in range(z.shape[1]) for j in range(i,z.shape[1])]])
 return z
def predict(a,b,g,degree,alpha):
 a=design(a,g,degree);b=design(b,g,degree)
 mean=a.mean(axis=0);scale=a.std(axis=0);scale[scale<1e-8]=1
 a=(a-mean)/scale;b=(b-mean)/scale
 y=np.tile([-1.,1.],len(a)//2)
 # Dual ridge keeps systems small even with quadratic features.
 weights=a.T@np.linalg.solve(a@a.T+alpha*np.eye(len(a)),y)
 return np.maximum(0,45+21*(b@weights))
def score(pred):
 true=np.tile([24.,66.],len(pred)//2);err=abs(pred-true)
 return int((err<=.1*true).sum()),float(err.mean())
out=[];alternatives=[];selection=[]
for held in people:
 train=[p for p in people if p!=held]
 inner=[data([p for p in train if p!=v],[v]) for v in train]
 scores=[]
 for g,degree,alpha in candidates:
  pred=np.concatenate([predict(a,b,g,degree,alpha) for a,b in inner]);hits,mae=score(pred)
  scores.append((-hits,mae))
 best=min(range(len(candidates)),key=lambda i:scores[i])
 a,b=data(train,[held])
 for k,(g,degree,alpha) in enumerate(candidates):
  pred=predict(a,b,g,degree,alpha)
  for j,actual in enumerate([24.,66.]):
   row=dict(pid=int(held),time=keys[held][j],candidate=k,features='+'.join(g),degree=degree,alpha=alpha,
    actual=actual,predicted=float(pred[j]),error_g=float(abs(pred[j]-actual)),within10=bool(abs(pred[j]-actual)<=.1*actual))
   alternatives.append(row)
   if k==best:out.append(row)
 selection.append(dict(pid=int(held),candidate=best,inner_hits=-scores[best][0],inner_mae=scores[best][1]))
p=pd.DataFrame(out);assert len(p)==52 and not p.duplicated(['pid','time']).any()
p.to_csv(O/'predictions.csv',index=False);pd.DataFrame(selection).to_csv(O/'selection.csv',index=False)
q=pd.DataFrame(alternatives);q.to_csv(O/'candidate_predictions.csv',index=False)
q.groupby(['candidate','features','degree','alpha']).agg(hits=('within10','sum'),MAE=('error_g','mean')).reset_index().to_csv(O/'candidate_summary.csv',index=False)
s={'meals':len(p),'people':p.pid.nunique(),'within10':int(p.within10.sum()),'MAE':float(p.error_g.mean()),
 'both_meals_correct':int(p.groupby('pid').within10.all().sum()),'median_absolute_percentage_error':float((p.error_g/p.actual).median()*100)}
(O/'summary.json').write_text(json.dumps(s,indent=2))
(O/'manifest.json').write_text(json.dumps({str(x):hashlib.sha256(x.read_bytes()).hexdigest() for x in [Path(__file__),B/'libre_features.csv',O/'PLAN.json']},indent=2))
print(json.dumps(s,indent=2))
