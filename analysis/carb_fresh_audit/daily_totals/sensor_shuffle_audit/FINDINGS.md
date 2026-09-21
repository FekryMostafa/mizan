# Does matching sensors to the correct day matter?

The observed fixed passive ensemble performed better than 99 of 100 within-person sensor shuffles. This supports investigating useful day-specific information in the combined sensor inputs, rather than interpreting every failed model as evidence of impossibility. It does not establish 10% accuracy or isolate glucose from activity.

| Condition | Daily MAPE |
|---|---:|
| Correctly paired sensor days | 18.395% |
| Personal mean intake, no daily sensor adjustment | 20.575% |
| Shuffled sensor days, median of 100 runs | 21.814% |
| Best shuffled run | 18.361% |
| Worst shuffled run | 25.204% |

The observed improvement over personal mean is 2.180 percentage points; the required improvement to reach 10% is still 8.395 points. The observed result has 16/44 days within 10%, versus 14/44 for personal mean. An average percentage error below a target would also not imply every day meets it.

The same 31-model uniform ensemble was refitted in every run. Complete feature rows were shuffled within each participant independently in the 64 training days and 44 later days. Labels, participant identities, dates, splits, and within-row feature correlations were preserved. This breaks the link between a day's labels and its sensor observations while retaining participant-level patterns. No features or hyperparameters were selected in this audit.

The observed prediction reproduced the saved ensemble within 1e-8 g. All 100 runs retained all 44 outcomes and preserved label/key columns exactly. The control includes glucose, heart rate, and activity features together; attribution requires separate controls.

This is a descriptive negative control on repeatedly inspected development data. Within-person temporal dependence, few days per person, and prior model exploration prevent treating 1/100 as a formal prospective significance claim. The best shuffled run is not a usable model improvement: it deliberately mismatches sensor days and is selected using outcomes. Source records and prior predictions were preserved.
