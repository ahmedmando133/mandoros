"""
Tests for GSAP (GreenSock Animation Platform) Integration in MANDOROS.
Verifies CDN links injection, static/mandoros_gsap.js controller, and zero server footprint.
"""

import os
import sys
from pathlib import Path
import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


class TestGsapIntegration:
    """Verifies complete GSAP CDN integration and client-side animation controller."""

    def test_requirements_no_heavy_packages(self):
        """Verifies requirements.txt does not contain local GSAP or heavy animation packages."""
        req_path = ROOT_DIR / "requirements.txt"
        assert req_path.exists()
        content = req_path.read_text(encoding="utf-8").lower()
        assert "gsap" not in content
        assert "greensock" not in content

    def test_no_node_modules(self):
        """Verifies no heavy node_modules directory was created."""
        nm_path = ROOT_DIR / "node_modules"
        assert not nm_path.exists(), "node_modules should not exist; GSAP must be purely CDN-driven!"

    def test_gsap_controller_file_exists(self):
        """Verifies static/mandoros_gsap.js exists and implements all key features."""
        js_path = ROOT_DIR / "static" / "mandoros_gsap.js"
        assert js_path.exists()
        content = js_path.read_text(encoding="utf-8")

        # Plugin registration
        assert "ScrollTrigger" in content
        assert "TextPlugin" in content

        # Top Bar & Banner
        assert ".mandoros-top-mirror-bar" in content
        assert "mandoros-prod-dot" in content or "mandoros-prod-badge" in content
        assert "mandoros-hf-badge" in content
        assert "mandoros-ncpi-fhir-tool" in content

        # Hero Header & Metallic M Logo
        assert "emblem-wrapper" in content
        assert "mandoros-hero-title" in content
        assert "sine.inOut" in content

        # 8-Node Pipeline Strip
        assert "mandoros-pipeline-strip" in content
        assert "back.out(1.7)" in content
        assert "pipeline-chevron" in content

        # Bento 4-Pillar Matrix Cards & 3D Tilt
        assert "product-phase-card" in content
        assert "academic-pillar-card" in content
        assert "rotationX" in content
        assert "rotationY" in content

        # Workspace Tab Transitions & Counters
        assert "main-phases-tabs" in content
        assert "selectMandorosPhase" in content
        assert "mandoros-kpi-val" in content

        # PRISMA 2020 SVG Flow
        assert "prisma-flow-path" in content
        assert "prisma-stage-card" in content

        # Safeguards
        assert "prefers-reduced-motion" in content
        assert "MutationObserver" in content

    def test_gsap_head_injector(self):
        """Verifies infra_stability/gsap_injector.py outputs official CDN links."""
        from infra_stability.gsap_injector import GSAP_CDN_SCRIPTS, get_gsap_head_tags

        assert "https://cdn.jsdelivr.net/npm/gsap@3.12.5/dist/gsap.min.js" in GSAP_CDN_SCRIPTS
        assert "https://cdn.jsdelivr.net/npm/gsap@3.12.5/dist/ScrollTrigger.min.js" in GSAP_CDN_SCRIPTS
        assert "https://cdn.jsdelivr.net/npm/gsap@3.12.5/dist/TextPlugin.min.js" in GSAP_CDN_SCRIPTS

        head_tags = get_gsap_head_tags()
        assert "cdn.jsdelivr.net/npm/gsap@3.12.5" in head_tags
        assert "mandoros_gsap.js" in head_tags

    def test_app_py_head_and_routes(self):
        """Verifies app.py injects GSAP head tags and serves mandoros_gsap.js route."""
        app_content = (ROOT_DIR / "app.py").read_text(encoding="utf-8")

        assert "get_gsap_head_tags" in app_content
        assert "/mandoros_gsap.js" in app_content
        assert "/static/mandoros_gsap.js" in app_content

    def test_shared_ui_components_fast_cdn(self):
        """Verifies dashboard_engine/shared_ui_components.py includes GSAP CDN links."""
        from dashboard_engine.shared_ui_components import FAST_CDN_HEADER, render_kpi_card_html

        assert "https://cdn.jsdelivr.net/npm/gsap@3.12.5/dist/gsap.min.js" in FAST_CDN_HEADER
        assert "ScrollTrigger.min.js" in FAST_CDN_HEADER
        assert "TextPlugin.min.js" in FAST_CDN_HEADER

        kpi_html = render_kpi_card_html("🎯", "Field Completeness", "92.4%", "Test Subtitle")
        assert "mandoros-kpi-card" in kpi_html
        assert "mandoros-kpi-val" in kpi_html
        assert 'data-kpi-val="92.4%"' in kpi_html

    def test_prisma_flow_html_gsap(self):
        """Verifies src/prisma/dashboard_ui.py includes GSAP CDN and animated classes."""
        from src.prisma.dashboard_ui import create_prisma_flow_html

        flow_html = create_prisma_flow_html({
            "trials_count": 5,
            "outcomes_count": 28,
            "arms_count": 10,
            "workbooks_imported": 5,
            "critical_findings": 1
        })

        assert "https://cdn.jsdelivr.net/npm/gsap@3.12.5/dist/gsap.min.js" in flow_html
        assert "prisma-stage-card" in flow_html
        assert "prisma-flow-path" in flow_html
        assert "mandoros-kpi-val" in flow_html
        assert "triggerPrismaGsap" in flow_html
