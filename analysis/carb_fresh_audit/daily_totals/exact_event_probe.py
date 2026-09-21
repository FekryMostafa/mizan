"""Exact recorded meal-time diagnostic, summed to fixed daily outcomes."""
from pathlib import Path
import json,pickle
import pandas as pd
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
ROOT = str(Path(__file__).resolve().parents[3])  # repo root
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'exact_event_probe';OUT.mkdir(exist_ok=True)
daily=pd.read_csv(ROOT/'delayed_probe/sensor_inputs.csv');ids=pd.read_csv(ROOT/'delayed_probe/final_training_days.csv');later=daily[daily.split=='later'];days=pd.concat([ids,later[['pid','day']]]).drop_duplicates()
m=pd.read_csv(ROOT + '/dataset/cgmacros_clean_v1/meals.csv');m['day']=pd.to_datetime(m.timestamp).dt.strftime('%Y-%m-%d');m=m.rename(columns={'participant_id':'pid'}).merge(days,on=['pid','day']);rows=[]
(OUT/'PLAN.json').write_text(json.dumps(dict(target='Diagnostic for exact meal timing, still summed to same44 daily carb totals',events='All recorded meal timestamps; merge only identical participant/timestamp. Keep overlapping responses and zero-carb events.',inputs='Libre sampled -60..+240min around exact recorded meal time, raw and baseline-relative; clock-only/cgm-only/cgm+clock controls. No meal type, current macro amounts or food identity inputs.',models='Same fixed Poisson boosting80iterations,7leaves,min_leaf20,L2=1 as hourly diagnostic; no later-label tuning.',limits='Recorded meal times and event counts supplied at evaluation: not passive accuracy. Exact published timestamp not verified true ingestion onset. More events than hourly bins alters segmentation as well as alignment.'),indent=2))
for pid,g in m.groupby('pid'):
    raw=pd.read_csv(fROOT + '/dataset/cgmacros_clean_v1/participants/CGMacros-{pid:03}.csv');raw.columns=raw.columns.str.strip();raw.index=pd.to_datetime(raw.Timestamp)
    for timestamp,meal in g.groupby('timestamp'):
        t=pd.Timestamp(timestamp);signal=raw['Libre GL'].reindex(pd.date_range(t-pd.Timedelta(hours=1),periods=21,freq='15min')).to_numpy(float);baseline=np.nanmedian(signal[:4]) if np.isfinite(signal[:4]).any() else np.nan;hour=t.hour+t.minute/60
        r=dict(pid=pid,day=str(t.date()),timestamp=timestamp,target=float(meal.carbs_g.sum()),clock_sin=np.sin(2*np.pi*hour/24),clock_cos=np.cos(2*np.pi*hour/24),pre_glucose=baseline,coverage=float(np.isfinite(signal).mean()))
        for k,v in enumerate(signal):r[f'raw_{k}']=v;r[f'relative_{k}']=v-baseline
        rows.append(r)
x=pd.DataFrame(rows);x.to_csv(OUT/'event_inputs.csv',index=False);h=x.merge(ids,on=['pid','day']);q=x.merge(later[['pid','day']],on=['pid','day'])
truth=x.groupby(['pid','day']).target.sum();reference=daily.merge(days,on=['pid','day'])
assert all(np.isclose(truth.loc[(r.pid,r.day)],r.actual) for _,r in reference.iterrows())
clock=['clock_sin','clock_cos'];cgm=[c for c in x if c.startswith(('raw_','relative_'))]+['pre_glucose'];families=dict(clock=clock,cgm=cgm,cgm_clock=cgm+clock)
result=later[['pid','day','actual']].copy();summary={};events=q[['pid','day','timestamp','target']].copy()
def score(y,p):
    e=abs(y-p);return dict(n=len(y),hits=int((e<=.1*y).sum()),mape=float((e/y).mean()*100),mae=float(e.mean()))
for family,cols in families.items():
    model=HistGradientBoostingRegressor(loss='poisson',max_iter=80,max_leaf_nodes=7,min_samples_leaf=20,l2_regularization=1,early_stopping=False,random_state=20260908).fit(h[cols],h.target)
    p=model.predict(q[cols]);events[family]=p;z=q[['pid','day']].copy();z['pred']=p;s=z.groupby(['pid','day']).pred.sum();result[family]=[s.loc[(r.pid,r.day)] for _,r in result.iterrows()]
    (OUT/f'{family}_model.pkl').write_bytes(pickle.dumps(model));assert np.array_equal(p,model.predict(q.assign(target=999999)[cols]));summary[family]=score(result.actual.to_numpy(),result[family].to_numpy())
result.to_csv(OUT/'daily_predictions.csv',index=False);events.to_csv(OUT/'event_predictions.csv',index=False)
summary['counts']=dict(training_days=len(ids),training_events=len(h),later_days=len(result),later_events=len(q),incomplete_later_windows=int((q.coverage<1).sum()),all44=len(result)==44);summary['not_passive']=True
(OUT/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
