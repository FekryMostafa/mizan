# Rolling chronological validation, balanced by carbohydrate amount

The change did not improve the ±10% objective: 4/107 later meals meet tolerance versus 5/107 with the previous single-window selection. Mean absolute error improved slightly from 27.57 to 26.88 g. There are no successful low- or high-carb later predictions.

## Fixed method

Used the same 211 earlier meals for all fitting and selection. At 40%, 60% and 80% of each person’s sequence, fit the earlier prefix and predict the next 20%; require at least two training meals and one validation meal. This yields 181 rolling predictions over 135 distinct validation records. Inverse-multiplicity weights prevent overlapping windows from giving one meal extra total weight. All per-person chronological response-window boundaries were checked.

Compared the same 70 candidate settings as before: two input families, five gamma values and seven regularization strengths. Preprocessing uses only each fold’s fitting prefix. Selection maximizes the equal-weight mean of hit rates for zero, low (0–30 g), medium (30–70 g), and high (>70 g) carbs, breaking ties by equal-band MAE, fewer inputs, stronger regularization and smaller gamma. Positive-carb tolerance is ±10%; zero-carb tolerance is ±1 g.

Selected all 27 continuous glucose/HR/activity inputs, gamma 1.0 and ridge 10.0. Refitted on the entire 211-meal training set, saved a frozen model, wrote predictions for the same 107 later meals, then joined their labels. No later-answer-dependent selection or refitting was performed.

## Rolling selection results

Unique validation meals by band: high 16, low 22, medium 96, zero 1. Although scoring balances the bands, it cannot create more diverse validation observations. The selected configuration’s weighted hit rates were high 45.8%, medium 51.0%, low 0%, zero 0%. Its balanced score was 24.2%. These are model-selection results, not final validation accuracy.

## Later-meal results

| Carbohydrate band | Meals | Within tolerance | MAE (g) |
|---|---:|---:|---:|
| high | 43 | 0 | 29.46 |
| low | 40 | 0 | 32.98 |
| medium | 23 | 4 | 10.51 |
| zero | 1 | 0 | 48.17 |

Predictions lie between 45.68 and 65.24 g. Recorded values range from 0 to 133 g. The model continues to concentrate predictions near the middle instead of distinguishing small and large doses.

The training-mean baseline yields 3/107 hits and 29.02 g MAE. This selected model improves only slightly over that input-independent comparator. Changing validation windows has not fixed the underlying weak dose discrimination. It does not establish biological impossibility or prove that all feature representations will fail.

## Evidence and limits

PLAN.json records the origins, band definitions, candidate grid and tie rules. fold_assignments.csv identifies all fit/validation memberships. candidates.csv and candidate_band_scores.csv contain all selection results. selected_rolling_predictions.csv records the chosen candidate’s rolling outputs; later_results.csv contains every later-meal prediction. The saved model replay matched within 1e-8 g, and source hashes remained unchanged.

The 107 later-meal outcomes have been exposed in earlier development iterations. This is a reused development holdout; no independent prospective validation claim is warranted. Participants appear in both earlier and later sets, with their known initial calibration meals available.

Next work should inspect whether the chosen input representation and shared mapping preserve distinctions between low- and high-carb meals within each person, rather than assuming another regularization search will solve the collapse toward central doses.
