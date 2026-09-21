"""Audit prediction prerequisites; no model fitting or test-set performance claims."""
from pathlib import Path
import json,hashlib
import numpy as np,pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

OUT=Path(__file__).resolve().parent/'full_audit';OUT.mkdir(exist_ok=True)
ROOT=OUT.parents[2]
SENSORS=['Libre GL','Dexcom GL']; MAC=['Carbs','Protein','Fat','Fiber']
recipes={'reference':(66,22,10.5,0),'carb_low':(24,22,10.5,0),
         'protein_high':(66,66,10.5,0),'fat_high':(66,22,42,0),
         'fiber_high':(73,22,42,7),'fat_protein_high':(73,66,42,7)}
g=np.arange(-60,361);rows=[];quality=[];traces={};allrows=[];offsets=[]
for f in sorted((ROOT/'dataset/csv').glob('CGMacros-*.csv')):
 pid=int(f.stem[-3:]);d=pd.read_csv(f,parse_dates=['Timestamp']);d.columns=d.columns.str.strip()
 if 'Amount Consumed' not in d:d['Amount Consumed']=np.nan
 d=d.set_index('Timestamp').sort_index();assert not d.index.duplicated().any()
 activity='METs' if 'METs' in d else 'Intensity' if 'Intensity' in d else None
 delta=(d.index.to_series().diff().dt.total_seconds()/60)
 q={'pid':pid,'rows':len(d),'timestamp_gaps_over1min':int((delta>1).sum()),
    'activity_column':activity,'activity_missing':float(d[activity].isna().mean()) if activity else 1,
    'HR_missing':float(d.HR.isna().mean()),'source_sha256':hashlib.sha256(f.read_bytes()).hexdigest()}
 for s in SENSORS:
  q[s+'_missing']=float(d[s].isna().mean());q[s+'_min']=float(d[s].min());q[s+'_max']=float(d[s].max())
  dif=d[s].diff();q[s+'_longest_constant_run_min']=int(d[s].groupby((dif!=0).cumsum()).count().max())
 paired=d[SENSORS].dropna();q['median_Dexcom_minus_Libre']=float((paired[SENSORS[1]]-paired[SENSORS[0]]).median())
 quality.append(q)
 food=d[d['Meal Type'].notna()|d.Calories.notna()|d.Carbs.notna()]
 bf_order=0
 for idx,(t,r) in enumerate(food.iterrows()):
  if r[MAC[:3]].isna().any():continue
  mt=str(r['Meal Type']).strip().lower();v=tuple(r[MAC])
  recipe=next((k for k,rv in recipes.items() if rv==v),'other') if mt=='breakfast' else 'other'
  if mt=='breakfast':bf_order+=1
  nextmin=(food.index[idx+1]-t).total_seconds()/60 if idx+1<len(food) else np.nan
  prevmin=(t-food.index[idx-1]).total_seconds()/60 if idx else np.nan
  rid=f'{pid:03}_{t.isoformat()}'
  e={'id':rid,'pid':pid,'time':t.isoformat(),'meal_type':mt,'recipe':recipe,'breakfast_order':bf_order if mt=='breakfast' else np.nan,
     **dict(zip(MAC,v)),'Calories':r.Calories,'Amount Consumed':r['Amount Consumed'],'next_min':nextmin,'prev_min':prevmin,
     'image_path':r.get('Image path',''),'hour':t.hour+t.minute/60,
     'macro_kcal':4*r.Carbs+4*r.Protein+9*r.Fat}
  e['kcal_difference']=e['macro_kcal']-e['Calories']
  seg=d.reindex(t+pd.to_timedelta(g,unit='m'))
  e['activity_median_3h']=float(seg.loc[(g>=0)&(g<=180),activity].median()) if activity else np.nan
  e['activity_coverage_3h']=float(seg.loc[(g>=0)&(g<=180),activity].notna().mean()) if activity else 0
  e['activity_column']=activity
  for s in SENSORS:
   a=seg[s].to_numpy(float);pre=a[(g>=-10)&(g<0)];base=float(np.nanmedian(pre)) if np.isfinite(pre).sum()>=8 else np.nan
   z=a-base;traces[(rid,s)]=z
   e[s+'_base']=base;e[s+'_slope30']=(a[g==-1][0]-a[g==-30][0])/29
   for h in [60,120,180,300]:
    mask=(g>=0)&(g<=h)
    valid=bool(np.isfinite(z[mask]).all() and (pd.isna(nextmin) or nextmin>h) and (pd.isna(prevmin) or prevmin>=180))
    e[f'{s}_valid{h}']=valid
    if valid:
     zz=z[mask];tt=g[mask]
     e[f'{s}_mean{h}']=float(np.trapezoid(zz,x=tt)/h)
     e[f'{s}_peak{h}']=float(zz.max());e[f'{s}_peak_time{h}']=int(tt[zz.argmax()])
     e[f'{s}_mean0base{h}']=float(np.trapezoid(zz-zz[0],x=tt)/h)
     if h>=180:
      m=tt>=120;e[f'{s}_tail{h}']=float(np.trapezoid(zz[m],x=tt[m])/(h-120))
  rows.append(e)

e=pd.DataFrame(rows);q=pd.DataFrame(quality)
e.to_csv(OUT/'events_and_features.csv',index=False);q.to_csv(OUT/'device_context_quality.csv',index=False)
safe=e[(e['Amount Consumed']==100)&(e.recipe!='other')]
contrasts=[('Carbs: 24 → 66 g','carb_low','reference'),('Protein: 22 → 66 g','reference','protein_high'),('Fat: 10.5 → 42 g','reference','fat_high')]
stats=[];pairs=[]
fig,axes=plt.subplots(2,3,figsize=(14,8))
for row,s in enumerate(SENSORS):
 for col,(name,low,high) in enumerate(contrasts):
  sub=safe[safe[s+'_valid180']&safe.recipe.isin([low,high])]
  ids=[pid for pid,ss in sub.groupby('pid') if ss.recipe.nunique()==2]
  feat=[s+'_mean180',s+'_peak180',s+'_peak_time180',s+'_tail180',s+'_mean0base180',s+'_base',s+'_slope30']
  means=sub.groupby(['pid','recipe'])[feat].mean()
  for pid in ids:
   diff=means.loc[(pid,high)]-means.loc[(pid,low)]
   pairs.append({'sensor':s,'contrast':name,'pid':pid,**{k:float(v) for k,v in diff.items()}})
  st={'sensor':s,'contrast':name,'paired_people':len(ids),'usable_low_events':int((sub.recipe==low).sum()),'usable_high_events':int((sub.recipe==high).sum())}
  for ff in feat:
   dd=np.array([means.loc[(pid,high),ff]-means.loc[(pid,low),ff] for pid in ids])
   st[ff+'_median_difference']=float(np.median(dd));st[ff+'_positive_people']=int((dd>0).sum())
  stats.append(st)
  for rec,color in [(low,'#2869aa'),(high,'#d27922')]:
   arr=np.array([np.mean([traces[(rid,s)][(g>=0)&(g<=180)] for rid in sub[(sub.pid==pid)&(sub.recipe==rec)].id],axis=0) for pid in ids])
   axes[row,col].plot(np.arange(181),arr.mean(axis=0),color=color,label=rec.replace('_',' '))
  axes[row,col].set(title=f'{name}\n{s}, {len(ids)} paired people',xlabel='Minutes after breakfast',ylabel='Glucose change (mg/dL)');axes[row,col].legend(fontsize=8);axes[row,col].grid(alpha=.15)
fig.suptitle('Single-macro contrasts: other labeled macros held fixed',fontsize=15)
fig.tight_layout(rect=[0,0,1,.95]);fig.savefig(OUT/'three_macro_contrasts.png',dpi=150);plt.close(fig)
pd.DataFrame(pairs).to_csv(OUT/'within_person_macro_contrasts.csv',index=False)

# Cross-device agreement at meal-response level, not interchangeability assumed.
both=e[e[SENSORS[0]+'_valid180']&e[SENSORS[1]+'_valid180']]
agreement={}
for feat in ['mean180','peak180','peak_time180']:
 a=both[SENSORS[0]+'_'+feat];b=both[SENSORS[1]+'_'+feat]
 agreement[feat]={'n':len(both),'pearson':float(a.corr(b)),'median_abs_difference':float((b-a).abs().median())}

# Find within-person curve collisions among distinct known breakfast recipes.
# Exploratory search on all eligible examples; not a held-out test or fitted classifier.
collisions=[]
for s in SENSORS:
 for pid,sub in safe[safe[s+'_valid180']].groupby('pid'):
  ss=list(sub.itertuples(index=False));keep=(g>=0)&(g<=180)&(g%15==0)
  for i,a in enumerate(ss):
   for b in ss[i+1:]:
    if a.recipe==b.recipe:continue
    za=traces[(a.id,s)][keep];zb=traces[(b.id,s)][keep]
    rmse=float(np.sqrt(np.mean((za-zb)**2)))
    collisions.append({'sensor':s,'pid':pid,'id_a':a.id,'id_b':b.id,'recipe_a':a.recipe,'recipe_b':b.recipe,
                       'curve_RMSE_mgdl':rmse,'carb_difference':abs(a.Carbs-b.Carbs),'protein_difference':abs(a.Protein-b.Protein),'fat_difference':abs(a.Fat-b.Fat)})
collisions=pd.DataFrame(collisions).sort_values('curve_RMSE_mgdl');collisions.to_csv(OUT/'different_recipe_similar_curves.csv',index=False)
collisions=collisions[(collisions.carb_difference>=20)|(collisions.protein_difference>=20)|(collisions.fat_difference>=20)]
fig,axes=plt.subplots(2,3,figsize=(13,7))
for row,s in enumerate(SENSORS):
 cases=collisions[collisions.sensor==s].drop_duplicates('pid').head(3)
 for col,(_,a) in enumerate(cases.iterrows()):
  ax=axes[row,col]
  for idd in [a.id_a,a.id_b]:
   z=e[e.id==idd].iloc[0]
   ax.plot(g,traces[(idd,s)],label=f'{z.Carbs:g}C/{z.Protein:g}P/{z.Fat:g}F')
  ax.set(xlim=(0,180),title=f'{s}, P{a.pid}; RMSE {a.curve_RMSE_mgdl:.1f}',xlabel='Minutes',ylabel='Glucose change');ax.legend(fontsize=8)
fig.suptitle('Closest different-macro curves found by an explicit exploratory search')
fig.tight_layout(rect=[0,0,1,.95]);fig.savefig(OUT/'similar_curves_different_macros.png',dpi=150);plt.close(fig)

summary={'event_count':len(e),'meal_types':e.meal_type.value_counts().to_dict(),
 'amount_consumed_counts':e['Amount Consumed'].fillna('missing').value_counts().to_dict(),
 'macro_ranges':{c:{'min':float(e[c].min()),'max':float(e[c].max())} for c in MAC},
 'calorie_mismatch_over20percent':int(((e.Calories>0)&((e.kcal_difference/e.Calories).abs()>.2)).sum()),
 'matched_recipe_counts_all':e[e.recipe!='other'].recipe.value_counts().to_dict(),
 'matched_recipe_counts_100percent':safe.recipe.value_counts().to_dict(),
 'contrasts':stats,'sensor_agreement':agreement,
 'next_logged_food_within_minutes':{str(h):int((e.next_min<=h).sum()) for h in [30,60,120,180,300]},
 'late_missing_or_overlapping':{s:int((~e[s+'_valid300']).sum()) for s in SENSORS},
 'median_participant_sensor_offset':float(q.median_Dexcom_minus_Libre.median()),
 'activity_header_counts':q.activity_column.value_counts().to_dict(),
 'both_activity_HR_low_missing':int(((q.activity_missing<.1)&(q.HR_missing<.1)).sum()),
 'total_timestamp_gaps':int(q.timestamp_gaps_over1min.sum()),
 'collision_count_RMSE_under5':int((collisions.curve_RMSE_mgdl<5).sum()),
 'no_model_trained':True}
(OUT/'summary.json').write_text(json.dumps(summary,indent=2,allow_nan=False))
print(json.dumps(summary,indent=2))
