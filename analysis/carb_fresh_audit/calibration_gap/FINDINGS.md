# Feature and personal-calibration diagnosis

Found a concrete design limitation: the 211-meal shared-model training set contained no 24 g meal labels. The initial 24/66 g references were used to normalize glucose features, but their labels were not included as training examples. There were 72 training labels at 66 g. For eight people with later low-carb meals, there was no <=30 g meal in their training examples, despite each having an initial known 24 g calibration.

This is not literal absence of all calibration information: their two reference doses already enter the feature construction. The limitation is that the shared fit does not learn those reference examples directly or preserve their known outputs.

## Fixed-settings addition of the known anchors

Added all 52 initial references to the 211 training examples. All anchors occur before each person’s first training query, and none overlaps a later evaluation meal. Kept gamma 1, ridge 10, all 27 features, and the prior preprocessing statistics fixed. Recomputed the training target mean and kernel coefficients for the 263 examples, then evaluated the same later set. This is a development ablation after prior outcome inspection.

| Measure | Before | After adding anchors |
|---|---:|---:|
| Anchor MAE | 18.56 g | 10.17 g |
| Anchor predictions within 10% | 22/52 | 22/52 |
| Later-meal MAE | 26.88 g | 25.73 g |
| Later meals within tolerance | 4/107 | 4/107 |

Known 24 g anchors were predicted as 53.82–57.65 g before addition and 35.27–49.18 g afterward. The model still fails every one of those known low-dose references. This exposes excessive smoothing relative to the desired personal calibration, rather than establishing that those reference signals cannot be represented.

## Are useful distinctions present in our features?

Compared each later meal with that same person’s earlier training examples plus their two initial anchors. Used the same fixed preprocessing and 27-feature distance; no later labels selected the nearest neighbor. Joined answers only to check agreement afterward.

The nearest historical label is within the target tolerance in 30/107 cases, versus 4/107 predictions from the shared model. This is a descriptive retrieval diagnostic, not a validated replacement model. It reuses exposed outcomes, retains repeated recipe labels, and does not show that all unseen doses can be inferred. Nevertheless, it demonstrates local distinctions that the current shared mapping is not preserving.

Examples where the earlier personal reference has the right amount but the model misses:

| Person | Later true carbs | Nearest earlier carbs | Model prediction | Initial anchor? |
|---|---:|---:|---:|---|
| 3 | 73 | 66 | 52.15 | False |
| 4 | 43 | 39 | 55.41 | False |
| 4 | 24 | 24 | 39.49 | True |
| 5 | 73 | 66 | 63.32 | False |
| 6 | 73 | 66 | 61.92 | False |

## What this supports next

The next targeted change should make the mapping explicitly personal and check its outputs on known calibration meals, rather than merely supply normalized features to a heavily smoothed shared model. Start from the better matching personal references and examine the 77 remaining nearest-neighbor mismatches, including mixed doses and incomplete HR, before treating similarity as a gram conversion. Adding the omitted anchor examples was necessary to test this limitation but was insufficient to solve prediction.

Artifacts: anchor_inputs.csv and anchor_predictions.csv document the initial known references; same_person_neighbors.csv records the nearest three earlier examples per later meal; nearest_history_label_agreement.csv scores their labels; later_results.csv records the fixed-settings ablation. PLAN.json records the intended change. The feature adapter reproduced all 211 prior measured inputs within 1e-8, and all source hashes remained unchanged. No earlier models or datasets were overwritten.
