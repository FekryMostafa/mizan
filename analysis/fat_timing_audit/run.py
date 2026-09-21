from pathlib import Path
import numpy as np
import pandas as pd
import json, hashlib
ROOT = str(Path(__file__).resolve().parents[2])  # repo root

B=Path(ROOT + '/analysis/macro_features')
O=Path(__file__).resolve().parent
f=pd.read_csv(B/'features.csv');f.time=pd.to_datetime(f.time,format='mixed')
x=np.load(B/'curve_audit/curves.npz')['X']; t=np.arange(37)*5
c=pd.read_csv(B/'personal_dose_repeat/contrasts.csv');c=c[c.macro=='Fat']
idx={(r.dataset,int(r.pid),r.time.isoformat()):i for i,r in f.iterrows()}
def ix(pid,time):return idx['CGMacros',int(pid),pd.Timestamp(time).isoformat()]
# Fixed before query labels are evaluated. These are sensitivity bounds,
# not estimated physiological distributions or confidence intervals.
plan={'fat_grid_g':[0,100,.25], 'gain_grid':[.8,1.2,.05],
      'time_scale_grid':[.8,1.2,.05], 'calibration':'first low and high fat meals',
      'evaluation':'same later controlled meals; no reserved subjects',
      'near_fit':'RMSE <= best RMSE + 1 mg/dL; NOT a confidence interval',
      'models':['fixed','gain_and_time'],
      'limitation':'empirical interpolation, not a validated physiological model'}
(O/'PLAN.json').write_text(json.dumps(plan,indent=2))
doses=np.arange(0,100.001,.25); rows=[]; profiles=[]
for r in c.itertuples():
    a,b=ix(r.pid,r.low_calibration_time),ix(r.pid,r.high_calibration_time)
    lo,hi=float(f.loc[a,'Fat']),float(f.loc[b,'Fat'])
    assert np.allclose(f.loc[a,['Carbs','Protein']].to_numpy(float),f.loc[b,['Carbs','Protein']].to_numpy(float))
    assert hi>lo
    for method in plan['models']:
        gains=[1.] if method=='fixed' else np.linspace(.8,1.2,9)
        scales=[1.] if method=='fixed' else np.linspace(.8,1.2,9)
        templates=[]; parameters=[]
        for scale in scales:
            # Clip outside observed 0..180; no invented extrapolated tail.
            low=np.interp(t/scale,t,x[a]);high=np.interp(t/scale,t,x[b])
            base=low[None,:]+((doses-lo)/(hi-lo))[:,None]*(high-low)[None,:]
            for gain in gains:
                templates.append(gain*base);parameters.append((gain,scale))
        templates=np.asarray(templates)
        for qt in [r.low_query_time,r.high_query_time]:
            q=ix(r.pid,qt)
            assert max(f.loc[a,'time'],f.loc[b,'time'])+pd.Timedelta(minutes=180)<f.loc[q,'time']
            rmse=np.sqrt(np.mean((templates-x[q])**2,axis=2))
            profile=rmse.min(axis=0);best=int(profile.argmin());pidx=int(rmse[:,best].argmin())
            pred=float(doses[best]);minimum=float(profile[best]);near=doses[profile<=minimum+1]
            # Truth is used only for scoring, after prediction.
            actual=float(f.loc[q,'Fat']);truth_i=int(np.argmin(abs(doses-actual)))
            rows.append(dict(pid=int(r.pid),time=str(qt),method=method,actual=actual,predicted=pred,
                error_g=abs(pred-actual),within10=abs(pred-actual)<=.1*actual,
                best_rmse=minimum,truth_rmse=float(profile[truth_i]),
                near_fit_low=float(near.min()),near_fit_high=float(near.max()),
                gain=parameters[pidx][0],time_scale=parameters[pidx][1]))
            profiles.extend(dict(pid=int(r.pid),time=str(qt),method=method,fat_g=float(d),rmse=float(v)) for d,v in zip(doses,profile))
p=pd.DataFrame(rows);assert len(p)==100 and not p.duplicated(['pid','time','method']).any()
p.to_csv(O/'predictions.csv',index=False);pd.DataFrame(profiles).to_csv(O/'profiles.csv',index=False)
summary=[]
for method,z in p.groupby('method'):
    summary.append(dict(method=method,n=len(z),hits=int(z.within10.sum()),MAE=float(z.error_g.mean()),
        median_near_fit_width=float((z.near_fit_high-z.near_fit_low).median()),
        mean_best_rmse=float(z.best_rmse.mean()),both_correct=int(z.groupby('pid').within10.all().sum())))
(O/'summary.json').write_text(json.dumps(summary,indent=2))
(O/'manifest.json').write_text(json.dumps({str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),B/'features.csv',B/'curve_audit/curves.npz',B/'personal_dose_repeat/contrasts.csv']},indent=2))
print(json.dumps(summary,indent=2))
