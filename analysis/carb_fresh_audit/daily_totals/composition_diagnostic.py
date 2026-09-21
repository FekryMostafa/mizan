"""Non-deployable known-composition diagnostic; never a passive accuracy claim."""
from pathlib import Path
import ast,json
import numpy as np
import pandas as pd
ROOT = str(Path(__file__).resolve().parents[3])  # repo root
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'composition_diagnostic';OUT.mkdir(exist_ok=True)
d=pd.read_csv(ROOT/'delayed_probe/sensor_inputs.csv');m=pd.read_csv(ROOT + '/dataset/cgmacros_clean_v1/meals.csv');m['day']=pd.to_datetime(m.timestamp).dt.strftime('%Y-%m-%d')
tot=m.groupby(['participant_id','day'])[['fat_g','protein_g','fiber_g','carbs_g']].sum(min_count=1).reset_index().rename(columns={'participant_id':'pid','fat_g':'known_fat','protein_g':'known_protein','fiber_g':'known_fiber','carbs_g':'check_carbs'})
d=d.merge(tot,on=['pid','day'],validate='one_to_one');assert np.allclose(d.actual,d.check_carbs)
d=d.drop(columns='check_carbs');d.to_csv(OUT/'diagnostic_inputs.csv',index=False)
sensor=[c for c in d if c.startswith(('g_','ctx_','next_'))];food=['known_fat','known_protein','known_fiber']
families={'sensors':sensor,'known_composition':food,'combined':sensor+food}
(OUT/'PLAN.json').write_text(json.dumps(dict(target='Explain existing CGMacros daily errors; not a deployable model',arms='sensors; known daily fat/protein/fiber; combined',selection='Same64 earlier training days,29 earlier validation days,44 later evaluation days. Ridge/kernel, .1/1/10/100/1000; each arm independently selected by earlier MAPE thenMAE.',interpretation='Food-only control detects dietary co-occurrence, so better combined predictions would not prove physiological compensation. No calorie field or carbohydrate-derived features.'),indent=2))
ns=dict(np=np,families=families);tree=ast.parse((ROOT/'context_probe.py').read_text());nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['predict','score']];exec(compile(ast.Module(body=nodes,type_ignores=[]),'functions','exec'),ns);predict,score=ns['predict'],ns['score']
h=pd.read_csv(ROOT/'delayed_probe/final_training_days.csv').merge(d,on=['pid','day']);q=d[d.split=='later'];folds=pd.read_csv(ROOT/'delayed_probe/folds.csv');parts=[]
for _,f in folds.groupby('fold'):
 t=f[f.role=='fit'][['pid','day']].merge(d,on=['pid','day']);v=f[f.role=='validate'][['pid','day']].merge(d,on=['pid','day']);parts.append((t,v))
selections={};candidates=[];result=q[['pid','day']].copy()
for arm in families:
 rows=[]
 for kind in ['ridge','kernel']:
  for reg in [.1,1,10,100,1000]:
   yy=[];pp=[]
   for t,v in parts:yy.extend(v.actual);pp.extend(predict(t,v,arm,kind,reg))
   rows.append(dict(arm=arm,kind=kind,reg=reg,**score(np.array(yy),np.array(pp))))
 rank=pd.DataFrame(rows).sort_values(['mape','mae']);best=rank.iloc[0].to_dict();selections[arm]=best;candidates.extend(rows)
 (OUT/f'{arm}_settings.json').write_text(json.dumps(best,indent=2))
 result[arm]=predict(h,q,arm,best['kind'],best['reg'])
 assert np.array_equal(result[arm].to_numpy(),predict(h,q.assign(actual=999999),arm,best['kind'],best['reg']))
pd.DataFrame(candidates).to_csv(OUT/'validation.csv',index=False);result.to_csv(OUT/'predictions_before_scoring.csv',index=False)
result['actual']=q.actual
for arm in families:result[arm+'_ape']=100*abs(result[arm]-result.actual)/result.actual
result.to_csv(OUT/'later_results.csv',index=False)
summary=dict(non_deployable_diagnostic=True,selections=selections,scores={arm:score(result.actual.to_numpy(),result[arm].to_numpy()) for arm in families},no_carbohydrate_or_calorie_inputs=True,all44=len(result)==44)
(OUT/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
for pid,days in [(9,['2020-09-20','2020-09-22']),(26,['2021-03-31','2021-04-04'])]:print(d[(d.pid==pid)&d.day.isin(days)][['pid','day','actual']+food].to_string(index=False))
