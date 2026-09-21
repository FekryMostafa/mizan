# Regularization with inner chronological selection

Regularization reduced later-meal MAE from 34.88 g to 27.57 g, but within-tolerance predictions fell from 11/107 to 5/107. This did not improve the requested ±10% objective. No settings were changed after examining those 107 answers.

## Procedure

Used only the 211 earlier training meals to select settings. For each person, earliest 70% were inner fitting and latest 30% were inner selection (136 fitting meals, 75 selection meals altogether). All selection response starts are later than that person’s last inner-fitting response endpoint. Compared 70 configurations: glucose-only or glucose plus HR/activity, five kernel widths, seven regularization strengths. Maximize inner hits first, break ties by MAE; tie rules were recorded beforehand. Imputation and scaling use inner-fitting data only.

Selected glucose plus HR/activity (27 inputs), gamma 0.001, ridge 0.1. On the inner selection meals this yielded 28/75 hits, 16.92 g MAE. Refit those settings on all 211 earlier meals, froze the model, saved all later predictions, and only then joined the 107 answers for scoring. Missingness/coverage indicators remain excluded from predictors.

## Results

| Group | Meals | Within tolerance | MAE (g) |
|---|---:|---:|---:|
| regularized_training | 211 | 47 | 17.92 |
| regularized_later | 107 | 5 | 27.57 |
| previous_later | 107 | 11 | 34.88 |
| training_mean_later | 107 | 3 | 29.02 |

Positive carbohydrate tolerance is ±10%; zero-carbohydrate tolerance is ±1 g. There is one zero-carb meal in each overall training/later set. Both the current and preceding models fail the later zero-carb case.

## What failed

All later predictions lie between 50.20 and 67.27 g, while true quantities span 0–133 g. The smoother model suppresses large previous errors by pulling predictions toward a central amount; this also prevents recovering small and large meals.

- All 28 later 24 g meals miss tolerance. Predictions range 50.31–64.11 g.
- All 21 later 94 g meals miss tolerance. Predictions range 54.13–67.27 g.
- Only 1/16 later 73 g meals meets tolerance.

The chronological split also exposes the prescribed meal schedule. Inner selection includes 27 meals at 66 g, 14 at 40 g and 11 at 43 g; later evaluation includes 28 at 24 g, 21 at 94 g and 16 at 73 g. These frequency differences help explain why an inner hit-rate winner was misleading. This is an observed distribution mismatch, not proof that it is the only cause of poor prediction.

## Per-person results

| Person | Later meals | Within tolerance | MAE (g) |
|---|---:|---:|---:|
| 1 | 5 | 0 | 27.89 |
| 2 | 4 | 0 | 34.21 |
| 3 | 4 | 1 | 14.42 |
| 4 | 5 | 0 | 24.68 |
| 5 | 5 | 0 | 29.32 |
| 6 | 5 | 0 | 21.19 |
| 8 | 5 | 0 | 33.16 |
| 9 | 5 | 0 | 31.75 |
| 10 | 5 | 0 | 28.57 |
| 14 | 5 | 1 | 25.73 |
| 17 | 5 | 0 | 43.02 |
| 27 | 4 | 0 | 27.28 |
| 31 | 4 | 0 | 22.26 |
| 32 | 2 | 0 | 26.08 |
| 33 | 4 | 0 | 23.71 |
| 34 | 3 | 0 | 25.53 |
| 35 | 3 | 0 | 31.75 |
| 36 | 4 | 0 | 32.30 |
| 38 | 4 | 1 | 16.15 |
| 39 | 3 | 0 | 26.10 |
| 41 | 5 | 0 | 34.16 |
| 42 | 2 | 1 | 19.07 |
| 43 | 6 | 0 | 26.05 |
| 44 | 4 | 0 | 28.49 |
| 45 | 3 | 1 | 24.99 |
| 49 | 3 | 0 | 28.68 |

## Interpretation and next experiment

The simple training-mean baseline has 29.02 g MAE and 3/107 hits. The selected model is only slightly better than that baseline on these metrics. Neither the highly flexible model nor this smoother configuration achieves accurate personalized grams.

An improved model-selection experiment should use multiple chronological origins within the development data and report dose-specific performance, so a common recipe cannot dominate selection. The currently exposed 107 meals cannot be made fresh by changing the split. New independent or prospective personalized meal data is required for a clean final validation claim. No additional model was tuned against the 107 outcomes in this run.

Artifacts: PLAN.json specifies the candidate grid and selection rules; inner_split.csv fixes records; candidates.csv reports every selection result; selected_settings.json records the chosen settings. frozen_model.npz stores coefficients and preprocessing. predictions_before_scoring.csv and later_results.csv retain all later predictions. VERIFICATION.json records the model hash, saved-model prediction replay and unchanged source hashes. This is a development evaluation on a previously inspected dataset, not a pristine prospective trial.
