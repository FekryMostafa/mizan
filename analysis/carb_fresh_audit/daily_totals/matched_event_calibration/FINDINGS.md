# Context-matched personal calibration

Matching prior personal errors by sensor context did not achieve 10% daily carbohydrate error. This experiment uses supplied meal times and therefore remains a diagnostic, not passive inference.

The fixed correction takes three nearest earlier same-person events, weights their out-of-sample residuals by Gaussian similarity, and shrinks toward zero using two pseudo-events. No later target chooses neighbors, weights, or settings. Fixed distance scales are documented in PLAN.json. All four arms are reported.

| Matching inputs | Earlier event MAE, 320 events | Later daily MAPE | Days within 10% |
|---|---:|---:|---:|
| No correction | 23.072 g | 21.10% | 16/44 |
| Clock | 23.532 g | 23.46% | 13/44 |
| Glucose | 23.126 g | 22.66% | 15/44 |
| Clock, HR, activity | 23.629 g | 21.98% | 14/44 |
| Glucose, clock, HR, activity | 23.005 g | 21.61% | 16/44 |

The combined matching rule improved earlier event MAE by only 0.067 g, insufficient evidence of a dependable improvement. Later daily absolute error fell from 44.62 to 43.55 g, but percentage error rose; these are distinct metrics, and the 10% objective did not improve.

For P13's recorded 147 g meal, combined matching selected earlier meals recorded as 13, 78, and 54 g. Their earlier model errors were -21.35, +42.10, and +14.99 g. The resulting prediction rose from 58.67 to 65.32 g, still far below 147 g. Thus these sensor-distance features did not find calibration examples supporting the needed correction. This does not establish physical impossibility or identical full sensor traces.

Verified: all 2,036 neighbor lists contain only response windows ending before the query's premeal window; unchanged reference daily predictions reproduce within 1e-8 g; all 189 evaluation events and 44 days retained. Both earlier and later evaluation use target labels only for scoring, with historical labels used for calibration. Earlier calibration residuals were generated out of sample in the preceding experiment. The 44 development days have been inspected repeatedly, so this is not independent validation.

The existing passive ensemble remains better at approximately 18.40% mean error. The nearest-neighbor experiment does not justify replacing it. Further model search should address representation of the full response and temporal overlap, rather than treating this negligible earlier gain as a validated correction.
