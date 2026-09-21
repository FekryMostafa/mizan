"""Fixed-model sensitivity to earlier-estimated relative CGM clock offsets."""
from pathlib import Path
import ast,json,hashlib
import numpy as np
import pandas as pd
ROOT = str(Path(__file__).resolve().parents[3])  # repo root
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'timing_probe';OUT.mkdir(exist_ok=True)
d=pd.read_csv(ROOT/'delayed_probe/sensor_inputs.csv');original=d.copy()
lags=pd.read_csv(ROOT/'sensor_audit/frozen_offset_evaluation.csv').groupby('pid').calibration_selected_dexcom_lag_minutes.first().to_dict()
(OUT/'PLAN.json').write_text(json.dumps(dict(target='Same44 daily carbohydrate totals',hypothesis='If Libre(t) aligns with Dexcom(t-lag), hypothetical aligned Libre at clock t is original Libre(t+lag). Dexcom clock is not established ground truth.',offsets='Frozen from earlier calibration sensor comparisons; no later carb labels used. Offsets not retuned.',model='Fixed glucose-only kernel ridge, reg0.1 from prior full-pool selection. Re-extract glucose summaries with and without offset; same64 calibration days and44 later days.',availability='Diagnostic uses shifted raw sensor times, up to next06:00 plus positive offset. Not necessarily available exactly at06:00.',limitations='Requires second sensor for this diagnostic calibration; not a CGM-only deployment improvement. No source changes. No later-label model selection.'),indent=2))
checks=[];hashes={}
def features(raw,t,lag):
    idx=pd.date_range(t+pd.Timedelta(minutes=lag),periods=1800,freq='min')
    a=raw['Libre GL'].reindex(idx).to_numpy();g=a[:1440]
    f={};ok=np.isfinite(g)
    if ok.mean()>=.9:
        qq=np.nanpercentile(g,[10,25,50,75,90]);diff=np.diff(g[::15]);diff=diff[np.isfinite(diff)]
        f.update(dict(g_mean=np.nanmean(g),g_sd=np.nanstd(g),g_q10=qq[0],g_q25=qq[1],g_median=qq[2],g_q75=qq[3],g_q90=qq[4],g_above_q10=np.nanmean(np.maximum(g-qq[0],0)),g_above_100=np.nanmean(np.maximum(g-100,0)),g_rises=np.maximum(diff,0).sum(),g_falls=np.maximum(-diff,0).sum(),g_night=np.nanmean(g[:360]),g_day=np.nanmean(g[360:1200])))
        for k in range(4):f[f'g_block{k}']=np.nanmean(g[k*360:(k+1)*360])
    for k in range(6):
        x=a[1440+60*k:1440+60*(k+1)];f[f'next_glucose_{k}']=np.nanmean(x) if np.isfinite(x).mean()>=.9 else np.nan
    tail=a[1440:]
    if np.isfinite(tail).all():
        f['next_glucose_sd']=np.std(tail,ddof=1);diff=np.diff(tail[::15]);f['next_glucose_rises']=np.maximum(diff,0).sum();f['next_glucose_falls']=np.maximum(-diff,0).sum()
    return f,int(np.isfinite(a).sum())
cols=[c for c in d if c.startswith('g_') or c.startswith('next_glucose')]
for pid,group in d.groupby('pid'):
    path=Path(fROOT + '/dataset/cgmacros_clean_v1/participants/CGMacros-{pid:03}.csv');hashes[str(path)]=hashlib.sha256(path.read_bytes()).hexdigest()
    raw=pd.read_csv(path);raw.columns=raw.columns.str.strip();raw.index=pd.to_datetime(raw.Timestamp)
    for i,r in group.iterrows():
        zero,_=features(raw,pd.Timestamp(r.day),0)
        for c in cols:
            old=r[c];new=zero.get(c,np.nan)
            assert (pd.isna(old) and pd.isna(new)) or np.isclose(old,new,rtol=0,atol=1e-8),(pid,r.day,c,old,new)
        corrected,n=features(raw,pd.Timestamp(r.day),int(lags[pid]))
        for c in cols:d.loc[i,c]=corrected.get(c,np.nan)
        checks.append(dict(pid=pid,day=r.day,split=r.split,shift_minutes=int(lags[pid]),available_shifted_minutes=n))
d.to_csv(OUT/'shifted_features.csv',index=False);pd.DataFrame(checks).to_csv(OUT/'coverage.csv',index=False)
ns=dict(np=np,families={'glucose':cols});tree=ast.parse((ROOT/'context_probe.py').read_text());nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['predict','score']];exec(compile(ast.Module(body=nodes,type_ignores=[]),'functions','exec'),ns)
ids=pd.read_csv(ROOT/'delayed_probe/final_training_days.csv');h=ids.merge(d,on=['pid','day']);q=d[d.split=='later']
p=ns['predict'](h,q,'glucose','kernel',.1)
base=ns['predict'](ids.merge(original,on=['pid','day']),original[original.split=='later'],'glucose','kernel',.1)
result=q[['pid','day']].copy();result['shifted_prediction']=p;result['original_prediction']=base;result.to_csv(OUT/'predictions_before_scoring.csv',index=False)
result['actual']=q.actual
result.to_csv(OUT/'later_results.csv',index=False)
assert np.array_equal(p,ns['predict'](h,q.assign(actual=999999),'glucose','kernel',.1))
summary=dict(original=ns['score'](q.actual.to_numpy(),base),shifted=ns['score'](q.actual.to_numpy(),p),all44=len(result)==44,zero_shift_extraction_verified=True,source_hashes_unchanged=all(hashlib.sha256(Path(f).read_bytes()).hexdigest()==v for f,v in hashes.items()),complete_shifted_later_days=sum(x['split']=='later' and x['available_shifted_minutes']==1800 for x in checks))
(OUT/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
