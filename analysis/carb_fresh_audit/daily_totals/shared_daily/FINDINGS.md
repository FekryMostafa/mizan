# Shared nonlinear daily model

The shared ExtraTrees residual model got 14/44 later days within ±10%, with 20.01% MAPE and 39.95 g MAE. The same calibration-day personal mean also got 14/44, with 20.58% MAPE and 39.65 g MAE. This experiment did not reach the objective or improve on the previous delayed linear model's 18.94% MAPE.

Used the same 64 calibration days, 44 later days, and purged 29-day chronological validation setup. Compared RandomForest and ExtraTrees, glucose-only versus glucose/history/activity/HR summaries, minimum leaves 2/5/10 and depth 3/unlimited. Each forest had 100 trees with a fixed seed. Selection used earlier validation MAPE then MAE. ExtraTrees with context and minimum leaf 2 won. Current query meal labels were not predictors; saved-model replay with query labels replaced left all predictions identical. Source feature file hash remained unchanged.

## Training-fit caveat found in inspection

The reported 64/64 training tolerance hits (1.05% MAPE) should not be interpreted as clean evidence of fitting sensor-to-dose relationships. The personal mean carbohydrate input is computed from the calibration set, including the very row being fitted. Each training answer contributes 20–50% of that mean. The target residual also subtracts that mean. This is a training/evaluation mismatch and contaminates the interpretation of training fit.

Later queries do not contribute to their baseline or model inputs, so their poor performance is still a valid development outcome under the declared setup. The training caveat does not invalidate later scores, but is a concrete reason to improve how the shared model learns personalization.

The earliest validation training fold has 17 rows and only one person with at least two calibration rows. Only two rows there permit within-person leave-one-out calibration. The next fold has 27 rows with at least two per person. Simply dropping all rows without leave-one-out history would make the first shared training fold nearly empty.

## Next correction

Train the shared nonlinear model on sensor inputs without an input baseline containing its own target. Estimate personal adjustment using out-of-sample predictions for the known calibration days. This preserves learning across people while preventing the training answer from entering a personal-mean feature. Use the same purged evaluation and report any calibration rows without an out-of-sample prediction. Do not interpret impurity feature importance as evidence of independent predictive signal.

The later-day results do not establish impossibility. They also do not validate the requested ±10% daily carbohydrate accuracy.
