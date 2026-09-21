# Timing-tolerant daily glucose matching

Allowing glucose curves to shift locally in time did not improve earlier validation. The selected configuration used no timing shifts, and its later result did not beat the existing passive ensemble.

| Allowed local timing shift; best configuration at each limit | Earlier validation daily MAPE |
|---|---:|
| None | 21.06% |
| Up to 60 minutes | 22.56% |
| Up to 120 minutes | 22.71% |

The selected unwarped matching model obtained 22.31% MAPE and 15/44 later days within 10%. The existing passive ensemble remains at approximately 18.40% MAPE. The new configuration is exploratory, not a replacement for the better existing model.

Each 30-hour trace was centered on its own 10th percentile while retaining glucose-change amplitudes. Banded dynamic time warping compares all 120 quarter-hour readings with squared local costs. Distance normalization divides accumulated cost by 120; this is a specified matching distance, not a measured physiological quantity. Band zero was verified to reproduce ordinary root mean squared distance. All distance matrices were symmetric with zero diagonals.

27 fixed configurations varied timing allowance, similarity bandwidth (5/15/30 mg/dL), and use of personal versus pooled residual neighbors. A personal-mean baseline was included. Pooled target residuals were centered within each participant. Selection used 33 earlier chronological queries with nonoverlapping same-person history, retaining the allowed other-person training pool. Settings were saved before later scoring.

Distances use sensors only; no meal timing, food identity, or query macro label is involved. Computing a distance matrix for all sensor rows fits no cross-row parameter, and predictions index only allowed training neighbors. All 44 later days were retained. Replacing query targets with a sentinel left predictions unchanged. The same development outcomes have been repeatedly inspected, so these are not fresh validation results.

This tests one concrete hypothesis: timing flexibility in nearest-trace matching might fix large errors. It did not help with this representation and calibration rule. It does not rule out all timing-aware models or establish impossibility of carbohydrate inference.
