"""Shared nonlinear residuals with small personal calibration, fixed daily split."""
from pathlib import Path
import json, pickle, hashlib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, ExtraTreesRegressor

ROOT=Path(__file__).resolve().parent; OUT=ROOT/'shared_daily';OUT.mkdir(exist_ok=True)
source=ROOT/'delayed_probe/sensor_inputs.csv'
source_hash=hashlib.sha256(source.read_bytes()).hexdigest()
d=pd.read_csv(source)
train=pd.read_csv(ROOT/'delayed_probe/final_training_days.csv').merge(d,on=['pid','day'])
later=d[d.split=='later'].copy()
folds=pd.read_csv(ROOT/'delayed_probe/folds.csv')
families={'glucose':[c for c in d if c.startswith('g_') or c.startswith('next_glucose')],
          'context':[c for c in d if c.startswith(('g_','ctx_','next_'))]}
(OUT/'PLAN.json').write_text(json.dumps(dict(target='Same 44 later calendar-day carbohydrate totals with next-morning sensors',
 training='Same 64 earlier days; shared forest predicts deviation from personal mean daily carbs; input includes absolute and personally centered sensors and mean calibration carbs.',
 selection='29 existing purged earlier chronological validation days; minimize MAPE then MAE; baseline is a candidate.',
 grid='RandomForest/ExtraTrees, 100 trees, leaves 2/5/10, depth 3/unlimited, glucose/context. Fixed seed 20260908.',
 limitations='Repeated development cohort, not fresh prospective data. Known personal calibration labels allowed; query food labels forbidden.'),indent=2))

def prepare(h,q,cols,prep=None):
    if prep is None:
        centers=h.groupby('pid')[cols].mean()
        means=h.groupby('pid').actual.mean()
        vals=h[cols].to_numpy(float)
        counts=np.isfinite(vals).sum(0)
        med=np.divide(np.nansum(vals,0),counts,out=np.zeros(len(cols)),where=counts>0)
        prep=dict(cols=cols,centers=centers,means=means,impute=med)
    a=q[cols].to_numpy(float)
    delta=a-prep['centers'].loc[q.pid].to_numpy()
    a=np.where(np.isfinite(a),a,prep['impute'])
    x=np.column_stack([a,np.nan_to_num(delta),q.pid.map(prep['means']).to_numpy()])
    return x,prep

def fit(h,setting):
    if setting['kind']=='baseline':return dict(means=h.groupby('pid').actual.mean())
    cols=families[setting['family']]
    x,prep=prepare(h,h,cols)
    y=h.actual.to_numpy()-h.pid.map(prep['means']).to_numpy()
    cls=RandomForestRegressor if setting['kind']=='forest' else ExtraTreesRegressor
    model=cls(n_estimators=100,min_samples_leaf=setting['leaf'],max_depth=setting['depth'],random_state=20260908,n_jobs=1)
    model.fit(x,y)
    return dict(prep=prep,model=model)

def predict(model,q):
    if 'means' in model:return q.pid.map(model['means']).to_numpy()
    x,_=prepare(None,q,model['prep']['cols'],model['prep'])
    return np.maximum(0,q.pid.map(model['prep']['means']).to_numpy()+model['model'].predict(x))

def score(y,p):
    err=np.abs(y-p)
    return dict(n=len(y),hits=int((err<=.1*y).sum()),mape=float(np.mean(err/y)*100),mae=float(err.mean()))

settings=[dict(kind='baseline',family='baseline',leaf=0,depth=None)]
settings += [dict(kind=k,family=f,leaf=l,depth=z) for k in ['forest','extra'] for f in families for l in [2,5,10] for z in [3,None]]
parts=[]
for fold,f in folds.groupby('fold'):
    h=f[f.role=='fit'][['pid','day']].merge(d,on=['pid','day'])
    q=f[f.role=='validate'][['pid','day']].merge(d,on=['pid','day'])
    for pid,g in q.groupby('pid'):
        assert pd.to_datetime(h[h.pid==pid].day).max()+pd.Timedelta(hours=30)<=pd.to_datetime(g.day).min()
    parts.append((h,q))
rows=[]
for i,s in enumerate(settings):
    yy=[];pp=[]
    for h,q in parts:
        pp.extend(predict(fit(h,s),q));yy.extend(q.actual)
    rows.append(dict(candidate=i,**s,**score(np.array(yy),np.array(pp))))
rank=pd.DataFrame(rows).sort_values(['mape','mae'],kind='stable')
rank.to_csv(OUT/'validation_candidates.csv',index=False)
chosen=int(rank.iloc[0].candidate);setting=settings[chosen]
(OUT/'selected_settings.json').write_text(json.dumps(setting,indent=2))
model=fit(train,setting)
(OUT/'model.pkl').write_bytes(pickle.dumps(model))
pred=predict(model,later)
result=later[['pid','day']].copy();result['prediction']=pred
result.to_csv(OUT/'predictions_before_scoring.csv',index=False)
result['actual']=later.actual;result['ape']=100*abs(result.prediction-result.actual)/result.actual
result.to_csv(OUT/'later_results.csv',index=False)
saved=pickle.loads((OUT/'model.pkl').read_bytes())
assert np.array_equal(pred,predict(saved,later.assign(actual=999999)))
assert source_hash==hashlib.sha256(source.read_bytes()).hexdigest()
summary=dict(setting=setting,validation=json.loads(rank.iloc[0].to_json()),training=score(train.actual.to_numpy(),predict(model,train)),later=score(later.actual.to_numpy(),pred),baseline=score(later.actual.to_numpy(),predict(fit(train,settings[0]),later)),verified_model_replay_and_no_query_labels=True,source_unchanged=True)
(OUT/'summary.json').write_text(json.dumps(summary,indent=2))
print(json.dumps(summary,indent=2))
if 'model' in model:
    cols=model['prep']['cols'];names=cols+['personal_deviation_'+c for c in cols]+['personal_mean_carbs']
    pd.DataFrame(dict(feature=names,importance=model['model'].feature_importances_)).sort_values('importance',ascending=False).to_csv(OUT/'training_importance.csv',index=False)
