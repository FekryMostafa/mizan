# Fat prediction: timing and response scale sensitivity

The ±10% fat target is not met. This diagnostic tests a specific explanation for earlier failure: a personal glucose response may change timing and scale between meals.

Each of 25 people supplies their first low-fat and high-fat controlled meals for calibration. Two later meals per person are evaluated. Other macros match in the calibration pair. The empirical forward response interpolates the two calibration curves across candidate fat doses from 0 to 100 g. The flexible version also searches response gains and time scales from 0.8 to 1.2. These bounds are sensitivity assumptions, not measured physiological distributions. Query fat labels are used only after prediction for scoring.

| Method | Within ±10% | Mean absolute fat error | Mean best glucose RMSE |
|---|---:|---:|---:|
| Fixed personal curve | 7/50 | 17.75 g | 24.76 mg/dL |
| Variable timing and scale | 8/50 | 17.06 g | 16.71 mg/dL |

Neither method predicts both later doses within ±10% for any participant. Improving glucose fit substantially therefore does not translate into accurate fat recovery here. This rejects this particular timing/scale correction as sufficient; it does not establish that CGM fat inference is impossible.

The median span of candidate doses whose fitted RMSE is within 1 mg/dL of the best fit is 12.63 g for the flexible model. This is an arbitrary sensitivity diagnostic, NOT a confidence interval, noise estimate, or fundamental identifiability bound. Endpoint clipping is used when time scaling requests unobserved curve times; no physiological extrapolation is claimed.

These are previously inspected development records, known dose repeats, three-hour response windows, and a deliberately simple empirical model. They do not validate arbitrary meals, five-hour fat effects, or new fat doses. Reserved participants remain untouched. Chronology and uniqueness assertions ran; saved scoring was checked independently. Inputs and script hashes are in manifest.json. All per-meal predictions and per-dose fit profiles are saved alongside this report.

## Literature implication

[Bell et al.](https://pubmed.ncbi.nlm.nih.gov/31455688/) report early suppression and late elevation as dietary fat increases with carbohydrate held fixed in type 1 diabetes. This supports studying timing but does not supply a validated inverse model for healthy users. [Yamaguchi et al.](https://pubmed.ncbi.nlm.nih.gov/30282861/) report no significant glucose effect in healthy adults given meals with 0/10/20/40 g butter (butter mass, not fat mass). That null finding does not prove identical individual curves. Abstracts were checked in this pass; full methods were not reviewed here.

The next unresolved question is whether independently constrained absorption and glucose regulation parameters improve held-out fat estimates. Allowing them to vary freely to improve curve fit is insufficient evidence. A mechanistic candidate must specify how fat grams enter its equations and how personal calibration determines that mapping, without using the unknown meal's macro labels.
