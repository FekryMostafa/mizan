# Do skin conductance and temperature improve macro prediction?

8 September 2026. Completed the fixed comparison specified in PLAN.md before looking at added-signal prediction outcomes. All 12 EDA/TEMP files for development participants 002, 004–008 were downloaded and verified against publisher SHA256 values (980,043,082 raw bytes). The final download used selected compressed entries from the publisher ZIP; extracted raw hashes were checked again after modeling. Reserved participants 009–016 were not parsed or modeled.

All versions use the same 65 later meals from five people, with four earlier calibration meals per person. Population training uses other BIG IDEAs development people only, because CGMacros does not supply these modalities. The comparison therefore uses the earlier small-cohort ridge/kernel baseline, not the CGMacros-trained tree model. Training-only imputation/scaling, personal calibration chronology, and exclusion of the evaluated person from population training are enforced. No settings were changed in response to outcomes.

| Inputs | All three within 10% | Carb MAE | Protein MAE | Fat MAE |
|---|---:|---:|---:|---:|
| Glucose | 0/65 | 39.56 g | 13.73 g | 13.02 g |
| Glucose + EDA | 0/65 | 39.75 g | 14.31 g | 12.37 g |
| Glucose + temperature | 0/65 | 39.13 g | 13.91 g | 12.63 g |
| Glucose + both (primary) | 0/65 | 39.41 g | 14.38 g | 12.00 g |
| Personal calibration median, no sensor | 0/65 | 41.18 g | 15.56 g | 13.74 g |

Adding both signals improved average fat error by 1.02 g while worsening protein error by 0.64 g. Fat error improved in four people and worsened in one; person-level improvements were +1.86, -0.79, +1.75, +2.81 and +0.19 g for P4–P8. This small development sample does not establish a reliable independent signal or explain biological mechanisms. It plainly does not reach the requested accuracy.

## Missingness and limits

EDA and temperature have identical coverage windows in this release. Average query coverage is about 76%, 76%, 76% and 80% across the premeal and three hourly postmeal windows. Eleven queries have no postmeal wrist data; they remain in the primary evaluation with training-only imputation. Forty-five have at least 50% coverage in every window. A post-hoc descriptive comparison restricted to those same 45 queries is saved in coverage_subset.json; it does not replace the original denominator or constitute a newly selected validation result. Both primary methods still have zero joint successes in that subset.

These features summarize minute medians using window means, standard deviations and coverage. They do not represent all fast EDA dynamics or establish whether the wristband was worn properly at every timestamp. Observed temperatures span 19.2–37.81 in the released numeric scale, and EDA includes zeros. No outcome-driven cleaning threshold was introduced. Adding dimensions also changes the personal kernel geometry, so small gains cannot be attributed solely to physiological information. A richer representation or different model could behave differently, but these results do not justify a hardware recommendation or a 10% promise.

## Verification

The run finished successfully. Original glucose-only predictions reproduced within 1e-8 with zero relative tolerance. A separate verification checked all 325 predictions, identical query keys across five methods, finite nonnegative predictions, and every tolerance flag recomputed from actual and predicted grams. All 12 raw-file hashes were reverified. The pandas/NumPy date-range deprecation warnings did not interrupt execution; extracted coverage and dates were inspected. Model outputs remain comparisons against logged nutrient estimates, not chemical measurements of actual intake.

The target remains unachieved. This experiment resolves one specific uncertainty: these available EDA/temperature summaries do not rescue the tested gram-inference model. It does not establish impossibility for all sensors or algorithms.

- [Every prediction](predictions.csv)
- [Summary](summary.json)
- [Calibration and population split](split_manifest.json)
- [Independent checks and person-level differences](verification.json)
- [Coverage subset](coverage_subset.json)
- [Run provenance](run_manifest.json)
