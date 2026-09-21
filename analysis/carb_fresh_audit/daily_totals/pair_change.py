"""Learn shared within-person day-to-day differences; no current food inputs."""
from pathlib import Path
import json,pickle
import numpy as np
import pandas as pd
from sklearn.ensemble import ExtraTreesRegressor
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'pair_change';OUT.mkdir(exist_ok=True)
d=pd.read_csv(ROOT/'delayed_probe/sensor_inputs.csv');h=pd.read_csv(ROOT/'delayed_probe/final_training_days.csv').merge(d,on=['pid','day']);q=d[d.split=='later'];fold=pd.read_csv(ROOT/'delayed_probe/folds.csv')
families={'shape':['g_rises','g_sd','g_above_q10','g_above_100','g_night','next_glucose_rises','next_glucose_sd'],
          'glucose':[c for c in d if c.startswith('g_') or c.startswith('next_glucose')],
          'context':[c for c in d if c.startswith(('g_','ctx_','next_'))]}
(OUT/'PLAN.json').write_text(json.dumps(dict(target='Same 44 later daily carbohydrate totals',method='Shared ExtraTrees on within-person sensor differences and carb differences. Symmetric correction, average historical day carb + predicted change. Never give current carb label as input.',selection='Same existing29 chronological validation days, MAPE then MAE; leaf2/5/10; shape/glucose/context; personal mean baseline included.',caveat='Pair rows reuse days and are not independent observations. Earliest validation fold has very few same-person training pairs. Reused development data.'),indent=2))
def fit(t,cols,leaf):
    xx=[];yy=[]
    for _,g in t.groupby('pid'):
        a=g[cols].to_numpy(float);y=g.actual.to_numpy()
        for i in range(len(g)):
            for j in range(i):
                delta=a[i]-a[j]
                delta=np.where(np.isfinite(delta),delta,0)
                xx.extend([delta,-delta]);yy.extend([y[i]-y[j],y[j]-y[i]])
    if not xx:raise ValueError('No training day pairs')
    model=ExtraTreesRegressor(n_estimators=200,min_samples_leaf=leaf,random_state=20260908,n_jobs=1)
    model.fit(np.array(xx),np.array(yy));return dict(model=model,cols=cols,training=t,pair_rows=len(xx))
def predict(m,v):
    out=[]
    for _,r in v.iterrows():
        old=m['training'][m['training'].pid==r.pid]
        assert pd.to_datetime(old.day).max()+pd.Timedelta(hours=30)<=pd.Timestamp(r.day)
        delta=r[m['cols']].to_numpy(float)-old[m['cols']].to_numpy(float)
        delta=np.where(np.isfinite(delta),delta,0)
        correction=(m['model'].predict(delta)-m['model'].predict(-delta))/2
        out.append(max(0,np.mean(old.actual.to_numpy()+correction)))
    return np.array(out)
def score(y,p):
    e=abs(y-p);return dict(n=len(y),hits=int((e<=.1*y).sum()),mape=float((e/y).mean()*100),mae=float(e.mean()))
parts=[]
for _,f in fold.groupby('fold'):
    t=f[f.role=='fit'][['pid','day']].merge(d,on=['pid','day']);v=f[f.role=='validate'][['pid','day']].merge(d,on=['pid','day']);parts.append((t,v))
rows=[]
for name,cols in families.items():
    for leaf in [2,5,10]:
        yy=[];pp=[]
        for t,v in parts:yy.extend(v.actual);pp.extend(predict(fit(t,cols,leaf),v))
        rows.append(dict(family=name,leaf=leaf,**score(np.array(yy),np.array(pp))))
yy=[];pp=[]
for t,v in parts:yy.extend(v.actual);pp.extend(v.pid.map(t.groupby('pid').actual.mean()))
rows.append(dict(family='baseline',leaf=0,**score(np.array(yy),np.array(pp))))
rank=pd.DataFrame(rows).sort_values(['mape','mae']);rank.to_csv(OUT/'validation.csv',index=False)
best=rank.iloc[0].to_dict();(OUT/'settings.json').write_text(json.dumps(best,indent=2))
if best['family']=='baseline':
    model=None;p=q.pid.map(h.groupby('pid').actual.mean()).to_numpy()
else:
    model=fit(h,families[best['family']],int(best['leaf']));p=predict(model,q)
(OUT/'model.pkl').write_bytes(pickle.dumps(model))
r=q[['pid','day']].copy();r['prediction']=p;r.to_csv(OUT/'predictions_before_scoring.csv',index=False)
r['actual']=q.actual;r['ape']=100*abs(r.actual-r.prediction)/r.actual;r.to_csv(OUT/'later_results.csv',index=False)
if model is not None:assert np.array_equal(p,predict(pickle.loads((OUT/'model.pkl').read_bytes()),q.assign(actual=999999)))
s=dict(setting=best,later=score(q.actual.to_numpy(),p),baseline=score(q.actual.to_numpy(),q.pid.map(h.groupby('pid').actual.mean()).to_numpy()),training_days=len(h),training_pair_rows=model['pair_rows'] if model else None,all44=len(r)==44)
(OUT/'summary.json').write_text(json.dumps(s,indent=2));print(json.dumps(s,indent=2))
