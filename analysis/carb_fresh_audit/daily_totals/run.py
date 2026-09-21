"""Daily CGM prediction: audited labels, chronological personal calibration."""
from pathlib import Path
import json, hashlib
import numpy as np
import pandas as pd
ROOT = str(Path(__file__).resolve().parents[3])  # repo root

OUT = Path(__file__).resolve().parent
SRC = Path(ROOT + '/dataset/cgmacros_clean_v1')
PLAN = dict(target='Recorded carbohydrate grams per midnight-to-midnight day',
    eligibility='1440 unique minutes and complete Libre; >=3 meal records including breakfast/lunch/dinner; every label eligible_full_consumption; positive daily carbs. Bounds retained and flagged.',
    split='Per person: >=5 eligible days; final ceil(30%) reserved; last earlier day validates shared settings. Final fit uses all earlier days.',
    candidates='Personal historical mean; ridge residual above personal mean using centered CGM or CGM+HR/activity, ridge 0.1,1,10,100,1000.',
    selection='Minimum validation mean absolute percentage error, tie MAE. No later labels used for selection.',
    limitations='Meal logging completeness cannot be proven. Source is already interpolated. Midnight responses cross day boundaries. Same participants as prior research; development evidence, not prospective validation.')
(OUT/'PLAN.json').write_text(json.dumps(PLAN, indent=2))
files = [SRC/'meals.csv', *sorted((SRC/'participants').glob('*.csv'))]
hashes = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
meals = pd.read_csv(SRC/'meals.csv')
meals['day'] = pd.to_datetime(meals.timestamp).dt.normalize()
rows = []
for p in files[1:]:
    pid = int(p.stem.split('-')[1])
    raw = pd.read_csv(p)
    raw.columns = raw.columns.str.strip()
    raw['t'] = pd.to_datetime(raw.Timestamp)
    for day, d in raw.groupby(raw.t.dt.normalize()):
        m = meals[(meals.participant_id == pid) & (meals.day == day)]
        flags = []
        if len(d)!=1440 or d.t.nunique()!=1440: flags.append('incomplete_day_grid')
        if d['Libre GL'].notna().sum()!=1440: flags.append('incomplete_libre')
        if len(m)<3 or not {'breakfast','lunch','dinner'}.issubset(set(m.meal_type)): flags.append('missing_main_meal_records')
        if not len(m) or not m.label_status.eq('eligible_full_consumption').all(): flags.append('unresolved_meal_labels')
        total = m.carbs_g.sum(min_count=1)
        if not np.isfinite(total) or total<=0: flags.append('no_positive_total')
        r = dict(pid=pid, day=str(day.date()), records=len(m), actual=total,
                 reasons=';'.join(flags), eligible=not flags,
                 bounds_minutes=int(((d['Libre GL']<=40)|(d['Libre GL']>=400)).sum()))
        if not flags:
            g = d.sort_values('t')['Libre GL'].to_numpy()
            q = np.percentile(g,[10,25,50,75,90])
            r.update(dict(g_mean=g.mean(), g_sd=g.std(), g_q10=q[0],g_q25=q[1],g_median=q[2],g_q75=q[3],g_q90=q[4],
                g_above_q10=np.maximum(g-q[0],0).mean(),g_above_100=np.maximum(g-100,0).mean(),
                g_rises=np.maximum(np.diff(g[::15]),0).sum(),g_falls=np.maximum(-np.diff(g[::15]),0).sum(),
                g_night=g[:360].mean(), g_day=g[360:1200].mean()))
            for j in range(4): r[f'g_block{j}']=g[j*360:(j+1)*360].mean()
            for name,col in [('hr','HR'),('activity','Calories (Activity)')]:
                v = pd.to_numeric(d[col],errors='coerce')
                r[name+'_mean']=v.mean() if v.notna().mean()>=.9 else np.nan
                r[name+'_sd']=v.std() if v.notna().mean()>=.9 else np.nan
        rows.append(r)
df = pd.DataFrame(rows)
df.to_csv(OUT/'day_audit.csv',index=False)
good = df[df.eligible].copy()
good['split']='insufficient_person_days'
for pid,d in good.groupby('pid'):
    d=d.sort_values('day')
    if len(d)<5: continue
    ntest=int(np.ceil(.3*len(d)))
    good.loc[d.index[:-ntest],'split']='earlier'
    good.loc[d.index[-ntest:],'split']='later'
good.to_csv(OUT/'daily_records.csv',index=False)
early=good[good.split=='earlier'].copy(); later=good[good.split=='later'].copy()
if early.empty: raise RuntimeError('No participants meet prespecified daily split')
val=early.groupby('pid',group_keys=False).tail(1)
fit=early.drop(val.index)
features={'cgm':[c for c in df if c.startswith('g_')], 'cgm_activity':[c for c in df if c.startswith(('g_','hr_','activity_'))]}

def predict(train, query, family, ridge):
    means=train.groupby('pid').actual.mean()
    base=query.pid.map(means).to_numpy()
    assert np.isfinite(base).all()
    for pid,d in query.groupby('pid'):
        assert train[train.pid==pid].day.max()<d.day.min()
    if family=='baseline': return base, {}
    cols=features[family]
    centers=train.groupby('pid')[cols].mean()
    a=train[cols].to_numpy()-centers.loc[train.pid].to_numpy()
    b=query[cols].to_numpy()-centers.loc[query.pid].to_numpy()
    # Missing deviations imply unknown and are imputed to zero; scale fit only.
    a=np.nan_to_num(a); b=np.nan_to_num(b)
    scale=np.maximum(a.std(axis=0),1e-6)
    a=a/scale; b=b/scale
    y=train.actual.to_numpy()-train.pid.map(means).to_numpy()
    coef=np.linalg.solve(a.T@a+ridge*np.eye(len(cols)), a.T@y)
    return np.maximum(base+b@coef,0), dict(features=cols,coefficient=coef.tolist(),scale=scale.tolist(),personal_means={str(k):v for k,v in means.items()},personal_centers=centers.fillna(0).to_dict('index'))

def score(y,p):
    err=np.abs(y-p)
    return dict(n=len(y),hits=int((err<=.1*y).sum()),mae=float(err.mean()),mape=float((err/y).mean()*100),bias=float((p-y).mean()))

candidates=[]
for family in ['baseline',*features]:
    for ridge in ([0] if family=='baseline' else [.1,1,10,100,1000]):
        pred,_=predict(fit,val,family,ridge)
        candidates.append(dict(family=family,ridge=ridge,**score(val.actual.to_numpy(),pred)))
rank=pd.DataFrame(candidates).sort_values(['mape','mae'],kind='stable')
rank.to_csv(OUT/'validation_candidates.csv',index=False)
best=rank.iloc[0]
(OUT/'selected_settings.json').write_text(json.dumps(best.to_dict(),indent=2))
pred,model=predict(early,later,best.family,float(best.ridge))
base,_=predict(early,later,'baseline',0)
result=later[['pid','day']].copy(); result['prediction']=pred; result['baseline']=base
result.to_csv(OUT/'predictions_before_scoring.csv',index=False)
(OUT/'model.json').write_text(json.dumps(model,indent=2))
result['actual']=later.actual.to_numpy()
result['error_g']=pred-result.actual; result['ape_pct']=100*abs(result.error_g)/result.actual
result['within_10pct']=result.ape_pct<=10
result.to_csv(OUT/'later_results.csv',index=False)
summary=dict(audited_days=len(df),eligible_days=len(good),participants=int(early.pid.nunique()),earlier_days=len(early),validation_days=len(val),
    selected=best.to_dict(),later=score(result.actual.to_numpy(),pred),baseline=score(result.actual.to_numpy(),base),
    excluded_reasons=df.reasons.str.get_dummies(sep=';').sum().to_dict(),
    sources_unchanged=all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in hashes.items()))
assert summary['sources_unchanged']
assert set(early.index).isdisjoint(later.index)
(OUT/'summary.json').write_text(json.dumps(summary,indent=2))
print(json.dumps(summary,indent=2))
