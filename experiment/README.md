# Collecting references we can actually audit

This supports the original target: predict carbohydrate, protein and fat grams from wearable signals plus earlier personal calibration, each within 10% on later meals. **No model has achieved that target. This recording tool does not predict macros from a sensor.**

The available data has sparse calibration, variable repeat responses and uncertain meal references. More arbitrary fitting cannot repair unknown consumed quantities. The next collection should make those quantities and the calibration/test boundary auditable.

For each ordinary meal used in the experiment:

1. Record a pseudonymous participant ID, meal ID, sensor ID and start/finish times including timezone. Preserve the sensor's original timestamps and units in its original export.
2. Weigh each component as served and its leftovers separately. Match the reference food's state to the weighed food: raw and cooked weights cannot be substituted without a documented conversion. A homogeneous mixture can share one nutrient basis; mixed leftovers require component-specific accounting.
3. Record the nutrition source, its mass basis, and carbohydrate/protein/fat values for that basis. Save its label photograph or source record. Missing fat remains unknown, never zero. Food labels still have uncertainty; this procedure does not turn them into chemical assays.
4. Record the scale resolution, preparation, additions, other intake, activity and sensor interruptions in accompanying notes. Keep annotations separate from signals available to a future wearable.
5. Designate calibration versus evaluation before examining predictions. Calibration includes only earlier measurements, including the complete response window. Keep later meal labels in a separate evaluation file from model inputs.

Known meals should include repeated ordinary recipes and varied portions/combinations; repetitions measure stability, while held-out amounts measure generalization. Simply repeating the same four macro labels does not establish continuous gram recovery. This document specifies data recording, not a diet, fasting protocol or prescribed nutrient challenge.

Before any final evaluation, freeze the preprocessing, model, onboarding selection, observation duration, allowable inputs and tolerance definition. Record a hash of that configuration and generate predictions before joining the held-out macro labels. Report every eligible meal and exclusion reason, every macro's gram error, and the fraction where all three are within 10%. Keep zero-gram handling explicit; do not introduce an absolute tolerance after seeing results. Meal detection and daily totals require separate validation.

`validate_meal.py` calculates recorded reference macros from the supplied nutrition basis and consumed mass, rejects basic unit/state/missing-value errors, and checks calibration chronology. It does not verify a nutrition source's accuracy, physical scale accuracy, complete intake recording, sensor alignment, or model generalization. `test_validate_meal.py` contains synthetic arithmetic and data-integrity tests only.

The eight reserved BIG IDEAs participants remain reserved. They can evaluate a frozen model later, but their logs will still have their own reference uncertainty. Preparing this collection format does not mark the macro-prediction goal complete.
