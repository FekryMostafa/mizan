# Individual fat-heavy, low-carbohydrate meal audit

## Scope

Selected every labeled CGMacros event with **at least 10 g fat and at most 10 g carbohydrate**: 22 records. Ranked them by fat's share of energy calculated from the recorded carbs/protein/fat using 4/4/9. Examined both CGM traces from one hour before to six hours after each event. All 22 were plotted; none was selected for having a desired glucose response. No model was trained and no gram estimates were generated.

Measured glucose change relative to the preceding ten-minute median. Numerical response windows stop before the next logged food event. Subsequent traces remain visible but shaded on plots. Source data are already interpolated minute-level CGM data; no new missing-value filling was performed. Earlier meals can still affect the response even if they occurred several hours before.

## Most informative individual cases

### Repeated 18 g fat / 7 g carbs / 6 g protein snack, participant 14

Two entries have identical macro labels and reported 100% consumption. They may be the same food, but photo/ingredient identity was not verified. Both have more than nine hours until the next logged food, allowing an extended response inspection.

| Recording date | Libre maximum rise, first 3 hours | Dexcom maximum rise, first 3 hours |
|---|---:|---:|
| May 15 | +50 mg/dL at 122 min | +70.6 mg/dL at 133 min |
| May 17 | +8.8 mg/dL at 87 min | +22.3 mg/dL at 148 min |

There is a large delayed rise on May 15 and a considerably smaller response on May 17. Both devices show that difference, although their magnitudes differ.

Context also differs. On May 15, a dinner labeled 80C/39P/32F was 280 minutes earlier. On May 17, dinner was 65C/7P/16F, 183 minutes earlier. Glucose was falling before both snacks, more steeply on May 17. Libre baselines were approximately 101 versus 88 mg/dL; Dexcom 127 versus 110 mg/dL. Activity data are present: median source METs values over the following three hours were 12 versus 10 (the source uses ten times METs), and median heart rates were 77 versus 75. These descriptive context differences do not establish which factor caused the response difference.

**Interpretation:** these are the best low-protein, fat-heavy repeated-label examples found. They support investigating delayed responses and context, while directly showing why one personal curve cannot be treated as a stable dose-to-response conversion.

### 14 g fat / 2 g carbs / 4 g protein snack, participant 10

Before the next food at minute 73, glucose rises +20.4 mg/dL on Libre at minute 51 and +36.5 mg/dL on Dexcom at minute 64. The earlier lunch was 188 minutes before and contained 94C/44P/20F. Both curves were declining before the snack. The next snack contains 24C/21P/8F.

**Interpretation:** a real observed early rise, but neither fat-specific attribution nor an isolated late response is available.

### 22 g fat / 7 g carbs / 2 g protein event, participant 2

This initially looks like an excellent high-fat, low-protein example. However, it occurred **20 minutes after a dinner with 90 g carbs, 33 g protein and 19 g fat**. Glucose was already rising. Treating its subsequent peak as a response to the 22 g-fat entry alone would be misleading. It is better understood as an overlapping eating episode unless original logs establish otherwise.

### 26 g fat / 4 g carbs / 9 g protein snack, participant 34

Before another food event 53 minutes later, Libre rises only about 2 mg/dL above baseline; Dexcom stays below its premeal baseline. Later portions of the trace are contaminated by the subsequent food. This does not establish that fat has no later effect.

The same participant also has two 13F/3C/10P snacks, but the next food follows after only 51 and 15 minutes. They cannot cleanly expose delayed fat effects.

### 90 g fat / 8 g carbs / 58 g protein dinner, participant 28

Both devices show a sustained rise extending into hours 3–5, with no new logged food for over twelve hours. However, the large protein quantity prevents treating this as mainly an isolated fat challenge. Amount Consumed is absent for this participant, so 90 g cannot be silently treated as a verified consumed amount. A second low-carb dinner in this participant (12F/7C/41P) has a falling later response, but these meals differ in several important respects and do not constitute a matched fat-dose experiment.

## Additional data-quality issue

Several candidate records have Amount Consumed values of 200, 400 or 600, while another has 2 and two records have missing values. The dictionary describes this field as a percentage. Do not multiply or divide macro labels by these values without resolving the original entry conventions. These records remain visible in the inspection and are not treated as reliable dose labels.

## Conclusion for the proposed model

Low-carb, fat-heavy meals do not uniformly produce flat CGM curves. Some have substantial delayed rises. But the highest-value repeated example has a much different response on the second day. Earlier intake, premeal trends, remaining carbs/protein, sensor behavior and label fidelity all matter.

Use the repeated 18 g-fat pair and the 14 g-fat snack as explicit stress tests for a future model. Do not calibrate a fat-to-glucose conversion from either single curve. The matched 10.5-versus-42 g-fat breakfasts remain the stronger training comparison because the other macro labels are held fixed and there are many more repetitions. Success there would still need testing on these low-carb cases.

## Outputs and provenance

- `repeated_18g_snack.png`: the most informative repeated-label case.
- `cases_1.png` through `cases_4.png`: all 22 candidate events, both devices, nearby food marked.
- `measurements.csv`: baselines, premeal trends, window coverage and response features.
- `nearby_food.csv`: preceding and subsequent nutritional labels within six hours.
- `selected_events.csv`: selection inventory including unmodified macro/consumption fields.

Derived from the original local CGMacros participant CSV files. Source files were not modified. Calendar dates are the dataset's shifted dates. Conclusions are descriptive and do not establish causal fat effects or prediction accuracy.
