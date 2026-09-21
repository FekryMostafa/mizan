# ScopeSense: long history, missing synchronized metabolic measurements

8 September 2026. Followed the official Simula dataset page to OSF project v5acr and enumerated the participant roots and immediate Apple Watch, Lifesum and PMSys folders, including all pagination. Saved the file inventory in `reference/literature_refresh/scopesense_inventory.json`. ECG and workout-route subfolders were not recursively downloaded; their parent folder names are recorded.

No glucose or sweat data files are listed in the inspected sensor inventory. Available streams include Apple Watch activity, heart rate, heart-rate variability, oxygen saturation and sleep, with separate daily ECG and workout-route folders. This is not the synchronized CGM-plus-macros cohort we were seeking to test longer personal calibration.

Downloaded and publisher-SHA256-verified both food files: 2,168 component records for A and 2,636 for B. They include carbohydrate, fat, protein, serving and some gram-amount fields. The date and meal-type fields identify a calendar day and categories such as breakfast or dinner, **not exact consumption times**. Every date is a date-only string; there is no separate clock-time column. This prevents identifying reliable pre/postmeal windows from these food records alone. Combining multiple snacks by date/category would risk merging distinct eating events.

These data could support a separate day-level nutrition/history analysis, but that would not validate our sensor-based gram inference. They cannot be paired with another study's CGM traces because those are different people and events. No new model was trained, and no ±10% result is claimed.

The local `dataset/scopesense/download_manifest.json` records the three successfully acquired and verified files (two food files and B's sensor note); `label_inventory.json` records counts and date coverage. A's sensor-note download returned HTTP 500, so it is not counted as acquired. No raw physiological data was bulk-downloaded.

The next actionable existing-data avenue is a matched, development-only test of the BIG IDEAs EDA and temperature streams alongside glucose, with all signals evaluated on the same later meals. Earlier heart-rate-only additions did not establish whether those different modalities help. MealMeter's flawed attribution does not supply that answer. The reserved BIG IDEAs participants must stay untouched during this development work.

Sources: [Official dataset page](https://datasets.simula.no/scopesense/), [OSF release](https://osf.io/v5acr/). Findings about fields and counts above come from the downloaded raw records, not just dataset descriptions.
