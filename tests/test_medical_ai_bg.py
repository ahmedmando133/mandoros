"""
Test suite validating the mandatory futuristic medical AI background implementation.
Ensures full viewport coverage, responsive layering (z-index 0, 1, 10+),
and global propagation across the main app and standalone dashboards.
"""

from pathlib import Path
from PIL import Image

ROOT_DIR = Path(__file__).resolve().parent.parent


def test_background_assets_exist_and_high_res():
    """Verify that background image assets exist in both assets/ and static/ in high resolution."""
    jpg_path = ROOT_DIR / "static" / "mandoros_medical_ai_bg.jpg"
    webp_path = ROOT_DIR / "static" / "mandoros_medical_ai_bg.webp"
    assets_jpg = ROOT_DIR / "assets" / "mandoros_medical_ai_bg.jpg"

    assert jpg_path.exists(), "static/mandoros_medical_ai_bg.jpg must exist"
    assert assets_jpg.exists(), "assets/mandoros_medical_ai_bg.jpg must exist"

    with Image.open(jpg_path) as img:
        assert img.width >= 1920, f"Expected high-res image (>=1920 width), got {img.width}"
        assert img.height >= 1000, f"Expected high-res image (>=1000 height), got {img.height}"

    if webp_path.exists():
        with Image.open(webp_path) as img:
            assert img.width >= 1920


def test_app_py_background_layering_and_rules():
    """Verify layering rules in app.py: z-index 0 for image, 1 for overlay, 10+ for content."""
    app_code = (ROOT_DIR / "app.py").read_text(encoding="utf-8")

    # Background canvas container
    assert "mandoros-global-bg-container" in app_code
    assert "mandoros-bg-image-layer" in app_code
    assert "mandoros-bg-vignette-layer" in app_code

    # Layering rules verification
    assert "z-index: 0 !important" in app_code
    assert "z-index: 1 !important" in app_code
    assert "z-index: 10 !important" in app_code

    # Cover & responsive rules
    assert "background-size: cover !important" in app_code
    assert "background-attachment: fixed !important" in app_code

    # HTTP serving endpoints
    assert "/mandoros_bg.jpg" in app_code
    assert "/static/mandoros_medical_ai_bg.jpg" in app_code


def test_shared_ui_components_has_background():
    """Verify that exported dashboards automatically inherit the medical AI background."""
    shared_ui = (ROOT_DIR / "dashboard_engine" / "shared_ui_components.py").read_text(encoding="utf-8")
    assert "mandoros-global-bg-container" in shared_ui
    assert "mandoros-bg-image-layer" in shared_ui
    assert "mandoros-bg-vignette-layer" in shared_ui
    assert "mandoros_medical_ai_bg" in shared_ui
