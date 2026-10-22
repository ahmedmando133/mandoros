"""
Top Multi-Channel Mirror & App Status Bar for MANDOROS.
Tier-1 Hardware-Grade Architecture (Adidas x Apple/Samsung x Meta).
Strictly eliminates generic AI styling and replaces emojis with Lucide SVG vectors.
"""

from __future__ import annotations
from infra_stability.lucide_icons import get_icon


def render_mirror_and_app_bar() -> str:
    """
    Renders the hardware-grade status bar HTML for the top of the interface.
    """
    icon_zap = get_icon("zap", size=13, cls="text-sky-400")
    icon_download = get_icon("download", size=13, cls="text-zinc-100")
    icon_laptop = get_icon("laptop", size=13, cls="text-zinc-400")
    icon_shield = get_icon("shield_check", size=13, cls="text-emerald-400")

    return f"""
    <div class="mandoros-top-mirror-bar" style="
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        justify-content: space-between;
        gap: 12px;
        padding: 9px 20px;
        margin: 0 0 16px 0;
        background: linear-gradient(180deg, rgba(18, 18, 24, 0.40) 0%, rgba(9, 9, 14, 0.20) 100%);
        backdrop-filter: blur(14px) saturate(160%);
        -webkit-backdrop-filter: blur(14px) saturate(160%);
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 12px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.45), inset 0 1px 0 rgba(255, 255, 255, 0.10);
        font-family: 'JetBrains Mono', -apple-system, monospace;
    ">
      <!-- Left: Primary & Mirror Channels -->
      <div style="display: flex; flex-wrap: wrap; align-items: center; gap: 10px;">
        <span class="mandoros-prod-badge" style="
            display: inline-flex;
            align-items: center;
            gap: 7px;
            padding: 4px 10px;
            background: rgba(16, 185, 129, 0.12);
            border: 1px solid rgba(16, 185, 129, 0.35);
            border-radius: 6px;
            color: #10B981;
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 0.04em;
        ">
          <span class="mandoros-prod-dot" style="width: 7px; height: 7px; background: #10B981; border-radius: 50%; box-shadow: 0 0 8px #10B981; display: inline-block;"></span>
          PROD // <a href="https://mandoros.onrender.com/" target="_blank" style="color: #34D399; text-decoration: none; margin-left: 2px;">mandoros.onrender.com</a>
        </span>

        <a href="https://huggingface.co/spaces" target="_blank" class="mandoros-hf-badge mandoros-magnetic-btn" style="
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 4px 12px;
            background: rgba(255, 255, 255, 0.06);
            backdrop-filter: blur(8px);
            -webkit-backdrop-filter: blur(8px);
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 6px;
            color: #E4E4E7;
            font-size: 11px;
            font-weight: 600;
            text-decoration: none;
            letter-spacing: 0.03em;
            transition: all 0.2s;
        ">
          {icon_zap} Free 16GB HF Mirror
        </a>
      </div>

      <!-- Center: Academic Attribution (Rawda Mofed Gamal · AJMAN UNIVERSITY) -->
      <div class="mandoros-creator-top-pill mandoros-magnetic-btn" style="
          display: inline-flex;
          align-items: center;
          gap: 8px;
          padding: 4px 14px;
          background: linear-gradient(135deg, rgba(255, 255, 255, 0.08) 0%, rgba(0, 245, 212, 0.12) 100%);
          backdrop-filter: blur(14px);
          -webkit-backdrop-filter: blur(14px);
          border: 1px solid rgba(0, 245, 212, 0.45);
          border-radius: 20px;
          box-shadow: 0 0 16px rgba(0, 245, 212, 0.25), inset 0 1px 0 rgba(255, 255, 255, 0.25);
          font-size: 11px;
          letter-spacing: 0.02em;
          transition: all 0.25s ease;
      " title="Project Inventor & Lead Researcher • Ajman University">
        <span style="font-size: 13px; line-height: 1;">🎓</span>
        <span style="color: #FFFFFF; font-weight: 800; letter-spacing: -0.01em;">Rawda Mofed Gamal</span>
        <span style="color: #475569; font-weight: 600;">•</span>
        <span style="color: #38BDF8; font-weight: 800; letter-spacing: 0.04em;">AJMAN UNIVERSITY</span>
      </div>

      <!-- Right: App Options & Janitor Health -->
      <div style="display: flex; flex-wrap: wrap; align-items: center; gap: 10px;">
        <button class="mandoros-pwa-install-btn mandoros-magnetic-btn" style="
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 5px 12px;
            background: rgba(255, 255, 255, 0.14);
            backdrop-filter: blur(8px);
            -webkit-backdrop-filter: blur(8px);
            border: 1px solid rgba(255, 255, 255, 0.25);
            border-radius: 6px;
            color: #FFFFFF;
            font-size: 11px;
            font-weight: 700;
            cursor: pointer;
            letter-spacing: 0.03em;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.35);
            transition: all 0.2s;
        ">
          {icon_download} Install PWA
        </button>

        <a href="https://github.com/ahmedmando133/MANDOROS" target="_blank" class="mandoros-desktop-badge mandoros-magnetic-btn" style="
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 4px 10px;
            background: rgba(255, 255, 255, 0.06);
            backdrop-filter: blur(8px);
            -webkit-backdrop-filter: blur(8px);
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 6px;
            color: #CBD5E1;
            font-size: 11px;
            font-weight: 600;
            text-decoration: none;
            letter-spacing: 0.02em;
        ">
          {icon_laptop} Desktop App
        </a>

        <span class="mandoros-janitor-badge" style="
            display: inline-flex;
            align-items: center;
            gap: 5px;
            padding: 4px 9px;
            background: rgba(255, 255, 255, 0.04);
            backdrop-filter: blur(8px);
            -webkit-backdrop-filter: blur(8px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 6px;
            color: #94A3B8;
            font-size: 11px;
            font-weight: 500;
        " title="Temp directories >30min or >200MB are pruned automatically">
          {icon_shield} Auto-Janitor 200MB Active
        </span>
      </div>
    </div>
    """
