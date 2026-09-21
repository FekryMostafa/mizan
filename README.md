# Mizan — can wearables replace food logging?

**Question.** Can carbohydrate, protein and fat grams be recovered per meal, within ±10%, from
a continuous glucose monitor plus wrist signals, after a one-time personal calibration?

**Answer so far (Sep 2026): no for fat and protein, partially for carbs.** This repo is the
audit trail: cleaned public datasets, personalized calibration experiments, controls, and an
honest feasibility log. The negative result is consistent with the physiology (dietary fat
enters blood as chylomicrons via lymph and never becomes glucose; its echo on the glucose
curve is cancelled by insulin) and with the published literature (CGMacros CGM-only NRMSE:
carbs 29%, protein 46%, fat 40%; MealMeter carb MAE 13 g / 37% relative in lab conditions).

Start with [`analysis/FEASIBILITY_STATUS.md`](analysis/FEASIBILITY_STATUS.md).

## What was done

| Step | Where | Result |
|---|---|---|
| Clean + audit CGMacros (45 people, 10 days, two CGMs, logged macros) | `analysis/data_quality`, `dataset/cgmacros_clean_v1` | 738 eligible meals; no duplicate curves; label inconsistencies documented |
| Independent cohort: BIG IDEAs (16 people, Dexcom G6) with 8 participants reserved untouched before any parsing | `analysis/big_ideas_audit` | 86 development meals; reserved split frozen in `dataset/big_ideas_1_1_3/RESERVED_SPLIT.json` |
| Stanford CGM database audit | `analysis/stanford_cgmdb_audit` | 578 distinct curves of 588 sessions; duplicate pairs found and excluded |
| Per-macro feature study on 5-min grids (18 curve features, 652 + 86 meals) | `analysis/macro_features` | Carbs: peak rise r≈+0.43–0.48. Fat: max rise slope r≈−0.12 to −0.24. Protein: variability r≈−0.20. Fat/protein signals are near noise |
| Matched-meal fat contrast (66 g carb / 22 g protein shakes at 10.5 g vs 42 g fat, 33 people, both sensors) | `analysis/cgm_fat_audit` | Higher fat: median peak delay ≈ +11 min, early response ≈ −5 mg/dL. Tail effect not consistent. Repeat-day variability (12–14 mg/dL) exceeds the fat contrast (7–8 mg/dL) |
| Personalized calibration → later-meal prediction (linear and nonlinear, with/without EDA/skin-temp) | `analysis/macro_features/*`, `analysis/big_ideas_audit/skin_*` | Best: carbs 6/65 within ±10%, MAE 39.7 g. Joint all-three-macros: 0/65. Pooled response directions did not beat personal ones |
| Sep 4–8 carbohydrate push: two-sensor personal projection, nested feature combinations, backward failure analysis, daily totals, rolling validation, frozen-formula test on unseen doses | `analysis/carb_fresh_audit/*` | Dose ordering right in 23/26 later matched pairs. Grams: best 9–10/52 within ±10% (MAE 15–18 g). Daily totals 13/44 within ±10% (20% MAPE), equal to a personal mean. Frozen 42-term formula on unseen doses: 4/54, MAE 85 g |
| Fat timing audit and sweat-lipid research notes | `analysis/fat_timing_audit`, `analysis/sweat_research` | See FINDINGS and audit notes |
| Reproducibility audit of MealMeter (CGM + Empatica E4, 12 people) | `analysis/mealmeter_audit` | Notebook mixes participants across "personal" blocks, preprocesses before split, and uses random rather than chronological splits; dataset not public |
| Audit of first public sweat-lipid traces (PolyCORE 2026) | `analysis/polycore_audit`, `analysis/lipid_meals` | Real glucose / cholesterol / TG-proxy currents for 5 meal conditions, but no intake labels, no premeal baseline (meal eaten 30 min before sensor placement), TG channel is a lipolysis proxy. Gram inference not testable from released data |
| Auditable meal-recording protocol for a future collection | `experiment/` | `validate_meal.py` checks nutrient basis, mass, state, and calibration chronology; tests in `test_validate_meal.py` |

## What would change the answer

A direct fat channel (sweat or blood triglycerides) and a direct protein channel (amino
acids), measured alongside glucose, in a graded feeding study with blood truth.

## Layout

```
analysis/     experiments, each folder has FINDINGS.md or RESULTS.md and the code that produced it
dataset/      manifests, checksums, licenses, reserved-split record (raw data not committed; see each README)
experiment/   meal-recording protocol + validator
```

## Reproducing

Python 3.12+. Each `analysis/*` folder is self-contained; scripts resolve the repo root from their own
location and read from `dataset/` paths named in their FINDINGS file. Manifests record input hashes with
`<repo>/` in place of the machine path. Datasets: CGMacros and BIG IDEAs from PhysioNet (credentialed),
PolyCORE workbooks from the paper's supplement.
