# Frozen formula: later meals from calibrated participants

Outcome: 4 of 54 later meals were predicted within ±10% carbohydrate error. Mean absolute error was 84.83 g; median absolute error was 58.23 g. The formula was not refitted or modified. This is a negative result for the current fitted equation, not proof that all CGM-based approaches are impossible.

## What was tested

Examined all 99 logged meals occurring strictly after the end of each participant’s last response used in the 52-meal fit. Selected 54 meals from 25 of its 26 participants using prespecified record-quality requirements. Carbohydrate answers were not used to select coefficients, features, or predictions. All predictions were written to predictions_before_scoring.csv before target answers were joined for scoring. Eligibility necessarily uses label completeness and reported consumption.

Exclusion flags among the 45 ineligible records: 28 had another food event in the response interval, 15 had unresolved labels, 5 incomplete response data and 1 glucose at a device bound. Flags overlap. Every inspected record and its disposition is in eligibility.csv. There were no eligible zero-carbohydrate meals.

Eligible records require full-consumption labels, an isolated complete three-hour Libre response without device-bound readings, and ten minutes of complete uncensored baseline readings. HR missingness is retained and handled by the frozen model. The original two personal calibration responses are reused without updating them from test answers.

## Results by group

| Group | Meals | Within 10% | MAE (g) |
|---|---:|---:|---:|
| all_positive_carb | 54 | 4 | 84.83 |
| breakfast | 16 | 2 | 76.82 |
| other_meals | 38 | 2 | 88.21 |
| doses_other_than_24_66 | 52 | 4 | 86.61 |

The 16 breakfasts all record 73 g carbohydrate, 22 g protein, 42 g fat and 7 g fiber. The fitted breakfasts had 24/66 g carbohydrate, 22 g protein, 10.5 g fat and zero fiber. Consequently this test changes both carbohydrate dose and meal composition, as well as day-to-day conditions. The other 38 meals are lunches, dinners or snacks. Overall doses range from 4 to 133 g.

## Where the fitted equation breaks

- P39: a 73 g breakfast is predicted as 486.42 g. Its late-HR-coverage term alone contributes +358.85 g. None of its individual primitive inputs lies outside the marginal training ranges, so merely clipping those ranges would not resolve this example. Their combination is poorly handled.
- P3: a 52 g dinner is predicted as 434.23 g. The interaction between personal peak timing and baseline difference contributes +315.78 g. Its personal timing feature is outside the training range.
- P8: a 94 g lunch is predicted as 432.17 g. The same timing/baseline interaction contributes +307.49 g.
- Fourteen predictions clip to zero. These are model outputs, not evidence of zero food intake.

These are exact additive contributions from the frozen equation, not physiological causes. term_contributions.csv records every term for every meal. Large coefficients fitted to the narrow training set amplify different recording patterns and meal responses.

## Sanity comparisons

The original personal full-curve projection without the 42 fitted corrections gets 8/54 within 10%, with 35.36 g MAE. An input-independent 66 g prediction gets 18/54, with 25.26 g MAE. These are diagnostic baselines, not alternatives selected to replace the frozen formula. They show that the added fitting complexity hurts this later-meal test.

## Verification and limitations

- Recomputed all 46 original input features for each of the 52 fitting examples from the clean participant files. They matched the saved features, including missingness. Replayed all 52 frozen predictions and matched within 1e-8 g.
- Verified the formula bytes and original clean-source hashes remained unchanged. Prediction-file hash before scoring: 4d56178c5bf82d5fa16f0725f5b54d4aaee03ebe9289b402908eb6e6028634d2.
- No fit calls, coefficient updates, or test-answer-dependent feature selection are performed by evaluate.py.
- These later meals were excluded from this particular formula fitting run. The dataset and portions of it have been inspected during earlier research; this is not a pristine never-seen prospective validation cohort.
- Meal timestamps are supplied, and prior meal-label review status is an input inherited from the existing formula. This test does not demonstrate passive meal detection or an entirely logging-free deployment.
- Source quality flags cannot establish exact consumed quantities or photo-verified timing. The test uses the existing documented clean-data policy.

## All predictions

| Person | Timestamp | Meal | Recorded carbs (g) | Predicted carbs (g) | Within 10% |
|---|---|---|---:|---:|---|
| 1 | 2020-05-10 19:59:00 | dinner | 26 | 0.00 | no |
| 1 | 2020-05-11 10:58:00 | breakfast | 73 | 75.12 | yes |
| 2 | 2019-11-24 11:48:00 | lunch | 94 | 93.70 | yes |
| 2 | 2019-11-24 18:18:00 | dinner | 7 | 184.32 | no |
| 2 | 2019-11-25 20:23:00 | breakfast | 73 | 230.00 | no |
| 3 | 2020-03-20 19:46:00 | dinner | 52 | 434.23 | no |
| 3 | 2020-03-21 07:56:00 | breakfast | 73 | 44.03 | no |
| 4 | 2023-09-20 13:18:00 | lunch | 94 | 18.63 | no |
| 4 | 2023-09-20 20:30:00 | dinner | 25 | 0.00 | no |
| 5 | 2020-08-26 14:48:00 | lunch | 94 | 0.00 | no |
| 5 | 2020-08-26 19:44:00 | dinner | 24 | 0.00 | no |
| 5 | 2020-08-27 09:06:00 | breakfast | 73 | 245.56 | no |
| 6 | 2023-04-16 13:48:00 | lunch | 94 | 122.84 | no |
| 6 | 2023-04-16 20:26:00 | snack | 60 | 206.62 | no |
| 6 | 2023-04-17 07:00:00 | breakfast | 73 | 73.87 | yes |
| 8 | 2023-02-08 12:14:00 | lunch | 94 | 432.17 | no |
| 8 | 2023-02-08 18:12:00 | dinner | 117 | 160.84 | no |
| 8 | 2023-02-09 08:12:00 | breakfast | 73 | 32.42 | no |
| 9 | 2020-09-24 12:29:00 | lunch | 94 | 0.00 | no |
| 9 | 2020-09-24 19:29:00 | dinner | 133 | 24.52 | no |
| 10 | 2020-06-30 13:19:00 | lunch | 94 | 145.31 | no |
| 10 | 2020-06-30 17:40:00 | snack | 24 | 77.42 | no |
| 10 | 2020-07-01 05:40:00 | breakfast | 73 | 48.76 | no |
| 14 | 2023-05-18 12:25:00 | lunch | 94 | 120.60 | no |
| 14 | 2023-05-19 08:17:00 | breakfast | 73 | 5.68 | no |
| 17 | 2023-10-19 13:05:00 | snack | 15 | 49.43 | no |
| 17 | 2023-10-19 21:00:00 | dinner | 131 | 52.23 | no |
| 17 | 2023-10-20 16:40:00 | breakfast | 73 | 108.12 | no |
| 27 | 2024-06-19 13:40:00 | lunch | 94 | 378.62 | no |
| 31 | 2022-07-08 11:54:00 | lunch | 94 | 129.68 | no |
| 31 | 2022-07-08 20:06:00 | dinner | 65 | 13.78 | no |
| 32 | 2022-01-10 13:31:00 | lunch | 94 | 165.92 | no |
| 33 | 2022-04-25 11:55:00 | lunch | 94 | 0.00 | no |
| 33 | 2022-04-26 08:00:00 | breakfast | 73 | 103.77 | no |
| 34 | 2022-03-11 12:10:00 | lunch | 94 | 195.81 | no |
| 35 | 2024-12-21 12:58:00 | lunch | 94 | 0.00 | no |
| 36 | 2022-04-07 12:36:00 | lunch | 94 | 0.00 | no |
| 36 | 2022-04-07 17:32:00 | dinner | 4 | 0.00 | no |
| 36 | 2022-04-08 08:00:00 | breakfast | 73 | 0.00 | no |
| 38 | 2022-02-03 16:39:00 | dinner | 55 | 0.00 | no |
| 38 | 2022-02-04 06:02:00 | breakfast | 73 | 11.53 | no |
| 39 | 2025-02-16 12:05:00 | lunch | 94 | 0.00 | no |
| 39 | 2025-02-17 09:17:00 | breakfast | 73 | 486.42 | no |
| 41 | 2022-05-05 11:15:00 | lunch | 94 | 13.01 | no |
| 41 | 2022-05-05 17:01:00 | snack | 98 | 65.70 | no |
| 43 | 2025-10-23 12:52:00 | lunch | 94 | 129.21 | no |
| 43 | 2025-10-23 17:47:00 | dinner | 34 | 183.10 | no |
| 43 | 2025-10-23 22:34:00 | dinner | 18 | 152.21 | no |
| 43 | 2025-10-24 08:12:00 | breakfast | 73 | 34.03 | no |
| 44 | 2022-10-26 12:24:00 | lunch | 94 | 59.49 | no |
| 45 | 2025-04-03 12:16:00 | lunch | 94 | 96.62 | yes |
| 45 | 2025-04-04 10:24:00 | breakfast | 73 | 0.00 | no |
| 49 | 2025-05-20 12:53:00 | lunch | 94 | 0.00 | no |
| 49 | 2025-05-21 08:02:00 | breakfast | 73 | 82.71 | no |

The next development question is how to constrain or replace the unstable coverage and interaction corrections while training across broader meal compositions. These 54 meals are now exposed; future changes should not be advertised as independently validated by retesting only these same answers.
