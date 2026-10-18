"""
Automated Comprehensive Test Suite for MANDOROS Phase 3: Research Gap & Thesis Navigator.
Verifies all 5 pillars, biostatistical calculations, multi-sheet Excel generation,
and isolated error resilience.
"""

import os
import sys
from pathlib import Path
import pytest
import pandas as pd

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.phase3.models import (
    EvidenceStudy,
    EvidenceMatrix,
    ObservedResearchGap,
    LiteratureMatch,
    RealityCheckReport,
    MethodologicalAssessment,
    ThesisProposal,
    SampleSizeSpec,
    ProtocolDraft,
    Phase3Dossier
)
from src.phase3.evidence_mapper import EvidenceMapperEngine
from src.phase3.reality_check import RealityCheckEngine
from src.phase3.quality_assessor import QualityAssessorEngine
from src.phase3.thesis_architect import ThesisArchitectEngine
from src.phase3.protocol_planner import ProtocolPlannerEngine
from src.phase3.exporter import Phase3DossierExporter
from src.phase3.orchestrator import Phase3NavigatorOrchestrator


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------
@pytest.fixture
def sample_study():
    return EvidenceStudy(
        study_id="NCT04567890",
        title="Efficacy and Safety of Tirzepatide in Type 2 Diabetes: A 40-Week Randomized Trial",
        condition="Type 2 Diabetes Mellitus",
        population_summary="Adults with T2D (HbA1c 7.5-10.5%, N=475, Female: 48%)",
        sample_size=475,
        interventions=["Tirzepatide 15mg Once-Weekly"],
        comparators=["Matching Placebo"],
        primary_outcomes=["Change in HbA1c at Week 40 (%)"],
        secondary_outcomes=["Body Weight Change (%)", "Fasting Glucose (mg/dL)"],
        safety_outcomes=["Nausea", "Diarrhea", "Hypoglycemia"],
        follow_up_weeks=40.0,
        study_design="Randomized, Double-Blind, Parallel-Group Clinical Trial",
        blinding="Double-Blind",
        eligibility_criteria_summary="Inclusion: Age 18-75, BMI >= 25; Exclusion: eGFR < 30 mL/min/1.73m2",
        source_file="Tirzepatide_Trial.pdf",
        key_findings=["Achieved significant HbA1c reduction (-2.1%) vs placebo."],
        reported_limitations=["Short duration beyond 40 weeks; excluded severe renal impairment."]
    )


@pytest.fixture
def sample_study_2():
    return EvidenceStudy(
        study_id="NCT03876543",
        title="Cardiovascular Outcomes with Semaglutide in Patients with Overweight and Established CVD",
        condition="Obesity & Cardiovascular Disease",
        population_summary="Adults aged >= 45 years with established CVD and BMI >= 27 (N=17604)",
        sample_size=17604,
        interventions=["Semaglutide 2.4mg Once-Weekly"],
        comparators=["Placebo"],
        primary_outcomes=["Time to First Major Adverse Cardiovascular Event (MACE)"],
        secondary_outcomes=["Death from CV Causes", "Non-fatal Myocardial Infarction"],
        safety_outcomes=["Gastrointestinal Disorders", "Gallbladder-related Disorders"],
        follow_up_weeks=156.0,
        study_design="Randomized, Double-Blind, Event-Driven Trial",
        blinding="Double-Blind",
        eligibility_criteria_summary="Age >= 45 with established cardiovascular disease; no prior diabetes.",
        source_file="Semaglutide_SELECT.pdf",
        key_findings=["Reduced primary composite MACE by 20%."],
        reported_limitations=["Underrepresentation of patients aged >= 80."]
    )


# -----------------------------------------------------------------------------
# Pillar I: Evidence Mapping & Gap Discovery Tests
# -----------------------------------------------------------------------------
def test_pillar1_evidence_matrix_construction(sample_study, sample_study_2):
    """Tests cross-trial evidence matrix construction and patient pooling."""
    matrix = EvidenceMapperEngine.build_evidence_matrix([sample_study, sample_study_2])
    assert matrix.total_patients_pooled == 475 + 17604
    assert len(matrix.studies) == 2
    assert len(matrix.compared_populations) == 2
    assert len(matrix.compared_interventions) == 2
    assert len(matrix.compared_outcomes) == 2
    assert len(matrix.observed_gaps) >= 3


def test_pillar1_algorithmic_gap_detection(sample_study):
    """Tests detection of active comparator void, unmeasured PROs, and high-risk exclusions."""
    matrix = EvidenceMapperEngine.build_evidence_matrix([sample_study])
    gap_categories = [g.category for g in matrix.observed_gaps]

    # Must detect: comparator_absence (since only placebo was used)
    assert "comparator_absence" in gap_categories
    # Must detect: unmeasured_outcome (since no QoL/PROs were measured)
    assert "unmeasured_outcome" in gap_categories
    # Must detect: population_underrepresentation (renal eGFR < 30 excluded)
    assert "population_underrepresentation" in gap_categories


def test_pillar1_phase1_excel_ingestion():
    """Tests loading a real Phase 1 Excel workbook if present in repo."""
    excel_candidates = [
        "outputs/orlistat_structured_extracted.xlsx",
        "outputs/metformin_structured_extracted.xlsx",
        "outputs/semaglutide_structured_extracted.xlsx"
    ]
    found_any = False
    for path in excel_candidates:
        if os.path.exists(path):
            studies = EvidenceMapperEngine.ingest_documents([path])
            assert len(studies) >= 1
            assert studies[0].sample_size > 0
            found_any = True
            break

    # If output excel not present, test generic fallback
    if not found_any:
        studies = EvidenceMapperEngine.ingest_documents(["non_existent_file.pdf"])
        assert len(studies) == 0


# -----------------------------------------------------------------------------
# Pillar II: External Reality Check Tests
# -----------------------------------------------------------------------------
def test_pillar2_query_construction():
    """Tests PICO-informed query string generation."""
    gap = ObservedResearchGap(
        gap_id="GAP-001",
        category="comparator_absence",
        title="Absence of Head-to-Head Active Comparator",
        description="Placebo only",
        candidate_pico={
            "population": "Type 2 Diabetes",
            "intervention": "Tirzepatide",
            "comparator": "Semaglutide",
            "outcome": "HbA1c"
        }
    )
    query = RealityCheckEngine._construct_search_query(gap)
    assert "Type 2 Diabetes" in query or "Tirzepatide" in query


def test_pillar2_offline_resilience_and_graceful_fallback():
    """Tests that network timeouts or disconnects do NOT crash the system."""
    gap = ObservedResearchGap(
        gap_id="GAP-TEST",
        category="population_underrepresentation",
        title="Geriatric Subgroup Gap",
        description="Elderly population",
        candidate_pico={"population": "Heart Failure", "intervention": "Empagliflozin"}
    )
    # Force fallback by passing simulated errors
    fallback_report = RealityCheckEngine._generate_graceful_offline_report(
        gap=gap,
        query="Heart Failure Empagliflozin",
        timestamp="2026-10-18 12:00:00 UTC",
        errors=["Simulated Timeout"]
    )
    assert fallback_report.status == "Search Incomplete — Insufficient Evidence"
    assert len(fallback_report.literature_matches) >= 1
    assert len(fallback_report.registered_trials) >= 1
    assert "Simulated Timeout" in fallback_report.limitations[1]


# -----------------------------------------------------------------------------
# Pillar III: Methodological Quality (RoB 2.0 / CONSORT) Tests
# -----------------------------------------------------------------------------
def test_pillar3_cochrane_rob2_assessment(sample_study):
    """Tests Cochrane RoB 2.0 appraisal logic."""
    assessment = QualityAssessorEngine.assess_study_methodology(sample_study, framework="Cochrane RoB 2.0")
    assert assessment.framework == "Cochrane RoB 2.0"
    assert assessment.overall_rating in ["Low Risk", "Some Concerns", "High Risk"]
    assert len(assessment.domain_scores) == 5
    assert "D1: Randomisation Process" in assessment.domain_scores
    assert assessment.consort_reporting_score >= 80.0


def test_pillar3_consort_checklist(sample_study):
    """Tests CONSORT 2010 reporting appraisal."""
    assessment = QualityAssessorEngine.assess_study_methodology(sample_study, framework="CONSORT 2010")
    assert assessment.framework == "CONSORT 2010"
    assert "Item 1: Title & Abstract (RCT Identification)" in assessment.domain_scores
    assert assessment.consort_reporting_score >= 90.0


def test_pillar3_human_override(sample_study):
    """Tests that researcher can override automated quality rating with notes."""
    assessment = QualityAssessorEngine.assess_study_methodology(sample_study, framework="Cochrane RoB 2.0")
    overridden = QualityAssessorEngine.apply_human_override(
        assessment=assessment,
        new_rating="High Risk",
        notes="Concern over unblinded rescue medication in secondary subgroup."
    )
    assert overridden.overall_rating == "High Risk"
    assert overridden.reviewer_overridden is True
    assert "rescue medication" in overridden.reviewer_notes


# -----------------------------------------------------------------------------
# Pillar IV: Thesis Proposal Blueprint Tests
# -----------------------------------------------------------------------------
def test_pillar4_thesis_proposal_generation(sample_study):
    """Tests generation of academic titles, PICO, and FINER criteria."""
    gap = ObservedResearchGap(
        gap_id="GAP-001",
        category="comparator_absence",
        title="Head-to-Head Active Controlled Void",
        description="No direct trials against SGLT2i",
        candidate_pico={
            "population": "Adults with T2D and high CV risk",
            "intervention": "Tirzepatide 15mg",
            "comparator": "Empagliflozin 25mg",
            "outcome": "Cardiometabolic composite"
        }
    )
    proposal = ThesisArchitectEngine.develop_thesis_proposal(gap=gap, studies=[sample_study])
    assert len(proposal.proposed_titles) == 3
    assert proposal.primary_objective != ""
    assert len(proposal.secondary_objectives) >= 2
    assert "Feasible" in proposal.finer_criteria
    assert len(proposal.supervisor_verification_claims) >= 3


# -----------------------------------------------------------------------------
# Pillar V: Biostatistical Sample Size Calculation Tests (Validated Formulas)
# -----------------------------------------------------------------------------
def test_pillar5_two_sample_continuous_sample_size():
    """
    Standard Reference Check:
    Delta = 5.0, SD = 10.0 (Cohen's d = 0.50), Alpha = 0.05 (two-sided, Z=1.960), Power = 0.80 (Z=0.842).
    Standard textbook formula gives n ≈ 63-64 per group, N_eval ≈ 126-128.
    With 15% attrition: N_total ≈ 128 / 0.85 ≈ 151.
    """
    spec = ProtocolPlannerEngine.calculate_sample_size(
        design_type="two_sample_continuous",
        primary_outcome_name="Reduction in Body Weight (kg)",
        alpha=0.05,
        power=0.80,
        allocation_ratio=1.0,
        attrition_rate=0.15,
        param_inputs={"mean_difference": 5.0, "pooled_sd": 10.0}
    )
    assert 62 <= spec.n_per_group <= 65, f"Expected n_per_group ~ 63-64, got {spec.n_per_group}"
    assert 124 <= spec.n_total_evaluable <= 130
    assert 145 <= spec.n_total_with_attrition <= 155
    assert "Z_(1-α/2)" in spec.mathematical_formula


def test_pillar5_two_sample_binary_sample_size():
    """
    Standard Reference Check for Proportions:
    p1 = 0.45, p2 = 0.25 (Diff = 0.20), Alpha = 0.05, Power = 0.80.
    Standard textbook n ≈ 85-95 per group.
    """
    spec = ProtocolPlannerEngine.calculate_sample_size(
        design_type="two_sample_binary",
        primary_outcome_name="Proportion Achieving >= 5% Weight Loss",
        alpha=0.05,
        power=0.80,
        allocation_ratio=1.0,
        attrition_rate=0.10,
        param_inputs={"p1_experimental": 0.45, "p2_control": 0.25}
    )
    assert 80 <= spec.n_per_group <= 100, f"Expected n_per_group ~ 88-92, got {spec.n_per_group}"
    assert spec.n_total_with_attrition > spec.n_total_evaluable


def test_pillar5_reproducible_pubmed_query(sample_study):
    """Tests generation of reproducible Boolean query with MeSH terms."""
    gap = ObservedResearchGap(
        gap_id="GAP-001",
        category="comparator_absence",
        title="Active Comparator Void",
        description="Placebo only",
        candidate_pico={"population": "Type 2 Diabetes", "intervention": "Tirzepatide"}
    )
    proposal = ThesisArchitectEngine.develop_thesis_proposal(gap, studies=[sample_study])
    boolean_query, mesh_terms, doc = ProtocolPlannerEngine.generate_pubmed_search_strategy(proposal)

    assert "AND" in boolean_query
    assert "MeSH" in boolean_query or "Title/Abstract" in boolean_query
    assert len(mesh_terms) >= 2
    assert "Reproducible PubMed Search Strategy" in doc


# -----------------------------------------------------------------------------
# Exporter & Multi-Sheet Excel Verification
# -----------------------------------------------------------------------------
def test_phase3_excel_and_markdown_export(sample_study):
    """Verifies that all 7 sheets are generated in the Excel deliverable."""
    dossier = Phase3NavigatorOrchestrator.process_research_navigator(
        files=[],  # will use benchmark study
        selected_gap_index=0
    )
    assert dossier.excel_path is not None
    assert os.path.exists(dossier.excel_path)

    # Inspect sheets with openpyxl
    import openpyxl
    wb = openpyxl.load_workbook(dossier.excel_path)
    sheet_names = wb.sheetnames

    assert len(sheet_names) == 7
    expected_sheets = [
        "1_Evidence_Matrix",
        "2_Research_Gaps",
        "3_Reality_Check",
        "4_Quality_Assessment_RoB",
        "5_Thesis_Proposal",
        "6_Sample_Size_Planning",
        "7_Protocol_and_Strategy"
    ]
    for exp in expected_sheets:
        assert exp in sheet_names, f"Missing sheet: {exp} in {sheet_names}"

    # Verify Markdown export
    md_file = os.path.join("outputs", f"MANDOROS_Phase3_Dossier_{dossier.target_topic.replace(' ', '_')[:30]}.md")
    assert os.path.exists(md_file)
    with open(md_file, "r", encoding="utf-8") as f:
        md_text = f.read()
    assert "Pillar I: Evidence Mapping" in md_text
    assert "Pillar V: Biostatistical Sample Size Planning" in md_text


# -----------------------------------------------------------------------------
# End-to-End Orchestrator UI Formatting Test
# -----------------------------------------------------------------------------
def test_phase3_ui_formatting_contract():
    """Verifies the tuple contract for Gradio UI rendering."""
    dossier = Phase3NavigatorOrchestrator.process_research_navigator(files=[])
    outputs = Phase3NavigatorOrchestrator.format_ui_outputs(dossier)

    assert len(outputs) == 9
    (verdict_html, matrix_df, gaps_df, rc_html, rob_df, prop_html, proto_html, xl_path, md_path) = outputs

    assert "<div" in verdict_html
    assert isinstance(matrix_df, pd.DataFrame)
    assert isinstance(gaps_df, pd.DataFrame)
    assert not gaps_df.empty
    assert isinstance(rob_df, pd.DataFrame)
    assert "<div" in prop_html
    assert "<div" in proto_html
    assert xl_path.endswith(".xlsx")
    assert md_path.endswith(".md")
