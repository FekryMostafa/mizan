"""Robust aggregation after detecting extreme daily component predictions."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'robust_ensemble_probe';OUT.mkdir(exist_ok=True)
(OUT/'PLAN.json').write_text(json.dumps({'scope':'Same31 fixed candidate models, original33earlier predictions and44later outcomes.','hypothesis':'Very low or high component predictions may dominate uniform mean.','rules':['original mean','median','trim3 at each tail then mean','trim6 at each tail then mean','winsorize3 each tail then mean'],'selection':'Earlier33daily MAPE thenMAE only, freeze rule before later scoring. No per-person or failure-specific choice.','limitations':'Post hoc hypothesis from inspected failures; same development set, not fresh validation. Robustification does not prove biological conversion.'},indent=2))
v=pd.read_csv(ROOT/'full_pool_validation/validation_predictions.csv');v['candidate']=v.family+'|'+v.kind+'|'+v.reg.astype(str);wide=v.pivot(index=['pid','day','actual'],columns='candidate',values='prediction');x=wide.to_numpy();y=wide.index.get_level_values('actual').to_numpy();names=list(wide.columns)
def aggregate(x,rule):
 s=np.sort(x,axis=1)
 if rule=='mean':return x.mean(1)
 if rule=='median':return np.median(x,axis=1)
 if rule=='trim3':return s[:,3:-3].mean(1)
 if rule=='trim6':return s[:,6:-6].mean(1)
 return np.clip(x,s[:,3,None],s[:,-4,None]).mean(1)
def score(y,p):
 e=abs(y-p);return dict(n=len(y),hits=int((e<=.1*y).sum()),mape=float((e/y).mean()*100),mae=float(e.mean()))
rank=pd.DataFrame([dict(rule=r,**score(y,aggregate(x,r))) for r in ['mean','median','trim3','trim6','winsor3']]).sort_values(['mape','mae'],kind='stable');rank.to_csv(OUT/'validation.csv',index=False);rule=rank.iloc[0].rule;(OUT/'settings.json').write_text(json.dumps({'rule':rule},indent=2));later=pd.read_csv(ROOT/'ensemble_probe/candidate_predictions_before_scoring.csv');old=pd.read_csv(ROOT/'ensemble_probe/later_results.csv');assert later[['pid','day']].equals(old[['pid','day']]);p=aggregate(later[names].to_numpy(),rule);assert np.allclose(aggregate(later[names].to_numpy(),'mean'),old.uniform,atol=1e-8,rtol=0);out=later[['pid','day']].copy();out['prediction']=p;out.to_csv(OUT/'predictions_before_scoring.csv',index=False);out['actual']=old.actual;out.to_csv(OUT/'later_results.csv',index=False);s=dict(selected=rule,validation=rank.iloc[0].to_dict(),later=score(old.actual.to_numpy(),p),reference_reproduced=True,all44=len(out)==44);(OUT/'summary.json').write_text(json.dumps(s,indent=2));print(rank.to_string(index=False));print(json.dumps(s,indent=2))
