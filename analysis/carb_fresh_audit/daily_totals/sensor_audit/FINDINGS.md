# Two-sensor timing audit within CGMacros

Found reproducible relative timing discrepancies between Libre and Dexcom for several participants. No source timestamps, meal labels or prediction outputs were corrected. The deployed candidate models remain Libre-based; Dexcom was used only as a diagnostic reference and is not assumed ground truth.

## Initial quality checks

Examined the original participant files at15-minute spacing over the same30-hour observation windows for all44 evaluation days. None of the eight days outside every candidate model's tolerance range contained a Libre value at40/400 on this sampling grid. This does not exclude a bound value between sampled points. Inter-device mean absolute discrepancy was not greater on those failures: group medians27.53 versus31.59 mg/dL. Median unshifted correlation was lower,0.60 versus0.80. Different device means do not identify which device is accurate.

## Offset estimated from earlier calibration, then frozen

For each person searched relative Dexcom shifts from−120 to+120 minutes in15-minute steps, selecting the highest median same-day correlation across their original earlier calibration days. Required at least96 paired readings for a day/lag to enter selection. No carbohydrate labels entered this procedure. Applied the selected offset unchanged to later days; the main source values were not altered.

| Participant | Selected relative shift | Later median correlation before | After |
|---|---:|---:|---:|
| P6 | +30 min |0.162|0.507|
| P8 | +45 min |0.320|0.832|
| P9 |−75 min |0.485|0.870|
| P13 |−60 min |0.085|0.736|

Sign convention: compare Libre at t to Dexcom at t−lag. Relative alignment does not determine whether either device is correctly aligned to meal timestamps. For P13, the earlier calibration days also showed greatest agreement around−60/−75 minutes. This is not a lag selected to make later food answers fit.

The correction is not universally helpful: P15's selected−15-minute shift reduced its later median correlation from0.519 to0.376. P17 and P26 have large mean device offsets but comparatively stable curve agreement with zero temporal shift. Their calorie-prediction failures cannot be assigned to this same timing phenomenon.

## Implication

The raw signals are not all clock-aligned as their shared timestamp column suggests. Possible explanations include device timing differences or processing alignment, but the present evidence identifies relative offsets, not their cause. It also cannot establish which time reference matches food records.

This motivates a narrowly scoped sensitivity test: use only offsets estimated from earlier sensor data, consider the alternative that Libre is displaced relative to the shared meal clock, re-extract time-sensitive Libre features in a separate derived experiment and retain the original analysis as control. Do not silently declare a timestamp correction factual. Improvement in sensor correlation alone is not improved carbohydrate prediction, and the daily±10% objective remains unmet.
