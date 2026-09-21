# Explicitly personal, anchor-consistent regression

Progress: the model now reproduces all 52 known initial calibration meals exactly. This removes the previous model’s inability to reproduce its known 24 g anchors. It does not meet the overall goal: 7 of 107 later meals meet tolerance, with 24.09 g MAE. No low-carb later meal meets tolerance.

## What changed

Fit an independent kernel regression for each person, using only that person’s earlier meals and two known initial references. The two reference observations have zero regularization in the kernel system; other earlier observations have a ridge penalty. This imposes equality at the reference inputs while permitting regularization elsewhere. The actual 24/66 g values are checked after every fit.

Compared 48 settings using the same three rolling chronological windows entirely within the earlier development data: shape-only, glucose-only, or glucose/HR/activity; four gamma values; four ridge values. Fit median imputation and scaling separately from each person’s available earlier observations and anchors. Selected using equal-band within-tolerance rate, then equal-band MAE. Later answers did not select settings.

Selected glucose-only, gamma 0.1 and ridge 0.1. No recording-coverage flags, participant ID predictor, current food labels, or current target macros enter the equation. Models are selected by participant to represent personal calibration, not to infer carbs from identity alone.

## Later-meal results

| Band | Meals | Within tolerance | MAE (g) |
|---|---:|---:|---:|
| high | 43 | 4 | 28.33 |
| low | 40 | 0 | 25.26 |
| medium | 23 | 3 | 13.42 |
| zero | 1 | 0 | 40.99 |

Positive-carbohydrate tolerance remains ±10%; zero carbs is evaluated separately at ±1 g. Compared with the shared rolling-selected model, hits improve from 4 to 7 and MAE from 26.88 to 24.09 g. This modest improvement does not establish generalization at the requested accuracy.

## Failure interpretation

Because anchor outputs are now correct by construction, inaccurate later predictions cannot be blamed solely on failing to preserve the two known reference outputs. Different meal responses occupy different parts of the feature representation; exact interpolation of two anchors does not determine a reliable dose mapping for those new responses. Nor does this prove that other representations or additional calibration data cannot work.

The earlier same-person nearest-reference diagnostic had more within-tolerance matches (30/107) than this regression. That is a useful direction to inspect, not an independent validation victory: the same outcome set has already been exposed. ranked_failures.csv records the largest current errors.

## Verification and goal status

Checked all anchor outputs throughout selection and final fitting within 1e-5 g. Reloaded the saved per-person models and independently recomputed every later prediction within 1e-8 g. Original cleaned source hashes remained unchanged. Chronological training response endpoints precede each person’s later evaluation meals. Frozen predictions were saved before joining target answers.

This is continued development on a previously inspected public dataset and reused later set, not a pristine prospective test. The active objective of accurate later-meal carbohydrate grams within 10% remains unmet. No goal completion is claimed.

Files: PLAN.json, candidates.csv, selected_settings.json, frozen_model.json, selected_rolling_predictions.csv, predictions_before_scoring.csv, later_results.csv and VERIFICATION.json preserve the procedure and evidence.
