# Does a larger independent training cohort help?

Completed a fixed-model transfer experiment: 652 eligible Dexcom meals from 34 CGMacros participants supplied population training. Predictions were evaluated on the same 65 later meals from five BIG IDEAs development participants used previously, with four earlier labeled meals per person for calibration. The eight reserved participants remain unopened by the analysis.

The two datasets use the same feature definition: 13 baseline-subtracted glucose readings from 0 to 180 minutes, baseline from -10 and -5 minutes, and the premeal slope between those two readings. The standardizer is fitted only on CGMacros. Source meals pass the existing completeness, isolation, full-consumption and label-consistency filters. CGMacros readings come from its released interpolated grid; BIG IDEAs readings use bounded interpolation from its original Dexcom timestamps. This remaining measurement-processing difference is a limitation.

Three fixed population algorithms were tested: ridge regression, randomized regression trees and median-loss boosted trees. Each was evaluated alone, with personal offset correction, and with personal kernel correction. The designated primary method was trees plus kernel correction. This is exploratory development with no performance-based selection of the reported primary model, not a fresh validation claim.

## Result

| Primary continuous model | Joint success within 10% | Carbohydrate MAE | Protein MAE | Fat MAE |
|---|---:|---:|---:|---:|
| Earlier small-cohort ridge + personal kernel | 0/65 | 39.6 g | 13.7 g | 13.0 g |
| CGMacros-trained trees + personal kernel | 1/65 | 37.1 g | 13.5 g | 12.5 g |

Both training dataset and population model changed in this comparison. It is therefore not an isolated causal test of training size. The closer comparison using ridge plus personal kernel in both settings changed errors to 39.2 g carbohydrate, 14.3 g protein and 13.0 g fat, with 0/65 joint successes. More external training did not produce a large improvement under these tested methods.

## Inspecting the apparent success

Participant 006's March 1 pizza meal has recorded macros **70 g carbohydrate, 26 g protein and 26 g fat**. The primary model predicted **71.74, 26.57 and 24.41 g**, respectively, all within 10%.

However, the same logged food description, "4 small pizza slices everything", and identical macro values appeared in **two of this person's four onboarding meals**. Thus this is a repeat of an already calibrated meal, not evidence of recovering a new dose. Actual food wording was inspected only after evaluation and was never a model input.

A diagnostic no-sensor control that always returns the most frequent earlier calibration macro vector (ties resolved by earliest occurrence) also gets this pizza right. Across all 65 queries that control gets 3 within tolerance, compared with the primary model's one. The control was added after inspecting the apparent success, so it is a post-hoc diagnostic rather than a prespecified comparison. It demonstrates that this individual success does not require glucose information.

## Verification

The run completed after fixing a NumPy string to pandas timestamp conversion error. Predictions from the failed attempt were not used. Verified exact agreement of the 65 query events with the prior experiment, chronology of all four calibration meals before queries, development-only target IDs, and all tolerance flags recomputed from numeric predictions. Population fitting uses CGMacros only; the separate source/target dataset identities are recorded in the manifest.

The target remains unachieved. The present models mostly produce broad estimates; repeated-menu successes and small average-error reductions do not validate ±10% macro measurement. Reserved participants should remain reserved while development performance is this weak.

- [All predictions](predictions.csv)
- [All nine fixed comparisons](summary.json)
- [Source and calibration manifest](split_manifest.json)
- [No-sensor modal calibration control](no_sensor_mode.csv)
- [Run provenance](run_manifest.json)
