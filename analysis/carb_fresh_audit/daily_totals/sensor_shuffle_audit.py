"""Within-person negative control for the fixed passive uniform ensemble."""
from pathlib import Path
import ast,json
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'sensor_shuffle_audit';OUT.mkdir(exist_ok=True)
(OUT/'PLAN.json').write_text(json.dumps({'target':'Does the fixed31-model uniform ensemble exploit correctly paired sensor days beyond personal intake averages?','control':'100 fixed-seed permutations of complete sensor feature rows within each participant, separately in64training and44later days. Preserve personal identity, labels, split, feature correlations and all outcomes. Refit unchanged models.','interpretation':'Descriptive negative control on repeatedly inspected development days. Temporal dependence and nonexchangeable daily states mean this is not a formal causal or prospective significance test. Shuffle does not show physical impossibility.','selection':'No feature or model selection, fixed uniform ensemble and seed20260908.'},indent=2))
d=pd.read_csv(ROOT/'delayed_probe/sensor_inputs.csv');h=pd.read_csv(ROOT/'delayed_probe/final_training_days.csv').merge(d,on=['pid','day']).reset_index(drop=True);q=d[d.split=='later'].reset_index(drop=True)
families={'summary':[c for c in d if c.startswith(('g_','ctx_','next_'))],'glucose':[c for c in d if c.startswith('g_') or c.startswith('next_glucose')],'sequence':[c for c in d if c.startswith(('seq_','nextseq_'))]};cols=list(dict.fromkeys(c for group in families.values() for c in group));assert 'actual' not in cols
ns=dict(np=np,families=families);tree=ast.parse((ROOT/'context_probe.py').read_text());nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['predict','score']];exec(compile(ast.Module(body=nodes,type_ignores=[]),'shared','exec'),ns);predict,score=ns['predict'],ns['score'];names=pd.read_csv(ROOT/'ensemble_probe/weights_before_evaluation.csv').candidate.tolist()
def ensemble(t,v):
 p=[]
 for name in names:
  family,kind,reg=name.split('|');p.append(predict(t,v,family,kind,float(reg)))
 return np.mean(p,axis=0)
def shuffle(frame,rng):
 z=frame.copy()
 for _,g in frame.groupby('pid'):z.loc[g.index,cols]=frame.loc[rng.permutation(g.index),cols].to_numpy()
 assert z[['pid','day','actual']].equals(frame[['pid','day','actual']]);return z
p=ensemble(h,q);previous=pd.read_csv(ROOT/'ensemble_probe/later_results.csv');assert np.allclose(p,previous.uniform,atol=1e-8,rtol=0);actual=q.actual.to_numpy();observed=score(actual,p);rows=[];rng=np.random.default_rng(20260908)
for i in range(100):
 t=shuffle(h,rng);v=shuffle(q,rng);pred=ensemble(t,v);rows.append(dict(iteration=i,**score(actual,pred)))
 if (i+1)%20==0:print(i+1,'controls complete',flush=True)
r=pd.DataFrame(rows);r.to_csv(OUT/'shuffled_scores.csv',index=False);baseline=q.pid.map(h.groupby('pid').actual.mean()).to_numpy();s=dict(observed=observed,personal_mean=score(actual,baseline),shuffled_mape_median=float(r.mape.median()),shuffled_mape_min=float(r.mape.min()),shuffled_mape_max=float(r.mape.max()),shuffled_at_least_as_good=int((r.mape<=observed['mape']).sum()),n_controls=len(r),reference_reproduced=True,all44=len(q)==44);(OUT/'summary.json').write_text(json.dumps(s,indent=2));print(json.dumps(s,indent=2))
