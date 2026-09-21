# Daily carbohydrate prediction: first chronological test

The daily target has not reached ±10%. Across 44 later days from 16 people, 13 days (29.5%) were within ±10%. Mean absolute percentage error was 20.08%; mean absolute error was 39.56 g. A person's earlier average alone also hit 13/44, with 21.21% error and 41.03 g MAE. The CGM model adds little predictive value in this first test.

## Data and protocol

Audited 533 participant calendar days from all 45 source participants. 130 passed prespecified checks for complete published Libre minute coverage, breakfast/lunch/dinner records, and resolved full-consumption labels for every recorded meal. Ten of these days belonged to people with fewer than five eligible days; the remaining 120 split into 76 earlier and 44 later days. Exclusion counts overlap; see summary.json and day_audit.csv. Sensor-bound values were retained.

A day is midnight to midnight. The outcome is the sum of recorded carbohydrate grams, not independently verified total intake. Having three main meals recorded does not prove that all intake was logged. Sensor coverage reflects publisher interpolation, not verified native sample availability. The eligible subset is selective and cannot represent arbitrary real-world days.

Compared a personal intake mean with ridge models predicting deviations from that mean using daily glucose summaries, and glucose plus HR/activity summaries. Features included glucose distribution, positive 15-minute changes, excursion area proxies, and six-hour mean levels. The latter are descriptors, not glucose mass measurements. Personal centering, scaling and model coefficients used earlier data only. Current meal timing, meal counts, food types and macro labels were not predictors.

Shared settings were chosen on each person's final earlier day (16 validation days), then refit on all 76 earlier days. CGM-only with strong regularization won this small validation comparison. The 44 later predictions were saved before scoring. These people have appeared in earlier meal experiments, so this is development evidence rather than a fresh prospective validation. No claim of generalization to new people is made.

## What failed

The selected model stayed close to personal historical intake: its median absolute change from that baseline was only 5.36 g/day. It therefore missed large departures from usual intake. This describes the fitted model's weakness; it does not establish that those departures have no recoverable CGM signature.

For example, P26 had a recorded 122 g day (24+94+4), but the model predicted 215.59 g against a personal baseline of 211 g. P9 had 132 g (66+40+0+26), predicted 206.54 g. P6 had 150 g (66+43+41), predicted 226.10 g. The ten largest percentage-error cases were checked against both the prepared meal table and original raw participant CSV carbohydrate cells; every sum matched. This rules out an aggregation mistake in these cases, not errors in original food logging.

All 44 saved predictions were independently reconstructed from the saved coefficients and personal centers within 1e-8 g. Input prepared-source hashes remained unchanged.

Next investigation: compare complete sensor traces on low-intake days with earlier high-intake days for the same person; audit late-night meal carryover and preceding-day activity before choosing another representation. The present result does not justify declaring daily CGM carbohydrate prediction impossible or accurate within ±10%.
