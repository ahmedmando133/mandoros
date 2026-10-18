"""
MANDOROS Phase 3: Research Gap & Thesis Navigator — Core Data Models.
Defines strongly-typed, schema-validated contracts for:
- Pillar I: Evidence Study & Cross-Trial Evidence Matrix
- Pillar II: External Literature & Registry Reality Check
- Pillar III: Methodological Assessment (RoB 2, ROBINS-I, CONSORT, GRADE)
- Pillar IV: Thesis Proposal & Research Question Blueprint (FINER, PICO/PICOTS)
- Pillar V: Protocol, Search Strategy & Biostatistical Planning (Sample Size)
"""

from __future__ import annotations

import os
import json
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional, Tuple, Union


@dataclass
class EvidenceStudy:
    """Represents a single clinical study analyzed within the Phase 3 evidence collection."""
    study_id: str
    title: str
    condition: str
    population_summary: str
    sample_size: int
    interventions: List[str] = field(default_factory=list)
    comparators: List[str] = field(default_factory=list)
    primary_outcomes: List[str] = field(default_factory=list)
    secondary_outcomes: List[str] = field(default_factory=list)
    safety_outcomes: List[str] = field(default_factory=list)
    follow_up_weeks: Optional[float] = None
    study_design: str = "Randomized Controlled Trial"
    blinding: str = "Double-Blind"
    eligibility_criteria_summary: str = ""
    source_file: str = ""
    key_findings: List[str] = field(default_factory=list)
    reported_limitations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ObservedResearchGap:
    """Represents a potential scientific gap discovered across the analyzed documents."""
    gap_id: str
    category: str  # e.g., "population_underrepresentation", "unmeasured_outcome", "dose_response_scarcity", "comparator_absence", "follow_up_duration", "methodological_limitation"
    title: str
    description: str
    observed_in_studies: List[str] = field(default_factory=list)
    evidence_rationale: str = ""
    candidate_pico: Dict[str, str] = field(default_factory=dict)
    confidence_score: float = 0.85
    verification_status: str = "Observed in Uploaded Cohort — Requires External Reality Check"
    status_color: str = "#38BDF8"  # Cyan for observed gap

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class EvidenceMatrix:
    """Structured matrix comparing all uploaded studies across standard clinical dimensions."""
    studies: List[EvidenceStudy] = field(default_factory=list)
    compared_populations: List[Dict[str, Any]] = field(default_factory=list)
    compared_interventions: List[Dict[str, Any]] = field(default_factory=list)
    compared_outcomes: List[Dict[str, Any]] = field(default_factory=list)
    compared_durations: List[Dict[str, Any]] = field(default_factory=list)
    observed_gaps: List[ObservedResearchGap] = field(default_factory=list)
    total_patients_pooled: int = 0
    common_condition: str = "Clinical Population"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class LiteratureMatch:
    """Individual external scholarly publication or registered clinical trial record."""
    source: str  # "OpenAlex", "PubMed", "ClinicalTrials.gov"
    record_id: str  # PMID, DOI, or NCT ID
    title: str
    year: Optional[int] = None
    authors_or_sponsor: str = ""
    url: str = ""
    relevance_tier: str = "Related Evidence"  # "Exact Match", "Related Evidence", "Indirect Evidence"
    overall_status: Optional[str] = None  # For ClinicalTrials: "RECRUITING", "COMPLETED", "TERMINATED"
    summary_snippet: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RealityCheckReport:
    """External verification report for a specific research gap."""
    gap_id: str
    search_query_used: str
    databases_queried: List[str] = field(default_factory=lambda: ["OpenAlex", "PubMed", "ClinicalTrials.gov"])
    status: str = "Potential Gap — Requires Further Verification"
    # Possible statuses:
    # - "Potential Gap — Requires Further Verification"
    # - "Related Evidence Found"
    # - "Existing Coverage Identified"
    # - "Ongoing or Registered Research Identified"
    # - "Search Incomplete — Insufficient Evidence"
    status_badge: str = "⚡ Potential Research Opportunity"
    status_color: str = "#F59E0B"  # Amber
    literature_matches: List[LiteratureMatch] = field(default_factory=list)
    registered_trials: List[LiteratureMatch] = field(default_factory=list)
    summary_verdict: str = ""
    limitations: List[str] = field(default_factory=list)
    timestamp: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MethodologicalAssessment:
    """Methodological quality and reporting completeness appraisal for an included study."""
    study_id: str
    framework: str  # "Cochrane RoB 2.0", "ROBINS-I", "CONSORT 2010", "GRADE"
    overall_rating: str  # "Low Risk", "Some Concerns", "High Risk", "High Certainty", etc.
    rating_color: str = "#10B981"
    domain_scores: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    # domain_name -> {"rating": str, "justification": str, "evidence_quote": str}
    consort_reporting_score: float = 100.0  # percentage
    grade_certainty: str = "Moderate"
    reviewer_overridden: bool = False
    reviewer_notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ThesisProposal:
    """Structured research proposal and thesis blueprint generated from a defensible gap."""
    gap_id: str
    proposed_titles: List[str] = field(default_factory=list)
    research_question_pico: Dict[str, str] = field(default_factory=dict)
    # {"population": ..., "intervention": ..., "comparator": ..., "outcome": ..., "timing": ..., "setting": ...}
    primary_objective: str = ""
    secondary_objectives: List[str] = field(default_factory=list)
    recommended_study_design: str = "Randomized Controlled Trial"
    design_justification: str = ""
    scientific_rationale: str = ""
    finer_criteria: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    # {"Feasible": {"score": "High", "details": ...}, "Interesting": ..., "Novel": ..., "Ethical": ..., "Relevant": ...}
    supervisor_verification_claims: List[str] = field(default_factory=list)
    feasibility_and_ethics: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SampleSizeSpec:
    """Biostatistical sample size calculation specification."""
    design_type: str  # "two_sample_continuous", "two_sample_binary", "non_inferiority_continuous", "non_inferiority_binary"
    primary_outcome_name: str
    alpha: float = 0.05
    power: float = 0.80
    allocation_ratio: float = 1.0  # N2 / N1
    attrition_rate: float = 0.15  # 15% drop-out
    input_parameters: Dict[str, float] = field(default_factory=dict)
    # Continuous: {"mean_diff": 5.0, "sd_pooled": 10.0}
    # Binary: {"p1": 0.40, "p2": 0.25}
    n_per_group: int = 0
    n_total_evaluable: int = 0
    n_total_with_attrition: int = 0
    mathematical_formula: str = ""
    assumptions_rationale: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ProtocolDraft:
    """Complete structured draft protocol package (PRISMA-P / SPIRIT / PROSPERO)."""
    framework: str  # "SPIRIT 2013 (RCT)" or "PRISMA-P (Systematic Review)" or "PROSPERO Registration"
    sections: Dict[str, str] = field(default_factory=dict)
    pubmed_search_strategy: str = ""
    mesh_terms_used: List[str] = field(default_factory=list)
    boolean_query: str = ""
    prospero_checklist: List[Dict[str, str]] = field(default_factory=list)
    download_filename: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Phase3Dossier:
    """Consolidated end-to-end dossier encompassing all five Phase 3 pillars."""
    dossier_id: str
    target_topic: str
    evidence_matrix: EvidenceMatrix
    reality_check_reports: List[RealityCheckReport] = field(default_factory=list)
    methodological_assessments: List[MethodologicalAssessment] = field(default_factory=list)
    thesis_proposals: List[ThesisProposal] = field(default_factory=list)
    sample_size_plan: Optional[SampleSizeSpec] = None
    protocol_draft: Optional[ProtocolDraft] = None
    generated_at: str = ""
    markdown_report: str = ""
    excel_path: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        return d
