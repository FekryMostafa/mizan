# Calibration preservation and HR/activity test

## Confirmed conversion weakness

Replayed the original selected feature-combination model on the same personal calibration examples used to normalize its inputs. Only 9/52 predictions reproduce their known doses within ±10%; MAE is 8.66 g. Recomputed its later predictions simultaneously and verified agreement with the original saved results.

Example: P8's actual calibration doses of 24/66 g become approximately 38/56 g. P3's become 35/57 g. The original design normalizes with calibration values, but the learned population conversion can move both anchors toward the middle. Therefore a later response resembling a calibration response need not receive that calibration's known dose. This is a verified design limitation for the requested personalization, not proof that every miss is an implementation defect.

## Controlled test

Compared four linear ridge variants: CGM only, CGM plus activity, and each with exact personal calibration constraints. Activity features capture HR mean/90th percentile/coverage and Fitbit calorie-estimate mean/coverage separately before the meal and during three postmeal hours. Missing values are imputed from training rows only, with coverage retained. METs and Intensity are not conflated.

Each outer person is excluded from population fitting and model selection. Their two earlier known calibration meals are permitted onboarding data. Inner person-held-out selection chooses ridge penalty 1, 10 or 100 separately for each variant. The anchored version enforces exact outputs on the two personal calibration examples. These constraints can also lock in noisy calibration; perfect calibration fit is not evidence of later accuracy.

| Variant | Later meals within ±10% | Later MAE |
|---|---:|---:|
| CGM, unconstrained | 9/52 | 15.82 g |
| CGM, calibration preserved | 11/52 | 17.61 g |
| CGM + activity, unconstrained | 4/52 | 22.01 g |
| CGM + activity, calibration preserved | 10/52 | 17.30 g |

All constrained calibration predictions match their known labels to numerical precision by design. No later labels are used for constraints. No snapping to 24/66 g is applied. No exclusions. These linear variants are not identical to the earlier selected linear/quadratic mixture, whose result was 9/52 with 15.20 g MAE. More hits with worse MAE is not an across-the-board improvement.

## Case investigation

With calibration preserved and activity included, P8's two meals change from 36.6/51.5 g to 24.1/61.0 g, both within ±10%. P2's 66 g meal improves from 39.5 to 66.8 g. P42's 66 g meal moves from 58.7 to 70.7 g. However, five previous successes become misses while six previous misses become hits; these examples are not representative proof of improvement. P36's previously correct 66 g estimate becomes 104.6 g.

For the constrained CGM-only model, inspected exact linear feature contributions relative to each same-dose calibration:

- P3, 66 g: several changes in peak, early peak, rise rate and peak timing cumulatively lower the prediction. No single catastrophic feature explains it.
- P36, 24 g: middle-window area contributes about +11.9 g, the largest term in a substantial overestimate. Similar-looking absolute glucose peaks do not imply equal baseline-relative responses. The visual review's suggestion of a pure conversion problem was too strong here.
- P38, 24 g: late area, response duration and late-area fraction collectively push the estimate upward. Correlated summaries make the attribution nonunique as a physiological explanation.
- P27, 66 g: early area, early peak, peak time and rise rate all push downward, eventually giving a negative raw estimate clipped to zero. This is an extrapolation failure of the conversion, not evidence that no carbs were eaten.

Attributions explain arithmetic inside this model; they do not identify causal physiological mechanisms or prove a different feature representation will recover grams.

## Conclusion and verification

The calibration inconsistency is real and can be removed. Removing it does not achieve the target. These HR/activity features do not deliver an overall accuracy improvement. ±10% remains unverified on later meals and on arbitrary meals.

Verified 208 unique later predictions across four variants, all saved error flags, exact calibration constraints, and reproduction of the original model's later predictions during calibration replay. Saved per-meal comparisons, feature attributions, selection results and hashes. All 52 later controlled-dose development meals are retained. No reserved participants accessed. Earlier inspection of this dataset remains a limitation; this is exploratory development evidence, not pristine final validation.
