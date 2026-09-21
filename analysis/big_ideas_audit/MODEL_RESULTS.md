# Continuous grams with ordinary-meal onboarding

Development experiment completed. The target of predicting all three macros within 10% is not achieved. Reserved participants 009–016 remain unparsed and unevaluated.

## Four earlier meals, then predict later meals

The eligible development data supplies 65 later meals from five people after four earlier meals per person are used for calibration. Population regression excludes the evaluated person. The model receives only three-hour glucose responses and premeal glucose state; personal corrections use the earlier known macro labels. No later food names, calories, macro labels, clock time or participant identifiers are predictors.

Fixed ridge regression, personal offset correction, personal linear correction and personal kernel correction all produced zero meals meeting the joint 10% target. The primary kernel correction's mean absolute errors were 39.6 g carbohydrate, 13.7 g protein and 13.0 g fat. A no-sensor calibration median had errors of 41.2, 15.6 and 13.7 g respectively. Improvement over that control is modest and does not establish useful gram recovery.

Nearest-onboarding matching got 6/65 meals within tolerance. Five were exact repeats of earlier macro labels; the sixth differed by only 2 g carbohydrate with identical protein and fat. Of 51 unfamiliar-macro meals, only that one was within tolerance. These successes are not evidence of general continuous dose estimation.

## Does additional onboarding help?

Compared four versus eight onboarding meals on exactly the same 45 later meals from the same five people. Population training and test inputs are unchanged. The extra four labeled meals occur before every test meal.

| Measure | Four onboarding meals | Eight onboarding meals |
|---|---:|---:|
| Primary continuous model: all three within 10% | 0/45 | 0/45 |
| Carbohydrate mean absolute error | 42.3 g | 41.0 g |
| Protein mean absolute error | 12.5 g | 13.1 g |
| Fat mean absolute error | 13.4 g | 11.7 g |
| No-sensor median fat error | 13.8 g | 12.2 g |
| Nearest-onboarding joint successes | 3/45 | 6/45 |

More onboarding improved fat error somewhat, but part of that improvement also occurs in the no-sensor control. It did not make any continuous-model predictions pass the joint tolerance.

One person's first four calibration meals had only two independent directions of macro variation. Eight meals supplied three for every evaluated person. This remedies one mathematical coverage limitation without fixing prediction accuracy. Full rank does not establish well-conditioned calibration, sufficient range, reliable labels, stable physiology or accurate inversion.

## Verification and limitations

All three runs completed. Independently checked evaluated-participant exclusion, calibration completion before queries, exact agreement of the two 45-meal test sets, and every saved success flag against its actual and predicted grams. Glucose interpolation is bounded by observed readings with gaps no greater than 601 seconds. No reserved-person file is opened by the modeling script.

The model uses the preliminary development meal audit, whose exclusions and unresolved food-log issues are described in [FINDINGS.md](FINDINGS.md). Food values remain logged estimates. This is development evaluation, not fresh validation, a daily total experiment or an automatic meal detector. Zero-valued labels require zero predictions under the strict relative tolerance; no unrequested absolute-error floor was substituted.

The primary kernel settings were fixed before each run. Other fixed approaches are reported as exploratory comparisons, not selected winners with independent validation. The eight-meal test follows inspection of the four-meal results and is explicitly an adaptive development experiment.

- [Initial 65-meal predictions](development_model/predictions.csv)
- [Initial results and controls](development_model/summary.json)
- [Four-meal calibration on the matched later subset](calibration_4_after_8/summary.json)
- [Eight-meal calibration on that same subset](calibration_8_after_8/summary.json)
- Training/calibration manifests and individual predictions accompany each result.

The initial four-meal run preceded adding configurable calibration counts to the same script. Its original source hash records that initial version; later run manifests record the updated source. All results remain from completed runs. A pandas/NumPy timedelta deprecation warning occurred during chronological assertions; these assertions passed, and chronology was checked independently from the saved timestamp manifests.
