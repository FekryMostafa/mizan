# Published model suitability for CGM-only fat inference

Checked 2026-09-08. Goal remains fat grams within ±10% on unseen meals after personal calibration. Not achieved.

## O'Donovan Mixed Meal Model: rejected unchanged

Directly inspected the author's [ODE implementation](https://raw.githubusercontent.com/shauna-odonovan/Mixed_Meal_Model/main/M3al_Model_ODE.m). Its glucose/insulin subsystem has no dependency on meal lipid mass, circulating triglycerides, or NEFA. Lipid input feeds the triglyceride compartments; insulin influences lipid handling, without feedback into glucose equations. Consequently, at fixed parameters and initial conditions, changing meal fat cannot change predicted glucose. The glucose-only inverse objective is flat in fat mass. This is a structural deduction, not a numerical simulation or biological claim.

Checked [parameter construction](https://raw.githubusercontent.com/shauna-odonovan/Mixed_Meal_Model/main/M3al_Model_Parameters.m) for an indirect coupling: gastric emptying and glucose uptake parameters are fitted values, not functions of meal fat. Checked [initialization](https://raw.githubusercontent.com/shauna-odonovan/Mixed_Meal_Model/main/M3al_Model_Initial.m): initial glucose and insulin states do not depend on meal fat. The [simulation driver](https://raw.githubusercontent.com/shauna-odonovan/Mixed_Meal_Model/main/Run_Model_Simulation.m) specifies meal carbohydrate and lipid independently from kinetic parameters.

Fitting separate parameters for different meals could reflect dietary effects, but does not supply a calibrated grams-to-parameter relationship. Adding one would be a new, unvalidated extension requiring testing.

## Why its published personalization is insufficient for this goal

The [2024 study](https://pmc.ncbi.nlm.nih.gov/articles/PMC10946327/) fits multiple measured metabolite trajectories with meal composition supplied. Its personalization results therefore do not validate inference of an unknown fat dose from glucose alone.

## Next candidate and acceptance criteria

[Noguchi and Furutani 2017](https://www.jstage.jst.go.jp/article/iscie/30/7/30_286/_article) explicitly describes lipid-derived insulin resistance and separate carbohydrate/fat transit. Its full equations and parameter estimation must be inspected before implementation. It targets type 1 diabetes, so endogenous insulin regulation requires special attention for our intended users.

A candidate must demonstrate: (1) a fat-input pathway to predicted glucose; (2) parameters calibratable using the permitted observations; (3) recovery of unknown doses in synthetic sanity checks without supplying the answer; and (4) held-out real-meal accuracy. Synthetic recovery alone cannot establish feasibility.

## Access and reproducibility limits

Git clone failed because shell DNS could not resolve GitHub. Source was inspected through the web tool; no repository checkout or commit-pinned source copy was obtained. This report records URLs rather than claiming a downloaded or executed reference implementation. No reserved participant data was accessed.
