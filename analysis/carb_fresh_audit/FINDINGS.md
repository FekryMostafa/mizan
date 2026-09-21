# Fresh carbohydrate audit: two independent sensors

Re-extracted both sensor channels directly from 26 original CGMacros participant CSV files on 2026-09-08. Used four controlled meals per person: first 24 g and 66 g carbohydrate meals for calibration, then two later repetitions for evaluation. Recorded protein and fat are held at 22 g and 10.5 g; labels and chronology were checked against the original rows.

## What the signals show

With the two baseline-subtracted sensor curves averaged, the higher-carbohydrate meal has a larger peak in 25/26 calibration pairs and 23/26 later pairs. Separately, the later ordering holds for Dexcom in 22/26 and Libre in 23/26. There is useful dose-related information in these controlled meals. This is paired ordering, not successful inference of continuous grams or proof of causality.

Median same-meal disagreement between sensor response curves is 15.79 mg/dL RMSE. Median participant-level average same-dose repeat curve RMSE is 26.96 mg/dL for Dexcom, 18.75 for Libre, and 21.57 after averaging. These comparisons do not decompose biological variance from measurement error. Sensor channels in the released CSV are already interpolated, so minute rows are not independent native sensor observations.

## Fixed diagnostic conversion

Before execution, selected full-curve personal interpolation with the sensor average as primary, and each sensor separately as controls. A person's calibration low/high contrast defines a response per gram. Project each later curve onto that contrast, clipping predictions only at zero. No current meal carbohydrate label enters prediction. No hyperparameter tuning or post-hoc best-sensor selection.

| Input | Within ±10% | Mean absolute error |
|---|---:|---:|
| Dexcom | 5/52 | 19.25 g |
| Libre | 8/52 | 17.51 g |
| Two-sensor average, primary | 10/52 | 17.96 g |

No participant has both later predictions within ±10% using the primary method. All participants had sufficient paired coverage; no exclusions or abstentions. No significance or improvement claim is established by these descriptive comparisons.

For participant 1, the primary method predicts 33.38 g for a recorded 24 g meal and 35.02 g for a recorded 66 g meal. Both separate sensors also miss the 66 g meal substantially. This specific failure is not resolved by changing sensors.

## Conclusion

Carbohydrate dose ordering is considerably more encouraging than precise gram recovery. A fixed personal scale fails despite controlled composition and familiar doses. This does not rule out a state-dependent or nonlinear model. The next useful investigation is which measurable premeal states explain changes in response per gram across repeated meals, evaluated across people without tuning to each failure.

These are previously inspected development records and repeated recipes, not unseen doses or arbitrary meals. The target is still individual carbohydrate grams within ±10%; neither pair ordering nor mean accuracy substitutes for that target. Reserved BIG IDEAs participants were not accessed.

Saved raw sampled curves, coverage, contrasts, predictions, fixed plan, and SHA-256 input hashes. Recomputed error flags independently and checked query-key uniqueness after execution. Original data were read-only throughout.
