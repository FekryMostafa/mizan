# Sweat calories: evidence audit and first experiment

Prepared 4 September 2026. This is a focused technical audit, not an exhaustive literature review, clinical validation, or patentability opinion.

## Decision

There is enough evidence to justify a small chemistry feasibility experiment. There is not yet evidence here that sweat can recover daily calories eaten with useful accuracy. The first investment should answer whether a reproducible, intake-related signal survives basic controls. Building a wearable before answering that question would consume resources without resolving the main uncertainty.

## Materials actually inspected

- Downloaded and extracted the 16-page [2026 lipid-sensing paper](https://www.gao.caltech.edu/uploads/2/6/7/2/26723767/non-invasive_continuous_lipid_profiling.pdf).
- Downloaded and inspected the 52-page [supplement](https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs44460-026-00117-0/MediaObjects/44460_2026_117_MOESM1_ESM.pdf), including visual verification of Tables 3–4.
- Inspected publisher source workbooks for Figures 2–5; Figure 4 includes actual sensor traces. Recalculated numerical results from Figure 5.
- Cloned [the released code](https://github.com/SIJIEJI/polycore-lipid-causal/tree/6277a9be38cadb7448cdaeaf2a9dd7eb95835000), commit `6277a9be38cadb7448cdaeaf2a9dd7eb95835000`.
- Read the assay manufacturer's protocol and an earlier primary study on sweat collection contamination.

## Findings that change the experiment

**1. The triglyceride channel also detects free glycerol.** The paper explicitly describes its measurement as a proxy rather than strictly selective absolute triglycerides. Its 24-person blood-mapping protocol includes a 75 g glucose challenge, not a controlled dietary fat dose-response study. These are important limits when translating lipid profiling into calorie intake. [Paper](https://www.nature.com/articles/s44460-026-00117-0)

**2. The released validation permits the same participant in training and testing.** `src/reproduce_figure5hi.py`, lines 126–136, applies shuffled KFold to rows, despite carrying PatientID. This can overstate performance on unfamiliar people. Without the complete subject-linked dataset, I cannot quantify the effect or establish that every published analysis used precisely this split. The repository itself recommends subject-grouped validation for that use case. [Code](https://github.com/SIJIEJI/polycore-lipid-causal/blob/6277a9be38cadb7448cdaeaf2a9dd7eb95835000/src/reproduce_figure5hi.py)

**3. The model comparison changes both assumptions and algorithm.** The released “Causal ML” implementation uses random forests; comparators use linear models. For triglycerides, its inputs match the full-model inputs. A matched random forest is needed to isolate any benefit from the causal specification. This is an evaluation issue, not evidence that the sensor is useless. [Feature definitions](https://github.com/SIJIEJI/polycore-lipid-causal/blob/6277a9be38cadb7448cdaeaf2a9dd7eb95835000/src/causal_specification.py)

**4. Reported error values need reconciliation.** Supplement Table 4 gives cholesterol MAE 23.5 and triglyceride MAE 16.44 mg/dL; source sheet 5hi gives 15.27 and 20.8 respectively. Table 3 gives 15.27 and 16.44. Different analyses or editorial errors might explain this. Do not treat it as misconduct, or select whichever number looks best. Table 3 does include a no-sensor comparison. [Supplement Tables 3–4](https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs44460-026-00117-0/MediaObjects/44460_2026_117_MOESM1_ESM.pdf), [Figure 5 source data](https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs44460-026-00117-0/MediaObjects/44460_2026_117_MOESM6_ESM.xlsx)

**5. Collection can overwhelm the signal.** An earlier study found 4–10 times more lipid in scraped sweat than sweat collected with a skin barrier. This does not invalidate the modern device, but makes skin contamination controls necessary. [Takemura et al., 1989](https://pubmed.ncbi.nlm.nih.gov/2638916/)

## Independent arithmetic on released figure data

| Published sheet | Numeric pairs | Recalculation |
|---|---:|---|
| 5b, sweat/blood cholesterol | 76 | Pearson r² = 0.02384 |
| 5c, sweat/blood triglycerides | 77 | Pearson r² = 0.01996 |
| 5l, true/predicted blood cholesterol | 35 | MAE 14.504 mg/dL; predictive R² 0.64645 |
| 5m, true/predicted blood triglycerides | 30 | MAE 16.842 mg/dL; predictive R² 0.90633 |

These are calculations on published plotted points, not an independently trained model or a reproduction of cross-validation. Pearson r² and predictive R² differ. Different subsets and fold averaging can explain differences from reported summaries. Real figure-level data are public; the repository's synthetic demo is not the only available data. Complete participant-linked training records are still needed for the decisive validation. Exact results and source checksum are in `published-data-recalculation.json`.

## Cheapest useful experimental sequence — proposed, not validated

**First: establish what the chemistry reads, before anyone eats a test meal.** Ask a laboratory to test blanks, glycerol, triglyceride standards, and mixtures, with and without lipase. Four conditions × two reactions × duplicates is 16 wells, plus calibration and quality controls. Repeat the relevant checks in a sweat-like matrix, then actual collected sweat. Let the laboratory select compatible standards and handling.

The commercial assay already instructs users to run samples without lipase and subtract free glycerol. Its stated matrices are serum, plasma and lysates; sweat suitability must be established. It requires a fluorescence plate reader and cold storage, so an Arduino alone cannot execute this assay. [Manufacturer protocol](https://www.cellbiolabs.com/sites/default/files/STA-397-serum-triglyceride-quantification-kit-fluorometric.pdf)

Retain both readings: free-glycerol signal and lipase-dependent increment. The increment is not automatically exclusive to dietary triglycerides. Have TULMAC assess whether a small subset can be checked for intact triglyceride species by mass spectrometry, including collection blanks and skin controls.

Proposed analytical gates, to agree with the laboratory before testing: duplicate CV ≤20% above the quantification limit; 80–120% spike recovery; a detectable lipase-dependent increment exceeding blank variability. These are starting engineering criteria, not established sweat-calorie standards. A failure is useful: resolve chemistry or sampling before fitting an AI model.

**Second: a small randomized within-person meal pilot, only if the assay works.** A researcher should help finalize collection and human-study requirements. Start with two ordinary meals matched for carbohydrate and protein but differing by a known, weighed amount of fat, each repeated on three separate days in randomized order. Collect a genuine premeal baseline and several postmeal samples over a lab-selected window. Standardize collection site and method, prior meal, timing and activity; record collected volume, duration, temperature and relevant deviations. Include collection blanks. This six-session design estimates repeatability; it cannot establish a consumer product's accuracy.

The first endpoint is whether either chemical channel distinguishes fat doses consistently beyond sweat rate, time, and day-to-day noise. Follow a promising result with an equal-calorie fat-versus-carbohydrate substitution to separate fat response from total-energy response. Avoid treating consecutive seconds from one meal as independent examples.

**Third: build the dataset your company needs.** Ground truth must include weighed consumed portions and leftovers, meal composition, participant and session identifiers, sample timestamps, collection volume/duration, assay batch, both chemical readings, and quality flags. Hold out entire days for personal predictions and entire participants for new-user predictions. Compare the same model with and without biochemical inputs. A small six-session pilot calls for simple comparisons and uncertainty estimates, not a large neural network. Later evaluate full days, missed meals, novel recipes and delayed responses.

## Spending and outreach

- Spend $0 on custom electrodes now. Use software skills to organize data and implement honest evaluation.
- Obtain a written quote for the smallest analytical pilot before buying reagents. A commercial kit was listed at about $535/100 assays during research; duplicates, glycerol controls and standards consume that capacity. This is not a total experiment quote. Instrument time, collection supplies, storage, labor and confirmatory analysis are additional. [Supplier listing](https://www.cellbiolabs.com/triglyceride-assays)
- Treat an initial $1,000 ceiling as a founder-imposed stop rule, not a promise the work fits. It may require donated laboratory access or existing reagents. If quotes exceed it, seek an in-kind academic pilot before hardware spending.
- **Juliane Sempionatto, Rice, jsemp@rice.edu:** request the participant-linked dataset and ask about glycerol correction, participant-held-out performance and the conflicting MAEs. [Verified faculty contact](https://profiles.rice.edu/faculty/juliane-sempionatto)
- **Pragney Deme / Norman Haughey, TULMAC:** request analytical feasibility, minimum sweat volume, appropriate controls and a price for a small targeted pilot. Their lipidomics capability does not establish validated sweat assays or free external access. [Team](https://tulmac.com/team/), [contact](https://tulmac.com/contact/)

The potentially better approach is two separately characterized chemical signals, direct food-intake labels, and evaluation on unseen sessions and people. These are testable research choices, not claims of patent novelty. Your immediate milestone is a repeatable intake-related signal with a known collection method and assay cost. That is concrete progress toward the company even if the eventual wearable architecture changes.
