# Effect of personal calibration history

More personal calibration improved the fixed passive ensemble on this cohort. This is a positive result for onboarding, but the available history does not reach 10% daily error.

| Personal calibration retained | Ensemble MAPE | Days within 10% | Personal mean alone MAPE |
|---|---:|---:|---:|
| First day | 24.66% | 11/44 | 31.04% |
| First two days | 20.97% | 16/44 | 23.36% |
| First three, or all if fewer | 19.26% | 15/44 | 22.56% |
| All available: 2–5 days | 18.40% | 16/44 | 20.58% |

All 16 participants have two calibration days. Fifteen have at least three. The full pool has one person with two days, four with three, five with four, and six with five. Thus the third row is not exactly three days for everyone, and the final row is not five days for everyone.

Each participant was evaluated on exactly the same later days at every level. Other participants' original allowed training rows were retained, and only the query participant's history was reduced. The 31-model uniform ensemble and every hyperparameter stayed fixed. Personal history starts with the earliest allowed days and expands chronologically. No query labels or food timestamps are inputs. Source data and previous models were preserved.

The full-history result reproduces the prior ensemble within 1e-8 g. Every query's personal training sensor window ends before its evaluation begins. All four levels retain the same 44 outcomes. Replacing query labels with a sentinel leaves predictions unchanged at every level.

This demonstrates that limited personal history is a relevant constraint for this algorithm. It does not show how many additional days would be sufficient or guarantee that the trend continues to 10%. Much of the improvement also appears in the no-sensor personal mean, so it cannot all be attributed to learning physiological conversion. History size and recency co-vary, and the same development outcomes have been repeatedly inspected. New calibration days cannot be manufactured by duplicating existing rows or treating unlabeled days as zero intake.
