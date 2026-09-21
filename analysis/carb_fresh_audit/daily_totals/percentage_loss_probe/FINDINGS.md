# Training directly for percentage error

Optimizing percentage error helped this boosting model, but did not achieve 10% or beat the existing passive ensemble.

Earlier chronological validation selected a seven-leaf model using glucose and activity context, trained with absolute loss weighted by inverse recorded carbs. This minimizes training absolute percentage error rather than squared gram error. Its earlier validation error was 23.05%, compared with 31.58% for the otherwise matched squared-error model. It still performed worse than the previously validated glucose kernel model (20.69% on the same 33 validation days); it should not replace that model based on later results.

On the same 44 later development days, the selected percentage-loss candidate obtained 20.73% MAPE, 43.25 g MAE, and 17/44 days within 10%. The previously recorded passive ensemble remains lower at approximately 18.40% MAPE. More days passing the threshold does not mean the mean-error objective has been reached.

Eight prespecified boosting configurations and two personal baselines were compared on earlier days only. Each query retained other people's allowed training rows and only its person's earlier nonoverlapping days. Inputs contain sensor data through next morning, plus historical personal intake mean. A training row's personal mean excludes that row's own label; singleton groups use the other rows' mean. No query meal time, food identity, or macro amount is used. This loss uses labels as training weights only.

Verified: all 44 later days retained; saved model reproduces predictions with query labels replaced by a sentinel; mutating the first training target does not alter that row's personal-mean input. Settings were written before later scoring. The 44 days have been repeatedly inspected and are not an independent validation set.

The result shows that loss choice affects this model's performance, but is insufficient to close the remaining gap. It does not establish that the physiological signal is absent or that another model will necessarily succeed.
