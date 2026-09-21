# Passive daily multiscale glucose features

The new features did not improve earlier chronological validation, so they were not selected for the later-day prediction. The 10% target remains unmet.

This experiment adds 60 sensor-only descriptors: changes across 15, 30, 60, 120, and 240 minutes, their magnitude and direction, autocorrelation, and spectral power across fixed time bands. Both the 24-hour day and the 30-hour window through next morning are described. No query meal timestamps, food identities, or macros are inputs. Spectral descriptors measure variation, not absorbed grams; they cannot by themselves separate overlapping meals or identify physiology.

| Feature family, best earlier-validation configuration | Earlier daily MAPE | Earlier days within 10% |
|---|---:|---:|
| Original glucose summaries | 20.69% | 13/33 |
| Original + multiscale | 21.01% | 11/33 |
| Multiscale alone | 22.75% | 11/33 |

All three best configurations used kernel regression with regularization 0.1. Selection compared 31 prespecified configurations including the personal-mean baseline. Each validation query used only its person's earlier nonoverlapping days, retaining other people in the allowed training pool. Settings were saved before scoring later outcomes.

The unchanged selected reference scored 21.00% MAPE and 15/44 later days within 10%. It is not the earlier ensemble, which remains the best recorded passive result at approximately 18.40%. New families were not selected by their later performance. This comparison supplies no evidence that these multiscale features should replace existing features.

Verified: all 120 source traces have the required finite sensor readings; 33 earlier validation queries; identical original-reference predictions within 1e-8 g; changing query targets to a sentinel leaves selected predictions unchanged; all 44 later days retained. The same development days have been inspected repeatedly, so this is not fresh independent validation.

Files: `PLAN.json`, `sensor_inputs.csv`, `validation.csv`, `settings.json`, `predictions_before_scoring.csv`, `later_results.csv`, `summary.json`. Source data and prior outputs were preserved.
