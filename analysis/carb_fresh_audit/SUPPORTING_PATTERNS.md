# Supporting Libre carbohydrate patterns

Extracted 12 descriptive features from 104 controlled-meal curves: 26 people, two known calibration doses and two later repeated doses. This is exploratory feature analysis of existing development data. It is not independent model validation.

| Feature | Larger for 66 g than 24 g during calibration | Larger on later pair |
|---|---:|---:|
| Positive area 60–120 min | 26/26 | 23/26 |
| Peak rise | 24/26 | 23/26 |
| Positive-area time centroid | 23/26 | 23/26 |

The centroid is the time-weighted average of the positive glucose response: a larger value means more response occurs later. All features use Libre alone. Other recorded macros match by design. No per-person feature sign was selected from query labels.

The median within-person later/calibration difference ratio is 0.63 for middle area and 0.42 for peak. Thus dose ordering is fairly persistent, while the observed difference between low and high responses often shrinks. This helps explain why a fixed calibration scale underestimates many high-dose meals. It does not establish a biological cause or justify multiplying all future predictions by a correction factor. Study order, measurement drift, meal-label fidelity and changing personal state remain possible explanations.

Simple scalar inversions demonstrate the distinction: middle area gives 11/52 predictions within ±10%, with mean absolute error 20.87 g. Late area gives 15/52 but a much worse 50.32 g mean error because some calibration differences are near zero. Therefore selecting the feature with most hits alone is misleading. Zero calibration contrasts are abstentions counted as failures; MAE excludes undefined predictions, so cross-feature MAE needs that qualification. All counts are reported in feature_patterns.csv.

Candidate representation for a subsequent model: middle response area (magnitude), peak (amplitude), and time centroid (timing). Their combination has not been tested here and correlated features need not provide independent information. The central unresolved prediction problem is estimating changing personal response scale from information available before or during the meal, without using the meal's true dose.

Verified 104 unique meal keys and independently recomputed every saved ±10% flag. Source extraction and hashes are documented in the preceding audit. No reserved participant records were accessed. Single-feature predictions are diagnostics, not a deployment recommendation.
