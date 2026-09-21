"""Inspect labeled CGM data for fat-dose information; no model training."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
SENSORS=['Libre GL','Dexcom GL']
grid=np.arange(-15,301)
events=[]; curves={}; quality=[]; all_food={}
for f in sorted((ROOT/'dataset/csv').glob('CGMacros-*.csv')):
    pid=int(f.stem.split('-')[1])
    d=pd.read_csv(f,parse_dates=['Timestamp']).sort_values('Timestamp')
    d.columns=d.columns.str.strip()
    if 'Amount Consumed' not in d: d['Amount Consumed']=np.nan
    quality.append({'participant':pid,'rows':len(d),'duplicate_timestamps':int(d.Timestamp.duplicated().sum()),
                    **{s+'_missing_fraction':float(d[s].isna().mean()) for s in SENSORS}})
    assert not d.Timestamp.duplicated().any()
    d=d.set_index('Timestamp')
    food=d[d['Meal Type'].notna() | d['Calories'].notna() | d['Carbs'].notna()]
    all_food[pid]=food
    for idx,(t,r) in enumerate(food.iterrows()):
        if not all(pd.notna(r.get(k)) for k in ['Carbs','Protein','Fat']):continue
        gap=(food.index[idx+1]-t).total_seconds()/60 if idx+1<len(food) else np.nan
        prev=(t-food.index[idx-1]).total_seconds()/60 if idx else np.nan
        rid=f'{pid:03d}_{t.isoformat()}'
        e={'id':rid,'participant':pid,'time':t.isoformat(),'meal_type':str(r['Meal Type']).lower(),
           'carbs':r.Carbs,'protein':r.Protein,'fat':r.Fat,'fiber':r.Fiber,
           'amount_consumed':r['Amount Consumed'],'next_food_min':gap,'previous_food_min':prev}
        e['fat_group']=('low' if r.Fat==10.5 else 'high') if (e['meal_type']=='breakfast' and
            r.Carbs==66 and r.Protein==22 and r.Fat in [10.5,42] and r.Fiber==0 and r['Amount Consumed']==100) else ''
        times=t+pd.to_timedelta(grid,unit='m')
        segment=d.reindex(times)
        for sensor in SENSORS:
            a=segment[sensor].to_numpy(float)
            pre=a[(grid<0)&(grid>=-10)]
            baseline=float(np.nanmedian(pre)) if np.isfinite(pre).sum()>=8 else np.nan
            delta=a-baseline
            curves[(rid,sensor)]=delta
            e[sensor+'_baseline']=baseline
            for horizon in [60,120,180,300]:
                mask=(grid>=0)&(grid<=horizon)
                # No filling missing observations and no interpolating through later meals.
                valid=bool(np.isfinite(delta[mask]).all() and
                    (pd.isna(gap) or gap>horizon) and (pd.isna(prev) or prev>=180))
                e[f'{sensor}_valid{horizon}']=valid
                if valid:
                    z=delta[mask]; gg=grid[mask]
                    e[f'{sensor}_mean{horizon}']=float(np.trapezoid(z,x=gg)/horizon)
                    e[f'{sensor}_peak{horizon}']=float(z.max())
                    e[f'{sensor}_timepeak{horizon}']=int(gg[z.argmax()])
                    if horizon>=180:
                        tail=gg>=120
                        e[f'{sensor}_tail{horizon}']=float(np.trapezoid(z[tail],x=gg[tail])/(horizon-120))
        events.append(e)

e=pd.DataFrame(events); e.to_csv(OUT/'meal_inventory.csv',index=False)
pd.DataFrame(quality).to_csv(OUT/'source_quality.csv',index=False)
matched=e[e.fat_group!=''].copy(); matched.to_csv(OUT/'matched_breakfasts.csv',index=False)
summary={'labeled_events':len(e),'participants':int(e.participant.nunique()),
         'exact_fat_only':int(((e.carbs==0)&(e.protein==0)&(e.fat>0)).sum()),
         'matched_breakfasts':matched.groupby('fat_group').size().to_dict(),
         'matched_participants':int(matched.participant.nunique()),
         'all_events_no_later_food_for_hours':{str(h):int(((e.next_food_min>h*60)|e.next_food_min.isna()).sum()) for h in [1,2,3,5]},
         'sensor_comparisons':{},'no_model_trained':True}
pair_rows=[]; repeat_rows=[]
fig,axes=plt.subplots(2,3,figsize=(14,8))
for row,sensor in enumerate(SENSORS):
    for horizon in [180,300]:
        sub=matched[matched[f'{sensor}_valid{horizon}']]
        groups=sub.groupby(['participant','fat_group'])
        means=groups[[f'{sensor}_mean{horizon}',f'{sensor}_timepeak{horizon}',f'{sensor}_tail{horizon}']].mean()
        paired=[]
        for pid in sub.participant.unique():
            if (pid,'low') not in means.index or (pid,'high') not in means.index:continue
            diff=means.loc[(pid,'high')]-means.loc[(pid,'low')]
            pr={'sensor':sensor,'horizon':horizon,'participant':int(pid),
                'mean_delta_high_minus_low':float(diff.iloc[0]),
                'peak_delay_high_minus_low_min':float(diff.iloc[1]),
                'tail_delta_high_minus_low':float(diff.iloc[2])}
            pair_rows.append(pr);paired.append(pr)
        key=f'{sensor}_{horizon}'
        summary['sensor_comparisons'][key]={'usable_low':int((sub.fat_group=='low').sum()),
            'usable_high':int((sub.fat_group=='high').sum()),'paired_people':len(paired)}
        if paired:
            pp=pd.DataFrame(paired)
            for col in ['mean_delta_high_minus_low','peak_delay_high_minus_low_min','tail_delta_high_minus_low']:
                summary['sensor_comparisons'][key][col]={'median':float(pp[col].median()),
                    'q25':float(pp[col].quantile(.25)),'q75':float(pp[col].quantile(.75)),
                    'positive_people':int((pp[col]>0).sum())}
        # Same-label repeated-day differences, same clean-window criteria.
        for (pid,grp), ss in groups:
            if len(ss)<2:continue
            ss=ss.sort_values('time')
            first,last=ss.iloc[0],ss.iloc[-1]
            diff=abs(last[f'{sensor}_mean{horizon}']-first[f'{sensor}_mean{horizon}'])
            repeat_rows.append({'sensor':sensor,'horizon':horizon,'participant':int(pid),
                                'group':grp,'abs_same_recipe_mean_difference':float(diff)})
        if horizon==180 and paired:
            pids=[p['participant'] for p in paired]
            for grp,col,label in [('low','#2665a8','10.5 g fat'),('high','#d77a21','42 g fat')]:
                arr=[]
                for pid in pids:
                    ids=sub[(sub.participant==pid)&(sub.fat_group==grp)].id
                    arr.append(np.mean([curves[(rid,sensor)][(grid>=0)&(grid<=180)] for rid in ids],axis=0))
                arr=np.array(arr); tt=np.arange(181)
                axes[row,0].plot(tt,arr.mean(axis=0),color=col,label=f'{label}, {len(pids)} people')
            axes[row,0].set(title=sensor+': paired-person average',xlabel='Minutes after breakfast',ylabel='Change from baseline (mg/dL)')
            axes[row,0].legend(fontsize=8)
            pp=pd.DataFrame(paired).sort_values('participant')
            axes[row,1].bar(np.arange(len(pp)),pp.tail_delta_high_minus_low,color='#557d96')
            axes[row,1].axhline(0,color='black',lw=.8)
            axes[row,1].set(title='Extra fat: change in 2–3 hour tail',xlabel='Participant (sorted by ID)',ylabel='High minus low fat (mg/dL)')
            same=[r['abs_same_recipe_mean_difference'] for r in repeat_rows if r['sensor']==sensor and r['horizon']==180]
            between=abs(pp.mean_delta_high_minus_low).tolist()
            axes[row,2].boxplot([between,same],tick_labels=['10.5 vs 42 g fat','Same recipe\nrepeat days'],showfliers=True)
            axes[row,2].set(title='Response differences versus repeat variability',ylabel='Absolute difference in 0–3h mean (mg/dL)')
for ax in axes.flat:ax.grid(axis='y',alpha=.2)
fig.suptitle('Same 66 g carbs / 22 g protein / 0 g fiber; only labeled fat differs',fontsize=15)
fig.tight_layout(rect=[0,0,1,.95]);fig.savefig(OUT/'matched_fat_comparison.png',dpi=150);plt.close(fig)
pd.DataFrame(pair_rows).to_csv(OUT/'paired_person_differences.csv',index=False)
pd.DataFrame(repeat_rows).to_csv(OUT/'repeat_variability.csv',index=False)
for sensor in SENSORS:
    rr=[r['abs_same_recipe_mean_difference'] for r in repeat_rows if r['sensor']==sensor and r['horizon']==180]
    summary['sensor_comparisons'][sensor+'_180']['same_recipe_repeat_median_abs_difference']=float(np.median(rr)) if rr else None
    summary['sensor_comparisons'][sensor+'_180']['same_recipe_repeat_pairs']=len(rr)
    pp=[abs(r['mean_delta_high_minus_low']) for r in pair_rows if r['sensor']==sensor and r['horizon']==180]
    summary['sensor_comparisons'][sensor+'_180']['fat_contrast_median_abs_difference']=float(np.median(pp)) if pp else None

# Every eligible participant's paired mean curves, not selected by desired direction.
sensor='Libre GL';sub=matched[matched[f'{sensor}_valid180']]
pids=[pid for pid,g in sub.groupby('participant') if g.fat_group.nunique()==2]
fig,axes=plt.subplots(int(np.ceil(len(pids)/5)),5,figsize=(15,int(np.ceil(len(pids)/5))*2.4),squeeze=False)
for ax,pid in zip(axes.flat,pids):
    for grp,color in [('low','#2665a8'),('high','#d77a21')]:
        ids=sub[(sub.participant==pid)&(sub.fat_group==grp)].id
        for rid in ids:ax.plot(grid,curves[(rid,sensor)],color=color,alpha=.35,lw=.8)
        a=np.mean([curves[(rid,sensor)] for rid in ids],axis=0)
        ax.plot(grid,a,color=color,lw=2,label=f'{grp} fat')
    ax.set(xlim=(0,180),title=f'Participant {pid}',xlabel='Minutes');ax.axhline(0,color='gray',lw=.5)
for ax in list(axes.flat)[len(pids):]:ax.set_visible(False)
axes.flat[0].legend(fontsize=7)
fig.suptitle('All eligible Libre participants: orange 42 g fat, blue 10.5 g; thin lines = repeat days')
fig.tight_layout(rect=[0,0,1,.97]);fig.savefig(OUT/'all_person_curves.png',dpi=130);plt.close(fig)

# The previously identified near-fat-only snack; show later food explicitly.
target=e[(e.participant==10)&(e.time=='2020-06-30T16:27:00')].iloc[0]
fig,ax=plt.subplots(figsize=(10,4))
for sensor in SENSORS:ax.plot(grid,curves[(target.id,sensor)],label=sensor)
later=all_food[10];t=pd.Timestamp(target.time)
for ft,fr in later.iterrows():
    dt=(ft-t).total_seconds()/60
    if 0<dt<=300:
        ax.axvline(dt,color='red',ls='--');ax.text(dt+3,-25,f'Next food at {dt:g} min\n{fr.Carbs:g}C / {fr.Protein:g}P / {fr.Fat:g}F',fontsize=8,va='bottom')
ax.axvspan(73,300,color='red',alpha=.05)
ax.set(title='14 g fat / 2 g carbs / 4 g protein snack: participant 10',xlabel='Minutes after snack',ylabel='Change from baseline (mg/dL)',xlim=(-15,300))
ax.legend();fig.tight_layout();fig.savefig(OUT/'near_fat_only_snack.png',dpi=150);plt.close(fig)
summary['near_fat_only_snack']={'participant':10,'carbs':2,'protein':4,'fat':14,'next_food_min':73,
    'previous_food_min':float(target.previous_food_min),**{s+'_baseline':float(target[s+'_baseline']) for s in SENSORS}}
(OUT/'summary.json').write_text(json.dumps(summary,indent=2,allow_nan=False))
print(json.dumps(summary,indent=2))
