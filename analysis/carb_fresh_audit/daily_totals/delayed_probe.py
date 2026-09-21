"""Paired midnight/next-morning daily carbohydrate development experiment."""
from pathlib import Path
import ast, json, hashlib
import numpy as np
import pandas as pd
ROOT = str(Path(__file__).resolve().parents[3])  # repo root

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'delayed_probe'; OUT.mkdir(exist_ok=True)
SRC=Path(ROOT + '/dataset/cgmacros_clean_v1')
PLAN=dict(target='Same midnight-to-midnight carbohydrate totals and same 44 later days',
    availability='Delayed estimate uses sensor data up to next-day 05:59; no next-day food labels are predictors.',
    comparison='Same folds, same training rows, same candidate grid for midnight and delayed models. Select independently on earlier validation MAPE then MAE.',
    purge='For each person exclude calibration days whose 30-hour sensor window overlaps the first query day. Apply to both arms.',
    missing='Retain all days; unavailable overnight features remain NaN, converted to zero personal deviations by training-only preprocessing.',
    candidates='summary_context and sequence_context, ridge/kernel, regularization .1,1,10,100,1000, plus baseline.',
    limitations='Repeatedly exposed development cohort, sparse personal calibration, unverified food-log completeness; next-day food may affect overnight CGM.')
(OUT/'PLAN.json').write_text(json.dumps(PLAN,indent=2))
d=pd.read_csv(ROOT/'context_probe/sensor_inputs.csv')
audit=[]; hashes={}
for pid,group in d.groupby('pid'):
    f=SRC/'participants'/f'CGMacros-{pid:03}.csv'
    hashes[str(f)]=hashlib.sha256(f.read_bytes()).hexdigest()
    raw=pd.read_csv(f); raw.columns=raw.columns.str.strip(); raw.index=pd.to_datetime(raw.Timestamp)
    assert not raw.index.duplicated().any()
    for i,r in group.iterrows():
        start=pd.Timestamp(r.day)+pd.Timedelta(days=1)
        window=raw.reindex(pd.date_range(start,periods=360,freq='min'))
        g=window['Libre GL']
        audit.append(dict(pid=pid,day=r.day,split=r.split,overnight_glucose_minutes=int(g.notna().sum()),overnight_bound_minutes=int(((g<=40)|(g>=400)).sum())))
        for hour in range(6):
            for col,key in [('Libre GL','glucose'),('HR','hr'),('Calories (Activity)','activity')]:
                x=pd.to_numeric(window.iloc[60*hour:60*(hour+1)][col],errors='coerce')
                d.loc[i,f'next_{key}_{hour}']=x.mean() if x.notna().mean()>=.9 else np.nan
        for k,v in enumerate(g.iloc[::15]): d.loc[i,f'nextseq_{k:02}']=v
        if g.notna().all():
            d.loc[i,'next_glucose_sd']=g.std()
            d.loc[i,'next_glucose_rises']=np.maximum(np.diff(g.iloc[::15]),0).sum()
            d.loc[i,'next_glucose_falls']=np.maximum(-np.diff(g.iloc[::15]),0).sum()
pd.DataFrame(audit).to_csv(OUT/'coverage.csv',index=False)
d.to_csv(OUT/'sensor_inputs.csv',index=False)
families={}
for base,prefix in [('summary_context',('g_','ctx_')),('sequence_context',('seq_','ctx_'))]:
    families['midnight_'+base]=[c for c in d if c.startswith(prefix)]
    families['delayed_'+base]=families['midnight_'+base]+[c for c in d if c.startswith('next_') or (base=='sequence_context' and c.startswith('nextseq_'))]
tree=ast.parse((ROOT/'context_probe.py').read_text())
funcs=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['predict','score']]
ns=dict(np=np,families=families)
exec(compile(ast.Module(body=funcs,type_ignores=[]),'shared_predict','exec'),ns)
predict,score=ns['predict'],ns['score']
early=d[d.split=='earlier']; later=d[d.split=='later']

def purge(train,query):
    keep=[]
    for pid,q in query.groupby('pid'):
        h=train[train.pid==pid]
        h=h[pd.to_datetime(h.day)+pd.Timedelta(hours=30)<=pd.Timestamp(q.day.min())]
        assert len(h)>0
        keep.extend(h.index)
    return train.loc[keep]

folds=[]; assignments=[]
for n in [2,3]:
    tr=[];va=[]
    for pid,g in early.groupby('pid'):
        g=g.sort_values('day')
        if len(g)<=n: continue
        tr.extend(g.index[:n]);va.append(g.index[n])
    query=d.loc[va]; train=purge(d.loc[tr],query); folds.append((train,query))
    for role,frame in [('fit',train),('validate',query)]:
        assignments.extend(dict(fold=n,role=role,pid=int(r.pid),day=r.day) for _,r in frame.iterrows())
pd.DataFrame(assignments).to_csv(OUT/'folds.csv',index=False)
train=purge(early,later)
train[['pid','day']].to_csv(OUT/'final_training_days.csv',index=False)
results=later[['pid','day']].copy(); selections={}; all_candidates=[]
for arm in ['midnight','delayed']:
    candidates=[('baseline','baseline',0)]+[(f,k,r) for f in families if f.startswith(arm) for k in ['ridge','kernel'] for r in [.1,1,10,100,1000]]
    rows=[]
    for family,kind,reg in candidates:
        actual=[];pred=[]
        for tr,va in folds:
            actual.extend(va.actual);pred.extend(predict(tr,va,family,kind,reg))
        rows.append(dict(arm=arm,family=family,kind=kind,reg=reg,**score(np.array(actual),np.array(pred))))
    rank=pd.DataFrame(rows).sort_values(['mape','mae'],kind='stable'); all_candidates.extend(rows)
    best=rank.iloc[0].to_dict();selections[arm]=best
    (OUT/f'{arm}_settings.json').write_text(json.dumps(best,indent=2))
    results[arm]=predict(train,later,best['family'],best['kind'],best['reg'])
pd.DataFrame(all_candidates).to_csv(OUT/'validation_candidates.csv',index=False)
results['baseline']=predict(train,later,'baseline','baseline',0)
results.to_csv(OUT/'predictions_before_scoring.csv',index=False)
results['actual']=later.actual
for arm in ['midnight','delayed','baseline']: results[arm+'_ape']=100*abs(results[arm]-results.actual)/results.actual
results.to_csv(OUT/'later_results.csv',index=False)

# Food fields below describe results only and are never model inputs.
m=pd.read_csv(SRC/'meals.csv'); m['t']=pd.to_datetime(m.timestamp)
diagnostic=[]
for _,r in results.iterrows():
    t=pd.Timestamp(r.day); own=m[(m.participant_id==r.pid)&(m.t>=t)&(m.t<t+pd.Timedelta(days=1))]
    following=m[(m.participant_id==r.pid)&(m.t>=t+pd.Timedelta(days=1))&(m.t<t+pd.Timedelta(hours=30))]
    diagnostic.append(dict(pid=int(r.pid),day=r.day,carbs_after18=own[own.t.dt.hour>=18].carbs_g.sum(),next_morning_meal_records=len(following),next_morning_recorded_carbs=following.carbs_g.sum(min_count=1)))
diag=results.merge(pd.DataFrame(diagnostic),on=['pid','day']).merge(pd.DataFrame(audit)[['pid','day','overnight_glucose_minutes']],on=['pid','day'])
diag.to_csv(OUT/'boundary_diagnostics.csv',index=False)
verification={}
for arm in selections:
    b=selections[arm]; changed=later.copy();changed['actual']=999999
    pp=predict(train,changed,b['family'],b['kind'],b['reg'])
    assert np.array_equal(pp,results[arm].to_numpy())
verification['query_labels_do_not_affect_predictions']=True
verification['all_44_preserved']=len(results)==44
verification['purged_training_days']=len(early)-len(train)
verification['sources_unchanged']=all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h for f,h in hashes.items())
assert verification['sources_unchanged'] and verification['all_44_preserved']
(OUT/'verification.json').write_text(json.dumps(verification,indent=2))
summary=dict(training_days=len(train),later_days=len(results),complete_overnights=int((diag.overnight_glucose_minutes==360).sum()),
    next_morning_food_days=int((diag.next_morning_meal_records>0).sum()),settings=selections,
    scores={arm:score(results.actual.to_numpy(),results[arm].to_numpy()) for arm in ['midnight','delayed','baseline']})
(OUT/'summary.json').write_text(json.dumps(summary,indent=2))
print(json.dumps(summary,indent=2))
print(diag[diag.pid==4].to_string(index=False))
