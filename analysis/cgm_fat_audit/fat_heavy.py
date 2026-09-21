"""Individual traces for every event with >=10g fat and <=10g carbs."""
from pathlib import Path
import json
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

OUT=Path(__file__).resolve().parent/'fat_heavy'
OUT.mkdir(exist_ok=True)
ROOT=OUT.parents[2]
events=pd.read_csv(OUT.parent/'meal_inventory.csv')
chosen=events[(events.fat>=10)&(events.carbs<=10)].copy()
chosen['fat_energy_fraction']=9*chosen.fat/(9*chosen.fat+4*chosen.carbs+4*chosen.protein)
chosen=chosen.sort_values('fat_energy_fraction',ascending=False)
metrics=[];contexts=[];loaded={};traces={}
sensors=['Libre GL','Dexcom GL']
grid=np.arange(-60,361)
for _,e in chosen.iterrows():
    pid=int(e.participant);t=pd.Timestamp(e.time)
    if pid not in loaded:
        d=pd.read_csv(ROOT/f'dataset/csv/CGMacros-{pid:03d}.csv',parse_dates=['Timestamp'])
        d.columns=d.columns.str.strip();loaded[pid]=d.set_index('Timestamp').sort_index()
    d=loaded[pid];seg=d.reindex(t+pd.to_timedelta(grid,unit='m'))
    nearby=events[(events.participant==pid)].copy()
    nearby['relative_min']=(pd.to_datetime(nearby.time)-t).dt.total_seconds()/60
    nearby=nearby[(nearby.relative_min>=-360)&(nearby.relative_min<=360)]
    for _,n in nearby.iterrows():contexts.append({'target_id':e.id,'relative_min':n.relative_min,'carbs':n.carbs,'protein':n.protein,'fat':n.fat,'type':n.meal_type})
    curves=[]
    for sensor in sensors:
        a=seg[sensor].to_numpy(float)
        pre=a[(grid>=-10)&(grid<0)]
        baseline=float(np.nanmedian(pre)) if np.isfinite(pre).sum()>=8 else np.nan
        z=a-baseline;curves.append(z)
        row={'id':e.id,'participant':pid,'time':e.time,'carbs':e.carbs,'protein':e.protein,'fat':e.fat,
             'amount_consumed':e.amount_consumed,'fat_energy_fraction':e.fat_energy_fraction,
             'previous_food_min':e.previous_food_min,'next_food_min':e.next_food_min,'sensor':sensor,
             'baseline_mgdl':baseline,'postmeal_6h_coverage':float(np.isfinite(a[grid>=0]).mean()),
             'premeal_30min_change':float(a[grid==-1][0]-a[grid==-30][0])}
        for name,lo,hi in [('early',0,72),('middle',73,180),('late',181,300),('six_hour',0,360)]:
            stop=min(hi,int(e.next_food_min)-1) if pd.notna(e.next_food_min) else hi
            keep=(grid>=lo)&(grid<=stop)
            row[name+'_end_min']=stop
            valid=keep.sum()>=10 and np.isfinite(z[keep]).all()
            row[name+'_usable']=bool(valid)
            if valid:
                v=z[keep];tt=grid[keep]
                row[name+'_peak_rise']=float(v.max());row[name+'_peak_min']=int(tt[v.argmax()])
                row[name+'_mean_change']=float(np.trapezoid(v,x=tt)/(tt[-1]-tt[0]))
        metrics.append(row)
    traces[e.id]=curves

pd.DataFrame(metrics).to_csv(OUT/'measurements.csv',index=False)
pd.DataFrame(contexts).to_csv(OUT/'nearby_food.csv',index=False)
chosen.to_csv(OUT/'selected_events.csv',index=False)
# All cases shown in rank order, including problematic ones.
for page in range(0,len(chosen),6):
    batch=chosen.iloc[page:page+6];fig,axes=plt.subplots(3,2,figsize=(13,11))
    for ax,(_,e) in zip(axes.flat,batch.iterrows()):
        for sensor,z in zip(sensors,traces[e.id]):ax.plot(grid,z,label=sensor,lw=1.5)
        ax.axvline(0,color='black',lw=.8);ax.axhline(0,color='gray',lw=.5)
        if pd.notna(e.next_food_min) and e.next_food_min<=360:
            ax.axvspan(e.next_food_min,360,color='red',alpha=.07)
            ax.axvline(e.next_food_min,color='red',ls='--',lw=1)
        if pd.notna(e.previous_food_min) and e.previous_food_min<=60:
            ax.axvline(-e.previous_food_min,color='red',ls='--',lw=1)
        ax.set(xlim=(-60,360),xlabel='Minutes relative to meal',ylabel='Glucose change (mg/dL)',
               title=f'P{int(e.participant)} {e.time[:10]} | {e.carbs:g}C / {e.protein:g}P / {e.fat:g}F\n'
               f'Prior food {e.previous_food_min:g} min; next {e.next_food_min:g} min; consumed {e.amount_consumed:g}%')
        ax.grid(alpha=.15)
        ax.title.set_fontsize(9)
    for ax in list(axes.flat)[len(batch):]:ax.set_visible(False)
    axes.flat[0].legend(fontsize=8)
    fig.suptitle('Low-carb, fat-heavy records; red shading = after next logged food',fontsize=15)
    fig.tight_layout(rect=[0,0,1,.96]);fig.savefig(OUT/f'cases_{page//6+1}.png',dpi=140);plt.close(fig)
# Repeat with the same macro labels, prior/post meal context visible.
rep=chosen[(chosen.participant==14)&(chosen.fat==18)]
fig,axes=plt.subplots(1,2,figsize=(12,4.5))
for j,(ax,sensor) in enumerate(zip(axes,sensors)):
    for _,e in rep.iterrows():ax.plot(grid,traces[e.id][j],label=e.time[:10])
    ax.axvline(0,color='black',lw=.8);ax.axhline(0,color='gray',lw=.5)
    ax.set(xlim=(-60,360),xlabel='Minutes relative to snack',ylabel='Glucose change (mg/dL)',title=sensor)
    ax.legend();ax.grid(alpha=.15)
fig.suptitle('Same person, same logged 18 g fat / 7 g carbs / 6 g protein; two days')
fig.tight_layout();fig.savefig(OUT/'repeated_18g_snack.png',dpi=150);plt.close(fig)
m=pd.DataFrame(metrics)
print('Total candidates',len(chosen))
print(m[m.participant.isin([2,10,14,28,34])][['participant','time','sensor','carbs','protein','fat','premeal_30min_change','early_peak_rise','early_peak_min','late_mean_change','late_peak_rise','postmeal_6h_coverage']].to_string(index=False))
