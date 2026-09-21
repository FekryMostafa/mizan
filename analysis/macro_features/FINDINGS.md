# Separate-macro CGM feature investigation

8 September 2026. Following the user's direction, this analysis examines signal features separately for carbohydrate, fat and protein before choosing or combining prediction algorithms. No new model accuracy claim is made.

Re-extracted five-minute CGM grids from original records for the existing 652 eligible CGMacros meals (34 people) and 86 BIG IDEAs development meals (six people, one with only one eligible record). All earlier cached 15-minute features reproduced within 1e-6 absolute tolerance. This is additional feature resolution, not additional independent observations: the released CGMacros grid itself is interpolated. BIG IDEAs interpolation remains bounded by 601-second source gaps. Reserved participants were not accessed. Flat and negative responses remain included.

Eighteen features cover baseline, premeal slope, peak height/time, trough, end change, variability, maximum rise/fall slopes, negative area, tail, late-versus-early peak, and signed/positive areas in each of three hours. No label-derived features are supplied to any proposed wearable.

## First evidence for each macro

The table gives partial rank correlations after removing person indicators and ranked amounts of the other two macros by linear residualization. These known labels are used **only for explanatory diagnostics**, not deployable prediction. Adjusting recorded covariates does not establish causality or fully remove meal-composition confounding.

| Macro | Source-selected feature | CGMacros association | BIG IDEAs development association |
|---|---|---:|---:|
| Carbs | Peak rise above baseline | +0.430 | +0.478 |
| Carbs | Positive area, minutes 60–120 | +0.417 | +0.447 |
| Fat | Maximum five-minute rise slope | -0.240 | -0.120 |
| Fat | Response variability | -0.226 | -0.033 |
| Protein | Response variability | -0.215 | -0.198 |
| Protein | Peak rise above baseline | -0.144 | -0.088 |

Carbohydrate-related rise and area are the clearest candidates in this feature set. The same-direction carbohydrate peak association appears in 31/34 source people and 4/5 development people with enough data; middle-area direction agrees in 33/34 and 4/5. Maximum-rise slope has the source fat direction in 29/34 and 4/5 people. Protein variability has the source direction in 29/34 and 4/5. These sign counts are descriptive, not significance tests; tiny within-person datasets and correlated features limit interpretation.

Fat and protein associate with overlapping shape features, and their effects are weaker than carbohydrate's in this analysis. That motivates testing feature specificity rather than assuming each curve feature belongs uniquely to a macro. A correlation of 0.43 is not 43% accuracy and does not specify grams-per-unit conversion or a 10% error guarantee.

## Repeat variability

Grouping the same person's meals by exact recorded C/P/F vectors yields 119 repeated groups and 121 pairs in CGMacros, and 10 groups/27 pairs in BIG IDEAs development. Median absolute peak-rise differences within those pairs are 20.1 and 13.0 mg/dL, respectively. Median maximum-rise-slope differences are 0.88 and 0.66 mg/dL/min. These groups match recorded macro vectors, not necessarily ingredients, fiber, preparation or actual intake. Pairs sharing a meal are not independent samples. Variability therefore cannot be attributed solely to biological noise or used as an irreducible accuracy bound.

## Next evaluation boundary

Use these diagnostics to define separate candidate representations for each macro. Candidate selection must happen inside training/development splits; query labels cannot select the winning extractor, calibrator or algorithm. Compare each macro against a personal no-sensor reference, report its individual within-10% rate and gram errors, then join independently generated predictions by the same meal ID to measure joint success. Do not combine the best result for each individual test meal after looking at its true label. The final reserved cohort remains separate until a configuration is frozen.

All current associations use previously inspected development data. No macro has been perfected, and no combined predictor is validated by this feature audit. The next actual gram experiment should start with the better-supported carbohydrate features while retaining separate fat/protein diagnostics.

- [Extracted features for every meal](features.csv)
- [All associations, with/without other-macro adjustment](associations.csv)
- [Person-level direction checks](person_consistency.csv)
- [Repeated-vector feature differences](repeat_variability.csv)
- [Extraction provenance](manifest.json)
