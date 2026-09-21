# Retaining the full other-person calibration pool

This changed model selection, but did not improve later-day accuracy. Selected glucose-summary kernel regression with penalty 0.1 gives 15/44 later days within ±10%, MAPE 21.00%, MAE 42.59 g. The previous delayed linear model remains better on this reused development set at 18.94% MAPE.

## Validation correction

For each eligible day in the 64-day earlier calibration pool, withheld that participant's current and subsequent days, including any preceding 30-hour sensor window that overlaps the query day. Retained all original calibration records from other participants. This yielded 33 earlier validation days, each with 60–62 training rows, versus the older synchronized 17/27-row folds. The 44 later days were excluded from selection. Since cohort dates were shifted and participants were independent, chronology was enforced within person rather than across unrelated calendar dates.

Compared the same ridge/kernel penalties across sensor-summary, glucose-only and full-sequence families, plus personal-mean baseline. The selected model had 20.69% MAPE and 13/33 hits in earlier validation; the previous strongly regularized summary model had 24.41% and 10/33 under the same new folds. The selection rule was followed before scoring later outcomes.

## Did the model stop clinging to usual intake?

Yes, descriptively. Median absolute correction from personal mean increased from 6.51 g to 17.23 g. Yet only 19/44 later days improved in absolute percentage error. Four previous successes became misses and four previous misses became successes. Bigger corrections were not reliably better corrections.

P26's 122 g day improved from 211.93 to 183.39 g but remained 50.32% high. P9's 132 g day worsened from 200.34 to 211.85 g. P6's 150 g day remained badly overestimated at 230.17 g. These examples show why shrinkage alone was not a sufficient explanation of the failures.

Query label replacement left every prediction identical. All 44 later days remain in scoring. Saved files include validation membership counts, candidate scores, individual earlier validation predictions, settings saved before later scoring, later predictions and old/new comparisons.

The goal remains unachieved. This experiment removes one plausible evaluation-design explanation without establishing that no other CGM representation could work. Further improvements must demonstrate corrections that track actual intake changes; larger corrections or better calibration fits alone are insufficient.
