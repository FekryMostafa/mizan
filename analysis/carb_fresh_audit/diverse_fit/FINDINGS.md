# Same-person personalization: broader fitting and later meals

Trained on 211 earlier meals and evaluated 107 later meals from the same 26 people. Each person contributes to both sets. All 211 training meals meet tolerance; 11 of 107 later meals do. Average absolute error is 0.036 g on training and 34.876 g on later meals.

## Split and personalization

For each of the original 26 people, selected an initial eligible 24 g and 66 g calibration breakfast with 22 g protein, 10.5 g fat and zero fiber. Included quality-eligible mixed meals only after both calibration response windows had finished. Ordered each person’s meals chronologically, used the earlier 70% for training and reserved the final 30% (at least two meals). Every later meal starts after the final training response window ends for that person. This is neither a random meal split nor a new-person evaluation.

The personalized inputs compare each meal’s response with that same person’s two initial references. The learned model is shared across people and learns from their earlier mixed meals; it does not fit a separate independent model per participant or use participant ID. This implements the requested same-person test, but does not exhaust possible individualized adaptation methods.

## Model and fitting

Used Gaussian kernel ridge regression on 27 continuous glucose, HR and activity observations, with training-only standardization and median imputation. No coverage flags or prior-food-review indicators are included as predictors. Missing values still require imputation; removing explicit indicators does not guarantee that the model cannot infer missingness indirectly. No current macro labels, meal identity, date, or participant ID are predictors.

Gamma candidates and ridge were specified before fitting. The first gamma (0.01, ridge 1e-8) already met the training tolerance, so no additional candidate was tried. The saved model contains one kernel coefficient per training example: a flexible interpolation model, not a physiological equation. Its successful training fit is a capacity/debugging checkpoint.

Positive-carb tolerance is ±10%; zero-carb tolerance is separately defined as ±1 g because relative percentage error is undefined at zero. Training includes one zero-carb meal, and evaluation includes one.

## Results

| Set | Meals | Within tolerance | Mean absolute error (g) |
|---|---:|---:|---:|
| Earlier training | 211 | 211 | 0.036 |
| Later, same people | 107 | 11 | 34.876 |
| Later, always predict training mean | 107 | 3 | 29.022 |

The learned model gets more meals inside tolerance than the simple mean predictor, but its mean absolute error is worse. Neither metric establishes usable personalized prediction yet. The validation predictions were saved before joining their target quantities, and no model parameters were changed afterward.

## Scope and verification

All source hashes remained unchanged. Reloading the saved model reproduced training predictions within 1e-6 g. The split and candidate schedule are recorded in PLAN.json and selected_records.csv; frozen_model.npz stores the fitted model and preprocessing. The feature extractor is the previously checked source, pinned by hash. All calibration normalization floors are derived from the training participants’ early anchors.

These later labels were not used by this fitting run. The public dataset and earlier experiments have already exposed some of these records, so this is a development holdout, not an independently pristine prospective trial. Supplied meal timestamps and known early calibration meals are assumed. No fat/protein inference is evaluated.

Next stage: regularization and model simplification under a separate inner chronological validation split within the earlier meals. Keep the final later-meal set fixed and avoid repeatedly tuning against its answers.

## Per-person later-meal results

| Person | Later meals | Within tolerance | MAE (g) |
|---|---:|---:|---:|
| 1 | 5 | 0 | 42.63 |
| 2 | 4 | 0 | 48.07 |
| 3 | 4 | 0 | 44.00 |
| 4 | 5 | 1 | 18.16 |
| 5 | 5 | 0 | 49.44 |
| 6 | 5 | 1 | 25.95 |
| 8 | 5 | 1 | 32.77 |
| 9 | 5 | 1 | 29.48 |
| 10 | 5 | 0 | 23.51 |
| 14 | 5 | 1 | 15.54 |
| 17 | 5 | 1 | 40.45 |
| 27 | 4 | 1 | 91.74 |
| 31 | 4 | 1 | 20.48 |
| 32 | 2 | 0 | 68.47 |
| 33 | 4 | 0 | 26.70 |
| 34 | 3 | 0 | 21.49 |
| 35 | 3 | 0 | 55.17 |
| 36 | 4 | 1 | 26.33 |
| 38 | 4 | 0 | 28.30 |
| 39 | 3 | 2 | 24.49 |
| 41 | 5 | 0 | 45.47 |
| 42 | 2 | 0 | 17.90 |
| 43 | 6 | 0 | 30.05 |
| 44 | 4 | 0 | 23.13 |
| 45 | 3 | 0 | 44.91 |
| 49 | 3 | 0 | 29.49 |
