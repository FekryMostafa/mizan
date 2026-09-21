# Is postmeal glucose contributing useful information?

Completed a diagnostic comparison on the same 65 later meals from five BIG IDEAs development participants. Population training uses 652 eligible CGMacros meals. Four earlier target-person meals supply personal calibration. Reserved participants remain unparsed.

The fixed randomized-tree model and personal kernel correction were run with all 15 glucose features and with only the two premeal features. Model hyperparameters were unchanged. A separate control permuted the 13 postmeal glucose values together as a curve between later meals within each person, keeping that query's premeal baseline and slope unchanged. Each of 50 permutations evaluated all 65 meals. Neither calibration labels nor query labels were shuffled.

| Input to the model | Carbohydrate MAE | Protein MAE | Fat MAE |
|---|---:|---:|---:|
| Premeal baseline and slope only | 41.03 g | 14.21 g | 13.19 g |
| Premeal plus correctly matched postmeal curve | 37.12 g | 13.48 g | 12.45 g |
| Premeal plus scrambled postmeal curve, average over 50 runs | 41.72 g | 14.70 g | 13.25 g |

The correctly matched postmeal response improved average errors in this experiment. The improvement relative to premeal-only was 3.91 g carbohydrate, 0.74 g protein and 0.74 g fat. This is consistent with some useful response information, but it is small relative to the remaining errors and does not validate 10% prediction.

Descriptive participant-bootstrap 95% intervals for those improvements were -0.12 to 7.48 g carbohydrate, -1.00 to 2.42 g protein and -0.56 to 1.97 g fat. All include zero. There are only five people; these intervals are unstable and do not correct for repeated analyst exploration. They are not proof that a macro has no signal.

Premeal-only produced zero joint successes, while the full model produced one. That one is the repeat pizza already diagnosed in [the transfer report](../transfer_model/FINDINGS.md), which a no-sensor calibration-mode control also predicts correctly. The target remains unachieved.

## Scope of the diagnostic

Removing postmeal features changes how the fitted model uses its remaining features; this is a model ablation, not a physiological intervention. Permuting postmeal curves breaks their association with food and can also create mismatches with premeal state. Therefore these permutations are descriptive diagnostics, not a formal causal test or an information-theoretic limit. They must not be used to claim that better representations, physiological models or additional measurements cannot help.

Before interpreting the controls, the full model reproduced all original transfer predictions within 1e-10. Independently verified 3,380 saved prediction rows, identical query sets in all 52 evaluations, unique event keys and all success flags recomputed from grams. The run completed without changing the frozen test participant reservation.

- [Every prediction](predictions.csv)
- [All ablation and permutation results](summary.json)
- [Participant-bootstrap diagnostic](paired_uncertainty.json)
- [Run provenance](run_manifest.json)
