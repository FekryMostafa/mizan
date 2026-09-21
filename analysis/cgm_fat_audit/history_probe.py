"""Use preceding glucose history and clock time, without prior meal labels."""
from pathlib import Path
import json
import numpy as np,pandas as pd
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.svm import SVC
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.model_selection import GroupKFold
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'analysis/cgm_fat_audit/history_probe';OUT.mkdir(exist_ok=True)
P=ROOT/'analysis/cgm_fat_audit/shape_probe';e=pd.read_csv(ROOT/'analysis/cgm_fat_audit/full_audit/events_and_features.csv',parse_dates=['time']).set_index('id')
m=pd.read_csv(ROOT/'analysis/cgm_fat_audit/separability/repeat_matches.csv');m=m[(m.baseline=='pre10')&(m.minutes==180)]
T=np.array([[66,22,10.5],[24,22,10.5],[66,66,10.5],[66,22,42]])
def model(name):
 if name=='lda':est=LinearDiscriminantAnalysis(solver='lsqr',shrinkage='auto')
 elif name=='tree':est=ExtraTreesClassifier(n_estimators=100,min_samples_leaf=4,random_state=500,n_jobs=1)
 else:est=SVC(C=float(name[3:]))
 return make_pipeline(SimpleImputer(add_indicator=True),StandardScaler(),est)
outputs=[];summaries=[];selection=[]
for s in ['Libre GL','Dexcom GL']:
 data=np.load(P/('balanced_'+s.split()[0]+'.npz'));Y=data['Y'];G=data['G'];ids=data['ids'];base=data['rich_180' if s=='Libre GL' else 'shape_180'];features={h:[] for h in [60,360,720]}
 rawcache={pid:pd.read_csv(ROOT/f'dataset/csv/CGMacros-{pid:03}.csv',parse_dates=['Timestamp']).set_index('Timestamp') for pid in np.unique(G)}
 def history(id,h):
  r=e.loc[id];raw=rawcache[r.pid];grid=r.time+pd.to_timedelta(np.arange(-h,0,15),unit='m');v=raw[s].reindex(grid).to_numpy(float);v=v-r[s+'_base'];hour=r.time.hour+r.time.minute/60
  return np.r_[v,np.isfinite(v).mean(),np.sin(2*np.pi*hour/24),np.cos(2*np.pi*hour/24)]
 for i,id in enumerate(ids):
  calids=m[(m.sensor==s)&(m.pid==G[i])].calibration_id.unique()
  for h in features:
   b=history(id,h);cal=np.array([history(cid,h) for cid in calids]);valid=np.isfinite(cal).sum(axis=0);mu=np.divide(np.nansum(cal,axis=0),valid,out=np.full(cal.shape[1],np.nan),where=valid>0)
   features[h].append(np.r_[base[i],b,b-mu])
 X={h:np.array(v) for h,v in features.items()};configs=[(h,a) for h in X for a in ['rbf0.1','rbf1','rbf10','lda','tree']];preds={f'{h}/{a}':np.zeros(len(Y),int) for h,a in configs};chosen=np.zeros(len(Y),int)
 for pid in np.unique(G):
  tr=np.flatnonzero(G!=pid);te=np.flatnonzero(G==pid);scores={}
  for h,a in configs:
   pp=np.zeros(len(tr),int)
   for it,iv in GroupKFold(4).split(tr,Y[tr],G[tr]):
    fit=model(a);fit.fit(X[h][tr[it]],Y[tr[it]]);pp[iv]=fit.predict(X[h][tr[iv]])
   name=f'{h}/{a}';scores[name]=float((pp==Y[tr]).mean());fit=model(a);fit.fit(X[h][tr],Y[tr]);preds[name][te]=fit.predict(X[h][te])
  best=max(scores,key=scores.get);chosen[te]=preds[best][te];selection.append(dict(sensor=s,pid=int(pid),selected=best,inner_scores=scores))
 preds['nested_selected']=chosen
 for name,pred in preds.items():
  err=abs(T[pred]-T[Y]);summaries.append(dict(sensor=s,method=name,meals=len(Y),hits=int((pred==Y).sum()),MAE=err.mean(axis=0).tolist()))
  for i,id in enumerate(ids):outputs.append(dict(sensor=s,pid=int(G[i]),id=id,method=name,actual_C=T[Y[i],0],actual_P=T[Y[i],1],actual_F=T[Y[i],2],predicted_C=T[pred[i],0],predicted_P=T[pred[i],1],predicted_F=T[pred[i],2],all_three_within10=bool(pred[i]==Y[i])))
 print(s,'done',flush=True)
pd.DataFrame(outputs).to_csv(OUT/'predictions.csv',index=False);(OUT/'summary.json').write_text(json.dumps(summaries,indent=2));(OUT/'selection.json').write_text(json.dumps(selection,indent=2));print(json.dumps([s for s in summaries if s['method']=='nested_selected'],indent=2))
