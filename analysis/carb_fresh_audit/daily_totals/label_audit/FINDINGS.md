# Daily food-label audit

No supported label correction was found. All original daily outcomes and prediction scores remain unchanged.

## Exact duplication and source photos

Audited all 1,706 meal records and resolved 1,644 referenced photos from the original archive. The 44 evaluation days contain 189 meal records, with 181 available referenced photos. None of those evaluation meals share an exact SHA-256 photo-file hash with another meal record anywhere in the dataset. No evaluation records share the same participant, timestamp and carbohydrate/protein/fat vector. These checks rule out those exact duplication mechanisms, not visually similar re-encoded photos or repeated logging at different timestamps.

The ten largest percentage-error days of the delayed linear model, plus P4's 513 g day, were traced back to their meal rows. Their carbohydrate sums match the evaluated totals. P4 has nine entries, eight distinct referenced photos, 5,206 reported kcal and 5,136 kcal calculated from its macro totals. There is no numerical justification to delete its multiple dinner entries just because they are unusually large.

## Calorie–macro discrepancies

Six evaluation meals differ by more than 250 kcal between the reported calorie field and the conventional 4C+4P+9F calculation. This is an exploratory audit threshold, not a validated exclusion rule. The largest positive discrepancies are P8's dinner (2,015 reported versus 990 calculated), P17's late meal (1,740 versus 767), and P41's meal (842 versus 259). P2's dinner goes in the opposite direction (382 versus 817).

These differences warrant source clarification. They do not identify which nutrient or calorie entry is wrong. The simple energy calculation also does not account for all sources of energy or label conventions. It cannot be used to infer corrected carb grams.

Visually inspected the original P8 dinner photo: a restaurant meal with rice, topped/stuffed food, salad, chips and a drink. The image cannot establish portion weights, exact ingredients, consumption or a corrected nutrient total. Visually inspected P4's 18:19 photo: pasta with shrimp, a wrapped food item and drinks visible. Its image likewise does not verify the recorded 124 g carbs, 141 g fat and 116 g protein. The photo evidence was used only for label inspection, not as a model input.

## Does this explain the error rate?

No, not in the available diagnostic. Even if the six flagged days were set aside, the already-fitted delayed model would get only 13/38 remaining days within ±10%, with 19.47% MAPE. The flagged six actually had lower mean error (15.52%). This is a post-hoc sensitivity analysis, not a cleaned benchmark or permission to exclude records.

The full retained result remains 15/44 within ±10%, MAPE 18.94%. The ±10% daily goal has not been met.

## Source protocol and remaining gap

The local full CGMacros paper, Methods, states that participants logged meals in MyFitnessPal, photographed food before and after, received designed shake breakfasts and Chipotle lunches, and chose their own dinners. The study provides a useful recorded-intake benchmark; the material inspected here does not independently establish every complete day's true intake to ±10%.

No correction can be justified from exact-file hashes, arithmetic or photos alone. The current experiments neither demonstrate accurate daily inference nor establish physical impossibility. The next useful evidence would be either source clarification of these meal entries or an independent, sufficiently long CGM dataset with verified full-day carbohydrate totals. Repeatedly retuning on the same 44 exposed days would not independently validate the target.
