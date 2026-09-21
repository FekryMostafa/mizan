"""Duration and decay-compensated glucose descriptors, same daily benchmark."""
from pathlib import Path
import ast,json
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'excursion_probe';OUT.mkdir(exist_ok=True)
d=pd.read_csv(ROOT/'delayed_probe/sensor_inputs.csv')
(OUT/'PLAN.json').write_text(json.dumps(dict(target='Same44 later daily carb totals; known-day calibration and next-morning sensors',hypothesis='Rise-only measures miss sustained elevation. Describe amplitude, duration and positive increments after assumed exponential decay.',features='Observed CGM only. Baseline=30-hour10th percentile; three separate clock segments. Fixed descriptive decay constants30/60/120min. These are not measured absorption rates or gram conversions.',selection='Same29 purged earlier validation days, MAPE thenMAE; old summaries versus excursions versus combined, ridge/kernel, regularization. No food features.',limitations='Daily baseline may change with physiology; fixed decay rates are hypotheses, not subject physiology. Existing outcomes repeatedly exposed.'),indent=2))
new=[]
for _,r in d.iterrows():
    g=r[[f'seq_{i:02}' for i in range(96)]+[f'nextseq_{i:02}' for i in range(24)]].to_numpy(float)
    baseline=np.nanpercentile(g,10);v={}
    for name,start,end in [('night',0,24),('day',24,96),('tail',96,120)]:
        x=g[start:end];ok=np.isfinite(x)
        if ok.mean()<.9:continue
        z=np.maximum(x-baseline,0);delta=np.diff(x);valid=ok[1:]&ok[:-1]
        v[f'ex_{name}_area']=float(np.nansum(z)*15)
        v[f'ex_{name}_peak']=float(np.nanmax(z))
        v[f'ex_{name}_rise']=float(np.maximum(delta[valid],0).sum())
        v[f'ex_{name}_fall']=float(np.maximum(-delta[valid],0).sum())
        for threshold in [10,20,40]:
            high=ok&(z>threshold);longest=current=0
            for flag in high:current=current+1 if flag else 0;longest=max(longest,current)
            v[f'ex_{name}_minutes_above{threshold}']=float(high.sum()*15)
            v[f'ex_{name}_longest_above{threshold}']=float(longest*15)
        for tau in [30,60,120]:
            innovation=z[1:]-np.exp(-15/tau)*z[:-1]
            v[f'ex_{name}_positive_innovation_tau{tau}']=float(np.maximum(innovation[valid],0).sum())
    new.append(v)
d=pd.concat([d,pd.DataFrame(new)],axis=1);d.to_csv(OUT/'sensor_inputs.csv',index=False)
base=[c for c in d if c.startswith(('g_','ctx_','next_'))]
ex=[c for c in d if c.startswith('ex_')]
families=dict(old=base,excursions=ex,combined=base+ex)
ns=dict(np=np,families=families)
tree=ast.parse((ROOT/'context_probe.py').read_text());nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['predict','score']]
exec(compile(ast.Module(body=nodes,type_ignores=[]),'shared_functions','exec'),ns);predict,score=ns['predict'],ns['score']
h=pd.read_csv(ROOT/'delayed_probe/final_training_days.csv').merge(d,on=['pid','day']);q=d[d.split=='later'];fold=pd.read_csv(ROOT/'delayed_probe/folds.csv');parts=[]
for _,f in fold.groupby('fold'):
    t=f[f.role=='fit'][['pid','day']].merge(d,on=['pid','day']);v=f[f.role=='validate'][['pid','day']].merge(d,on=['pid','day']);parts.append((t,v))
rows=[]
for family in families:
    for kind in ['ridge','kernel']:
        for reg in [.1,1,10,100,1000]:
            yy=[];pp=[]
            for t,v in parts:yy.extend(v.actual);pp.extend(predict(t,v,family,kind,reg))
            rows.append(dict(family=family,kind=kind,reg=reg,**score(np.array(yy),np.array(pp))))
rank=pd.DataFrame(rows).sort_values(['mape','mae']);rank.to_csv(OUT/'validation.csv',index=False)
best=rank.iloc[0].to_dict();(OUT/'settings.json').write_text(json.dumps(best,indent=2))
pred=predict(h,q,best['family'],best['kind'],best['reg'])
r=q[['pid','day']].copy();r['prediction']=pred;r.to_csv(OUT/'predictions_before_scoring.csv',index=False)
r['actual']=q.actual;r['ape']=100*abs(r.actual-r.prediction)/r.actual;r.to_csv(OUT/'later_results.csv',index=False)
assert np.array_equal(pred,predict(h,q.assign(actual=999999),best['family'],best['kind'],best['reg']))
# Same representation and settings must reproduce the prior reference result.
reference=predict(h,q,'old','ridge',1000)
previous=pd.read_csv(ROOT/'delayed_probe/later_results.csv')
assert np.allclose(reference,previous.delayed.to_numpy(),atol=1e-8,rtol=0)
s=dict(selected=best,later=score(q.actual.to_numpy(),pred),reference=score(q.actual.to_numpy(),reference),old_model_reproduced=True,no_query_label_dependence=True,all44=len(r)==44)
(OUT/'summary.json').write_text(json.dumps(s,indent=2));print(json.dumps(s,indent=2))
