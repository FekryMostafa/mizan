# Expand the shared carbohydrate formula from 10 to 20 meals

Completed the deliberate fitting checkpoint: all 20 selected meals are within ±10%, with 0.75 g mean absolute error. This is training performance on previously inspected records. The original ten remain included.

## Fixed selection

Kept the ten previously selected largest failures. Added five successes and five failures from the original 52-query model. Within each added group, selected three 24 g and two 66 g records by ascending participant then timestamp, without ranking their new predictions. This produces ten 24 g and ten 66 g meals. Selection was saved before new predictions. The other 32 were diagnostic only and never entered fitting or term selection.

## One formula, one addition at a time

The formula remains max(0, the personal full-curve estimate + an intercept + a weighted sum of standardized observations). First apply the old formula unchanged, then refit its same seven terms on twenty examples, then add one observable at a time and refit jointly. The final formula has 14 terms plus an intercept. Each candidate addition minimizes squared training error. This objective can lower total error while temporarily reducing the count inside the 10% threshold.

| Stage | Terms | Within 10% / 20 | Mean absolute error (g) |
|---|---:|---:|---:|
| old_formula_unchanged | 7 | 11 | 10.75 |
| same_seven_terms_refit_on_20 | 7 | 6 | 9.25 |
| add_early_activity | 8 | 8 | 6.38 |
| add_middle_hr_coverage | 9 | 9 | 4.64 |
| add_pre6_hr_coverage | 10 | 13 | 3.59 |
| add_shape_minimum | 11 | 15 | 2.91 |
| add_middle_activity | 12 | 19 | 1.88 |
| add_personal_rise_0_30 | 13 | 19 | 1.22 |
| add_shape_start | 14 | 20 | 0.75 |

Activity means are Fitbit kcal/min estimates, not measured carbohydrate oxidation. Coverage terms describe recording availability. Shape terms compare the whole curve with earlier personal low/high carbohydrate references after removing its amplitude: shape_minimum subtracts the curve minimum; shape_start subtracts its initial value. They are continuous observables, not discrete dose outputs.

## What happened near the target

- After adding the first curve-shape term, five meals still missed: P1/P2/P3/P35 low carbohydrate and P27 high carbohydrate.
- Adding middle-hour activity brought those within tolerance, but P45 low carbohydrate became the sole miss at 30.42 g instead of 24 g.
- Adding early glucose rise corrected P45, while P27 low carbohydrate became the sole miss at 21.39 g instead of 24 g.
- Adding the second curve-shape comparison left both corrected: P45 24.98 g and P27 low 23.80 g.

This shows the interaction of jointly refitted terms. It does not establish that any particular term is a causal physiological correction. Several terms still describe missing HR, so recording patterns remain part of this fitting experiment.

## Final per-meal predictions

| Person | Recorded carbs (g) | Predicted carbs (g) | Selection |
|---|---:|---:|---|
| 1 | 24 | 23.40 | added_old_failure |
| 1 | 66 | 64.79 | added_old_failure |
| 2 | 24 | 22.80 | added_old_failure |
| 2 | 66 | 64.62 | original_ten_failures |
| 3 | 24 | 23.78 | added_old_failure |
| 3 | 66 | 65.83 | added_old_failure |
| 4 | 66 | 68.32 | added_old_success |
| 5 | 24 | 24.35 | original_ten_failures |
| 5 | 66 | 64.95 | added_old_success |
| 27 | 24 | 23.80 | added_old_success |
| 27 | 66 | 67.18 | original_ten_failures |
| 32 | 66 | 65.81 | original_ten_failures |
| 34 | 24 | 23.84 | added_old_success |
| 35 | 24 | 25.61 | original_ten_failures |
| 36 | 24 | 24.89 | original_ten_failures |
| 38 | 24 | 24.00 | original_ten_failures |
| 38 | 66 | 65.67 | original_ten_failures |
| 41 | 66 | 66.19 | original_ten_failures |
| 45 | 24 | 24.98 | added_old_success |
| 49 | 66 | 65.20 | original_ten_failures |

## Diagnostic context and verification

The other 32 meals have 4/32 predictions within 10% and 28.94 g MAE with the final formula, versus 3/32 and 32.23 g with the old formula. They are not a fresh independent test set and some people occur in both groups. Their results were not used to pick terms or stop this fitting run.

No recipes, participant identifiers, current meal macros, or dates enter the predictor. The twenty recorded carbohydrate answers are used to select terms and fit coefficients, deliberately. Earlier personal calibration meals remain known. All twenty query meals are from the same two carbohydrate doses; this does not test arbitrary intermediate doses.

Exact coefficients, imputation and standardization are saved in formula.json. Selected records are in selected_20.csv; every intermediate estimate is in predictions_each_step.csv. run.py reproduces selection and fitting from the preceding verified extraction. Final predictions were independently reconstructed from saved scaling and coefficients within 1e-9 g. Clean-source hashes remained unchanged; the earlier ten-meal experiment was preserved.
