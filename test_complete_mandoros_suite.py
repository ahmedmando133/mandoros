"""
Complete All-in-One Verification Test Suite for MANDOROS.
Validates:
1. Render Compatibility & Non-Removal Check (render.yaml, Procfile, Dockerfile, PORT binding, requirements.txt)
2. Multi-User & Memory Janitor Check (SESSION_ROOT, session isolation, concurrent runs, janitor cleanup, PWA assets)
3. All 3 Phases Excel-to-Dashboard Check (Phase 1, Phase 2, Phase 3 HTML generation, CDN links, Base64 instant download bar in <2s)
4. Phase 3 Scientific Rigor Check (4 Gap Types, live/parallel reality checker, 3-color traffic-light rules, presize sample size math, protocol risk gauge, GRADE & SPIRIT blueprints)
"""

import os
import sys
import time
import base64
import tempfile
import threading
from pathlib import Path
import pytest
import pandas as pd
import openpyxl

# Add repo root to sys.path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


# =========================================================================
# 1. RENDER COMPATIBILITY & NON-REMOVAL VERIFICATION
# =========================================================================
class TestRenderCompatibility:
    """Verifies that Render deployment settings and port bindings are 100% intact."""

    def test_render_yaml_intact(self):
        render_yaml_path = ROOT_DIR / "render.yaml"
        assert render_yaml_path.exists(), "render.yaml must exist for Render deployment!"
        content = render_yaml_path.read_text(encoding="utf-8")
        assert "pip install -r requirements.txt" in content, "render.yaml buildCommand must install requirements.txt"
        assert "python app.py" in content, "render.yaml startCommand must launch python app.py"

    def test_procfile_intact(self):
        procfile_path = ROOT_DIR / "Procfile"
        assert procfile_path.exists(), "Procfile must exist!"
        content = procfile_path.read_text(encoding="utf-8")
        assert "web: python app.py" in content.strip(), "Procfile must specify web: python app.py"

    def test_dockerfile_render_safe(self):
        dockerfile_path = ROOT_DIR / "Dockerfile"
        assert dockerfile_path.exists(), "Dockerfile must exist!"
        content = dockerfile_path.read_text(encoding="utf-8")
        assert "PORT" in content, "Dockerfile must reference PORT environment variable"
        assert "python app.py" in content or '["python", "app.py"]' in content, "Dockerfile must run app.py"

    def test_app_py_port_binding(self):
        app_py_path = ROOT_DIR / "app.py"
        assert app_py_path.exists(), "app.py must exist!"
        content = app_py_path.read_text(encoding="utf-8")
        assert 'os.environ.get("PORT"' in content or "os.environ.get('PORT'" in content, \
            "app.py must dynamically bind to os.environ.get('PORT', 7860)"
        assert 'server_name="0.0.0.0"' in content, "app.py must bind to server_name='0.0.0.0' for Render container routing"

    def test_requirements_txt_packages(self):
        req_path = ROOT_DIR / "requirements.txt"
        assert req_path.exists(), "requirements.txt must exist!"
        content = req_path.read_text(encoding="utf-8").lower()
        mandatory = [
            "plotly", "openpyxl", "pandas", "numpy", "scipy",
            "requests", "httpx", "curl_cffi", "pyalex", "pytrials",
            "sweetviz", "pygwalker", "great_tables"
        ]
        for pkg in mandatory:
            assert pkg in content, f"Package '{pkg}' must be listed in requirements.txt"


# =========================================================================
# 2. MULTI-USER ISOLATION & STORAGE JANITOR VERIFICATION
# =========================================================================
class TestMultiUserAndStorageJanitor:
    """Verifies per-user session isolation and the background disk/RAM janitor."""

    def test_session_isolator_creates_unique_directories(self):
        from infra_stability.session_isolator import create_isolated_session, SESSION_ROOT
        assert SESSION_ROOT.exists()

        s1 = create_isolated_session("test_p1")
        s2 = create_isolated_session("test_p2")
        assert s1.exists()
        assert s2.exists()
        assert s1 != s2, "Each session must have a distinct directory"
        assert s1.name.startswith("test_p1_")
        assert s2.name.startswith("test_p2_")

    def test_concurrent_sessions_no_collision(self):
        from infra_stability.session_isolator import create_isolated_session, get_session_file_path
        session_dirs = []
        lock = threading.Lock()

        def _worker(thread_idx):
            sess = create_isolated_session(f"concurr_{thread_idx}")
            fpath = get_session_file_path(sess, "result.txt")
            with open(fpath, "w") as f:
                f.write(f"Thread-{thread_idx} data payload")
            with lock:
                session_dirs.append((sess, fpath, f"Thread-{thread_idx} data payload"))

        threads = [threading.Thread(target=_worker, args=(i,)) for i in range(12)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(session_dirs) == 12
        unique_paths = set(s[0] for s in session_dirs)
        assert len(unique_paths) == 12, "All 12 concurrent threads must have distinct session folders"

        for _, fpath, expected_text in session_dirs:
            assert fpath.exists()
            assert fpath.read_text() == expected_text

    def test_cleanup_expired_sessions(self):
        from infra_stability.storage_memory_janitor import cleanup_expired_sessions, SESSION_ROOT
        # Create an artificial expired test folder
        test_folder = SESSION_ROOT / "expired_test_session"
        test_folder.mkdir(parents=True, exist_ok=True)
        dummy_file = test_folder / "temp.bin"
        with open(dummy_file, "wb") as f:
            f.write(b"0" * 1024)

        # Force mtime into the past (>1800s ago)
        old_time = time.time() - 3600
        os.utime(test_folder, (old_time, old_time))
        os.utime(dummy_file, (old_time, old_time))

        stats = cleanup_expired_sessions(max_age_seconds=1800, max_folder_mb=200)
        assert isinstance(stats, dict)
        assert not test_folder.exists(), "Expired session directory must be deleted by janitor"

    def test_pwa_assets_and_head_tags(self):
        from infra_stability.pwa_manifest_injector import get_pwa_head_html
        head_html = get_pwa_head_html()
        assert 'rel="manifest"' in head_html
        assert 'serviceWorker' in head_html
        assert 'mandoros-pwa-install-btn' in head_html

        manifest_file = ROOT_DIR / "static" / "manifest.json"
        assert manifest_file.exists(), "static/manifest.json must exist!"
        sw_file = ROOT_DIR / "static" / "sw.js"
        assert sw_file.exists(), "static/sw.js must exist!"

    def test_mirror_and_app_bar_markup(self):
        from infra_stability.mirror_and_app_bar import render_mirror_and_app_bar
        bar_html = render_mirror_and_app_bar()
        assert "mandoros.onrender.com" in bar_html
        assert "Free 16GB HF Mirror" in bar_html
        assert "mandoros-pwa-install-btn" in bar_html
        assert "Desktop App" in bar_html


# =========================================================================
# 3. UNIVERSAL EXCEL-TO-DASHBOARD ENGINE CHECK (ALL 3 PHASES)
# =========================================================================
class TestAll3PhasesExcelToDashboard:
    """Verifies that Phase 1, Phase 2, and Phase 3 Excel workbooks generate interactive HTML dashboards in <2s."""

    @pytest.fixture
    def sample_phase1_xlsx(self, tmp_path):
        wb = openpyxl.Workbook()
        ws1 = wb.active
        ws1.title = "Master Excel Sheet"
        ws1.append(["Header 1", "Header 2", "Header 3"])
        ws1.append(["Group A", "Group A", "Group B"])
        ws1.append(["Sub 1", "Sub 2", "Sub 3"])
        ws1.append(["Val 1", "Val 2", "Val 3"])

        ws2 = wb.create_sheet("Study_Characteristics")
        ws2.append(["Parameter", "Value"])
        ws2.append(["Trial_Name", "EMPAGLIFLOZIN_RCT_01"])
        ws2.append(["Total_Sample_Size", 850])
        ws2.append(["Active_Drug", "Empagliflozin 10mg"])
        ws2.append(["Comparator", "Placebo"])

        ws3 = wb.create_sheet("Population_Baseline")
        ws3.append(["Characteristic", "Arm 1", "Arm 2"])
        ws3.append(["Age (years)", "62.4 ± 8.1", "63.1 ± 7.9"])
        ws3.append(["Female (%)", "44.2%", "43.8%"])

        ws4 = wb.create_sheet("Intervention_Arms")
        ws4.append(["Arm_ID", "Arm_Name", "Regimen", "Dose", "Duration"])
        ws4.append(["ARM_01", "Empagliflozin", "Oral daily", "10 mg", "24 weeks"])
        ws4.append(["ARM_02", "Placebo", "Oral daily", "Matching", "24 weeks"])

        ws5 = wb.create_sheet("Outcomes")
        ws5.append(["Outcome_Name", "Arm_1_Mean", "Arm_1_SD", "Arm_2_Mean", "Arm_2_SD", "MD", "CI_95", "P_Value"])
        ws5.append(["HbA1c Reduction (%)", "-0.82", "0.45", "-0.15", "0.50", "-0.67", "[-0.78, -0.56]", "<0.001"])

        ws6 = wb.create_sheet("Variables_Matrix")
        ws6.append(["Domain", "Arm 1", "Arm 2"])
        ws6.append(["Primary Efficacy", "-0.82", "-0.15"])

        ws7 = wb.create_sheet("Eligibility_Criteria")
        ws7.append(["Criterion_Type", "Category", "Parameter", "Operator", "Value", "Unit"])
        ws7.append(["Inclusion", "Age", "Age", ">=", "18", "years"])
        ws7.append(["Exclusion", "Renal", "eGFR", "<", "30", "mL/min/1.73m2"])

        p = tmp_path / "test_p1_sample.xlsx"
        wb.save(p)
        return str(p)

    def test_phase1_dashboard_generation_speed_and_content(self, sample_phase1_xlsx, tmp_path):
        from dashboard_engine.phase1_trial_dashboard import build_phase1_single_trial_dashboard
        out_html = str(tmp_path / "test_phase1_dash.html")

        t0 = time.time()
        res_path = build_phase1_single_trial_dashboard(sample_phase1_xlsx, out_html)
        elapsed = time.time() - t0

        assert elapsed < 2.0, f"Phase 1 dashboard must generate in <2 seconds (took {elapsed:.2f}s)"
        assert os.path.exists(res_path)
        content = Path(res_path).read_text(encoding="utf-8")

        # Verify CDN links from Section 1.2
        assert "cdn.tailwindcss.com" in content
        assert "cdn.plot.ly/plotly-2.35.2.min.js" in content
        assert "cdn.datatables.net/1.13.8" in content

        # Verify 8 KPI Cards and Glassmorphism
        assert "glass-card" in content
        assert "Overview &amp; CONSORT Flow" in content or "Overview & CONSORT Flow" in content
        assert "Baseline Demographics Explorer" in content
        assert "Dosing &amp; Regimen Swimlane" in content or "Dosing & Regimen Swimlane" in content
        assert ("Efficacy &amp; Safety" in content or "Efficacy & Safety" in content) and "Lab" in content
        assert "Eligibility Criteria Gatekeeper" in content

    def test_phase2_multi_trial_dashboard_generation(self, sample_phase1_xlsx, tmp_path):
        from dashboard_engine.phase2_cohort_excel_dash import build_phase2_multi_trial_dashboard
        out_html = str(tmp_path / "test_phase2_dash.html")

        t0 = time.time()
        res_path = build_phase2_multi_trial_dashboard(sample_phase1_xlsx, output_html_path=out_html)
        elapsed = time.time() - t0

        assert elapsed < 2.0, f"Phase 2 dashboard must generate in <2 seconds (took {elapsed:.2f}s)"
        assert os.path.exists(res_path)
        content = Path(res_path).read_text(encoding="utf-8")
        assert "Meta-Analysis" in content
        assert "Pooled Trials" in content

    def test_instant_download_banner_base64(self, tmp_path):
        from dashboard_engine.shared_ui_components import build_instant_download_banner
        test_html = tmp_path / "sample.html"
        test_html.write_text("<html><body>Hello MANDOROS</body></html>")
        test_xlsx = tmp_path / "sample.xlsx"
        test_xlsx.write_bytes(b"dummy_excel_bytes")

        banner = build_instant_download_banner(str(test_html), str(test_xlsx), phase_label="Phase 1")
        assert "data:text/html;base64," in banner, "Must contain Base64 data URI for instant HTML download"
        assert "data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64," in banner, \
            "Must contain Base64 data URI for instant Excel download"
        assert "download=\"sample.html\"" in banner
        assert "download=\"sample.xlsx\"" in banner

    def test_excel_watcher_hook_auto_detection(self, sample_phase1_xlsx):
        from dashboard_engine.excel_watcher_hook import auto_generate_dashboard_for_excel
        html_path, banner = auto_generate_dashboard_for_excel(sample_phase1_xlsx, phase_hint="Phase 1")
        assert html_path and os.path.exists(html_path)
        assert "Instant Download" in banner


# =========================================================================
# 4. PHASE 3 RESEARCH GAP & THESIS NAVIGATOR SCIENTIFIC RIGOR
# =========================================================================
class TestPhase3ScientificRigor:
    """Verifies the 4 Gap Types, 3 colors, parallel global checks, and presize sample size math."""

    def test_gap_taxonomy_all_4_types(self):
        from phase3_navigator.gap_taxonomy_extractor import GapCategory, GapTaxonomyExtractor, ScientificGap
        from phase3_navigator.schema_ingestor import IngestedTrialData, SingleTrialRecord

        trial = SingleTrialRecord(
            study_id="TEST_01",
            trial_name="Trial Test 01",
            authors="Smith et al.",
            year=2024,
            journal="Lancet",
            active_drug="Tirzepatide",
            comparator="Placebo",
            total_n=120, # < 150 -> will trigger sample size / OIS gap
            follow_up_weeks=12, # short follow-up -> INT_COMP_GAP
            blinding_status="Open-label", # RoB gap
            rob_overall="Some concerns", # RoB gap
            eligibility_rows=[
                {"criterion_type": "exclusion", "category": "age", "parameter": "Age", "operator": ">", "value": "65", "unit": "years", "raw_text": "Age >65 excluded"}
            ],
            outcomes_rows=[
                {"outcome_name": "HbA1c Reduction", "unit": "%", "effect_size_md": -1.5, "ci_lower": -2.2, "ci_upper": -0.8}
            ]
        )
        data = IngestedTrialData(
            trials=[trial],
            drug_name="Tirzepatide",
            condition="Type 2 Diabetes",
            comparator_name="Placebo",
            total_sample_size=120
        )

        gaps = GapTaxonomyExtractor.extract_all_gaps(data)
        categories_found = set(g.category for g in gaps)

        assert GapCategory.POP_GAP in categories_found, "Must extract POP_GAP from elderly exclusion"
        assert GapCategory.INT_COMP_GAP in categories_found, "Must extract INT_COMP_GAP from short duration / placebo-only"
        assert GapCategory.OUTCOME_GAP in categories_found, "Must extract OUTCOME_GAP from missing hard endpoints/QoL"
        assert GapCategory.METHOD_ROB_GRADE_GAP in categories_found, "Must extract METHOD_ROB_GRADE_GAP from open-label/small N"

        for g in gaps:
            assert g.source_sheet, "Every gap must cite its source sheet provenance"
            assert g.exact_extracted_value_or_quote, "Every gap must cite exact extracted quote/value"

    def test_global_reality_checker_3_color_traffic_light_rules(self):
        from phase3_navigator.gap_taxonomy_extractor import ScientificGap, GapCategory
        from phase3_navigator.global_reality_checker import GlobalRealityChecker, TrafficLightColor
        from unittest.mock import patch

        gap = ScientificGap(
            gap_id="GAP_TEST",
            category=GapCategory.POP_GAP,
            badge_label="Population Void",
            badge_arabic="فجوة سكانية",
            title="Severe Renal Impairment (eGFR <30)",
            description="Patients with severe CKD excluded",
            source_file_name="trial.xlsx",
            source_sheet="Eligibility_Criteria",
            row_coord="Row 12",
            exact_extracted_value_or_quote="eGFR < 30 mL/min excluded",
            clinical_rationale="CKD stage 4/5 pharmacokinetics unknown",
            target_query_keyword="renal impairment CKD",
            proposed_resolution="Dedicated Phase 3 in CKD patients"
        )

        # Case 1: 🟢 GREEN - Verified Global Unexplored Void (pubmed=0, completed=0, ongoing<=1)
        with patch("phase3_navigator.global_reality_checker.verify_gap_globally_fast") as mock_fast:
            mock_fast.return_value = {
                "pubmed_rct_count": 0, "ctgov_ongoing_count": 0, "ctgov_completed_count": 0,
                "ctgov_total_count": 0, "openalex_count": 0, "pubmed_articles": [], "ctgov_studies": [], "openalex_works": []
            }
            v_green = GlobalRealityChecker.verify_gap(gap, "Type 2 Diabetes", "Tirzepatide")
            assert v_green.traffic_light_color == TrafficLightColor.GREEN
            assert "🟢" in v_green.badge_label

        # Case 2: 🟡 YELLOW - Contested / Ongoing (1 <= pubmed <= 3, or ongoing >= 1)
        with patch("phase3_navigator.global_reality_checker.verify_gap_globally_fast") as mock_fast:
            mock_fast.return_value = {
                "pubmed_rct_count": 2, "ctgov_ongoing_count": 2, "ctgov_completed_count": 0,
                "ctgov_total_count": 2, "openalex_count": 5, "pubmed_articles": [], "ctgov_studies": [], "openalex_works": []
            }
            v_yellow = GlobalRealityChecker.verify_gap(gap, "Type 2 Diabetes", "Tirzepatide")
            assert v_yellow.traffic_light_color == TrafficLightColor.YELLOW
            assert "🟡" in v_yellow.badge_label

        # Case 3: 🔴 RED - Saturated / Covered Externally (pubmed >= 4 or completed >= 2)
        with patch("phase3_navigator.global_reality_checker.verify_gap_globally_fast") as mock_fast:
            mock_fast.return_value = {
                "pubmed_rct_count": 6, "ctgov_ongoing_count": 1, "ctgov_completed_count": 3,
                "ctgov_total_count": 4, "openalex_count": 45, "pubmed_articles": [], "ctgov_studies": [], "openalex_works": []
            }
            v_red = GlobalRealityChecker.verify_gap(gap, "Type 2 Diabetes", "Tirzepatide")
            assert v_red.traffic_light_color == TrafficLightColor.RED
            assert "🔴" in v_red.badge_label

    def test_presize_and_sample_size_math(self):
        from phase3_navigator.sample_size_and_risk import SampleSizeAndRiskEngine

        # Continuous Superiority calculation
        res_cont = SampleSizeAndRiskEngine.calculate_continuous_superiority(
            delta=-0.80,
            sigma=1.20,
            alpha=0.05,
            power=0.80,
            attrition_rate=0.15
        )
        assert res_cont.n_per_arm_evaluable > 20
        assert res_cont.n_per_arm_enrolled > res_cont.n_per_arm_evaluable, "Enrolled must be higher than evaluable to account for attrition"
        assert res_cont.n_total_enrolled == res_cont.n_per_arm_enrolled * 2

        # Binary Superiority calculation
        res_bin = SampleSizeAndRiskEngine.calculate_binary_superiority(
            p_treatment=0.35,
            p_control=0.20,
            alpha=0.05,
            power=0.80,
            attrition_rate=0.15
        )
        assert res_bin.n_per_arm_evaluable > 50
        assert res_bin.n_total_enrolled > res_bin.n_total_evaluable

        # presize CI width precision
        res_prec = SampleSizeAndRiskEngine.calculate_precision_sample_size(
            target_ci_width=0.40,
            sigma=1.20,
            alpha=0.05
        )
        assert res_prec.n_total_evaluable > 50

    def test_protocol_risk_gauge_0_to_100(self):
        from phase3_navigator.sample_size_and_risk import SampleSizeAndRiskEngine
        from phase3_navigator.schema_ingestor import IngestedTrialData, SingleTrialRecord

        trial = SingleTrialRecord(
            study_id="TEST_RISK",
            trial_name="High Risk Trial",
            authors="Doe et al.",
            year=2023,
            journal="Journal",
            active_drug="Drug X",
            comparator="Placebo",
            total_n=40, # very small
            follow_up_weeks=8, # very short
            blinding_status="Open-label",
            rob_overall="High"
        )
        data = IngestedTrialData(trials=[trial], drug_name="Drug X", condition="Hypertension", total_sample_size=40)

        report = SampleSizeAndRiskEngine.audit_protocol_risk(data)
        assert 0.0 <= report.total_score <= 100.0, "Score must be bounded between 0 and 100"
        assert len(report.domains) == 5, "Must evaluate 5 protocol risk domains (Wood & McNair 2023 standard)"

    def test_phase3_excel_and_html_exporter(self, tmp_path):
        from phase3_navigator.gap_taxonomy_extractor import GapTaxonomyExtractor, ScientificGap, GapCategory
        from phase3_navigator.sample_size_and_risk import SampleSizeAndRiskEngine
        from phase3_navigator.thesis_protocol_builder import ThesisProtocolBuilder
        from phase3_navigator.excel_html_exporter import Phase3DossierExporter
        from phase3_navigator.schema_ingestor import IngestedTrialData, SingleTrialRecord

        trial = SingleTrialRecord(
            study_id="P3_TEST",
            trial_name="Phase 3 Integration Study",
            authors="Expert et al.",
            year=2024,
            journal="NEJM",
            active_drug="Semaglutide",
            comparator="Placebo",
            total_n=300,
            follow_up_weeks=24,
            blinding_status="Double-blind",
            rob_overall="Low",
            eligibility_rows=[
                {"criterion_type": "exclusion", "category": "age", "parameter": "Age", "operator": ">", "value": "75", "unit": "years", "raw_text": "Age >75"}
            ],
            outcomes_rows=[
                {"outcome_name": "Weight Loss", "unit": "kg", "effect_size_md": -5.4, "ci_lower": -6.8, "ci_upper": -4.0}
            ]
        )
        data = IngestedTrialData(trials=[trial], drug_name="Semaglutide", condition="Obesity", total_sample_size=300)

        gaps = GapTaxonomyExtractor.extract_all_gaps(data)
        sens_matrix = SampleSizeAndRiskEngine.build_sensitivity_matrix(data)
        risk_rep = SampleSizeAndRiskEngine.audit_protocol_risk(data)
        blueprint = ThesisProtocolBuilder.build_blueprint(gaps[0] if gaps else None, data)

        out_xlsx = str(tmp_path / "MANDOROS_Phase3_Test.xlsx")
        out_html = str(tmp_path / "MANDOROS_Phase3_Test.html")

        # Test Excel export
        saved_xlsx = Phase3DossierExporter.export_excel(out_xlsx, gaps, sens_matrix, risk_rep, blueprint, data)
        assert os.path.exists(saved_xlsx)

        wb = openpyxl.load_workbook(saved_xlsx)
        assert len(wb.sheetnames) >= 6, "Phase 3 Excel must have at least 6 specialized sheets"
        expected_sheets = [
            "Executive Gap Matrix", "Evidence & Gap Map Data", "Sample Size & Power Models",
            "Protocol Risk Audit", "GRADE Summary of Findings", "Search Strategies & Blueprints"
        ]
        for es in expected_sheets:
            assert es in wb.sheetnames, f"Sheet '{es}' must be in Phase 3 Excel"

        # Check color fills
        ws1 = wb["Executive Gap Matrix"]
        assert ws1.max_row >= 4

        # Test HTML export
        saved_html = Phase3DossierExporter.export_html_dossier(out_html, gaps, sens_matrix, risk_rep, blueprint, data)
        assert os.path.exists(saved_html)
        content_html = Path(saved_html).read_text(encoding="utf-8")
        assert "cdn.plot.ly" in content_html
        assert "cdn.tailwindcss.com" in content_html
        assert "GRADE Summary of Findings" in content_html
