# PolyCORE public-data audit

8 September 2026. Objective: determine whether this newly released sweat-lipid dataset can test consumed carbohydrate/protein/fat grams within 10%. That objective remains unachieved.

## What we actually obtained

The author-hosted full paper, publisher supplement and four source workbooks are downloaded under `dataset/polycore_lipid_2026` and `reference/literature_refresh`. The repository is checked out at commit `6277a9be38cadb7448cdaeaf2a9dd7eb95835000`. Its synthetic example is not participant data and was not used as validation.

The Figure 4 workbook contains real released electrical traces: glucose current, cholesterol current, TG-proxy current, pH voltage, ATP calibration information and sweat-rate samples. Five condition sheets have 3,301 / 3,436 / 3,434 / 3,335 / 3,423 time-indexed electrical rows respectively (fasting, bacon and eggs, pizza, ground beef, milkshake), about 55–57 minutes each. Separate Figure 4j sheets contain longer habitual-activity segments. These are plotted condition traces, not thousands of independent meals.

`extract.py` exports the five condition traces with original spreadsheet row numbers, preserving electrical units. It checks numeric channels and strictly increasing timestamps. `extraction_summary.json` preserves counts, ranges and the source SHA256. Originals remain unchanged. No concentration or gram conversion was fabricated.

## Why this is useful, and why we cannot yet train the requested model

The paper's Figure 4 shows different glucose, cholesterol and TG-proxy trajectories across conditions. A lipid-related channel can therefore be investigated separately from glucose. However, dose discrimination is not established by different meal-type examples.

1. **Intake labels:** no measured portions, consumed macro grams, participant IDs or repeated-dose mapping were found linked to the five Figure 4 traces in their source sheets or the inspected dietary methods and supplement tables. Bacon/eggs and beef are food descriptions in the article, not verified nutrient references. Do not infer a portion from an illustrative icon or the photograph.
2. **Timing:** the article explicitly states meals were eaten 30 minutes BEFORE sensor placement, both in the results and methods. The first point in each released trace is therefore not a true premeal baseline. This corrects the earlier preliminary interpretation that food came 30 minutes into monitoring.
3. **What the TG channel measures:** the paper explicitly acknowledges endogenous glycerol interference. Its enzyme cascade responds to glycerol including that produced by triglyceride hydrolysis; the authors describe a lipolytic-activity proxy, not strictly selective absolute triglycerides. Neither current nor inferred sweat concentration is grams of dietary fat consumed.
4. **Calibration:** ATP supply, pH and sweat flow affect interpretation. Raw nA values across different sensors cannot be ranked as fat doses. Sheet 4f labels pH voltage as V whereas other meal sheets say mV; numerical values are similar in magnitude. Preserve this discrepancy and request clarification rather than silently changing units.
5. **Independent validation:** thousands of adjacent timestamps cannot be randomly split to create an honest unseen-meal test from five condition traces. Meal/session/participant grouping and repeated doses are required before constructing such a test.

## Accuracy and reproducibility discrepancies worth resolving

The published task is sweat-to-BLOOD lipid concentration in mg/dL, not intake grams. Public code uses a random forest for its causal-assumption-guided model and linear methods as conventional baselines, so that comparison changes both feature specification and estimator. A stronger result should compare the same estimator with/without candidate information.

The checked code uses shuffled `KFold` on rows (`splitter.split(x)`), despite retaining PatientID. It does not enforce participant separation or chronological personal calibration. Repeated measurements could cross folds. Without the full identified paired dataset we cannot quantify overlap or reproduce a grouping-corrected result. This is a validation concern, not proof of the cause of reported accuracy.

| Source | Cholesterol MAE | TG MAE |
|---|---:|---:|
| Main article text | 15.27 | 16.44 |
| Supplementary Table 4, visually checked | 23.5 | 16.44 |
| Publisher Figure 5hi workbook | 15.27 | 20.8 |
| Repository reported-summary CSV | 15.27 | 20.8 |

All numbers are mg/dL. These conflicts are unresolved; do not choose the most favorable version or describe them as reproduced. The main text refers to 24 participants, whereas Supplementary Table 2 lists patients 1–25; an inclusion/exclusion mapping is needed. Public Figure 5 source data includes blood/sweat scatter values and demographic values, but not a documented row-level join with participant, time, sweat rate and all model variables. Pairing them by spreadsheet position would invent linkage. Figure 5j/k are model response curves, not measured continuous blood trajectories.

## Concrete information needed from this study

- For every meal session: anonymous participant/session ID, measured food amounts and macros, exact intake and recording times, repeats, prior-food timing, and sensor-specific calibration coefficients.
- Original synchronized glucose/CH/TG electrical signals, pH, ATP and sweat-rate data with units and conversion code; premeal recordings if any exist outside the release.
- The fully linked paired sweat/blood dataset and original train/test assignments, with corrected metric values and the participant inclusion list.

These would let us test whether the additional sweat channels improve prediction of withheld doses after personal calibration, versus glucose and personal-history controls. They would not guarantee 10% accuracy. No author contact was sent during this audit, and no human hardware trial was initiated.

## Sources

- [Author-hosted full article](https://www.gao.caltech.edu/uploads/2/6/7/2/26723767/non-invasive_continuous_lipid_profiling.pdf)
- [Publisher and source data](https://www.nature.com/articles/s44460-026-00117-0)
- [Public analysis code](https://github.com/SIJIEJI/polycore-lipid-causal)

Scope of reading in this audit: dietary results/methods, interpretation of TG chemistry, Figure 4 (visually), supplement meal captions and tables, workbook inventory and five electrical traces, Figure 5hi values, and the relevant public validation code. This is not a claim that every fabrication method or supplement figure has been independently reproduced.
