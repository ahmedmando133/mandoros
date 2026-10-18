"""
MANDOROS Excel Watcher Hook.
Automatically intercepts ANY .xlsx file created or uploaded across Phase 1, Phase 2, or Phase 3,
identifies its structural archetype, generates an interactive standalone .html dashboard in <2 seconds,
and returns the file path and instant Base64 1-click download bar.
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Optional, Tuple
import openpyxl

from dashboard_engine.shared_ui_components import build_instant_download_banner
from dashboard_engine.phase1_trial_dashboard import build_phase1_single_trial_dashboard
from dashboard_engine.phase2_cohort_excel_dash import build_phase2_multi_trial_dashboard
from dashboard_engine.phase3_gap_thesis_dash import build_phase3_gap_thesis_dashboard


DASHBOARD_CACHE: dict[str, Tuple[str, str]] = {}


def detect_excel_phase(xlsx_path: str) -> str:
    """
    Inspects sheet names in the Excel workbook to detect whether it is Phase 1, 2, or 3.
    """
    if not os.path.exists(xlsx_path):
        return "Phase 1"

    try:
        wb = openpyxl.load_workbook(xlsx_path, read_only=True)
        sheets = [s.lower() for s in wb.sheetnames]
        wb.close()

        # Check Phase 3 indicators
        if any("gap" in s for s in sheets) or any("thesis" in s for s in sheets) or any("evidence & gap" in s for s in sheets):
            return "Phase 3"

        # Check Phase 2 indicators
        if any("meta" in s for s in sheets) or any("cohort" in s for s in sheets) or any("comparison" in s for s in sheets) or any("sucra" in s for s in sheets):
            return "Phase 2"

        # Check Phase 1 indicators
        if any("characteristics" in s for s in sheets) or any("eligibility" in s for s in sheets) or any("variables" in s for s in sheets) or any("outcomes" in s for s in sheets):
            return "Phase 1"

        return "Phase 1"
    except Exception:
        return "Phase 1"


def auto_generate_dashboard_for_excel(
    xlsx_path: str,
    phase_hint: Optional[str] = None,
    force_refresh: bool = False
) -> Tuple[str, str]:
    """
    Intercepts an Excel workbook, builds its corresponding HTML dashboard,
    and returns (html_path, instant_download_banner_html).
    """
    if not os.path.exists(xlsx_path):
        empty_banner = build_instant_download_banner(None, None, phase_label=phase_hint or "Phase")
        return "", empty_banner

    # Check cache
    cache_key = f"{xlsx_path}_{os.path.getmtime(xlsx_path)}"
    if not force_refresh and cache_key in DASHBOARD_CACHE:
        return DASHBOARD_CACHE[cache_key]

    phase = phase_hint or detect_excel_phase(xlsx_path)

    out_dir = "outputs"
    os.makedirs(out_dir, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(xlsx_path))[0]

    try:
        if "3" in str(phase):
            html_path = os.path.join(out_dir, f"{base_name}_Phase3_Thesis_Dashboard.html")
            build_phase3_gap_thesis_dashboard(xlsx_path, html_path)
            banner = build_instant_download_banner(html_path, xlsx_path, phase_label="Phase 3 Gap & Thesis")
        elif "2" in str(phase):
            html_path = os.path.join(out_dir, f"{base_name}_Phase2_Executive_Dashboard.html")
            build_phase2_multi_trial_dashboard(xlsx_path, output_html_path=html_path)
            banner = build_instant_download_banner(html_path, xlsx_path, phase_label="Phase 2 Multi-Trial")
        else:
            html_path = os.path.join(out_dir, f"{base_name}_Phase1_Trial_Dashboard.html")
            build_phase1_single_trial_dashboard(xlsx_path, html_path)
            banner = build_instant_download_banner(html_path, xlsx_path, phase_label="Phase 1 Single-Trial")

        DASHBOARD_CACHE[cache_key] = (html_path, banner)
        return html_path, banner
    except Exception as e:
        # Fallback to single trial builder
        html_path = os.path.join(out_dir, f"{base_name}_Trial_Dashboard.html")
        try:
            build_phase1_single_trial_dashboard(xlsx_path, html_path)
            banner = build_instant_download_banner(html_path, xlsx_path, phase_label="Trial")
            DASHBOARD_CACHE[cache_key] = (html_path, banner)
            return html_path, banner
        except Exception:
            empty_banner = build_instant_download_banner(None, xlsx_path, phase_label=phase)
            return "", empty_banner
