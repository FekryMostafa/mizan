from pathlib import Path
import numpy as np
import pandas as pd
import json, hashlib
ROOT = str(Path(__file__).resolve().parents[2])  # repo root

B=Path(ROOT + '')
O=Path(__file__).resolve().parent
c=pd.read_csv(B/'analysis/macro_features/personal_dose_repeat/contrasts.csv')
c=c[c.macro=='Carbs']
plan={'primary':'mean_sensor_full_curve','controls':['Dexcom GL','Libre GL'],
 'calibration':'first 24 g and 66 g carb meals; recorded protein 22 g, fat 10.5 g',
 'query':'two later controlled meals; existing development records',
 'representation':'0..180 min every 5 min, baseline mean at -10 and -5 min',
 'no_tuning':True,'reserved_accessed':False,
 'coverage':'both sensors required; interpolation brackets <=10 min',
 'interpretation':'sensor diagnostic; repeated known recipes not unseen meal validation'}
(O/'PLAN.json').write_text(json.dumps(plan,indent=2))
rows=[];quality=[];raw=[];contrasts=[];files=[]
def curve(df,tm,col):
    v=df[['Timestamp',col]].dropna().sort_values('Timestamp')
    v=v.groupby('Timestamp',as_index=False)[col].mean()
    u=(v.Timestamp-pd.Timestamp(tm)).dt.total_seconds().to_numpy()/60
    vals=v[col].to_numpy(float);grid=np.arange(-10,181,5)
    if not len(u) or grid[0]<u[0] or grid[-1]>u[-1]:return None
    rr=np.searchsorted(u,grid);ll=np.maximum(0,rr-1);rr=np.minimum(rr,len(u)-1)
    exact=np.isclose(u[rr],grid)
    if np.any((u[rr]-u[ll]>10)&~exact):return None
    y=np.interp(grid,u,vals);return y[2:]-y[:2].mean()
for r in c.itertuples():
    path=B/f'dataset/csv/CGMacros-{r.pid:03d}.csv';files.append(path)
    d=pd.read_csv(path);d.Timestamp=pd.to_datetime(d.Timestamp,format='mixed')
    times=[r.low_calibration_time,r.high_calibration_time,r.low_query_time,r.high_query_time]
    labels=[]
    for tm in times:
        z=d[d.Timestamp==pd.Timestamp(tm)]
        assert len(z)==1
        assert np.allclose(z[['Protein','Fat']].iloc[0].to_numpy(float),[22,10.5])
        labels.append(float(z.Carbs.iloc[0]))
    assert labels==[24,66,24,66]
    assert max(pd.Timestamp(t).value for t in times[:2])+180*60*10**9<min(pd.Timestamp(t).value for t in times[2:])
    curves={col:[curve(d,tm,col) for tm in times] for col in plan['controls']}
    valid=all(y is not None for ys in curves.values() for y in ys)
    quality.append({'pid':int(r.pid),'both_sensors_complete':valid})
    if not valid:continue
    for col,ys in curves.items():
        for j,y in enumerate(ys):
            raw.extend(dict(pid=int(r.pid),sensor=col,time=times[j],minute=i*5,relative_glucose=float(v)) for i,v in enumerate(y))
    curves['mean_sensor_full_curve']=[(a+b)/2 for a,b in zip(*curves.values())]
    for method,ys in curves.items():
        slope=(ys[1]-ys[0])/42;center=(ys[0]+ys[1])/2
        for j in [2,3]:
            pred=max(0,45+float((ys[j]-center)@slope/(slope@slope))) if slope@slope>1e-12 else np.nan
            actual=labels[j]
            rows.append(dict(pid=int(r.pid),time=times[j],method=method,actual=actual,predicted=pred,
                error_g=abs(pred-actual),within10=bool(abs(pred-actual)<=.1*actual)))
        contrasts.append(dict(pid=int(r.pid),method=method,calibration_peak_difference=float(ys[1].max()-ys[0].max()),
            query_peak_difference=float(ys[3].max()-ys[2].max()),
            repeat_shape_rmse=float(np.mean([np.sqrt(np.mean((ys[0]-ys[2])**2)),np.sqrt(np.mean((ys[1]-ys[3])**2))]))))
p=pd.DataFrame(rows);p.to_csv(O/'predictions.csv',index=False)
pd.DataFrame(quality).to_csv(O/'coverage.csv',index=False)
pd.DataFrame(raw).to_csv(O/'raw_curves.csv',index=False)
pd.DataFrame(contrasts).to_csv(O/'contrasts.csv',index=False)
s=[]
for method,z in p.groupby('method'):
    s.append(dict(method=method,people=z.pid.nunique(),meals=len(z),hits=int(z.within10.sum()),MAE=float(z.error_g.mean()),both_correct=int(z.groupby('pid').within10.all().sum())))
(O/'summary.json').write_text(json.dumps(s,indent=2))
(O/'manifest.json').write_text(json.dumps({str(q):hashlib.sha256(q.read_bytes()).hexdigest() for q in [Path(__file__),*files]},indent=2))
print(json.dumps(s,indent=2));print('Excluded for incomplete paired sensor coverage:',sum(not q['both_sensors_complete'] for q in quality))
