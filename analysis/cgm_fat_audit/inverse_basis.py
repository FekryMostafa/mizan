"""Direct continuous gram inference from personal dose-response basis vectors."""
from pathlib import Path
import json
import numpy as np,pandas as pd
from scipy.optimize import lsq_linear
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'analysis/cgm_fat_audit/inverse_basis';OUT.mkdir(exist_ok=True)
e=pd.read_csv(ROOT/'analysis/cgm_fat_audit/full_audit/events_and_features.csv',parse_dates=['time']).set_index('id')
m=pd.read_csv(ROOT/'analysis/cgm_fat_audit/separability/repeat_matches.csv');m=m[(m.baseline=='pre10')&(m.minutes==180)]
REC=['reference','carb_low','protein_high','fat_high'];ref=np.array([66,22,10.5]);dose=np.array([-42,44,31.5]);rows=[]
for (s,pid),x in m.groupby(['sensor','pid']):
 raw=pd.read_csv(ROOT/f'dataset/csv/CGMacros-{pid:03}.csv',parse_dates=['Timestamp']).set_index('Timestamp')
 def signal(id):
  r=e.loc[id];return raw[s].reindex(r.time+pd.to_timedelta(np.arange(0,181,15),unit='m')).to_numpy(float)-r[s+'_base']
 a=np.array([signal(x[x.recipe==r].iloc[0].calibration_id) for r in REC])
 for _,r in x.iterrows():
  b=signal(r.query_id);actual=e.loc[r.query_id,['Carbs','Protein','Fat']].to_numpy(float)
  for baseline in ['pre10','start']:
   aa=a.copy();bb=b.copy()
   if baseline=='start':aa-=aa[:,0,None];bb-=bb[0]
   for h in [60,120,180]:
    n=h//15+1;A=(aa[1:,:n]-aa[0,:n]).T;y=bb[:n]-aa[0,:n];scale=max(np.linalg.norm(A)/np.sqrt(3),1);A=A/scale;y=y/scale
    for prior in [0,.25]:
     for lam in [0,.01,.1,1,10,100]:
      Z=np.r_[A,np.sqrt(lam)*np.eye(3)];v=np.r_[y,np.full(3,prior)*np.sqrt(lam)]
      fit=lsq_linear(Z,v,bounds=(0,1),tol=1e-8);assert fit.success
      pred=ref+dose*fit.x;err=abs(pred-actual);row=dict(sensor=s,pid=pid,id=r.query_id,method=f'{baseline}/{h}/prior{prior}/lambda{lam}',relative_error=float((err/actual).mean()),all_three_within10=bool((err<=actual*.1+1e-9).all()))
      for k,macro in enumerate(['C','P','F']):row['actual_'+macro]=actual[k];row['predicted_'+macro]=pred[k]
      rows.append(row)
d=pd.DataFrame(rows);selected=[];choices=[]
for s,x in d.groupby('sensor'):
 for pid in x.pid.unique():
  tr=x[x.pid!=pid];te=x[x.pid==pid]
  table=tr.groupby('method').agg(hits=('all_three_within10','mean'),relative_error=('relative_error','mean')).sort_values(['hits','relative_error'],ascending=[False,True])
  best=table.index[0];chosen=te[te.method==best].copy();chosen['method']='nested_selected';selected.append(chosen);choices.append(dict(sensor=s,pid=int(pid),choice=best))
d=pd.concat([d,*selected],ignore_index=True);d.to_csv(OUT/'predictions.csv',index=False)
summary=d.groupby(['sensor','method']).agg(meals=('id','size'),hits=('all_three_within10','sum'),relative_error=('relative_error','mean')).reset_index();summary.to_csv(OUT/'summary.csv',index=False)
(OUT/'selection.json').write_text(json.dumps(choices,indent=2));print(summary[summary.method=='nested_selected'].to_string(index=False))
