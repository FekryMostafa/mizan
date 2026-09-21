from pathlib import Path
import numpy as np
import pandas as pd
import json
ROOT = str(Path(__file__).resolve().parents[2])  # repo root
B=Path(__file__).resolve().parent
r=pd.read_csv(B/'raw_curves.csv');r=r[r.sensor=='Libre GL'];r.time=pd.to_datetime(r.time)
c=pd.read_csv(ROOT + '/analysis/macro_features/personal_dose_repeat/contrasts.csv');c=c[c.macro=='Carbs']
def features(y):
    p=np.maximum(y,0); t=np.arange(len(y))*5
    area=lambda a,b:float(np.trapezoid(p[a//5:b//5+1],dx=5))
    total=area(0,180)
    return dict(peak=float(max(y)),early_peak=float(max(y[:13])),
        area_0_60=area(0,60),area_60_120=area(60,120),area_120_180=area(120,180),area_0_180=total,
        steepest_15min_rise=float(max((y[3:]-y[:-3])/15)),rise_0_30=float((y[6]-y[0])/30),
        peak_time=float(t[y.argmax()]),positive_duration=float(np.trapezoid((y>0).astype(float),dx=5)),
        area_centroid=float(np.trapezoid(t*p,dx=5)/total) if total>1e-9 else np.nan,
        late_area_fraction=area(120,180)/total if total>1e-9 else np.nan)
rows=[]
for a in c.itertuples():
    for role in ['low_calibration','high_calibration','low_query','high_query']:
        tm=pd.Timestamp(getattr(a,role+'_time'))
        y=r[(r.pid==a.pid)&(r.time==tm)].sort_values('minute').relative_glucose.to_numpy()
        assert len(y)==37
        rows.append(dict(pid=a.pid,role=role,time=tm.isoformat(),carbs=24 if role.startswith('low') else 66,**features(y)))
f=pd.DataFrame(rows);f.to_csv(B/'libre_features.csv',index=False)
summary=[];predictions=[]
for col in list(features(np.arange(37))):
    w=f.pivot(index='pid',columns='role',values=col)
    dc=w.high_calibration-w.low_calibration;dq=w.high_query-w.low_query
    usable=(abs(dc)>1e-9)&np.isfinite(dc)&np.isfinite(dq)
    ratios=dq[usable]/dc[usable]
    pp=[]
    for pid,z in w.iterrows():
        for role,true in [('low_query',24),('high_query',66)]:
            pred=max(0,24+42*(z[role]-z.low_calibration)/(z.high_calibration-z.low_calibration)) if usable.loc[pid] else np.nan
            d=dict(feature=col,pid=int(pid),role=role,actual=true,predicted=pred,error=abs(pred-true),within10=bool(abs(pred-true)<=true*.1))
            predictions.append(d);pp.append(d)
    summary.append(dict(feature=col,calibration_higher=int((dc>0).sum()),query_higher=int((dq>0).sum()),
       consistent_sign=int(((dc*dq)>0).sum()),usable_people=int(usable.sum()),
       median_query_to_calibration_contrast=float(ratios.median()),
       hits=sum(z['within10'] for z in pp),mae=float(np.nanmean([z['error'] for z in pp]))))
s=pd.DataFrame(summary);s.to_csv(B/'feature_patterns.csv',index=False)
pd.DataFrame(predictions).to_csv(B/'single_feature_predictions.csv',index=False)
print(s.to_string(index=False))
