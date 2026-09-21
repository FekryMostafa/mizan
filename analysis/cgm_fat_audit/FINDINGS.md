# CGMacros raw-data audit: can glucose contain information about fat intake?

## Main finding

There is a useful matched-meal contrast in the actual data: breakfast shakes with **66 g carbohydrate, 22 g protein and 0 g fiber**, with either **10.5 g or 42 g fat**. The paper rounds the lower amount to 11 g. This is substantially stronger material for a first fat-information experiment than the single near-fat-only snack.

The larger-fat breakfast generally has a later peak and a lower early response on the participant-average plots. Individual responses and repeat days vary substantially. These are descriptive observations, not proof of accurate grams prediction, isolated causal effects or fat-only inference. No prediction model was trained in this audit.

## Coverage and selection

- Inspected all 45 participant CSV files: 1,706 entries with carbohydrate, protein and fat labels. Entries are meal/snack records, not necessarily independent experiments.
- Exact recipe labels initially identify 87 lower-fat and 89 higher-fat breakfast records. Requiring explicitly recorded 100% consumption leaves **68 lower-fat and 69 higher-fat records in 35 people**.
- For each device separately, retained complete glucose data for 0–180 minutes, at least 8 of the 10 preceding baseline minutes, no subsequent logged food through the window, and no preceding logged food within 180 minutes. There are **33 people with both fat conditions** on each device. Libre has 66 eligible lower-fat and 63 higher-fat events; Dexcom has 65 and 61. Pairwise analyses use people with both conditions, averaging repeated meals within each person and condition.
- At five hours only **8 people per device** retain both conditions. This small subset is not interchangeable with the three-hour cohort. Subsequent meals are an important limitation for late-response analysis.
- No fat-only labeled entry exists. The near-fat-only snack is 14 g fat, 2 g carbs and 4 g protein, participant 10. It follows lunch by 188 minutes and another snack follows it by 73 minutes.

## What the curves show

| Within-person high-fat minus low-fat comparison, first 3 hours | Libre | Dexcom |
|---|---:|---:|
| People with a later peak | 22 / 33 | 26 / 33 |
| Median change in peak timing | +10.5 min | +11 min |
| Median change in average baseline-adjusted glucose | −5.3 mg/dL | −5.5 mg/dL |
| People with a higher average glucose response during hours 2–3 | 18 / 33 | 17 / 33 |

Peak delay is a promising feature. A universal rule that more fat creates a higher late tail is not supported by these three-hour records. Peak timing is approximate: the released minute-level readings were interpolated from 15-minute Libre and 5-minute Dexcom measurements.

The direction of median peak delay also appears in the healthy subgroup: 12 eligible people, roughly +13 minutes on Libre and +15 on Dexcom. These small exploratory subgroup summaries are not a guarantee for any individual.

## Repeatability matters

Comparing the early and later repetitions of the same labeled recipe, the median absolute difference in the three-hour average glucose response is approximately **12 mg/dL for Libre and 14 mg/dL for Dexcom**. The median absolute difference between the person-averaged low/high-fat conditions is approximately **8 and 7 mg/dL**, respectively. These are descriptive comparisons with different averaging and dependence structures, not a formal signal-to-noise estimate.

For participants with two usable repetitions of each condition, the sign of the peak-time contrast agrees across the two chronological repetitions in **18/28 people on Libre** (two have a zero contrast) and **15/25 on Dexcom**. The sign of the 2–3 hour tail contrast agrees in only 7/28 and 11/25, respectively. Personalization may help, but the data do not justify assuming a perfectly stable personal response.

## The near-fat-only snack

Both devices show a rise before the next snack: approximately **20 mg/dL on Libre**, peaking at minute 51, and **37 mg/dL on Dexcom**, peaking at minute 64, relative to the median preceding ten-minute baseline. It is therefore not a flat trace.

We cannot attribute that rise specifically to 14 g fat: the snack includes carbohydrate and protein, follows a large lunch, and has no matched control or repeat. The subsequent snack prevents interpreting later rises as this snack alone. Its curve is useful to inspect but is not a clean calibration example.

## Data-quality and interpretation checks

- Source timestamps were checked for duplicates; no duplicate timestamp was accepted. Missing readings were not filled by this audit. Original minute-level interpolation remains present.
- Different CSVs use different activity headers (METs, Intensity, Steps), one has a trailing space in Amount Consumed, and two lack that field entirely. Headers were trimmed; absent consumption was preserved as unknown, not assumed to be 100%.
- No macro amounts were multiplied by the consumption percentage. The central comparison uses explicitly 100%-consumed entries to avoid that ambiguity.
- Baseline is the median glucose in the ten minutes before the meal, excluding the meal timestamp. Signed changes are retained rather than clipping dips to zero.
- Both sensors were examined separately. They are simultaneous views of many of the same events, not independent cohorts or twice as many people.
- No control for activity, sleep, stress, ingredient differences or calendar-day effects has been applied. The protocol repeats recipes on scheduled days, so recipe/day associations are a potential shortcut for future models. Activity columns need harmonization before adjustment.
- All eligible Libre participant plots were generated and inspected; no participants were selected because their curves supported the hypothesis. No significance, prediction accuracy or confidence interval is claimed.

## What this justifies doing next

The first supervised benchmark should use these matched breakfasts. Train using earlier repetitions, test later repetitions, and compare curve-shape features against a no-signal baseline. Predict the two fat levels first, while keeping meal/day IDs out of the inputs. This tests whether the apparent differences repeat well enough to be useful. Only after that should we expand to fat grams across mixed meals. Two fat levels cannot establish arbitrary dose estimation, and mixed-meal results will not establish fat-only performance.

## Files

- `matched_fat_comparison.png`: group curves, person-level tail contrasts and repeat variability.
- `all_person_curves.png`: every eligible Libre participant, with repeat-day curves.
- `near_fat_only_snack.png`: target snack with next-food timing marked.
- `meal_inventory.csv`, `matched_breakfasts.csv`, `paired_person_differences.csv`, `repeat_variability.csv`, `source_quality.csv`, `summary.json`: numerical audit outputs.
- `differences_by_health_group.csv`, `repeat_direction.json`: exploratory subgroup and chronological-repeat checks.

Sources: local CGMacros participant CSVs and bio.csv; [CGMacros paper](https://doi.org/10.1038/s41597-025-05851-7), Tables 3–4 and Data Records. The Karpathy article supplied by the user informed the inspect-first and simple-baseline workflow. Original datasets were not modified.
