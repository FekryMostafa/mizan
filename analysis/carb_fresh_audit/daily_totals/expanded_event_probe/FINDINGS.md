# Expanded individual-meal training inside CGMacros

Audited843 candidate events and retained820 from34 people with complete301-minute Libre windows from−60 through+240 minutes. Excluded incomplete windows and any training window too close to the first later day of an evaluation participant. All189 evaluation events and44 daily outcomes remained unchanged. The additional data came entirely from CGMacros, including valid individual meals from days that were unsuitable as complete daily training targets.

Applied the same fixed exact-event models without tuning on later outcomes:

| Inputs, with recorded event times supplied | Daily±10% hits | MAPE | MAE |
|---|---:|---:|---:|
| Clock only |14/44|19.73%|40.26 g|
| CGM only |7/44|24.15%|49.08 g|
| CGM plus clock |9/44|21.52%|46.69 g|

The CGM-plus-clock MAPE improved from22.79% with267 training events to21.52%, but tolerance hits fell from12 to9. Clock-only remained stronger on these outcomes. No arm reaches10%, and these are diagnostics with known event timing, not passive wearable accuracy.

P13's147 g event was predicted37.10 g by expanded CGM-plus-clock, versus44.97 g previously. The larger pool still has only8 events≥120 g. More ordinary meals did not resolve this high-dose case.

Training and evaluation event keys are disjoint; evaluation-participant training windows end before the earliest later midnight minus1h, leaving separation from query premeal windows. Other participants are training-only. Recorded targets are unchanged, source participant hashes match, and serialized models reproduce predictions when query carb labels are replaced. Clock-only can exploit meal schedules and supplied event counts; its results are not evidence that glucose encodes grams.

This experiment establishes that simply adding the available valid meals is insufficient under the tested conversion. It leaves a specific representation gap: these event models have used only glucose and clock features, whereas aligned activity/heart-rate trajectories may distinguish some responses that daily activity averages obscure. That can be tested within the same expanded training pool without altering the44 daily outcomes or supplying food composition.
