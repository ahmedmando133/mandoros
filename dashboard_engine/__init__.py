"""
MANDOROS Universal Automatic Excel-to-Dashboard Engine.
Intercepts any .xlsx across Phase 1, Phase 2, and Phase 3,
generating rich, interactive, standalone HTML dashboards with instant 1-click Base64 download links.
"""

from dashboard_engine.shared_ui_components import (
    FAST_CDN_HEADER,
    build_instant_download_banner,
    render_kpi_card_html,
    render_datatable_component,
)
from dashboard_engine.phase1_trial_dashboard import build_phase1_single_trial_dashboard
from dashboard_engine.phase2_cohort_excel_dash import (
    build_phase2_multi_trial_dashboard,
    bundle_cohort_individual_dashboards,
)
from dashboard_engine.phase3_gap_thesis_dash import build_phase3_gap_thesis_dashboard
from dashboard_engine.excel_watcher_hook import (
    detect_excel_phase,
    auto_generate_dashboard_for_excel,
)

__all__ = [
    "FAST_CDN_HEADER",
    "build_instant_download_banner",
    "render_kpi_card_html",
    "render_datatable_component",
    "build_phase1_single_trial_dashboard",
    "build_phase2_multi_trial_dashboard",
    "bundle_cohort_individual_dashboards",
    "build_phase3_gap_thesis_dashboard",
    "detect_excel_phase",
    "auto_generate_dashboard_for_excel",
]
