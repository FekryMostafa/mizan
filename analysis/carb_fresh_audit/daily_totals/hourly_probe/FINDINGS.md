# Hourly intake estimation summed into daily carbs

Resumed the investigation within CGMacros, using a different supervision strategy rather than repeating the prior daily regressions. The objective remains unmet.

Split each of the64 known calibration days into24 hourly intake targets using its recorded meal labels:1,536 hour bins,248 with nonzero recorded carbs. These are not independent new observations; adjacent glucose windows overlap and bins share people/days. At prediction time the model receives glucose windows and optionally clock time, not the query day's food entries. Sum24 hourly predictions into the daily target.

The glucose window runs from one hour before to four hours after each hour's start, sampled at15-minute spacing. Inputs include raw glucose and deviations from the preceding-hour median. Daily output therefore uses following-day glucose. Clock-only, CGM-only and CGM-plus-clock controls were compared using Poisson gradient boosting with7/15 leaves and raw versus personally offset daily sums. Personal offsets used calibration labels only; fitted calibration residuals are not an independent training accuracy estimate.

Kept the same64 training days and44 later days. Chose settings on33 earlier validation days with all other participants' original calibration data retained and the target person's future/overlapping days excluded. The clock-only offset model won, with25.20% earlier validation MAPE. Its later result is14/44 within±10%,20.58% MAPE and39.65 g MAE, exactly the matched personal daily-mean baseline. A clock-only model produces the same24-hour sum each day, so its calibrated offset algebraically reduces to that baseline.

This result does not establish that meal-level supervision is useless. It shows that this particular hourly mapping failed to add reliable signal beyond timing habits under earlier-day selection. The competing CGM configurations and scores are saved in validation.csv. No glucose model was promoted because of later outcomes.

Verified hourly carb labels sum to each day's existing target before training. All44 evaluation days remained present; serialized model replay was exact and changing query targets did not affect predictions. Every consumed participant source hash remained unchanged. The best prior development MAPE remains18.40%; no result here reaches10%.
