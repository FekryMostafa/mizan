# Nonlinear check of the added wrist signals

8 September 2026. Tested a fixed ExtraTrees population model (200 trees, minimum leaf size 5, seed 20260908) with the same personal residual-kernel correction used in the preceding linear comparison. Settings were specified before execution; no search or selection based on these outcomes was performed.

The same 65 later meals, five evaluated people, four earlier calibration meals, and other-person BIG IDEAs population training were used. EDA and temperature features were reused unchanged. Reserved participants stayed unopened. This remains exploratory development on repeatedly examined participants, not independent validation.

| Inputs | All three within 10% | Carb MAE | Protein MAE | Fat MAE |
|---|---:|---:|---:|---:|
| Glucose | 0/65 | 40.04 g | 14.95 g | 13.26 g |
| EDA + temperature | 0/65 | 40.18 g | 15.23 g | 13.40 g |
| Glucose + EDA + temperature | 0/65 | 42.15 g | 14.72 g | 12.94 g |
| Personal median without sensors | 0/65 | 41.18 g | 15.56 g | 13.74 g |

The nonlinear combined model is worse on all three MAEs than the previous linear combined model (39.41 / 14.38 / 12.00 g). Within the nonlinear comparison, adding wrist signals slightly improved protein/fat error and worsened carbohydrate error. None meets the goal. This rules out the narrow explanation that simply replacing the linear population estimator with this standard nonlinear estimator rescues these feature summaries. It does not establish a biological limit or rule out every possible representation/model.

Verified all 260 stored predictions independently for finite nonnegative values and correct tolerance flags. Confirmed exactly identical calibration, population-person and query splits to the linear experiment; unchanged input-feature hashes; and reproduced the no-sensor control numerically. The model script and input hashes are saved in run_manifest.json.

The same limitations remain: sparse personal dose coverage, estimated nutrient labels, missing wrist segments in 11 of 65 postmeal windows, and feature summaries that do not capture every fast signal characteristic. The target is unachieved; these results do not support buying sensors on a promise of 10% accuracy.

- [Predictions](predictions.csv)
- [Summary](summary.json)
- [Verification](verification.json)
- [Split manifest](split_manifest.json)
