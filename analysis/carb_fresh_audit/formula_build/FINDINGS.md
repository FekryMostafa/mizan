# One shared formula, built incrementally

This run deliberately fits the same ten largest previously selected failures. It tests whether a flexible equation can fit those observations; it does not prove that grams can be recovered for unknown meals. The first step reaching the requested tolerance is step 7. Step 8 was also evaluated and is retained in the logs.

Inputs were re-extracted from the cleaned participant CSVs. All 104 calibration/query records used have full-consumption labels. Only past personal calibration labels and current/prior sensor observations enter predictors. Current meal carbohydrate answers enter fitting and scoring, never the predictor vector. No current protein/fat, recipes, photos, participant ID, or date enters the formula. Meal timestamps are assumed known.

Baseline: project the three-hour baseline-relative glucose response onto the difference between the earlier 24 g and 66 g reference responses; convert that projection continuously to grams. This is not the previous 12-feature model, so its individual starting estimates differ.

At each step, choose one of 46 observable features that most reduces squared error on the ten targets. Refit the intercept and all selected coefficients together. Features are standardized using those ten fitting cases. Means require 90% coverage; unavailable means use training medians, with separate coverage features. The formula has no per-person lookup or hand-set output correction, but eight fitted coefficients for ten observations and feature selection make overfitting easy.

## Progress

| Step | Added observable | Hits / 10 fitted | Mean absolute error, g | Hits / 42 other cases |
|---|---|---:|---:|---:|
| 0 | personal_full_curve_projection | 0 | 28.11 | 8 |
| 1 | personal_area_60_120 | 2 | 19.44 | 8 |
| 2 | late_hr_coverage | 1 | 17.59 | 8 |
| 3 | pre1_activity | 2 | 8.63 | 3 |
| 4 | pre24_hr_coverage | 3 | 7.01 | 4 |
| 5 | late_activity | 6 | 4.67 | 3 |
| 6 | pre24_hr | 9 | 1.39 | 2 |
| 7 | middle_hr | 10 | 0.26 | 4 |

HR coverage is the fraction of expected minutes with recorded HR. It measures recording availability, not heart physiology. `pre1_activity` is the preceding hour's Fitbit estimated kcal/min; `late_activity` is minutes 120–180. `middle_hr` is minutes 60–120. `pre24_hr` and its coverage refer to the preceding day. These are empirical terms, not conversions of activity calories into carbohydrate oxidation.

## Formula at step 7

C = max(0, C_base + 4.525892710724044
    -6.539854213883028 × z(personal_area_60_120)
    -65.855846516170857 × z(late_hr_coverage)
    +13.009450808130321 × z(pre1_activity)
    +37.616811588438388 × z(pre24_hr_coverage)
    +10.815526929156423 × z(late_activity)
    -10.474916572122787 × z(pre24_hr)
    +6.442696113339362 × z(middle_hr)
)

`z` subtracts the saved training mean and divides by its saved standard deviation. Exact scaling, imputation values, coefficients and every earlier version are in formula.json. The personal middle-hour-area feature is centered on the two calibration values and divided by their signed difference, with a floor derived from historical calibration contrasts. The script supplies this definition exactly. Coefficients are not causal physiological constants.

## Each of the ten

| Person | True g | Baseline g | Step 7 g |
|---|---:|---:|---:|
| 2 | 66 | 108.73 | 66.11 |
| 5 | 24 | 49.41 | 23.99 |
| 27 | 66 | 38.16 | 65.44 |
| 32 | 66 | 3.10 | 66.17 |
| 35 | 24 | 35.84 | 23.48 |
| 36 | 24 | 53.36 | 24.36 |
| 38 | 24 | 32.60 | 23.94 |
| 38 | 66 | 49.36 | 66.34 |
| 41 | 66 | 42.01 | 65.83 |
| 49 | 66 | 34.18 | 66.34 |

The largest improvement is not universally the last term. For example, premeal activity changes P36 from 47.46 to 23.73 g at step 3; later refitting temporarily breaks that correction. P5 reaches 24.26 g at step 6, while P35 is still at 28.30 g and needs the next step to meet tolerance. Every intermediate prediction is recorded in step_predictions.csv.

## What the checks say

- Step 7 fits all ten within 10%, with 0.26 g mean absolute error. These are training results.
- The other 42 previously inspected cases deteriorate from 8/42 hits and 14.98 g MAE to 4/42 hits and 29.61 g MAE. These are diagnostic controls, not a fresh independent test set; some participants appear in both groups.
- Repeating feature selection, imputation, scaling and fitting without each target participant yields 1/10 hits at step 7, with 68.36 g MAE. Personal earlier calibration meals remain allowed. This is a small, failure-selected diagnostic rather than a population accuracy estimate.
- Very large coverage coefficients show that missingness is helping fit this sample. This is not evidence that missing HR physically changes carbohydrate absorption.
- All targets contain either 24 or 66 g carbohydrate. No result here establishes precise inference of intermediate doses or arbitrary meals.

Conclusion: a shared formula can be made to fit these ten; this run demonstrates fitting capacity, not recoverability on unknown data. The next useful work is finding corrections that also survive predictions made without the target answers, rather than adding more terms to the now-solved fitting objective.

Verification: recomputed step 7 directly from saved formula/scaling and all 52 saved inputs; matched exported predictions within 1e-9 g. Source file hashes remained unchanged. No original analyses or clean data were overwritten.
