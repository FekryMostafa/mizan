from pathlib import Path
import hashlib,json
import numpy as np
import pandas as pd
ROOT = str(Path(__file__).resolve().parents[3])  # repo root

O=Path(__file__).resolve().parent;B=O.parent
R=Path(ROOT + '/dataset/cgmacros_clean_v1')
formula_path=B/'formula_build_52/formula.json'
frozen_bytes=formula_path.read_bytes();j=json.loads(frozen_bytes);model=j['steps'][-1]
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in j['source_hashes'].items())
training=pd.read_csv(B/'formula_build/formula_inputs.csv',parse_dates=['time'])
reference=pd.read_csv(B/'libre_features.csv',parse_dates=['time'])
meals=pd.read_csv(R/'meals.csv',parse_dates=['timestamp'])
measured=pd.read_csv(B/'formula_build/measured_inputs.csv')
cols=list(j['scaling']['means']);gcols=['peak','area_0_60','area_60_120','area_120_180','peak_time','rise_0_30']
floors={c:max(.25*np.median([abs(z.set_index('role').loc['high_calibration',c]-z.set_index('role').loc['low_calibration',c]) for _,z in measured.groupby('pid')]),1e-6) for c in gcols}
cutoffs=training.groupby('pid').time.max()+pd.Timedelta(hours=3)
plan={'formula_sha256':hashlib.sha256(frozen_bytes).hexdigest(),
      'selection':'All logged meals from fitted people strictly after the end of their last fitted three-hour response. Full-consumption label and isolated complete Libre response required; complete uncensored ten-minute premeal baseline required.',
      'prediction':'Frozen 42-term formula, frozen scaling/imputation, original two personal calibration meals. No refitting or coefficient selection.',
      'scoring':'Absolute gram error, per-meal relative error for positive carbs, within 10 percent; zero-carb rows reported separately.',
      'cutoffs':{str(p):t.isoformat() for p,t in cutoffs.items()},
      'limitations':'Later meals excluded from this formula fit, not a pristine never-inspected dataset; known timestamps and earlier meal-label quality information are supplied.'}
(O/'PLAN.json').write_text(json.dumps(plan,indent=2));(O/'frozen_formula.json').write_bytes(frozen_bytes)
data={};anchors={};audit=[];eligible=[]
for pid in cutoffs.index:
 path=R/'participants'/f'CGMacros-{pid:03d}.csv'
 d=pd.read_csv(path);d.columns=d.columns.str.strip();d.Timestamp=pd.to_datetime(d.Timestamp,format='mixed');d=d.set_index('Timestamp');assert d.index.is_unique;data[pid]=d
 z=meals[(meals.participant_id==pid)&(meals.timestamp>cutoffs[pid])]
 for r in z.itertuples():
  reasons=[]
  if r.label_status!='eligible_full_consumption':reasons.append('label_needs_review')
  if not r.response3h_libre_complete:reasons.append('response_incomplete')
  if r.response3h_libre_bound_present:reasons.append('response_at_device_bound')
  if r.other_meal_record_within3h:reasons.append('another_meal_within3h')
  pre=d['Libre GL'].reindex(pd.date_range(r.timestamp-pd.Timedelta(minutes=10),periods=10,freq='min'))
  if not np.isfinite(pre).all():reasons.append('baseline_incomplete')
  if pre.le(40).any() or pre.ge(400).any():reasons.append('baseline_at_device_bound')
  audit.append(dict(record_id=r.record_id,pid=pid,time=r.timestamp,meal_type=r.meal_type,eligible=not reasons,reasons=';'.join(reasons)))
  if not reasons:eligible.append((pid,r.timestamp,r.record_id))
pd.DataFrame(audit).to_csv(O/'eligibility.csv',index=False)
assert eligible

def observations(pid,time):
 d=data[pid];g=d['Libre GL'].reindex(pd.date_range(time-pd.Timedelta(minutes=10),time+pd.Timedelta(minutes=180),freq='5min')).to_numpy(float)
 assert np.isfinite(g).all()
 baseline=g[:2].mean();y=g[2:]-baseline;p=np.maximum(y,0)
 out=dict(baseline=baseline,peak=max(y),peak_time=float(np.argmax(y)*5),rise_0_30=float((y[6]-y[0])/30))
 for start,end in [(0,60),(60,120),(120,180)]:out[f'area_{start}_{end}']=float(np.trapezoid(p[start//5:end//5+1],dx=5))
 for name,aa,bb in [('pre24',-1440,0),('pre6',-360,0),('pre1',-60,0),('early',0,60),('middle',60,120),('late',120,180)]:
  w=d.reindex(pd.date_range(time+pd.Timedelta(minutes=aa),periods=bb-aa,freq='min'))
  for col,key in [('Libre GL','glucose'),('HR','hr'),('Calories (Activity)','activity')]:
   v=w[col];cov=v.notna().mean();out[f'{name}_{key}_coverage']=cov;out[f'{name}_{key}']=float(v.mean()) if cov>=.9 else np.nan
 prior=meals[(meals.participant_id==pid)&(meals.timestamp>=time-pd.Timedelta(hours=24))&(meals.timestamp<time)]
 out['prior_food_review']=float(prior.label_status.ne('eligible_full_consumption').any())
 return out,y

for pid in cutoffs.index:
 anchors[pid]=[]
 for role in ['low_calibration','high_calibration']:
  time=reference[(reference.pid==pid)&reference.role.eq(role)].iloc[0].time
  anchors[pid].append(observations(pid,time))

def inputs(pid,time):
 (lo,yl),(hi,yh)=anchors[pid];q,y=observations(pid,time);delta=yh-yl
 base=max(0,24+42*float(np.dot(y-yl,delta)/max(np.dot(delta,delta),1e-8)))
 out=dict(pid=pid,time=time,base=base)
 for c in gcols:
  diff=hi[c]-lo[c];den=(-1 if diff<0 else 1)*max(abs(diff),floors[c]);out['personal_'+c]=(q[c]-(lo[c]+hi[c])/2)/den
 for origin in ['start','minimum']:
  norm=[]
  for yy in [yl,yh,y]:
   yy=yy-(yy[0] if origin=='start' else min(yy));norm.append(yy/max(np.linalg.norm(yy),1e-8))
  dl=np.linalg.norm(norm[2]-norm[0]);dh=np.linalg.norm(norm[2]-norm[1]);out['shape_'+origin]=(dl-dh)/max(dl+dh,1e-8)
 out['baseline_difference']=q['baseline']-(lo['baseline']+hi['baseline'])/2
 for c,v in q.items():
  if c.startswith(('pre24_','pre6_','pre1_','early_','middle_','late_')):out[c]=v
 out['prior_food_review']=q['prior_food_review']
 return out

def predict(frame):
 x=frame[cols].to_numpy(float)
 med=np.array([j['scaling']['medians'][c] for c in cols]);mu=np.array([j['scaling']['means'][c] for c in cols]);sd=np.array([j['scaling']['scales'][c] for c in cols])
 z=(np.where(np.isfinite(x),x,med)-mu)/sd
 pred=frame.base.to_numpy()+model['coef'][0];contributions={}
 for name,weight in zip(model['terms'],model['coef'][1:]):
  v=np.ones(len(frame))
  for comp in j['definitions'][name]:v*=z[:,cols.index(comp)]
  contributions[name]=v*weight;pred+=v*weight
 return np.maximum(0,pred),pd.DataFrame(contributions)

# Verify adapter on the original 52 before applying it to later meals.
replay=pd.DataFrame([inputs(r.pid,r.time) for r in training.itertuples()])
assert np.allclose(replay[cols].to_numpy(float),training[cols].to_numpy(float),atol=1e-8,rtol=0,equal_nan=True)
replayed,_=predict(replay)
old=pd.read_csv(B/'formula_build_52/final_predictions.csv',parse_dates=['time'])
check=training[['pid','time']].merge(old,on=['pid','time'],validate='one_to_one');assert np.allclose(replayed,check.predicted,atol=1e-8,rtol=0)
features=pd.DataFrame([dict(**inputs(pid,time),record_id=rid) for pid,time,rid in eligible]);features.to_csv(O/'prediction_inputs.csv',index=False)
values,contrib=predict(features)
blind=features[['record_id','pid','time']].copy();blind['predicted_carbs_g']=values
# Save predictions before joining the target answers for scoring.
blind.to_csv(O/'predictions_before_scoring.csv',index=False)
prediction_hash=hashlib.sha256((O/'predictions_before_scoring.csv').read_bytes()).hexdigest()
contrib.insert(0,'record_id',features.record_id);contrib.to_csv(O/'term_contributions.csv',index=False)
scored=blind.merge(meals[['record_id','meal_type','carbs_g','protein_g','fat_g','fiber_g','pre24h_food_record_needs_review','quality_flags']],on='record_id',validate='one_to_one')
scored['error_g']=abs(scored.predicted_carbs_g-scored.carbs_g)
scored['relative_error_pct']=np.where(scored.carbs_g>0,100*scored.error_g/scored.carbs_g,np.nan)
scored['within10']=np.where(scored.carbs_g>0,scored.error_g<=.1*scored.carbs_g,False)
scored.to_csv(O/'scored_predictions.csv',index=False)
summary=[]
groups={'all_positive_carb':scored[scored.carbs_g>0],'breakfast':scored[(scored.carbs_g>0)&scored.meal_type.eq('breakfast')],
 'other_meals':scored[(scored.carbs_g>0)&~scored.meal_type.eq('breakfast')],
 'doses_other_than_24_66':scored[(scored.carbs_g>0)&~scored.carbs_g.isin([24,66])]}
for name,z in groups.items():
 summary.append(dict(group=name,n=len(z),people=z.pid.nunique(),hits=int(z.within10.sum()),mae=float(z.error_g.mean()),median_error_g=float(z.error_g.median()),carbs_min=float(z.carbs_g.min()),carbs_max=float(z.carbs_g.max())))
s=pd.DataFrame(summary);s.to_csv(O/'summary.csv',index=False)
assert formula_path.read_bytes()==frozen_bytes
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in j['source_hashes'].items())
(O/'VERIFICATION.json').write_text(json.dumps(dict(training_replay_matches=True,frozen_formula_unchanged=True,source_hashes_unchanged=True,predictions_before_scoring_sha256=prediction_hash,examined_later_records=len(audit),eligible=len(eligible),zero_carb_count=int(scored.carbs_g.eq(0).sum())),indent=2))
print(s.to_string(index=False));print(scored[['pid','time','meal_type','carbs_g','predicted_carbs_g','error_g']].round(2).to_string(index=False))
