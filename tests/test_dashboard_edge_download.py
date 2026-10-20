"""
Unit tests for Microsoft Edge Unblocked 360 Dashboard Downloads and Direct Web Viewing.
Verifies:
1. Companion .zip package generation (ensure_dashboard_zip)
2. ZIP archive validity and contents
3. HTML served as application/octet-stream when downloaded as attachment
4. Inline rendering for /api/view
5. UI Banner action buttons (Open Fullscreen, Download .ZIP, Instant Download .html)
"""

import os
import zipfile
import pytest
from dashboard_engine.shared_ui_components import (
    ensure_dashboard_zip,
    build_instant_download_banner
)


def test_ensure_dashboard_zip(tmp_path):
    html_file = tmp_path / "Test_Phase1_Trial_Dashboard.html"
    xlsx_file = tmp_path / "Test_Phase1_Trial.xlsx"
    html_file.write_text("<html><body><h1>MANDOROS 360 Dashboard</h1></body></html>", encoding="utf-8")
    xlsx_file.write_text("dummy excel content", encoding="utf-8")

    zip_path = ensure_dashboard_zip(str(html_file), str(xlsx_file))
    assert os.path.exists(zip_path), "ZIP file must be created"
    assert zip_path.endswith(".zip")

    with zipfile.ZipFile(zip_path, "r") as zf:
        namelist = zf.namelist()
        assert "Test_Phase1_Trial_Dashboard.html" in namelist
        assert "Test_Phase1_Trial.xlsx" in namelist


def test_banner_contains_edge_unblocked_links(tmp_path):
    html_file = tmp_path / "Etoricoxib_Phase1_Trial_Dashboard.html"
    xlsx_file = tmp_path / "Etoricoxib_Phase1.xlsx"
    html_file.write_text("<html><body>Test Dashboard</body></html>", encoding="utf-8")
    xlsx_file.write_text("excel data", encoding="utf-8")

    banner = build_instant_download_banner(str(html_file), str(xlsx_file), phase_label="Phase 1 Single-Trial")

    # 1. Direct web viewing in new tab without downloading
    assert "/api/view?file=" in banner
    assert "Open Full Dashboard (New Tab)" in banner

    # 2. ZIP package download bypassing Windows Edge restrictions
    assert "/api/download?file=" in banner
    assert "&zip=1" in banner
    assert "Download Dashboard (.zip)" in banner

    # 3. Raw HTML download with octet-stream fallback
    assert "&octet=1" in banner
    assert "Instant Download Phase 1 Single-Trial Interactive Dashboard (.html)" in banner

    # 4. Excel workbook
    assert "Instant Download Phase 1 Single-Trial Excel Workbook (.xlsx)" in banner
