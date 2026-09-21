# First wearable meal-model experiment

## Result

The published signals differ across meals. A simple proportional current-to-intake model produces gram outputs, but those outputs are unstable under baseline choice and lipid-channel choice. This first model does not support a reliable grams estimate. That conclusion applies to this model and dataset, not to the feasibility of a future personalized wearable.

## What was actually run

Read the original numerical Figure 4 workbook, sheets 4e–4i. Preserved all source files. Plotted glucose, cholesterol, TG-related current, pH electrode voltage, ATP and sweat rate. Used the shared 1–55 minute recording window and resampled currents at one-minute intervals. Verified the main calculation again at one-second resolution; ratios changed by less than 0.001.

Built a deterministic, one-reference proportional model, not a trained neural network. Its primary feature is the integrated positive current above the separate fasting trace, divided by the window duration. For each channel:

`conditional grams = assumed reference grams × meal feature / reference feature`

Glucose is the candidate carb channel; TG-related current is the candidate fat channel. Meal names are used for display and selecting the reference, not feature extraction. Pizza is therefore a calibration input, not an independently predicted meal. Fasting gives zero by construction, not as a successful test. No measured macro labels exist to train or evaluate this model, so no accuracy metric or confidence interval is claimed.

The illustrative scale is **pizza = 60 g carbs and 25 g fat**. These numbers are explicitly invented calibration assumptions, not recovered pizza portions, nutritional database estimates, or study facts. Doubling either assumed macro doubles every corresponding output.

## Outputs under that assumed scale

| Meal | Carbs, g | Fat from TG-related current, g |
|---|---:|---:|
| Bacon and eggs | 22.4 | 7.5 |
| Pizza, fixed reference | 60.0 | 25.0 |
| Ground beef | 23.5 | 3.1 |
| Milkshake | 91.0 | 0.0 |

The milkshake zero means its current does not exceed the fasting trace in this window. It is a failure of the assumed conversion, not evidence of zero fat intake. These results are conditional calculations, not calibrated physiological predictions.

## Patterns and failure checks

- Milkshake and pizza have the largest glucose currents. Bacon/eggs and beef have similar, lower glucose currents.
- Pizza has the largest TG-related current peak. Beef has the largest cholesterol current peak. Those channels do not provide an interchangeable measure of dietary fat.
- Switching from the fasting trace to each recording's early level changes milkshake carbs from 91.0 g to 18.3 g. Early levels were already post-meal, so this alternative can subtract an existing meal response.
- Using raw current levels without baseline subtraction gives milkshake fat 11.8 g, versus 0 g with fasting subtraction. The same raw-level model assigns fasting 18.9 g carbs and 20.9 g fat, illustrating background contamination.
- Using cholesterol in place of the TG-related channel changes beef fat from 3.1 g to 89.4 g. No evidential basis was found for selecting or averaging these outputs as an accurate fat estimate.
- Using only recording minutes 20–55 changes bacon/eggs fat from 7.5 g to 49.1 g. The observed window matters considerably.

These alternatives are sensitivity tests, not candidates selected using knowledge of the meals' expected macros. Their spread is not a statistical uncertainty interval.

## Data and calibration issues

- Five conditions from one participant, not thousands of independent meal examples. Current records contain 3,301–3,436 complete one-second rows per condition. No random row train/test split was used.
- Source data are electrical currents. ATP-dependent TG calibration was **not applied**. The scientific supplement supplies an interpolation table in current-density units while Figure 4 provides nA currents. The corresponding electrode-area/current normalization and reproduction of published calibrated meal curves remain unresolved in this first pass. Consequently the gram outputs above must not be represented as the result of a fully calibrated wearable pipeline.
- ATP has only five reported points per condition. Fasting, pizza and beef contain exactly identical ATP arrays, which should be clarified before treating these as independent measured correction trajectories.
- Sweat-rate records contain negative values: six for bacon/eggs, one for pizza, eight for beef. Values were preserved and not used as a nutrient-mass multiplier. These need a source-defined treatment; a negative measured rate is not negative physical sweat production.
- The bacon/eggs pH-voltage header says V while other sheets say mV; numerical ranges are similar. No silent unit conversion was performed.
- Meals were consumed approximately 30 minutes before patch placement; induction and filling add time before sensing. Recording minute zero is not meal time. The separate fasting visit is not each meal's true pre-meal baseline.
- The TG-related chemistry also responds to endogenous glycerol. Even correctly calibrated concentration is not pure dietary TG or ingested fat mass.

## Next technically useful iteration

Reproduce the authors' ATP-corrected meal curves before interpreting relative fat amounts. Then rerun the same frozen feature and sensitivity calculations. Do not tune the model to expected meal macros and describe that as validation. Known-intake onboarding would provide a real scale, but repeat meals/days would still be needed to test its usefulness.

## Files and provenance

- `raw_signals.png`: all source channels.
- `model_sensitivity.png`: outputs under three baseline definitions.
- `conditional_outputs.csv`, `window_sensitivity.csv`: numerical outputs.
- `signal_features.csv`, `quality_checks.csv`, `metadata.json`: reproducibility details and source hash.
- `analyze.py`: rerunnable model; arguments `--reference-carbs` and `--reference-fat` change the explicitly assumed scale.

Source: Mizan/dataset/sweat/lipid_study/source-figure4.xlsx, sheets 4e–4i. [Paper](https://www.nature.com/articles/s44460-026-00117-0), main Figure 4 and Methods; scientific supplement Note 3, Figure 38 and Table 1. The supplied Karpathy article informed the inspect-first, simple-model, visualization and sensitivity-check workflow. No model-performance claim is drawn from that article.
