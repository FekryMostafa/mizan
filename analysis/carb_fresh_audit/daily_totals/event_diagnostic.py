"""Separate eating-event detection from carbohydrate dose estimation."""
from pathlib import Path
import json,pickle
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier,HistGradientBoostingRegressor
from sklearn.metrics import roc_auc_score,average_precision_score,precision_score,recall_score
ROOT = str(Path(__file__).resolve().parents[3])  # repo root
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'event_diagnostic';OUT.mkdir(exist_ok=True)
x=pd.read_csv(ROOT/'hourly_probe/hourly_inputs.csv');daily=pd.read_csv(ROOT/'delayed_probe/sensor_inputs.csv');ids=pd.read_csv(ROOT/'delayed_probe/final_training_days.csv')
m=pd.read_csv(ROOT + '/dataset/cgmacros_clean_v1/meals.csv');m['t']=pd.to_datetime(m.timestamp);m['day']=m.t.dt.strftime('%Y-%m-%d');m['hour']=m.t.dt.hour
events=set(zip(m.participant_id,m.day,m.hour));x['has_food']=[(p,d,h) in events for p,d,h in zip(x.pid,x.day,x.hour)]
assert (x.loc[~x.has_food,'target']==0).all()
h=x.merge(ids,on=['pid','day']);q=x.merge(daily[daily.split=='later'][['pid','day']],on=['pid','day'])
clock=['clock_sin','clock_cos'];cgm=[c for c in x if c.startswith(('raw_','relative_'))]+['pre_glucose'];families={'clock':clock,'cgm':cgm,'cgm_clock':cgm+clock}
(OUT/'PLAN.json').write_text(json.dumps(dict(target='Same44 daily carb totals; detect eating hours vs infer grams conditional on eating.',models='Fixed80iteration histogram boosting,7leaves,min_leaf20,L2=1; classifier for any recordedfood hour including0carb, Poisson regressor for grams trained on recordedfood hours only.',comparisons='clock-only/cgm-only/cgm+clock. Passive daily sums probability(food)*conditionalgrams. Oracle sums recordedfood mask*same conditionalgrams. Known eating-hour control is not passive.',selection='No later-label hyperparameter selection; all three prespecified arms reported.',limits='Hourly food logs may omit intake; detector performance is against recorded events. No threshold tuning. Overlapping windows separated by whole-day30h purge. Reused development cohort.'),indent=2))
summary={};out=daily[daily.split=='later'][['pid','day','actual']].copy()
def score(y,p):
 e=abs(y-p);return dict(n=len(y),hits=int((e<=.1*y).sum()),mape=float((e/y).mean()*100),mae=float(e.mean()))
bins=q[['pid','day','hour','has_food','target']].copy()
for family,cols in families.items():
 kwargs=dict(max_iter=80,max_leaf_nodes=7,min_samples_leaf=20,l2_regularization=1,early_stopping=False,random_state=20260908)
 clf=HistGradientBoostingClassifier(**kwargs).fit(h[cols],h.has_food)
 reg=HistGradientBoostingRegressor(loss='poisson',**kwargs).fit(h.loc[h.has_food,cols],h.loc[h.has_food,'target'])
 p=clf.predict_proba(q[cols])[:,1];grams=reg.predict(q[cols]);bins[family+'_p_food']=p;bins[family+'_grams_if_food']=grams
 model_path=OUT/f'{family}_models.pkl';model_path.write_bytes(pickle.dumps((clf,reg)))
 # Both predictions share the same dose model; only the event indicator differs.
 for role,pred in [('passive',p*grams),('known_events',q.has_food.to_numpy()*grams)]:
  z=q[['pid','day']].copy();z['prediction']=pred;sums=z.groupby(['pid','day']).prediction.sum()
  out[family+'_'+role]=[sums.loc[(r.pid,r.day)] for _,r in out.iterrows()]
 summary[family]=dict(detector=dict(auc=float(roc_auc_score(q.has_food,p)),average_precision=float(average_precision_score(q.has_food,p)),precision_at_half=float(precision_score(q.has_food,p>=.5,zero_division=0)),recall_at_half=float(recall_score(q.has_food,p>=.5)),event_fraction=float(q.has_food.mean())),
    passive=score(out.actual.to_numpy(),out[family+'_passive'].to_numpy()),known_events_not_passive=score(out.actual.to_numpy(),out[family+'_known_events'].to_numpy()))
 reloaded=pickle.loads(model_path.read_bytes());modified=q.assign(target=999999,has_food=False)
 assert np.array_equal(p,reloaded[0].predict_proba(modified[cols])[:,1]) and np.array_equal(grams,reloaded[1].predict(modified[cols]))
out.to_csv(OUT/'daily_predictions.csv',index=False);bins.to_csv(OUT/'hour_predictions.csv',index=False)
summary['counts']=dict(training_days=len(ids),training_hours=len(h),training_eating_hours=int(h.has_food.sum()),later_days=len(out),later_hours=len(q),later_eating_hours=int(q.has_food.sum()),all44=len(out)==44)
(OUT/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
