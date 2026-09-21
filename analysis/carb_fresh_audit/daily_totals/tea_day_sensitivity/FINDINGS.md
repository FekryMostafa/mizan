# One additional calibration day: tea-label sensitivity

Accepting the recorded zero-macro tea and adding P27 June11 increased training from64 to65 days. It did not improve daily percentage error:18.395% became18.530%, with16/44 days within10% in both runs. Mean absolute error decreased slightly from38.095 to37.711g; that is a different metric.

The effect on P27 illustrates the remaining problem:

| Later date | Recorded carbs | Original prediction | Added-day prediction |
|---|---:|---:|---:|
| June17 | 204g | 166.08g | 198.19g |
| June18 | 133g | 172.67g | 210.82g |

The added277g calibration day raised both predictions. It fixed the first day's underprediction while worsening the second day's overprediction. Additional history can change the personal average without resolving which later day had greater intake. Since the ensemble shares training across people, adding this day also affects other participants; all44 outcomes were scored.

The source-zero beverage recordCGMacros-027:2388 has a tea photo. This run accepts its existing zero label as a sensitivity assumption; no additives or actual intake can be established from that photo alone. Other meals on the added day already pass the strict full-consumption rule. No source labels were edited or estimated. Photos were not model inputs.

Re-extracted all required glucose, HR/activity, previous-day and next-morning features and verified them against all6 existing P27 sensor rows within1e-8, including missing values. The new30-hour glucose window was complete and ended before later evaluation. The original ensemble result was reproduced within1e-8g. Query-label mutation left predictions unchanged, the raw participant file hash was unchanged, and all44 later outcomes were retained. Model settings and31-member uniform weights were fixed.

The strict-data reference remains18.395% and the goal remains unmet. This is the same repeatedly inspected development evaluation, not independent validation. The sensitivity result is preserved separately and is not promoted as a new best result.
