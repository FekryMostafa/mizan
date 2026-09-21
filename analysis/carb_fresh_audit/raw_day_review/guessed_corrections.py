from pathlib import Path
import pandas as pd,numpy as np
ROOT = str(Path(__file__).resolve().parents[3])  # repo root
B=Path(__file__).resolve().parent.parent;O=Path(__file__).resolve().parent;R=Path(ROOT + '/dataset/csv')
f=pd.read_csv(B/'libre_features.csv',parse_dates=['time']);records=[];raw={}
for pid,z in f.groupby('pid'):
 d=pd.read_csv(R/f'CGMacros-{pid:03d}.csv');d.columns=d.columns.str.strip();d.Timestamp=pd.to_datetime(d.Timestamp,format='mixed')
 for r in z.itertuples():
  rec=r._asdict();rec.pop('Index');delta=(d.Timestamp-r.time).dt.total_seconds()/3600
  for hrs in [6,12,24]:
   w=d[(delta>=-hrs)&(delta<0)];rec[f'coverage_{hrs}']=len(w)/(hrs*60)
   rec[f'energy_{hrs}']=w['Calories (Activity)'].mean();rec[f'hr_{hrs}']=w.HR.mean()
   # Excess over this same window's lower decile, a Fitbit activity proxy, not grams oxidized.
   v=w['Calories (Activity)'];rec[f'excess_{hrs}']=np.maximum(v-v.quantile(.1),0).mean()
   rec[f'glucose_{hrs}']=w['Libre GL'].mean()
  records.append(rec)
  y=d.set_index('Timestamp')['Libre GL'].reindex(pd.date_range(r.time,r.time+pd.Timedelta(hours=3),freq='5min')).to_numpy(float);raw[pid,r.role]=y
x=pd.DataFrame(records);x.to_csv(O/'guessed_context_inputs.csv',index=False);pred=[]
for pid,z in x.groupby('pid'):
 z=z.set_index('role');lo=z.loc['low_calibration'];hi=z.loc['high_calibration']
 for role in ['low_query','high_query']:
  q=z.loc[role]
  for hrs in [6,12,24]:
   if min(lo[f'coverage_{hrs}'],hi[f'coverage_{hrs}'],q[f'coverage_{hrs}'])<.95:continue
   for proxy in ['energy','excess','hr']:
    vv=np.array([lo[f'{proxy}_{hrs}'],hi[f'{proxy}_{hrs}'],q[f'{proxy}_{hrs}']])
    if not np.isfinite(vv).all() or min(vv)<=1e-6:continue
    for direction in [1,-1]:
     for feat in ['peak','area_60_120','area_0_180']:
      yy=np.array([lo[feat],hi[feat],q[feat]])*(vv/np.mean(vv[:2]))**direction
      if abs(yy[1]-yy[0])<1e-6:continue
      value=max(0,24+42*(yy[2]-yy[0])/(yy[1]-yy[0]));pred.append(dict(pid=pid,time=q.time,actual=q.carbs,rule=f'{feat}_{proxy}_{hrs}h_power{direction}',predicted=value,error=abs(value-q.carbs)))
  # Remove response scale and compare only full curve shape to the two known anchors.
  for baseline in ['start','minimum']:
   ys=[]
   for rr in ['low_calibration','high_calibration',role]:
    yy=raw[pid,rr].copy();yy-=yy[0] if baseline=='start' else min(yy);yy/=max(np.linalg.norm(yy),1e-6);ys.append(yy)
   dl=np.linalg.norm(ys[2]-ys[0]);dh=np.linalg.norm(ys[2]-ys[1]);value=24 if dl<dh else 66
   pred.append(dict(pid=pid,time=q.time,actual=q.carbs,rule='normalized_curve_nearest_'+baseline,predicted=value,error=abs(value-q.carbs)))
p=pd.DataFrame(pred);p['within10']=p.error<=.1*p.actual;p.to_csv(O/'guessed_predictions.csv',index=False)
c=pd.read_csv(B/'backward_failures/selected_cases.csv',parse_dates=['time'])
for r in c.itertuples():
 pp=p[(p.pid==r.pid)&(p.time==r.time)].sort_values('error');print(r.pid,r.actual,pp[['rule','predicted','within10']].head(3).to_dict('records'))
print(p.groupby('rule').agg(n=('error','size'),hits=('within10','sum'),mae=('error','mean')).sort_values('hits',ascending=False).head(10).to_string())
