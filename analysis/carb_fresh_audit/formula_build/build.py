from pathlib import Path
import json, hashlib
import numpy as np
import pandas as pd
ROOT = str(Path(__file__).resolve().parents[3])  # repo root

O=Path(__file__).resolve().parent; B=O.parent
R=Path(ROOT + '/dataset/cgmacros_clean_v1')
refs=pd.read_csv(B/'libre_features.csv',parse_dates=['time'])
cases=pd.read_csv(B/'backward_failures/selected_cases.csv',parse_dates=['time'])
labels=pd.read_csv(R/'meals.csv',parse_dates=['timestamp'])
rows=[]; curves={}; sources={}
for pid,z in refs.groupby('pid'):
 path=R/'participants'/f'CGMacros-{pid:03d}.csv'
 sources[str(path)]=hashlib.sha256(path.read_bytes()).hexdigest()
 d=pd.read_csv(path);d.columns=d.columns.str.strip();d.Timestamp=pd.to_datetime(d.Timestamp,format='mixed');d=d.set_index('Timestamp')
 assert d.index.is_unique
 for r in z.itertuples():
  record=dict(pid=pid,role=r.role,time=r.time)
  mm=labels[(labels.participant_id==pid)&(labels.timestamp==r.time)]
  assert len(mm)==1 and mm.iloc[0].label_status=='eligible_full_consumption'
  record['carbs']=float(mm.iloc[0].carbs_g)
  g=d['Libre GL'].reindex(pd.date_range(r.time-pd.Timedelta(minutes=10),r.time+pd.Timedelta(minutes=180),freq='5min')).to_numpy(float)
  assert np.isfinite(g).all()
  base=g[:2].mean();y=g[2:]-base;p=np.maximum(y,0)
  record['baseline']=base;record['peak']=max(y)
  for start,end in [(0,60),(60,120),(120,180)]:
   record[f'area_{start}_{end}']=float(np.trapezoid(p[start//5:end//5+1],dx=5))
  record['peak_time']=float(np.argmax(y)*5);record['rise_0_30']=float((y[6]-y[0])/30)
  curves[pid,r.role]=y
  for name,aa,bb in [('pre24',-1440,0),('pre6',-360,0),('pre1',-60,0),('early',0,60),('middle',60,120),('late',120,180)]:
   expected=pd.date_range(r.time+pd.Timedelta(minutes=aa),periods=bb-aa,freq='min')
   w=d.reindex(expected)
   for col,key in [('Libre GL','glucose'),('HR','hr'),('Calories (Activity)','activity')]:
    v=w[col];cov=v.notna().mean()
    record[f'{name}_{key}_coverage']=cov
    record[f'{name}_{key}']=float(v.mean()) if cov>=.9 else np.nan
  prior=labels[(labels.participant_id==pid)&(labels.timestamp>=r.time-pd.Timedelta(hours=24))&(labels.timestamp<r.time)]
  record['prior_food_review']=float(prior.label_status.ne('eligible_full_consumption').any())
  rows.append(record)
f=pd.DataFrame(rows);f.to_csv(O/'measured_inputs.csv',index=False)
gcols=['peak','area_0_60','area_60_120','area_120_180','peak_time','rise_0_30']
# Floors depend only on historical calibration signals, not query answers.
floors={c:max(.25*np.median([abs(z.set_index('role').loc['high_calibration',c]-z.set_index('role').loc['low_calibration',c]) for _,z in f.groupby('pid')]),1e-6) for c in gcols}
features=[]
for pid,z in f.groupby('pid'):
 z=z.set_index('role');lo=z.loc['low_calibration'];hi=z.loc['high_calibration'];yl=curves[pid,'low_calibration'];yh=curves[pid,'high_calibration'];delta=yh-yl
 for role in ['low_query','high_query']:
  q=z.loc[role];y=curves[pid,role]
  base=max(0,24+42*float(np.dot(y-yl,delta)/max(np.dot(delta,delta),1e-8)))
  out=dict(pid=pid,time=q.time,actual=q.carbs,base=base)
  for c in gcols:
   diff=hi[c]-lo[c];den=(-1 if diff<0 else 1)*max(abs(diff),floors[c]);out['personal_'+c]=(q[c]-(lo[c]+hi[c])/2)/den
  for origin in ['start','minimum']:
   norm=[]
   for yy in [yl,yh,y]:
    yy=yy-(yy[0] if origin=='start' else min(yy));norm.append(yy/max(np.linalg.norm(yy),1e-8))
   dl=np.linalg.norm(norm[2]-norm[0]);dh=np.linalg.norm(norm[2]-norm[1]);out['shape_'+origin]=(dl-dh)/max(dl+dh,1e-8)
  out['baseline_difference']=q.baseline-(lo.baseline+hi.baseline)/2
  for c in f.columns:
   if c.startswith(('pre24_','pre6_','pre1_','early_','middle_','late_')):
    out[c]=q[c]
  out['prior_food_review']=q.prior_food_review
  features.append(out)
a=pd.DataFrame(features);a.time=pd.to_datetime(a.time)
a['target_case']=[bool(((cases.pid==r.pid)&(cases.time==r.time)).any()) for r in a.itertuples()]
assert a.target_case.sum()==10 and len(a)==52
# No identity, dose category, dates, current food, current fat or protein enters predictors.
cols=[c for c in a if c not in ['pid','time','actual','base','target_case']]
a.to_csv(O/'formula_inputs.csv',index=False)
def preparation(train):
 x=a[cols].to_numpy(float);tr=x[train]
 med=np.array([np.nanmedian(v) if np.isfinite(v).any() else 0 for v in tr.T])
 x=np.where(np.isfinite(x),x,med);mean=x[train].mean(axis=0);sd=x[train].std(axis=0);sd[sd<1e-8]=1
 x=(x-mean)/sd
 return x,med,mean,sd

def path_fit(train,max_terms=8):
 x,med,mu,sd=preparation(train);resid=a.actual.to_numpy()-a.base.to_numpy()
 selected=[];steps=[dict(terms=[],coef=[],pred=a.base.to_numpy().copy())]
 # Add a single observable each step; refit coefficients jointly on the ten cases.
 for step in range(max_terms):
  options=[]
  for j in range(len(cols)):
   if j in selected or np.std(x[train,j])<1e-8:continue
   ix=selected+[j];design=np.c_[np.ones(len(a)),x[:,ix]]
   coef=np.linalg.lstsq(design[train],resid[train],rcond=1e-8)[0]
   pred=np.maximum(0,a.base.to_numpy()+design@coef)
   err=pred[train]-a.actual.to_numpy()[train]
   options.append((float(err@err),j,coef,pred))
  if not options:break
  _,j,coef,pred=min(options,key=lambda v:(v[0],v[1]));selected.append(j)
  steps.append(dict(terms=[cols[j] for j in selected],coef=coef.tolist(),pred=pred))
 return steps,dict(medians=dict(zip(cols,med)),means=dict(zip(cols,mu)),scales=dict(zip(cols,sd)))

train=a.target_case.to_numpy();steps,scaling=path_fit(train)
predictions=[];summaries=[]
for k,s in enumerate(steps):
 for i,r in a.iterrows():
  pred=s['pred'][i];predictions.append(dict(step=k,pid=r.pid,time=r.time,actual=r.actual,predicted=pred,error=abs(pred-r.actual),within10=abs(pred-r.actual)<=.1*r.actual,target_case=r.target_case))
 for group,mask in [('ten_fitted_cases',train),('other_42_diagnostic_only',~train)]:
  error=abs(s['pred'][mask]-a.actual.to_numpy()[mask]);summaries.append(dict(step=k,group=group,n=int(mask.sum()),hits=int((error<=.1*a.actual.to_numpy()[mask]).sum()),mae=float(error.mean()),added_term=s['terms'][-1] if s['terms'] else 'personal_full_curve_projection'))
pd.DataFrame(predictions).to_csv(O/'step_predictions.csv',index=False)
# Selection itself repeated with one target participant omitted: no oracle selection on that person's answer.
loo=[]
for pid in a.loc[train,'pid'].unique():
 tr=train & a.pid.ne(pid).to_numpy();ss,_=path_fit(tr)
 mask=train & a.pid.eq(pid).to_numpy()
 for k,s in enumerate(ss):
  for i in np.flatnonzero(mask):
   r=a.iloc[i];pr=s['pred'][i];loo.append(dict(step=k,pid=int(pid),time=r.time,actual=r.actual,predicted=pr,error=abs(pr-r.actual),within10=abs(pr-r.actual)<=.1*r.actual))
l=pd.DataFrame(loo);l.to_csv(O/'leave_person_out.csv',index=False)
for k,z in l.groupby('step'):summaries.append(dict(step=k,group='ten_leave_person_out',n=len(z),hits=int(z.within10.sum()),mae=float(z.error.mean()),added_term='selected_without_this_person'))
s=pd.DataFrame(summaries);s.to_csv(O/'summary.csv',index=False)
formula=dict(definition='max(0, personal_full_curve_projection + intercept + sum(coefficient * standardized_observable))',
 target='carbohydrate grams',fit_scope='ten previously selected largest failures; retrospective feature selection and fitting',
 steps=[{k:v for k,v in step.items() if k!='pred'} for step in steps],scaling=scaling,
 missing='less than 90 percent coverage => unavailable mean; training-only median imputation; coverage remains observable',
 source_hashes=sources)
(O/'formula.json').write_text(json.dumps(formula,indent=2))
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in sources.items())
print(s.to_string(index=False))
print(pd.DataFrame(predictions).query('target_case').pivot(index=['pid','actual'],columns='step',values='predicted').round(2).to_string())
