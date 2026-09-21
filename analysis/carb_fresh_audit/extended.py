from pathlib import Path
import pandas as pd
import numpy as np
import json
ROOT = str(Path(__file__).resolve().parents[2])  # repo root
B=Path(__file__).resolve().parent;O=B/'extended';O.mkdir(exist_ok=True)
R=Path(ROOT + '')
base=pd.read_csv(B/'libre_features.csv');records=[];coverage=[];traces=[]
for pid,z in base.groupby('pid'):
 d=pd.read_csv(R/f'dataset/csv/CGMacros-{pid:03d}.csv');d.columns=d.columns.str.strip()
 d.Timestamp=pd.to_datetime(d.Timestamp,format='mixed'); d=d.sort_values('Timestamp')
 good=d[['Timestamp','Libre GL']].dropna().groupby('Timestamp',as_index=False).mean()
 meals=d[d.Calories.fillna(0)>0]
 for r in z.itertuples():
  tm=pd.Timestamp(r.time);m=(good.Timestamp-tm).dt.total_seconds().to_numpy()/60;v=good['Libre GL'].to_numpy(float)
  nexts=(meals.Timestamp-tm).dt.total_seconds()/60;next_min=float(nexts[nexts>0].min())
  for end in [180,240,300]:
   grid=np.arange(-60,end+1,5);right=np.searchsorted(m,grid);valid=right.max()<len(m) and grid.min()>=m.min()
   if valid:
    left=np.maximum(0,right-1);valid=bool(np.all((m[right]-m[left]<=10)|np.isclose(m[right],grid)))
   clean=valid and (not np.isfinite(next_min) or next_min>end)
   coverage.append(dict(pid=int(pid),role=r.role,time=r.time,window=end,next_meal_min=next_min,sensor_valid=valid,clean=clean))
   if not clean:continue
   vals=np.interp(grid,m,v);pre=vals[:12];baseline=float(vals[10:12].mean());y=vals[12:]-baseline;t=grid[12:];p=np.maximum(y,0)
   def area(a,b):
    mask=(t>=a)&(t<=b);return float(np.trapezoid(p[mask],t[mask])) if mask.sum()>1 else 0.
   total=area(0,end)
   onset=next((int(t[i]) for i in range(len(y)-2) if np.all(y[i:i+3]>=10)),end+5)
   available=max(0,end-onset)
   ft=dict(peak=float(y.max()),early_peak=float(y[:13].max()),area_0_60=area(0,60),area_60_120=area(60,120),area_120_180=area(120,180),area_0_180=area(0,180),
    steepest_15min_rise=float(max((y[3:]-y[:-3])/15)),rise_0_30=float((y[6]-y[0])/30),peak_time=float(t[y.argmax()]),positive_duration=float(np.trapezoid((y>0).astype(float),t)),
    area_centroid=float(np.trapezoid(t*p,t)/total) if total>1e-8 else 0.,late_area_fraction=area(120,end)/total if total>1e-8 else 0.,
    baseline=baseline,pre_slope=float(np.polyfit(np.arange(-60,0,5),pre,1)[0]),pre_range=float(np.ptp(pre)),pre_recent_slope=float((pre[-1]-pre[-4])/15),
    onset=float(onset),aligned_area_60=area(onset,min(end,onset+60)),aligned_area_120=area(onset,min(end,onset+120)),aligned_observed_minutes=float(min(120,available)),
    end_change=float(y[-1]),end_slope=float((y[-1]-y[-4])/15),negative_area=float(np.trapezoid(np.minimum(y,0),t)),total_area=total)
   records.append(dict(pid=int(pid),role=r.role,time=r.time,carbs=r.carbs,window=end,**ft))
   traces.extend(dict(pid=int(pid),role=r.role,time=r.time,window=end,minute=int(a),glucose=float(b)) for a,b in zip(grid,vals))
f=pd.DataFrame(records);q=pd.DataFrame(coverage);q.to_csv(O/'coverage.csv',index=False);pd.DataFrame(traces).to_csv(O/'traces.csv',index=False)
for end in [180,240,300]:
 z=f[f.window==end].drop(columns='window');pids=z.groupby('pid').size();pids=pids[pids==4].index;z=z[z.pid.isin(pids)]
 z.to_csv(O/f'features_{end}.csv',index=False)
 print(end,'complete-person sets',len(pids),'later meals',2*len(pids))
print('P42 clean windows',q[q.pid==42].to_string(index=False))
(O/'feature_definitions.json').write_text(json.dumps({'onset':'first 3 consecutive 5-min samples >=10 mg/dL above premeal baseline, else window+5',
 'aligned_area':'positive area beginning at detected onset; truncated at window endpoint; available duration included',
 'prehistory':'previous 60 min of Libre; baseline mean at -10 and -5',
 'longer_window_rule':'all four meals sensor-covered and no later logged positive-calorie event through endpoint',
 'missing_events':'absence of a logged event does not prove no food was eaten','reserved_accessed':False},indent=2))
