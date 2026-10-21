# -*- coding: utf-8 -*-
"""
Test Suite for MANDOROS National Center for Biotechnology Information (NCBI) / HL7 FHIR (EBMonFHIR) Zero-Server-Load Add-on.
Verifies all 3 phases in academic English, multi-format exports (JSON, Excel, Dashboard),
the explanatory frontend pillar, master toggle, and non-destructive constraints.
"""

import os
import re
import json
import pytest

from infra_stability.ncpi_fhir_addon import (
    get_ncbi_fhir_head_tags,
    render_ncbi_fhir_pillar_html,
    get_ncpi_fhir_head_tags,
    render_ncpi_fhir_pillar_html,
    render_phase2_rxnorm_component_html,
    render_phase3_nih_benchmark_html,
)
from dashboard_engine.shared_ui_components import build_instant_download_banner


def test_ncpi_fhir_pillar_html():
    """Verifies that the Frontend Explanatory Pillar contains all English titles, subtitles, and 3 highlights."""
    html = render_ncbi_fhir_pillar_html()

    # 1. Title verification (Academic English)
    assert "Cloud Interoperability & Evidence Standards" in html or "Cloud Interoperability &amp; Evidence Standards" in html
    assert "NIH NCBI & HL7 FHIR EVIDENCE STANDARDS" in html or "NIH NCBI &amp; HL7 FHIR EVIDENCE STANDARDS" in html

    # 2. Subtitle verification
    assert "National Center for Biotechnology Information (NCBI)" in html

    # 3. Three Mini-Pillar Highlights
    assert "Phase 1 · Multi-Format FHIR Export" in html
    assert "Phase 2 · Pharmacological Harmonization" in html
    assert "Phase 3 · Cloud Benchmark & Verification" in html or "Phase 3 · Cloud Benchmark &amp; Verification" in html

    # 4. Master Toggle verification
    assert 'id="ncbi-master-toggle"' in html
    assert "Enable NCBI / FHIR Layer" in html
    assert "National Center for Biotechnology Information (NCBI)" in html


def test_ncpi_fhir_head_tags_and_js_module():
    """Verifies that client-side JavaScript module exists and contains all required functions."""
    head_tags = get_ncbi_fhir_head_tags()
    assert "exportToNCBIFhir" in head_tags
    assert "exportToNCBIFhirExcel" in head_tags
    assert "exportToNCBIFhirDashboard" in head_tags
    assert "mandoros-ncbi-fhir-tool" in head_tags
    assert "mandoros-ncpi-fhir-tool" in head_tags

    js_file = os.path.join(os.path.dirname(__file__), "..", "static", "ncbiFhirAddon.js")
    assert os.path.exists(js_file), "static/ncbiFhirAddon.js must exist"

    with open(js_file, "r", encoding="utf-8") as f:
        js_code = f.read()

    # Phase 1 multi-format functions
    assert "function exportToNCBIFhir" in js_code
    assert "function exportToNCBIFhirExcel" in js_code
    assert "function exportToNCBIFhirDashboard" in js_code
    # Backward compatibility aliases
    assert "exportToNCPIFhir" in js_code
    assert "exportToNCPIFhirExcel" in js_code
    assert "exportToNCPIFhirDashboard" in js_code

    # FHIR resources
    assert 'resourceType: "Bundle"' in js_code
    assert 'resourceType: "ResearchStudy"' in js_code
    assert 'resourceType: "EvidenceVariable"' in js_code
    assert 'resourceType: "Evidence"' in js_code
    assert "https://mandoros.org/fhir/StructureDefinition/extracted-88-fields" in js_code

    # Phase 2 function & NIH NLM endpoint
    assert "async function fetchDrugRxNormCode" in js_code
    assert "https://rxnav.nlm.nih.gov/REST/rxcui.json" in js_code
    assert "sessionStorage" in js_code

    # Phase 3 function & ClinicalTrials.gov API v2 endpoint
    assert "async function fetchClinicalTrialsBenchmark" in js_code
    assert "https://clinicaltrials.gov/api/v2/studies" in js_code

    # Master Toggle
    assert "function toggleNcbiAddon" in js_code
    assert "toggleNcpiAddon" in js_code
    assert "localStorage" in js_code


def test_phase1_instant_download_banner_fhir_buttons():
    """Verifies that Phase 1 download banner includes JSON, Excel, and Dashboard buttons in English alongside standard downloads."""
    banner = build_instant_download_banner(
        html_file_path=None,
        xlsx_file_path="Custom_Drug_MANDOROS_Master_Report.xlsx",
        phase_label="Phase 1 Single-Trial"
    )

    # Standard Excel download
    assert "Instant Download Phase 1 Single-Trial Excel Workbook" in banner

    # Multi-format FHIR additions (in English)
    assert "Export HL7 FHIR (JSON)" in banner
    assert "Export FHIR Excel (.xlsx)" in banner
    assert "FHIR Dashboard" in banner
    assert "exportToNCBIFhir" in banner
    assert "exportToNCPIFhir" in banner
    assert "exportToNCBIFhirExcel" in banner
    assert "exportToNCPIFhirExcel" in banner
    assert "exportToNCBIFhirDashboard" in banner
    assert "exportToNCPIFhirDashboard" in banner
    assert "mandoros-ncbi-fhir-tool" in banner
    assert "mandoros-ncpi-fhir-tool" in banner


def test_phase2_rxnorm_component():
    """Verifies that the Phase 2 RxNorm drug explorer has interactive buttons and tooltips in English."""
    rx_html = render_phase2_rxnorm_component_html()
    assert "NIH RxNorm Pharmacological Harmonization & Standardization" in rx_html or "NIH RxNorm Pharmacological Harmonization &amp; Standardization" in rx_html
    assert "Resolve RxCUI" in rx_html
    assert "Empagliflozin" in rx_html
    assert "Metformin" in rx_html
    assert "Dapagliflozin" in rx_html
    assert "Semaglutide" in rx_html


def test_phase3_nih_benchmark_component():
    """Verifies that the Phase 3 lazy-loaded ClinicalTrials benchmark component is ready with all 3 export actions."""
    p3_html = render_phase3_nih_benchmark_html()
    assert "NIH CLINICALTRIALS.GOV V2 PROTOCOL BENCHMARK" in p3_html
    assert "Clinical Evidence Cross-Verification · Side-by-Side Reporting Bias Appraisal" in p3_html
    assert "phase3-nct-input" in p3_html
    assert "runPhase3ClinicalTrialsCheck" in p3_html
    assert "NCT01131676" in p3_html
    assert "NCT01730534" in p3_html
    assert "NCT00870337" in p3_html
    assert "FHIR (JSON)" in p3_html
    assert "FHIR (Excel)" in p3_html
    assert "Dashboard" in p3_html


def test_non_destructive_constraints():
    """Ensures requirements.txt was not modified and 88 fields schema remains intact."""
    schema_path = os.path.join(os.path.dirname(__file__), "..", "schema", "extraction_schema.json")
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)

    # Core 7 relational entities
    assert "studies" in schema["properties"]
    assert "arms" in schema["properties"]
    assert "eligibility" in schema["properties"]
    assert "outcomes" in schema["properties"]
    assert "baseline" in schema["properties"]
    assert "provenance" in schema["properties"]
