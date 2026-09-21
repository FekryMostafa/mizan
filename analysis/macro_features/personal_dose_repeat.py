"""Direct within-person dose contrast repeatability, one macro at a time."""
from pathlib import Path
import json
import hashlib
import numpy as np
import pandas as pd

B = Path(__file__).resolve().parent
O = B / 'personal_dose_repeat'
O.mkdir(exist_ok=True)
specs = {
    'Carbs': dict(low=[24,22,10.5], high=[66,22,10.5], feature='peak_height'),
    'Protein': dict(low=[66,22,10.5], high=[66,66,10.5], feature='response_std'),
    'Fat': dict(low=[66,22,10.5], high=[66,22,42], feature='rise_max'),
}
plan = dict(specs=specs, matching='Exact recorded other macros, fiber zero, breakfast, amount consumed 100.',
    calibration='First available low and high dose; both responses finish before either query.',
    query='First later low and first later high dose; no repeated reuse within a macro/person.',
    conversion='Two-point affine inverse, clip only at zero. Zero feature contrast means abstention, counted as failure.',
    selection='Feature choices fixed from preceding audit. No test-driven feature or sign selection.',
    limitation='Exploratory repeated controlled recipes; not unseen-portion or arbitrary-meal validation.',
    reserved_accessed=False)
(O/'PLAN.json').write_text(json.dumps(plan,indent=2))
f = pd.read_csv(B/'features.csv')
f = f[f.dataset.eq('CGMacros')].copy()
e = pd.read_csv(B.parent/'cgm_fat_audit/full_audit/events_and_features.csv')
for z in [f,e]: z['time'] = pd.to_datetime(z.time,format='mixed')
f = f.merge(e[['pid','time','Fiber','meal_type','Amount Consumed']],on=['pid','time'],validate='one_to_one')
f = f[f.Fiber.eq(0) & f.meal_type.eq('breakfast') & f['Amount Consumed'].eq(100)]
macros = ['Carbs','Protein','Fat']
rows, contrasts, availability = [], [], []
for macro,spec in specs.items():
    k = macros.index(macro)
    lo,hi = spec['low'][k],spec['high'][k]
    feature = spec['feature']
    for pid,z in f.groupby('pid'):
        low = z[np.isclose(z[macros],spec['low'],atol=1e-8,rtol=0).all(axis=1)].sort_values('time')
        high = z[np.isclose(z[macros],spec['high'],atol=1e-8,rtol=0).all(axis=1)].sort_values('time')
        availability.append(dict(macro=macro,pid=int(pid),low_records=len(low),high_records=len(high)))
        if len(low)<2 or len(high)<2: continue
        a,b = low.iloc[0],high.iloc[0]
        end = max(a.time.value,b.time.value) + 180*60*10**9
        ql = low[low.time.astype('int64')>end]
        qh = high[high.time.astype('int64')>end]
        if ql.empty or qh.empty: continue
        ql,qh = ql.iloc[0],qh.iloc[0]
        delta = b[feature]-a[feature]
        later_delta = qh[feature]-ql[feature]
        usable = abs(delta)>1e-9
        contrasts.append(dict(macro=macro,pid=int(pid),feature=feature,calibration_delta=delta,
            later_delta=later_delta,sign_repeats=bool(delta*later_delta>0),usable=usable,
            low_calibration_time=a.time.isoformat(),high_calibration_time=b.time.isoformat(),
            low_query_time=ql.time.isoformat(),high_query_time=qh.time.isoformat()))
        for q in [ql,qh]:
            pred = float(max(0,lo+(q[feature]-a[feature])*(hi-lo)/delta)) if usable else np.nan
            actual = float(q[macro])
            midpoint = (lo+hi)/2
            rows.append(dict(macro=macro,pid=int(pid),time=q.time.isoformat(),feature=feature,
                actual=actual,predicted=pred,feature_value=float(q[feature]),
                calibration_low_feature=float(a[feature]),calibration_high_feature=float(b[feature]),
                within10=bool(usable and abs(pred-actual)<=.1*actual+1e-9),
                midpoint_prediction=midpoint,midpoint_error=abs(midpoint-actual),
                midpoint_within10=bool(abs(midpoint-actual)<=.1*actual+1e-9)))
r = pd.DataFrame(rows); c = pd.DataFrame(contrasts)
assert not r.duplicated(['macro','pid','time']).any()
r.to_csv(O/'predictions.csv',index=False)
c.to_csv(O/'contrasts.csv',index=False)
pd.DataFrame(availability).to_csv(O/'availability.csv',index=False)
summary=[]
for macro,z in r.groupby('macro'):
    cc=c[c.macro.eq(macro)]
    error=abs(z.predicted-z.actual)
    summary.append(dict(macro=macro,people=z.pid.nunique(),meals=len(z),hits=int(z.within10.sum()),
        abstentions=int(z.predicted.isna().sum()),MAE_emitted=float(error.mean()),median_error_emitted=float(error.median()),
        largest_error=float(error.max()),contrast_sign_repeats=int(cc.sign_repeats.sum()),
        contrasts=len(cc),midpoint_MAE=float(z.midpoint_error.mean()),midpoint_hits=int(z.midpoint_within10.sum())))
(O/'summary.json').write_text(json.dumps(summary,indent=2))
(O/'manifest.json').write_text(json.dumps(dict(script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    inputs={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [B/'features.csv',B.parent/'cgm_fat_audit/full_audit/events_and_features.csv']},
    plan=plan),indent=2))
print(json.dumps(summary,indent=2))
