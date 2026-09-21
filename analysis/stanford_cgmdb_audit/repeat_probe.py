"""Descriptive added-dose repeatability; cross-condition chronology unavailable."""
from pathlib import Path
import json,hashlib,argparse
import numpy as np
import pandas as pd
B=Path(__file__).resolve().parent
D=B.parents[1]/'dataset/stanford_cgmdb'
parser=argparse.ArgumentParser()
parser.add_argument('--earliest-available',action='store_true')
args=parser.parse_args()
if args.earliest_available:
    B=B/'earliest_available';B.mkdir(exist_ok=True)
plan=dict(target='Nominal added nutrient: 15 g fat or 10 g protein, not total meal macros.',
    calibration_counts=[1,2],query='Every available repeat numbered >=3, identical queries for both counts.',
    inclusion='At least three rice and three supplemented-condition sessions per person.',
    representation='0..170 minute smoothed curves minus median at -25,-20,-15 minutes, before nominal preload.',
    conversion='Project query onto high-minus-low calibration mean curve; clip below zero only.',
    tuning=False,chronological_validation=False,
    limitations='Cross-condition dates unavailable; baseline spline is noncausal; intervention nutrition co-varies; only two people.')
if args.earliest_available:
    plan['query']='All sessions after the two earliest available repetitions within each condition; identical queries for both calibration counts.'
    plan['calibration_selection']='Earliest n available repeat identifiers within each condition, including gaps.'
(B/'REPEAT_PLAN.json').write_text(json.dumps(plan,indent=2))
f=pd.read_csv(D/'data_cgm.csv');curves={}
for key,z in f.groupby(['subject','foods','rep']):
    z=z.sort_values('mins_since_start')
    assert np.array_equal(z.mins_since_start,np.arange(-25,171,5))
    base=z[z.mins_since_start.lt(-10)].glucose.median()
    curves[key]=z[z.mins_since_start.ge(0)].glucose.to_numpy()-base
rows=[];splits=[]
for macro,dose in [('Fat',15),('Protein',10)]:
    condition='Rice+'+macro
    for pid in sorted(f.subject.unique()):
        low=sorted(k for k in curves if k[0]==pid and k[1]=='Rice')
        high=sorted(k for k in curves if k[0]==pid and k[1]==condition)
        if len(low)<3 or len(high)<3:continue
        if args.earliest_available:
            queries=low[2:]+high[2:]
        else:
            if not all((pid,cond,r) in curves for cond in ['Rice',condition] for r in [1,2]):continue
            queries=[k for k in low+high if k[2]>=3]
        for n in [1,2]:
            cal_low=low[:n] if args.earliest_available else [(pid,'Rice',r) for r in range(1,n+1)]
            cal_high=high[:n] if args.earliest_available else [(pid,condition,r) for r in range(1,n+1)]
            assert not set(cal_low+cal_high)&set(queries)
            serial=lambda keys:[[str(a),str(b),int(c)] for a,b,c in keys]
            splits.append(dict(macro=macro,pid=pid,n=n,calibration=serial(cal_low+cal_high),queries=serial(queries)))
            a=np.mean([curves[k] for k in cal_low],axis=0)
            b=np.mean([curves[k] for k in cal_high],axis=0)
            direction=b-a;denom=direction@direction
            for key in queries:
                pred=float(max(0,(curves[key]-a)@direction/denom*dose)) if denom>1e-12 else np.nan
                actual=dose if key[1]==condition else 0
                rows.append(dict(macro=macro,pid=pid,condition=key[1],rep=int(key[2]),calibration_repeats=n,
                    actual_added_g=actual,predicted_added_g=pred,error_g=abs(pred-actual),
                    within10=bool(np.isfinite(pred) and abs(pred-actual)<=.1*actual+1e-9)))
p=pd.DataFrame(rows);p.to_csv(B/'repeat_predictions.csv',index=False)
(B/'split_manifest.json').write_text(json.dumps(splits,indent=2))
summary=[]
for (m,n),z in p.groupby(['macro','calibration_repeats']):
    added=z[z.actual_added_g.gt(0)];control=z[z.actual_added_g.eq(0)]
    summary.append(dict(macro=m,calibration_repeats=int(n),people=z.pid.nunique(),queries=len(z),
        hits=int(z.within10.sum()),MAE=float(z.error_g.mean()),positive_dose_queries=len(added),
        positive_dose_hits=int(added.within10.sum()),positive_dose_MAE=float(added.error_g.mean()),
        control_queries=len(control),control_hits=int(control.within10.sum())))
(B/'repeat_summary.json').write_text(json.dumps(summary,indent=2))
(B/'repeat_manifest.json').write_text(json.dumps(dict(script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    input_sha256=hashlib.sha256((D/'data_cgm.csv').read_bytes()).hexdigest(),plan=plan),indent=2))
print(json.dumps(summary,indent=2))
