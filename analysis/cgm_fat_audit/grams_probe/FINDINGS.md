# Personalized macro grams: first measured result

7 September 2026. **The requested 10% error target was not achieved.** Predictions and errors are in `all_meal_predictions.csv`. This supersedes any suggestion that a measurable average macro effect already establishes reliable individual gram recovery.

## What we tested

The question was whether three hours of glucose plus four earlier, labeled calibration meals could recover the carbohydrate, protein and fat grams of later meals. The target was absolute error no larger than 10% of the recorded amount for **each** macro on the same meal. We also report average gram errors, so this is not merely a pass/fail definition issue.

Only four controlled breakfast recipes were considered, each consumed twice and marked 100% consumed. Other food within three hours and incomplete sensor windows were excluded under the existing audit rules. All four calibration meals must precede every evaluated meal. That last check excluded participant 12, whose recipe schedule was atypical. Final sample: 22 people / 88 later meals for Libre, 21 people / 84 for Dexcom. These are substantially overlapping people and meals, not independent replications.

This is an easier setting than unknown everyday meals: meal times are supplied and future meals repeat the known recipes. The recipes are 66C/22P/10.5F, 24C/22P/10.5F, 66C/66P/10.5F and 66C/22P/42F. All have zero labeled fiber. This does not test intermediate doses, pure fat or whole days.

## Raw-signal findings before regression

I compared baseline-adjusted curves on a 15-minute grid. For each later meal, I measured its distance from that person's four earlier curves. No current recipe name or study-day number was supplied to the matching procedure.

At three hours, the correct earlier recipe is closest for 28/88 Libre meals and 26/84 Dexcom meals, compared with a 25% random four-choice reference. Restricting the question to low versus high fat gives approximately 48% correct matches on both sensors, against a 50% two-choice reference. The corresponding carbohydrate distinction is approximately 64% and 62%; protein is approximately 45% and 60%.

Using one, two or three hours and either the preceding baseline or meal-start glucose changes results but does not produce strong four-recipe separation: across these fixed checks, approximately 26–36% are correctly matched. These are exploratory comparisons, not a search that establishes the best possible representation. The raw matching method uses equal weighting over time and only one calibration example per recipe.

## Models and controls

The no-sensor controls return the mean or median of the known calibration macros. The personal-curve control returns the macros of the nearest earlier curve. The trained candidates are standardized ridge regression at four regularization strengths and two Extra Trees regression settings.

For each test person, learned models are trained only on other people's later examples, each represented relative to that other person's earlier calibration. Four-fold participant-grouped validation inside those training people selects a candidate by mean absolute relative macro error. The selected model is then fitted without the test person and evaluated on their later meals. Current macro labels, calories, study day and current recipe identity are not input features. Inputs contain glucose curves, differences/distances to known personal calibration curves, baseline and preceding glucose slope. The calibration recipe ordering is fixed and known, matching the prescribed onboarding menu.

Selection minimizes relative error, not the discrete all-three-within-10% hit rate. We therefore report both and include all fixed candidates, rather than claim this selection is optimal for the user's threshold. Predictions are clipped only below zero. No future test-person curve is used to compute calibration statistics.

## Actual results

| Method | Libre: all three within ±10% | Dexcom: all three within ±10% |
|---|---:|---:|
| Calibration median, without glucose | 22/88 (25%) | 21/84 (25%) |
| Closest personal calibration curve | 28/88 (31.8%) | 26/84 (31.0%) |
| Trained model selected inside training data | 0/88 | 0/84 |

None of the six fixed regression settings achieves a meal with all three predictions inside the tolerance. This does not imply zero useful information: for example, carbohydrate alone is within tolerance for 35/88 Libre and 34/84 Dexcom meals under the selected models. Protein and fat are much weaker.

| Method / sensor | Mean absolute carb error | Protein error | Fat error |
|---|---:|---:|---:|
| No-sensor median / either | 10.5 g | 11.0 g | 7.9 g |
| Personal curve / Libre | 14.3 g | 19.0 g | 9.3 g |
| Personal curve / Dexcom | 15.0 g | 17.3 g | 10.1 g |
| Selected regression / Libre | 12.7 g | 16.5 g | 11.1 g |
| Selected regression / Dexcom | 13.1 g | 17.5 g | 11.1 g |

The trained models' average absolute relative errors are approximately 35–36% for carbohydrate, 51–54% for protein and 64–65% for fat. Thus an interpretation of the goal as 10% **average** error is also unmet.

The no-sensor median benefits from three of four recipes sharing the same value of each individual macro. That is precisely why it is an essential control: superficially good macro hit rates can arise from the menu distribution. Personal matching improves the joint hit rate slightly but has worse gram MAE for every macro. Participant-bootstrap intervals for that joint improvement are saved in `comparison_uncertainty.json`; this small sample does not establish a dependable gain.

Example, first evaluated Libre participant's high-fat repeat: recorded 66C/22P/42F, selected-model prediction 51.7C/34.3P/16.8F. This is a miss, despite having that person's earlier high-fat calibration meal. All other predictions are available, not just this example.

## What this establishes and what it does not

The files contain usable labels and repeated responses for a controlled experiment. They do **not** currently supply demonstrated, reliably separable information sufficient for our 10% target under these methods. An average response difference across people does not automatically survive as a repeatable dose signature in an individual.

This is not proof that CGM cannot work or that a better representation cannot improve it. We have not exhausted model families, activity-aware approaches or longer calibration histories. Four prescribed recipes provide limited dose coverage; errors may reflect physiology, sensor variation, source/portion uncertainty, experimental schedule or modeling limitations. This dataset has been explored extensively, so these are retrospective exploratory results, not untouched external validation.

Before claiming a viable all-macro meter, a method must outperform the no-sensor baseline on later meals and meet the error target at an explicitly reported coverage. Producing a numerical output, interpolating assumed physiology or fitting calibration meals exactly does not meet that requirement. The next scientific question is whether additional deployable context or repeated calibration resolves the observed ambiguity; that benefit remains to be measured.

## Outputs and checks

- `all_meal_predictions.csv`: each meal, actual and predicted grams, absolute error and every 10% flag, for all methods.
- `calibration_manifest.csv`: which earlier meals each prediction is allowed to use.
- `model_selection.json`: training-only selection results for each held-out person.
- `summary.json`, `comparison_uncertainty.json`: complete scores and uncertainty.
- `run_manifest.json`: script hashes and package versions.
- `../separability/`: raw curve distances, matching results and a visual confusion table.

Validated that every query follows all its calibration meals, test people do not appear in model training, output meal IDs are unique within each method/sensor, and every saved error and tolerance flag agrees with the actual and predicted grams. Source data were not modified.
