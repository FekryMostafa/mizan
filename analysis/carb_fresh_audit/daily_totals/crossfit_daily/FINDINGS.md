# Shared model with out-of-bag personal calibration

Corrected the prior shared model's training shortcut. The sensor model no longer receives a personal carbohydrate mean containing the training target. Each person's additive correction uses the mean error on their known calibration days, with each calibration prediction averaged only over trees that did not train on that day.

Result: 15/44 later days within ±10%, MAPE 20.27%, MAE 40.73 g. The matched personal-mean baseline gets 14/44, MAPE 20.58%, MAE 39.65 g. This does not reach the daily accuracy objective and does not establish a meaningful advantage over usual intake.

## Design and verification

Kept the same 64 earlier calibration days, same 29 earlier chronological validation days, same 44 later evaluation days and six-hour delayed observation window. Compared RandomForest and ExtraTrees, glucose-only and glucose/activity/history features, leaves 2/5 and personal correction multipliers 0/0.5/1. Every forest used 200 bootstrap trees with a fixed seed. The personal mean baseline was included in model selection. Earlier validation MAPE then MAE selected glucose-only ExtraTrees, leaf 5, full personal correction.

Features consist of raw sensor summaries and their deviations from personal sensor means. Neither current carb labels nor personal mean carb labels enter the forest. Known calibration labels are used for fitting and personal adjustment, as allowed for onboarding.

Every calibration row had at least 54 trees that excluded it from fitting. Increasing the first calibration label by 10,000 g and refitting left that row's own out-of-bag prediction unchanged within 1e-8 g. This verifies the specific shortcut has been removed. The adjustment then legitimately uses known calibration errors; those adjusted calibration values must not be called held-out evaluation predictions.

Saved model replay with all query carb labels replaced reproduced every later prediction exactly. All 44 days remained in scoring, and the source feature file hash remained unchanged. Calibration/evaluation sensor windows are separated by the existing purge. Out-of-bag calibration itself is not chronological; it operates on the fully available onboarding set. Later evaluation is chronological.

## Conclusion and remaining evidence gap

Independent personal interpolation, shared nonlinear residuals and corrected shared nonlinear calibration all remain near a 20% mean daily error on these repeatedly examined development days. The best previously observed daily MAPE is 18.94%, with only 15/44 days within ±10%. Perfect calibration fits do not establish recovery of true daily intake.

There are only 2–5 accepted calibration days per person, and the target is recorded intake rather than independently verified complete intake. Model development also reused the same later days repeatedly. These facts limit what can be established from current experiments; they do not prove that CGM-based daily carbohydrate inference is physically impossible.

Further work should first audit whether large-error daily labels are supported by distinct source food records and whether repeated images or duplicated meal entries inflate totals. Preserve every record and treat suspected duplicates as unresolved until source evidence supports a change. Repeatedly changing model families on the same small development set cannot substitute for validating the labels or obtaining a fresh evaluation.
