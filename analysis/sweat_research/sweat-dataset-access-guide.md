# Sweat dataset collection
Verified 7 September 2026. This is a starter collection of downloaded public data and metadata, not a complete download of every raw instrument file. Measurements from different studies must not be joined as if they describe the same person or meal. Original source terms continue to apply; commercial rights have not been assessed.

## 1. Sweat lipid profiling, 2026
Included: four original source-data workbooks for Figures 2, 3, 4 and 5. Figure 4 contains sensor traces; Figure 5 contains paired measurements and reported model results. These are figure-level data, not a complete participant-linked training dataset.
Paper: https://www.nature.com/articles/s44460-026-00117-0
Direct source file pattern: https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs44460-026-00117-0/MediaObjects/44460_2026_117_MOESM5_ESM.xlsx
MOESM3 = Figure 2; MOESM4 = Figure 3; MOESM5 = Figure 4; MOESM6 = Figure 5.

## 2. NutriTrek, 2022
Included: original 27-sheet source-data workbook. Downloaded successfully from the publisher; MD5 matches the Caltech repository listing: cf85a78743c6c6b19e2ab908c5501b7f.
Contains numerical source data for Figures 4 and 5 and supplementary figures 36 and 39–41. Intake challenges include amino-acid supplementation; this is not a daily protein-gram benchmark.
Repository: https://authors.library.caltech.edu/records/6e5ws-37180
Direct download: https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41551-022-00916-z/MediaObjects/41551_2022_916_MOESM6_ESM.xlsx
Additional raw/analysed data are available from the corresponding author on request.

## 3. Nutritional supplementation, MTBLS2427
Included: investigation, assay, sample metadata and metabolite annotation table; raw-file directory listing.
Verified metadata: 13 participant identifiers; high/low supplementation groups; 47 sample rows including pooled samples. Annotation table lists 23 metabolites, including several amino acids and carnitine. Crucially, all sample-abundance cells in this downloaded annotation table are empty. It is NOT a ready-to-train numerical matrix.
A separate publisher supplement was subsequently located and downloaded: Table_2.XLSX. It supplies the missing processed measurements: 39 sample rows from 13 participants, 15 metabolite columns, sample masses, High/Low supplement labels, mass-normalized measurements, and 26 baseline-relative fold-change rows. The workbook's Raw sheet contains processed assay values, not raw mass-spectrometry files. This removes the need to request the processed matrix for the initial analysis.
Direct Excel: https://www.frontiersin.org/api/v4/articles/659583/file/Table_2.XLSX/659583_supplementary-materials_tables_2_xlsx/1
47 raw instrument files are also publicly listed, but are not included in this starter pack.
Study: https://www.frontiersin.org/journals/chemistry/articles/10.3389/fchem.2021.659583/full
Metadata: https://ftp.ebi.ac.uk/pub/databases/metabolights/studies/public/MTBLS2427/
Raw files: https://ftp.ebi.ac.uk/pub/databases/metabolights/studies/public/MTBLS2427/FILES/RAW_FILES/

## 4. Finger sweat, MTBLS2772 and MTBLS2776
Included: sample/assay metadata and metabolite tables from both accessions, plus 41 donor-named CSV files from the authors' mathematical_model/raw_data folder. Those CSVs contain time, caffeine, paraxanthine, theobromine and theophylline measurements. These are processed measurements, not the repository's simulated sensitivity-analysis results. The authors' README and license are included for interpretation.
MTBLS2772 annotation table has 95 rows; MTBLS2776 has 96. Tables contain numerical abundance entries but also missing values; entries are not necessarily absolute concentrations. The counts of donor files, sample rows and instrument runs are not interchangeable counts of independent people.
Raw-file listings contain 930 and 1,026 .raw links respectively; these bulk raw files are not included.
Paper: https://www.nature.com/articles/s41467-021-26245-4
Metadata/data directories:
https://ftp.ebi.ac.uk/pub/databases/metabolights/studies/public/MTBLS2772/
https://ftp.ebi.ac.uk/pub/databases/metabolights/studies/public/MTBLS2776/
Measured time-series CSVs and analysis code: https://github.com/Gotsmy/finger_sweat/tree/master/mathematical_model/raw_data
This study concerns caffeine uptake/metabolism; it is useful for sweat kinetics and normalization, not evidence of calorie inference.

## 5. WATCH, 2021
No public participant-level numerical download was located. The paper explicitly says supporting data are available from the corresponding author upon reasonable request. The public Word supplement is included; it is not established as the underlying participant-level dataset.
Paper/access statement: https://aiche.onlinelibrary.wiley.com/doi/10.1002/btm2.10241
Contacts listed in the paper: shalini.prasad@utdallas.edu; sriramm@enlisense.com.
Needed request: timestamped sweat glucose/cortisol, participant/session IDs, meal timestamps and consumed macro quantities, calibration and reference measurements. No request has been sent.

## What is ready now
The lipid and NutriTrek workbooks and finger-sweat CSVs can be inspected immediately. The supplementation study now also has its processed Excel measurements included; its large raw instrument files remain available separately. WATCH needs author access. No new model fitting or clinical validation was performed during this collection.

## Additional repository search
Searched publisher/PMC supplements, author GitHub repositories, and web-indexed GitHub, Kaggle, Zenodo and Figshare records using WATCH, author names, sweat/glucose/cortisol, paper DOI and supplementation accession. No matching public WATCH participant-level dataset was located. This is a bounded search, not proof that no unindexed copy exists. The author request is limited to that missing dataset. No emails sent.
