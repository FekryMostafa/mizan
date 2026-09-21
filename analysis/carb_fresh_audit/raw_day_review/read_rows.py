# Read stored source values only. Time offsets select rows; no signal calculations.
from pathlib import Path
import csv,datetime
R=Path(ROOT + '/dataset/csv');B=Path(__file__).resolve().parent.parent
with open(B/'backward_failures/selected_cases.csv') as fh:cases=list(csv.DictReader(fh))
with open(B/'libre_features.csv') as fh:refs=list(csv.DictReader(fh))
import sys
ROOT = str(Path(__file__).resolve().parents[3])  # repo root
for k in [int(v) for v in sys.argv[1:]]:
 c=cases[k-1];pid=int(c['pid']);true=float(c['actual']);ref=next(r for r in refs if int(r['pid'])==pid and r['role']==('low_calibration' if true==24 else 'high_calibration'))
 path=R/f'CGMacros-{pid:03}.csv'
 with open(path) as fh:
  reader=csv.DictReader(fh);rows=[{key.strip():val for key,val in r.items()} for r in reader]
 parsed=[]
 for r in rows:
  s=r['Timestamp']
  try:t=datetime.datetime.fromisoformat(s)
  except ValueError:t=datetime.datetime.strptime(s,'%m/%d/%Y %H:%M')
  parsed.append((t,r))
 print('\nCASE',k,'PERSON',pid,'RECORDED CARBS',c['actual'],'SOURCE',path.name)
 for role,ts in [('EARLIER',ref['time']),('FAILURE',c['time'])]:
  t=datetime.datetime.fromisoformat(ts);start=t-datetime.timedelta(days=1);end=t+datetime.timedelta(hours=3)
  print(role,ts,'MEAL ROWS: timestamp,type,carbs,protein,fat,fiber,consumed')
  for dt,r in parsed:
   if start<=dt<=end and r.get('Meal Type'):
    print(','.join([r['Timestamp']]+[r.get(v,'') for v in ['Meal Type','Carbs','Protein','Fat','Fiber','Amount Consumed']]))
  print('STORED SENSOR ROWS: timestamp,Libre,HR,activity_kcal,METs_or_Intensity')
  targets={t+datetime.timedelta(minutes=n) for n in [-1440,-1080,-720,-360,-180,-60,0,15,30,60,90,120,180]}
  for dt,r in parsed:
   if dt in targets:print(','.join([r['Timestamp'],r.get('Libre GL',''),r.get('HR',''),r.get('Calories (Activity)',''),r.get('METs',r.get('Intensity',''))]))
