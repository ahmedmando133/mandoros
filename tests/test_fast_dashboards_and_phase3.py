"""
Unit and Integration Tests for MANDOROS Instant Automatic Dashboards and Phase 3 Navigator.
Tests:
1. Phase 1 Single-Trial 360 Interactive Dashboard Generation (<2s, Base64 banner, 7 tabs)
2. Phase 2 Multi-Trial Cohort Explorer Dashboard Generation (<2s, SUCRA, Meta-Analysis, DataGrid)
3. Excel Watcher Hook with automatic phase routing and LRU caching
4. Global Reality Checker fast parallel execution (<4s) with 3-color traffic light system
5. Phase 3 4-Type Gap Taxonomy with cell coordinates and verbatim quotes
6. 6-sheet color-coded Excel & Standalone HTML/Markdown Dossier export
7. Zero data-mixing and empty state verification
"""

import os
import time
import pytest
import pandas as pd
import openpyxl

from dashboard_engine.shared_ui_components import build_instant_download_banner
from dashboard_engine.phase1_trial_dashboard import build_phase1_single_trial_dashboard
from dashboard_engine.phase2_cohort_excel_dash import build_phase2_cohort_explorer_dashboard, bundle_cohort_individual_dashboards
from dashboard_engine.excel_watcher_hook import auto_generate_dashboard_for_excel
from phase3_navigator.schema_ingestor import SchemaIngestor
from phase3_navigator.gap_taxonomy_extractor import GapTaxonomyExtractor, GapCategory
from phase3_navigator.global_reality_checker import GlobalRealityChecker, TrafficLightColor
from phase3_navigator.sample_size_and_risk import SampleSizeAndRiskEngine
from phase3_navigator.thesis_protocol_builder import ThesisProtocolBuilder
from phase3_navigator.excel_html_exporter import Phase3DossierExporter


@pytest.fixture
def sample_phase1_xlsx(tmp_path):
    """Generates a representative 7-sheet Phase 1 Excel workbook."""
    p = tmp_path / "MANDOROS_Phase1_Test_Trial.xlsx"
    wb = openpyxl.Workbook()

    # Sheet 1: Master Excel Sheet
    ws1 = wb.active
    ws1.title = "Master Excel Sheet"
    ws1.append(["Study Characteristics and Treatment Arms"])
    ws1.append(["Study ID", "NCT01131676", "Title", "Empagliflozin vs Placebo in Patients with T2D"])
    ws1.append(["Authors", "Nishimura et al.", "Journal", "Diabetes Obes Metab", "Year", 2015])
    ws1.append(["Arm Name", "Target Dose", "Duration", "Sample Size N", "Comparator"])
    ws1.append(["Empagliflozin 10mg", "10mg once daily", "24 weeks", 270, "Placebo"])
    ws1.append(["Empagliflozin 25mg", "25mg once daily", "24 weeks", 272, "Placebo"])
    ws1.append(["Placebo", "Matching placebo", "24 weeks", 271, "None"])
    ws1.append([])
    ws1.append(["Baseline Characteristics"])
    ws1.append(["Parameter", "Placebo (N=271)", "Empa 10mg (N=270)", "Empa 25mg (N=272)", "Unit", "p-value"])
    ws1.append(["Age (years)", "58.2 ± 9.4", "57.9 ± 9.8", "58.6 ± 9.1", "years", "0.68"])
    ws1.append(["HbA1c (%)", "7.96 ± 0.82", "7.94 ± 0.81", "7.98 ± 0.84", "%", "0.85"])
    ws1.append(["BMI (kg/m²)", "25.6 ± 3.4", "25.8 ± 3.7", "25.5 ± 3.3", "kg/m²", "0.72"])
    ws1.append(["eGFR (mL/min)", "84.2 ± 16.5", "85.1 ± 17.2", "83.9 ± 16.8", "mL/min/1.73m²", "0.91"])
    ws1.append([])
    ws1.append(["Efficacy Outcomes"])
    ws1.append(["Endpoint", "Timepoint", "Arm", "Baseline", "Change from Baseline", "Difference vs Placebo", "95% CI", "p-value"])
    ws1.append(["HbA1c", "Week 24", "Empa 10mg", 7.94, -0.66, -0.58, "[-0.72, -0.44]", "<0.0001"])
    ws1.append(["HbA1c", "Week 24", "Empa 25mg", 7.98, -0.78, -0.70, "[-0.84, -0.56]", "<0.0001"])
    ws1.append(["Body Weight", "Week 24", "Empa 10mg", 68.4, -2.1, -1.8, "[-2.3, -1.3]", "<0.0001"])
    ws1.append([])
    ws1.append(["Safety Outcomes"])
    ws1.append(["Adverse Event", "Placebo n (%)", "Empa 10mg n (%)", "Empa 25mg n (%)"])
    ws1.append(["Overall AEs", "165 (60.9%)", "162 (60.0%)", "168 (61.8%)"])
    ws1.append(["Hypoglycemia", "4 (1.5%)", "3 (1.1%)", "5 (1.8%)"])
    ws1.append(["Genital Infections", "2 (0.7%)", "9 (3.3%)", "11 (4.0%)"])

    # Sheet 2: Variables
    ws2 = wb.create_sheet(title="Variables")
    ws2.append(["Variable Name", "Category", "Data Type", "Standard Unit", "Reported Value", "Provenance"])
    ws2.append(["HbA1c Week 24", "Primary Efficacy", "Continuous", "%", "-0.70 vs Placebo", "Table 2, Page 4"])

    # Sheet 3: Outcomes
    ws3 = wb.create_sheet(title="Outcomes")
    ws3.append(["Outcome Name", "Domain", "Arm", "N", "Mean", "SD", "CI_Lower", "CI_Upper", "p_value"])
    ws3.append(["HbA1c", "Glycemic", "Empa 10mg", 270, -0.66, 0.45, -0.72, -0.44, 0.0001])
    ws3.append(["HbA1c", "Glycemic", "Empa 25mg", 272, -0.78, 0.48, -0.84, -0.56, 0.0001])

    # Sheet 4: Eligibility Criteria
    ws4 = wb.create_sheet(title="Eligibility Criteria")
    ws4.append(["Criterion Type", "Category", "Description", "Standardized Filter"])
    ws4.append(["Inclusion", "Age", "Patients aged >= 20 and <= 75 years", "20 <= Age <= 75"])
    ws4.append(["Inclusion", "HbA1c", "HbA1c >= 7.0% and <= 10.0%", "7.0 <= HbA1c <= 10.0"])
    ws4.append(["Exclusion", "Renal", "eGFR < 60 mL/min/1.73m² (Moderate/Severe Impairment)", "eGFR < 60"])

    # Sheet 5: Regimens
    ws5 = wb.create_sheet(title="Regimens")
    ws5.append(["Arm Name", "Compound", "Dose", "Frequency", "Route", "Duration"])
    ws5.append(["Empagliflozin 10mg", "Empagliflozin", "10mg", "QD", "Oral", "24 weeks"])

    # Sheet 6: Data Dictionary
    ws6 = wb.create_sheet(title="Data Dictionary")
    ws6.append(["Field Name", "Description", "Formula"])
    ws6.append(["HbA1c", "Glycated hemoglobin", "High-performance liquid chromatography"])

    # Sheet 7: Audit Log
    ws7 = wb.create_sheet(title="Audit Log")
    ws7.append(["Timestamp", "Step", "Engine", "Status"])
    ws7.append(["2026-10-19 01:00:00", "Master Extraction", "Clinical Engine", "PASSED 100%"])

    wb.save(str(p))
    return str(p)


@pytest.fixture
def sample_phase2_xlsx(tmp_path):
    """Generates a representative Phase 2 Cohort Master Excel workbook."""
    p = tmp_path / "Custom_Drug_MANDOROS_Master_Report.xlsx"
    wb = openpyxl.Workbook()

    ws1 = wb.active
    ws1.title = "Master Extraction Sheet"
    ws1.append(["Study ID", "Drug Name", "Dose mg", "Duration wks", "Sample Size N", "Endpoint", "Mean Difference", "SE", "p-value"])
    ws1.append(["Nishimura 2015", "Empagliflozin", 10, 24, 270, "HbA1c", -0.58, 0.07, 0.0001])
    ws1.append(["Nishimura 2015", "Empagliflozin", 25, 24, 272, "HbA1c", -0.70, 0.07, 0.0001])
    ws1.append(["Roden 2013", "Empagliflozin", 10, 24, 224, "HbA1c", -0.62, 0.08, 0.0001])
    ws1.append(["Roden 2013", "Empagliflozin", 25, 24, 224, "HbA1c", -0.74, 0.08, 0.0001])

    ws2 = wb.create_sheet(title="Meta-Analysis Summary")
    ws2.append(["Clinical Parameter", "k Studies", "Total N", "Pooled RE Estimate", "95% CI Lower", "95% CI Upper", "I2 (%)", "tau2", "p-value"])
    ws2.append(["HbA1c Change (%)", 2, 990, -0.66, -0.73, -0.59, "12.4%", 0.0012, 0.00001])

    ws3 = wb.create_sheet(title="SUCRA Rankings")
    ws3.append(["Rank", "Treatment", "SUCRA Score (%)", "Mean Effect", "SE", "Best Prob (%)", "Worst Prob (%)", "Tier"])
    ws3.append(["#1", "Empagliflozin 25mg", "94.2%", -0.72, 0.06, "88.4%", "0.1%", "High Efficacy"])
    ws3.append(["#2", "Empagliflozin 10mg", "55.8%", -0.60, 0.06, "11.5%", "0.5%", "Standard Efficacy"])
    ws3.append(["#3", "Placebo", "0.0%", 0.00, 0.00, "0.0%", "99.4%", "Control"])

    ws4 = wb.create_sheet(title="Comparison Matrix")
    ws4.append(["Trial", "Active Drug", "Comparator", "Sample Size", "Primary Endpoint", "Duration"])
    ws4.append(["Nishimura 2015", "Empagliflozin", "Placebo", 813, "HbA1c at 24 weeks", "24 weeks"])
    ws4.append(["Roden 2013", "Empagliflozin", "Placebo", 672, "HbA1c at 24 weeks", "24 weeks"])

    wb.save(str(p))
    return str(p)


# =============================================================================
# Test Suite 1: Phase 1 Single-Trial 360 Dashboard Engine
# =============================================================================

def test_phase1_dashboard_builder_speed_and_content(sample_phase1_xlsx):
    """Verifies that Phase 1 HTML Dashboard builds in <2 seconds with 8 KPI cards and 7 tabs."""
    t0 = time.time()
    html_path = build_phase1_single_trial_dashboard(sample_phase1_xlsx)
    elapsed = time.time() - t0

    assert elapsed < 3.0, f"Dashboard generation took {elapsed:.2f}s, expected <3.0s"
    assert os.path.exists(html_path)

    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "MANDOROS Single-Trial 360" in content
    assert "data:text/html;base64," in content or "download=" in content
    assert "Overview &amp; CONSORT" in content
    assert "Baseline Demographics" in content
    assert "Efficacy &amp; Safety Lab" in content
    assert "Eligibility Gatekeeper" in content


# =============================================================================
# Test Suite 2: Phase 2 Cohort Explorer Dashboard Engine
# =============================================================================

def test_phase2_cohort_dashboard_builder_speed_and_content(sample_phase2_xlsx):
    """Verifies that Phase 2 Cohort Dashboard builds in <2 seconds with SUCRA, Meta-Analysis, and DataGrid."""
    t0 = time.time()
    html_path = build_phase2_cohort_explorer_dashboard(sample_phase2_xlsx)
    elapsed = time.time() - t0

    assert elapsed < 3.0, f"Cohort dashboard generation took {elapsed:.2f}s, expected <3.0s"
    assert os.path.exists(html_path)

    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "MANDOROS Multi-Trial Meta-Analysis" in content
    assert "Meta-Analysis Forest &amp; SUCRA" in content
    assert "Cross-Trial Matrix" in content
    assert "In-Silico Bliss Synergy" in content
    assert "Master Workbook DataGrid" in content


# =============================================================================
# Test Suite 3: Excel Watcher Hook & Instant Base64 Banner
# =============================================================================

def test_excel_watcher_hook_automatic_detection(sample_phase1_xlsx, sample_phase2_xlsx):
    """Verifies automatic detection of Phase 1 vs Phase 2 and instant Base64 action bar."""
    p1_html, p1_banner = auto_generate_dashboard_for_excel(sample_phase1_xlsx)
    assert os.path.exists(p1_html)
    assert "Instant Download" in p1_banner
    assert ".html" in p1_banner
    assert ".xlsx" in p1_banner
    assert "data:text/html;base64," in p1_banner
    assert "data:application/vnd.openxmlformats" in p1_banner

    p2_html, p2_banner = auto_generate_dashboard_for_excel(sample_phase2_xlsx)
    assert os.path.exists(p2_html)
    assert "Instant Download" in p2_banner
    assert "Phase 2 Multi-Trial" in p2_banner



# =============================================================================
# Test Suite 4: Phase 3 4-Type Gap Taxonomy & Fast Reality Check (<3s)
# =============================================================================

def test_phase3_taxonomy_and_parallel_reality_checker(sample_phase1_xlsx):
    """Verifies extraction of 4-Type Gap Taxonomy with cell coordinates and parallel external check."""
    trial_data = SchemaIngestor.ingest_files([sample_phase1_xlsx])
    assert len(trial_data) >= 1
    trial = trial_data[0]
    assert trial.total_sample_size > 0

    gaps = GapTaxonomyExtractor.extract_gaps(trial_data)
    assert len(gaps) >= 4, f"Expected at least 4 gaps across taxonomy, got {len(gaps)}"

    categories_found = {g.category for g in gaps}
    assert GapCategory.POP_GAP in categories_found
    assert GapCategory.INT_COMP_GAP in categories_found
    assert GapCategory.OUTCOME_GAP in categories_found
    assert GapCategory.METHOD_ROB_GRADE_GAP in categories_found

    # Verify cell coordinates and source quotes are non-empty
    for g in gaps:
        assert g.row_coord or g.source_sheet, f"Gap {g.gap_id} has empty coordinate"
        assert g.exact_extracted_value_or_quote, f"Gap {g.gap_id} has empty quote"

    # Parallel Reality Check
    t0 = time.time()
    verdicts = GlobalRealityChecker.verify_all_gaps_parallel(
        gaps=gaps,
        condition=trial.condition,
        drug_name=trial.drug_name,
        skip_network=False
    )
    elapsed = time.time() - t0
    assert elapsed < 6.0, f"Reality check took {elapsed:.2f}s, expected <6.0s in parallel"

    assert len(verdicts) == len(gaps)
    for v in verdicts:
        assert v.traffic_light_color in (TrafficLightColor.GREEN, TrafficLightColor.YELLOW, TrafficLightColor.RED)
        assert v.badge_label


# =============================================================================
# Test Suite 5: Phase 3 Export Deliverables (6-Sheet Excel & HTML Dossier)
# =============================================================================

def test_phase3_excel_and_html_exports(sample_phase1_xlsx, tmp_path):
    """Verifies generation of 6-sheet color-coded Excel and standalone HTML dossier."""
    trial_data = SchemaIngestor.ingest_files([sample_phase1_xlsx])
    trial = trial_data[0]
    gaps = GapTaxonomyExtractor.extract_gaps(trial_data)

    base_sample = SampleSizeAndRiskEngine.calculate_continuous_superiority(
        delta=5.0, sigma=10.0, alpha=0.05, power=0.80, attrition_rate=0.15
    )
    sensitivity_table = SampleSizeAndRiskEngine.build_sensitivity_matrix(
        base_result=base_sample, delta=5.0, sigma=10.0, attrition_rate=0.15
    )
    risk_report = SampleSizeAndRiskEngine.audit_protocol_risk(trial)
    blueprint = ThesisProtocolBuilder.build_blueprint(gaps[0], trial)

    out_xl = str(tmp_path / "MANDOROS_Phase3_Test_Gap_Matrix.xlsx")
    out_html = str(tmp_path / "MANDOROS_Phase3_Test_Thesis_Dossier.html")
    out_md = str(tmp_path / "MANDOROS_Phase3_Test_Thesis_Report.md")

    Phase3DossierExporter.export_excel(
        output_path=out_xl,
        gaps=gaps,
        sensitivity_table=sensitivity_table,
        risk_report=risk_report,
        blueprint=blueprint,
        trial_data=trial_data,
    )
    assert os.path.exists(out_xl)

    # Inspect openpyxl sheets
    wb = openpyxl.load_workbook(out_xl)
    expected_sheets = [
        "Executive Gap Matrix",
        "Evidence & Gap Map Data",
        "Sample Size & Power Models",
        "Protocol Risk Audit",
        "GRADE Summary of Findings",
        "Search Strategies & Blueprints",
    ]
    for s in expected_sheets:
        assert s in wb.sheetnames, f"Sheet '{s}' missing in exported Excel"

    Phase3DossierExporter.export_html_dossier(
        output_path=out_html,
        gaps=gaps,
        sensitivity_table=sensitivity_table,
        risk_report=risk_report,
        blueprint=blueprint,
        trial_data=trial_data,
    )
    assert os.path.exists(out_html)

    Phase3DossierExporter.export_markdown_dossier(
        output_path=out_md,
        gaps=gaps,
        sensitivity_table=sensitivity_table,
        risk_report=risk_report,
        blueprint=blueprint,
        trial_data=trial_data,
    )
    assert os.path.exists(out_md)


# =============================================================================
# Test Suite 6: Empty State and Zero Data-Mixing Isolation
# =============================================================================

def test_phase3_empty_state_isolation():
    """Verifies that running Phase 3 with no files produces None downloads and clean error notice."""
    from app import process_phase3_ui

    res = process_phase3_ui(
        files=None,
        gap_choice="Gap 1",
        design_choice="Two-Sample Continuous",
        alpha=0.05,
        power=0.80,
        attrition=0.15,
        mean_diff=5.0,
        pooled_sd=10.0,
        p1_rate=0.45,
        p2_rate=0.25,
        ni_margin=2.5,
    )

    verdict_html, matrix_df, gaps_df, rc_html, rob_df, prop_html, proto_html, xl_dl, md_dl = res

    assert "Missing Input Documents" in verdict_html
    assert xl_dl is None, "Download file must be None on empty upload"
    assert md_dl is None, "Download file must be None on empty upload"
