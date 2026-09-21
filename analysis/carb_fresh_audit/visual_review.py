from pathlib import Path
import numpy as np,pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT = str(Path(__file__).resolve().parents[2])  # repo root
B=Path(__file__).resolve().parent;O=B/'visual_review';O.mkdir(exist_ok=True)
R=Path(ROOT + '/dataset')
p=pd.read_csv(B/'combinations/predictions.csv');f=pd.read_csv(B/'libre_features.csv')
bio=pd.read_csv(R/'csv/bio.csv');bio.columns=bio.columns.str.strip();bio=bio.set_index('subject')
order=p.groupby('pid').error_g.max().sort_values(ascending=False).index.tolist()
raw={};metrics=[];nearby=[]
for pid in order:
 d=pd.read_csv(R/f'csv/CGMacros-{pid:03d}.csv');d.columns=d.columns.str.strip();d.Timestamp=pd.to_datetime(d.Timestamp,format='mixed')
 raw[pid]=d
 for row in f[f.pid==pid].itertuples():
  tm=pd.Timestamp(row.time);v=d.copy();v['minute']=(v.Timestamp-tm).dt.total_seconds()/60
  rec=dict(pid=pid,role=row.role,time=row.time,carbs=row.carbs)
  for period,a,b in [('before',-180,0),('after',0,180)]:
   z=v[(v.minute>=a)&(v.minute<b)]
   rec[period+'_rows']=len(z)
   for field in ['HR','Calories (Activity)']:
    s=z[field];rec[period+'_'+field+'_coverage']=float(s.notna().mean());rec[period+'_'+field+'_mean']=float(s.mean());rec[period+'_'+field+'_max']=float(s.max())
   if 'METs' in z:
    rec[period+'_METs_mean']=float(z.METs.mean()/10);rec[period+'_METs_coverage']=float(z.METs.notna().mean())
   if 'Intensity' in z:
    rec[period+'_Intensity_mean']=float(z.Intensity.mean());rec[period+'_Intensity_coverage']=float(z.Intensity.notna().mean())
  rec.update({col:bio.loc[pid,col] for col in ['Age','Gender','BMI','A1c PDL (Lab)','Fasting GLU - PDL (Lab)','Insulin']})
  metrics.append(rec)
  z=v[(v.minute>=-720)&(v.minute<=360)&(v.Calories.fillna(0)>0)]
  nearby.extend(dict(pid=pid,role=row.role,minute=float(a.minute),meal=a['Meal Type'],carbs=a.Carbs,protein=a.Protein,fat=a.Fat) for _,a in z.iterrows())
pd.DataFrame(metrics).to_csv(O/'context.csv',index=False);pd.DataFrame(nearby).to_csv(O/'nearby_meals.csv',index=False)
for page in range(0,len(order),2):
 people=order[page:page+2];fig,axes=plt.subplots(8,2,figsize=(13,15),sharex=True)
 for block,pid in enumerate(people):
  d=raw[pid];bi=bio.loc[pid]
  for col,(prefix,dose) in enumerate([('low',24),('high',66)]):
   pred=p[(p.pid==pid)&(p.actual==dose)].iloc[0]
   axs=axes[block*4:block*4+4,col];activity='METs' if 'METs' in d else 'Intensity'
   for role,color in [('calibration','#2366b5'),('query','#d26520')]:
    row=f[(f.pid==pid)&(f.role==prefix+'_'+role)].iloc[0];tm=pd.Timestamp(row.time)
    u=(d.Timestamp-tm).dt.total_seconds()/60;z=d[(u>=-180)&(u<=180)].copy();z['minute']=u[(u>=-180)&(u<=180)]
    for ax,field in zip(axs,['Libre GL','HR','Calories (Activity)',activity]):
     vals=z[field]/10 if field=='METs' else z[field]
     ax.plot(z.minute,vals,color=color,lw=.85,alpha=.85,label=role)
    events=d[(d.Calories.fillna(0)>0)&(u>=-180)&(u<=180)]
    for idx,event in events.iterrows():
     if abs(u.loc[idx])>.1:axs[0].axvline(u.loc[idx],color=color,ls=':',lw=1)
   status='HIT' if pred.within10 else 'MISS'
   axs[0].set_title(f'P{pid}: {dose} g → {pred.predicted:.1f} g ({status}) | {int(bi.Age)}y {bi.Gender}, BMI {bi.BMI:.1f}',fontsize=10,color='#137743' if pred.within10 else '#333333')
   for ax,label in zip(axs,['Glucose mg/dL','Heart rate bpm','Fitbit kcal/min',activity]):
    ax.axvline(0,color='black',lw=.7);ax.set_ylabel(label,fontsize=8);ax.grid(alpha=.15);ax.tick_params(labelsize=8);ax.spines[['top','right']].set_visible(False)
   axs[0].legend(fontsize=7,loc='upper left');axs[-1].set_xlabel('Minutes from logged meal',fontsize=8)
 if len(people)==1:
  for ax in axes[4:].flat:ax.set_visible(False)
 fig.suptitle('Same-dose calibration vs later meal | blue = calibration, orange = later\nGaps remain missing; dotted glucose lines mark other logged food. Intensity is not METs.',fontsize=12)
 fig.tight_layout(rect=[0,0,1,.96]);fig.savefig(O/f'page_{page//2+1:02d}.png',dpi=110);plt.close(fig)
print('Rendered pages:',(len(order)+1)//2,'participant order:',order)
