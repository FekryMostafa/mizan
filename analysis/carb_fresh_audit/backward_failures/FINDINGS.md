# Work backward through the ten largest carbohydrate errors

Selected the ten largest errors from the original 52-query model before running these diagnostics. This is retrospective failure analysis, not a new accuracy validation. Each candidate prediction uses only personal meals whose three-hour response finished before the query. Choosing the best candidate per query DOES use its true answer; those choices cannot be deployed as an algorithm.

## Raw records first

Directly inspected all 45 CGMacros CSV files: 1,706 meal records (436 breakfasts, 435 lunches, 492 dinners, 343 snacks under three spellings). Paper Table 3 identifies breakfasts as protein shakes; lunches are Chipotle, dinners self-selected. Individual CSV rows provide meal category, macro estimates, consumption percentage and image path, not necessarily an ingredient-level food description. No images were inspected in this pass.

The recent experiment restricted calibration to two shakes: 24 or 66 g carbohydrate, 22 g protein, 10.5 g fat (paper rounds fat to 11). This was our design restriction. The ten failures have 9–28 additional-candidate historical meals INCLUDING the two anchors, after requiring full consumption, a complete sampled three-hour Libre curve, >=95% minute coverage, no recorded subsequent food inside three hours, and no samples at the lower sensor bound. These filters do not establish correct timestamps, labels, or absence of earlier-meal carryover. Other history recipes include different protein and fat amounts. Two raw files lack the consumption column; those rows are not silently assumed fully consumed.

Raw peak extraction exactly reproduces all 104 prior calibration/query peaks. No future meals or query macros enter distance calculations. History macros are supervised reference labels. Current test has only 24/66 g query labels, so exact-dose retrieval benefits from repeated recipes and does not demonstrate interpolation to unseen doses.

## Ten individual cases

| Person / true carbs | Original estimate | Backward candidate | What the raw history says and what undermines it |
|---|---:|---:|---|
| 27 / 66 g | 0.0 | 67.6 using three neighbors with glucose/context | Query rises only 8.3 mg/dL above baseline. Selected historical meals contain 119, 16 and 66 g. Their weighted average happens to fit. This is NOT a coherent recovery of a 66 g signature. Rule hits only 6/52 overall. |
| 32 / 66 g | 27.1 | 66.0 using glucose/context neighbor | Earlier 66 g high-fat shake has a short response: middle-hour area 14 versus query 80. But 73 g and 24 g historical meals are nearly tied neighbors. Query HR is entirely missing, so this cannot be called an HR correction. Rule hits 16/52. |
| 35 / 24 g | 60.4 | 24.0 using response duration | Both low calibration and query stay above baseline for the entire 180-minute window. HOWEVER the later 66 g query also lasts 180 minutes and this rule predicts 24 for that meal too. Reject duration alone as the solution. Query peak rise 156.9 versus low calibration 73.3; amplitude neighbors are 66/66/73 g. |
| 5 / 24 g | 54.7 | 33.0 using nearest peak timing; still fails | Query peak rise 115.2 at 115 minutes; nearest timing meals contain 33 and 36 g but peaks only 36 and 51. No tested correction reaches 21.6–26.4 g. Matching timing does not explain changed amplitude. |
| 36 / 24 g | 54.2 | 24.0 using glucose/context neighbor | Context changes nearest historical reference to the actual earlier 24 g shake, despite middle-hour area changing from 389 to 4,179. But two 66 g references are almost equally close. A candidate for context-sensitive reference choice, not a demonstrated physiological correction. Rule hits 16/52 overall. |
| 38 / 24 g | 53.1 | 23.4 using middle-hour area | Query middle-hour area 2,084 closely matches the earlier 24 g meal's 2,123; the high anchor is 5,002. Peak increased from 45.4 to 70.7, so weighting peak and tail can obscure a stable middle segment. This is a concrete locally useful feature. Same rule hits only 11/52 overall. |
| 2 / 66 g | 39.5 | 66.0 using peak timing | Closest timing is an earlier high-fat 66 g shake; next timing matches contain 26 and 19 g. Timing alone provides weak dose separation. Rule hits 13/52. |
| 38 / 66 g | 40.5 | 66.0 using amplitude/history neighbor | Two closest amplitude references both contain 66 g; a 24 g reference is third and fairly close. Broad historical reference matching avoids the previous downward conversion for this example. Rule hits 23/52 overall. |
| 49 / 66 g | 41.1 | 66.0 using amplitude/history neighbor | Closest reference is an earlier high-fat 66 g shake, peak 135 versus query 106. A 24 g meal is the second reference. High prior HR does not tell us an exact correction; different earlier recipes provide another useful comparator. |
| 41 / 66 g | 43.3 | 68.6 averaging three amplitude neighbors | Three nearest records contain 73, 66 and 66 g, with middle-hour areas 4,420, 5,669 and 5,124 versus query 5,970. This is a more internally consistent neighborhood. Query HR is missing, so the clue comes from glucose history. Rule hits 8/52 overall. |

Areas are positive baseline-relative glucose area in mg/dL·min. “Context” uses baseline glucose plus premeal and three hourly HR/activity means, scaled from that person's earlier eligible history. Missing query context dimensions are excluded, not interpreted as zero/rest. Historical missing values use historical medians. These simple metrics have not had their weights optimized. The metric named `shape` in the files is ONLY peak time, not complete curve shape.

## Cross-case checks

Same single rule applied to all 52 previously inspected queries:

- Nearest historical amplitude (peak + three hourly areas): 23/52 within 10%; MAE 16.50 g. Hits 7/26 low-carb and 16/26 high-carb queries.
- Nearest historical amplitude plus context: 16/52; MAE 25.21 g.
- Original model: 9/52; MAE 15.20 g.
- Most common carbohydrate label in eligible personal history, ignoring glucose: 22/52; MAE 24.31 g.
- Always predicting 66 g, ignoring everything: 26/52; MAE 21 g. This is a dose-composition sanity check, not a proposed product.

Thus 23 versus 9 hits is not sufficient evidence that history matching solved inference. Its MAE beats the simple label baselines but not the original model, and its hit rate is below the constant-66 sanity check. The retrospective 9/10 figure chooses a different rule with knowledge of each answer; it must never be reported as predictive accuracy.

## Pattern supported by this audit

There are useful local comparisons the original conversion misses, especially a stable curve segment (P38 low) or several earlier curves with similar carbohydrate labels (P41 high). Other apparently successful corrections are demonstrably unreliable: duration saturation (P35), conflicting neighboring doses (P27/P32/P36), or timing matches that do not preserve amplitude (P5).

The missing algorithmic step is selecting a trustworthy historical reference or segment WITHOUT seeing the target grams. This audit gives specific positive and negative examples for that selector, not proof that such a selector will achieve 10%. A defensible next test would select rules from earlier within-person prediction errors, account for label disagreement among nearby references, and evaluate on later meals without choosing rules from those later answers. Broader query carbohydrate doses are also needed so repeated 66 g labels cannot masquerade as precise gram inference.

Reproduction: run audit.py with the existing Mizan lipid_meals virtualenv. Candidate predictions, all neighbors, raw inventory, historical eligibility and selected ten cases are saved alongside this report. Baselines were calculated from the same saved raw history audit and are in baselines.csv.
