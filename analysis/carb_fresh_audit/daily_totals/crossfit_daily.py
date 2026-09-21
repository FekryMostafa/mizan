"""Shared sensor-only forests plus honest out-of-bag calibration offsets."""
from pathlib import Path
import json,pickle,hashlib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor,ExtraTreesRegressor

ROOT=Path(__file__).resolve().parent;OUT=ROOT/'crossfit_daily';OUT.mkdir(exist_ok=True)
src=ROOT/'delayed_probe/sensor_inputs.csv';digest=hashlib.sha256(src.read_bytes()).hexdigest()
d=pd.read_csv(src)
train=pd.read_csv(ROOT/'delayed_probe/final_training_days.csv').merge(d,on=['pid','day'])
later=d[d.split=='later'];folds=pd.read_csv(ROOT/'delayed_probe/folds.csv')
families={'glucose':[c for c in d if c.startswith('g_') or c.startswith('next_glucose')],
          'context':[c for c in d if c.startswith(('g_','ctx_','next_'))]}
(OUT/'PLAN.json').write_text(json.dumps(dict(target='Same 44 later daily carb totals with next-morning sensor availability',
    training='64 earlier days, sensor-only shared forest. No carbohydrate mean in model input. Personal additive offset is mean known-label minus out-of-bag prediction.',
    selection='Same purged 29 earlier validation days, minimum MAPE then MAE. RandomForest/ExtraTrees, glucose/context, leaf2/5, offset multiplier 0/.5/1; 200 bootstrap trees, fixed seed.',
    controls='Personal intake mean baseline; verify every OOB prediction has voters excluding that row; mutate a training answer and verify its own OOB prediction is unchanged.',
    limitations='OOB is calibration cross-fitting, not chronological evaluation. Later evaluation is chronological. Reused development cohort, not prospective proof.'),indent=2))

def inputs(h,q,cols,prep=None):
    if prep is None:
        a=h[cols].to_numpy(float);n=np.isfinite(a).sum(0)
        impute=np.divide(np.nansum(a,0),n,out=np.zeros(len(cols)),where=n>0)
        prep=dict(cols=cols,impute=impute,centers=h.groupby('pid')[cols].mean())
    a=q[cols].to_numpy(float);delta=a-prep['centers'].loc[q.pid].to_numpy()
    return np.column_stack([np.where(np.isfinite(a),a,prep['impute']),np.nan_to_num(delta)]),prep

def fit(h,s):
    x,prep=inputs(h,h,families[s['family']])
    cls=RandomForestRegressor if s['kind']=='forest' else ExtraTreesRegressor
    model=cls(n_estimators=200,bootstrap=True,oob_score=True,min_samples_leaf=s['leaf'],random_state=20260908,n_jobs=1)
    model.fit(x,h.actual.to_numpy())
    votes=np.zeros(len(h),int)
    for sampled in model.estimators_samples_:
        mask=np.ones(len(h),bool);mask[np.unique(sampled)]=False;votes+=mask
    assert votes.min()>0
    residual=h.actual.to_numpy()-model.oob_prediction_
    offsets=pd.Series(residual,index=h.pid).groupby(level=0).mean()
    return dict(model=model,prep=prep,offsets=offsets,oob_votes=votes)

def predict(model,q,weight):
    x,_=inputs(None,q,model['prep']['cols'],model['prep'])
    return np.maximum(0,model['model'].predict(x)+weight*q.pid.map(model['offsets']).to_numpy())

def score(y,p):
    e=abs(y-p)
    return dict(n=len(y),hits=int((e<=.1*y).sum()),mape=float(np.mean(e/y)*100),mae=float(e.mean()))

parts=[]
for _,f in folds.groupby('fold'):
    h=f[f.role=='fit'][['pid','day']].merge(d,on=['pid','day']);q=f[f.role=='validate'][['pid','day']].merge(d,on=['pid','day'])
    for pid,g in q.groupby('pid'):
        assert pd.to_datetime(h[h.pid==pid].day).max()+pd.Timedelta(hours=30)<=pd.to_datetime(g.day).min()
    parts.append((h,q))
rows=[];settings=[]
for family in families:
    for kind in ['forest','extra']:
        for leaf in [2,5]:
            s=dict(family=family,kind=kind,leaf=leaf);models=[fit(h,s) for h,q in parts]
            for weight in [0.,.5,1.]:
                setting=dict(**s,weight=weight);yy=[];pp=[]
                for model,(h,q) in zip(models,parts):
                    yy.extend(q.actual);pp.extend(predict(model,q,weight))
                rows.append(dict(candidate=len(settings),**setting,**score(np.array(yy),np.array(pp))));settings.append(setting)
yy=[];pp=[]
for h,q in parts: yy.extend(q.actual);pp.extend(q.pid.map(h.groupby('pid').actual.mean()))
rows.append(dict(candidate=len(settings),family='baseline',kind='baseline',leaf=0,weight=0,**score(np.array(yy),np.array(pp))))
settings.append(dict(kind='baseline'))
rank=pd.DataFrame(rows).sort_values(['mape','mae'],kind='stable');rank.to_csv(OUT/'validation_candidates.csv',index=False)
s=settings[int(rank.iloc[0].candidate)];(OUT/'selected_settings.json').write_text(json.dumps(s,indent=2))
if s['kind']=='baseline':
    model=dict(baseline=train.groupby('pid').actual.mean());pred=later.pid.map(model['baseline']).to_numpy()
else:
    model=fit(train,s);pred=predict(model,later,s['weight'])
    pd.DataFrame(dict(pid=train.pid,day=train.day,actual=train.actual,oob_prediction=model['model'].oob_prediction_,oob_voters=model['oob_votes'])).to_csv(OUT/'calibration_oob.csv',index=False)
(OUT/'model.pkl').write_bytes(pickle.dumps(model))
r=later[['pid','day']].copy();r['prediction']=pred;r.to_csv(OUT/'predictions_before_scoring.csv',index=False)
r['actual']=later.actual;r['ape']=100*abs(r.actual-r.prediction)/r.actual;r.to_csv(OUT/'later_results.csv',index=False)
reloaded=pickle.loads((OUT/'model.pkl').read_bytes());changed=later.assign(actual=999999)
replay=changed.pid.map(reloaded['baseline']).to_numpy() if s['kind']=='baseline' else predict(reloaded,changed,s['weight'])
assert np.array_equal(replay,pred)
check=s if s['kind']!='baseline' else dict(family='context',kind='extra',leaf=2)
original=model if s['kind']!='baseline' else fit(train,check)
mutated=train.copy();mutated.loc[mutated.index[0],'actual']+=10000
probe=fit(mutated,check)
assert abs(original['model'].oob_prediction_[0]-probe['model'].oob_prediction_[0])<1e-8
summary=dict(setting=s,validation=json.loads(rank.iloc[0].to_json()),later=score(later.actual.to_numpy(),pred),baseline=score(later.actual.to_numpy(),later.pid.map(train.groupby('pid').actual.mean()).to_numpy()),
    own_training_label_cannot_change_own_oob_prediction=True,minimum_oob_voters=int(original['oob_votes'].min()),query_labels_do_not_change_predictions=True,all_44_days_retained=len(r)==44,source_unchanged=hashlib.sha256(src.read_bytes()).hexdigest()==digest)
assert summary['all_44_days_retained'] and summary['source_unchanged']
(OUT/'summary.json').write_text(json.dumps(summary,indent=2,allow_nan=False));print(json.dumps(summary,indent=2))
