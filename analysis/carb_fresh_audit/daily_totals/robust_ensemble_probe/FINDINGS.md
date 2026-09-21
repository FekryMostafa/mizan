# P27 reversal and extreme ensemble components

Inspecting P27's June17/18 raw values found two distinct issues. Neither establishes that carbohydrate inference is impossible.

The recorded204g day includes a69g dinner at19:02. At19:00 Libre/Dexcom are82.0/134.2mg/dL; at20:00 they are92.6/163.8. The recorded133g day includes a24g dinner at18:38. At18:30 Libre/Dexcom are69.6/119.2; at20:00 they are122.6/203.2. Thus both sensors show a larger observed evening rise on the day with the smaller recorded dinner. These points do not isolate dinner absorption from previous meals, activity or other physiology. No causal explanation is established.

The meals differ beyond carbs: June17 dinner has26g fat,14g protein,17g fiber, and follows a29g-carb snack58minutes earlier. June18 dinner has11g fat,11g protein,2g fiber. Breakfasts both contain66g carbs but differ in protein/fat. Full-minute traces and source meal records are saved here for inspection. Direct dose ordering cannot be assumed from the observed rise alone.

Separately, some weakly regularized sequence models predicted only20.87 and29.51g for the entire204g day. This motivated checking robust aggregation rather than inventing a correction for that one failure.

Five fixed aggregation rules were compared on the33 earlier predictions: mean, median, symmetric trimming of3 or6 components from each tail, and winsorizing3. Earlier MAPE selected median at24.20%, versus24.43% for mean. The selected median scored19.02% MAPE and17/44 later days within10%; it did not beat the original mean's18.40% MAPE, although MAE was slightly lower at37.71g versus38.10g. The earlier difference was small and did not transfer on the primary metric.

All31 original component models and all44 later outcomes were retained. Rule selection used earlier predictions only and was saved before later scoring. Original mean predictions reproduced within1e-8g. Current meal records and Dexcom readings were audit evidence only, not model inputs. This is the same repeatedly inspected development set. The strict-data passive reference remains18.395%; the10% goal remains unmet.
