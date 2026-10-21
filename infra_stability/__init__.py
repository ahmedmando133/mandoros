"""
infra_stability package for MANDOROS.
Provides:
- session_isolator: Per-user isolated workspaces preventing multi-user collisions
- storage_memory_janitor: Background disk and RAM auto-cleanup for Render
- pwa_manifest_injector: PWA manifest and service worker injection
- mirror_and_app_bar: Top multi-channel status bar linking Render, 16GB HF Mirror, PWA & Desktop
"""

from infra_stability.session_isolator import (
    SESSION_ROOT,
    create_isolated_session,
    get_session_file_path,
)
from infra_stability.storage_memory_janitor import (
    cleanup_expired_sessions,
    start_background_janitor,
    get_storage_stats,
)
from infra_stability.pwa_manifest_injector import (
    get_pwa_head_html,
    inject_pwa_head_tags,
)
from infra_stability.mirror_and_app_bar import (
    render_mirror_and_app_bar,
)
from infra_stability.ncpi_fhir_addon import (
    get_ncpi_fhir_head_tags,
    render_ncpi_fhir_pillar_html,
    render_phase2_rxnorm_component_html,
    render_phase3_nih_benchmark_html,
)
from infra_stability.gsap_injector import (
    GSAP_CDN_SCRIPTS,
    GSAP_BOOTSTRAP_JS,
    get_gsap_head_tags,
)
from infra_stability.lucide_icons import get_icon

__all__ = [
    "SESSION_ROOT",
    "create_isolated_session",
    "get_session_file_path",
    "cleanup_expired_sessions",
    "start_background_janitor",
    "get_storage_stats",
    "get_pwa_head_html",
    "inject_pwa_head_tags",
    "render_mirror_and_app_bar",
    "get_ncpi_fhir_head_tags",
    "render_ncpi_fhir_pillar_html",
    "render_phase2_rxnorm_component_html",
    "render_phase3_nih_benchmark_html",
    "GSAP_CDN_SCRIPTS",
    "GSAP_BOOTSTRAP_JS",
    "get_gsap_head_tags",
    "get_icon",
]
