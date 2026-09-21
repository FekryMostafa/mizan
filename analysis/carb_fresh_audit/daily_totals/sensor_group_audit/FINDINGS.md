# Separate glucose and HR/activity controls

Correct glucose-day pairing matters more than HR/activity-day pairing to the current fixed ensemble. This supports continuing glucose-focused work, but does not demonstrate 10% accuracy or a causal measure of intake.

| Input pairing | Median daily MAPE | Shuffles matching or beating real pairing |
|---|---:|---:|
| Correct pairing | 18.395% | — |
| Glucose shuffled, HR/activity intact | 21.275% | 0/100 |
| HR/activity shuffled, glucose intact | 18.762% | 22/100 |

Glucose shuffles ranged from 18.963% to 24.953%. HR/activity shuffles ranged from 17.531% to 20.000%. The lowest shuffled score is not a deployable improvement: it uses deliberately mismatched days and is identified after looking at outcomes.

Each control uses 100 paired random seeds and refits all 31 fixed ensemble models. Feature rows are permuted within each participant, separately within the 64 training and 44 later days. All 150 glucose-derived features are permuted together, or all 68 HR/activity features together. Every nonpermuted column is asserted unchanged, including labels, identities, dates and the other sensor group. The original prediction reproduces within 1e-8 g. All 44 outcomes remain included.

The ensemble architecture favors glucose: glucose-summary and glucose-sequence model families have no HR/activity inputs; HR/activity enters only the summary/context family. These results therefore describe this algorithm's reliance, not the maximum information available from each sensor. Selective shuffling can also create unrealistic combinations by breaking cross-sensor coherence. The same development days have been repeatedly inspected, so this is descriptive evidence, not an independent significance test.

The result narrows the current investigation: correctly paired glucose contains useful predictive structure for this algorithm, while another generic HR/activity correction appears a weaker route. It does not show that all carbohydrate grams are identifiable. The unchanged passive result is 18.395% MAPE with 16/44 days within 10%, leaving the goal unmet.
