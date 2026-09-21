# Exact duplicate curves in the Stanford public release

The attempted extension to XB19 revealed identical predictions for different repeat IDs. Fingerprinting every session's full 40-point glucose vector found **10 exact duplicate pairs**, all in XB19: 20 session IDs represent only 10 distinct curves. Across the entire downloaded table there are 588 session IDs but 578 unique glucose vectors. Distinct IDs and unique time-within-session keys had therefore not been sufficient to establish independent repetitions.

Critical pairs for the current experiment:

- Rice repeats 3 and 4 are exactly identical.
- Rice+Fat repeats 1 and 2 are identical; repeats 3 and 4 are identical.
- Rice+Protein repeats 1 and 2 are identical; repeats 3 and 4 are identical.

Consequently XB19 has only two distinct rice curves and two distinct curves for each of the added-fat/protein conditions. Averaging two nominal supplemented repeats averages the same values twice. Using rice repeat 3 for calibration and rice repeat 4 for evaluation reuses exactly the same signal. The earliest-available two-person experiment is invalid as an independent-repeat comparison and has been marked accordingly. No success claim should rely on it.

The cause could be upstream record duplication or export/processing behavior; the public table alone does not establish which. No claim is made about author intent or the original raw sensor records. The fingerprint audit covers exact equality, not near-duplicates or all possible leakage.

XB6 has no exact duplicate curves in this audit. The earlier one-person experiment remains the applicable result: two calibration repetitions yielded 0/5 fat and 1/5 protein added-dose predictions within ±10%, with only 1/3 supplemented protein sessions correct. Cross-condition dates and true raw traces remain unavailable in the downloaded table.

Full session fingerprints and all duplicate pairs are saved alongside this report. This finding narrows the usable repeated-calibration evidence; it does not demonstrate that all CGM inference is impossible or meet the requested ±10% goal.
