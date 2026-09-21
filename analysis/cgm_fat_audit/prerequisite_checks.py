"""Additional label, repeat, deployment and calendar checks; no predictive fit."""
from pathlib import Path
import json, zipfile
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'analysis/cgm_fat_audit/full_audit'
e=pd.read_csv(OUT/'events_and_features.csv');e['time']=pd.to_datetime(e.time)
bio=pd.read_csv(ROOT/'dataset/csv/bio.csv');bio.columns=bio.columns.str.strip()
assert set(e.pid)==set(bio.subject) and not bio.subject.duplicated().any()
e=e.merge(bio[['subject','A1c PDL (Lab)']],left_on='pid',right_on='subject',validate='many_to_one')
e['health']=pd.cut(e['A1c PDL (Lab)'],[-np.inf,5.699999,6.499999,np.inf],labels=['healthy','prediabetes','T2D'])
e['date']=e.time.dt.date
e['kcal_flag']=(e.Calories>0)&((e.kcal_difference/e.Calories).abs()>.2)
e['fiber_exceeds_carbs']=e.Fiber>e.Carbs
e['portion_uncertain']=e['Amount Consumed']!=100
e[e.kcal_flag|e.fiber_exceeds_carbs|e.portion_uncertain].to_csv(OUT/'label_review_queue.csv',index=False)
safe=e[(e.recipe!='other')&(e['Amount Consumed']==100)]
out={'bio_ids_match':True,'bio_missing_cells':int(bio.isna().sum().sum()),
 'fiber_exceeds_carbs':int(e.fiber_exceeds_carbs.sum()),'portion_above100':int((e['Amount Consumed']>100).sum()),
 'complete_controlled_breakfasts':len(safe),'breakfast_people':int(safe.pid.nunique())}
repeats=[];subgroups=[];adequacy=[]
for s in ['Libre GL','Dexcom GL']:
 valid=safe[safe[s+'_valid180']]
 adequacy.append({'sensor':s,'usable_events':len(valid),'people':int(valid.pid.nunique()),
  'all_three_contrasts_people':sum(set(['reference','carb_low','protein_high','fat_high']).issubset(set(x.recipe)) for _,x in valid.groupby('pid')),
  'repeat_each_four_recipes_people':sum(all((x.recipe==r).sum()>=2 for r in ['reference','carb_low','protein_high','fat_high']) for _,x in valid.groupby('pid'))})
 for rec in ['reference','carb_low','protein_high','fat_high']:
  pairs=[]
  for pid,x in valid[valid.recipe==rec].groupby('pid'):
   x=x.sort_values('time')
   if len(x)==2:pairs.append(float(abs(x.iloc[1][s+'_mean180']-x.iloc[0][s+'_mean180'])))
  repeats.append({'sensor':s,'recipe':rec,'paired_people':len(pairs),'median_abs_3h_mean_difference':float(np.median(pairs)) if pairs else None})
 for label,lo,hi in [('carbs','carb_low','reference'),('protein','reference','protein_high'),('fat','reference','fat_high')]:
  for health,x in valid.groupby('health',observed=True):
   m=x.groupby(['pid','recipe'])[s+'_mean180'].mean().unstack()
   if lo not in m or hi not in m:continue
   d=(m[hi]-m[lo]).dropna()
   subgroups.append({'sensor':s,'macro':label,'health':str(health),'people':len(d),'positive':int((d>0).sum()),'median_3h_mean_difference':float(d.median())})
out['onboarding_adequacy']=adequacy;out['repeatability']=repeats;out['health_contrasts']=subgroups
daily=[];context=[];photo=[]
zf=zipfile.ZipFile(ROOT/'dataset/cgmacros_raw/CGMacros_dateshifted365.zip')
names=set(zf.namelist());basenames={Path(x).name for x in names if x.lower().endswith(('.jpg','.jpeg','.png'))}
for f in sorted((ROOT/'dataset/csv').glob('CGMacros-*.csv')):
 pid=int(f.stem[-3:]);d=pd.read_csv(f,parse_dates=['Timestamp']);d.columns=d.columns.str.strip()
 # All calendar days, including sensor days without meal records. Boundaries are not complete study days.
 dates=pd.date_range(d.Timestamp.min().normalize(),d.Timestamp.max().normalize(),freq='D')
 for date in dates:
  x=d[d.Timestamp.dt.normalize()==date];food=e[(e.pid==pid)&(e.date==date.date())]
  daily.append({'pid':pid,'date':str(date.date()),'sensor_rows':len(x),'meal_rows':len(food),
   'has_breakfast_lunch_dinner':{'breakfast','lunch','dinner'}.issubset(set(food.meal_type)),
   'all_food_amount100':bool(len(food)>0 and (food['Amount Consumed']==100).all()),
   'any_kcal_or_fiber_flag':bool(food.kcal_flag.any() or food.fiber_exceeds_carbs.any()),
   'Libre_present_minutes':int(x['Libre GL'].notna().sum()),'Dexcom_present_minutes':int(x['Dexcom GL'].notna().sum())})
 for _,r in d[d.Carbs.notna()&d.Protein.notna()&d.Fat.notna()].iterrows():
  name=r.get('Image path'); photo.append({'pid':pid,'timestamp':str(r.Timestamp),'path':name,'basename_in_archive':bool(isinstance(name,str) and Path(name.replace('\\','/')).name in basenames)})
pd.DataFrame(daily).to_csv(OUT/'daily_completeness.csv',index=False)
pd.DataFrame(photo).to_csv(OUT/'photo_link_checks.csv',index=False)
dd=pd.DataFrame(daily);ph=pd.DataFrame(photo)
out['photo_event_rows']=len(ph);out['photo_paths_present']=int(ph.path.notna().sum());out['photo_basename_matches']=int(ph.basename_in_archive.sum())
out['calendar_days']=len(dd);out['calendar_days_without_meals']=int((dd.meal_rows==0).sum())
out['days_with_three_main_meals']=int(dd.has_breakfast_lunch_dinner.sum())
out['days_three_meals_all_amount100_no_obvious_label_flag']=int((dd.has_breakfast_lunch_dinner&dd.all_food_amount100&~dd.any_kcal_or_fiber_flag).sum())
out['note']='Calendar counts include deployment edges; three meals or a matching photograph cannot certify complete intake.'
(OUT/'additional_checks.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
