# Additional earlier calibration days

There are 27 unused earlier calendar days for the 16 evaluation participants whose 30-hour windows could precede the later evaluation. None passes the existing strict eligibility rule unchanged. This does not mean every exclusion is necessarily bad data.

- 16 have incomplete daily sensor coverage, mostly at study start.
- 4 have complete sensors and full-consumption labels but lack a main-meal category: P2 Nov17; P9 Sep16 and Sep17; P26 Mar27. Their daily totals cannot be assumed complete simply because other records exist; participants could also have skipped a meal. The record does not resolve this.
- 7 have complete sensors with unresolved labels; one also lacks a main meal.

The 7 label-review days include three all-zero macro records and four P41 days with partial or out-of-range consumption fields. On P41 Apr29, a lunch recorded at 75% has 94 g carbs, the same as the full planned HLLL lunch in the source paper. This leaves portion interpretation unresolved; no multiplication or label replacement was performed. Other out-of-range consumption values likewise remain unresolved.

## Source-photo inspection

Extracted the three all-zero records' original photos from the local CGMacros archive and viewed them directly:

- P12 March3 21:24, record CGMacros-012:7963: a plate with meat and pale vegetable/potato-like pieces. Consumption is recorded as zero. The picture does not prove anything was eaten, but it does not establish an empty meal either. Keep unresolved.
- P27 June11 23:58, record CGMacros-027:2388: a cup containing a tea bag and liquid. The reported zero macros are plausible for unsweetened tea. Additives cannot be verified from the image. This is a reasonable candidate for a separately marked sensitivity experiment using the existing zero label, rather than an invented macro estimate.
- P27 June15 17:36, record CGMacros-027:7766: a cup of tea-like liquid. Zero is similarly plausible, but that day also lacks a main-meal category, so resolving the beverage alone would not satisfy the strict day rule.

Thus there is one concrete candidate day (P27 June11, recorded daily carbs277 g) to test under a documented acceptance of the original zero-calorie beverage record. It would increase P27's personal calibration, not establish clean additional history for everyone. No source data, labels, training split, or published results were changed by this audit. Photos are used to audit historical targets only, not as deployment inputs.

Evidence: `excluded_earlier_days.csv`, `meal_records.csv`, `summary.json`, and three extracted JPEGs. The locally saved source paper is `<repo>/reference/CGMacros-paper.md`, Methods and Data Records sections and lunch-composition table. This audit identifies an assumption to test; it does not prove the full day's true intake or the 10% goal.
