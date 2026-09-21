"""Passive multiscale daily glucose descriptors, earlier-only selection."""
from pathlib import Path
import ast,json
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'multiscale_daily_probe';OUT.mkdir(exist_ok=True)
(OUT/'PLAN.json').write_text(json.dumps({'scope':'Same CGMacros daily carb target,64 training days/44 later development days; no query meal times or amounts. Sensors through next06:00.','features':'Fixed glucose lag increments at15/30/60/120/240min, RMS/net positive/negative/90th percentile increments, autocorrelation; spectral power in30-60/60-120/120-240/240-480/480-1800min bands. Separate24h and30h traces. These are descriptors, not physiological carbohydrate flux estimates.','selection':'Same33 chronological earlier validation days retaining other people training pool; baseline, originalglucose, multiscale, combined; ridge/kernel regularization0.1/1/10/100/1000, MAPE thenMAE. Freeze selected settings before later scoring.','limits':'Repeatedly inspected44development days are not fresh validation.'},indent=2))
d=pd.read_csv(ROOT/'delayed_probe/sensor_inputs.csv');rows=[]
for _,r in d.iterrows():
 full=r[[f'seq_{i:02}' for i in range(96)]+[f'nextseq_{i:02}' for i in range(24)]].to_numpy(float);assert np.isfinite(full).all();z={}
 for segment,g in [('day',full[:96]),('extended',full)]:
  for lag in [1,2,4,8,16]:
   delta=g[lag:]-g[:-lag];prefix=f'ms_{segment}_lag{lag}_';z[prefix+'rms']=np.sqrt(np.mean(delta**2));z[prefix+'rise']=np.maximum(delta,0).mean();z[prefix+'fall']=np.maximum(-delta,0).mean();z[prefix+'q90']=np.percentile(abs(delta),90)
   z[prefix+'correlation']=np.corrcoef(g[lag:],g[:-lag])[0,1] if min(g[lag:].std(),g[:-lag].std())>0 else 0
  fft=np.fft.rfft(g-g.mean());power=abs(fft)**2/len(g)**2;freq=np.fft.rfftfreq(len(g),d=15);period=np.divide(1,freq,out=np.full_like(freq,np.inf),where=freq>0)
  for lo,hi in [(30,60),(60,120),(120,240),(240,480),(480,1801)]:z[f'ms_{segment}_power{lo}_{hi}']=power[(period>=lo)&(period<hi)].sum()
 rows.append(z)
d=pd.concat([d,pd.DataFrame(rows)],axis=1);d.to_csv(OUT/'sensor_inputs.csv',index=False)
old=[c for c in d if c.startswith('g_') or c.startswith('next_glucose')];new=[c for c in d if c.startswith('ms_')];families=dict(glucose=old,multiscale=new,combined=old+new)
ns=dict(np=np,families=families);tree=ast.parse((ROOT/'context_probe.py').read_text());nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['predict','score']];exec(compile(ast.Module(body=nodes,type_ignores=[]),'shared','exec'),ns);predict,score=ns['predict'],ns['score']
h=pd.read_csv(ROOT/'delayed_probe/final_training_days.csv').merge(d,on=['pid','day']);q=d[d.split=='later'];parts=[]
for idx,r in h.iterrows():
 own=h[(h.pid==r.pid)&(pd.to_datetime(h.day)+pd.Timedelta(hours=30)<=pd.Timestamp(r.day))]
 if len(own):parts.append((pd.concat([h[h.pid!=r.pid],own]),h.loc[[idx]]))
assert len(parts)==33
rows=[]
for family,kind,reg in [('baseline','baseline',0)]+[(f,k,r) for f in families for k in ['ridge','kernel'] for r in [.1,1,10,100,1000]]:
 y=[];p=[]
 for tr,v in parts:y.extend(v.actual);p.extend(predict(tr,v,family,kind,reg))
 rows.append(dict(family=family,kind=kind,reg=reg,**score(np.array(y),np.array(p))))
rank=pd.DataFrame(rows).sort_values(['mape','mae'],kind='stable');rank.to_csv(OUT/'validation.csv',index=False);best=rank.iloc[0].to_dict();(OUT/'settings.json').write_text(json.dumps(best,indent=2));p=predict(h,q,best['family'],best['kind'],best['reg']);out=q[['pid','day']].copy();out['prediction']=p;out.to_csv(OUT/'predictions_before_scoring.csv',index=False);out['actual']=q.actual;out.to_csv(OUT/'later_results.csv',index=False)
assert np.array_equal(p,predict(h,q.assign(actual=999999),best['family'],best['kind'],best['reg']))
ref=predict(h,q,'glucose','kernel',.1);assert np.allclose(ref,pd.read_csv(ROOT/'full_pool_validation/later_results.csv').prediction,atol=1e-8,rtol=0)
s={'selected':best,'later':score(q.actual.to_numpy(),p),'reference_reproduced':True,'no_query_label_dependence':True,'all44':len(out)==44};(OUT/'summary.json').write_text(json.dumps(s,indent=2));print(json.dumps(s,indent=2));print(rank.head(8).to_string(index=False))
