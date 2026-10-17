# UNIFIED CLINICAL EVIDENCE & METHODOLOGICAL AUDIT ENGINE (PRODUCTION SPECIFICATION)

This file defines the automated processing and validation layers for all project generation tasks.

================================================================================
LAYER 3: TRIALMIND SYSTEMATIC EVIDENCE SYNTHESIS ENGINE
(Derived from Nature npj Digital Medicine 2025; DOI: 10.1038/s41746-025-01840-7)
================================================================================

1. Skill_PICO_Deconstruction_and_Query_Expansion:
   - Formalize research questions into Population, Intervention, Comparison, and Outcome (PICO).
   - Execute a 3-step Chain-of-Thought (CoT) + Retrieval-Augmented Generation (RAG) query cycle:
     * Candidate term extraction from relevant biomedical abstracts.
     * Term pruning (eliminating high-noise or overly broad descriptors).
     * Expansion with MeSH terms and synonyms to maintain search recall >= 78%.

2. Skill_Atomic_Eligibility_Criteria_Builder:
   - Convert clinical goals into atomic, testable Inclusion (I) and Exclusion (E) criteria.
   - Each criterion must isolate a single testable property (e.g., disease stage, previous therapy line, trial design).

3. Skill_Criterion_Level_Screening_and_Verbatim_Grounding:
   - Evaluate text spans against each criterion using ternary logic:
     * +1: Explicitly Eligible
     * -1: Explicitly Ineligible
     *  0: Uncertain / Insufficient Information
   - Zero-False-Negative Safeguard: A score of 0 must NEVER eliminate an article; it must be passed to full-text review.
   - Verbatim Anchor Requirement: Every +1 or -1 scoring must extract an exact, continuous verbatim quote from the source text.

4. Skill_Relevance_Aggregation_and_Ranking:
   - Calculate cumulative relevance score $\hat{I}_i = \sum_m I_i^m$ across all criteria.
   - Sort candidates descendingly to present highest-probability studies at the top (achieving Recall@50 > 70%).

5. Skill_Chunk_Anchored_Data_Extraction:
   - Partition full texts into indexed chunks (`[Chunk_ID]`).
   - Extract design features, patient cohorts, and demographics as structured pairs: `{Extracted_Value, Source_Chunk_ID}`.
   - Unanchored claims are rejected immediately.

6. Skill_Clinical_Endpoint_and_Numerical_Extraction:
   - Extract primary/secondary clinical endpoints (ORR, PFS, OS, Hazard Ratios, Risk Ratios, Adverse Event grades).
   - Execute two-stage CoT:
     * Stage 1: Extract verbatim context describing the metric.
     * Stage 2: Separate cohorts, counts, rates, and 95% confidence intervals.

7. Skill_Code_Interpreted_Standardization:
   - Strictly prohibit internal LLM mental math.
   - Formulate and execute deterministic Python scripts to convert raw values into standardized tabular records ready for statistical pooling.

8. Skill_PRISMA_2020_Flow_Integrity:
   - Keep audit counts for PRISMA flow: Identified -> Screened -> Excluded (with atomic reason) -> Included.

================================================================================
LAYER 4: RCTMETHODOLOGYIE DEEP METHODOLOGICAL AUDIT & INTERNAL VALIDITY GATE
(Derived from AMIA 2022; PMC10148349 / CONSORT 2010 & OCRe Ontology)
================================================================================

1. Skill_Trial_Architecture_Classifier:
   - Classify trial structural design: Parallel Group, Crossover, or Factorial.
   - Identify clinical trial phase: Phase 1, Phase 2, Phase 3, Phase 4, Phase IIb.
   - Identify comparative intent: Superiority, Non-inferiority, or Equivalence.

2. Skill_Blinding_and_Masking_Auditor:
   - Categorize blinding type: Open Label, Single-Blind, Double-Blind, Triple-Blind.
   - Dissect and verify blinding across all four operational entities:
     * Patients / Participants
     * Care Providers / Treating Clinicians
     * Outcome Assessors / Investigators
     * Data Analysts / Statisticians

3. Skill_Randomization_Granular_Extractor:
   - Identify sequence generation method: Computer-generated random numbers, interactive web-response system, random tables.
   - Extract randomization subtype: Simple, Block (extracting block size and variance), or Stratified (extracting stratification factors: age, site, severity).
   - Extract allocation ratio (e.g., 1:1, 2:1) and independent personnel administering the schedule.

4. Skill_Allocation_Concealment_Auditor:
   - Appraise allocation concealment mechanisms: Centralized pharmacy, IWRS/IVRS, or sequentially numbered opaque sealed envelopes (SNOSE).
   - Flag trials where concealment is open or unstated as high/unclear risk of selection bias.

5. Skill_Power_and_Sample_Size_Validator:
   - Extract sample size parameters: Statistical Power (e.g., 80%, 90%), Alpha level (e.g., 0.05, 0.01), and anticipated loss to follow-up / dropout rate.
   - Cross-check Planned Required Sample Size against Actual Sample Size at Enrollment and Actual Sample Size at Final Outcome Analysis.

6. Skill_Settings_and_Multicenter_Classifier:
   - Differentiate between Single-center vs. Multicenter studies.
   - Extract geographical sites, hospital networks, and countries of study execution.

7. Skill_Verbatim_Verification_Hook:
   - Automated server-side string validator: Any quote cited in Layer 3 or Layer 4 is checked against the raw document string. If the quote does not exist verbatim, the extraction is aborted and flagged for hallucination.

8. Skill_Cochrane_Risk_of_Bias_Synthesizer (RoB 2 / ROBINS-I):
   - Synthesize the outputs of skills 1–6 into five formal risk-of-bias domains:
     * D1: Bias arising from the randomization process.
     * D2: Bias due to deviations from intended interventions.
     * D3: Bias due to missing outcome data.
     * D4: Bias in measurement of the outcome.
     * D5: Bias in selection of the reported result.
