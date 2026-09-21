# Does each person's macro calibration repeat?

8 September 2026. Tested a direct two-point feature-to-gram conversion separately for each macro, using the existing eligible CGMacros breakfasts. Other recorded macros are identical within each comparison, recorded fiber is zero, and recorded consumption is 100%. This reduces composition differences but does not establish identical ingredients or control day-to-day physiology.

Each person's first low-dose and first high-dose meals calibrate an affine conversion. The first later low-dose and first later high-dose meals are queries; both calibration response windows must finish before either query. Feature choices were fixed from the preceding exploratory audit, not selected from these results. Negative predicted grams are clipped to zero; no upper clipping or special rules conceal unstable calibration slopes. This is a simple diagnostic of feature repeatability, not the strongest possible predictor.

| Target | Low / high dose | Feature | People | Later meals within ±10% | Mean absolute error |
|---|---|---|---:|---:|---:|
| Carbohydrate | 24 / 66 g | Peak rise | 26 | 3/52 | 28.66 g |
| Fat | 10.5 / 42 g | Maximum five-minute rise slope | 25 | 3/50 | 34.12 g |
| Protein | 22 / 66 g | Response variability | 28 | 4/56 | 44.23 g |

The same person can appear in all three rows; reference meals can be shared across macro experiments. These are not 79 independent people. Query doses repeat known reference doses, so success would not establish unseen-dose estimation. No reserved BIG IDEAs records were accessed.

## What changes between calibration and repeat?

The sign of the high-minus-low feature difference repeats for 20/26 carbohydrate comparisons, 15/25 fat comparisons, and 24/28 protein comparisons. Thus some directional information survives, particularly for protein in this narrow controlled comparison. The size of that difference is much less stable:

| Macro | Median later/calibration feature contrast | People with contrast ratio 0.8–1.2 | Median absolute midpoint shift, expressed through the original gram conversion |
|---|---:|---:|---:|
| Carbohydrate | 0.41 | 4/26 | 16.36 g |
| Fat | 0.29 | 4/25 | 14.29 g |
| Protein | 0.49 | 1/28 | 24.82 g |

The ratio retains its sign; a negative value indicates reversal. These descriptive ratios are not biological sensitivity estimates. Midpoint shift measures movement of the center of the two feature values; it is distinct from the change in their separation. Both can break a fixed gram conversion. The 0.8–1.2 contrast interval is diagnostic and is not equivalent to the ±10% gram target.

No person had both later doses predicted within ±10% for any of the three selected features. Median absolute gram errors were 16.24 g carbohydrate, 18.59 g fat and 22.00 g protein. Mean errors are larger because dividing by small calibration contrasts produces extreme estimates; maximum errors reached 235.96, 388.50 and 407.29 g respectively. A calibration midpoint without CGM had lower mean errors of 21, 15.75 and 22 g, though zero within-10% hits for these deliberately separated doses.

## Consequence for the design

One low-dose and one high-dose example per person do not establish a stable grams-per-feature conversion for these extractors. The evidence supports retaining personalization as a hypothesis while rejecting this specific calibration formula as adequate. Regularizing the slope could limit numerical blowups, but it would not by itself show that a physiological feature identifies grams. Repeated calibration at each dose, assessed chronologically, is the next question; any useful rule still needs validation on new amounts and new meal compositions before supporting the requested model.

Verification independently recomputed all 158 predictions and checked all 79 calibration/query temporal boundaries. Saved availability counts document missing repeat pairs; no feature-sign exclusion was applied. Results remain exploratory because the feature choices were informed by previously inspected data. These failures do not prove that every CGM algorithm is impossible, and they do not meet the user's ±10% objective.
