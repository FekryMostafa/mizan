# Deliberate fitting expanded to all 52 meals

All 52 recorded meals fit within ±10% carbohydrate error. Mean absolute error: 0.713 g. Largest relative error: 9.74%. This is a training-fit checkpoint on previously inspected examples, not validation performance.

## Expansion and capacity

- Kept the original twenty and included every remaining query in the same 26-person experiment. No query was removed because of its previous prediction error.
- Applied the previous 14-term formula unchanged first: 24/52 hits, 18.10 g MAE.
- Refit those 14 terms on all 52: 11/52 hits, 12.59 g MAE. Minimizing squared error can reduce the number inside a per-meal tolerance even while improving overall fit.
- Added independent linear terms one at a time. At 35 terms, the formula reached 20/52 hits and 7.78 g MAE. Other available linear terms were constant or dependent on the existing design at the chosen rank tolerance.
- Then allowed products of two standardized continuous observations. Added seven products, one at a time, reaching 52/52 with 42 terms plus an intercept. The final fitting design has rank 43 for 52 observations.

## Interaction additions

| Added product | Within 10% | MAE (g) |
|---|---:|---:|
| personal_area_60_120 * shape_start | 28/52 | 5.379 |
| baseline_difference * pre24_glucose | 29/52 | 4.556 |
| personal_peak_time * baseline_difference | 40/52 | 3.000 |
| shape_minimum * pre1_hr | 41/52 | 2.099 |
| personal_peak_time * shape_minimum | 47/52 | 1.474 |
| shape_minimum * late_activity | 49/52 | 0.953 |
| pre1_activity * late_hr | 52/52 | 0.713 |

These products increase fitting flexibility. They are not established physiological mechanisms. In particular, multiplying two observations in a fitted equation does not show that one causes the other. The final formula retains recording-coverage and prior-food-review indicators from earlier stages.

## Scope and data

All targets remain the same 24 g and 66 g controlled breakfast repeats, 26 at each dose. This expansion increases examples, not the range of meal types or carbohydrate quantities. Earlier personal calibration records remain known; meal timestamps are assumed supplied. No current food identity, protein, fat, participant ID, date or target carbohydrate value enters the predictor vector. The 52 target answers are deliberately used to select and fit terms.

No holdout remains among these 52. Other datasets were not opened or used in this expansion. This run neither names those datasets as validated holdouts nor claims their cohort independence has been audited. P32’s low-dose device-bound record remains included and flagged in the clean source; numerical fitting does not repair that measurement.

## Final predictions

| Person | Recorded carbs (g) | Predicted carbs (g) | Error (%) |
|---|---:|---:|---:|
| 1 | 24 | 23.977 | 0.10 |
| 1 | 66 | 66.220 | 0.33 |
| 2 | 24 | 21.663 | 9.74 |
| 2 | 66 | 66.395 | 0.60 |
| 3 | 24 | 22.783 | 5.07 |
| 3 | 66 | 64.960 | 1.58 |
| 4 | 24 | 23.835 | 0.69 |
| 4 | 66 | 66.480 | 0.73 |
| 5 | 24 | 23.828 | 0.71 |
| 5 | 66 | 65.714 | 0.43 |
| 6 | 24 | 23.371 | 2.62 |
| 6 | 66 | 66.854 | 1.29 |
| 8 | 24 | 22.006 | 8.31 |
| 8 | 66 | 67.052 | 1.59 |
| 9 | 24 | 25.351 | 5.63 |
| 9 | 66 | 65.573 | 0.65 |
| 10 | 24 | 25.851 | 7.71 |
| 10 | 66 | 65.854 | 0.22 |
| 14 | 24 | 25.746 | 7.27 |
| 14 | 66 | 65.830 | 0.26 |
| 17 | 24 | 25.417 | 5.90 |
| 17 | 66 | 66.204 | 0.31 |
| 27 | 24 | 23.344 | 2.74 |
| 27 | 66 | 66.897 | 1.36 |
| 31 | 24 | 25.580 | 6.58 |
| 31 | 66 | 64.239 | 2.67 |
| 32 | 24 | 24.247 | 1.03 |
| 32 | 66 | 66.066 | 0.10 |
| 33 | 24 | 24.000 | 0.00 |
| 33 | 66 | 67.493 | 2.26 |
| 34 | 24 | 23.775 | 0.94 |
| 34 | 66 | 66.522 | 0.79 |
| 35 | 24 | 24.231 | 0.96 |
| 35 | 66 | 66.074 | 0.11 |
| 36 | 24 | 23.880 | 0.50 |
| 36 | 66 | 65.118 | 1.34 |
| 38 | 24 | 22.878 | 4.67 |
| 38 | 66 | 65.736 | 0.40 |
| 39 | 24 | 25.149 | 4.79 |
| 39 | 66 | 66.289 | 0.44 |
| 41 | 24 | 24.327 | 1.36 |
| 41 | 66 | 64.373 | 2.47 |
| 42 | 24 | 24.028 | 0.12 |
| 42 | 66 | 65.394 | 0.92 |
| 43 | 24 | 23.459 | 2.25 |
| 43 | 66 | 65.551 | 0.68 |
| 44 | 24 | 24.959 | 4.00 |
| 44 | 66 | 66.172 | 0.26 |
| 45 | 24 | 23.018 | 4.09 |
| 45 | 66 | 66.256 | 0.39 |
| 49 | 24 | 23.305 | 2.90 |
| 49 | 66 | 66.679 | 1.03 |

## Reproduction

run.py starts from the preserved measured inputs and twenty-meal formula. formula.json records all versions, coefficients, primitive-feature scaling, and product definitions. predictions_each_step.csv contains every intermediate prediction; final_predictions.csv contains all 52 final estimates. Product terms multiply standardized observations after the saved missing-value handling. Old-formula evaluation uses its original twenty-case scaling.

Verification: each original clean-source hash was checked before and after the run. Final predictions were reconstructed separately from the saved formula definitions and coefficients and matched within 1e-8 g. All 52 outputs were checked individually against their ±10% targets. Earlier experiment artifacts were preserved.
