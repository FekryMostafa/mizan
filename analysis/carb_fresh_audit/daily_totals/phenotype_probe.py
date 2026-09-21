"""Baseline phenotype interactions with personal glucose deviations."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
ROOT = str(Path(__file__).resolve().parents[3])  # repo root
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'phenotype_probe';OUT.mkdir(exist_ok=True)
d=pd.read_csv(ROOT/'delayed_probe/sensor_inputs.csv');bio=pd.read_csv(ROOT + '/dataset/cgmacros_clean_v1/bio.csv');bio.columns=bio.columns.str.strip()
mapping={'subject':'pid','Age':'bio_age','BMI':'bio_bmi','A1c PDL (Lab)':'bio_a1c','Fasting GLU - PDL (Lab)':'bio_fasting_glucose','Insulin':'bio_insulin','Triglycerides':'bio_triglycerides'}
b=bio[list(mapping)].rename(columns=mapping);b['bio_male']=bio.Gender.map({'M':1.,'F':0.});d=d.merge(b,on='pid',validate='many_to_one')
h=pd.read_csv(ROOT/'delayed_probe/final_training_days.csv').merge(d,on=['pid','day']);q=d[d.split=='later'];cols=[c for c in d if c.startswith('g_') or c.startswith('next_glucose')]
phenos={'none':[],'basic':['bio_age','bio_bmi','bio_male'],'labs':['bio_age','bio_bmi','bio_male','bio_a1c','bio_fasting_glucose','bio_insulin','bio_triglycerides']}
(OUT/'PLAN.json').write_text(json.dumps(dict(target='Same44 later CGMacros daily carbohydrate totals',inputs='Known onboarding age/BMI/gender and optionally baseline lab measurements; interact with personally centered glucose features. No current meal labels.',selection='Same33 full-pool personal chronological validation days; ridge/kernel; .1/1/10/100/1000. Each arm separately selected by MAPE then MAE.',interpretation='Lab arm requires existing baseline blood tests, not CGM-only onboarding. Static phenotype enters interactions so personal centering does not erase it. This is predictive association, not a causal explanation.'),indent=2))
def predict(t,v,arm,kind,reg):
    means=t.groupby('pid').actual.mean();centers=t.groupby('pid')[cols].mean()
    x=np.nan_to_num(t[cols].to_numpy()-centers.loc[t.pid].to_numpy());z=np.nan_to_num(v[cols].to_numpy()-centers.loc[v.pid].to_numpy())
    scale=np.maximum(x.std(0),1.);x/=scale;z/=scale
    if phenos[arm]:
        ph=phenos[arm];distinct=t.drop_duplicates('pid')[ph];mu=distinct.mean().fillna(0).to_numpy();sd=distinct.std(ddof=0).fillna(0).to_numpy();sd=np.maximum(sd,1e-6)
        a=np.nan_to_num((t[ph].to_numpy()-mu)/sd);b=np.nan_to_num((v[ph].to_numpy()-mu)/sd)
        x=np.column_stack([x,(x[:,:,None]*a[:,None,:]).reshape(len(x),-1)])
        z=np.column_stack([z,(z[:,:,None]*b[:,None,:]).reshape(len(z),-1)])
    y=t.actual.to_numpy()-t.pid.map(means).to_numpy()
    if kind=='ridge':p=z@x.T@np.linalg.solve(x@x.T+reg*np.eye(len(x)),y)
    else:
        def k(a,b):return np.exp(-np.maximum((a*a).sum(1)[:,None]+(b*b).sum(1)[None,:]-2*a@b.T,0)/a.shape[1])
        p=k(z,x)@np.linalg.solve(k(x,x)+reg*np.eye(len(x)),y)
    return np.maximum(0,v.pid.map(means).to_numpy()+p)
def score(y,p):
    e=abs(y-p);return dict(n=len(y),hits=int((e<=.1*y).sum()),mape=float((e/y).mean()*100),mae=float(e.mean()))
parts=[]
for i,r in h.iterrows():
    own=h[(h.pid==r.pid)&(pd.to_datetime(h.day)+pd.Timedelta(hours=30)<=pd.Timestamp(r.day))]
    if len(own):parts.append((pd.concat([h[h.pid!=r.pid],own]),h.loc[[i]]))
assert len(parts)==33
rows=[];settings={};result=q[['pid','day']].copy()
for arm in phenos:
    armrows=[]
    for kind in ['ridge','kernel']:
        for reg in [.1,1,10,100,1000]:
            yy=[];pp=[]
            for t,v in parts:yy.extend(v.actual);pp.extend(predict(t,v,arm,kind,reg))
            armrows.append(dict(arm=arm,kind=kind,reg=reg,**score(np.array(yy),np.array(pp))))
    rank=pd.DataFrame(armrows).sort_values(['mape','mae']);best=rank.iloc[0].to_dict();settings[arm]=best;rows.extend(armrows)
    (OUT/f'{arm}_settings.json').write_text(json.dumps(best,indent=2))
    result[arm]=predict(h,q,arm,best['kind'],best['reg'])
    assert np.array_equal(result[arm],predict(h,q.assign(actual=999999),arm,best['kind'],best['reg']))
pd.DataFrame(rows).to_csv(OUT/'validation.csv',index=False);result.to_csv(OUT/'predictions_before_scoring.csv',index=False)
result['actual']=q.actual
for arm in phenos:result[arm+'_ape']=100*abs(result[arm]-result.actual)/result.actual
result.to_csv(OUT/'later_results.csv',index=False)
prev=pd.read_csv(ROOT/'full_pool_validation/later_results.csv');assert np.allclose(prev.prediction,result['none'],rtol=0,atol=1e-8)
summary=dict(settings=settings,scores={arm:score(result.actual.to_numpy(),result[arm].to_numpy()) for arm in phenos},no_query_label_dependence=True,reference_replayed=True,all44=len(result)==44)
(OUT/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
