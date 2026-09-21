# P13's147 g afternoon event: raw review

The original row is2024-02-02 15:41, dinner,147 g carbohydrate,50 g fat,84 g protein,1,289 kcal,100% consumption. The archived photo shows a mixed plate with meat, flatbread-like food, cabbage, an orange and a drink. It does not establish portion weights or justify changing147 g. The image was inspected only as source evidence, not used as a predictor.

Libre readings fall from118 at15:11 to109.3 at the event, then rise to142.7 at17:11. A snack with41 g carbs is recorded at18:19, so later responses can overlap. The existing inter-device timing discrepancy remains; neither device was assumed ground truth.

Compared five earlier personal dinners using identical−30 to+180-minute sampling. The target event's peak rise above its two-point premeal baseline is27.07 mg/dL; an earlier54 g dinner gives27.53 mg/dL. That earlier dinner also has50 g fat, but40 g protein rather than84 g. Another112 g dinner gives38 mg/dL rise, and a70 g dinner46.97 mg/dL. These are different full traces, not identical physiological responses, but peak height does not order their doses.

Target-window mean HR/activity are90.93 bpm and1.63 kcal/min, within the spread of the five earlier dinner windows. Their averages do not identify a unique outlying state. Detailed time-varying measurements are saved in raw_15min.csv and dinner_raw_traces.csv; averages do not rule out activity effects.

## Training support

P13 has19 meal examples in the64-day calibration subset, with maximum112 g carbs. Across267 training events only7 contain at least120 g. A post-hoc descriptive bin of carbs≥100 g, fat≥40 g and protein≥60 g contains just2 events, both from P4. These label-based counts diagnose coverage; they are not deployable food features or causal proof.

Checked whether training can expand inside CGMacros without consuming later labels. There are843 candidate full-consumption meals from35 participants after excluding all evaluation participants' events whose four-hour windows reach the first later-day cutoff. Other participants do not contribute to the44-day evaluation. This pool contains only8 meals≥120 g and still only2 in the descriptive high-carb/fat/protein bin. So expanding the pool adds many typical examples but little high-dose coverage.

This is an inventory, not a trained result: four-hour signal completeness and precise validation-fold membership still need checking before use. It provides a concrete next experiment within the existing dataset: train from valid individual meals even where other food records make their day unsuitable as a daily training target, while preserving the same daily evaluation. The147 g label remains unchanged, and the±10% goal is not achieved.
