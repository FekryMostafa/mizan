from pathlib import Path
import pandas as pd,numpy as np
ROOT = str(Path(__file__).resolve().parents[3])  # repo root
B=Path(__file__).resolve().parent.parent;O=Path(__file__).resolve().parent
R=Path(ROOT + '/dataset/csv')
old=pd.read_csv(B/'calibration_test/case_comparison.csv');old.time=pd.to_datetime(old.time)
f=pd.read_csv(B/'libre_features.csv');f.time=pd.to_datetime(f.time)
# Freeze cases by previous error before calculating candidate corrections.
cases=old.sort_values('error_g',ascending=False).head(10);cases.to_csv(O/'selected_cases.csv',index=False)
records=[];inventory=[];curves={}
for path in sorted(R.glob('CGMacros-*.csv')):
 pid=int(path.stem.split('-')[1]);d=pd.read_csv(path);d.columns=d.columns.str.strip();d.Timestamp=pd.to_datetime(d.Timestamp,format='mixed');d=d.sort_values('Timestamp').drop_duplicates('Timestamp').set_index('Timestamp')
 meals=d[d['Meal Type'].notna() | pd.to_numeric(d.Calories,errors='coerce').gt(0)].copy()
 for i,(t,r) in enumerate(meals.iterrows()):
  gap=(meals.index[i+1]-t).total_seconds()/60 if i+1<len(meals) else np.inf
  rec=dict(pid=pid,time=t,meal_type=str(r['Meal Type']).lower(),carbs=r.Carbs,protein=r.Protein,fat=r.Fat,fiber=r.Fiber,consumed=r.get('Amount Consumed',np.nan),image=r.get('Image path'),next_minutes=gap)
  inventory.append(rec.copy())
  if pid not in old.pid.unique():continue
  w=d.reindex(pd.date_range(t-pd.Timedelta(minutes=10),t+pd.Timedelta(minutes=180),freq='min'))
  g=pd.to_numeric(w['Libre GL'],errors='coerce');rec['coverage']=g.notna().mean();rec['floor_minutes']=int(g.le(40).sum())
  baseline=g.iloc[[0,5]].mean();gg=g.iloc[10::5].to_numpy(float);y=gg-baseline;p=np.maximum(y,0);tt=np.arange(37)*5
  ar=lambda a,b:float(np.trapezoid(p[a//5:b//5+1],dx=5))
  rec.update(baseline=baseline,peak=float(np.max(y)),early_peak=float(np.max(y[:13])),area_0_60=ar(0,60),area_60_120=ar(60,120),area_120_180=ar(120,180),area_0_180=ar(0,180),peak_time=float(tt[np.argmax(y)]))
  for name,a,b in [('pre',-180,0),('early',0,60),('middle',60,120),('late',120,180)]:
   ww=d.loc[(d.index>=t+pd.Timedelta(minutes=a))&(d.index<t+pd.Timedelta(minutes=b))]
   rec[name+'_hr']=pd.to_numeric(ww.HR,errors='coerce').mean();rec[name+'_activity']=pd.to_numeric(ww['Calories (Activity)'],errors='coerce').mean()
   rec[name+'_hr_coverage']=ww.HR.notna().sum()/(b-a)
  rec['usable']=bool(rec['coverage']>=.95 and np.isfinite(y).all() and gap>=180 and rec['floor_minutes']==0 and pd.notna(r.Carbs) and r.get('Amount Consumed',np.nan)==100)
  records.append(rec);curves[(pid,t)]=y
inv=pd.DataFrame(inventory);inv.to_csv(O/'raw_meal_inventory.csv',index=False)
a=pd.DataFrame(records);a.to_csv(O/'raw_history_audit.csv',index=False)
rows=[];neighbors=[];histcounts=[]
sets={'amplitude':['peak','area_0_60','area_60_120','area_120_180'],'shape':['peak_time'],'amplitude_context':['peak','area_0_60','area_60_120','area_120_180','baseline','pre_hr','early_hr','middle_hr','late_hr','pre_activity','early_activity','middle_activity','late_activity']}
for q in old.itertuples():
 query=a[(a.pid==q.pid)&(a.time==q.time)].iloc[0]
 h=a[(a.pid==q.pid)&(a.time+pd.Timedelta(minutes=180)<q.time)&a.usable].copy()
 histcounts.append(dict(pid=q.pid,time=q.time,prior_labeled=int(((inv.pid==q.pid)&(inv.time+pd.Timedelta(minutes=180)<q.time)).sum()),usable_history=len(h),breakfast=int(h.meal_type.eq('breakfast').sum()),lunch=int(h.meal_type.eq('lunch').sum()),dinner=int(h.meal_type.eq('dinner').sum()),query_floor_minutes=query.floor_minutes))
 for name,cols in sets.items():
  hh=h[cols].to_numpy(float);v=query[cols].to_numpy(float);usable=np.isfinite(v)&(np.isfinite(hh).mean(axis=0)>=.8)
  if not usable.any() or len(h)<3:continue
  hh=hh[:,usable];v=v[usable];med=np.nanmedian(hh,axis=0);hh=np.where(np.isfinite(hh),hh,med)
  scale=np.nanstd(hh,axis=0);scale=np.maximum(scale,1e-6)
  dist=np.sqrt(np.mean(((hh-v)/scale)**2,axis=1));ix=np.argsort(dist,kind='stable')
  for k in [1,3]:
   ii=ix[:k];weights=1/np.maximum(dist[ii],.1);pred=float(np.average(h.iloc[ii].carbs,weights=weights))
   rows.append(dict(pid=q.pid,time=q.time,actual=q.actual,rule=f'history_{name}_{k}',predicted=pred,error=abs(pred-q.actual),within10=abs(pred-q.actual)<=.1*q.actual))
  for rank,j in enumerate(ix[:3]):
   z=h.iloc[j];neighbors.append(dict(pid=q.pid,time=q.time,metric=name,rank=rank+1,history_time=z.time,history_type=z.meal_type,carbs=z.carbs,protein=z.protein,fat=z.fat,distance=dist[j],query_peak=query.peak,history_peak=z.peak,query_middle_area=query.area_60_120,history_middle_area=z.area_60_120))
 # Single feature inverse: earlier two matched-macro anchors, no clipping to known doses.
 ff=f[f.pid==q.pid].set_index('role');qr=f[(f.pid==q.pid)&(f.time==q.time)].iloc[0]
 for col in f.columns[4:]:
  lo=ff.loc['low_calibration',col];hi=ff.loc['high_calibration',col]
  if np.isfinite([lo,hi,qr[col]]).all() and abs(hi-lo)>1e-8:
   pred=max(0,24+42*(qr[col]-lo)/(hi-lo));rows.append(dict(pid=q.pid,time=q.time,actual=q.actual,rule='anchor_'+col,predicted=pred,error=abs(pred-q.actual),within10=abs(pred-q.actual)<=.1*q.actual))
 for col in ['CGM_True','CGM_activity_True']:
  pred=getattr(q,col);rows.append(dict(pid=q.pid,time=q.time,actual=q.actual,rule=col,predicted=pred,error=abs(pred-q.actual),within10=abs(pred-q.actual)<=.1*q.actual))
p=pd.DataFrame(rows);p.to_csv(O/'candidate_predictions.csv',index=False);pd.DataFrame(neighbors).to_csv(O/'neighbors.csv',index=False);pd.DataFrame(histcounts).to_csv(O/'history_counts.csv',index=False)
s=p.groupby('rule').agg(n=('error','size'),hits=('within10','sum'),mae=('error','mean'));s.to_csv(O/'rule_summary.csv')
out=[]
for c in cases.itertuples():
 pp=p[(p.pid==c.pid)&(p.time==c.time)].sort_values('error');best=pp.iloc[0];hh=pd.DataFrame(histcounts);h=hh[(hh.pid==c.pid)&(hh.time==c.time)].iloc[0]
 out.append(dict(pid=c.pid,time=c.time,actual=c.actual,original=c.original,best_rule=best.rule,retrospective_prediction=best.predicted,hit=best.within10,prior_meals=h.prior_labeled,usable_history=h.usable_history,floor_minutes=h.query_floor_minutes,rule_total_hits=int(s.loc[best.rule,'hits']),rule_n=int(s.loc[best.rule,'n'])))
pd.DataFrame(out).to_csv(O/'ten_cases.csv',index=False)
print('RAW INVENTORY',len(inv),inv.meal_type.value_counts().to_dict())
print(pd.DataFrame(out).to_string(index=False));print(s.sort_values('hits',ascending=False).to_string())
