# Repeated calibration using earliest available sessions

**Superseded as an independent-repeat comparison:** a subsequent exact-curve audit found that XB19's rice repeats 3 and 4 are identical at all 40 glucose points, causing calibration/evaluation signal duplication. Rice-plus-fat repeats 1/2 and 3/4 are also identical within each pair, as are rice-plus-protein repeats 1/2 and 3/4. These rows cannot be counted as independent repetitions. The two-person results below are retained only to document the detected problem; they are not valid independent-repeat evidence. See ../DUPLICATE_FINDINGS.md. The original XB6-only comparison is unaffected by these exact duplicates.

The preceding diagnostic required explicit repeat identifiers 1 and 2, excluding XB19 because rice repeat 1 was absent. This follow-up uses the earliest available sessions within each condition, so both XB19 and XB6 contribute. The formula, baseline and feature representation are unchanged. This is a disclosed development-protocol revision, not an untouched validation claim.

For XB19, rice repetitions 2 and 3 provide two-session calibration, and rice repetition 4 is excluded for evaluation. Supplemented repetitions 1 and 2 provide calibration, and 3 and 4 are evaluated. For XB6, calibration and evaluation remain exactly as before. The one-session comparison uses the first of these calibration sessions while retaining the same evaluation records. No test labels select parameters.

| Added nutrient | Calibration sessions per condition | Excluded evaluation sessions | Within ±10% | Mean absolute error |
|---|---:|---:|---:|---:|
| Fat | 1 | 8 | 0/8 | 7.22 g |
| Fat | 2 | 8 | 0/8 | 6.45 g |
| Protein | 1 | 8 | 0/8 | 4.58 g |
| Protein | 2 | 8 | 2/8 | 4.63 g |

Each row includes five supplemented sessions and three rice-only controls across two people. For two-session calibration, supplemented-session hits alone are 0/5 for fat and 1/5 for protein. The other protein hit is a zero-added-protein control, with predictions clipped below zero. Fat error on supplemented sessions worsens from 8.77 to 9.52 g; its aggregate improvement comes from controls. Protein supplemented-session error changes from 4.49 to 4.42 g.

All 32 predictions were independently recomputed within 1e-8. All 20 predictions for XB6 reproduce the previous run. Calibration and evaluation session identifiers are disjoint, with a saved split manifest. Cross-condition chronological separation is still unverified because public dates are absent; within-condition repeat ordering does not resolve it.

This removes the unnecessary reliance on contiguous repeat identifiers but does not rescue the tested calibration rule. The result concerns nominal added doses, not fully verified total macros. Only two people, retrospectively smoothed traces, a single supplemented dose per macro, and missing cross-condition dates prevent a credible general ±10% claim. No new doses or arbitrary mixed-meal performance were validated. The full original objective remains unmet.
