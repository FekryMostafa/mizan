# Objective audit: daily carbohydrates within ±10%

Recomputed scores from saved per-day predictions for14 experiment outputs. All evaluate the identical44 participant/day keys with identical recorded carb totals. No duplicate keys, missing predictions, or changed target labels were found.

No experiment meets either daily±10% on every evaluated day or even mean absolute percentage error≤10%. Lowest observed MAPE is18.395%, from equal-weight averaging, with16/44 days within tolerance. Highest tolerance hit count is18/44 from the context model, whose MAPE is20.765%. These are different models; their best metrics cannot be combined into one claimed result.

Successful calibration interpolation is not success on the objective: shuffled calibration labels also fitted perfectly. Known current fat/protein/fiber supplied in a diagnostic did not solve the daily problem. Baseline labs and the secondCGM timing comparison were diagnostics requiring additional information, not proof of CGM-only prediction. The relative timing correction did not resolve the large errors.

The later44 days have been repeatedly inspected while hypotheses and representations were developed. Even a future fit to those exact outcomes would not independently verify generalization. This is separate from whether the observed error reaches10%; currently it does not.

The supported hypotheses tested include personal calibration, full sequences, daily context and activity, delayed overnight observation, nonlinear shared/personal mappings, within-person change prediction, sustained elevation, baseline phenotype interactions, training/evaluation corrections, ensembles, source-label duplicates, and relative sensor timing. These tests are not an exhaustive mathematical proof that every possible algorithm fails. They provide no supported correction that establishes the requested accuracy.

Current state: genuine impasse for certifying this objective with the present approach and evidence. No switch of dataset is authorized by the latest user steering. No model is certified, no rows are removed to manufacture success, and no source labels are changed. The goal remains unachieved. First blocked-condition audit recorded; no blocked goal status has been set at this point.
