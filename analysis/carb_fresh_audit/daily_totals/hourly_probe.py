"""Predict hourly intake from CGM windows, then aggregate to the daily target."""
from pathlib import Path
import json,pickle,hashlib
import pandas as pd
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
ROOT = str(Path(__file__).resolve().parents[3])  # repo root
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'hourly_probe';OUT.mkdir(exist_ok=True)
daily=pd.read_csv(ROOT/'delayed_probe/sensor_inputs.csv')
ids=pd.read_csv(ROOT/'delayed_probe/final_training_days.csv');train_days=ids.merge(daily,on=['pid','day']);later=daily[daily.split=='later']
days=pd.concat([train_days,later]).drop_duplicates(['pid','day']).reset_index(drop=True)
meals=pd.read_csv(ROOT + '/dataset/cgmacros_clean_v1/meals.csv');meals['t']=pd.to_datetime(meals.timestamp)
(OUT/'PLAN.json').write_text(json.dumps(dict(target='Same44 CGMacros daily carbohydrate totals; no meal entries needed at inference.',method='Train hourly carb targets by summing known calibration meal labels in each clock hour. Inputs are 15min Libre samples from1h before to4h after hour start, baseline-relative samples and hour sine/cosine. Sum24 hourly predictions.',controls='Clock-only intake predictor; personal historical daily mean. No current food count/type/time supplied to model.',selection='Full other-person calibration pool and chronological same-person history,33 earlier validation days. Poisson boosted trees; leaves7/15, min_leaf20,80iterations,regularization1; raw and calibration-offset corrected daily sums.',limits='Hourly absence of a logged meal is treated as zero logged intake, not verified fasting. Adjacent windows overlap; validation separated by whole days and30h purge. Outputs require following-day observations. Same reused development cohort.'),indent=2))
rows=[];hashes={}
for pid,g in days.groupby('pid'):
    f=Path(fROOT + '/dataset/cgmacros_clean_v1/participants/CGMacros-{pid:03}.csv');hashes[str(f)]=hashlib.sha256(f.read_bytes()).hexdigest()
    raw=pd.read_csv(f);raw.columns=raw.columns.str.strip();raw.index=pd.to_datetime(raw.Timestamp)
    for _,day in g.iterrows():
        date=pd.Timestamp(day.day)
        labels=meals[(meals.participant_id==pid)&(meals.t>=date)&(meals.t<date+pd.Timedelta(days=1))]
        assert np.isclose(labels.carbs_g.sum(),day.actual)
        for hour in range(24):
            t=date+pd.Timedelta(hours=hour)
            signal=raw['Libre GL'].reindex(pd.date_range(t-pd.Timedelta(hours=1),periods=21,freq='15min')).to_numpy(float)
            baseline=np.nanmedian(signal[:4]) if np.isfinite(signal[:4]).any() else np.nan
            r=dict(pid=pid,day=day.day,hour=hour,target=float(labels[labels.t.dt.hour==hour].carbs_g.sum()),clock_sin=np.sin(2*np.pi*hour/24),clock_cos=np.cos(2*np.pi*hour/24))
            for i,value in enumerate(signal):r[f'raw_{i}']=value;r[f'relative_{i}']=value-baseline
            r['pre_glucose']=baseline;rows.append(r)
x=pd.DataFrame(rows);x.to_csv(OUT/'hourly_inputs.csv',index=False)
clock=['clock_sin','clock_cos'];cg=[c for c in x if c.startswith(('raw_','relative_'))]+['pre_glucose']
families={'clock':clock,'cgm':cg,'cgm_clock':cg+clock}
def fit(h,family,leaves):
    model=HistGradientBoostingRegressor(loss='poisson',max_iter=80,max_leaf_nodes=leaves,min_samples_leaf=20,l2_regularization=1,early_stopping=False,random_state=20260908)
    model.fit(h[families[family]],h.target);return model
def totals(model,q,family):
    z=q[['pid','day']].copy();z['prediction']=model.predict(q[families[family]]);return z.groupby(['pid','day'],sort=False).prediction.sum()
def scores(y,p):
    e=abs(y-p);return dict(n=len(y),hits=int((e<=.1*y).sum()),mape=float((e/y).mean()*100),mae=float(e.mean()))
splits=[]
for _,r in train_days.iterrows():
    own=train_days[(train_days.pid==r.pid)&(pd.to_datetime(train_days.day)+pd.Timedelta(hours=30)<=pd.Timestamp(r.day))]
    if not len(own):continue
    others=train_days[train_days.pid!=r.pid];h=x.merge(pd.concat([others,own])[['pid','day']],on=['pid','day']);q=x[(x.pid==r.pid)&(x.day==r.day)]
    # Query window includes one preceding hour; prior training windows end by03:00 next day, leaving sufficient separation under30h purge.
    splits.append((h,q,own,float(r.actual)))
assert len(splits)==33
rows=[];cached={}
for family in families:
    for leaves in [7,15]:
        yy=[];pp=[];cc=[]
        for h,q,own,y in splits:
            model=fit(h,family,leaves);p=float(totals(model,q,family).iloc[0]);cal=totals(model,h[h.pid==q.pid.iloc[0]],family).mean();offset=float(own.actual.mean()-cal)
            yy.append(y);pp.append(p);cc.append(max(0,p+offset))
        for correction,pred in [('raw',pp),('offset',cc)]:rows.append(dict(family=family,leaves=leaves,correction=correction,**scores(np.array(yy),np.array(pred))))
        print('validated',family,leaves,flush=True)
rank=pd.DataFrame(rows).sort_values(['mape','mae']);rank.to_csv(OUT/'validation.csv',index=False)
best=rank.iloc[0].to_dict();(OUT/'selected_settings.json').write_text(json.dumps(best,indent=2))
h=x.merge(ids,on=['pid','day']);q=x.merge(later[['pid','day']],on=['pid','day']);family=best['family'];model=fit(h,family,int(best['leaves']))
(OUT/'model.pkl').write_bytes(pickle.dumps(model));p=totals(model,q,family)
if best['correction']=='offset':
    fitmeans=totals(model,h,family).groupby('pid').mean();truthmeans=train_days.groupby('pid').actual.mean();offset=truthmeans-fitmeans
    p=np.maximum(0,p+pd.Series(p.index.get_level_values('pid').map(offset),index=p.index))
else:offset=pd.Series(0.,index=ids.pid.unique())
offset.to_csv(OUT/'calibration_offsets.csv')
r=p.rename('prediction').reset_index();r.to_csv(OUT/'predictions_before_scoring.csv',index=False);r=r.merge(later[['pid','day','actual']],on=['pid','day'],validate='one_to_one');r['ape']=100*abs(r.prediction-r.actual)/r.actual;r.to_csv(OUT/'later_results.csv',index=False)
assert len(r)==44 and np.isfinite(r.prediction).all()
originalpred=model.predict(q[families[family]]);assert np.array_equal(originalpred,pickle.loads((OUT/'model.pkl').read_bytes()).predict(q.assign(target=999999)[families[family]]))
summary=dict(selected=best,later=scores(r.actual.to_numpy(),r.prediction.to_numpy()),baseline=scores(r.actual.to_numpy(),r.pid.map(train_days.groupby('pid').actual.mean()).to_numpy()),training_days=len(train_days),training_hour_bins=len(h),nonzero_training_bins=int((h.target>0).sum()),all44=True,query_label_independence=True,source_unchanged=all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==v for f,v in hashes.items()))
(OUT/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
