---
name: mandoros-app
description: Autonomous orchestrator for MANDOROS (Meta-Analysis Network for Data, Outcomes & Research Optimization Synthesis). Executes Phase 1 deep trial extraction, Phase 2 meta-analysis & virtual trials, Phase 3 Research Gap & Thesis navigation, automated Excel-to-HTML interactive dashboards, and cloud/desktop infrastructure management.
license: Apache-2.0
compatibility: Python 3.10+, Gradio 4+, Windows, Linux, macOS
metadata:
  version: "3.0"
  system: "MANDOROS"
---

# MANDOROS Autonomous Orchestrator Skill

## Overview
This skill equips Antigravity with end-to-end execution capabilities for the MANDOROS biostatistical and clinical trial synthesis platform:
1. **Phase 1: Clinical Trial Deep Extractor**: 88 atomic fields extracted across 7 standardized Excel sheets (`Master Excel Sheet`, `Studies`, `Arms`, `Baseline`, `Regimens`, `Outcomes`, `Eligibility`).
2. **Phase 2: Multi-Trial Meta-Analysis & In-Silico Synthesis**: `metafor`-grade REML/DL pooling, Bucher NMA, SUCRA rankings, and Virtual Trial extrapolation.
3. **Phase 3: Research Gap & Thesis Navigator**: 4 Gap Types (`POP_GAP`, `INT_COMP_GAP`, `OUTCOME_GAP`, `METHOD_ROB_GRADE_GAP`), 3-Color Traffic Light system (🟢/🟡/🔴), parallel API verification (<3s via PubMed, ClinicalTrials.gov v2, OpenAlex), presize sample size math, protocol informativeness risk gauge, and FINER/GRADE/SPIRIT/PROSPERO blueprints.
4. **Universal Excel-to-Interactive-Dashboard Engine**: Instant `<2s` translation of any `.xlsx` into a self-contained, high-speed `.html` dashboard with 1-click Base64 instant downloads.
5. **Infrastructure & Stability Hardening**: Multi-user session isolation, 200MB background memory/disk janitor, PWA 1-click installation, and zero-server local Desktop runner.

## Available Modules & Scripts

### 1. Launching MANDOROS Locally or Desktop App
- Launch Desktop App:
  ```powershell
  python run_desktop_app.py
  ```
- Launch Standard Web Server (Render & HF Space compatible):
  ```powershell
  python app.py
  ```

### 2. Automatic Excel-to-Dashboard Engine
To convert any clinical trial workbook (.xlsx) into an interactive dashboard:
```python
from dashboard_engine.excel_watcher_hook import auto_generate_dashboard_for_excel

html_path, download_banner = auto_generate_dashboard_for_excel(
    xlsx_path="outputs/trial_extracted.xlsx",
    phase_hint="Phase 1"  # "Phase 1", "Phase 2", or "Phase 3"
)
```

### 3. Running Phase 3 Research Gap & Thesis Navigator
```python
from phase3_navigator.schema_ingestor import UnifiedSchemaIngestor
from phase3_navigator.gap_taxonomy_extractor import GapTaxonomyExtractor
from phase3_navigator.global_reality_checker import GlobalRealityChecker
from phase3_navigator.sample_size_and_risk import SampleSizeAndRiskEngine
from phase3_navigator.thesis_protocol_builder import ThesisProtocolBuilder
from phase3_navigator.excel_html_exporter import Phase3DossierExporter

# 1. Ingest trial data from Excel or PDF
trial_data = UnifiedSchemaIngestor.ingest_source("outputs/trial_extracted.xlsx")

# 2. Extract scientific gaps with provenance
gaps = GapTaxonomyExtractor.extract_all_gaps(trial_data)

# 3. Fast parallel reality check (<3s)
verdicts = GlobalRealityChecker.verify_all_gaps_parallel(
    gaps,
    condition=trial_data.condition,
    drug_name=trial_data.drug_name
)

# 4. Sample size calculations & protocol risk
sensitivity_matrix = SampleSizeAndRiskEngine.build_sensitivity_matrix(trial_data)
risk_report = SampleSizeAndRiskEngine.audit_protocol_risk(trial_data)

# 5. Build Thesis Blueprint (FINER, GRADE, SPIRIT, PROSPERO)
blueprint = ThesisProtocolBuilder.build_blueprint(gaps[0] if gaps else None, trial_data)

# 6. Export 6-sheet Excel and standalone HTML dashboard
Phase3DossierExporter.export_excel("outputs/MANDOROS_Phase3_Gap_Matrix.xlsx", gaps, sensitivity_matrix, risk_report, blueprint, trial_data)
Phase3DossierExporter.export_html_dossier("outputs/MANDOROS_Phase3_Thesis_Dashboard.html", gaps, sensitivity_matrix, risk_report, blueprint, trial_data)
```

### 4. Background Storage & Memory Janitor
```python
from infra_stability import cleanup_expired_sessions, start_background_janitor

# Start background janitor thread (auto cleans temp files >30min or total >200MB)
start_background_janitor(interval_seconds=300)

# Or trigger manual cleanup on demand
stats = cleanup_expired_sessions(max_age_seconds=1800, max_folder_mb=200)
```
