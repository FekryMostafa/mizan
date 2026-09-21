"""One source-zero beverage day admitted as marked calibration sensitivity."""
from pathlib import Path
import ast,json,hashlib
import numpy as np
import pandas as pd
ROOT = str(Path(__file__).resolve().parents[3])  # repo root
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'tea_day_sensitivity';OUT.mkdir(exist_ok=True)
(OUT/'PLAN.json').write_text(json.dumps({'scope':'Add P27 2024-06-11 training day only, retain same44 queries and fixed31model uniform ensemble.','assumption':'Accept original zero macros for tea recordCGMacros-027:2388. Photo shows tea, additives unverified. No estimated macros, original daily recorded sum277g. Source files unchanged.','verification':'Reextract all required features and reproduce existing P27 rows before applying to added day. Complete30hour glucose required. Exclude query labels.','interpretation':'Sensitivity under label acceptance, not independently verified extra ground truth or a new untouched validation set.'},indent=2))
d=pd.read_csv(ROOT/'delayed_probe/sensor_inputs.csv');h=pd.read_csv(ROOT/'delayed_probe/final_training_days.csv').merge(d,on=['pid','day']);q=d[d.split=='later'];families={'summary':[c for c in d if c.startswith(('g_','ctx_','next_'))],'glucose':[c for c in d if c.startswith('g_') or c.startswith('next_glucose')],'sequence':[c for c in d if c.startswith(('seq_','nextseq_'))]};cols=list(dict.fromkeys(c for group in families.values() for c in group));ns=dict(np=np,pd=pd,families=families)
for script,names in [('context_probe.py',['predict','score']),('timing_probe.py',['features'])]:
 tree=ast.parse((ROOT/script).read_text());nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names];exec(compile(ast.Module(body=nodes,type_ignores=[]),'shared','exec'),ns)
f=Path(ROOT + '/dataset/cgmacros_clean_v1/participants/CGMacros-027.csv');digest=hashlib.sha256(f.read_bytes()).hexdigest();raw=pd.read_csv(f);raw.columns=raw.columns.str.strip();raw.index=pd.to_datetime(raw.Timestamp)
def extract(day):
 t=pd.Timestamp(day);z,n=ns['features'](raw,t,0);assert n==1800
 a=raw['Libre GL'].reindex(pd.date_range(t,periods=120,freq='15min')).to_numpy()
 for k in range(96):z[f'seq_{k:02}']=a[k]
 for k in range(24):z[f'nextseq_{k:02}']=a[k+96]
 for hours in [6,24]:
  prev=raw.reindex(pd.date_range(t-pd.Timedelta(hours=hours),periods=60*hours,freq='min'))
  for col,key in [('Libre GL','glucose'),('HR','hr'),('Calories (Activity)','activity')]:
   x=pd.to_numeric(prev[col],errors='coerce');ok=x.notna().mean()>=.9;z[f'ctx_prev{hours}_{key}_mean']=x.mean() if ok else np.nan;z[f'ctx_prev{hours}_{key}_sd']=x.std() if ok else np.nan
 for hour in range(30):
  sl=raw.reindex(pd.date_range(t+pd.Timedelta(hours=hour),periods=60,freq='min'))
  for col,key in [('HR','hr'),('Calories (Activity)','activity')]:
   x=pd.to_numeric(sl[col],errors='coerce');name=f'ctx_{key}_{hour:02}' if hour<24 else f'next_{key}_{hour-24}';z[name]=x.mean() if x.notna().mean()>=.9 else np.nan
 return z
for _,r in d[d.pid==27].iterrows():
 z=extract(r.day)
 for c in cols:assert np.isclose(z[c],r[c],rtol=0,atol=1e-8,equal_nan=True),(r.day,c,z[c],r[c])
m=pd.read_csv(ROOT + '/dataset/cgmacros_clean_v1/meals.csv');m=m[(m.participant_id==27)&m.timestamp.str.startswith('2024-06-11')];assert set(m[m.label_status!='eligible_full_consumption'].record_id)=={'CGMacros-027:2388'};assert m.carbs_reported.sum()==277
extra=pd.DataFrame([dict(pid=27,day='2024-06-11',actual=float(m.carbs_reported.sum()),**extract('2024-06-11'))]);extra.to_csv(OUT/'added_training_day.csv',index=False);assert pd.Timestamp(extra.day.iloc[0])+pd.Timedelta(hours=30)<=pd.Timestamp(q[q.pid==27].day.min());assert not ((h.pid==27)&(h.day=='2024-06-11')).any()
settings=pd.read_csv(ROOT/'ensemble_probe/weights_before_evaluation.csv').candidate.tolist()
def ensemble(tr,v):
 pp=[]
 for name in settings:
  family,kind,reg=name.split('|');pp.append(ns['predict'](tr,v,family,kind,float(reg)))
 return np.mean(pp,axis=0)
base=ensemble(h,q);assert np.allclose(base,pd.read_csv(ROOT/'ensemble_probe/later_results.csv').uniform,rtol=0,atol=1e-8);tr=pd.concat([h,extra],ignore_index=True);pred=ensemble(tr,q);assert np.array_equal(pred,ensemble(tr,q.assign(actual=999999)))
out=q[['pid','day','actual']].copy();out['reference']=base;out['added_day']=pred;out.to_csv(OUT/'later_results.csv',index=False);score=ns['score'];summary=dict(reference=score(q.actual.to_numpy(),base),sensitivity=score(q.actual.to_numpy(),pred),p27=out[out.pid==27].to_dict('records'),training_days=len(tr),all44=len(q)==44,reextraction_checked_rows=int((d.pid==27).sum()),source_unchanged=hashlib.sha256(f.read_bytes()).hexdigest()==digest,query_labels_unused=True);assert summary['source_unchanged'];(OUT/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
