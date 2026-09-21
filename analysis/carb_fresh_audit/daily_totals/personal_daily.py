"""Personal nonlinear calibration fit with chronological evaluation."""
from pathlib import Path
import json
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'personal_daily';OUT.mkdir(exist_ok=True)
d=pd.read_csv(ROOT/'delayed_probe/sensor_inputs.csv')
train=pd.read_csv(ROOT/'delayed_probe/final_training_days.csv').merge(d,on=['pid','day'],validate='one_to_one')
later=d[d.split=='later'].copy()
folds=pd.read_csv(ROOT/'delayed_probe/folds.csv')
families={
 'summary':[c for c in d if c.startswith('g_') or c.startswith('next_glucose')],
 'sequence':[c for c in d if c.startswith(('seq_','nextseq_'))],
 'context':[c for c in d if c.startswith(('g_','ctx_','next_'))]}
(OUT/'PLAN.json').write_text(json.dumps(dict(target='Same 44 later daily carbohydrate totals with next-morning CGM',
    fit='Independent Gaussian kernel interpolation per person, ridge 1e-8; family summary/sequence/context; gamma .01,.1,1,10',
    select='Minimum MAPE then MAE on existing 29 chronological earlier validation days; never select on later answers',
    checks='Training-fit tolerance, later outcomes, saved-model replay, label-independence, pairwise earlier trace/dose comparisons',
    limitations='Very few calibration days per person; interpolation success is a debugging checkpoint. Reused development cohort.'),indent=2))

def kernel(a,b,gamma):
    dist=np.maximum((a*a).sum(1)[:,None]+(b*b).sum(1)[None,:]-2*a@b.T,0)/a.shape[1]
    return np.exp(-gamma*dist)

def fit_person(h,cols,gamma):
    a=h[cols].to_numpy(float)
    count=np.isfinite(a).sum(0)
    center=np.divide(np.nansum(a,axis=0),count,out=np.zeros(a.shape[1]),where=count>0)
    x=np.nan_to_num(a-center)
    scale=np.maximum(x.std(0),1.)
    x=x/scale;y=h.actual.to_numpy();mean=float(y.mean())
    coef=np.linalg.solve(kernel(x,x,gamma)+1e-8*np.eye(len(x)),y-mean)
    return dict(cols=cols,center=center.tolist(),scale=scale.tolist(),x=x.tolist(),coef=coef.tolist(),mean=mean,gamma=gamma)

def apply_model(model,q):
    z=np.nan_to_num(q[model['cols']].to_numpy(float)-model['center'])/model['scale']
    return np.maximum(0,model['mean']+kernel(z,np.array(model['x']),model['gamma'])@model['coef'])

def predict(h,q,family,gamma,chronological=True):
    p=pd.Series(index=q.index,dtype=float);models={}
    for pid,g in q.groupby('pid'):
        hist=h[h.pid==pid]
        assert len(hist)>0
        if chronological: assert pd.to_datetime(hist.day).max()+pd.Timedelta(hours=30)<=pd.to_datetime(g.day).min()
        model=fit_person(hist,families[family],gamma)
        p.loc[g.index]=apply_model(model,g);models[str(pid)]=model
    return p.to_numpy(),models

def score(y,p):
    e=abs(y-p)
    return dict(n=len(y),hits=int((e<=.1*y).sum()),mape=float(np.mean(e/y)*100),mae=float(e.mean()),max_ape=float(np.max(e/y)*100))

candidates=[]
for family in families:
    for gamma in [.01,.1,1.,10.]:
        yy=[];pp=[]
        for _,f in folds.groupby('fold'):
            h=f[f.role=='fit'][['pid','day']].merge(d,on=['pid','day'])
            q=f[f.role=='validate'][['pid','day']].merge(d,on=['pid','day'])
            p,_=predict(h,q,family,gamma);yy.extend(q.actual);pp.extend(p)
        candidates.append(dict(family=family,gamma=gamma,**score(np.array(yy),np.array(pp))))
rank=pd.DataFrame(candidates).sort_values(['mape','mae'],kind='stable')
rank.to_csv(OUT/'validation_candidates.csv',index=False)
best=rank.iloc[0].to_dict();(OUT/'selected_settings.json').write_text(json.dumps(best,indent=2))
pred,models=predict(train,later,best['family'],best['gamma'])
(OUT/'models.json').write_text(json.dumps(models))
r=later[['pid','day']].copy();r['prediction']=pred;r.to_csv(OUT/'predictions_before_scoring.csv',index=False)
fit,_=predict(train,train,best['family'],best['gamma'],False)
tr=train[['pid','day','actual']].copy();tr['prediction']=fit;tr.to_csv(OUT/'training_fit.csv',index=False)
r['actual']=later.actual;r['ape']=100*abs(r.prediction-r.actual)/r.actual
r.to_csv(OUT/'later_results.csv',index=False)
# Earlier pair structure, no evaluation labels used.
pairs=[]
for pid,h in train.groupby('pid'):
    for i in range(len(h)):
        for j in range(i+1,len(h)):
            a,b=h.iloc[i],h.iloc[j]
            x=a[families['sequence']].to_numpy(float);z=b[families['sequence']].to_numpy(float)
            ok=np.isfinite(x)&np.isfinite(z)
            pairs.append(dict(pid=int(pid),day1=a.day,day2=b.day,carbs1=a.actual,carbs2=b.actual,
                carb_difference=abs(a.actual-b.actual),trace_rmse=float(np.sqrt(np.mean((x[ok]-z[ok])**2))),paired_points=int(ok.sum())))
pd.DataFrame(pairs).to_csv(OUT/'earlier_pairs.csv',index=False)
reloaded=json.loads((OUT/'models.json').read_text());replay=pd.Series(index=later.index,dtype=float)
for pid,g in later.groupby('pid'): replay.loc[g.index]=apply_model(reloaded[str(pid)],g.assign(actual=999999))
assert np.allclose(replay.to_numpy(),pred,rtol=0,atol=1e-8)
summary=dict(selected=best,training=score(train.actual.to_numpy(),fit),later=score(later.actual.to_numpy(),pred),
    calibration_days_per_person=train.groupby('pid').size().to_dict(),saved_model_replay_and_query_label_independence=True)
(OUT/'summary.json').write_text(json.dumps(summary,indent=2))
print(json.dumps(summary,indent=2))
print(pd.DataFrame(pairs).sort_values('trace_rmse').head(8).to_string(index=False))
