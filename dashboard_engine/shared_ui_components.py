"""
MANDOROS Dashboard Engine: Shared UI Components & Instant Download Bar.
Provides:
- Fast CDN Header (Tailwind, Plotly, DataTables.js, Inter/Cairo fonts)
- Zero-latency Base64 1-Click Instant Download Bar
- Glassmorphism KPI Card Grid
- DataTables Searchable & Sortable Heatmap Renderer
"""

from __future__ import annotations

import base64
import json
import os
import urllib.parse
from typing import Any, Dict, List, Optional
import pandas as pd


FAST_CDN_HEADER = """
<!-- Fast CDN Stack for Standalone MANDOROS HTML Dashboards -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Cairo:wght@500;700;800&display=swap" rel="stylesheet">
<script src="https://cdn.tailwindcss.com"></script>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<link rel="stylesheet" href="https://cdn.datatables.net/1.13.8/css/jquery.dataTables.min.css">
<script src="https://code.jquery.com/jquery-3.7.1.min.js"></script>
<script src="https://cdn.datatables.net/1.13.8/js/jquery.dataTables.min.js"></script>
<style>
  body { font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
  .glass-card {
    background: rgba(15, 23, 42, 0.75);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid rgba(51, 65, 85, 0.7);
  }
  .dataTables_wrapper { color: #CBD5E1 !important; padding: 12px 0; }
  .dataTables_wrapper select, .dataTables_wrapper input {
    background: #1E293B !important;
    border: 1px solid #475569 !important;
    color: #F8FAFC !important;
    border-radius: 6px !important;
    padding: 4px 8px !important;
  }
  table.dataTable tbody tr { background-color: transparent !important; }
  table.dataTable tbody tr:hover { background-color: rgba(51, 65, 85, 0.5) !important; }
  table.dataTable thead th { border-bottom: 2px solid #334155 !important; color: #94A3B8 !important; }
  table.dataTable tbody td { border-bottom: 1px solid #1E293B !important; color: #E2E8F0 !important; }
  .dataTables_paginate .paginate_button { color: #94A3B8 !important; border-radius: 6px !important; }
  .dataTables_paginate .paginate_button.current { background: #0284C7 !important; color: #fff !important; border: none !important; }
  .mandoros-ncpi-fhir-tool { transition: all 0.2s ease; }
  .ncpi-hidden { display: none !important; }
</style>
<script src="/ncpiFhirAddon.js"></script>
<script>
window.mandorosDownloadBlob = window.mandorosDownloadBlob || function(b64Data, filename, mimeType, fallbackUrl) {
  try {
    if (!b64Data) { if (fallbackUrl) window.location.href = fallbackUrl; return false; }
    const bin = atob(b64Data);
    const len = bin.length;
    const bytes = new Uint8Array(len);
    for (let i = 0; i < len; i++) bytes[i] = bin.charCodeAt(i);
    const blob = new Blob([bytes], { type: mimeType || 'application/octet-stream' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.style.display = 'none';
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    setTimeout(() => URL.revokeObjectURL(url), 2000);
    return false;
  } catch(err) {
    console.warn('[MANDOROS] Blob download fallback to link:', err);
    if (fallbackUrl) window.location.href = fallbackUrl;
    return false;
  }
};
</script>
"""


def build_instant_download_banner(
    html_file_path: Optional[str],
    xlsx_file_path: Optional[str] = None,
    phase_label: str = "Phase 1"
) -> str:
    """
    Generates a high-speed, zero-latency HTML action bar with embedded Base64 data URIs
    so the user can download the Interactive HTML Dashboard and Excel Workbook in <0.1s with 1 click,
    or open the Dashboard in a new full-screen browser tab.
    """
    buttons_html = []
    if html_file_path and os.path.exists(html_file_path):
        with open(html_file_path, "rb") as f:
            b64_html = base64.b64encode(f.read()).decode("utf-8")
        fname = os.path.basename(html_file_path)
        norm_h = urllib.parse.quote(html_file_path.replace("\\", "/"), safe="/:")
        h_dl_url = f"/api/download?file={urllib.parse.quote(fname)}"
        buttons_html.append(f'''
            <a href="{h_dl_url}" download="{fname}" data-base64="data:text/html;base64,{b64_html}"
               onclick="if(window.mandorosDownloadBlob){{return window.mandorosDownloadBlob('{b64_html}','{fname}','text/html;charset=utf-8','{h_dl_url}');}}"
               style="display:inline-flex;align-items:center;gap:8px;background:linear-gradient(135deg,#10B981,#059669);color:#fff;padding:10px 18px;border-radius:10px;font-weight:700;font-size:13px;text-decoration:none;box-shadow:0 4px 14px rgba(16,185,129,0.35);transition:all 0.2s;"
               onmouseover="this.style.transform='translateY(-1px)'" onmouseout="this.style.transform='none'">
               ⚡ Instant Download {phase_label} Interactive Dashboard (.html)
            </a>
            <a href="/gradio_api/file={norm_h}" target="_blank"
               style="display:inline-flex;align-items:center;gap:8px;background:linear-gradient(135deg,#06B6D4,#0891B2);color:#fff;padding:10px 18px;border-radius:10px;font-weight:700;font-size:13px;text-decoration:none;box-shadow:0 4px 14px rgba(6,182,212,0.35);transition:all 0.2s;"
               onmouseover="this.style.transform='translateY(-1px)'" onmouseout="this.style.transform='none'">
               🌐 Open Full Dashboard (New Tab)
            </a>
        ''')
    if xlsx_file_path and os.path.exists(xlsx_file_path):
        with open(xlsx_file_path, "rb") as f:
            b64_xlsx = base64.b64encode(f.read()).decode("utf-8")
        xname = os.path.basename(xlsx_file_path)
        x_dl_url = f"/api/download?file={urllib.parse.quote(xname)}"
        buttons_html.append(f'''
            <a href="{x_dl_url}" download="{xname}" data-base64="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64_xlsx}"
               onclick="if(window.mandorosDownloadBlob){{return window.mandorosDownloadBlob('{b64_xlsx}','{xname}','application/vnd.openxmlformats-officedocument.spreadsheetml.sheet','{x_dl_url}');}}"
               style="display:inline-flex;align-items:center;gap:8px;background:linear-gradient(135deg,#3B82F6,#2563EB);color:#fff;padding:10px 18px;border-radius:10px;font-weight:700;font-size:13px;text-decoration:none;box-shadow:0 4px 14px rgba(59,130,246,0.35);transition:all 0.2s;"
               onmouseover="this.style.transform='translateY(-1px)'" onmouseout="this.style.transform='none'">
               📊 Instant Download {phase_label} Excel Workbook (.xlsx)
            </a>
        ''')

    # Optional Phase 1 NIH NCPI / HL7 FHIR (EBMonFHIR) Multi-Format Standards Export
    if "1" in str(phase_label) or "Single-Trial" in str(phase_label):
        buttons_html.append('''
            <button type="button" class="mandoros-ncpi-fhir-tool" onclick="if(window.exportToNCPIFhir){window.exportToNCPIFhir();}else{var s=document.createElement('script');s.src='/ncpiFhirAddon.js';s.onload=function(){if(window.exportToNCPIFhir)window.exportToNCPIFhir();};document.head.appendChild(s);}"
               title="Export 88 atomic fields as an HL7 FHIR Bundle (JSON) conforming to EBMonFHIR specification"
               style="display:inline-flex;align-items:center;gap:6px;background:linear-gradient(135deg,#8B5CF6,#7C3AED);color:#fff;padding:10px 16px;border-radius:10px;font-weight:700;font-size:12.5px;border:none;cursor:pointer;box-shadow:0 4px 14px rgba(139,92,246,0.35);transition:all 0.2s;"
               onmouseover="this.style.transform='translateY(-1px)'" onmouseout="this.style.transform='none'">
               🧬 Export HL7 FHIR (JSON)
            </button>
            <button type="button" class="mandoros-ncpi-fhir-tool" onclick="if(window.exportToNCPIFhirExcel){window.exportToNCPIFhirExcel();}else{var s=document.createElement('script');s.src='/ncpiFhirAddon.js';s.onload=function(){if(window.exportToNCPIFhirExcel)window.exportToNCPIFhirExcel();};document.head.appendChild(s);}"
               title="Export 88 atomic fields as a Multi-Sheet HL7 FHIR Relational Excel Workbook (.xlsx)"
               style="display:inline-flex;align-items:center;gap:6px;background:linear-gradient(135deg,#059669,#047857);color:#fff;padding:10px 16px;border-radius:10px;font-weight:700;font-size:12.5px;border:none;cursor:pointer;box-shadow:0 4px 14px rgba(5,150,105,0.35);transition:all 0.2s;"
               onmouseover="this.style.transform='translateY(-1px)'" onmouseout="this.style.transform='none'">
               📊 Export FHIR Excel (.xlsx)
            </button>
            <button type="button" class="mandoros-ncpi-fhir-tool" onclick="if(window.exportToNCPIFhirDashboard){window.exportToNCPIFhirDashboard();}else{var s=document.createElement('script');s.src='/ncpiFhirAddon.js';s.onload=function(){if(window.exportToNCPIFhirDashboard)window.exportToNCPIFhirDashboard();};document.head.appendChild(s);}"
               title="Open standalone Interactive HL7 FHIR & NCPI Interoperability Dashboard"
               style="display:inline-flex;align-items:center;gap:6px;background:linear-gradient(135deg,#0284C7,#0369A1);color:#fff;padding:10px 16px;border-radius:10px;font-weight:700;font-size:12.5px;border:none;cursor:pointer;box-shadow:0 4px 14px rgba(2,132,199,0.35);transition:all 0.2s;"
               onmouseover="this.style.transform='translateY(-1px)'" onmouseout="this.style.transform='none'">
               🌐 FHIR Dashboard
            </button>
        ''')

    if not buttons_html:
        return f'''
        <div style="display:flex;align-items:center;justify-content:space-between;padding:12px 16px;background:rgba(15,23,42,0.6);border:1px dashed #334155;border-radius:12px;margin-bottom:14px;color:#94A3B8;font-size:13px;">
          <span>⏳ {phase_label} Deliverables will appear here once synthesis completes.</span>
        </div>
        '''

    return f'''
    <div style="display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:12px;padding:14px 18px;background:linear-gradient(90deg,#0F172A,#1E293B);border:1.5px solid rgba(56,189,248,0.4);border-radius:14px;margin-bottom:16px;box-shadow:0 8px 24px rgba(0,0,0,0.4);">
        <div style="display:flex;align-items:center;gap:10px;">
          <div style="width:36px;height:36px;border-radius:10px;background:rgba(56,189,248,0.15);display:flex;align-items:center;justify-content:center;font-size:18px;">🚀</div>
          <div>
            <div style="color:#F8FAFC;font-weight:800;font-size:14.5px;">{phase_label} Verified Interactive Deliverables Ready</div>
            <div style="color:#94A3B8;font-size:11.5px;">Zero-latency 1-click downloads embedded as Base64 data URIs</div>
          </div>
        </div>
        <div style="display:flex;flex-wrap:wrap;gap:10px;">{"".join(buttons_html)}</div>
    </div>
    '''


def render_kpi_card_html(
    icon: str,
    title: str,
    value: str,
    subtitle: str = "",
    badge: str = "",
    badge_color: str = "#10B981"
) -> str:
    """Renders a modern glassmorphism KPI card with tailwind styling."""
    badge_html = f"<span style='background: {badge_color}22; color: {badge_color}; border: 1px solid {badge_color};' class='text-[10px] font-bold px-2 py-0.5 rounded-full'>{badge}</span>" if badge else ""
    return f"""
    <div class="glass-card rounded-xl p-4 flex flex-col justify-between hover:border-slate-500 transition-all shadow-lg">
      <div class="flex items-center justify-between mb-2">
        <span class="text-xs uppercase tracking-wider font-semibold text-slate-400">{title}</span>
        <div class="flex items-center gap-1.5">
          {badge_html}
          <span class="text-xl">{icon}</span>
        </div>
      </div>
      <div class="text-xl font-extrabold text-white tracking-tight my-1 truncate">{value}</div>
      <div class="text-[11px] text-slate-400 truncate">{subtitle}</div>
    </div>
    """


def render_datatable_component(df: pd.DataFrame, table_id: str, title: str = "") -> str:
    """Renders an interactive searchable, paginated HTML DataTable with jQuery DataTables."""
    if df is None or df.empty:
        return f"<div class='p-4 text-slate-400 text-sm'>No tabular records to display for {title}.</div>"

    cols = list(df.columns)
    headers_html = "".join([f"<th class='text-left py-2 px-3 text-xs uppercase tracking-wider text-slate-400 bg-slate-900'>{c}</th>" for c in cols])

    rows_html = []
    for _, row in df.head(300).iterrows():
        tds = []
        for c in cols:
            val = str(row[c]) if pd.notna(row[c]) else ""
            # Apply color pill if cell contains specific patterns
            if val.lower() in ["low", "low risk", "passed", "reported"]:
                cell_html = f"<span class='bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 px-2 py-0.5 rounded text-xs font-semibold'>{val}</span>"
            elif val.lower() in ["some concerns", "moderate", "unclear"]:
                cell_html = f"<span class='bg-amber-500/15 text-amber-400 border border-amber-500/30 px-2 py-0.5 rounded text-xs font-semibold'>{val}</span>"
            elif val.lower() in ["high", "high risk", "failed", "not_reported"]:
                cell_html = f"<span class='bg-rose-500/15 text-rose-400 border border-rose-500/30 px-2 py-0.5 rounded text-xs font-semibold'>{val}</span>"
            else:
                cell_html = f"<span class='text-xs text-slate-200'>{val}</span>"
            tds.append(f"<td class='py-2 px-3 align-middle'>{cell_html}</td>")
        rows_html.append(f"<tr class='hover:bg-slate-800/50 border-b border-slate-800/80'>{''.join(tds)}</tr>")

    table_html = f"""
    <div class="my-3">
      {f'<h4 class="text-sm font-bold text-slate-300 mb-2 flex items-center gap-2"><span>📋</span> {title}</h4>' if title else ''}
      <div class="overflow-x-auto rounded-lg border border-slate-700 bg-slate-900/60 p-2">
        <table id="{table_id}" class="display responsive nowrap w-full text-xs">
          <thead>
            <tr>{headers_html}</tr>
          </thead>
          <tbody>
            {"".join(rows_html)}
          </tbody>
        </table>
      </div>
      <script>
        $(document).ready(function() {{
          if (!$.fn.DataTable.isDataTable('#{table_id}')) {{
            $('#{table_id}').DataTable({{
              pageLength: 10,
              lengthMenu: [5, 10, 25, 50],
              responsive: true,
              order: []
            }});
          }}
        }});
      </script>
    </div>
    """
    return table_html
