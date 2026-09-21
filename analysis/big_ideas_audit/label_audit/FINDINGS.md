# Reference-label audit beneath the meal totals

8 September 2026. Inspected 535 food-item records from the seven development participants whose files have usable headers. Participant 003 remains excluded because its schema is unresolved. Reserved participants 009–016 were not opened.

## Findings

Of 45 records explicitly measured in grams, one contains a substantial mass inconsistency: participant 008's March 14 14:15 `Golden Crust Chicken Patil` records **4 g of food**, **41 g carbohydrate + 30 g protein + 12 g fat = 83 g macros**, and 405 kcal. At least the amount, unit, nutrient values or their interpretation is wrong. The raw file cannot tell us which. This item falls in the person's four-meal onboarding period, not the later test set.

The audit also flagged 45 items whose calories differ by more than 20% from 4C+4P+9F. These are review flags, not proven macro errors: alcohol energy, fiber, specific food-energy factors and rounding can contribute. Examples include records whose description alone does not specify preparation or additions. No corrected values were invented.

Nineteen of the 65 evaluated meals contain at least one component with this discrepancy even though their summed meal totals passed the earlier 20% check. Aggregating components can hide individual inconsistencies. Four-macro quantities were never treated as missing-zero substitutes.

## Do those flags explain the failed model?

Using the existing frozen tree/kernel predictions, without retraining or changing reported overall accuracy:

| Later-meal subset | Meals | Joint successes | Carbohydrate MAE | Protein MAE | Fat MAE |
|---|---:|---:|---:|---:|---:|
| No component calorie flag | 46 | 1 | 33.50 g | 10.36 g | 10.04 g |
| At least one component calorie flag | 19 | 0 | 45.88 g | 21.03 g | 18.30 g |

The flagged subset has larger prediction errors. This is a post-hoc association, not evidence that label errors caused the difference. Meal size, ingredients and other differences can contribute. More importantly, **45 of 46 unflagged meals still fail the target**. Label cleanup alone is not an established solution. Unflagged labels are not independently certified true intake.

The mass-inconsistent onboarding item may have an incorrect unit with correct macros, or incorrect macros, or both. Removing that person's results after seeing errors would be a new analysis choice, not an honest improvement to the original model's accuracy.

## What this changes

For a future claim of ±10% against actual consumed grams, we need traceable component quantities, units, nutrient-source serving bases, actual amount consumed and clearly stated reference uncertainty. The current benchmark measures agreement with logged estimates. A model cannot establish the accuracy of its own training references.

The goal remains unachieved. These findings strengthen the case for better ground-truth collection while preserving the evidence that the current methods fail even on the less-flagged data.

- [All inspected food items and flags](food_item_audit.csv)
- [Review queue with source row numbers](review_queue.csv)
- [Every test prediction joined to label flags](prediction_label_flags.csv)
- [Counts and caveats](summary.json)
