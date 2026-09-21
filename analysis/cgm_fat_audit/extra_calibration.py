"""Does additional labeled onboarding resolve day-to-day drift? Same-query controls."""
from pathlib import Path
import json
import numpy as np,pandas as pd
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'analysis/cgm_fat_audit/extra_calibration';OUT.mkdir(exist_ok=True)
e=pd.read_csv(ROOT/'analysis/cgm_fat_audit/full_audit/events_and_features.csv',parse_dates=['time']).set_index('id')
m=pd.read_csv(ROOT/'analysis/cgm_fat_audit/separability/repeat_matches.csv');m=m[(m.baseline=='pre10')&(m.minutes==180)]
REC=['reference','carb_low','protein_high','fat_high'];rows=[]
for (sensor,pid),x in m.groupby(['sensor','pid']):
 raw=pd.read_csv(ROOT/f'dataset/csv/CGMacros-{pid:03}.csv',parse_dates=['Timestamp']).set_index('Timestamp')
 def signal(id):
  r=e.loc[id];return raw[sensor].reindex(r.time+pd.to_timedelta(np.arange(0,181,15),unit='m')).to_numpy(float)-r[sensor+'_base']
 a=np.array([signal(x[x.recipe==r].iloc[0].calibration_id) for r in REC])
 later=sorted(x.query_id,key=lambda id:e.loc[id].time)
 for k in [0,1,2,3]:
  known=later[:k];test=later[k:];updated=a.copy();before=[];after=[]
  for id in known:
   j=REC.index(e.loc[id].recipe);z=signal(id);updated[j]=z;before.append(a[j]);after.append(z)
  shifted=a.copy();affine=a.copy()
  if k:
   shifted=a+np.mean(np.array(after)-np.array(before),axis=0)
   xx=np.array(before).flatten();yy=np.array(after).flatten();gain,bias=np.linalg.lstsq(np.c_[xx,np.ones(len(xx))],yy,rcond=None)[0]
   gain=np.clip(gain,.25,4);affine=a*gain+bias
  for id in test:
   b=signal(id);actual=REC.index(e.loc[id].recipe)
   for method,templates in [('original',a),('latest_same_recipe',updated),('common_curve_shift',shifted),('common_gain_offset',affine)]:
    for metric in ['amplitude','shape']:
     aa=templates.copy();bb=b.copy()
     if metric=='shape':aa/=np.maximum(np.linalg.norm(aa,axis=1,keepdims=True),1);bb/=max(np.linalg.norm(bb),1)
     pred=int(np.argmin(((aa-bb)**2).mean(axis=1)))
     rows.append(dict(sensor=sensor,pid=pid,extra_known=k,id=id,method=method,metric=metric,correct=pred==actual,predicted_recipe=REC[pred],actual_recipe=REC[actual]))
d=pd.DataFrame(rows);d.to_csv(OUT/'all_results.csv',index=False)
s=d.groupby(['sensor','extra_known','method','metric']).correct.agg(['size','sum','mean']).reset_index();s.to_csv(OUT/'summary.csv',index=False)
print(s[s.extra_known.isin([1,2])].to_string(index=False))
