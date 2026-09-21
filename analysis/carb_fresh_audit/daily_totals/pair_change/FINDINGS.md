# Learning changes in daily intake directly

Stayed with CGMacros and the same daily target. No other dataset was used.

## What successful and failed days had in common

For the best previous delayed linear model, 11/15 successful days were already within ±10% using the person's historical mean. Four days were rescued by sensor corrections; three baseline successes were harmed. On the 26 days both methods missed, the median absolute difference between actual and usual intake was 53 g, but the median absolute model correction was only 4.45 g. On days both got right, those values were 9.6 g and 7.68 g. Thus, many apparent successes reflected ordinary intake, while large changes remained inadequately predicted.

The rescued P13/P14/P15 days had lower total upward glucose movement than their own earlier average and lower carb intake. P26's rescued 243 g day had somewhat higher upward movement and mean glucose. However, P27's harmed 204 g day had lower upward movement despite above-usual carb intake. These outcome-conditioned examples motivate testing a representation; they are not validated individual correction rules.

## Direct change model

Built training pairs only from earlier days of the same person. Each pair contributes the difference in sensor features and the difference in known carb totals. Reversed pairs were included, and predictions were made antisymmetric by averaging forward and negative reverse predictions. For a query day, the model adds the predicted change to each known historical day's carbs and averages these estimates. Current food labels are never inputs.

Compared low-dimensional glucose shape, glucose summaries, and glucose/history/activity context, with three ExtraTrees leaf settings and a personal-mean baseline. Selected settings on the same 29 purged earlier validation days. The selected shape model used minimum leaf size 10.

It got 13/44 later days within ±10%, MAPE 20.47%, MAE 42.15 g. The matched baseline got 14/44, MAPE 20.58%, MAE 39.65 g. The direct change formulation did not solve the large-change problem or reach the objective.

The 206 directed training pairs came from only 64 days and are not 206 independent observations. The earliest selection fold had only one participant with two usable training days, so its learned change function is particularly weakly supported. All 44 later outcomes remain included. The serialized model reproduced predictions exactly after query labels were replaced with a constant.

The result narrows the algorithmic explanation: predicting differences rather than absolute daily grams is not by itself sufficient with these features and calibration data. It does not prove all useful physiological features have been exhausted. The best previous daily MAPE remains 18.94%, and no tested model has demonstrated daily ±10% accuracy.
