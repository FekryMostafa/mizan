from pathlib import Path
import pandas as pd,numpy as np,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT = str(Path(__file__).resolve().parents[3])  # repo root
B=Path(__file__).resolve().parent.parent;O=Path(__file__).resolve().parent;R=Path(ROOT + '/dataset/csv')
cases=pd.read_csv(B/'backward_failures/selected_cases.csv',parse_dates=['time']);f=pd.read_csv(B/'libre_features.csv',parse_dates=['time']);bio=pd.read_csv(R/'bio.csv');bio.columns=bio.columns.str.strip();bio[bio.subject.isin(cases.pid)].to_csv(O/'baseline_bio.csv',index=False)
allraw=[];allmeals=[];summary=[];hourly=[];schema=[]
for k,q in enumerate(cases.itertuples(),1):
 d=pd.read_csv(R/f'CGMacros-{q.pid:03d}.csv');d.columns=d.columns.str.strip();d.Timestamp=pd.to_datetime(d.Timestamp,format='mixed');d=d.sort_values('Timestamp');schema.append(dict(pid=q.pid,columns=' | '.join(d.columns)))
 cal=f[(f.pid==q.pid)&f.role.eq('low_calibration' if q.actual==24 else 'high_calibration')].iloc[0].time
 motion='METs' if 'METs' in d else 'Intensity';chs=['Libre GL','HR','Calories (Activity)',motion]
 fig,axes=plt.subplots(4,2,figsize=(15,10),sharex='col',gridspec_kw={'width_ratios':[2.6,1]})
 for role,t,color in [('earlier',cal,'#1570b8'),('failure',q.time,'#d56017')]:
  w=d[(d.Timestamp>=t-pd.Timedelta(hours=24))&(d.Timestamp<=t+pd.Timedelta(hours=3))].copy();w['relative_hour']=(w.Timestamp-t).dt.total_seconds()/3600;w['case']=k;w['role']=role;w['pid']=q.pid;allraw.append(w)
  mm=d[d['Meal Type'].notna() | pd.to_numeric(d.Calories,errors='coerce').gt(0)].copy();last=mm[mm.Timestamp<t].tail(1)
  m=mm[(mm.Timestamp>=t-pd.Timedelta(hours=24))&(mm.Timestamp<=t+pd.Timedelta(hours=3))].copy();m['case']=k;m['role']=role;m['pid']=q.pid;m['relative_hour']=(m.Timestamp-t).dt.total_seconds()/3600;allmeals.append(m[['case','pid','role','Timestamp','relative_hour','Meal Type','Calories','Carbs','Protein','Fat','Fiber','Amount Consumed','Image path']])
  rec=dict(case=k,pid=q.pid,true_carbs=q.actual,role=role,meal_time=t,previous_meal_time=last.Timestamp.iloc[0] if len(last) else None,previous_meal_gap_hours=(t-last.Timestamp.iloc[0]).total_seconds()/3600 if len(last) else np.nan,previous_meal_carbs=last.Carbs.iloc[0] if len(last) else np.nan)
  for name,aa,bb in [('daybefore',-24,0),('last6h',-6,0),('pre1h',-1,0),('post3h',0,3)]:
   z=w[(w.relative_hour>=aa)&(w.relative_hour<bb)]
   rec[name+'_row_coverage']=len(z)/((bb-aa)*60)
   for ch in chs:
    v=pd.to_numeric(z[ch],errors='coerce');rec[name+'_'+ch+'_mean']=v.mean();rec[name+'_'+ch+'_min']=v.min();rec[name+'_'+ch+'_max']=v.max();rec[name+'_'+ch+'_coverage']=v.notna().sum()/((bb-aa)*60)
   rec[name+'_floor_minutes']=int(z['Libre GL'].le(40).sum());rec[name+'_ceiling_minutes']=int(z['Libre GL'].ge(400).sum())
  prior=m[m.relative_hour<0]
  for ch in ['Carbs','Protein','Fat','Fiber','Calories']:rec['logged_prior24_'+ch]=prior[ch].sum(min_count=1)
  rec['logged_prior24_meals']=len(prior);summary.append(rec)
  w['hour_bin']=np.floor(w.relative_hour)
  for hour,z in w.groupby('hour_bin'):
   rr=dict(case=k,pid=q.pid,role=role,hour=hour)
   for ch in chs:rr[ch+'_mean']=z[ch].mean();rr[ch+'_coverage']=z[ch].notna().sum()/60
   hourly.append(rr)
  for ci,ch in enumerate(chs):
   for j,(aa,bb) in enumerate([(-24,0),(0,3)]):
    z=w[(w.relative_hour>=aa)&(w.relative_hour<=bb)];axes[ci,j].plot(z.relative_hour,z[ch],color=color,lw=.9,label=role,alpha=.85);axes[ci,j].grid(alpha=.2)
    axes[ci,j].set_ylabel(ch);axes[ci,j].set_xlim(aa,bb)
  for mr in m[m.relative_hour<0].itertuples():
   axes[0,0].axvline(mr.relative_hour,color=color,alpha=.2)
 axes[0,0].legend(loc='upper left');axes[0,1].set_title('Meal to +3 hours');axes[0,0].set_title('Preceding 24 hours (vertical lines = logged meals)')
 axes[3,0].set_xlabel('Hours relative to meal');axes[3,1].set_xlabel('Hours relative to meal')
 fig.suptitle(f'Case {k}: P{q.pid}, {q.actual:g} g carbs, old estimate {q.original:.1f} g\nEarlier {cal} vs failure {q.time}; METs shown as stored (x10)',fontsize=13)
 fig.tight_layout(rect=[0,0,1,.94]);fig.savefig(O/f'case_{k:02}.png',dpi=110);plt.close(fig)
pd.concat(allraw).to_csv(O/'minute_records.csv',index=False);pd.concat(allmeals).to_csv(O/'meal_timeline.csv',index=False);pd.DataFrame(summary).to_csv(O/'context_summary.csv',index=False);pd.DataFrame(hourly).to_csv(O/'hourly_inspection.csv',index=False);pd.DataFrame(schema).drop_duplicates().to_csv(O/'available_columns.csv',index=False)
print(pd.DataFrame(summary)[['case','pid','role','previous_meal_gap_hours','logged_prior24_Carbs','logged_prior24_Fat','last6h_Libre GL_mean','last6h_HR_mean','post3h_HR_coverage','daybefore_row_coverage']].round(2).to_string(index=False))
