# CGMacros prepared data, version 1

This is a conservative, traceable copy for the carbohydrate investigation. It is not a claim that all labels, timestamps, or physiological responses have been validated. No model was trained and no glucose response was corrected.

## Use these files

- `meals.csv`: all meal events, normalized categories, reported values, separate normalized fields, and quality flags. Use this file for the full food history, including unresolved events.
- `calibration_candidates.csv`: full-consumption labels with a complete three-hour Libre record, no device-bound values in that response and no other meal record through its endpoint. This is a preliminary candidate subset, not a representative evaluation set. It does not guarantee a reliable preceding day or timestamp accuracy.
- `meals_needing_review.csv`: meal labels whose quantities or consumption are unresolved. Retained for inspection; not silently interpreted as fasting or zero intake.
- `participants/`: all 45 source CSVs with every original column/cell retained and additional `qc_` columns. Source row numbers count the header as row 1. Blank HR/activity values remain blank. Nothing is interpolated, clipped, smoothed, or removed.
- `issues.csv`: original-cell locations, flags, and dispositions. `file_summary.csv`, `summary.json`, and `manifest.json` record counts, hashes, and verification.
- The three auxiliary CSVs are byte-for-byte copies. Their baseline lab, demographic and microbiome information has not been reinterpreted or used to explain individual meal failures.

## Cleaning decisions

1. Normalize meal category casing and map `snacks` / `snack 1` to `snack` in the meal table. Preserve the original category beside it. Parse timestamps into a separate ISO field, without timezone assumptions or guessed time shifts.
2. Preserve all reported macros. Separate normalized macro columns are unavailable for missing, negative, nonfinite or all-zero macro vectors. All-zero vectors are unresolved, not necessarily errors: the source does not establish whether each is no intake, a drink, or missing nutrition information. A genuine zero-carbohydrate meal with positive fat/protein is retained as zero carbohydrate.
3. Do not multiply macros by consumption. The dictionary describes macros in the consumed meal; applying the percentage again could double-adjust them. Values outside 0–100 cannot be accepted as percentages. Small values strictly between 0 and 10 are additionally flagged for possible mixed units (the source includes 1, 2, 3 and 0.75 alongside 100 and 75). This is a conservative review heuristic, not a claim that all small percentages are invalid. Their normalized percentage is withheld pending clarification. Only 100% records pass the full-consumption label filter; partial records remain available for review.
4. Mark missing HR, glucose and activity explicitly. Constant activity with missing HR is not established rest. Keep METs and Intensity as distinct source columns; do not convert one to the other.
5. Flag malformed, duplicate, out-of-order and gapped timestamps. Do not shift meal times based on glucose shape. Every meal timestamp remains `unverified_source_timestamp`; no photo-based time audit was done here.
6. Retain glucose values at device bounds (40/400) with flags. Retain all unusual in-range curves, regardless of prediction error. Do not classify every low or high response as a bad measurement.
7. Inspect the published one-minute grid for completeness, retaining missing minutes rather than inventing observations. The publisher already interpolated Libre and Dexcom values; complete minute coverage is not independent native sensor coverage and cannot detect interpolation over undocumented native gaps.
8. Keep unresolved food events when flagging possible response overlap. `pre24h_food_record_needs_review` identifies recorded history with unresolved labels. A false value does not prove all meals were logged. `pre24h_*_complete` describes sensor records only.

No cohort was selected based on old prediction errors. The current 24/66 g experiment and its predictions have not been overwritten or rerun. Future experiments should use the prepared meal table and explicit quality criteria, retaining failures as outcomes.

## Evidence checked

- PhysioNet v1.0.0 [dataset](https://physionet.org/content/cgmacros/1.0.0/) and [dictionary](https://physionet.org/files/cgmacros/1.0.0/DataDictionary_CGMacros-00X.csv). The dictionary defines consumption as 0–100 percent and gives the glucose device bounds. Local dictionary: `../cgmacros_raw/DataDictionary_CGMacros-00X.csv`.
- Authors' [repository](https://github.com/PSI-TAMU/CGMacros), README and `parse_data.ipynb`, inspected September 8, 2026. No explanation of the anomalous consumption values was found in that notebook. A copy was saved in `../../analysis/data_quality/authors_parse_data.ipynb`.
- Local full paper `../../reference/CGMacros-paper.md` describes meal timestamps from photographs and interpolation of glucose to one-minute sampling.
- All 45 participant CSVs were compared byte-for-byte by SHA-256 with their members in the downloaded source archive. Every comparison matched. The anomalies are present in the archive, not introduced by the local CSV extraction.

## Reproduce and verify

Run `../../analysis/data_quality/clean_cgmacros.py` with bundled Python and pandas/numpy. It overwrites only this derived version's CSV outputs, never the source folder. Each exported participant CSV is re-read and every original cell is compared against its source. All input hashes are rechecked after processing. The manifest records the script hash and CSV output hashes.

What remains unresolved: the meaning of mixed consumption values; zero-filled meal records; whether partial-meal macros were already adjusted; actual meal-time accuracy; and native sensor gaps hidden by published interpolation. The available documentation does not authorize guessed corrections for these.
