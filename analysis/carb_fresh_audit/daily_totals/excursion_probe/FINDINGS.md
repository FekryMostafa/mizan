# Sustained elevation and decay descriptors

The new features did not improve earlier chronological validation, so the selection rule retained the previous model. Results remain 15/44 later days within ±10%, 18.94% MAPE and 37.60 g MAE. The goal is not achieved.

Added descriptors for sustained elevations: area above the 30-hour 10th-percentile glucose level, duration and longest run above 10/20/40 mg/dL relative to that level, rise/fall sums, and positive departures from hypothetical exponential decays with 30/60/120-minute constants. Kept midnight–06:00, 06:00–midnight, and next-midnight–06:00 separate. These descriptors measure glucose concentration patterns, not ingested grams or measured absorption. Segments with less than 90% finite samples remain unavailable.

Compared new descriptors alone and combined with existing sensors against the old representation using the same ridge/kernel grid and 29 earlier validation days. Best validation MAPE by family: old 22.70%, combined 22.99%, new descriptors 23.75%. No alternative was chosen after examining later outcomes. The old model's 44 predictions were reproduced within 1e-8 g, and replacing query labels did not change outputs.

## What the raw descriptors show

- P4, 316 versus 513 g: waking-segment area rises only from 15,541 to 16,143 mg/dL-min, while the following overnight area rises from 4,329.6 to 7,346.4. There is a larger overnight response, but the fitted conversion still does not recover the additional carb amount.
- P26, 167 versus 122 g: waking-segment area increases from 20,311 to 25,369.2 despite lower recorded carbs. Time more than 20 mg/dL above the chosen baseline rises from 390 to 570 minutes. Accounting for duration does not restore a simple dose ordering for this pair.
- P9, 182 versus 132 g: area increases from 14,580 to 20,310 and the longest elevated period from 105 to 270 minutes on the lower-carb day. Its poor estimate cannot be explained solely by ignoring how long glucose stayed elevated.

These comparisons concern selected previously observed failures; they do not establish universal physiology or an information limit. They do rule out the specific claim that these failures necessarily disappear once duration replaces spike height. A more informative next diagnostic is to quantify whether known differences in fat/protein composition explain otherwise misleading glucose responses, explicitly separating such explanatory labels from deployable sensor inputs. Current passive performance remains unchanged.
