"""Learn which personal calibration curve a query matches, using grouped validation."""
from pathlib import Path
import json
import numpy as np,pandas as pd
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.model_selection import GroupKFold
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'analysis/cgm_fat_audit/pair_probe';OUT.mkdir(exist_ok=True)
e=pd.read_csv(ROOT/'analysis/cgm_fat_audit/full_audit/events_and_features.csv',parse_dates=['time']).set_index('id')
m=pd.read_csv(ROOT/'analysis/cgm_fat_audit/separability/repeat_matches.csv');m=m[(m.baseline=='pre10')&(m.minutes==180)]
REC=['reference','carb_low','protein_high','fat_high'];T=np.array([[66,22,10.5],[24,22,10.5],[66,66,10.5],[66,22,42]])
def model(name):
 if name.startswith('log'):return make_pipeline(StandardScaler(),LogisticRegression(C=float(name[3:]),max_iter=2000))
 return HistGradientBoostingClassifier(max_iter=80,max_leaf_nodes=int(name[2:]),min_samples_leaf=12,l2_regularization=2,learning_rate=.05,random_state=300)
summaries=[];outputs=[];selections=[]
for sensor,ss in m.groupby('sensor'):
 X=[];Y=[];G=[];Q=[];queryids=[];actual=[]
 for pid,x in ss.groupby('pid'):
  raw=pd.read_csv(ROOT/f'dataset/csv/CGMacros-{pid:03}.csv',parse_dates=['Timestamp']).set_index('Timestamp')
  def sig(id):
   r=e.loc[id];return raw[sensor].reindex(r.time+pd.to_timedelta(np.arange(0,181,15),unit='m')).to_numpy(float)-r[sensor+'_base']
  calids=[x[x.recipe==r].iloc[0].calibration_id for r in REC];a=np.array([sig(id) for id in calids]);scale=max(a.std(),1)
  for _,r in x.iterrows():
   b=sig(r.query_id);yi=REC.index(r.recipe);qi=len(queryids);queryids.append(r.query_id);actual.append(yi)
   for j,aa in enumerate(a):
    bn=b/max(np.linalg.norm(b),1);an=aa/max(np.linalg.norm(aa),1)
    # Relative paired shapes, amplitude changes, response products, pre-meal state,
    # and the candidate's KNOWN calibration macros. Query macros never enter X.
    feat=np.r_[(b-aa)/scale,abs(b-aa)/scale,bn-an,bn*an,np.diff(b-aa)/scale,
      np.sqrt(np.mean((b-aa)**2))/scale,b.mean()/scale,aa.mean()/scale,np.argmax(b)/12,np.argmax(aa)/12,
      e.loc[r.query_id,sensor+'_base']-e.loc[calids[j],sensor+'_base'],e.loc[r.query_id,sensor+'_slope30']-e.loc[calids[j],sensor+'_slope30'],T[j]/np.array([66,66,42])]
    assert np.isfinite(feat).all();X.append(feat);Y.append(j==yi);G.append(pid);Q.append(qi)
 X=np.array(X);Y=np.array(Y);G=np.array(G);Q=np.array(Q);actual=np.array(actual);names=['log0.01','log0.1','log1','gb3','gb7'];preds={n:np.zeros(len(actual),int) for n in names};selected=np.zeros(len(actual),int)
 def accuracy(prob,indices):
  # All candidate pairs for any one query remain together in every split.
  qq=Q[indices];unique=np.unique(qq);pp=np.array([np.argmax(prob[qq==q]) for q in unique]);return float((pp==actual[unique]).mean())
 for pid in np.unique(G):
  tr=np.flatnonzero(G!=pid);te=np.flatnonzero(G==pid);scores={}
  for name in names:
   inner=np.zeros(len(tr))
   for a,b in GroupKFold(4).split(tr,Y[tr],G[tr]):
    fit=model(name);fit.fit(X[tr[a]],Y[tr[a]]);inner[b]=fit.predict_proba(X[tr[b]])[:,1]
   scores[name]=accuracy(inner,tr)
   fit=model(name);fit.fit(X[tr],Y[tr]);prob=fit.predict_proba(X[te])[:,1]
   for q in np.unique(Q[te]):preds[name][q]=np.argmax(prob[Q[te]==q])
  best=max(scores,key=scores.get);idx=np.unique(Q[te]);selected[idx]=preds[best][idx];selections.append(dict(sensor=sensor,pid=int(pid),selected=best,inner_scores=scores))
 preds['nested_selected']=selected
 for name,pred in preds.items():
  err=abs(T[pred]-T[actual]);hit=(err<=.1*T[actual]+1e-9).all(axis=1)
  summaries.append(dict(sensor=sensor,method=name,meals=len(actual),hits=int(hit.sum()),MAE=err.mean(axis=0).tolist()))
  for i,id in enumerate(queryids):outputs.append(dict(sensor=sensor,id=id,method=name,actual_recipe=REC[actual[i]],predicted_recipe=REC[pred[i]],all_three_within10=bool(hit[i])))
pd.DataFrame(outputs).to_csv(OUT/'predictions.csv',index=False);(OUT/'summary.json').write_text(json.dumps(summaries,indent=2));(OUT/'selection.json').write_text(json.dumps(selections,indent=2));print(json.dumps(summaries,indent=2))
