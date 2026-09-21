# Evidence checkpoint: macro inference within 10%

## Current CGM-only update

Latest data-quality update: an additional Stanford release was downloaded and audited. It has 588 session IDs but 578 distinct curves, with 10 exact duplicate pairs in one participant. The attempted two-person repeated-calibration extension was invalidated because it reused an identical rice signal across calibration/evaluation. The unaffected one-person comparison remains below target. See [Stanford duplicate findings](stanford_cgmdb_audit/DUPLICATE_FINDINGS.md). A separate [duplicate audit](macro_features/duplicate_audit/FINDINGS.md) found no exact or six-decimal rounded full-curve duplicates among the 738 earlier eligible CGMacros/BIG IDEAs records.

The user subsequently narrowed work to CGM. The older outreach impediment below is historical and is not a requirement for continuing CGM analysis. Recent completed work supersedes its stopping point:

- [Carbohydrate feature conversion](macro_features/carb_conversion/FINDINGS.md): 6/65 later meals within ±10%, mean absolute error 39.68 g.
- [Full-curve audit](macro_features/curve_audit/FINDINGS.md): selected examples differ in late response, but simple late-response ordering does not reliably generalize across comparable peaks.
- [Separate personal dose calibrations](macro_features/personal_dose_repeat/FINDINGS.md): 3/52 carbohydrate, 3/50 fat, 4/56 protein predictions within ±10%. Calibration contrast magnitude and response center vary between repeats.
- [Repeated calibration coverage](macro_features/repeat_calibration_coverage/FINDINGS.md): averaging two personal repetitions per dose leaves no later exact-dose evaluation meals in the inspected eligible data. The full CGMacros event table also contains at most two of each specific reference dose per person.

The ±10% objective remains unachieved. Additional repeated-dose records are needed to test that particular multiple-repeat calibration hypothesis; this does not rule out other exploratory methods using existing data. Reserved BIG IDEAs participants remain unopened. No model is running in the background and no new outreach, hardware purchase or human collection has occurred.

Subsequent [population-assisted full-curve calibration](macro_features/pooled_dose_direction/FINDINGS.md) produced 6/52 carbohydrate, 5/50 fat and 8/56 protein hits. Borrowing other people's response directions did not improve mean error over personal full-curve directions. All 474 primary/control predictions were independently reproduced; the target remains unmet.

## Earlier checkpoint, retained for provenance

8 September 2026. The original goal remains unachieved. No result establishes impossibility for every potential sensor or algorithm.

| Requirement | Evidence status |
|---|---|
| Predict continuous carbohydrate, protein and fat grams | Implemented and tested, but prediction errors remain too large. |
| Each macro within 10% on later meals | Not achieved. Latest linear and nonlinear glucose/EDA/temperature comparisons each have 0/65 joint successes. |
| Personal calibration | Implemented with four earlier meals and complete response windows before queries. Additional calibration experiments have not established the target. |
| Generalization beyond memorized recipes | Not established. The earlier successful pizza estimate repeated an onboarding macro vector and was also solved by a no-sensor prior. |
| Without overfitting | Development splits and controls reduce leakage; repeated analysis still means development performance is not fresh validation. Eight BIG IDEAs participants remain reserved. No model merits a final claimed success test yet. |
| Reliable actual-intake references | Incomplete. Current labels are logged nutrient estimates with documented inconsistencies, not independently verified actual macro intake. |
| Sweat-based alternative | Public electrical traces extracted, but dose/participant linkage and true premeal baselines are missing for the inspected meal traces. No gram-inference validation possible from those alone. |
| Complete wearable/day-level operation | Not validated. Current experiments use logged meal times and selected isolated response windows. Automatic meal detection and daily total accounting remain additional requirements for the original product vision. |

The recent runs are terminal: the downloads and linear/nonlinear comparisons completed. There is no model running whose completion will resolve the missing evidence.

## Current impediment

We do not have a validated mapping meeting the requested accuracy or the new paired dose/repetition records needed to investigate the remaining ambiguity directly. Further unmotivated parameter changes on the repeatedly inspected development set would not establish the requested result. This is an evidentiary impasse for the current workflow, not an information-theoretic impossibility claim or a claim that all research avenues are exhausted.

Two concrete existing-data routes are prepared in [author_data_requests.md](../experiment/author_data_requests.md). Sending those emails requires explicit user authorization; an automatic goal-continuation message is not authorization. The earlier WATCH request was found in Sent, with no matching response in the bounded Gmail search performed this session. The new requests have not been sent.

Work can move forward when the user authorizes the requests, supplies a relevant author reply/data release, or provides newly collected paired records. Author permission or a reply alone is not success: received data must be audited for usable dose labels, repeated sessions, timing, calibration and independent evaluation. The recording format for a prospective collection already exists in [experiment/README.md](../experiment/README.md); it is not a validated sensor or a prescribed human challenge protocol.

## Supporting records

- [Linear added-signal comparison](big_ideas_audit/skin_model/FINDINGS.md)
- [Nonlinear added-signal comparison](big_ideas_audit/skin_nonlinear/FINDINGS.md)
- [Raw failure comparisons](cgm_fat_audit/failure_analysis/FINDINGS.md)
- [Reference-label audit](big_ideas_audit/label_audit/FINDINGS.md)
- [PolyCORE release audit](polycore_audit/FINDINGS.md)
- [MealMeter release audit](mealmeter_audit/FINDINGS.md)

This checkpoint is a navigation and decision record. The underlying predictions, raw source hashes, splits and source releases remain the authoritative evidence.
