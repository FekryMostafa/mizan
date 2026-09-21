"""Paired within-person shuffle controls for glucose and HR/activity."""
from pathlib import Path
import ast,json
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'sensor_group_audit';OUT.mkdir(exist_ok=True)
(OUT/'PLAN.json').write_text(json.dumps({'target':'Separate dependence of fixed uniform ensemble on glucose and HR/activity day pairing','controls':'100 same-seed paired permutations per group, within person separately in training/later. Shuffle all glucose features together or all HR/activity features together. Refit unchanged31 models. Other group unchanged.','limits':'Descriptive development-set audit, not causal attribution. Shuffling one group disrupts cross-sensor coherence and may create unrealistic combinations. No model selection or claimed percentage improvement from a shuffled run.'},indent=2))
d=pd.read_csv(ROOT/'delayed_probe/sensor_inputs.csv');h=pd.read_csv(ROOT/'delayed_probe/final_training_days.csv').merge(d,on=['pid','day']).reset_index(drop=True);q=d[d.split=='later'].reset_index(drop=True)
families={'summary':[c for c in d if c.startswith(('g_','ctx_','next_'))],'glucose':[c for c in d if c.startswith('g_') or c.startswith('next_glucose')],'sequence':[c for c in d if c.startswith(('seq_','nextseq_'))]};allcols=list(dict.fromkeys(c for group in families.values() for c in group));glucose=[c for c in allcols if c.startswith(('g_','seq_','nextseq_')) or 'glucose' in c];activity=[c for c in allcols if c not in glucose];assert all('hr' in c or 'activity' in c for c in activity)
ns=dict(np=np,families=families);tree=ast.parse((ROOT/'context_probe.py').read_text());nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['predict','score']];exec(compile(ast.Module(body=nodes,type_ignores=[]),'shared','exec'),ns);predict,score=ns['predict'],ns['score'];names=pd.read_csv(ROOT/'ensemble_probe/weights_before_evaluation.csv').candidate.tolist()
def ensemble(t,v):
 p=[]
 for name in names:
  family,kind,reg=name.split('|');p.append(predict(t,v,family,kind,float(reg)))
 return np.mean(p,axis=0)
def shuffle(frame,rng,cols):
 z=frame.copy()
 for _,g in frame.groupby('pid'):z.loc[g.index,cols]=frame.loc[rng.permutation(g.index),cols].to_numpy()
 unchanged=[c for c in frame if c not in cols];assert z[unchanged].equals(frame[unchanged]);return z
actual=q.actual.to_numpy();p=ensemble(h,q);assert np.allclose(p,pd.read_csv(ROOT/'ensemble_probe/later_results.csv').uniform,atol=1e-8,rtol=0);observed=score(actual,p);rows=[];summary={'observed':observed,'controls':{}}
for group,cols in [('glucose',glucose),('hr_activity',activity)]:
 rng=np.random.default_rng(20260908)
 for i in range(100):
  t=shuffle(h,rng,cols);v=shuffle(q,rng,cols);pred=ensemble(t,v);rows.append(dict(group=group,iteration=i,**score(actual,pred)))
  if (i+1)%25==0:print(group,i+1,'complete',flush=True)
 r=pd.DataFrame([x for x in rows if x['group']==group]);summary['controls'][group]=dict(feature_count=len(cols),median_mape=float(r.mape.median()),min_mape=float(r.mape.min()),max_mape=float(r.mape.max()),at_least_as_good=int((r.mape<=observed['mape']).sum()),n=len(r))
pd.DataFrame(rows).to_csv(OUT/'shuffled_scores.csv',index=False);summary['audit']=dict(all44=len(q)==44,reference_reproduced=True,untouched_columns_exact=True);(OUT/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
