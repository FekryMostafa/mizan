# Daily sensor context and sequence experiment

The selected context model reached 18/44 later days within ±10% (40.9%), versus 13/44 for the preceding model and the personal intake mean. However, MAPE was 20.77% and MAE 42.45 g, compared with 20.08% and 39.56 g for the preceding model. It traded more tolerance hits for larger errors elsewhere. The daily ±10% objective remains unmet.

## What was tested

Kept all 44 later days and the same 76 earlier calibration days. Evaluated full 96-point daily glucose sequences, daily summary statistics with prior 6/24-hour glucose/HR/activity context, and sequences plus context. Current-day hourly HR/activity were included in context. No current food information was supplied. Missing sensor features were centered/imputed from training data only, with zero deviations for unknown values.

Compared linear ridge and nonlinear Gaussian kernel ridge at five regularization values, plus personal historical mean. Selected shared settings using 29 distinct expanding-window validation days drawn only from the earlier period (after two and three calibration days per person). Summary plus context with kernel ridge 0.1 won. This validation differs from the previous one-window selection, so the outcome difference cannot be attributed to new features alone. These are development data already examined in earlier work, not fresh prospective evidence.

## Raw-number findings from the ten largest prior failures

Saved all ten nearest earlier same-person comparisons and paired 15-minute glucose values. Nearest trace matching here is descriptive; answers did not choose neighbors.

- P26: 122 g versus an earlier 167 g day. Mean glucose was 99.41 versus 94.90 mg/dL; summed positive 15-minute changes were 377.07 versus 236.00 mg/dL. Daily HR means were almost equal (87.53/87.25); activity means were 2.80/2.77 kcal/min. The lower-carb day had more upward movement both overnight and after 06:00. Daily HR/activity averages and removing overnight rises do not directly resolve this pair. These sums measure trace variation, not glucose mass.
- P9: 132 versus 182 g, but total positive changes were 196.67 versus 195.33. After 06:00 these remained nearly equal (162.67/161.33). HR and activity were higher on the lower-carb day. Midnight readings were 177.7 versus 157.3 mg/dL, before that day's breakfast. This shows the day starts with a glucose state the current day's food cannot explain by itself; it does not prove the cause of that state.
- P4: 513 versus 316 g, clock-matched whole-day trace RMSE 12.67 mg/dL. Current-day HR/activity were higher on the 513 g day (88.10 versus 78.83 bpm; 2.84 versus 1.83 kcal/min), so context is a plausible contributor, not an established correction formula. The 513 g record contains nine food entries, with 404 g logged from 18:19 onward. Late responses can extend beyond midnight. The source has multiple dinner entries; they cannot be assumed duplicates or silently dropped. Prior-day glucose context was incomplete.
- P27 provides an encouraging contrast: a 133 g day resembles an earlier 120 g day; copying 120 would be within ±10%, while the old prediction was about 200 g. A personal average can obscure an available useful historical comparison.

Neither these pairs nor the modest model result establish information-theoretic impossibility. They do show why replacing the model with one daily glucose-area-to-grams multiplier would be insufficient.

## Verification and next discriminating experiment

Recomputed all 44 saved predictions from exported sensor features and selected settings within 1e-8 g. Replacing every query carbohydrate label with 999999 left predictions exactly unchanged. All consumed participant source hashes were unchanged. Sensor-grid values are publisher-interpolated, not independent native measurements.

The next test should keep the calendar-day target and allow a clearly stated delayed estimate using the following six hours of CGM. That can test whether midnight truncation explains late-food failures. It must include earlier-day calibration with the same delay, audit coverage for every existing day, and keep unavailable cases visible rather than dropping failures. This would be a next-morning estimate, not a midnight prediction; it will also contain responses to any early next-day food, which the model must handle without being given that food's labels.
