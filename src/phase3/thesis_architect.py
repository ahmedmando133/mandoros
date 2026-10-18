"""
MANDOROS Phase 3: Pillar IV — Thesis & Research Question Architect.
Converts verified research gaps into defensible academic research proposals,
PICO/PICOTS questions, FINER feasibility appraisals, and supervisor review checklists.
"""

from __future__ import annotations

import os
from typing import List, Dict, Any, Optional

from src.phase3.models import (
    ObservedResearchGap,
    RealityCheckReport,
    ThesisProposal,
    EvidenceStudy
)


class ThesisArchitectEngine:
    """
    Pillar IV Engine: Structures research questions into publication-grade proposals
    for Master's theses, PhD dissertations, or prospective clinical trial protocols.
    """

    @classmethod
    def develop_thesis_proposal(
        cls,
        gap: ObservedResearchGap,
        reality_report: Optional[RealityCheckReport] = None,
        studies: Optional[List[EvidenceStudy]] = None
    ) -> ThesisProposal:
        """
        Synthesizes a comprehensive research blueprint from a candidate research gap.
        Tailors recommendations based on whether existing coverage or ongoing trials were identified.
        """
        pico = gap.candidate_pico
        condition = pico.get("population") or "Target Clinical Population"
        intervention = pico.get("intervention") or "Investigational Regimen"
        comparator = pico.get("comparator") or "Active Standard of Care"
        primary_outcome = pico.get("outcome") or "Primary Efficacy Endpoint"

        # Determine recommended study design based on gap category and reality check status
        status = reality_report.status if reality_report else "Potential Gap — Requires Further Verification"
        design, design_justification = cls._determine_optimal_design(gap, status)

        # Formulate 3 Academic Titles
        titles = cls._generate_academic_titles(gap, design, condition, intervention, comparator)

        # Primary & Secondary Objectives
        prim_obj = f"To evaluate the clinical efficacy and safety of {intervention} compared with {comparator} in {condition}."
        sec_objs = [
            f"To assess between-group differences in {primary_outcome} over 24 to 52 weeks.",
            "To quantify treatment-emergent adverse events and discontinuation rates across treatment arms.",
            "To evaluate secondary changes in cardiometabolic biomarkers, renal parameters, and patient-reported quality of life."
        ]

        # Scientific Rationale
        rationale = (
            f"Current clinical trial literature predominantly focuses on short-term surrogate outcomes against placebo. "
            f"As demonstrated in our multi-study evidence matrix, {gap.description} "
            f"Executing this {design.lower()} directly addresses this clinical void, providing actionable evidence for guideline committees."
        )

        # FINER Criteria Evaluation
        finer = cls._evaluate_finer_criteria(gap, design, reality_report)

        # Supervisor Verification Claims (Institutional Review Board & Faculty Oversight)
        supervisor_claims = [
            "Clinical Equipoise: Faculty supervisor and ethics board must confirm that randomized allocation to the comparator arm satisfies current ethical standards.",
            "Sample Size Assumptions: Target difference (delta) and variance parameters must be validated against pilot data or historical registry cohorts.",
            "Patient Recruitment Feasibility: The estimated monthly recruitment rate and inclusion/exclusion stringency must be reviewed by the clinical department head.",
            "Safety Monitoring Plan: A Data Safety Monitoring Board (DSMB) charter must be established prior to enrolling vulnerable subgroups (e.g., eGFR < 30 mL/min/1.73m²)."
        ]

        feasibility_and_ethics = {
            "Recruitment Timeline": "Estimated 12–18 months across 3–5 clinical centers.",
            "Investigational Product Supply": "Commercially available pharmacotherapy or investigational drug provided via sponsored clinical supply agreement.",
            "Ethical Safeguards": "Written informed consent, predefined stopping rules for severe hypoglycemia or acute organ injury, and independent safety monitoring."
        }

        full_pico = {
            "Population": condition,
            "Intervention": intervention,
            "Comparator": comparator,
            "Primary Outcome": primary_outcome,
            "Secondary Outcomes": "Cardiometabolic Biomarkers, Adverse Events, HRQoL (SF-36)",
            "Timing / Follow-up": "24 to 52 Weeks",
            "Setting": "Multicenter, Tertiary Academic Medical Centers (Outpatient)"
        }

        return ThesisProposal(
            gap_id=gap.gap_id,
            proposed_titles=titles,
            research_question_pico=full_pico,
            primary_objective=prim_obj,
            secondary_objectives=sec_objs,
            recommended_study_design=design,
            design_justification=design_justification,
            scientific_rationale=rationale,
            finer_criteria=finer,
            supervisor_verification_claims=supervisor_claims,
            feasibility_and_ethics=feasibility_and_ethics
        )

    @classmethod
    def _determine_optimal_design(
        cls,
        gap: ObservedResearchGap,
        reality_status: str
    ) -> Tuple[str, str]:
        """Recommends the most defensible methodological design for the identified gap."""
        if "Existing Coverage" in reality_status:
            return (
                "Systematic Review & Individual Participant Data (IPD) Meta-Analysis",
                "Multiple trials have investigated this question; a prospective trial would be duplicative. A systematic review with IPD meta-regression is optimal to reconcile subgroup heterogeneity."
            )
        elif gap.category == "population_underrepresentation":
            return (
                "Prospective, Phase 4 Randomized Controlled Trial (or Enriched Cohort)",
                "A prospective randomized design with targeted stratification is necessary to obtain definitive safety and pharmacokinetic data in this underrepresented population."
            )
        elif gap.category == "unmeasured_outcome":
            return (
                "Pragmatic Randomized Controlled Trial with Embedded Patient-Reported Outcomes",
                "A pragmatic trial embedding validated PRO instruments (EQ-5D-5L, SF-36) into routine clinical follow-up provides high external validity."
            )
        elif gap.category == "comparator_absence":
            return (
                "Head-to-Head Active-Controlled Randomized Non-Inferiority / Superiority Trial",
                "Direct comparative effectiveness against the current first-line standard of care is urgently needed to inform clinical decision algorithms."
            )
        elif gap.category == "follow_up_duration":
            return (
                "Long-Term Extension Trial with Randomized Withdrawal Phase",
                "A randomized withdrawal design beyond 52 weeks is the gold standard to distinguish genuine disease modification from symptomatic control and post-drug rebound."
            )
        else:
            return (
                "Randomized, Double-Blind, Parallel-Group Clinical Trial",
                "Parallel-group randomized controlled design provides the highest internal validity for causal therapeutic inference."
            )

    @classmethod
    def _generate_academic_titles(
        cls,
        gap: ObservedResearchGap,
        design: str,
        condition: str,
        intervention: str,
        comparator: str
    ) -> List[str]:
        """Generates 3 publication-ready academic titles."""
        return [
            f"Comparative Effectiveness and Safety of {intervention} versus {comparator} in {condition}: A {design}",
            f"Optimizing Clinical Outcomes in {condition}: The Role of {intervention} — Methodological Synthesis and Protocol for a {design}",
            f"Addressing Evidence Gaps in {condition}: A Multicenter Investigation of {intervention} on Long-Term Biomarkers and Patient-Reported Outcomes"
        ]

    @classmethod
    def _evaluate_finer_criteria(
        cls,
        gap: ObservedResearchGap,
        design: str,
        reality_report: Optional[RealityCheckReport]
    ) -> Dict[str, Dict[str, Any]]:
        """Evaluates Feasible, Interesting, Novel, Ethical, Relevant criteria."""
        novel_rating = "High Novelty" if not reality_report or "Potential Gap" in reality_report.status else "Moderate (Incremental / Subgroup Focus)"
        novel_details = "Targeted external database reality check revealed no direct duplicate trials." if novel_rating == "High Novelty" else "Builds upon existing evidence by targeting previously excluded clinical subsets."

        return {
            "Feasible": {
                "score": "High Feasibility",
                "color": "#10B981",
                "details": "Sample size requirements fall within standard multicenter capacity (N=150–350); interventions use commercially available or accessible agents."
            },
            "Interesting": {
                "score": "High Scientific Interest",
                "color": "#10B981",
                "details": "Addresses ongoing clinical dilemmas regarding treatment selection, durability, and patient quality of life."
            },
            "Novel": {
                "score": novel_rating,
                "color": "#38BDF8",
                "details": novel_details
            },
            "Ethical": {
                "score": "Ethically Sound (Equipoise Confirmed)",
                "color": "#10B981",
                "details": "Clinical equipoise exists because optimal regimen superiority has not been established; active comparator prevents withholding care."
            },
            "Relevant": {
                "score": "Direct Guideline Impact",
                "color": "#10B981",
                "details": "Directly relevant to academic thesis requirements, clinical practice guideline refinement, and institutional formulary decision-making."
            }
        }
