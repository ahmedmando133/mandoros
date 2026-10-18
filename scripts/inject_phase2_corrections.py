# -*- coding: utf-8 -*-
"""
Injects the 20 Supreme Scientific Correction & Excel Restructuring Rules
permanently into Phase 2 master instructions and JSON rulebooks.
"""
import json
from pathlib import Path

RULES_MD = """

---

# SECTION 20 — PHASE 2 SCIENTIFIC CORRECTION & EXCEL RESTRUCTURING (20 SUPREME RULES)

**Task:** Correct the existing MANDOROS Phase 2 extraction, statistical analysis, validation, and Excel export pipeline. Keep the main template used and apply these changes to all future work.

**Reference documents:**
- `Phase 2 meta-analysis.json` — existing permanent scientific rules
- `Phase 1 extraction.json` — underlying extraction rules
- Nishimura et al. (2015) Empagliflozin RCT PDF — regression-test reference
- `Custom_Drug_MANDOROS_Master_Report (1)(1).xlsx` — previous output
- `Custom_Drug_MANDOROS_Master_Report(2).xlsx` — newer output

## PRIMARY INSTRUCTIONS
Review the existing codebase before making changes. Preserve the current MANDOROS workflow and all correctly functioning features.
Do not rebuild the application from scratch.
Implement the corrections below as permanent, generalized rules for future RCT extraction and meta-analysis.

**Critical priorities:**
1. Accurate clinical information and numerical values.
2. Correct identification of the statistical meaning of every number.
3. Complete preservation of baseline, efficacy, and safety outcomes.
4. Correct arm-specific and timepoint-specific sample sizes.
5. Elimination of invalid duplication without losing legitimate observations.
6. Statistically valid treatment-effect calculations and meta-analysis.
7. Independent verification against the original PDF before Excel export.
8. User Upload Isolation: Only process and analyze files specifically uploaded by the user in the current session. Never blend, contaminate, or merge new uploads with stale cached files or prior cohort analyses.

---

## RULE 1 — REDESIGN THE MASTER EXTRACTION SHEET
The first worksheet must always be named exactly:
`Master Excel Sheet`

Maintain the following sections in this order:
1. Study Characteristics and Treatment Arms
2. Eligibility Criteria — Inclusion and Exclusion
3. Baseline Characteristics
4. Efficacy Outcomes
5. Safety Outcomes

Do not replace the full Master Sheet with a simplified meta-analysis table.
Each outcome should appear under a clean outcome title, followed by separate rows for every applicable treatment arm. Report what is mentioned in the study.

**Required layout:**
**Outcome: [Exact outcome name]**

| Treatment Arm | Sample Analyzed (N) | Mean | SD | SE | Median | Q1 | Q3 | Change from Baseline | Adjusted Change | Treatment Difference vs Comparator | CI Lower | CI Upper | P-value |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Arm 1 | | | | | | | | | | | | | |
| Arm 2 | | | | | | | | | | | | | |
| Arm 3 | | | | | | | | | | | | | |

Additional metadata columns must include:
- Assessment Timepoint
- Outcome Unit
- Statistical Estimate Type
- Analysis Population
- Comparator Arm
- Source Page
- Source Table/Figure
- Validation Status

Only populate fields actually supported by the source or by an explicitly authorized, documented calculation.
Important: Mean, SD, SE, median, adjusted change, treatment difference, and geometric ratio are distinct statistical measures.
A correctly reported adjusted change must never be placed into the raw mean column.
Allow a merged outcome title for visual presentation, but do not merge analytical data cells.
Do not embed any numerical sample sizes, statistical classifications, or demographic assumptions in outcome titles.

---

## RULE 2 — KEEP SAMPLE SIZE IN SEPARATE COLUMNS
**This is a mandatory new requirement.**
Never write outcome headings such as:
`Insulin AUC1–4h [Full analysis set (n=20 at Day 28, n=21 at Day 1) | Asian (Japanese) | RAW_MEAN_DIFFERENCE]`
Instead, write only:
**Insulin AUC1–4h**

Store sample sizes in dedicated columns under the relevant treatment arm and timepoint.
Every outcome row must distinguish:
- N Randomized
- N Baseline Analyzed, where applicable
- N Outcome Analyzed
- Analysis Population
- Assessment Timepoint
- Missing/Withdrawn Participants, where reported

If sample size changes between baseline and follow-up, never overwrite the original baseline sample size. Write the new sample size if mentioned in the paper with the variable analyzed make a column under that additional variable.

IF baseline N and follow-up N differ:
- Preserve both.
- Put them in separate columns.
- Record the assessment day.
- Link the sample size to the correct arm.
- Preserve the original analysis-population definition.
- Do not assume a reason for missing participants unless supported by the source.

IF the paper does not report outcome-specific N:
Leave N Outcome Analyzed blank and flag it for verification. Do not automatically substitute N Randomized.

---

## RULE 3 — PRESERVE SAMPLE SIZE IN BASELINE CHARACTERISTICS
The Baseline Characteristics section must always contain a sample-size column for every treatment arm.
Required baseline structure:
| Baseline Variable | Arm | N Randomized | N Baseline Analyzed | Mean | SD | SE | Median | Q1 | Q3 | Unit |

Every baseline observation must have its own correct source-linked denominator.

---

## RULE 4 — CORRECT INSULIN AUC STATISTICS
The reference RCT reports:
- Baseline: geometric mean and geometric coefficient of variation.
- Relative changes: adjusted geometric mean ratios with 95% CIs.
- Between-treatment comparisons: adjusted geometric mean ratios versus placebo.

Required statistical fields:
- `GEOMETRIC_MEAN`
- `GEOMETRIC_CV`
- `ADJUSTED_GEOMETRIC_MEAN_RATIO`
- `CI_LOWER`
- `CI_UPPER`
- `P_VALUE`

Never store geometric CV under arithmetic SD.
Never store a geometric mean ratio under raw mean difference.
The table must clearly distinguish within-arm ratios from ratios versus placebo.
Apply the same extraction logic to AUC10–13h and any future log-transformed clinical outcomes.

---

## RULE 5 — CORRECT 8-ISO-PGF2α CLASSIFICATION
For the Empagliflozin trial:
Fasting urinary 8-iso-PGF2α — Day 28
Required classifications:
- Within-arm results: `ADJUSTED_MEAN_CHANGE`
- Between-arm results: `ADJUSTED_MEAN_DIFFERENCE`
Preserve the comparison confidence intervals and p-values in separate columns.
Apply the same rule to 24-hour 8-iso-PGF2α, but treat it as a distinct outcome from fasting 8-iso-PGF2α.

---

## RULE 6 — CORRECT ALL PUBLISHED TREATMENT EFFECTS
Regression test targets (Nishimura 2015):
- 24-hour 8-iso-PGF2α, Day 28: 10 mg = -24.7, 25 mg = -43.1
- HDL-C, Day 29: 10 mg = +4.5, 25 mg = +7.2
- LDL-C, Day 29: 10 mg = +4.7, 25 mg = +5.7
- Total cholesterol, Day 29: 10 mg = +4.0, 25 mg = +1.9

IF the extracted value disagrees with the PDF:
1. Verify the source table and statistical definition.
2. Verify the correct intervention and comparator.
3. Verify the exact assessment timepoint.
4. Replace the unsupported value.
5. Preserve the published CI, p-value, and unit.
6. Document the correction in the Validation Log.
Do not calculate an unadjusted difference from two adjusted within-arm changes and label it as the paper's adjusted treatment difference.

---

## RULE 7 — RESTORE MISSING VALID OUTCOMES
Review every relevant table, figure, caption, footnote, and available supplementary source.
Restore scientifically valid results including:
- Postprandial insulin AUC1–4h
- Postprandial insulin AUC10–13h
- Fasting urinary 8-iso-PGF2α
- 24-hour urinary 8-iso-PGF2α
- Total cholesterol, HDL-C, LDL-C, Triglycerides, Free fatty acids, Ketone bodies
- HbA1c, PPG outcomes, FPG, CGM mean glucose, MAGE
- Body weight and blood pressure, where reported
- Adverse events

Deduplication must use: `study, arm, comparator, endpoint, timepoint, analysis population, estimate type, and subgroup`.
Never delete a valid result simply because another record uses the same outcome name.

---

## RULE 8 — CORRECT PICO AND ELIGIBILITY
Preserve the study's complete population, intervention, comparator, and outcomes.
Preserve all three HbA1c eligibility conditions separately:
1. Drug-naïve screening: 7–10%.
2. Previously treated screening: 7–9.5%.
3. Placebo run-in: 7–10%.
Do not merge these into one generic HbA1c criterion.
The cardiovascular exclusion must preserve acute coronary syndrome, stroke, or TIA within 20 weeks before randomization (do not substitute 12 weeks).
All inclusion and exclusion comparisons must preserve exact thresholds, operators, units, medications, exceptions, and durations.

---

## RULE 9 — REMOVE UNSUPPORTED DEMOGRAPHIC INFERENCES
Do not use `Asian (Japanese)` as a universal racial classification in outcome titles.
Japanese describes the reported study population. It does not establish a separately reported 100% racial distribution.
IF race or ethnicity is not quantitatively reported: Leave arm-specific racial counts and percentages blank.

---

## RULE 10 — REMOVE FABRICATED OR MISCLASSIFIED STUDY INFORMATION
If clinical trial phase is not explicitly reported, leave the study-phase cell blank (do not write 'Not explicitly reported').
Do not infer Phase III simply because the Introduction discusses Phase III trials.
Do not write placebo dose as `0 mg` or another fabricated quantity unless the source explicitly reports it that way.
Preserve randomized arm sizes independently from outcome-analyzed sizes.
Correctly represent categorical demographic data as counts and percentages, not means and SDs.

---

## RULE 11 — CORRECT MAGE STATISTICAL CALCULATIONS
The study reports adjusted within-arm MAGE changes and states that the treatment differences were not statistically significant.
The system must not invent adjusted between-arm confidence intervals.
A simple difference between published within-arm adjusted changes may be calculated for descriptive purposes, but it must be labeled: `DERIVED_ARITHMETIC_DIFFERENCE`.
It must not automatically be classified as the published adjusted treatment effect.
IF the necessary covariance or treatment-effect uncertainty is unavailable: Do not fabricate a standard error, variance, CI, or p-value. Do not enter unsupported MAGE estimates into meta-analysis pooling.

---

## RULE 12 — PREVENT INVALID SINGLE-STUDY META-ANALYSIS
The reference document contains one independent randomized controlled trial with three arms. It does not contain three independent trials.
IF the number of independent eligible RCTs is one (k=1):
Allow:
- Complete clinical trial extraction.
- Individual treatment-effect estimates.
- Valid within-trial comparisons.
- Published confidence intervals.
- Descriptive summaries.
- Risk-of-bias assessment based on available evidence.
Do not perform:
- Multi-study fixed-effect pooling.
- Multi-study random-effects pooling.
- Between-study heterogeneity estimation.
- I² or τ² for a single independent study.
- Leave-one-study-out sensitivity analysis.
- Publication-bias statistics.
- Unsupported meta-regression.
- Prediction intervals requiring between-study variance.
Mark nonapplicable analyses as `NOT_APPLICABLE_SINGLE_STUDY` in the analysis status or validation log.
Do not populate numeric output fields with zero or fabricated values. Leave inapplicable analytical results blank.

---

## RULE 13 — PREVENT DOUBLE COUNTING
The Empagliflozin study contains two active treatment groups sharing one placebo group.
IF multiple arms share a comparator:
- Maintain the common trial ID.
- Preserve all randomized arms.
- Recognize the shared control population.
- Do not treat comparisons as statistically independent.
- Do not double-count placebo participants.
- Use a statistically appropriate multi-arm method if an eligible future meta-analysis requires combining comparisons.
Never pool different doses, outcomes, or assessment days without a documented scientific justification.

---

## RULE 14 — CORRECT EFFECT SCALES AND STATISTICAL FORMULAS
Do not place ordinary negative mean differences under a column named `Log Effect` unless the estimate has actually been log-transformed.
For continuous outcomes:
- Mean differences remain on their linear measurement scale.
- Ratios may be modeled on an appropriate logarithmic scale.
- Geometric mean ratios require their own statistical classification.
- Adjusted effects must retain their original estimand.
For binary outcomes, preserve the correct events and denominator.
For time-to-event outcomes, preserve the reported hazard ratio and CI. Never substitute RR for HR or vice versa.
Never invent SDs from SEs or confidence intervals without a justified, logged calculation using correct assumptions.

---

## RULE 15 — CORRECT P-VALUES AND CONFIDENCE INTERVALS
Never export a calculated p-value as exactly `0` merely because of numerical underflow or rounding.
Preserve source-reported values such as: `p < 0.001` using separate operator and numeric-value fields.
For every treatment comparison:
- Record the exact point estimate.
- Record CI lower and upper.
- Record confidence level.
- Record p-value and operator.
- Record comparator.
- Record whether the effect was published or calculated.
If the study does not provide sufficient statistical information, leave the unsupported result blank and flag it.

---

## RULE 16 — CORRECT ADVERSE-EVENT EXTRACTION
Preserve all reported safety outcomes and the correct treated population.
Separate columns for event count, denominator, and percentage.
Do not confuse number of events with number of patients experiencing an event.
Do not classify an adverse-event observation as a baseline measurement.
Do not duplicate `Any Adverse Event` simply because it appears in both the Results text and the safety worksheet.

---

## RULE 17 — SEPARATE ORIGINAL EVIDENCE FROM PREDICTIONS
Preserve existing optional predictive and simulation functionality, but separate it completely from the verified clinical evidence.
Every analytical result must be labeled as one of:
- `ORIGINAL_PUBLISHED_RESULT`
- `CALCULATED_FROM_PUBLISHED_DATA`
- `MODEL_PREDICTION`
- `SYNTHETIC_DATA`
Predictive projections, virtual trials, and hypothetical dose-response analyses must never be presented as original RCT findings.
They must never enter a published-evidence meta-analysis without an explicitly separate, scientifically justified simulation protocol.

---

## RULE 18 — INDEPENDENT PDF VALIDATION
Before generating the final Excel workbook, independently verify the output against the original PDF.
For every numerical record, validate:
1. Outcome identity.
2. Treatment arm.
3. Dose.
4. Comparator.
5. Correct sample size.
6. Analysis population.
7. Timepoint.
8. Exact numerical value.
9. Statistical estimate type.
10. Measurement unit.
11. Confidence interval.
12. P-value.
13. Source page and table/figure.
14. Absence of unsupported duplication.

Build a source-derived inventory of expected results before calculating completeness.
A clean Validation Log is not proof of correctness. The validator must detect both incorrect extracted values and valid published results that are missing.
Any unresolved critical error must prevent a `COMPLETE_AND_VALIDATED` status.

---

## RULE 19 — QUALITY SCORING
Generate separate, reproducible quality metrics:
- **Numerical Accuracy:** Correct verified numerical fields divided by all audited numerical fields.
- **Statistical Semantic Accuracy:** Correct outcome, population, arm, timepoint, and statistical classifications divided by all audited classifications.
- **Extraction Completeness:** Correctly extracted expected unique findings divided by all expected extractable findings in the defined source inventory.
- **Duplicate Error Rate:** Invalid duplicate observations divided by unique intended observations, using a documented denominator.
- **PICO Accuracy:** Correctly represented study characteristics and eligibility criteria divided by audited PICO fields.
- **Meta-analysis Validity:** Pass/fail of applicable statistical safeguards and independent-study requirements.
Always show exact numerators and denominators used in scoring. Do not automatically award 100/100 because the Excel file was generated successfully.

---

## RULE 20 — PERMANENT FUTURE APPLICATION
Apply all improvements to the permanent MANDOROS Phase 2 pipeline.
Use the Empagliflozin RCT only as a regression test. Do not hardcode any study-specific values or sample sizes.
For every future RCT, independently determine:
- The randomized sample size.
- Baseline analyzed sample size.
- Outcome analyzed sample size at each timepoint.
- Reported statistical summary type.
- Published and calculated treatment comparisons.
- Appropriate eligibility criteria.
- Whether meta-analysis is statistically permissible.
The sample-size columns and outcome-title rules must apply automatically to every future study, regardless of treatment, study population, disease, or number of treatment arms.
"""


def main():
    # 1. Update master_protocols/phase2_master_instructions.md
    p2_md = Path("master_protocols/phase2_master_instructions.md")
    if p2_md.exists():
        text = p2_md.read_text(encoding="utf-8")
        if "SECTION 20 — PHASE 2 SCIENTIFIC CORRECTION" not in text:
            p2_md.write_text(text + RULES_MD, encoding="utf-8")
            print("[+] Appended 20 Supreme Rules to master_protocols/phase2_master_instructions.md")
        else:
            print("[*] 20 Supreme Rules already present in master_protocols/phase2_master_instructions.md")

    # 2. Update master_protocols/Phase 2 meta-analysis.json
    for json_path in [Path("master_protocols/Phase 2 meta-analysis.json"), Path("backend instructions/Phase 2 meta-analysis.json")]:
        if json_path.exists():
            data = json.loads(json_path.read_text(encoding="utf-8"))
            data["scientific_correction_and_excel_restructuring_20_rules"] = {
                "rule_1_redesign_master_sheet": "First sheet must be Master Excel Sheet with clean outcome titles and per-arm rows",
                "rule_2_separate_sample_size_columns": "Store N in dedicated columns: N Randomized, N Baseline Analyzed, N Outcome Analyzed",
                "rule_3_baseline_sample_size": "Preserve baseline N per arm in dedicated columns",
                "rule_4_insulin_auc_statistics": "GEOMETRIC_MEAN, GEOMETRIC_CV, ADJUSTED_GEOMETRIC_MEAN_RATIO, CI_LOWER, CI_UPPER, P_VALUE",
                "rule_5_8_iso_pgf2a_classification": "Separate fasting and 24-hr; within-arm ADJUSTED_MEAN_CHANGE, between-arm ADJUSTED_MEAN_DIFFERENCE",
                "rule_6_correct_published_treatment_effects": "Strict verification against source; do not calculate unadjusted diff and label as adjusted",
                "rule_7_restore_missing_valid_outcomes": "Deduplicate on study, arm, comparator, endpoint, timepoint, population, estimate_type, subgroup",
                "rule_8_correct_pico_and_eligibility": "Preserve exact criteria, thresholds, operators, units, durations",
                "rule_9_remove_unsupported_demographics": "Do not infer 100% racial distribution; leave blank unless quantitatively reported",
                "rule_10_remove_fabricated_information": "Leave study phase blank if not reported; placebo dose blank unless reported as 0 mg",
                "rule_11_correct_mage_calculations": "Label simple diffs DERIVED_ARITHMETIC_DIFFERENCE; never invent CI/SE",
                "rule_12_prevent_single_study_meta_analysis": "If k=1 independent RCT, prohibit pooling, I2, tau2, sensitivity, leave blank and mark NOT_APPLICABLE_SINGLE_STUDY",
                "rule_13_prevent_double_counting": "Shared comparator arms must not be treated as independent or double-count control participants",
                "rule_14_correct_effect_scales": "Linear scale for continuous MD; never put negative MD under Log Effect",
                "rule_15_correct_p_values_and_cis": "Never export p=0; separate operator and numeric value",
                "rule_16_correct_adverse_events": "Separate event count, denominator, percentage; do not classify AE as baseline",
                "rule_17_separate_predictions_from_evidence": "Label results ORIGINAL_PUBLISHED_RESULT, CALCULATED_FROM_PUBLISHED_DATA, MODEL_PREDICTION, SYNTHETIC_DATA",
                "rule_18_independent_pdf_validation": "Validate identity, arm, dose, sample size, timepoint, value, estimate type against PDF",
                "rule_19_quality_scoring": "Explicit numerators and denominators for accuracy, completeness, duplicate error, PICO, meta-analysis validity",
                "rule_20_permanent_future_application": "System-wide generalized rules, no hardcoded constants, applies to all future RCTs",
                "user_upload_isolation_directive": "When user uploads files, ONLY process and analyze those files. Completely purge and isolate upload session directory so no old data or cached trials are blended."
            }
            json_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
            print(f"[+] Updated {json_path} with 20 Supreme Rules and upload isolation directive")


if __name__ == "__main__":
    main()
