"""Exact and tightly rounded curve fingerprint audit of prior eligible cohorts."""
from pathlib import Path
import hashlib,json
import numpy as np
import pandas as pd
B=Path(__file__).resolve().parent
O=B/'duplicate_audit';O.mkdir(exist_ok=True)
f=pd.read_csv(B/'features.csv')
x=np.load(B/'curve_audit/curves.npz',allow_pickle=False)['X']
manifest=json.loads((B/'curve_audit/manifest.json').read_text())
assert hashlib.sha256((B/'features.csv').read_bytes()).hexdigest()==manifest['input_sha256']
assert x.shape==(len(f),37) and np.isfinite(x).all()
assert np.allclose(x.max(axis=1),f.peak_height,atol=1e-6,rtol=0)
views={'baseline_relative_exact':x,'absolute_rounded_6':np.round(x+f.baseline.to_numpy()[:,None],6),
       'shape_rounded_6':np.round(x-x[:,[0]],6)}
summaries=[];all_duplicates=[]
for name,values in views.items():
    values=values.copy();values[values==0]=0 # Normalize signed zero.
    z=f[['dataset','pid','time']].copy()
    z['sha256']=[hashlib.sha256(np.asarray(v,dtype='<f8').tobytes()).hexdigest() for v in values]
    z['representation']=name
    duplicated=z[z.duplicated('sha256',keep=False)]
    all_duplicates.append(duplicated)
    for dataset,q in z.groupby('dataset'):
        du=q[q.duplicated('sha256',keep=False)]
        summaries.append(dict(representation=name,dataset=dataset,curves=len(q),unique=q.sha256.nunique(),
                              duplicate_rows=len(du),duplicate_groups=du.sha256.nunique()))
    cross=z.groupby('sha256').dataset.nunique()
    assert not cross.gt(1).any(), 'Cross-dataset duplicate requires split-level investigation.'
    z.to_csv(O/(name+'_fingerprints.csv'),index=False)
pd.concat(all_duplicates).to_csv(O/'duplicate_records.csv',index=False)
(O/'summary.json').write_text(json.dumps(summaries,indent=2))
(O/'manifest.json').write_text(json.dumps(dict(script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    source_feature_hash_verified=True,input_hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [B/'features.csv',B/'curve_audit/curves.npz']},
    reserved_accessed=False,scope='Existing 738 eligible curves only; not raw full releases or all forms of data leakage.'),indent=2))
print(json.dumps(summaries,indent=2))
print(pd.concat(all_duplicates).to_string(index=False))
