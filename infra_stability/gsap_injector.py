"""
MANDOROS - GSAP (GreenSock Animation Platform) CDN & Controller Head Injector
Zero Server Overhead (100% Client-Side GPU Accelerated via Lightweight CDN).
Guaranteed Browser DOM Execution via Dynamic Head Injection and Gradio load hooks.
"""

from __future__ import annotations

import os

GSAP_CDN_SCRIPTS = """
<!-- GSAP Core & Plugins via Lightweight CDN (Zero Server Footprint) -->
<script src="https://cdn.jsdelivr.net/npm/gsap@3.12.5/dist/gsap.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.12.5/dist/ScrollTrigger.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.12.5/dist/TextPlugin.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.12.5/dist/Flip.min.js"></script>
"""

# Client-Side Bootstrap Hook executed via demo.load(js=...)
GSAP_BOOTSTRAP_JS = """
() => {
    // Guaranteed Dynamic Head Injection for GSAP and plugins
    const cdnScripts = [
        "https://cdn.jsdelivr.net/npm/gsap@3.12.5/dist/gsap.min.js",
        "https://cdn.jsdelivr.net/npm/gsap@3.12.5/dist/ScrollTrigger.min.js",
        "https://cdn.jsdelivr.net/npm/gsap@3.12.5/dist/TextPlugin.min.js",
        "https://cdn.jsdelivr.net/npm/gsap@3.12.5/dist/Flip.min.js",
        "/mandoros_gsap.js"
    ];

    function loadScriptChain(index) {
        if (index >= cdnScripts.length) {
            if (window.mandorosGsap && typeof window.mandorosGsap.init === 'function') {
                window.mandorosGsap.init();
            }
            return;
        }
        const src = cdnScripts[index];
        const existing = document.querySelector(`script[src="${src}"]`);
        if (existing && window.gsap) {
            loadScriptChain(index + 1);
            return;
        }
        const s = document.createElement("script");
        s.src = src;
        s.async = false;
        s.onload = () => loadScriptChain(index + 1);
        s.onerror = () => loadScriptChain(index + 1);
        document.head.appendChild(s);
    }

    loadScriptChain(0);
}
"""


def get_gsap_head_tags() -> str:
    """
    Returns HTML head tags injecting the GSAP CDN scripts, StyleX/Aceternity CSS variables,
    and the MANDOROS GSAP controller with guaranteed execution.
    """
    repo_root = os.path.dirname(os.path.dirname(__file__))
    js_path = os.path.join(repo_root, "static", "mandoros_gsap.js")
    js_content = ""
    if os.path.exists(js_path):
        try:
            with open(js_path, "r", encoding="utf-8") as f:
                js_content = f.read()
        except Exception:
            js_content = ""

    return f"""
    {GSAP_CDN_SCRIPTS}
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700;800&family=Plus+Jakarta+Sans:wght@500;600;700;800;900&display=swap" rel="stylesheet">
    <style>
      /* Tier-1 Adidas x Apple/Samsung x Meta Design Tokens & Hardware-Grade CSS Variables */
      :root {{
        --bg-obsidian: #09090B;
        --bg-carbon: #121215;
        --bg-surface: #18181B;
        --border-hairline: rgba(255, 255, 255, 0.09);
        --border-active: rgba(255, 255, 255, 0.22);
        --text-titanium: #FAFAFA;
        --text-alabaster: #F4F4F5;
        --text-muted: #A1A1AA;
        --accent-emerald: #10B981;
        --accent-sky: #38BDF8;
        --font-mono: 'JetBrains Mono', monospace;
      }}

      /* GPU Acceleration & Performance Optimizations for GSAP */
      .mandoros-top-mirror-bar,
      .mandoros-ncpi-pillar-container,
      .emblem-wrapper,
      .mandoros-hero-title,
      .mandoros-pipeline-strip,
      .pipeline-node,
      .product-phase-card,
      .academic-pillar-card,
      .mandoros-kpi-card,
      .prisma-stage-card,
      .bento-spotlight-card {{
        will-change: transform, opacity;
        transform: translateZ(0);
        backface-visibility: hidden;
      }}

      /* Aceternity / MagicUI Spotlight cursor-following gradient */
      .bento-spotlight-card {{
        position: relative;
        overflow: hidden;
        border: 1px solid var(--border-hairline);
        background: var(--bg-carbon);
        transition: border-color 0.3s ease;
      }}

      .bento-spotlight-card::before {{
        content: '';
        position: absolute;
        inset: 0;
        background: radial-gradient(400px circle at var(--mouse-x, 50%) var(--mouse-y, 50%), rgba(255, 255, 255, 0.08), transparent 40%);
        pointer-events: none;
        opacity: 0;
        transition: opacity 0.3s ease;
        z-index: 1;
      }}

      .bento-spotlight-card:hover::before {{
        opacity: 1;
      }}

      /* Laser pulse traveling line across pipeline nodes */
      .pipeline-laser-path {{
        stroke-dasharray: 20 80;
        animation: pipelineLaserFlow 3s linear infinite;
      }}

      @keyframes pipelineLaserFlow {{
        0% {{ stroke-dashoffset: 200; }}
        100% {{ stroke-dashoffset: -200; }}
      }}
    </style>
    <script>
    // Inline Guaranteed Loader Chain
    (function() {{
      const scripts = [
        "https://cdn.jsdelivr.net/npm/gsap@3.12.5/dist/gsap.min.js",
        "https://cdn.jsdelivr.net/npm/gsap@3.12.5/dist/ScrollTrigger.min.js",
        "https://cdn.jsdelivr.net/npm/gsap@3.12.5/dist/TextPlugin.min.js",
        "https://cdn.jsdelivr.net/npm/gsap@3.12.5/dist/Flip.min.js",
        "/mandoros_gsap.js"
      ];
      function loadNext(i) {{
        if (i >= scripts.length) {{
          if (window.mandorosGsap && typeof window.mandorosGsap.init === 'function') {{
            window.mandorosGsap.init();
          }}
          return;
        }}
        const url = scripts[i];
        if (document.querySelector('script[src="' + url + '"]') && window.gsap) {{
          loadNext(i + 1);
          return;
        }}
        const s = document.createElement('script');
        s.src = url;
        s.async = false;
        s.onload = function() {{ loadNext(i + 1); }};
        s.onerror = function() {{ loadNext(i + 1); }};
        document.head.appendChild(s);
      }}
      loadNext(0);
    }})();
    </script>
    <script>
    {js_content}
    </script>
    """
