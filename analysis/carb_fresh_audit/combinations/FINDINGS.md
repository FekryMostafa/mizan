# Libre feature combinations

## Result

The requested ±10% carbohydrate accuracy is not achieved. Nested person-held-out selection produces 9/52 predictions within ±10%, 15.20 g mean absolute error, and 32.26% median absolute percentage error. No participant has both later meals within ±10%.

Compared on the exact same 52 meal keys, the preceding Libre full-curve personal projection had 8/52 hits and 17.51 g mean absolute error. The new procedure improves absolute error on 29/52 meals, gains five hits and loses four. This descriptive change does not establish statistical significance.

## Experiment

Evaluated 48 candidates: all seven nonempty combinations of peak, positive area 60–120 min, and positive-area time centroid; plus all 12 extracted features. Each representation has linear and quadratic versions, with ridge penalties 1, 10, or 100. Quadratic terms include pairwise feature interactions.

Features are centered on each person's two calibration responses and divided by their signed half-contrast. To limit division by near-zero contrasts, the denominator magnitude is floored at 25% of the training participants' median absolute calibration half-contrast, with a numerical lower bound. This is a modeling assumption, not a physiological constant.

For each outer held-out person, train on other people's later controlled meals. An inner leave-one-person-out loop chooses the candidate by most ±10% hits, with mean absolute error as tie-breaker. Inner normalization and standardization exclude that inner held-out person from population statistics. The outer person's two earlier calibration meals are permitted onboarding information; neither later dose label enters selection or fitting. Predictions are continuous and clipped only at zero, with no snapping to the known recipes.

## Feature and error findings

Inner selection chose the full 12-feature representation in all 26 outer folds: linear in 16, quadratic in 10. This suggests testing information beyond the original three features, but it does not isolate which additional feature helps independently.

| Actual carbs | Hits | Mean absolute error | Mean signed error |
|---|---:|---:|---:|
| 24 g | 3/26 | 13.48 g | +12.05 g |
| 66 g | 6/26 | 16.93 g | -14.85 g |

Predictions shrink toward the middle, improving some large misses while failing tight tolerances. The strongest fixed candidate by post-hoc outer hit count reaches only 10/52; that ranking is exploratory and is not the primary result. No tested candidate reaches the target.

## Limits and next question

These are previously inspected development data with two repeated controlled doses and fixed other macros. Nested selection prevents direct outer-person label tuning inside this run; it does not erase earlier researcher exposure or validate unseen portions, arbitrary meals, or automatic meal timing. The current candidate family is finite and these results are not proof that all models fail.

The unresolved feature question is whether premeal glucose state and recent history predict the change in personal response scale. A next test should add those measurable inputs under the same selection protocol, not correct each miss from its known carbohydrate label. Reserved participants remain untouched.

## Verification

Checked 52 unique query keys, exact agreement with the earlier comparator's query keys, all saved absolute errors and ±10% flags. Plan, candidate results, selection per person, final predictions, and input/script hashes are saved here. No prediction exclusions or abstentions.
