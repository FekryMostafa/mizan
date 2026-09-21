from pathlib import Path
import json,hashlib
import numpy as np
import pandas as pd

O=Path(__file__).resolve().parent;B=O.parent;P=B/'formula_build'
a=pd.read_csv(P/'formula_inputs.csv',parse_dates=['time'])
j=json.loads((P/'formula.json').read_text());old=j['steps'][7]
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in j['source_hashes'].items())
past=pd.read_csv(B/'calibration_test/case_comparison.csv',parse_dates=['time'])
merged=a.merge(past[['pid','time','within10']],on=['pid','time'],validate='one_to_one')
selected=merged[merged.target_case].copy();selected['selection']='original_ten_failures'
new=[]
# Freeze selection before computing any new predictions. Five old successes and
# five old failures; three low-dose and two high-dose in each. No score ranking.
for success in [True,False]:
 for dose,n in [(24,3),(66,2)]:
  z=merged[(~merged.target_case)&merged.within10.eq(success)&merged.actual.eq(dose)].sort_values(['pid','time']).head(n).copy()
  assert len(z)==n
  z['selection']='added_old_success' if success else 'added_old_failure';new.append(z)
sel=pd.concat([selected,*new]);assert len(sel)==20 and not sel.duplicated(['pid','time']).any()
sel[['pid','time','actual','selection']].to_csv(O/'selected_20.csv',index=False)
keys=set(zip(sel.pid,sel.time));train=np.array([(r.pid,r.time) in keys for r in a.itertuples()])
assert train.sum()==20
cols=list(j['scaling']['means']);raw=a[cols].to_numpy(float)
def scale(s):
 med=np.array([s['medians'][c] for c in cols]);mu=np.array([s['means'][c] for c in cols]);sd=np.array([s['scales'][c] for c in cols]);return (np.where(np.isfinite(raw),raw,med)-mu)/sd
oldx=scale(j['scaling']);oldpred=np.maximum(0,a.base+old['coef'][0]+oldx[:,[cols.index(c) for c in old['terms']]]@old['coef'][1:])
med=np.array([np.nanmedian(v) if np.isfinite(v).any() else 0 for v in raw[train].T]);filled=np.where(np.isfinite(raw),raw,med);mu=filled[train].mean(axis=0);sd=filled[train].std(axis=0);sd[sd<1e-8]=1
x=(filled-mu)/sd;target=a.actual.to_numpy();base=a.base.to_numpy();residual=target-base
terms=old['terms'].copy()
steps=[dict(stage='old_formula_unchanged',terms=terms.copy(),coef=old['coef'],pred=np.array(oldpred),scaling='old_ten')]
def fit(names):
 design=np.c_[np.ones(len(a)),x[:,[cols.index(c) for c in names]]]
 coef=np.linalg.lstsq(design[train],residual[train],rcond=1e-8)[0]
 pred=np.maximum(0,base+design@coef)
 return coef,pred,int(np.linalg.matrix_rank(design[train]))
coef,pred,rank=fit(terms);steps.append(dict(stage='same_seven_terms_refit_on_20',terms=terms.copy(),coef=coef.tolist(),pred=pred,rank=rank,scaling='twenty'))
while not np.all(abs(pred[train]-target[train])<=.1*target[train]) and len(terms)<19:
 options=[]
 for c in cols:
  if c in terms or np.std(x[train,cols.index(c)])<1e-8:continue
  cc,pp,rr=fit(terms+[c]);err=pp[train]-target[train];options.append((float(err@err),c,cc,pp,rr))
 assert options
 _,c,coef,pred,rank=min(options,key=lambda v:(v[0],cols.index(v[1])))
 terms.append(c);steps.append(dict(stage='add_'+c,terms=terms.copy(),coef=coef.tolist(),pred=pred,rank=rank,scaling='twenty'))
rows=[];summary=[]
for k,s in enumerate(steps):
 for i,r in a.iterrows():
  er=abs(s['pred'][i]-r.actual);rows.append(dict(step=k,stage=s['stage'],pid=r.pid,time=r.time,actual=r.actual,predicted=s['pred'][i],error_g=er,within10=er<=.1*r.actual,in_twenty=bool(train[i]),original_ten=bool(r.target_case)))
 for name,mask in [('twenty_fit',train),('original_ten',a.target_case.to_numpy()),('added_ten',train&~a.target_case.to_numpy()),('other32_diagnostic',~train)]:
  err=abs(s['pred'][mask]-target[mask]);summary.append(dict(step=k,stage=s['stage'],terms=len(s['terms']),group=name,n=int(mask.sum()),hits=int((err<=.1*target[mask]).sum()),mae=float(err.mean())))
p=pd.DataFrame(rows);p.to_csv(O/'predictions_each_step.csv',index=False);s=pd.DataFrame(summary);s.to_csv(O/'summary.csv',index=False)
scaling=dict(medians=dict(zip(cols,med)),means=dict(zip(cols,mu)),scales=dict(zip(cols,sd)))
result=dict(scope='Deliberate fitting on 20 previously inspected meals; not generalization evidence',selection='Original ten plus five old successes/five old failures; each added group has 3 low and 2 high, sorted by participant then time',steps=[{k:v for k,v in st.items() if k!='pred'} for st in steps],scaling=scaling,old_scaling=j['scaling'])
(O/'formula.json').write_text(json.dumps(result,indent=2))
last=steps[-1];check=np.maximum(0,base+last['coef'][0]+scale(scaling)[:,[cols.index(c) for c in last['terms']]]@last['coef'][1:]);assert np.allclose(check,last['pred'],atol=1e-9,rtol=0)
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in j['source_hashes'].items())
print(s[s.group.isin(['twenty_fit','other32_diagnostic'])].to_string(index=False))
print(p[(p.step==len(steps)-1)&p.in_twenty][['pid','actual','predicted','within10']].to_string(index=False))
