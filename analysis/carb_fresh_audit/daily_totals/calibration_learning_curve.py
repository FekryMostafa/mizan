"""Fixed passive ensemble as personal calibration history grows."""
from pathlib import Path
import ast,json
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'calibration_learning_curve';OUT.mkdir(exist_ok=True)
(OUT/'PLAN.json').write_text(json.dumps({'scope':'Same44 later CGMacros daily totals. Fixed31-member uniform passive ensemble.','history':'For each query participant retain first1/2/3/all allowed calibration days; retain every other participants original training days. Query days unchanged. No future labels or meal timestamps.','controls':'Personal mean at each history level. Levels with fewer available days use all available and are explicitly counted. No hyperparameter selection from later results.','limits':'History count and its time span co-vary. Same repeatedly inspected44development days. This measures this algorithm, not an extrapolated learning guarantee.'},indent=2))
d=pd.read_csv(ROOT/'delayed_probe/sensor_inputs.csv');h=pd.read_csv(ROOT/'delayed_probe/final_training_days.csv').merge(d,on=['pid','day']);q=d[d.split=='later'];families={'summary':[c for c in d if c.startswith(('g_','ctx_','next_'))],'glucose':[c for c in d if c.startswith('g_') or c.startswith('next_glucose')],'sequence':[c for c in d if c.startswith(('seq_','nextseq_'))]}
ns=dict(np=np,families=families);tree=ast.parse((ROOT/'context_probe.py').read_text());nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['predict','score']];exec(compile(ast.Module(body=nodes,type_ignores=[]),'shared','exec'),ns);predict,score=ns['predict'],ns['score'];names=pd.read_csv(ROOT/'ensemble_probe/weights_before_evaluation.csv').candidate.tolist()
def ensemble(t,v):
 p=[]
 for name in names:
  family,kind,reg=name.split('|');p.append(predict(t,v,family,kind,float(reg)))
 return np.mean(p,axis=0)
rows=[]
for level in [1,2,3,99]:
 for pid,v in q.groupby('pid'):
  own=h[h.pid==pid].sort_values('day').head(level);t=pd.concat([h[h.pid!=pid],own]);assert pd.Timestamp(own.day.max())+pd.Timedelta(hours=30)<=pd.Timestamp(v.day.min())
  p=ensemble(t,v);assert np.array_equal(p,ensemble(t,v.assign(actual=999999)))
  for (_,r),pred in zip(v.iterrows(),p):rows.append(dict(level='all' if level==99 else str(level),pid=int(pid),day=r.day,personal_days=len(own),training_days=len(t),actual=r.actual,prediction=float(pred),baseline=float(own.actual.mean())))
 print('history',level,'complete',flush=True)
r=pd.DataFrame(rows);r.to_csv(OUT/'predictions.csv',index=False);summary={}
for level,g in r.groupby('level',sort=False):
 assert len(g)==44
 summary[level]=dict(ensemble=score(g.actual.to_numpy(),g.prediction.to_numpy()),baseline=score(g.actual.to_numpy(),g.baseline.to_numpy()),personal_day_counts=g.drop_duplicates('pid').personal_days.value_counts().sort_index().to_dict())
a=r[r.level=='all'].merge(pd.read_csv(ROOT/'ensemble_probe/later_results.csv')[['pid','day','uniform']],on=['pid','day'],validate='one_to_one');assert np.allclose(a.prediction,a.uniform,rtol=0,atol=1e-8);summary['audit']=dict(all44_each_level=True,reference_reproduced=True,query_labels_unused=True)
(OUT/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
