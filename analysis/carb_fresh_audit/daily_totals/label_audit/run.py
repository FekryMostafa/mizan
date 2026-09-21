from pathlib import Path
import json,zipfile,hashlib
import pandas as pd
ROOT = str(Path(__file__).resolve().parents[4])  # repo root
ROOT=Path(__file__).resolve().parent
SRC=Path(ROOT + '/dataset')
m=pd.read_csv(SRC/'cgmacros_clean_v1/meals.csv');m['day']=pd.to_datetime(m.timestamp).dt.strftime('%Y-%m-%d')
daily=pd.read_csv(ROOT.parent/'delayed_probe/later_results.csv')
rows=[]
with zipfile.ZipFile(SRC/'cgmacros_raw/CGMacros_dateshifted365.zip') as z:
    names=set(z.namelist())
    for _,r in m.iterrows():
        path=r.image_path_reported
        member=f'CGMacros/CGMacros-{int(r.participant_id):03}/{path}' if isinstance(path,str) else ''
        found=member in names
        data=z.read(member) if found else b''
        rows.append(dict(record_id=r.record_id,photo_present=found,photo_sha256=hashlib.sha256(data).hexdigest() if found else '',archive_member=member))
    m=m.merge(pd.DataFrame(rows),on='record_id',validate='one_to_one')
    m['same_time_duplicate']=m.duplicated(['participant_id','timestamp','carbs_reported','fat_reported','protein_reported'],keep=False)
    m['same_day_photo_duplicate']=m.photo_present & m.duplicated(['participant_id','day','photo_sha256'],keep=False)
    m['any_photo_duplicate']=m.photo_present & m.duplicated('photo_sha256',keep=False)
    m['macro_kcal_449']=4*m.carbs_g+4*m.protein_g+9*m.fat_g
    m['kcal_difference']=m.calories_reported-m.macro_kcal_449
    m.to_csv(ROOT/'all_meal_audit.csv',index=False)
    q=daily.rename(columns={'pid':'participant_id'}).merge(m,on=['participant_id','day'])
    q.to_csv(ROOT/'evaluation_meal_audit.csv',index=False)
    top=daily.sort_values('delayed_ape',ascending=False).head(10)
    keys=set(zip(top.pid,top.day)); keys.add((4,'2023-09-19'))
    detailed=[]
    for pid,day in sorted(keys):
        g=m[(m.participant_id==pid)&(m.day==day)]
        assert abs(g.carbs_g.sum()-daily[(daily.pid==pid)&(daily.day==day)].actual.iloc[0])<1e-8
        detailed.append(dict(pid=pid,day=day,carbs=float(g.carbs_g.sum()),meal_records=len(g),photos=int(g.photo_present.sum()),same_day_duplicate_photos=int(g.same_day_photo_duplicate.sum()),same_time_duplicates=int(g.same_time_duplicate.sum()),reported_kcal=float(g.calories_reported.sum()),macro_kcal=float(g.macro_kcal_449.sum())))
    pd.DataFrame(detailed).to_csv(ROOT/'worst_days.csv',index=False)
    chosen=q[(q.participant_id==4)&(q.day=='2023-09-19')]
    paths=[]
    for _,r in chosen.iterrows():
        if not r.photo_present:continue
        path=ROOT/f'p4_{int(r.source_row)}.jpg';path.write_bytes(z.read(r.archive_member));paths.append(dict(path=str(path),timestamp=r.timestamp,carbs=r.carbs_g,fat=r.fat_g,protein=r.protein_g,calories=r.calories_reported))
    (ROOT/'p4_photos.json').write_text(json.dumps(paths,indent=2))
summary=dict(all_meal_records=len(m),all_found_photos=int(m.photo_present.sum()),evaluation_days=len(daily),evaluation_records=len(q),evaluation_photos=int(q.photo_present.sum()),evaluation_same_day_duplicate_photo_records=int(q.same_day_photo_duplicate.sum()),evaluation_same_time_duplicate_records=int(q.same_time_duplicate.sum()),evaluation_anywhere_reused_photo_records=int(q.any_photo_duplicate.sum()),labels_changed=0)
(ROOT/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2));print(pd.DataFrame(detailed).to_string(index=False));print(json.dumps(paths[:3],indent=2))
