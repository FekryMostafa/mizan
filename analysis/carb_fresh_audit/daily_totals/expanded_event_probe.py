"""Expand labeled meals within CGMacros, preserving daily evaluation."""
from pathlib import Path
import json,pickle,hashlib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
ROOT = str(Path(__file__).resolve().parents[3])  # repo root
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'expanded_event_probe';OUT.mkdir(exist_ok=True)
m=pd.read_csv(ROOT/'p13_event_audit/expanded_training_candidates.csv');later=pd.read_csv(ROOT/'delayed_probe/later_results.csv');cut=later.groupby('pid').day.min().map(pd.Timestamp).to_dict()
(OUT/'PLAN.json').write_text(json.dumps(dict(target='Same44 daily carbohydrate totals; known meal-time diagnostic',expansion='Valid full-consumption individual meals from other days/people in sameCGMacros. Each evaluation participant: training four-hour postmeal window ends before earliest later midnight minus1h. Others have no evaluation days.',quality='Require all301 published minute values from−60 through+240min finite; keep device bounds flagged and overlaps. No new interpolation.',models='Fixed exact-event Poisson boosting80iterations,7leaves,min_leaf20,L2=1; clock/cgm/cgm+clock. No tuning on later labels. Compare prior267-event results.',limits='Known event times supplied; not passive. More individual meals do not establish complete daily intake. Additional participants are training-only.'),indent=2))
rows=[];audit=[];hashes={}
for pid,g in m.groupby('participant_id'):
    f=Path(fROOT + '/dataset/cgmacros_clean_v1/participants/CGMacros-{pid:03}.csv');hashes[str(f)]=hashlib.sha256(f.read_bytes()).hexdigest()
    raw=pd.read_csv(f);raw.columns=raw.columns.str.strip();raw.index=pd.to_datetime(raw.Timestamp)
    for timestamp,events in g.groupby('timestamp'):
        t=pd.Timestamp(timestamp);reasons=[]
        if pid in cut and t+pd.Timedelta(hours=4)>=cut[pid]-pd.Timedelta(hours=1):reasons.append('evaluation_window_proximity')
        grid=raw['Libre GL'].reindex(pd.date_range(t-pd.Timedelta(hours=1),periods=301,freq='min')).to_numpy(float)
        if not np.isfinite(grid).all():reasons.append('incomplete_sensor_window')
        audit.append(dict(pid=pid,timestamp=timestamp,carbs=float(events.carbs_g.sum()),included=not reasons,reasons=';'.join(reasons)))
        if reasons:continue
        signal=grid[::15];baseline=np.median(signal[:4]);hour=t.hour+t.minute/60
        r=dict(pid=pid,day=str(t.date()),timestamp=timestamp,target=float(events.carbs_g.sum()),clock_sin=np.sin(2*np.pi*hour/24),clock_cos=np.cos(2*np.pi*hour/24),pre_glucose=baseline)
        for k,v in enumerate(signal):r[f'raw_{k}']=v;r[f'relative_{k}']=v-baseline
        rows.append(r)
h=pd.DataFrame(rows);h.to_csv(OUT/'training_events.csv',index=False);pd.DataFrame(audit).to_csv(OUT/'candidate_audit.csv',index=False)
q=pd.read_csv(ROOT/'exact_event_probe/event_inputs.csv').merge(later[['pid','day']],on=['pid','day'],validate='many_to_one')
clock=['clock_sin','clock_cos'];cgm=[c for c in h if c.startswith(('raw_','relative_'))]+['pre_glucose'];families=dict(clock=clock,cgm=cgm,cgm_clock=cgm+clock)
assert set(zip(h.pid,h.timestamp)).isdisjoint(set(zip(q.pid,q.timestamp)))
out=later[['pid','day','actual']].copy();events=q[['pid','day','timestamp','target']].copy();summary={}
def score(y,p):
    e=abs(y-p);return dict(n=len(y),hits=int((e<=.1*y).sum()),mape=float((e/y).mean()*100),mae=float(e.mean()))
for family,cols in families.items():
    model=HistGradientBoostingRegressor(loss='poisson',max_iter=80,max_leaf_nodes=7,min_samples_leaf=20,l2_regularization=1,early_stopping=False,random_state=20260908).fit(h[cols],h.target)
    p=model.predict(q[cols]);events[family]=p;z=q[['pid','day']].copy();z['pred']=p;s=z.groupby(['pid','day']).pred.sum();out[family]=[s.loc[(r.pid,r.day)] for _,r in out.iterrows()];summary[family]=score(out.actual.to_numpy(),out[family].to_numpy())
    f=OUT/f'{family}_model.pkl';f.write_bytes(pickle.dumps(model));assert np.array_equal(p,pickle.loads(f.read_bytes()).predict(q.assign(target=999999)[cols]))
out.to_csv(OUT/'daily_predictions.csv',index=False);events.to_csv(OUT/'event_predictions.csv',index=False)
summary['audit']=dict(candidate_events=len(audit),training_events=len(h),training_people=int(h.pid.nunique()),training_meals_at_least120=int((h.target>=120).sum()),later_events=len(q),later_days=len(out),all44=len(out)==44,training_test_event_disjoint=True,source_hashes_unchanged=all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==v for f,v in hashes.items()),not_passive=True)
(OUT/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2));print(events[(events.pid==13)&(events.timestamp=='2024-02-02T15:41:00')].to_string(index=False))
