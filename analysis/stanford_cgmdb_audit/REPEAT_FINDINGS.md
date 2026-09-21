# Stanford processing audit and repeated-calibration diagnostic

Author code inspected at commit 390646019243df30e5c7490d797946778411cabb in https://github.com/mikeaalv/cgm_meal_manuscript . The preprocessing script sorts sessions by participant and local datetime before assigning repeat numbers within participant/condition. Therefore repeat order is meaningful within a condition, but cannot establish cross-condition chronology from the public table, which omits dates. The original script retains dates before public release.

The R preprocessing fits a smoothing spline independently to each session using npreg::ss, all.knots=TRUE, m=3, method=REML, and predicts a 40-point grid from -25 to 170 minutes. It excludes sessions missing either boundary or with a recorded gap greater than 30 minutes. This is retrospective smoothing, not a causal wearable signal pipeline; the smoothed premeal baseline can be influenced by later points. The preprocessing scripts read original records and manual correction files from local paths; those inputs were not reproduced in this audit.

Supplementary Table S6 supplies the seven base-meal nutrition profiles, extracted to base_meal_nutrients.csv. Rice is listed as 49.983 g carbohydrate, 4.773 g protein and 0.497 g fat. S6 does not supply complete preload composition. The article gives nominal added doses of 15 g fat from creme fraiche and 10 g protein from egg white; neither should be treated as a chemically pure nutrient or a full meal label.

## Fixed diagnostic

Compared calibration using repeat 1 versus repeats 1 and 2 averaged, then evaluated the identical repeats numbered 3 and higher. Each macro is evaluated separately against rice alone. Baseline is the median at -25, -20 and -15 minutes, preceding the intended -10 minute preload. The full 0–170 minute curve is projected onto the difference between calibration conditions to estimate the nominal added dose. No feature/parameter search was performed, and no query belongs to calibration.

Only XB6 meets the fixed requirement to have repeats 1 and 2 for all needed conditions. XB19 has three rice sessions but they are numbered 2, 3 and 4; repeat 1 is absent. Earlier inventory counts were correct, but they did not guarantee the availability of those specific calibration repeat identifiers.

| Added nutrient | Calibration repeats per condition | Test sessions | Within ±10% | Mean absolute error |
|---|---:|---:|---:|---:|
| Fat | 1 | 5 | 0/5 | 7.13 g |
| Fat | 2 | 5 | 0/5 | 6.01 g |
| Protein | 1 | 5 | 0/5 | 5.51 g |
| Protein | 2 | 5 | 1/5 | 6.11 g |

Each row includes three supplemented sessions and two rice-only controls. With two calibration repetitions, the three nominal 15 g fat doses were estimated as 7.91, 5.64 and 5.13 g; the three nominal 10 g protein doses as 9.16, 0 and 5.18 g. Fat's aggregate error reduction comes from the controls: error on supplemented sessions worsens from 7.81 to 8.77 g. Protein's supplemented-session error improves slightly from 5.36 to 5.22 g but control error worsens. At zero added dose, a relative ±10% criterion requires an exact zero estimate; positive-dose results are reported separately to make that limitation visible.

All 20 saved error values and success flags were recomputed, and matched query keys were verified across calibration counts. This tiny, retrospective, nominal-added-dose experiment does not validate total macro grams, unseen portions, chronological onboarding or ±10% generalization. It also does not show that additional calibration universally fails. It provides an independent-data example where this fixed two-repeat averaging rule is insufficient.
