"""Exploratory repeat-template diagnostic, not a tuned gram-prediction model."""
from pathlib import Path
import itertools,json
import numpy as np,pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/'analysis/cgm_fat_audit/separability';OUT.mkdir(exist_ok=True)
e=pd.read_csv(ROOT/'analysis/cgm_fat_audit/full_audit/events_and_features.csv',parse_dates=['time'])
REC=['reference','carb_low','protein_high','fat_high']; sensors=['Libre GL','Dexcom GL'];rng=np.random.default_rng(704)
records=[];distances=[];contrasts=[];summaries=[];confusions={}
for sensor in sensors:
 sub=e[(e['Amount Consumed']==100)&e.recipe.isin(REC)&e[sensor+'_valid180']]
 people={pid:x for pid,x in sub.groupby('pid') if all((x.recipe==r).sum()==2 for r in REC)}
 # Entire onboarding block must finish before any evaluated query, not merely
 # before its own same-recipe repeat. Participant 12 has an atypical schedule.
 people={pid:x for pid,x in people.items() if max(x[x.recipe==r].time.min() for r in REC)<min(x[x.recipe==r].time.max() for r in REC)}
 curves={}
 for pid,x in people.items():
  raw=pd.read_csv(ROOT/f'dataset/csv/CGMacros-{pid:03}.csv',parse_dates=['Timestamp']).set_index('Timestamp')
  for rec in REC:
   rr=x[x.recipe==rec].sort_values('time'); assert rr.iloc[0].time<rr.iloc[1].time
   for repeat,(_,r) in enumerate(rr.iterrows()):
    y=raw[sensor].reindex(r.time+pd.to_timedelta(np.arange(0,181,15),unit='m')).to_numpy(float)
    assert np.isfinite(y).all();curves[pid,rec,repeat]=(y,r[sensor+'_base'],r.id)
 for baseline in ['pre10','start']:
  for horizon in [60,120,180]:
   matrices=[];acc=[];pairacc={m:[] for m in ['carbs','protein','fat']};cm=np.zeros((4,4),int)
   for pid in people:
    a=[];b=[]
    for rec in REC:
     for repeat,dest in [(0,a),(1,b)]:
      y,base,_=curves[pid,rec,repeat];dest.append((y-(base if baseline=='pre10' else y[0]))[:horizon//15+1])
    a=np.array(a);b=np.array(b)
    # rows: later queries; columns: earlier calibration recipes
    dm=np.sqrt(((b[:,None,:]-a[None,:,:])**2).mean(axis=2));matrices.append(dm)
    pred=dm.argmin(axis=1);acc.append(float((pred==np.arange(4)).mean()))
    for i,rec in enumerate(REC):
     cm[i,pred[i]]+=1
     other=np.delete(dm[i],i)
     records.append(dict(sensor=sensor,baseline=baseline,minutes=horizon,pid=pid,recipe=rec,closest_recipe=REC[pred[i]],
      same_recipe_RMSE=dm[i,i],nearest_other_RMSE=other.min(),same_is_closest=bool(pred[i]==i),
      query_id=curves[pid,rec,1][2],calibration_id=curves[pid,rec,0][2]))
     for j in range(4):distances.append(dict(sensor=sensor,baseline=baseline,minutes=horizon,pid=pid,query=rec,calibration=REC[j],RMSE=dm[i,j]))
    for macro,j in [('carbs',1),('protein',2),('fat',3)]:
     ids=[0,j];pa=float((dm[np.ix_(ids,ids)].argmin(axis=1)==np.arange(2)).mean());pairacc[macro].append(pa)
     ca=a[j]-a[0];cb=b[j]-b[0]
     cos=float(np.dot(ca,cb)/(np.linalg.norm(ca)*np.linalg.norm(cb))) if np.linalg.norm(ca)*np.linalg.norm(cb)>0 else np.nan
     contrasts.append(dict(sensor=sensor,baseline=baseline,minutes=horizon,pid=pid,macro=macro,
       early_late_contrast_cosine=cos,binary_accuracy=pa))
   boot=np.array([np.mean(rng.choice(acc,size=len(acc),replace=True)) for _ in range(5000)])
   null=[]
   for _ in range(5000):
    null.append(np.mean([np.mean(rng.permutation(4)[dm.argmin(axis=1)]==np.arange(4)) for dm in matrices]))
   obs=np.mean(acc)
   summaries.append(dict(sensor=sensor,baseline=baseline,minutes=horizon,people=len(people),later_meals=4*len(people),
    same_recipe_nearest_fraction=obs,bootstrap_95_percentile=list(np.quantile(boot,[.025,.975])),
    chance=.25,permutation_p=(1+sum(v>=obs for v in null))/(1+len(null)),
    binary_recipe_match={k:float(np.mean(v)) for k,v in pairacc.items()}))
   if baseline=='pre10' and horizon==180:confusions[sensor]=cm
pd.DataFrame(records).to_csv(OUT/'repeat_matches.csv',index=False);pd.DataFrame(distances).to_csv(OUT/'all_distances.csv',index=False)
pd.DataFrame(contrasts).to_csv(OUT/'contrast_reproducibility.csv',index=False)
(OUT/'summary.json').write_text(json.dumps(summaries,indent=2))
fig,axes=plt.subplots(1,2,figsize=(11,4.8))
labels=['Reference','Low carb','High protein','High fat']
for ax,(s,cm) in zip(axes,confusions.items()):
 ax.imshow(cm,cmap='Blues');ax.set(xticks=range(4),yticks=range(4),xticklabels=labels,yticklabels=labels,title=s,xlabel='Closest earlier curve',ylabel='Actual later recipe')
 ax.tick_params(axis='x',rotation=25)
 for i in range(4):
  for j in range(4):ax.text(j,i,str(cm[i,j]),ha='center',va='center',color='white' if cm[i,j]>cm.max()/2 else 'black')
fig.suptitle('Does a later meal resemble its own earlier example?\nThree-hour glucose curves; same-person comparison; no recipe schedule input')
fig.tight_layout(rect=[0,0,1,.9]);fig.savefig(OUT/'repeat_confusion.png',dpi=150)
print(json.dumps([s for s in summaries if s['baseline']=='pre10'],indent=2))
