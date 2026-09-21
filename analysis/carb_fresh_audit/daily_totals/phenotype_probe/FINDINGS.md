# Baseline phenotype and daily glucose interpretation

Adding baseline characteristics did not reach the ±10% objective. With each arm independently selected on the same33 earlier validation days:

| Inputs | Later days within ±10% | MAPE | MAE |
|---|---:|---:|---:|
| Glucose and personal meal calibration | 15/44 | 21.00% | 42.59 g |
| Plus age/BMI/gender interactions | 15/44 | 20.11% | 39.27 g |
| Plus HbA1c/fasting glucose/insulin/triglyceride interactions | 16/44 | 19.20% | 37.57 g |

The lab arm requires known onboarding blood-test results. These are source measurements already available for this retrospective diagnostic, not additional passive wearable measurements. Neither daily foods nor current carbohydrate labels enter prediction. Age/BMI/gender were encoded from bio.csv; ethnic categories were not used.

Baseline characteristics were standardized using unique training participants only, then interacted with personally centered glucose descriptors. This prevents static characteristics from disappearing under personal centering. These are learned associations, not estimates of insulin action or causally established physiological corrections.

Kept the same64 calibration days and44 later days, and the same33 full-other-person-pool earlier validation days. Each arm compared ridge/kernel with five penalties. The arm without added characteristics was best on earlier validation (20.69% MAPE versus24.07% basic and23.15% labs). Thus the better later lab-arm score cannot justify selecting it as though that choice had been made beforehand. All arms are reported as a prespecified diagnostic comparison.

The glucose-only reference replayed the previous experiment within1e-8 g, and replacing query labels did not change any predictions. All44 later days remain included. No correction of source labels was made.

The prior best daily MAPE remains18.94%. Baseline lab information provides no demonstrated route to the requested10% accuracy here. This result does not rule out a mechanistically better use of those measurements, but it weakens the claim that simply adding the available demographic and metabolic context will solve the current errors.
