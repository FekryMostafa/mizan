# Carbohydrate feature-to-gram check

8 September 2026. This is a diagnostic conversion check of extracted features, not a finished wearable model. Four fixed representations were compared: peak height, positive area from 60–120 minutes, both, and both plus premeal glucose level/slope. Each uses a source-trained linear ridge conversion (alpha 10) and a personal offset from four earlier labeled meals. No query fat/protein amounts, food names or query carbohydrate labels enter the conversion.

Selection used leave-one-person-out CGMacros evaluation, fitting the population conversion without that person and calibrating with their first four eligible meals. The lowest person-balanced gram error selected peak + area + premeal context. Its source error was 23.57 g, essentially tied with peak + area (23.58 g), versus 25.08 g for the personal median. This tiny difference does not establish a superior algorithm. The feature families themselves were informed by earlier exploratory inspection; this is not fully nested, pristine validation.

All alternatives were then evaluated on the same 65 later BIG IDEAs development meals from five people. These records have already been inspected in other experiments; reserved participants remain unopened.

| Representation | Meals within ±10% carbohydrate | Mean absolute error |
|---|---:|---:|
| Peak height | 5/65 | 39.75 g |
| Middle response area | 7/65 | 40.07 g |
| Peak + area | 6/65 | 39.85 g |
| Peak + area + premeal context, source selected | 6/65 | 39.68 g |
| Personal median without CGM | 5/65 | 41.18 g |

The area-only alternative has more hits but was not selected using these target labels. No candidate is close to the requested accuracy.

## What fails in the raw features

For the source-selected conversion, all 27 meals outside the person's four-meal carbohydrate calibration range failed ±10%, with 70.51 g mean absolute error. The 38 inside that range produced six hits and 17.78 g error. Calibration range is evaluation metadata only. Wider calibration deserves examination, but this comparison does not prove it would fix the failures.

The 14 meals above 100 g carbohydrate all failed, averaging 92.27 g error. The largest miss was participant 6, March 5 at 23:30: recorded 228 g, predicted 67.84 g. Its peak rose 94.79 mg/dL and its middle positive area was 4603.54 mg/dL·min. Two same-person meals provide a useful comparison:

| Meal | Recorded carbohydrate | Peak height | Middle positive area |
|---|---:|---:|---:|
| March 2, 22:00 | 226 g | 100.43 mg/dL | 4835.23 mg/dL·min |
| March 4, 08:25 | 56.5 g | 102.81 mg/dL | 5105.93 mg/dL·min |

The two high-carbohydrate meals have similar feature values, which is encouraging for repeatability. But the 56.5 g meal has an even higher peak and area: these two features alone do not order the recorded doses consistently. Other curve features, preceding history, food composition, and label uncertainty remain possible explanations. This does not establish identical complete glucose traces or prove CGM inference impossible.

## Next feature question

Examine the complete trajectories of these same-person high/low carbohydrate cases, including timing, early versus late area and preceding glucose, before adding complexity. A candidate feature must separate these cases consistently across other meals; choosing a special rule from their labels would not validate it. Fat and protein remain separate unresolved analyses and should not be combined into a claimed accurate system.

Verification checked that every method uses the same existing 65 query keys, all saved absolute errors and ±10% flags recompute correctly, and every calibration response finishes before the first query. Predictions, raw features for ranked failures, source selection scores and input/script hashes accompany this report. Meal labels are recorded estimates, not chemically verified intake.
