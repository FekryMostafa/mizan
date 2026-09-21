"""Event-aligned HR/activity, same expanded CGMacros training and daily test."""
from pathlib import Path
import json,pickle
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
ROOT = str(Path(__file__).resolve().parents[3])  # repo root
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'event_activity_probe';OUT.mkdir(exist_ok=True)
# Restore the original in-memory training floats exactly; default CSV parsing
# perturbs tied values enough to change histogram boosting splits.
h=pd.read_csv(ROOT/'expanded_event_probe/training_events.csv',float_precision='round_trip');days=pd.read_csv(ROOT/'delayed_probe/later_results.csv');q=pd.read_csv(ROOT/'exact_event_probe/event_inputs.csv').merge(days[['pid','day']],on=['pid','day']);h['role']='train';q['role']='later';data=pd.concat([h,q],ignore_index=True)
(OUT/'PLAN.json').write_text(json.dumps(dict(target='Same44 daily carbohydrate totals under supplied-meal-time diagnostic',features='20 consecutive15min HR/activity means from−60 to+240min; mean unavailable if <90% observed. Premeal24h means similarly require90% coverage. No missing-to-rest conversion.',arms='glucose+clock reference; plus activity; plus activity+HR; activity+HR+clock without glucose control',models='Same fixed Poisson boosting80iterations,7leaves,min_leaf20,L2=1. No later-label selection or filtering.',limits='All meal times supplied; not passive. Activity calories are tracker estimates, not directly measured glucose disposal. Missingness may encode participant differences.'),indent=2))
extra=[]
for pid,g in data.groupby('pid'):
    raw=pd.read_csv(fROOT + '/dataset/cgmacros_clean_v1/participants/CGMacros-{pid:03}.csv');raw.columns=raw.columns.str.strip();raw.index=pd.to_datetime(raw.Timestamp)
    for idx,r in g.iterrows():
        t=pd.Timestamp(r.timestamp);z=raw.reindex(pd.date_range(t-pd.Timedelta(hours=1),periods=300,freq='min'));before=raw.reindex(pd.date_range(t-pd.Timedelta(hours=24),periods=1440,freq='min'));row={'index':idx}
        for key,col in [('hr','HR'),('activity','Calories (Activity)')]:
            for k in range(20):
                a=pd.to_numeric(z.iloc[15*k:15*(k+1)][col],errors='coerce');row[f'{key}_bin{k}']=a.mean() if a.notna().mean()>=.9 else np.nan
            a=pd.to_numeric(before[col],errors='coerce');row[f'{key}_pre24']=a.mean() if a.notna().mean()>=.9 else np.nan
        extra.append(row)
extra=pd.DataFrame(extra).set_index('index').reindex(data.index);data=pd.concat([data,extra],axis=1);data.to_csv(OUT/'event_inputs.csv',index=False);h=data[data.role=='train'];q=data[data.role=='later']
clock=['clock_sin','clock_cos'];cg=[c for c in data if c.startswith(('raw_','relative_'))]+['pre_glucose'];hr=[c for c in data if c.startswith('hr_')];activity=[c for c in data if c.startswith('activity_')]
families=dict(reference=cg+clock,plus_activity=cg+clock+activity,plus_hr_activity=cg+clock+activity+hr,context_without_glucose=clock+activity+hr)
out=days[['pid','day','actual']].copy();preds=q[['pid','day','timestamp','target']].copy();summary={}
def score(y,p):
    e=abs(y-p);return dict(n=len(y),hits=int((e<=.1*y).sum()),mape=float((e/y).mean()*100),mae=float(e.mean()))
for family,cols in families.items():
    model=HistGradientBoostingRegressor(loss='poisson',max_iter=80,max_leaf_nodes=7,min_samples_leaf=20,l2_regularization=1,early_stopping=False,random_state=20260908).fit(h[cols],h.target)
    p=model.predict(q[cols]);preds[family]=p;z=q[['pid','day']].copy();z['p']=p;s=z.groupby(['pid','day']).p.sum();out[family]=[s.loc[(r.pid,r.day)] for _,r in out.iterrows()];summary[family]=score(out.actual.to_numpy(),out[family].to_numpy())
    f=OUT/f'{family}_model.pkl';f.write_bytes(pickle.dumps(model));assert np.array_equal(p,pickle.loads(f.read_bytes()).predict(q.assign(target=999999)[cols]))
out.to_csv(OUT/'daily_predictions.csv',index=False);preds.to_csv(OUT/'event_predictions.csv',index=False)
previous=pd.read_csv(ROOT/'expanded_event_probe/daily_predictions.csv');assert np.allclose(previous.cgm_clock,out.reference,rtol=0,atol=1e-8)
summary['audit']=dict(training_events=len(h),later_events=len(q),all44=len(out)==44,reference_replayed=True,later_complete_hr_windows=int(q[hr[:-1]].notna().all(axis=1).sum()),later_complete_activity_windows=int(q[activity[:-1]].notna().all(axis=1).sum()),not_passive=True)
(OUT/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2));print(preds[(preds.pid==13)&(preds.timestamp=='2024-02-02T15:41:00')].to_string(index=False))
