# Can other people's dose responses stabilize personal calibration?

8 September 2026. Tested a fixed population-assisted conversion separately for carbohydrate, fat and protein on the same later controlled-dose meals as the preceding personal calibration experiment. The ±10% objective remains unmet.

## Fixed calculation

Represent each meal by its 37 baseline-subtracted CGM values at five-minute intervals from 0–180 minutes. The difference between the person's first high- and low-dose curves, divided by the known gram difference, defines a personal response direction per gram. Other people's first calibration pairs define an average direction, excluding the evaluated person entirely. The primary rule averages personal and population directions equally, retains the person's own calibration midpoint, and projects the new curve onto that direction to estimate grams. Predictions are clipped at zero only.

The 50/50 weight was fixed before execution. Personal-only and population-only directions are fixed controls, not alternatives selected using query labels. Even the population-only direction uses the person's calibration midpoint. No current meal's macro label enters prediction. Both calibration response windows finish before either evaluation meal.

## Results

| Macro | Primary 50/50 blend: hits | Primary mean error | Full curve, personal-only: hits | Personal-only mean error |
|---|---:|---:|---:|---:|
| Carbohydrate | 6/52 | 20.48 g | 5/52 | 19.25 g |
| Fat | 5/50 | 26.89 g | 7/50 | 17.76 g |
| Protein | 8/56 | 24.95 g | 9/56 | 23.22 g |

All predictions were emitted; none was excluded as uncertain. The population-only direction produced 4/52, 1/50 and 4/56 hits respectively. The primary blend predicted both later carbohydrate doses correctly for one of 26 people, both fat doses for none of 25, and both protein doses for none of 28. Participants overlap across macro experiments.

Using the full curve reduces mean errors relative to the earlier single-feature inverse conversions, but borrowing other people's dose directions does not improve mean error over the full-curve personal-only control for any macro. These descriptive improvements do not establish statistical significance or performance on new meals.

## Why pooling may fail

The median cosine similarity between a person's calibration direction and the other-person average is 0.83 for carbohydrate, 0.59 for protein, and 0.05 for fat. Negative similarity occurs for 3/26, 3/28 and 12/25 people respectively: their observed calibration difference points against the pooled difference. This is especially problematic for a common fat-response direction. These are noisy observed contrasts, not proof that underlying physiology reverses or that a nonlinear model cannot help.

## Interpretation and verification

This is an exploratory controlled-composition diagnostic. The query doses repeat known calibration doses and the other macros are fixed by study design, so even successful results would not validate simultaneous inference of unknown macros in arbitrary meals. Previously inspected feature/data choices mean this is not a pristine final validation. Reserved participants were untouched.

All 474 saved predictions were independently recomputed within 1e-8 absolute tolerance. The script checks exact calibration macro vectors, chronology, unique query keys and equality of query sets with the earlier single-feature experiment. Input and script hashes accompany the results. The tested population stabilization rule is inadequate; it provides no basis for claiming the three macro components can now be combined into a model meeting ±10%.
