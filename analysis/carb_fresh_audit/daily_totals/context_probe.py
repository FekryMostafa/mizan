"""Full daily sequences and prior sensor context, fixed daily development split."""
from pathlib import Path
import json, hashlib
import numpy as np
import pandas as pd
ROOT = str(Path(__file__).resolve().parents[3])  # repo root

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'context_probe'; OUT.mkdir(exist_ok=True)
SRC=Path(ROOT + '/dataset/cgmacros_clean_v1/participants')
d=pd.read_csv(ROOT/'daily_records.csv')
d=d[d.split.isin(['earlier','later'])].reset_index(drop=True)
(OUT/'PLAN.json').write_text(json.dumps(dict(
    target='Same 44 later daily carbohydrate totals, no changed exclusions',
    features='15-minute CGM readings; daily summaries; prior 24h sensor context; hourly HR/activity where >=90% complete. No food inputs or later-day labels.',
    selection='Expanding same-person windows after 2 and 3 earlier days, next day validation; minimum MAPE then MAE. Candidate families summary+context, full CGM, full CGM+context. Residual ridge and Gaussian kernel ridge; personal mean baseline.',
    interpretation='Already exposed development outcomes; not a fresh validation cohort. Previous-day signals are available before prediction.'),indent=2))
hashes={}
for pid, group in d.groupby('pid'):
    f=SRC/f'CGMacros-{pid:03}.csv'; hashes[str(f)]=hashlib.sha256(f.read_bytes()).hexdigest()
    raw=pd.read_csv(f); raw.columns=raw.columns.str.strip()
    raw.index=pd.to_datetime(raw.Timestamp)
    assert not raw.index.duplicated().any()
    for i,r in group.iterrows():
        t=pd.Timestamp(r.day)
        g=raw['Libre GL'].reindex(pd.date_range(t,periods=96,freq='15min')).to_numpy()
        assert np.isfinite(g).all()
        for k,v in enumerate(g): d.loc[i,f'seq_{k:02}']=v
        for hours in [6,24]:
            prev=raw.reindex(pd.date_range(t-pd.Timedelta(hours=hours),periods=60*hours,freq='min'))
            for col,key in [('Libre GL','glucose'),('HR','hr'),('Calories (Activity)','activity')]:
                x=pd.to_numeric(prev[col],errors='coerce')
                ok=x.notna().mean()>=.9
                d.loc[i,f'ctx_prev{hours}_{key}_mean']=x.mean() if ok else np.nan
                d.loc[i,f'ctx_prev{hours}_{key}_sd']=x.std() if ok else np.nan
        for hour in range(24):
            sl=raw.reindex(pd.date_range(t+pd.Timedelta(hours=hour),periods=60,freq='min'))
            for col,key in [('HR','hr'),('Calories (Activity)','activity')]:
                x=pd.to_numeric(sl[col],errors='coerce')
                d.loc[i,f'ctx_{key}_{hour:02}']=x.mean() if x.notna().mean()>=.9 else np.nan
d.to_csv(OUT/'sensor_inputs.csv',index=False)
earlier=d[d.split=='earlier']; later=d[d.split=='later']
families={
 'summary_context':[c for c in d if c.startswith(('g_','ctx_'))],
 'sequence':[c for c in d if c.startswith('seq_')],
 'sequence_context':[c for c in d if c.startswith(('seq_','ctx_'))]}

def predict(train,query,family,kind,reg):
    means=train.groupby('pid').actual.mean()
    base=query.pid.map(means).to_numpy()
    for pid,q in query.groupby('pid'):
        assert train[train.pid==pid].day.max()<q.day.min()
    if kind=='baseline': return base
    cols=families[family]
    centers=train.groupby('pid')[cols].mean()
    x=np.nan_to_num(train[cols].to_numpy()-centers.loc[train.pid].to_numpy())
    z=np.nan_to_num(query[cols].to_numpy()-centers.loc[query.pid].to_numpy())
    scale=np.maximum(x.std(axis=0),1.)
    x=x/scale; z=z/scale
    y=train.actual.to_numpy()-train.pid.map(means).to_numpy()
    if kind=='ridge':
        pred=z@x.T@np.linalg.solve(x@x.T+reg*np.eye(len(x)),y)
    else:
        def kernel(a,b):
            return np.exp(-np.maximum((a*a).sum(1)[:,None]+(b*b).sum(1)[None,:]-2*a@b.T,0)/len(cols))
        pred=kernel(z,x)@np.linalg.solve(kernel(x,x)+reg*np.eye(len(x)),y)
    return np.maximum(base+pred,0)

def score(y,p):
    e=np.abs(y-p)
    return dict(n=len(y),hits=int((e<=.1*y).sum()),mape=float(np.mean(e/y)*100),mae=float(e.mean()))

folds=[]
for n in [2,3]:
    tr=[];va=[]
    for pid,g in earlier.groupby('pid'):
        g=g.sort_values('day')
        if len(g)<=n: continue
        tr.extend(g.index[:n]); va.append(g.index[n])
    folds.append((tr,va))
rows=[]
for family,kind,reg in [('baseline','baseline',0)]+[(f,k,r) for f in families for k in ['ridge','kernel'] for r in [.1,1,10,100,1000]]:
    yy=[];pp=[]
    for tr,va in folds:
        q=d.loc[va]; yy.extend(q.actual); pp.extend(predict(d.loc[tr],q,family,kind,reg))
    rows.append(dict(family=family,kind=kind,reg=reg,**score(np.array(yy),np.array(pp))))
rank=pd.DataFrame(rows).sort_values(['mape','mae'],kind='stable')
rank.to_csv(OUT/'validation_candidates.csv',index=False)
best=rank.iloc[0]
(OUT/'selected_settings.json').write_text(json.dumps(best.to_dict(),indent=2))
pred=predict(earlier,later,best.family,best.kind,float(best.reg))
result=later[['pid','day']].copy(); result['prediction']=pred
result.to_csv(OUT/'predictions_before_scoring.csv',index=False)
result['actual']=later.actual; result['ape_pct']=100*abs(pred-result.actual)/result.actual
result.to_csv(OUT/'later_results.csv',index=False)

# Diagnostic only: the nearest earlier same-person full trace for each failure.
# Query label is used solely to sort failures and report dose differences.
old=pd.read_csv(ROOT/'later_results.csv').sort_values('ape_pct',ascending=False).head(10)
cases=[]; pair_records=[]
for _,r in old.iterrows():
    q=d[(d.pid==r.pid)&(d.day==r.day)].iloc[0]
    hist=earlier[earlier.pid==r.pid]
    cols=families['sequence']
    dist=np.sqrt(((hist[cols].to_numpy()-q[cols].to_numpy(dtype=float))**2).mean(axis=1))
    neighbor=hist.iloc[np.argmin(dist)]
    case=dict(pid=int(r.pid),day=r.day,actual=q.actual,prediction_old=r.prediction,
        earlier_day=neighbor.day,earlier_carbs=neighbor.actual,trace_rmse_mg_dl=float(min(dist)))
    for col in ['g_mean','g_sd','g_rises','hr_mean','activity_mean','ctx_prev24_glucose_mean','ctx_prev24_activity_mean']:
        case[col]=q[col];case['earlier_'+col]=neighbor[col]
    cases.append(case)
    for label,row in [('failure',q),('earlier_neighbor',neighbor)]:
        for k in range(96): pair_records.append(dict(pid=int(r.pid),failure_day=r.day,role=label,day=row.day,minute=k*15,glucose=row[f'seq_{k:02}']))
pd.DataFrame(cases).to_csv(OUT/'worst_ten_comparisons.csv',index=False)
pd.DataFrame(pair_records).to_csv(OUT/'worst_ten_raw_glucose.csv',index=False)
assert np.isfinite(pred).all()
assert all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==h for f,h in hashes.items())
summary=dict(best=best.to_dict(),later=score(later.actual.to_numpy(),pred),
    baseline=score(later.actual.to_numpy(),predict(earlier,later,'baseline','baseline',0)),
    validation_distinct_days=len(set(v for _,va in folds for v in va)),unchanged_input_hashes=True)
(OUT/'summary.json').write_text(json.dumps(summary,indent=2))
print(json.dumps(summary,indent=2))
print(pd.DataFrame(cases)[['pid','actual','earlier_carbs','trace_rmse_mg_dl','g_rises','earlier_g_rises']].to_string(index=False))
