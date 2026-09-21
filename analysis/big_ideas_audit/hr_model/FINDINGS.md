# Does heart rate resolve glucose-only failures?

8 September 2026. Completed a fixed-model comparison on the same 65 later development meals from five people. Population fitting uses the same 652 CGMacros meals. Four earlier meals provide personal calibration. The eight reserved participants remain unaccessed.

Downloaded six BIG IDEAs development heart-rate files, totaling 97,547,610 bytes, and checked all against the publisher's SHA256 manifest. Their actual headers are `datetime, hr`, rather than the generic column names described in the dataset documentation. The reader strips whitespace and handles that observed schema explicitly.

Heart rate was summarized at one-minute resolution in four windows: 30 minutes before food, and each of the three hours after food. Each window contributes mean, standard deviation and coverage. Windows below 50% minute coverage have missing summary values; coverage remains an input. Training-only imputation and missing-value indicators preserve identical query sets. Source minute readings and target one-second readings are reduced to minute medians before these summaries, although devices and their measurement processes still differ.

## Results

| Inputs | Joint success within 10% | Carbohydrate MAE | Protein MAE | Fat MAE |
|---|---:|---:|---:|---:|
| Glucose | 1/65 | 37.12 g | 13.48 g | 12.45 g |
| Heart rate | 0/65 | 40.27 g | 15.05 g | 13.04 g |
| Glucose plus heart rate | 0/65 | 38.59 g | 13.92 g | 12.44 g |

Adding these heart-rate summaries did not improve the tested model materially. Fat error changed by only about 0.02 g; carbohydrate and protein errors worsened. The glucose-only success is the already calibrated pizza described in the earlier transfer report. It is not an unfamiliar-dose success.

This does not establish that all heart-rate representations or other physiological measurements are unhelpful. Across all 86 eligible development meals, heart-rate window coverage averages roughly 75–78%, versus 93–94% in source meals. Missingness and source/target device differences limit the test. The model and calibration were fixed before this comparison; there was no outcome-based parameter selection.

## Verification

The original glucose-only predictions were reproduced within 1e-10. All 195 saved predictions have independently recomputed tolerance flags, unique event keys and identical 65-meal query sets. All six downloaded file hashes were rechecked after execution. The feature export and all three model runs completed. A pandas/NumPy timedelta deprecation warning during time-window construction did not interrupt extraction; the saved window coverage and aligned dates were inspected.

The ±10% target remains unachieved. This experiment tests an available additional signal directly instead of assuming that extra context must fix the problem.

- [Every prediction](predictions.csv)
- [Summary](summary.json)
- [Run provenance](run_manifest.json)
- [Heart-rate date ranges and minute coverage](../hr_quality.json)
