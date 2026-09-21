"""Fixed convex ensemble from earlier predictions; later-range diagnostic."""
from pathlib import Path
import ast,json
import numpy as np
import pandas as pd
from scipy.optimize import linprog
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'ensemble_probe';OUT.mkdir(exist_ok=True)
(OUT/'PLAN.json').write_text(json.dumps(dict(target='Same44 later CGMacros daily carbohydrate totals',ensemble='Nonnegative weights summing to1, each <=.25, fit to minimize absolute percentage error on33 earlier validation predictions. No weight tuning on later data.',control='Uniform mean of same31 candidates',diagnostic='After scoring, compute whether even arbitrary per-day convex combinations can fall within10%. Diagnostic uses answers and is not achievable model performance.',limits='Many candidate weights relative to33 days; ensemble calibration fit is optimistic. Later set repeatedly exposed. Restricted to existing model family, not a CGM information limit.'),indent=2))
v=pd.read_csv(ROOT/'full_pool_validation/validation_predictions.csv')
v['candidate']=v.family+'|'+v.kind+'|'+v.reg.astype(str)
wide=v.pivot(index=['pid','day','actual'],columns='candidate',values='prediction'); assert wide.notna().all().all()
names=list(wide.columns);a=wide.to_numpy();y=wide.index.get_level_values('actual').to_numpy();n,k=a.shape
# Minimize average absolute relative residual, with a simplex constraint.
rel=a/y[:,None]
c=np.r_[np.zeros(k),np.ones(n)/n]
upper=np.vstack([np.column_stack([rel,-np.eye(n)]),np.column_stack([-rel,-np.eye(n)])]);bounds=np.r_[np.ones(n),-np.ones(n)]
sol=linprog(c,A_ub=upper,b_ub=bounds,A_eq=np.array([np.r_[np.ones(k),np.zeros(n)]]),b_eq=[1.],bounds=[(0,.25)]*k+[(0,None)]*n,method='highs')
assert sol.success;w=sol.x[:k];assert abs(w.sum()-1)<1e-8 and w.min()>=-1e-8 and w.max()<=.25000001
pd.DataFrame(dict(candidate=names,weight=w)).to_csv(OUT/'weights_before_evaluation.csv',index=False)
d=pd.read_csv(ROOT/'delayed_probe/sensor_inputs.csv');h=pd.read_csv(ROOT/'delayed_probe/final_training_days.csv').merge(d,on=['pid','day']);q=d[d.split=='later']
families={'summary':[c for c in d if c.startswith(('g_','ctx_','next_'))], 'glucose':[c for c in d if c.startswith('g_') or c.startswith('next_glucose')], 'sequence':[c for c in d if c.startswith(('seq_','nextseq_'))]}
ns=dict(np=np,families=families);tree=ast.parse((ROOT/'context_probe.py').read_text());nodes=[z for z in tree.body if isinstance(z,ast.FunctionDef) and z.name in ['predict','score']];exec(compile(ast.Module(body=nodes,type_ignores=[]),'functions','exec'),ns);predict,score=ns['predict'],ns['score']
pred=[]
for name in names:
    family,kind,reg=name.split('|');pred.append(predict(h,q,family,kind,float(reg)))
matrix=np.column_stack(pred);p=matrix@w
allp=q[['pid','day']].copy();allp=pd.concat([allp.reset_index(drop=True),pd.DataFrame(matrix,columns=names)],axis=1);allp.to_csv(OUT/'candidate_predictions_before_scoring.csv',index=False)
r=q[['pid','day']].copy();r['ensemble']=p;r['uniform']=matrix.mean(1);r.to_csv(OUT/'predictions_before_scoring.csv',index=False)
r['actual']=q.actual.to_numpy();r['min_candidate']=matrix.min(1);r['max_candidate']=matrix.max(1)
r['any_convex_combination_within10']=(r.max_candidate>=.9*r.actual)&(r.min_candidate<=1.1*r.actual)
r['ensemble_ape']=100*abs(r.ensemble-r.actual)/r.actual;r.to_csv(OUT/'later_results.csv',index=False)
summary=dict(earlier_ensemble_fit=score(y,a@w),later_ensemble=score(r.actual.to_numpy(),p),later_uniform=score(r.actual.to_numpy(),r.uniform.to_numpy()),oracle_convex_range_coverage_days=int(r.any_convex_combination_within10.sum()),oracle_inaccessible_days=int((~r.any_convex_combination_within10).sum()),positive_weights=int((w>1e-9).sum()),all44=len(r)==44)
(OUT/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2));print(r[~r.any_convex_combination_within10][['pid','day','actual','min_candidate','max_candidate']].to_string(index=False))
