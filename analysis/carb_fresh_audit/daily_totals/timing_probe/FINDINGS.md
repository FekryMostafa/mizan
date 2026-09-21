# Relative sensor-clock sensitivity

Applying the earlier-estimated relative offsets to derived Libre features changed the fixed glucose-only model from15/44 to16/44 later days within±10%, and from21.00% to20.34% MAPE. MAE changed from42.59 to41.84 g. This modest improvement does not reach the10% goal or beat the prior equal-weight ensemble's18.40% development MAPE.

Used the same64 earlier calibration days and44 later evaluation days. Re-extracted daily glucose and following-six-hour summaries directly from original Libre minute records. Under the hypothesis that Libre rather than Dexcom is displaced, aligned Libre at clock t was taken from the original reading at t+lag. Lags were previously estimated only from earlier paired sensor data. No lag was selected using later carb labels, and model hyperparameters remained fixed at the prior glucose-only kernel/reg0.1 choice.

The relative sensor alignment does not identify which CGM clock actually agrees with food logging. This is therefore a sensitivity experiment, not a verified source-timestamp correction. It also uses a second sensor to estimate onboarding offsets. Positive offsets require data after the nominal06:00 reporting time; the largest positive offset used was45 minutes, so these predictions may require waiting until06:45. All44 shifted observation windows were complete.

## What changed in prominent failures

P8's148 g day improved from194.94 to175.79 g but still missed±10%. P9's132 g day worsened from211.85 to213.76 g. P13's297 g day improved from156.02 to163.43 g, while its294 g day worsened from160.80 to147.30 g. Thus the relative timing discrepancy does not explain those large dose errors on its own.

Every re-extracted zero-shift feature matched the stored reference within1e-8. Original predictions replayed; source participant file hashes remained unchanged. Replacing current query labels left predictions identical. No source timestamps or meal labels were modified, and all44 days stayed in scoring.

The objective remains unmet. The audit found a real relative alignment pattern, but greater sensor-to-sensor correlation has not translated into accurate daily carbohydrate recovery under this tested conversion.
