# If two macros were known, could the model recover the third?

Completed a deliberately nondeployable diagnostic. For each unknown macro separately, the model was supplied the actual recorded amounts of the other two macros. It was trained on CGMacros, personally adjusted using four earlier BIG IDEAs meals, and evaluated on the same 65 later development meals. These inputs would not be available to the proposed wearable. Reserved participants remained unaccessed.

Compared the known-other-macros model with the same fixed tree algorithm also receiving glucose. Each target uses a separate model; their results must not be combined into an all-three wearable accuracy result.

| Unknown macro | Known other macros: MAE | Also given glucose: MAE | Within 10% with glucose |
|---|---:|---:|---:|
| Carbohydrate | 39.55 g | 38.07 g | 6/65 |
| Protein | 13.20 g | 13.14 g | 6/65 |
| Fat | 9.95 g | 10.83 g | 5/65 |

Supplying the two other true macros did not make this fixed method reliably recover the remaining macro. In particular, adding glucose worsened average fat error relative to using the other macros alone, while increasing fat's within-tolerance count from 3 to 5. Average error and tolerance hit rate measure different aspects of performance.

The difficulty is therefore not resolved merely by removing uncertainty about the other two macros in this model. This does **not** prove biological impossibility, establish a theoretical accuracy bound, or rule out a better conditional model. Population differences, sparse dose coverage, reference-label quality and model misspecification remain possible explanations.

All 390 predictions were checked for unique keys, identical query counts, recomputed tolerance flags and exclusion of the target macro from the supplied query-label columns. Training and personal correction follow the previously checked source/target and chronological split. Hyperparameters were fixed rather than selected from these outcomes. These are exploratory diagnostic results on development participants.

- [Individual conditional predictions and exactly which labels were supplied](predictions.csv)
- [Summary](summary.csv)
- [Explicit nondeployable-run manifest](run_manifest.json)
