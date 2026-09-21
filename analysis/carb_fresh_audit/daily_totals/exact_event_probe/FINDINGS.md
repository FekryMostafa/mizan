# Exact recorded meal-time diagnostic

Exact meal-time anchoring did not solve carbohydrate amount estimation. The best of three prespecified diagnostic arms, CGM plus clock time, got12/44 daily totals within±10%, MAPE22.79%, MAE47.17 g. Clock alone got10/44 and25.40% MAPE; CGM alone got8/44 and26.16% MAPE. These are known-event diagnostics, not passive prediction results.

Used267 calibration food events across the same64 earlier days and189 food events across the same44 later days. Merged only identical timestamps, retained zero-carb events and overlapping responses, and verified event carbs sum to every existing daily target. All later event glucose windows were complete. Inputs were raw and baseline-relative Libre values from−60 to+240 minutes around recorded event times, plus clock encoding in the corresponding arms. No food identity, meal category or current macros were supplied. Fixed the model configuration to the prior diagnostic without tuning on later labels.

Hourly known-event CGM-plus-clock MAPE was25.22%; exact-event MAPE is22.79%. This comparison changes both alignment and event segmentation (multiple food records within an hour are now separate), so the gain cannot be assigned solely to more precise timing. Recorded timestamps are not independently verified ingestion times.

## Located a large daily error in a specific event

For P13 on2024-02-02, the297 g day breaks down as follows:

| Time | Recorded carbs | Predicted carbs |
|---|---:|---:|
|06:56|66 g|62.53 g|
|12:39|43 g|56.48 g|
|15:41|147 g|44.97 g|
|18:19|41 g|39.02 g|

The afternoon event accounts for102 g of underestimation, most of the daily deficit. Other severe event misses include P17's131 g at21:00 predicted19.47 g, P26's137 g at16:18 predicted25.89 g, and P4's126 g at18:57 predicted35.53 g. This narrows a next raw-data investigation to high-carbohydrate afternoon/evening events and their earlier calibration analogues.

The experiment did not validate10%. Query target replacement did not affect model outputs, all44 days remained evaluated, and exact event timing was explicitly provided only for this diagnostic. Improvements here must not be reported as solving passive meal detection or daily calorie tracking.
