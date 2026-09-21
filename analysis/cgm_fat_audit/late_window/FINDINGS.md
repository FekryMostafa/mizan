# Does observing five hours instead of three rescue gram predictions?

7 September 2026. The tested models did not improve enough to meet the target. This small comparison does not rule out useful late information with other methods or better data.

Both durations use exactly the same training rows, calibration meals and later test meals. All require complete five-hour glucose and no next logged food within five hours. Each person's four onboarding meals precede their test meals. Population training excludes the evaluated person. Fixed ridge settings were specified before running; no model was selected using these test outcomes.

Only five Libre participants with 18 later meals and four Dexcom participants with 12 later meals satisfy all those requirements. These device cohorts overlap and cannot be summed as independent participants.

| Primary continuous model | Three hours | Five hours |
|---|---:|---:|
| Libre: all three macros within 10% | 0/18 | 0/18 |
| Dexcom: all three macros within 10% | 0/12 | 0/12 |
| Libre fat mean absolute error | 16.10 g | 15.87 g |
| Dexcom fat mean absolute error | 13.14 g | 14.23 g |

Carbohydrate and protein mean absolute errors increased with the longer window on both devices. A nearest-onboarding-recipe comparison got 2/18 Libre meals correct at either duration and changed from 2/12 to 1/12 on Dexcom. That comparison cannot recover arbitrary new macro combinations. Seven Libre and five Dexcom queries have macro labels matching onboarding recipes; the rest are unfamiliar combinations.

The observation window is therefore not an established fix for the previous failures. The severe reduction in usable participants is itself a data limitation: this dataset provides too few complete four-recipe five-hour calibrations with later isolated tests for a strong conclusion.

[All predictions](predictions.csv), [summary](summary.json), [training and calibration IDs](split_manifest.json), and [fixed-run manifest](run_manifest.json) are saved for verification. This remains retrospective development evidence on an already explored dataset. Logged meal timing and isolation do not test automatic meal detection.
