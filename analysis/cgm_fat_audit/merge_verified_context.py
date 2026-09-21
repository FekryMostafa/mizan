"""Replace only affected activity-context results, preserving earlier raw results."""
from pathlib import Path
import json
import numpy as np,pandas as pd
ROOT=Path(__file__).resolve().parents[2];P=ROOT/'analysis/cgm_fat_audit';OUT=P/'shape_probe_verified';OUT.mkdir(exist_ok=True)
old=pd.read_csv(P/'shape_probe/predictions.csv');new=pd.read_csv(P/'shape_probe_context_verified/predictions.csv')
base=old[~old.method.str.startswith(('context','nested'))];new=new[new.method.str.startswith('context')];fixed=pd.concat([base,new],ignore_index=True)
a=json.load(open(P/'shape_probe/selection.json'));b={(x['sensor'],x['pid']):x for x in json.load(open(P/'shape_probe_context_verified/selection.json'))};selection=[];rows=[]
for x in a:
 key=(x['sensor'],x['pid']);scores=x['inner_scores'].copy();scores.update({k:v for k,v in b[key]['inner_scores'].items() if k.startswith('context')})
 for mode in ['nested_selected','nested_glucose_only']:
  options=[k for k in scores if mode!='nested_glucose_only' or not k.startswith('context')];best=max(options,key=scores.get)
  z=fixed[(fixed.sensor==key[0])&(fixed.pid==key[1])&(fixed.method==best)].copy();assert len(z)==4;z['method']=mode;rows.append(z)
  selection.append(dict(sensor=key[0],pid=key[1],mode=mode,selected=best,inner_scores=scores))
d=pd.concat([fixed,*rows],ignore_index=True);d.to_csv(OUT/'predictions.csv',index=False);res=[]
for (sensor,method),x in d.groupby(['sensor','method']):
 assert not x.id.duplicated().any();actual=x[['actual_C','actual_P','actual_F']].to_numpy();pred=x[['predicted_C','predicted_P','predicted_F']].to_numpy();ae=abs(actual-pred);hit=(ae<=actual*.1+1e-9)
 assert np.array_equal(hit.all(axis=1),x.all_three_within10)
 res.append(dict(sensor=sensor,method=method,meals=len(x),hits=int(hit.all(axis=1).sum()),MAE=ae.mean(axis=0).tolist(),macro_hits=hit.sum(axis=0).tolist()))
(OUT/'summary.json').write_text(json.dumps(res,indent=2));(OUT/'selection.json').write_text(json.dumps(selection,indent=2));print(json.dumps([x for x in res if x['method'].startswith('nested')],indent=2))
