"""Chronological personal validation retaining other people's training pool."""
from pathlib import Path
import ast,json
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'full_pool_validation';OUT.mkdir(exist_ok=True)
d=pd.read_csv(ROOT/'delayed_probe/sensor_inputs.csv');h=pd.read_csv(ROOT/'delayed_probe/final_training_days.csv').merge(d,on=['pid','day']);q=d[d.split=='later']
families={'summary':[c for c in d if c.startswith(('g_','ctx_','next_'))],
          'glucose':[c for c in d if c.startswith('g_') or c.startswith('next_glucose')],
          'sequence':[c for c in d if c.startswith(('seq_','nextseq_'))]}
(OUT/'PLAN.json').write_text(json.dumps(dict(target='Same44 later daily carbohydrate totals',validation='Each eligible earlier calibration day queried individually. Same-person training restricted to days whose30h sensor windows end before query midnight. All other participants original64 calibration-pool rows retained. Later44 never used.',grid='Three sensor families, ridge/kernel, penalties .1/1/10/100/1000 and personal mean baseline. Select earlier MAPE then MAE.',limits='Not population-held-out validation. Cohort dates shifted; chronology enforced within person. Later development set already exposed.'),indent=2))
ns=dict(np=np,families=families);tree=ast.parse((ROOT/'context_probe.py').read_text());nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['predict','score']];exec(compile(ast.Module(body=nodes,type_ignores=[]),'shared_functions','exec'),ns);predict,score=ns['predict'],ns['score']
parts=[];assignment=[]
for idx,row in h.iterrows():
    own=h[(h.pid==row.pid)&(pd.to_datetime(h.day)+pd.Timedelta(hours=30)<=pd.Timestamp(row.day))]
    if not len(own):continue
    tr=pd.concat([h[h.pid!=row.pid],own]);v=h.loc[[idx]]
    assert not ((tr.pid==row.pid)&(tr.day==row.day)).any()
    parts.append((tr,v));assignment.append(dict(pid=int(row.pid),day=row.day,training_rows=len(tr),personal_training_rows=len(own)))
pd.DataFrame(assignment).to_csv(OUT/'validation_days.csv',index=False)
rows=[];vp=[]
configs=[('baseline','baseline',0)]+[(f,k,r) for f in families for k in ['ridge','kernel'] for r in [.1,1,10,100,1000]]
for family,kind,reg in configs:
    yy=[];pp=[]
    for tr,v in parts:
        p=predict(tr,v,family,kind,reg);yy.extend(v.actual);pp.extend(p)
        vp.append(dict(family=family,kind=kind,reg=reg,pid=int(v.pid.iloc[0]),day=v.day.iloc[0],actual=float(v.actual.iloc[0]),prediction=float(p[0])))
    rows.append(dict(family=family,kind=kind,reg=reg,**score(np.array(yy),np.array(pp))))
rank=pd.DataFrame(rows).sort_values(['mape','mae'],kind='stable');rank.to_csv(OUT/'candidates.csv',index=False);pd.DataFrame(vp).to_csv(OUT/'validation_predictions.csv',index=False)
best=rank.iloc[0].to_dict();(OUT/'settings.json').write_text(json.dumps(best,indent=2))
p=predict(h,q,best['family'],best['kind'],best['reg'])
r=q[['pid','day']].copy();r['prediction']=p;r.to_csv(OUT/'predictions_before_scoring.csv',index=False)
r['actual']=q.actual;r['ape']=100*abs(r.prediction-r.actual)/r.actual;r.to_csv(OUT/'later_results.csv',index=False)
assert np.array_equal(p,predict(h,q.assign(actual=999999),best['family'],best['kind'],best['reg']))
old=rank[(rank.family=='summary')&(rank.kind=='ridge')&(rank.reg==1000)].iloc[0].to_dict()
s=dict(selected=best,old_settings_on_new_validation=old,validation_days=len(parts),validation_pool_range=[min(x['training_rows'] for x in assignment),max(x['training_rows'] for x in assignment)],later=score(q.actual.to_numpy(),p),no_query_label_dependence=True,all44=len(r)==44)
(OUT/'summary.json').write_text(json.dumps(s,indent=2));print(json.dumps(s,indent=2))
