# Does observing until 06:00 help daily carbohydrate estimation?

Yes, modestly in this development comparison. It does not achieve the ±10% goal.

| Model | Days within ±10% | Mean absolute percentage error | Mean absolute error |
|---|---:|---:|---:|
| Personal historical mean | 14/44 | 20.58% | 39.65 g |
| Midnight sensor model | 15/44 | 20.18% | 39.69 g |
| Next-morning sensor model | 15/44 | 18.94% | 37.60 g |

All 44 original evaluation days were retained. All had 360 overnight Libre minute values; none had a recorded food event between midnight and 06:00 the following day. The absence of a food record does not prove fasting. The outcome remains the original calendar day's recorded carbohydrate total, not a shifted 30-hour total.

## Comparable training and selection

Both arms used identical training rows and 29 earlier chronological validation days. To avoid shared sensor windows across calibration and evaluation, calibration days whose extended 30-hour windows overlapped a query day were excluded from both arms. This reduced final training from 76 to 64 days. The prior context model's 18/44 result is therefore not an otherwise identical comparator.

Both arms searched the same ridge/kernel grid and summary/sequence representations; the delayed arm additionally received hourly overnight glucose/HR/activity summaries, with 15-minute overnight glucose values for its sequence variant. Both selected summary/context ridge with regularization 1000. Selection used earlier validation MAPE, then MAE; later labels were used only for evaluation and descriptive diagnosis. Missing context was retained with training-only preprocessing.

The delayed model improved absolute percentage error on 26/44 days. Its paired mean improvement was 1.24 percentage points. A seeded 5,000-resample participant-cluster bootstrap gave a descriptive 95% interval of 0.36–2.22 points improvement. With only 16 participants, many prior experiments on these data and model-selection uncertainty not included in this bootstrap, this is not confirmation of prospective accuracy.

## Failures and what they rule out

- P4, 513 g with 404 g recorded after 18:00: midnight predicted 333.69 g; delayed predicted 340.91 g. This remains 33.55% low. Truncating glucose at midnight is not the sole explanation of this model's failure.
- P26, 122 g: midnight predicted 208.87 g; delayed 211.93 g. More overnight information did not rescue this low-intake day.
- P9, 132 g: delayed predicted 200.34 g. P6, 150 g: delayed predicted 225.12 g. Predictions still remain near usual intake.
- Only 8/44 daily labels lie outside their person's earlier observed carbohydrate range; 4 remain outside even after allowing ±10%. Thus, lack of calibration range alone cannot explain most failures. Range overlap does not imply enough examples at each dose or metabolic state.

Verification: all 44 outcomes retained; current query labels replaced with a constant did not change predictions; every consumed participant source hash remained unchanged. Plan, coverage, fold assignments, selected settings, pre-scoring predictions, final predictions and range diagnostics are saved beside this report.

## Next discriminating step

Before expanding algorithms again, measure the stability of the daily glucose-to-dose relationship within each person's earlier calibration days. Compare genuinely different known daily carb totals with all available sensor features, and separately test whether a nonlinear model can fit those calibration days at all. Then evaluate the same fitted representation on the existing later days. Training success will be treated as a debugging check only; it cannot establish the requested accuracy. The current regularized models are still largely predicting typical intake.
