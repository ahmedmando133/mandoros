"""
Top Multi-Channel Mirror & App Status Bar for MANDOROS.
Renders an elegant glassmorphic status banner at the top of the app:
- Keeps Render Primary (mandoros.onrender.com)
- Links to Free 16GB RAM Hugging Face Space Mirror
- One-click PWA App Install trigger
- Standalone Local Windows/Mac Desktop App Runner
- Live Render Storage/RAM Auto-Janitor Health Indicator
"""

from __future__ import annotations


def render_mirror_and_app_bar() -> str:
    """
    Renders top status bar HTML for the Gradio header.
    """
    return """
    <div class="mandoros-top-mirror-bar" style="
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        justify-content: space-between;
        gap: 12px;
        padding: 8px 18px;
        margin: 0 0 16px 0;
        background: rgba(15, 23, 42, 0.85);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(56, 189, 248, 0.25);
        border-radius: 12px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.35);
        font-family: 'Inter', -apple-system, sans-serif;
    ">
      <!-- Left: Primary & Mirror Channels -->
      <div style="display: flex; flex-wrap: wrap; align-items: center; gap: 10px;">
        <span style="
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 4px 10px;
            background: rgba(16, 185, 129, 0.15);
            border: 1px solid rgba(16, 185, 129, 0.5);
            border-radius: 9999px;
            color: #34D399;
            font-size: 11.5px;
            font-weight: 700;
        ">
          <span style="width: 7px; height: 7px; background: #10B981; border-radius: 50%; box-shadow: 0 0 8px #10B981;"></span>
          Primary Production: <a href="https://mandoros.onrender.com/" target="_blank" style="color: #6EE7B7; text-decoration: underline; margin-left: 2px;">mandoros.onrender.com</a>
        </span>

        <a href="https://huggingface.co/spaces" target="_blank" style="
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 4px 12px;
            background: rgba(56, 189, 248, 0.12);
            border: 1px solid rgba(56, 189, 248, 0.4);
            border-radius: 9999px;
            color: #38BDF8;
            font-size: 11.5px;
            font-weight: 700;
            text-decoration: none;
            transition: all 0.2s;
        " onmouseover="this.style.background='rgba(56,189,248,0.25)'" onmouseout="this.style.background='rgba(56,189,248,0.12)'">
          ⚡ Free 16GB HF Mirror
        </a>
      </div>

      <!-- Right: App Options & Janitor Health -->
      <div style="display: flex; flex-wrap: wrap; align-items: center; gap: 10px;">
        <button class="mandoros-pwa-install-btn" style="
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 4px 12px;
            background: linear-gradient(135deg, #6366F1, #4F46E5);
            border: 1px solid #818CF8;
            border-radius: 8px;
            color: #FFFFFF;
            font-size: 11.5px;
            font-weight: 700;
            cursor: pointer;
            box-shadow: 0 2px 10px rgba(99, 102, 241, 0.3);
            transition: all 0.2s;
        " onmouseover="this.style.transform='translateY(-1px)'" onmouseout="this.style.transform='none'">
          📲 Install MANDOROS as App
        </button>

        <a href="https://github.com/" target="_blank" style="
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 4px 10px;
            background: rgba(30, 41, 59, 0.8);
            border: 1px solid #475569;
            border-radius: 8px;
            color: #CBD5E1;
            font-size: 11.5px;
            font-weight: 600;
            text-decoration: none;
        ">
          💻 Desktop App (Win/Mac)
        </a>

        <span style="
            display: inline-flex;
            align-items: center;
            gap: 5px;
            padding: 4px 9px;
            background: rgba(148, 163, 184, 0.1);
            border: 1px solid rgba(148, 163, 184, 0.25);
            border-radius: 8px;
            color: #94A3B8;
            font-size: 11px;
            font-weight: 500;
        " title="Temp directories >30min or >200MB are pruned automatically">
          🛡️ 200MB Auto-Janitor Active
        </span>
      </div>
    </div>
    """
