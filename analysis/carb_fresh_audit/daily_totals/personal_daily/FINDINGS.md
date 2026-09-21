# Can a personal daily formula fit the known data?

Yes: the selected personal Gaussian-kernel formula fits all 64 calibration days within ±10%, with mean absolute error approximately 0.000017 g. But it gets only 12/44 later days within ±10%, with 23.85% mean absolute percentage error and 44.88 g MAE. The daily accuracy objective remains unmet.

## Experiment

Used the same 64 calibration days and 44 later days as the prior next-morning comparison. Each person's data has only 2–5 calibration days. The target remains midnight-to-midnight recorded carbs; glucose through the following 05:59 is available. Calibration observation windows end before query days begin.

Compared three feature families (daily summaries plus overnight glucose; full 120-point 30-hour glucose sequence; summaries with activity/HR/history) and four Gaussian kernel widths. Every model was fitted independently per person with tiny fixed regularization 1e-8 to allow interpolation. Shared settings were selected using the existing 29 earlier chronological validation days. Full sequence with gamma 0.01 won that comparison, hitting 11/29 validation days with 22.34% MAPE.

The selected model and all later predictions were saved before later scoring. Reloaded models reproduced all 44 predictions within 1e-8 g while current query labels were replaced by an arbitrary constant. No food information was used in the feature vectors. IDs choose the person's calibration model; they are not numeric sensor predictors.

## Memorization control

Repeated fitting 100 times after shuffling carbohydrate labels among the calibration days of each person. All 100 shuffled versions still fit all 64 calibration answers within ±10%. Their later MAPE had median 24.91% (range 19.82–33.25%), and median tolerance hits 13/44. The real-label model's 23.85% and 12/44 are not compelling compared with this control.

This is a descriptive negative control with model settings fixed, not a formal hypothesis test. It establishes that nearly perfect training fit is easy even when the correct pairing of signals with grams is deliberately broken. It does not establish that the original glucose signals have no useful information.

## Earlier-day raw structure

All pairs of earlier calibration days were compared using clock-matched CGM values. For P1, the 182 g and 116 g days differed by 9.94 mg/dL RMS over 120 time points. The 220 g and 210 g days differed by 13.26 mg/dL RMS. Thus, under this full-sequence distance, a 66 g dose difference looks more similar than a 10 g difference. These are not identical traces and this comparison does not rule out a better representation.

The current weakness is learning a transferable mapping from only 2–5 personal calibration days, rather than inability to fit those days. The best previously tested MAPE remains 18.94% on these reused later-day development data. None of these results validate ±10% daily prediction.

Next useful direction: test a model that learns shared nonlinear relationships across people while limiting personal calibration to a few parameters, rather than independently fitting a high-dimensional curve from 2–5 examples. Any such experiment should retain the same later outcomes, compare to the personal intake baseline, and use earlier windows for selection. More exact personal interpolation alone is not supported by this control.
