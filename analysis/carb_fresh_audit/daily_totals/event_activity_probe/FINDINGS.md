# Event-aligned activity and heart rate

Adding activity helped this glucose model modestly; it did not reach daily carbohydrate error within 10%. These are the same repeatedly inspected 44 development days, not fresh validation.

| Inputs | Mean absolute percentage error | Days within 10% |
|---|---:|---:|
| Glucose + clock | 21.52% | 9/44 |
| Glucose + clock + activity | 20.27% | 15/44 |
| Glucose + clock + activity + HR | 21.10% | 16/44 |
| Clock + activity + HR, without glucose | 19.73% | 14/44 |

All arms use 820 earlier labeled events and the same fixed boosting settings. Evaluation uses 189 supplied meal timestamps, then sums predictions into 44 daily totals. This is a diagnostic with known meal times, not a passive wearable result. No current food amounts are predictors. All arms are reported; no selection based on these outcomes.

Activity alone reduced absolute errors on 24/44 days; activity plus HR reduced them on 22/44. One correction: P6 April 14, recorded 229 g, moved from 162.56 to 215.23 g with activity. One regression: P27 June 18, recorded 133 g, moved from 151.48 to 179.78 g. Thus activity is not a universal correction.

The P13 147 g meal moved from 37.10 to 49.46 g with activity and 58.67 g with HR added. Its full 297 g day moved from 184.09 to 216.46 g with both. The following 294 g day remained severely underestimated at 185.59 g. These associations do not establish why those meals produce their glucose response.

All 189 query activity windows were complete under the 90% per-bin rule; 161 had complete HR bins. Unobserved bins remain missing, not zero. Activity calories are tracker estimates. The model without glucose performed better by mean error than these glucose arms, so the comparison does not demonstrate reliable recovery of carbohydrate dose from glucose.

The earlier passive ensemble's 18.40% error remains lower than these diagnostics. The 10% goal remains unmet.

## Reproducibility

Initial reference refitting failed: default CSV parsing perturbed training floating-point values and changed tree results. Reading the original training CSV with `float_precision='round_trip'` restored event predictions exactly (maximum difference 0.0 against the original saved model). The final run reproduced the prior reference daily predictions within 1e-8 g. Every saved model reproduces its predictions after reloading, including when query target labels are replaced with a sentinel. Original outputs and source records were preserved.

Outputs: `summary.json`, `daily_predictions.csv`, `event_predictions.csv`, and `failure_comparison.csv`. A further useful experiment would test calibration of event-level errors using only each person's earlier events, with chronological validation inside the earlier period; the present activity arms do not implement that residual calibration.
