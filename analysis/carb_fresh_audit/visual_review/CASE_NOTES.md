# Direct visual review of every participant

Reviewed all 13 rendered pages, two participants per page, covering all 52 evaluated meals and their 52 same-dose calibration meals. Curves show Libre glucose, heart rate, Fitbit calorie estimates, and METs or Intensity from three hours before to three hours after each logged meal. Outcomes refer consistently to the earlier nested feature-combination model (9/52 hits), not whichever model happens to do best per meal. No new prediction model was fitted in this review.

These are visual observations with hypotheses, not established causal explanations. Curves can look similar without implying that the entire response or baseline matches precisely.

| Person | Direct observation | Calibration implication to investigate |
|---|---|---|
| 27 | Low-dose repeat is visually close and succeeds. High-dose later excursion is weaker despite activity in both records; model emits zero. | A zero prediction cannot be interpreted as no meal. Inspect response scale and activity timing, not average HR alone. |
| 32 | Later low-dose Libre trace spends long stretches at 40; later HR largely or entirely absent. | Treat the lower sensor bound as censored data. Missing HR cannot be interpreted as rest. |
| 35 | High-dose glucose rises/falls similarly and succeeds; low-dose later rise is much larger and fails. | Same demographics support a success and failure. Low-dose calibration is not representative of that later curve. HR is incomplete even for the success. |
| 5 | High-dose repeat closely resembles calibration and succeeds despite higher later HR. Low-dose timing is similar but later amplitude grows and model overestimates. | No universal high-HR correction. Preserve personal dose anchors while checking amplitude change. |
| 36 | Low-dose shapes look reasonably similar but model predicts about 54 for 24. For high dose, calibration HR/activity rises during the early decline; later HR is lower while glucose stays elevated. High-dose prediction succeeds. | Both model-conversion error and activity-timing hypotheses are present. A hit does not prove the physiological explanation is right. |
| 38 | Both low-dose shapes are broadly similar; high-dose later response is smaller. Activity occurs in both. Both predictions regress toward the middle. | Inspect conversion bias before adding hidden physiological explanations. |
| 2 | Low-dose repeats resemble each other. High-dose later response is larger/longer but the combined model underestimates it. | A simple 'we missed a small spike' explanation is wrong for this high-dose miss. |
| 49 | Later high-dose premeal HR is substantially elevated relative to calibration and its glucose peak is smaller; low-dose repeat grows modestly. | Prior sustained activity is a plausible context variable; cannot assign cause or grams from this comparison. |
| 41 | Later glucose responses are smaller for both doses; later HR is absent while calorie estimates sit near baseline. | Do not equate flat estimated calories with confirmed inactivity. Activity correction is unavailable for these records. |
| 1 | Later high-dose meal follows more premeal activity; calibration has a much larger late activity bout. Low-dose glucose peaks look similar despite a miss. | Relative timing matters; overall response still suffers conversion bias. |
| 34 | Low-dose prediction succeeds with similar postmeal peak but different premeal glucose and missing portions of HR. High-dose later peak is smaller and fails. | Similar background conditions are not necessary for a hit; validate calibration quality around the actual baseline interval. |
| 43 | Curves broadly repeat, with amplitude/timing differences. Later activity is not consistently greater. Both estimates pull toward the middle. | No obvious activity-only explanation for both misses. |
| 44 | Low-dose later HR is missing; calibration shows substantial activity during glucose decline. Later high-dose HR is lower early and glucose remains higher later. | Possible activity-timing contrast for high dose; low-dose activity state is unknown. |
| 10 | Low-dose later response is larger; high-dose later response is smaller. HR/activity contrasts differ between meals. | A single person-level multiplier cannot fix opposite response changes. |
| 9 | Low-dose curves resemble each other. High-dose timing shifts earlier with different premeal activity. Both estimates miss. | Test timing-context interaction rather than a universal onset shift. |
| 6 | Calibration low-dose premeal activity is conspicuously stronger; high-dose calibration activity accompanies the declining response. Later glucose remains higher near the end. | A candidate for activity-aligned comparisons, not evidence for a fixed HR-to-grams ratio. |
| 3 | High-dose glucose curves are especially close, yet prediction is about 50 for 66. Calibration has a late activity bout largely absent later. | Strong example of a conversion failure despite a recognizable repeat curve. |
| 14 | Both glucose pairs are broadly similar despite different premeal HR/activity bouts; both miss. | Similarity alone is not being preserved by the population conversion. |
| 4 | High-dose repeat resembles calibration and succeeds despite a later premeal activity bout. Low-dose later peak is smaller but model overestimates. | More activity is not synonymous with failure; low-dose conversion deserves scrutiny. |
| 8 | Low-dose delayed peaks resemble each other and still miss; high-dose responses are both late with different tails. | Recognizable delayed responses are not enough for this model's precise grams. |
| 39 | High-dose broad rises/falls resemble each other and succeed. Low-dose also looks similar but is overestimated. | Dose-dependent conversion bias remains within one person. |
| 31 | Low-dose peak timing is similar; high-dose responses have multiple humps with different timing. Activity timing also differs. | Multiple response phases need comparison, but no causal explanation is established. |
| 17 | Later low-dose record has substantial late activity, with a small glucose excursion in both records. Neither estimate hits. | HR/activity may explain some tail changes but does not rescue gram inference by inspection. |
| 45 | Low-dose broad response is repeatable and succeeds. High-dose calibration calorie/MET estimates remain near baseline despite nonflat HR; later estimates show activity. | Cross-channel consistency needs auditing before treating either activity estimate as truth. |
| 42 | Later high-dose response is delayed and smaller; later HR is generally lower, not higher, during much of the window. | The smaller response is not explained by a visible increase in contemporaneous activity. Intensity is available even though METs is absent. |
| 33 | High-dose glucose curves closely resemble each other and succeed, with similar postmeal HR despite different prior activity. Later low-dose HR and calorie estimates are missing. | Good high-dose repeat; no valid activity explanation for the low-dose miss. |

## What the successes share, and what they do not

The nine successful meals belong to nine people; each of those people also has a failed meal. Ages span 24–61, BMI approximately 25.0–42.4, with six women and three men. Their median recorded postmeal mean HR is about 85 bpm, versus 84 for failures. The ranges overlap; this does not identify a demographic or HR threshold. Eight successes have at least 90% postmeal HR coverage; one has only 31%. Seven failures have less than 90% coverage. Demographics and these summaries are descriptive, with correlated meals per person, not a significance test.

Several successes show a recognizable repetition of the calibration glucose shape (P4, P5, P27 low, P33 high, P35 high, P39 high, P45 low). Similar-looking repetitions also fail (notably P3 high, P8 low, P14, P38 low). Therefore we cannot declare that repeatability, inactivity or matched HR uniquely identifies success.

## Concrete implications

1. Preserve missingness and sensor censoring explicitly. Do not turn missing HR or baseline-only calorie estimates into a resting-state label.
2. Compare sustained activity before the meal, during the rise, and during the fall separately. P36 and P49 motivate this hypothesis; P5 and P42 caution against a universal correction.
3. Investigate whether the learned conversion unnecessarily moves recognizable personal repeats toward an average dose. This is a model issue to test, not an excuse to relabel observed failures as successes.
4. A calibration protocol should capture repeated known meals under distinguishable activity contexts. The present two-dose, two-repeat records cannot establish a personal activity-to-glucose-uptake conversion just by visual inspection.

The dictionary says METs is stored multiplied by ten; plots divide it by ten. Intensity is kept separate. Fitbit calories are estimates per minute, not measured glucose oxidation. Baseline demographics/labs are not contemporaneous measurements of meal metabolism. No inference of grams burned, insulin action or a medical diagnosis is claimed.
