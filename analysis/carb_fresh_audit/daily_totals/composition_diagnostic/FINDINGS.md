# Does supplying known fat/protein/fiber explain the daily errors?

Not with the tested daily-summary models. On the same 44 later days:

| Inputs | Within ±10% | MAPE | MAE |
|---|---:|---:|---:|
| Sensors and personal calibration | 15/44 | 18.94% | 37.60 g |
| Known daily fat/protein/fiber and personal calibration | 14/44 | 20.56% | 39.64 g |
| Sensors plus those known daily macros | 13/44 | 19.05% | 37.85 g |

The known-macro arms are explanatory diagnostics, not passive wearable results. They do not count toward the goal. Food-only is included because macro co-occurrence could otherwise look like physiological correction. No current carbohydrate or calorie values were predictors. Prepared daily carb sums were reconciled with the existing targets before removing the check column.

Same 64 calibration days, 29 earlier purged chronological validation days and all 44 later days. Each arm independently selected ridge/kernel settings by earlier MAPE then MAE. Query carb labels replaced with a constant did not change any predictions. The sensor-only reference reproduces the previous result.

## Raw comparisons

P9's 182 g versus 132 g days contain respectively 73.5 versus 55.5 g fat, 123 versus 194 g protein, and 11 versus 14 g fiber. P26's 167 versus 122 g days contain 69.5 versus 50.5 g fat, 119 versus 102 g protein, and 7 versus 4 g fiber. Composition does vary between the compared days. These observations alone do not identify how much of the glucose difference each nutrient caused.

This result rejects neither physiological effects of fat/protein nor a better time-dependent model. Giving daily totals to a small regularized model is a limited test; those totals omit their ordering relative to individual glucose events. It only shows that adding these known totals did not automatically resolve current prediction errors.

## Evaluation-design issue to examine next

Current early validation folds restrict every participant to their first two or three calibration days simultaneously. After sensor-window purging the shared model sees only 17 or 27 training days, versus 64 in the final fit. This can favor excessive shrinkage when choosing shared-model complexity. A more representative internal check can validate one participant's earlier day while retaining all eligible earlier calibration data from other people, and only preceding nonoverlapping days for that participant. All 44 later outcomes must remain outside selection. This is an evaluation-design hypothesis, not a reason to select settings using the later answers.

The passive target remains unmet: no verified daily ±10% model has emerged.
