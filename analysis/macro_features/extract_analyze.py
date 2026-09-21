"""Macro-specific CGM feature diagnostics. No intake prediction claim."""
from pathlib import Path
import json,hashlib
import numpy as np
import pandas as pd
from scipy.stats import rankdata

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
B=ROOT/'analysis/big_ideas_audit'
S=np.load(B/'source_features.npz',allow_pickle=False)
T=np.load(B/'development_features.npz',allow_pickle=False)
EVENTS=pd.read_csv(ROOT/'analysis/cgm_fat_audit/full_audit/events_and_features.csv').set_index('id')
GRID=np.r_[-10,-5,np.arange(0,181,5)]

def features(raw):
    base=np.median(raw[:2]);v=raw[2:]-base;t=GRID[2:]
    out={'baseline':base,'pre_slope':(raw[1]-raw[0])/5,
         'peak_height':v.max(),'peak_minute':float(t[v.argmax()]),
         'trough':v.min(),'end_change':v[-1], 'response_std':v.std(),
         'rise_max':float(np.diff(v).max()/5),'fall_min':float(np.diff(v).min()/5),
         'negative_area':float(np.trapezoid(np.minimum(v,0),t)),
         'tail_mean':float(v[t>=150].mean()),
         'late_minus_early_peak':float(v[t>=90].max()-v[t<=60].max())}
    for a,b,label in [(0,60,'early'),(60,120,'middle'),(120,180,'late')]:
        mask=(t>=a)&(t<=b)
        out[label+'_signed_area']=float(np.trapezoid(v[mask],t[mask]))
        out[label+'_positive_area']=float(np.trapezoid(np.maximum(v[mask],0),t[mask]))
    return out

records=[]
for name,data in [('CGMacros',S),('BIG_IDEAs_development',T)]:
    for pid in np.unique(data['G']):
        if name=='CGMacros':
            file=ROOT/f'dataset/csv/CGMacros-{pid:03}.csv'
            raw=pd.read_csv(file,usecols=['Timestamp','Dexcom GL'])
            tt=pd.to_datetime(raw.Timestamp).astype('int64').to_numpy()
            vv=raw['Dexcom GL'].to_numpy(float)
        else:
            assert pid<=8
            file=ROOT/f'dataset/big_ideas_1_1_3/{pid:03}/Dexcom_{pid:03}.csv'
            raw=pd.read_csv(file);raw=raw[raw['Event Type'].eq('EGV')]
            tt=pd.to_datetime(raw['Timestamp (YYYY-MM-DDThh:mm:ss)']).astype('int64').to_numpy()
            vv=pd.to_numeric(raw['Glucose Value (mg/dL)'],errors='coerce').to_numpy(float)
        ok=np.isfinite(vv);tt,vv=tt[ok],vv[ok];assert (np.diff(tt)>0).all()
        for i in np.flatnonzero(data['G']==pid):
            time=str(EVENTS.loc[str(data['ids'][i]),'time']) if name=='CGMacros' else str(data['times'][i])
            target=pd.Timestamp(time).value+GRID*60*10**9
            if name=='CGMacros':
                ix=np.searchsorted(tt,target);assert (ix<len(tt)).all() and np.array_equal(tt[ix],target)
                vals=vv[ix]
            else:
                ix=np.searchsorted(tt,target);assert (ix>0).all() and (ix<len(tt)).all()
                assert ((tt[ix]-tt[ix-1])<=601*10**9).all()
                vals=np.interp((target-tt[0])/1e9,(tt-tt[0])/1e9,vv)
            # Coarse points must reproduce the earlier cached representation.
            old=np.r_[vals[2::3]-np.median(vals[:2]),np.median(vals[:2]),(vals[1]-vals[0])/5]
            assert np.allclose(old,data['X'][i],atol=1e-6,rtol=0)
            row=dict(dataset=name,pid=int(pid),time=time)
            row.update(dict(zip(['Carbs','Protein','Fat'],data['Y'][i])))
            row.update(features(vals));records.append(row)
d=pd.DataFrame(records);d.to_csv(OUT/'features.csv',index=False)
names=list(features(np.zeros(len(GRID))))
results=[]
for dataset,z in d.groupby('dataset'):
    # Control stable person differences; adjusted associations additionally
    # control other macros. This is descriptive, not deployable inference.
    persons=pd.get_dummies(z.pid,dtype=float).to_numpy()
    for macro in ['Carbs','Protein','Fat']:
        other=[m for m in ['Carbs','Protein','Fat'] if m!=macro]
        for feature in names:
            y=rankdata(z[macro]);x=rankdata(z[feature])
            for adjusted in [False,True]:
                controls=np.c_[persons,*[rankdata(z[m]) for m in other]] if adjusted else persons
                a=x-controls@np.linalg.lstsq(controls,x,rcond=None)[0]
                b=y-controls@np.linalg.lstsq(controls,y,rcond=None)[0]
                corr=float(np.corrcoef(a,b)[0,1]) if np.std(a)>1e-8 and np.std(b)>1e-8 else None
                results.append(dict(dataset=dataset,macro=macro,feature=feature,
                                    adjusted_for_other_macros=adjusted,partial_rank_correlation=corr,
                                    meals=len(z),people=z.pid.nunique()))
r=pd.DataFrame(results);r.to_csv(OUT/'associations.csv',index=False)
top=r[r.dataset.eq('CGMacros') & r.adjusted_for_other_macros].copy()
top['absolute']=top.partial_rank_correlation.abs()
top=top.sort_values('absolute',ascending=False).groupby('macro',sort=False).head(3)
print('Top source features after person/other-macro adjustment:')
print(top[['macro','feature','partial_rank_correlation']].to_string(index=False))
print('Same features in independent-dataset development records:')
for row in top.itertuples():
    z=r[(r.dataset!='CGMacros')&r.adjusted_for_other_macros&r.macro.eq(row.macro)&r.feature.eq(row.feature)]
    print(row.macro,row.feature,z.partial_rank_correlation.iloc[0])
(OUT/'manifest.json').write_text(json.dumps(dict(source_rows=int((d.dataset=='CGMacros').sum()),
    development_rows=int((d.dataset!='CGMacros').sum()),features=names,reserved_accessed=False,
    coarse_cache_reproduced=True,script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    caveat='Exploratory partial rank associations, no causal or prediction accuracy claim.'),indent=2))
