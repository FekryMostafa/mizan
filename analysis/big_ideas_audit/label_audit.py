"""Development-only reference-label audit; flags do not invent corrected grams."""
from pathlib import Path
import json
import pandas as pd
import numpy as np

BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[1]
OUT=BASE/'label_audit';OUT.mkdir(exist_ok=True)
rows=[]
for pid in range(1,9):
    f=ROOT/f'dataset/big_ideas_1_1_3/{pid:03}/Food_Log_{pid:03}.csv'
    d=pd.read_csv(f)
    required=['time_begin','logged_food','amount','unit','calorie','total_carb','protein','total_fat']
    if not set(required)<=set(d.columns):
        continue
    for n,r in d.iterrows():
        v=pd.to_numeric(r[['total_carb','protein','total_fat']],errors='coerce')
        complete=bool(v.notna().all());mass=float(v.sum()) if complete else np.nan
        amount=pd.to_numeric(r.amount,errors='coerce');unit=str(r.unit).strip().lower()
        gram_unit=unit in ['gram','grams','g'] and pd.notna(amount) and amount>0
        # Broad tolerance avoids flagging small rounding differences.
        mass_conflict=bool(gram_unit and complete and mass>amount*1.1)
        kcal=pd.to_numeric(r.calorie,errors='coerce')
        kcal_macro=float(v.iloc[0]*4+v.iloc[1]*4+v.iloc[2]*9) if complete else np.nan
        mismatch=bool(complete and pd.notna(kcal) and kcal>0 and abs(kcal_macro-kcal)/kcal>.2)
        rows.append(dict(pid=pid,source_row=n+2,time=str(r.time_begin),food=str(r.logged_food),
                         amount=amount,unit=unit,Carbs=v.iloc[0],Protein=v.iloc[1],Fat=v.iloc[2],
                         Calories=kcal,complete_macros=complete,gram_unit=gram_unit,
                         macro_mass=mass,mass_conflict=mass_conflict,
                         calorie_macro_mismatch=mismatch,macro_kcal=kcal_macro))
d=pd.DataFrame(rows);d.to_csv(OUT/'food_item_audit.csv',index=False)
d[d.mass_conflict|d.calorie_macro_mismatch|~d.complete_macros].to_csv(OUT/'review_queue.csv',index=False)
meal=d.groupby(['pid','time']).agg(items=('food','size'),mass_conflict=('mass_conflict','any'),
    component_calorie_mismatch=('calorie_macro_mismatch','any'),missing_component=('complete_macros',lambda v:not v.all())).reset_index()
pred=pd.read_csv(BASE/'transfer_model/predictions.csv');pred=pred[pred.method=='trees5/kernel']
merged=pred.merge(meal,on=['pid','time'],validate='one_to_one')
assert len(merged)==len(pred)==65
merged.to_csv(OUT/'prediction_label_flags.csv',index=False)
summary=dict(development_food_items=len(d),explicit_gram_items=int(d.gram_unit.sum()),
    mass_conflict_items=int(d.mass_conflict.sum()),component_calorie_mismatches=int(d.calorie_macro_mismatch.sum()),
    query_meals=65,queries_with_mass_conflict=int(merged.mass_conflict.sum()),
    queries_with_component_calorie_mismatch=int(merged.component_calorie_mismatch.sum()),
    note='Mass flags imply inconsistency among reported quantity, units and macros, not which field is wrong. '
         'Calorie mismatch is only a review flag: alcohol, fiber, food factors and rounding can contribute.')
(OUT/'summary.json').write_text(json.dumps(summary,indent=2))
print(json.dumps(summary,indent=2));print(d[d.mass_conflict][['pid','time','food','amount','unit','macro_mass','Calories']].to_string(index=False))
