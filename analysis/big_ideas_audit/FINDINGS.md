# Independent data for the macro-prediction experiment

7 September 2026. Downloaded the glucose and food-log files for all 16 participants in BIG IDEAs Lab Glycemic Variability and Wearable Device Data v1.1.3. All 34 downloaded data/license/demographic files match the publisher's SHA256 checksums. Total downloaded payload is approximately 2.43 MB, excluding the checksum and local manifest files. High-frequency wristband streams have not been downloaded.

Source: [PhysioNet v1.1.3](https://physionet.org/content/big-ideas-glycemic-wearable/1.1.3/). The study supplies Dexcom G6 recordings and logged food nutrients, with repeated standardized breakfasts. It is a different study from CGMacros. The documentation describes food logging; it does not establish chemically assayed macro truth.

## Reserved evaluation participants

Before parsing any meal records, participants 001–008 were assigned to development and 009–016 to reserved evaluation. Downloading and checking the latter files did not expose their traces or meal values. No reserved participant records have been parsed or modeled in this work.

The split is recorded in `dataset/big_ideas_1_1_3/RESERVED_SPLIT.json`. Freeze preprocessing, calibration selection, model parameters and success criteria before evaluating the reserved participants. A test subsequently used for tuning must no longer be called untouched. Public availability also means this is an analyst-level holdout, not proof that every possible pretrained model has never encountered it.

## First raw-data findings, development participants only

| Participant | Food item rows | Missing fat labels | Complete meals | Eligible isolated three-hour meals |
|---|---:|---:|---:|---:|
| 001 | 61 | 57 | 3 | 0 |
| 002 | 68 | 52 | 12 | 1 |
| 003 | Not safely parsed | Unknown | Unknown | Unknown |
| 004 | 55 | 0 | 25 | 18 |
| 005 | 93 | 0 | 45 | 17 |
| 006 | 73 | 0 | 48 | 20 |
| 007 | 103 | 0 | 36 | 11 |
| 008 | 82 | 0 | 30 | 19 |

There are **86 initially eligible meals across six development participants**, before removing any meals for personal onboarding. This is additional material to investigate, not a prediction result.

Participant 003's food file lacks the expected column names: its first line contains food data and fewer fields than the standard schema. No nutrient mapping was guessed. Participants 001 and 002 have extensive missing fat values despite having carbohydrate and protein values. Filling those blanks with zero would fabricate fat-free meals. Deriving fat from calories would create an inferred reference, not independently measured fat truth.

The preliminary audit combines food items only at exactly equal logged times. A meal is complete only if every component has all three macros and calories. It retains unknown-nutrient food events when checking previous/next food timing. Eligibility requires nonnegative nutrients, positive calories, 4C+4P+9F within 20% of calories, at least three hours since previous logged food and more than three hours until the next, and glucose samples bracketing each five-minute target from ten minutes before to three hours after food with no interpolation gap greater than 601 seconds. First/last logged events may have unknown previous/next intervals; this does not prove complete recording. Nearby but unequal food timestamps and amount semantics still need review before freezing preprocessing.

This evidence changes the next experiment: develop a continuous gram predictor with chronological calibration using these additional meals, then test a frozen pipeline on the reserved participants. The four exact CGMacros breakfast recipes cannot be assumed to exist in this dataset. This will require calibration selection that works with actual earlier logged meals.

[Per-participant quality results](development_quality.json) and [development meal audit](development_meals.csv) contain the raw audit outputs. Source files and provenance are under `dataset/big_ideas_1_1_3/`. No model has yet been verified on this independent cohort.
