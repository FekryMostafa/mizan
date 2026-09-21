# Additional Stanford CGM release

**Later correction:** the apparent three-plus repetitions for XB19 include exact duplicate curves. After the full-vector duplicate audit, only XB6 remains usable for the attempted independent repeated-calibration comparison. See DUPLICATE_FINDINGS.md; raw session counts below count IDs, not independent curves.

8 September 2026. Located and downloaded two primary-source tables from https://cgmdb.stanford.edu/data/ and the article HTML, with URL, byte counts and local SHA256 hashes saved in dataset/stanford_cgmdb/download_manifest.json. These hashes record downloaded content, not an independent publisher checksum verification.

The public CGM table contains 23,520 rows: 588 condition/repetition sessions from 38 people. Each has 40 glucose points, from -25 to 170 minutes at five-minute intervals. Session/time keys are unique and glucose values nonmissing. The article reports a larger study; it states that only participants consenting to sharing were publicly released. Do not confuse the public subset with all study participants.

Conditions include rice alone (82 sessions), rice with fat (42), rice with protein (42), and rice with fiber (43), plus other foods. There are 15 people with at least two rice and two rice-plus-fat sessions, and 13 with at least two rice and two rice-plus-protein sessions. Two people, XB19 and XB6, each have at least three rice and three rice-plus-fat sessions and also at least three rice-plus-protein sessions. This creates an additional repeated-calibration lead absent from the previously inspected cohorts.

The paper's intervention is 50 g total carbohydrate in the standardized base meal, with 15 g fat from 38 g creme fraiche or 10 g protein from 100 g boiled egg white consumed 10 minutes earlier. These are intervention amounts, not complete per-meal macro labels; supplementary nutrition composition must be checked before assigning total fat/protein/carbohydrate labels. Time zero is the base carbohydrate meal, so a premeal baseline must precede the -10 minute preload. The downloaded table is processed, non-integer glucose; it must not be described as unprocessed sensor export.

Source: Individual variations in glycemic responses to carbohydrates and underlying metabolic physiology, Nature Medicine (2025), https://www.nature.com/articles/s41591-025-03719-2 . The full HTML is saved; the relevant intervention, methods and sharing sections were examined. Full methodological review and supplementary-table verification are not yet complete.

## Next checks before inference

1. Verify smoothing/interpolation and repetition numbering from the author's linked code, https://github.com/mikeaalv/cgm_meal_manuscript . The table has no calendar dates; repetition order cannot yet be claimed to establish chronological separation across conditions.
2. Inspect supplementary nutrition values to separate added nutrient dose from total meal macros and quantify co-varying nutrients.
3. Freeze a repeat-based comparison before fitting. Two people with three-plus repetitions are too few for a general ±10% claim, but can test whether repeated calibration changes the measured instability.

No gram predictor has been fitted to these new records. This release changes the immediate next action from an external-data wait to a bounded provenance and repeatability audit. It does not establish feasibility or validate a finished model. Existing BIG IDEAs reserved participants remain untouched.
