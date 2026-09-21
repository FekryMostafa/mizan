"""Separate-macro inverse directions, stabilized using other people's calibration pairs."""
from pathlib import Path
import json
import hashlib
import numpy as np
import pandas as pd

B=Path(__file__).resolve().parent
O=B/'pooled_dose_direction';O.mkdir(exist_ok=True)
plan=dict(primary='half_population', weights={'personal_only':0,'half_population':.5,'population_only':1},
    representation='37 baseline-subtracted CGM samples, 0 through 180 minutes at five-minute intervals; equal weights.',
    population='Mean high-minus-low direction per gram from first calibration pairs of other people only.',
    personal='Blend population and own dose direction, retain own calibration midpoint; orthogonal projection gives grams.',
    target='Same later controlled-dose queries as personal_dose_repeat; each macro evaluated separately.',
    tuning=False,reserved_accessed=False,
    caveat='Known controlled composition during evaluation. Not arbitrary-meal or unknown-dose validation.')
(O/'PLAN.json').write_text(json.dumps(plan,indent=2))
f=pd.read_csv(B/'features.csv');f.time=pd.to_datetime(f.time,format='mixed')
x=np.load(B/'curve_audit/curves.npz',allow_pickle=False)['X']
assert x.shape==(len(f),37) and np.isfinite(x).all()
c=pd.read_csv(B/'personal_dose_repeat/contrasts.csv')
old=pd.read_csv(B/'personal_dose_repeat/predictions.csv')
specs=json.loads((B/'personal_dose_repeat/PLAN.json').read_text())['specs']
index={(r.dataset,int(r.pid),r.time.isoformat()):i for i,r in f.iterrows()}
def ix(pid,time):return index[('CGMacros',int(pid),pd.Timestamp(time).isoformat())]
rows=[];directions=[]
for macro,z in c.groupby('macro'):
    k=['Carbs','Protein','Fat'].index(macro)
    lo,hi=specs[macro]['low'][k],specs[macro]['high'][k]
    delta=hi-lo; midpoint=(hi+lo)/2
    calibration={}
    for r in z.itertuples():
        a,b=ix(r.pid,r.low_calibration_time),ix(r.pid,r.high_calibration_time)
        assert np.allclose(f.loc[a,['Carbs','Protein','Fat']].to_numpy(float),specs[macro]['low'])
        assert np.allclose(f.loc[b,['Carbs','Protein','Fat']].to_numpy(float),specs[macro]['high'])
        calibration[r.pid]=dict(slope=(x[b]-x[a])/delta, center=(x[b]+x[a])/2, a=a,b=b)
    for r in z.itertuples():
        own=calibration[r.pid]
        other=[v['slope'] for pid,v in calibration.items() if pid!=r.pid]
        assert len(other)==len(z)-1
        pop=np.mean(other,axis=0)
        for method,weight in plan['weights'].items():
            slope=(1-weight)*own['slope']+weight*pop
            denom=float(slope@slope)
            for time in [r.low_query_time,r.high_query_time]:
                i=ix(r.pid,time)
                assert max(f.loc[own['a'],'time'].value,f.loc[own['b'],'time'].value)+180*60*10**9<f.loc[i,'time'].value
                # Query label is read only after the signal-derived prediction.
                pred=float(max(0,midpoint+(x[i]-own['center'])@slope/denom)) if denom>1e-12 else np.nan
                actual=float(f.loc[i,macro])
                rows.append(dict(macro=macro,pid=int(r.pid),time=pd.Timestamp(time).isoformat(),method=method,
                    predicted=pred,actual=actual,error_g=abs(pred-actual),
                    within10=bool(np.isfinite(pred) and abs(pred-actual)<=.1*actual+1e-9)))
            directions.append(dict(macro=macro,pid=int(r.pid),method=method,direction_norm=float(np.sqrt(denom)),
                other_people=len(other)))
p=pd.DataFrame(rows);assert len(p)==3*len(old)
keys=lambda z:set(zip(z.macro,z.pid,pd.to_datetime(z.time,format='mixed').astype(str)))
assert all(keys(z)==keys(old) for _,z in p.groupby('method'))
assert not p.duplicated(['macro','pid','time','method']).any()
summary=[]
for (macro,method),z in p.groupby(['macro','method']):
    summary.append(dict(macro=macro,method=method,people=z.pid.nunique(),meals=len(z),hits=int(z.within10.sum()),
        both_doses_hit=int(z.groupby('pid').within10.all().sum()),abstentions=int(z.predicted.isna().sum()),
        MAE=float(z.error_g.mean()),median_error=float(z.error_g.median())))
p.to_csv(O/'predictions.csv',index=False)
pd.DataFrame(directions).to_csv(O/'directions.csv',index=False)
(O/'summary.json').write_text(json.dumps(summary,indent=2))
(O/'manifest.json').write_text(json.dumps(dict(script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    inputs={str(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in [B/'features.csv',B/'curve_audit/curves.npz',B/'personal_dose_repeat/contrasts.csv']},
    same_query_keys_verified=True,plan=plan),indent=2))
print(json.dumps(summary,indent=2))
