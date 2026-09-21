# CGM-only learning from all available earlier eligible meals

8 September 2026. Scope follows the user's instruction to focus on CGM, not sweat. Tested whether additional chronological personal labels improve prediction over four fixed onboarding meals. Only CGM features and earlier recorded macros are model inputs. No wrist signals, food names, query nutrient labels or query calories are supplied.

The frozen CGMacros population model is unchanged (652 meals, 34 people, ExtraTrees 200 trees, minimum leaf 5, seed 20260908). The same 65 later BIG IDEAs development meals from five people are evaluated. Initial onboarding uses four meals; rolling calibration grows to 4–19 earlier **eligible** labeled meals. Each earlier meal's full three-hour response must end before the next query begins. This tests extra supervised personal calibration, not learning macro labels from unlabeled CGM traces and not a wearable that requires no further logging after onboarding. The eight reserved participants remain unaccessed.

| Method | Joint 10% successes | Carb MAE | Protein MAE | Fat MAE |
|---|---:|---:|---:|---:|
| Fixed four-meal calibration | 1/65 | 37.12 g | 13.48 g | 12.45 g |
| Rolling continuous calibration (primary) | 0/65 | 38.62 g | 14.34 g | 11.68 g |
| Rolling no-sensor median | 0/65 | 40.30 g | 15.14 g | 12.73 g |
| Nearest earlier glucose curve, returning that meal's macros | 8/65 | 42.50 g | 18.72 g | 12.74 g |

There are 48 query meals with no identical macro vector in the available earlier history. Every method has zero joint successes on those 48. The nearest-curve method's eight successes all repeat known macro vectors: seven repeat 56.5 g carbs / 8 g protein / 2.5 g fat; one repeats 71.2 / 15.4 / 7.6 g. These are comparisons of recorded macro vectors, not proof of identical ingredients or portions.

A post-hoc diagnostic that always guesses the most frequent earlier macro vector, without glucose (ties resolved by earliest occurrence), gets 5/65 correct. Nearest-curve retrieval gets eight, so the no-sensor control does not explain away every success. However, neither result validates continuous dose recovery for unfamiliar meals. The primary rolling model modestly reduces fat error by 0.77 g while worsening carbohydrate/protein errors and missing the overall target.

## Verification and interpretation

Reproduced all fixed-calibration predictions from the earlier transfer experiment within 1e-8 absolute tolerance and zero relative tolerance. Independently verified all 260 predictions, exact same 65 query keys across methods, finite nonnegative predictions, and all joint tolerance flags recomputed from numeric outputs. Checked every historical response end against query start using the 65-row history manifest. Saved input/script hashes and the post-hoc no-sensor diagnostic separately. The earlier-meal labels are revealed only after their own prediction event; no query receives its own or future labels.

This remains repeatedly inspected development data, not a new independent validation claim. More usable chronological history did not produce the requested accuracy under this fixed continuous model. It does not establish impossibility or a theoretical accuracy bound. It also cannot assess months of personalization: the available eligible history tops out at 19 earlier meals.

- [Every prediction](predictions.csv)
- [Exact labels available before each query](history_manifest.json)
- [Results by familiarity](summary.json)
- [Post-hoc no-sensor control](rolling_mode_diagnostic.csv)
- [Verification](verification.json)
- [Run provenance](run_manifest.json)
