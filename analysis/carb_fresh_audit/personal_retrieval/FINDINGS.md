# Personal historical matching, selected on earlier windows

Later-meal result: 17/107 within tolerance, 24.89 g MAE. The preceding personal anchor-consistent regression achieved 7/107 and 24.09 g MAE. Retrieval improves the tolerance hit count but slightly worsens mean absolute error. The overall goal remains unmet.

## Procedure

Compared 18 configurations: shape-only, glucose-only, or glucose plus HR/activity; pooled-earlier or personal-earlier normalization; one, three, or five neighbors. Candidate selection used only the same three earlier rolling chronological windows, with equal-band hit-rate scoring and inverse-repeat weights. All histories include the person’s two initial known anchors.

Selected glucose-only, pooled-earlier normalization, three nearest examples. Prediction is their inverse-distance weighted mean carbohydrate amount, with a fixed 0.05 distance floor. Every neighbor is from the same person and occurs before the later evaluation meal. No ID, food identity or later target value is a distance input.

This differs from the earlier unselected 30/107 nearest-label diagnostic: that used one neighbor, 27 inputs and different fixed scaling. We did not pick a replacement setting by maximizing the later-meal outcome.

## Dose groups

| Band | Meals | Within tolerance | MAE (g) |
|---|---:|---:|---:|
| high | 43 | 9 | 24.66 |
| low | 40 | 1 | 30.34 |
| medium | 23 | 7 | 14.94 |
| zero | 1 | 0 | 45.86 |

Positive targets use ±10%; the one zero-carb meal uses ±1 g. The zero-carb case fails. Low-dose prediction remains especially poor, with only 1/40 low-carb meals inside tolerance.

## What history alone can and cannot supply

An answer-aware coverage audit found a historical label within tolerance for 91/107 later meals. Thus selecting exactly one earlier label has an upper bound of 91/107 on this set, even with perfect retrospective selection. This is a limit of the available label menu, not of CGM information in general.

Allowing arbitrary convex averages of all the person’s earlier labels can reach the tolerance interval for 100/107 meals. Seven targets fall outside that permitted range. These are hindsight representational ceilings, not achieved accuracy and not usable predictions. A method capable of inferring new quantities must go beyond copying or averaging known labels.

## Next diagnostic

Current distances summarize the response using peaks, areas, timing and a few shape comparisons. The next evidence-gathering step is to test whether the full glucose time sequence distinguishes the low-dose failures from their high-dose neighbors better than those summaries do, using earlier rolling selection again. Do not assume a better distance will overcome the historical-label range limit.

## Reproducibility and limits

PLAN.json fixes candidate definitions, scoring and prediction. candidates.csv and rolling_predictions.csv record model selection. neighbors.csv identifies every chosen earlier example and its recorded grams. predictions_before_scoring.csv was written before later labels were joined; later_results.csv and failures.csv retain every outcome. Source hashes remained unchanged.

This is ongoing development using an already-exposed later-meal set, not pristine prospective validation. The same 26 people supply calibration/training and later meals. Known meal timestamps and initial calibration are assumed. No goal completion is claimed.
