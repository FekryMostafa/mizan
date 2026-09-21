# Learning macro effects first, then solving backwards

Completed a different prediction formulation. A quadratic empirical model learns glucose responses from known carbohydrate, protein and fat amounts plus premeal glucose state, using 652 CGMacros meals from 34 participants. For each BIG IDEAs development person, four earlier labeled meals adjust a personal response gain and time-dependent offset. Numerical optimization then finds nonnegative grams explaining each later glucose response.

The quadratic interactions, common personal gain, response offset and optimization penalties are modeling assumptions, not established physiological laws. The three fixed penalty strengths were specified before this run. Each optimization used three starting points and chose its result using glucose-fit objective only, never query macro labels. The designated primary penalty was 0.1. Query true grams were used only after decoding for evaluation and a forward-model diagnostic. The eight reserved participants were not accessed.

## Results on the same 65 later development meals

| Penalty pulling toward onboarding macro median | Joint successes within 10% | Carbohydrate MAE | Protein MAE | Fat MAE |
|---|---:|---:|---:|---:|
| None | 0/65 | 80.0 g | 50.1 g | 50.9 g |
| 0.1, primary | 0/65 | 39.0 g | 17.6 g | 15.4 g |
| 1.0 | 0/65 | 39.4 g | 15.6 g | 13.7 g |

All 195 selected optimization results converged numerically. Convergence is not evidence of accurate macros or a globally unique solution. The target remains unachieved.

## Why glucose-curve fit alone is misleading

Without the onboarding penalty, median glucose-curve RMS error was 10.0 mg/dL. Feeding the actual recorded grams through the same personally adjusted forward model instead gave median error 17.7 mg/dL. The optimizer can therefore find wrong grams that fit observed responses better than this model's predictions at true grams.

For example, participant 005 on March 2 at 11:00 had recorded **9.6 g carbohydrate, 17.3 g protein and 9.0 g fat**. The unpenalized decoder returned **60.5, 79.7 and 24.0 g** while fitting glucose to **2.91 mg/dL RMS**. The forward model at the true grams had 5.82 mg/dL RMS error. This example was selected after evaluation as the lowest decoded-curve error, not as a representative accuracy estimate.

This directly exposes a problem in this empirical forward model and its inverse: optimizing glucose reconstruction is an unreliable substitute for testing gram accuracy. It does not establish that human physiology itself cannot distinguish these amounts. Errors could arise from model misspecification, insufficient calibration, noisy reference labels, measurement variability or omitted physiological state. This experiment does not identify which cause dominates.

Penalizing implausible departures from onboarding amounts reduces gram errors while worsening curve reconstruction. That tradeoff supports checking the target metric directly and against no-sensor controls, rather than treating a visually convincing curve fit as proof of macro recovery.

## Verification

Source and target features are the same checked artifacts used in the preceding transfer experiment. Calibration response windows finish before query meals; population fitting uses source data only. Independently recomputed all 195 tolerance flags from predicted and recorded grams, checked convergence flags, and inspected exact failing rows. Each penalty evaluates the same 65 meals. This is an adaptive development experiment, not untouched validation.

- [All gram predictions and curve-fit errors](predictions.csv)
- [Aggregate results](summary.json)
- [Calibration chronology and fitted personal gains](split_manifest.json)
- [Run provenance](run_manifest.json)
