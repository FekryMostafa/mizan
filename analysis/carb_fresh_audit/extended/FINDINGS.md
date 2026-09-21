# Completed follow-up: onset, premeal state, and longer windows

## Findings

The ±10% carbohydrate goal is unmet. This pass directly tested the timing hypothesis instead of stopping at a proposed experiment.

**The previously highlighted delayed meal does not conceal a large later spike.** Participant 42's later recorded 66 g meal peaks at 173 mg/dL at 195 minutes, from a 140 mg/dL baseline, and returns to 131 by 300 minutes. Calibration peaks near 230 from a baseline near 129. The additional observation captures a delayed but substantially smaller response. Timing alone does not explain the response difference. This corrects the earlier suggestion that the three-hour cutoff might explain most of this miss.

The calibration meal has another positive-calorie event at 183 minutes; therefore extending its curve as if it were an isolated meal would mix responses. The later meal's next logged event is at 477 minutes. Absence of a log does not prove absence of consumption.

## Feature tests

Added premeal glucose baseline, preceding-hour slope and range, recent slope, sustained response onset, onset-aligned positive areas, observed aligned duration, endpoint level and slope, negative area, and total area. Onset is the first of three consecutive five-minute values at least 10 mg/dL above the premeal baseline; the threshold is a fixed heuristic. Areas are truncated at the observation endpoint and observed duration is supplied. These are candidate features, not estimates of intestinal absorption.

For all 26 people, retained the same 52 later meals, personal two-meal calibration, and nested person-held-out evaluation. Four feature families each test linear/quadratic ridge with penalties 1/10/100. Inner selection maximizes ±10% hits with MAE tie-breaker. Population preprocessing excludes the evaluated person; their own earlier calibration is permitted. Premeal context is supplied as absolute values standardized on training rows, not divided by a dose contrast.

| Fixed feature family, parameters selected inside training folds | Hits / 52 | MAE |
|---|---:|---:|
| Original 12 features | 9 | 15.20 g |
| Original + timing/response-end features | 7 | 23.48 g |
| Original + premeal context | 9 | 17.43 g |
| All features | 2 | 20.92 g |

Selecting across all 24 candidates inside the training folds gives 4/52 hits and 22.96 g MAE. Thus feature-family selection itself generalizes poorly here. The original feature extraction reproduces exactly within numerical tolerance. Adding these particular features did not improve accuracy; this is not evidence that all timing/state models are useless.

## Longer-window comparison

All four comparison meals have valid Libre coverage and no intervening logged food for 180 minutes in 26 people, 240 minutes in five, and 300 minutes in one. On the same ten later meals from those five people:

| Fixed personal scalar conversion | Three-hour hits; MAE | Four-hour hits; MAE |
|---|---|---|
| Peak | 1/10; 32.35 g | 2/10; 27.97 g |
| Total positive area | 0/10; 41.67 g | 0/10; 49.63 g |
| Onset-aligned 120-minute area | 0/10; 27.95 g | 0/10; 24.67 g |

This small matched diagnostic provides no evidence for ±10% recovery by extending these features to four hours. It cannot exclude benefit from longer observations in a larger, better-controlled dataset. A five-hour population model was not fitted to one person.

## Scope and verification

Recorded doses remain 24/66 g with matched other macros; previously inspected development data, not unseen-dose validation. No dose snapping, no selective exclusion of errors, and no reserved participants accessed. Saved coverage, sampled traces, feature definitions, feature matrices, inner selection scores, per-candidate and selected predictions, and matched-window predictions. Independently recomputed scoring and confirmed the original twelve features reproduce prior values.

The physiological cause of the remaining between-meal response changes is unresolved. These results justify retaining the earlier simpler candidate rather than promoting the new features. They do not justify claiming that consumed carbs must be uniquely recoverable from the available glucose observations.
