Subject: Quick clarification on a few CGMacros meal records

Hi,

Thanks again for making CGMacros available. We've been using it to explore personalized daily carbohydrate estimates from CGM, and we're trying to make sure we interpret the meal labels correctly before including more calibration days.

Could you help clarify a few records in the date-shifted dataset?

1. Are the macro columns already adjusted for the amount consumed? In CGMacros-041.csv, the April 29, 2022 11:17 lunch has Consumption=75 and carbs/protein/fat=94/12/13 g—the same amounts listed for the full planned lunch. The May 2 11:25 lunch similarly has Consumption=75 and 76/22/18.5 g. Should we use these macro values as recorded, or apply the consumption percentage?

2. What do Consumption values 300, 400, and 500 represent? Examples in CGMacros-041.csv are April 30 at 16:05, 17:46, and 22:22, and May 1 at 16:01 and 20:34. Are these another unit, encoding, or entry errors?

3. Does an all-zero macro record mean zero intake or missing nutrition data? In CGMacros-027.csv, June 11, 2024 23:58 and June 15 17:36 have zero macros and photos of tea. In CGMacros-012.csv, March 3, 2023 21:24 has zero consumption and macros but a photo of a plated meal. Is there a way to distinguish an uneaten meal from an unannotated meal?

4. For a day with breakfast/lunch/snacks but no dinner entry, is there any completeness flag or diary confirming that dinner was skipped rather than unlogged? Examples include CGMacros-002 November 17, 2019; CGMacros-009 September 16–17, 2020; and CGMacros-026 March 27, 2021.

If a data dictionary or corrected file already answers these, a link would be very helpful. Happy to send the exact rows if that is easier.

Thank you for your help!
Fekry

---
Draft only; not sent. Dates above refer to the local date-shifted release. No new recipient has been inferred.
