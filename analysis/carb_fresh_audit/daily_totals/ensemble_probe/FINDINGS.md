# Can existing daily CGM models be combined to meet ±10%?

Not with the combinations tested. The learned convex ensemble gets14/44 later days within±10%, MAPE19.93%, MAE40.84 g. The prespecified equal-weight control gets16/44, MAPE18.40%, MAE38.10 g. The equal-weight MAPE is slightly lower than the previous18.94%, but this repeatedly examined development set does not establish prospective accuracy or the requested10% target.

Used the31 existing full-pool candidates, including the personal mean baseline, across three representations and ridge/kernel penalties. Learned nonnegative weights summing to1, each capped at0.25, by minimizing absolute percentage error on33 earlier validation predictions. Five weights were nonzero. Weights and the complete later candidate prediction matrix were written before later scoring. The equal-weight model was specified in advance as a control; it was not the model selected by earlier performance.

## A concrete limit of averaging these candidates

After scoring, inspected each day's minimum and maximum among all31 candidate predictions. Eight of44 days cannot reach the±10% interval with any convex average of these candidate outputs, even if an oracle selected different weights for each day. This unrestricted per-day diagnostic is more permissive than the actual fixed, capped ensemble.

Examples:

- Actual513 g: candidate predictions297.60–377.98 g; required461.7–564.3 g.
- Actual150 g:197.80–408.11 g; required135–165 g.
- Actual122 g:153.73–227.80 g; required109.8–134.2 g.
- Actual297 g:44.15–206 g; required267.3–326.7 g.

The other36 days merely have ranges intersecting their tolerance interval. This does not mean an algorithm can identify the needed weights. These oracle range results use answers and are not prediction performance. They restrict this candidate family only, not all possible CGM algorithms.

The pattern is systematic shared error on certain large changes, not just random errors that cancel when models are averaged. All44 days remain evaluated, and current food labels were used only for scoring/range diagnostics. The objective remains unachieved.
