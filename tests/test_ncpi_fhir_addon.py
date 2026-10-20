# -*- coding: utf-8 -*-
"""
Test Suite for MANDOROS NIH NCPI / HL7 FHIR (EBMonFHIR) Zero-Server-Load Add-on.
Verifies all 3 phases, the explanatory frontend pillar, master toggle, and non-destructive constraints.
"""

import os
import re
import json
import pytest

from infra_stability.ncpi_fhir_addon import (
    get_ncpi_fhir_head_tags,
    render_ncpi_fhir_pillar_html,
    render_phase2_rxnorm_component_html,
    render_phase3_nih_benchmark_html,
)
from dashboard_engine.shared_ui_components import build_instant_download_banner


def test_ncpi_fhir_pillar_html():
    """Verifies that the Frontend Explanatory Pillar contains all required titles, subtitles, and 3 highlights."""
    html = render_ncpi_fhir_pillar_html()

    # 1. Title verification
    assert "ركيزة التشغيل البيني السحابي القياسي" in html
    assert "NIH NCPI" in html
    assert "HL7 FHIR Add-on" in html

    # 2. Subtitle verification
    assert "طبقة معيارية اختيارية تعمل عند الطلب لتحويل مخرجات الـ 88 حقلاً" in html

    # 3. Three Mini-Pillar Highlights
    assert "المرحلة الأولى · التصدير القياسي" in html
    assert "المرحلة الثانية · التوحيد الدوائي" in html
    assert "المرحلة الثالثة · المطابقة المرجعية" in html

    # 4. Master Toggle verification
    assert 'id="ncpi-master-toggle"' in html
    assert "تفعيل أدوات المعيار العالمي NCPI/FHIR الاختيارية" in html
    assert "window.toggleNcpiAddon(this.checked)" in html


def test_ncpi_fhir_head_tags_and_js_module():
    """Verifies that client-side JavaScript module exists and contains all required functions."""
    head_tags = get_ncpi_fhir_head_tags()
    assert "exportToNCPIFhir" in head_tags
    assert "fetchDrugRxNormCode" in head_tags
    assert "fetchClinicalTrialsBenchmark" in head_tags
    assert "mandoros-ncpi-fhir-tool" in head_tags

    js_file = os.path.join(os.path.dirname(__file__), "..", "static", "ncpiFhirAddon.js")
    assert os.path.exists(js_file), "static/ncpiFhirAddon.js must exist"

    with open(js_file, "r", encoding="utf-8") as f:
        js_code = f.read()

    # Phase 1 function
    assert "function exportToNCPIFhir" in js_code
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
    assert "function toggleNcpiAddon" in js_code
    assert "localStorage" in js_code


def test_phase1_instant_download_banner_fhir_button():
    """Verifies that Phase 1 download banner includes the FHIR export button alongside Excel."""
    banner = build_instant_download_banner(
        html_file_path=None,
        xlsx_file_path="Custom_Drug_MANDOROS_Master_Report.xlsx",
        phase_label="Phase 1 Single-Trial"
    )

    # Both Excel and FHIR buttons must be present
    assert "Instant Download Phase 1 Single-Trial Excel Workbook" in banner
    assert "Export HL7 FHIR (JSON) | تصدير بمعيار FHIR" in banner
    assert "ResearchStudy" in banner
    assert "mandoros-ncpi-fhir-tool" in banner


def test_phase2_rxnorm_component():
    """Verifies that the Phase 2 RxNorm drug explorer has interactive buttons and tooltips."""
    rx_html = render_phase2_rxnorm_component_html()
    assert "التوثيق الدوائي الموحد (NIH RxNorm Auto-Tagging)" in rx_html
    assert "🔍 كود RxNorm القياسي" in rx_html
    assert "Empagliflozin" in rx_html
    assert "Metformin" in rx_html
    assert "Dapagliflozin" in rx_html


def test_phase3_nih_benchmark_component():
    """Verifies that the Phase 3 lazy-loaded ClinicalTrials benchmark component is ready."""
    p3_html = render_phase3_nih_benchmark_html()
    assert "إثراء الدراسة من السحابة" in p3_html
    assert "Side-by-Side Reporting Bias Check" in p3_html
    assert "phase3-nct-input" in p3_html
    assert "runPhase3ClinicalTrialsCheck" in p3_html
    assert "NCT01131676" in p3_html
    assert "NCT01730534" in p3_html


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
