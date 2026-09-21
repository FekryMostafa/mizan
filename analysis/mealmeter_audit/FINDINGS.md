# MealMeter reproducibility and relevance audit

8 September 2026. Read the full arXiv v1 article (including methods, results and references) and all source cells in the public notebook. Inspected stored text outputs without treating them as a fresh execution. Repository commit: `aafe2789cc1ed805ba4280d500c07f8c97ec12d9`.

## Relevance to the requested target

MealMeter studies 12 people over three controlled laboratory days, combining CGM with wrist signals. The diet targets approximately 55% carbohydrate, 20% protein and 25% fat by energy. Reported comparison-table MAEs are 13.2 g carbohydrate, 9.66 g protein and 3.67 g fat; corresponding RMS relative errors are 0.37, 4.51 and 0.74. These do not establish all-three-macros-within-10% accuracy. Its approximately fixed nutrient proportions also require a proportion-only control before concluding the system independently measures fat or protein dose. We have not measured the actual label correlations because those labels are not released here.

## Dataset search

The checked repository contains README.md and MealMeter.ipynb, not the original 173 signal files or matching nutrient spreadsheets. The notebook reads an author's local Windows drive. Its preview shows a few boundary rows, not a complete recoverable dataset. The author publication page links paper, code and poster, without a dataset link. Targeted MealMeter searches on Kaggle, Zenodo and Figshare produced no results on this date. This is a bounded search result, not proof that no public release exists anywhere.

## Verified notebook discrepancies

The executable audit in `audit_notebook.py` reads the notebook JSON and compares its saved filename output with its current source. Its output is `notebook_audit.json`, including a notebook SHA256. No participant models were executed.

1. **Personal groups do not match the saved participant ordering.** There are 173 signal filenames and 173 label filenames. Normalization uses block boundaries matching the saved participant counts, but the personal evaluation uses different boundaries. Ten of twelve evaluation blocks mix participants. Example: range 0:15 contains 14 P10 files and one P11 file; range 103:118 contains eight P5 files and seven P6 files. Thus the public artifact does not consistently implement a person-specific evaluation for the saved ordering. Stale output or different unpublished final code could explain this; the original analysis is needed to resolve it.
2. **Two signal/label filename pairs disagree.** Row 73 (zero-based) pairs P3_D1_snack2_short with P3_D1_snack1_label; row 74 pairs P3_D1_snacks1_short with P3_D1_snack2_label. Loading uses independent, unsorted directory listings, not an explicit meal-key join. These names suggest swapped snacks, but label contents are unavailable, so actual mislabeling is unconfirmed. The other 171 normalized filename pairs match.
3. **Personal minimum normalization precedes the split.** Cell 5 subtracts a minimum computed across all meals in each participant block, then cell 10 randomly splits meals. Held-out signals influence preprocessing. StandardScaler and PCA, in contrast, are properly fitted on training data only in the shown modeling cells. The effect of the earlier normalization cannot be quantified without data.
4. **Sensor-contribution aggregation is inconsistent with feature layout.** Features are constructed as 16 consecutive features per signal. Cell 19 uses `gamma.reshape(16, 7).sum(axis=0)`; this mixes features from all seven sensors into each named bar. The corresponding grouping for this layout would be `gamma.reshape(7, 16).sum(axis=1)`, though a signed coefficient sum still is not a causal or performance-based importance measure. The audit verifies the source-sensor mixture by index arithmetic. This issue concerns attribution, not the regression predictions themselves.
5. **Source and text disagree on resampling and PCA settings.** A stored 90-minute, 16 Hz preview has 86,400 rows. The code resamples to 10,800 points, equivalent to 2 Hz over 90 minutes, while the paper states 8 Hz. The pooled code uses seven PCA components; personal code uses three. The paper describes three. Do not silently choose one as the exact published protocol.
6. **Random splitting does not match future-meal onboarding.** The notebook uses 80/20 shuffled splits with seed 7; there is no chronological participant/day/meal exclusion rule. This does not implement calibration on earlier meals followed by prediction of later unfamiliar meals. It cannot be substituted for our requested evaluation.

## What could be reused

The broad approach—time/frequency summaries, train-only scaling/PCA, and a small regression model—is implementable. This audit does not establish that it will outperform models already tested on CGMacros or BIG IDEAs. We should not choose new hardware based on the notebook's sensor-importance bars. Whether additional EDA, temperature and BVP signals help requires a same-model comparison with and without those signals on the same withheld meals.

## Exact missing inputs for a faithful test

- The 173 complete signal records and corresponding nutrient labels, plus explicit participant, day and meal identifiers and units.
- Original timestamps and preprocessing/resampling code, together with the final notebook used for the article and its split assignments.
- Confirmation of the two snack pairings and per-person row boundaries.
- Ingredient/portion information and whether calorie conditions vary macro ratios independently or mostly scale a fixed mix.

With those inputs, we could rebuild joins by meal ID, fit all preprocessing on earlier calibration/training records only, compare against a no-sensor personal prior and nutrient-proportion control, and test all three gram outputs on withheld future meals. Correcting code does not guarantee better physiological prediction. No reported accuracy was reproduced, no new ±10% result was achieved, and no outreach was sent in this audit.

## Sources

- [Full paper](https://arxiv.org/html/2503.11683v1)
- [Public notebook](https://github.com/Arefeen06088/MealMeter/blob/main/MealMeter.ipynb)
- [Author publication page](https://asiful-arefeen.com/publication/mealmeter/)
