from pathlib import Path
import json, hashlib
import numpy as np
import pandas as pd

O=Path(__file__).resolve().parent; B=O.parent
a=pd.read_csv(B/'formula_build/formula_inputs.csv',parse_dates=['time'])
j=json.loads((B/'formula_build/formula.json').read_text())
previous=json.loads((B/'formula_build_20/formula.json').read_text())
old=previous['steps'][-1]; cols=list(j['scaling']['means'])
assert len(a)==52 and not a.duplicated(['pid','time']).any()
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in j['source_hashes'].items())
raw=a[cols].to_numpy(float); target=a.actual.to_numpy(); base=a.base.to_numpy()
def scaled(s):
 med=np.array([s['medians'][c] for c in cols]);mu=np.array([s['means'][c] for c in cols]);sd=np.array([s['scales'][c] for c in cols])
 return (np.where(np.isfinite(raw),raw,med)-mu)/sd
med=np.array([np.nanmedian(v) if np.isfinite(v).any() else 0 for v in raw.T])
fill=np.where(np.isfinite(raw),raw,med);mu=fill.mean(axis=0);sd=fill.std(axis=0);sd[sd<1e-8]=1
scaling=dict(medians=dict(zip(cols,med)),means=dict(zip(cols,mu)),scales=dict(zip(cols,sd)))
x=scaled(scaling); oldx=scaled(previous['scaling'])
oldpred=np.maximum(0,base+old['coef'][0]+oldx[:,[cols.index(c) for c in old['terms']]]@old['coef'][1:])
matrix={c:x[:,i] for i,c in enumerate(cols)};definitions={c:[c] for c in cols}
terms=old['terms'].copy(); steps=[]
def add_step(name,pred,coef,rank=None):
 steps.append(dict(stage=name,terms=terms.copy(),coef=list(coef),rank=rank,pred=np.asarray(pred),hits=int((abs(pred-target)<=.1*target).sum()),mae=float(np.mean(abs(pred-target)))))
def fit(names):
 d=np.c_[np.ones(len(a)),np.column_stack([matrix[c] for c in names])]
 coef,_,rank,_=np.linalg.lstsq(d,target-base,rcond=1e-8)
 pred=np.maximum(0,base+d@coef)
 return coef,pred,int(rank)
add_step('previous_20_formula_unchanged',oldpred,old['coef'])
coef,pred,rank=fit(terms);add_step('same_14_terms_refit_on_52',pred,coef,rank)
for phase in ['linear','quadratic']:
 if (abs(pred-target)<=.1*target).all(): break
 if phase=='quadratic':
  # Increase representational capacity after exhausting independent linear terms.
  # No identity or label features. Products are of standardized observations.
  continuous=[c for c in cols if 'coverage' not in c and c!='prior_food_review' and np.std(matrix[c])>1e-8]
  for i,c in enumerate(continuous):
   for d in continuous[i:]:
    name=f'{c} * {d}';matrix[name]=matrix[c]*matrix[d];definitions[name]=[c,d]
 while not (abs(pred-target)<=.1*target).all() and len(terms)<51:
  options=[]
  for c in matrix:
   if c in terms or np.std(matrix[c])<1e-8:continue
   cc,pp,rr=fit(terms+[c])
   if rr<=rank:continue
   options.append((float(np.sum((pp-target)**2)),c,cc,pp,rr))
  if not options:break
  error,c,coef,pred,newrank=min(options,key=lambda v:(v[0],v[1]))
  terms.append(c);rank=newrank;add_step('add_'+c,pred,coef,rank)
records=[];summary=[]
for k,s in enumerate(steps):
 summary.append(dict(step=k,stage=s['stage'],terms=len(s['terms']),rank=s['rank'],hits=s['hits'],mae=s['mae']))
 for i,r in a.iterrows():
  value=s['pred'][i];records.append(dict(step=k,pid=r.pid,time=r.time,actual=r.actual,predicted=value,error_g=abs(value-r.actual),within10=abs(value-r.actual)<=.1*r.actual))
pd.DataFrame(records).to_csv(O/'predictions_each_step.csv',index=False);pd.DataFrame(summary).to_csv(O/'summary.csv',index=False)
result=dict(scope='Deliberate training fit on all 52 previously inspected queries; no validation set in these 52',
 formula='max(0, personal_full_curve_estimate + intercept + sum(coefficient * term))',
 scaling=scaling,old_scaling=previous['scaling'],definitions=definitions,
 steps=[{k:v for k,v in s.items() if k!='pred'} for s in steps],
 input_sha256=hashlib.sha256((B/'formula_build/formula_inputs.csv').read_bytes()).hexdigest(),source_hashes=j['source_hashes'])
(O/'formula.json').write_text(json.dumps(result,indent=2))
# Reconstruct from saved definitions and coefficients independently of fit().
saved=json.loads((O/'formula.json').read_text());xx=scaled(saved['scaling']);last=saved['steps'][-1]
recon=base+last['coef'][0]
for name,weight in zip(last['terms'],last['coef'][1:]):
 val=np.ones(len(a))
 for component in saved['definitions'][name]:val*=xx[:,cols.index(component)]
 recon+=weight*val
assert np.allclose(np.maximum(0,recon),steps[-1]['pred'],atol=1e-8,rtol=0)
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in j['source_hashes'].items())
print(pd.DataFrame(summary).to_string(index=False))
