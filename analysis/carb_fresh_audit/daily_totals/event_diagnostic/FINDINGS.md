# Detection versus amount estimation

This diagnostic separated finding eating hours from estimating grams during them. It did not achieve the daily10% goal.

Trained a classifier for any recorded-food hour and a separate Poisson regressor for carbs conditional on a recorded-food hour. Included zero-carb food events; did not equate food with positive carbs. Used the same64 calibration days (1,536 hours,249 food-containing hours) and44 later days (1,056 hours,172 food-containing hours). All configurations were fixed in advance:80 boosting iterations,7 leaves,min_leaf20,L2=1, with clock-only/CGM-only/CGM-plus-clock inputs. No candidate was selected after later scoring.

## Glucose contains some eating-time information

Hourly event average precision was0.295 with clock alone,0.384 with CGM alone and0.480 with both, against an event prevalence of0.163. At the untuned0.5 probability threshold, CGM-plus-clock precision was0.511 and recall0.273. Probabilities, not thresholded events, were used to form passive daily estimates. These scores are descriptive results on the reused later cohort; hours are not independent samples.

## Knowing eating hours still did not solve grams

| Inputs | Passive daily MAPE | Given recorded eating hours: MAPE |
|---|---:|---:|
| Clock only |27.75%|24.22%|
| CGM only |29.32%|23.94%|
| CGM plus clock |29.93%|25.22%|

Each comparison holds its conditional-grams model fixed and replaces its predicted eating probability with the true recorded-food indicator. The latter is an oracle diagnostic, not passive wearable performance. It gives timing information but no target gram quantity to the predictor. The oracle arms get12/44,10/44 and8/44 days within±10%, respectively.

The result indicates both imperfect event detection and poor conditional dose estimation in this implementation. Detection alone is not sufficient to explain the current error. The diagnostic is not a theoretical performance bound: a better conditional model or exact minute-level alignment could improve it. Food records may also be incomplete, so event labels are recorded eating rather than independently verified every instance of intake.

Saved all hourly probabilities, conditional gram predictions and daily sums. Reloaded models reproduce predictions exactly even when query targets and food indicators are replaced; the passive model never uses those label columns as features. The oracle indicator is intentionally used only in its separately labeled diagnostic branch. No daily evaluation records were removed.

Next potentially discriminating analysis: replace coarse hourly alignment with exact recorded meal start times in an explicitly oracle-timing experiment, then sum its meal predictions to the same daily targets. This can test whether the hourly formulation hides the meal-response shape, without counting supplied meal timing as a passive result.
