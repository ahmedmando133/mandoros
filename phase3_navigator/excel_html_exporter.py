"""
Phase 3 Excel and Interactive HTML Exporter.
Exports the complete research synthesis dossier into:
1. 6-sheet color-coded Excel workbook (openpyxl PatternFill #D1FAE5, #FEF3C7, #FEE2E2)
2. Standalone interactive HTML dossier with embedded tables, search queries, and blueprints
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Dict, List, Optional
import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from phase3_navigator.gap_taxonomy_extractor import ScientificGap
from phase3_navigator.global_reality_checker import RealityCheckVerdict
from phase3_navigator.sample_size_and_risk import (
    SampleSizeResult,
    SampleSizeSensitivityTable,
    ProtocolRiskReport,
)
from phase3_navigator.thesis_protocol_builder import ThesisBlueprint
from phase3_navigator.schema_ingestor import IngestedTrialData


class Phase3DossierExporter:
    """
    Exports Phase 3 findings into publication-standard deliverables.
    """

    # Excel Theme Colors
    COLOR_HEADER_BG = "0F172A"      # Slate 900
    COLOR_HEADER_FONT = "F8FAFC"    # Slate 50
    COLOR_GREEN_BG = "D1FAE5"       # Emerald 100
    COLOR_GREEN_FONT = "065F46"     # Emerald 800
    COLOR_YELLOW_BG = "FEF3C7"      # Amber 100
    COLOR_YELLOW_FONT = "92400E"    # Amber 800
    COLOR_RED_BG = "FEE2E2"         # Rose 100
    COLOR_RED_FONT = "991B1B"       # Rose 800
    COLOR_ZEBRA_BG = "F8FAFC"       # Slate 50

    @classmethod
    def export_excel(
        cls,
        output_path: str,
        gaps: List[ScientificGap],
        sensitivity_table: Optional[SampleSizeSensitivityTable],
        risk_report: Optional[ProtocolRiskReport],
        blueprint: Optional[ThesisBlueprint],
        trial_data: Optional[IngestedTrialData] = None,
    ) -> str:
        """
        Creates the standardized 6-sheet color-coded Excel workbook:
        Sheet 1: Executive Gap Matrix
        Sheet 2: Evidence & Gap Map Data
        Sheet 3: Sample Size & Power Models
        Sheet 4: Protocol Risk Audit
        Sheet 5: GRADE Summary of Findings
        Sheet 6: Search Strategies & Blueprints
        """
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        wb = openpyxl.Workbook()

        # Styles
        header_font = Font(name="Calibri", size=11, bold=True, color=cls.COLOR_HEADER_FONT)
        header_fill = PatternFill(start_color=cls.COLOR_HEADER_BG, end_color=cls.COLOR_HEADER_BG, fill_type="solid")
        title_font = Font(name="Calibri", size=14, bold=True, color="0F172A")
        sub_font = Font(name="Calibri", size=10, italic=True, color="64748B")
        regular_font = Font(name="Calibri", size=10)
        bold_font = Font(name="Calibri", size=10, bold=True)
        thin_border = Border(
            left=Side(style="thin", color="CBD5E1"),
            right=Side(style="thin", color="CBD5E1"),
            top=Side(style="thin", color="CBD5E1"),
            bottom=Side(style="thin", color="CBD5E1"),
        )
        align_center = Alignment(horizontal="center", vertical="center", wrap_text=True)
        align_left = Alignment(horizontal="left", vertical="center", wrap_text=True)

        fill_green = PatternFill(start_color=cls.COLOR_GREEN_BG, end_color=cls.COLOR_GREEN_BG, fill_type="solid")
        font_green = Font(name="Calibri", size=10, bold=True, color=cls.COLOR_GREEN_FONT)

        fill_yellow = PatternFill(start_color=cls.COLOR_YELLOW_BG, end_color=cls.COLOR_YELLOW_BG, fill_type="solid")
        font_yellow = Font(name="Calibri", size=10, bold=True, color=cls.COLOR_YELLOW_FONT)

        fill_red = PatternFill(start_color=cls.COLOR_RED_BG, end_color=cls.COLOR_RED_BG, fill_type="solid")
        font_red = Font(name="Calibri", size=10, bold=True, color=cls.COLOR_RED_FONT)

        fill_zebra = PatternFill(start_color=cls.COLOR_ZEBRA_BG, end_color=cls.COLOR_ZEBRA_BG, fill_type="solid")

        # =========================================================================
        # Sheet 1: Executive Gap Matrix
        # =========================================================================
        ws1 = wb.active
        ws1.title = "Executive Gap Matrix"
        ws1.views.sheetView[0].showGridLines = True

        ws1["A1"] = "MANDOROS Phase 3: Research Gap & Thesis Navigator — Executive Gap Matrix"
        ws1["A1"].font = title_font
        ws1["A2"] = f"Generated on {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')} | Strict Evidence-Linked Gap Taxonomy & Real-Time Reality Checks"
        ws1["A2"].font = sub_font

        headers1 = [
            "Gap ID", "Taxonomy Category", "Category Badge", "Gap Title & Target",
            "Source File", "Sheet & Cell Coordinate", "Exact Extracted Evidence Quote",
            "Global Reality Check", "PubMed RCTs", "ClinicalTrials.gov Total",
            "CT.gov Ongoing", "Actionable Thesis Resolution"
        ]
        row_idx = 4
        for col_idx, h in enumerate(headers1, 1):
            cell = ws1.cell(row=row_idx, column=col_idx, value=h)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = align_center
            cell.border = thin_border
        ws1.row_dimensions[row_idx].height = 28

        for g in gaps:
            row_idx += 1
            ws1.row_dimensions[row_idx].height = 36
            vals = [
                g.gap_id,
                g.category.value,
                g.badge_label,
                g.title,
                g.source_file_name,
                f"{g.source_sheet} [{g.row_coord}]",
                g.exact_extracted_value_or_quote,
                f"{g.traffic_light_color}: {g.status_label}",
                g.pubmed_rct_count,
                g.ctgov_total_count,
                g.ctgov_ongoing_count,
                g.actionable_recommendation or g.proposed_resolution,
            ]
            for col_idx, v in enumerate(vals, 1):
                cell = ws1.cell(row=row_idx, column=col_idx, value=v)
                cell.font = regular_font
                cell.border = thin_border
                cell.alignment = align_center if col_idx in [1, 2, 3, 5, 6, 8, 9, 10, 11] else align_left

                # Highlight Reality Check column (Col 8)
                if col_idx == 8:
                    if g.traffic_light_color == "GREEN":
                        cell.fill = fill_green
                        cell.font = font_green
                    elif g.traffic_light_color == "YELLOW":
                        cell.fill = fill_yellow
                        cell.font = font_yellow
                    else:
                        cell.fill = fill_red
                        cell.font = font_red
                elif row_idx % 2 == 1:
                    cell.fill = fill_zebra

        # =========================================================================
        # Sheet 2: Evidence & Gap Map Data
        # =========================================================================
        ws2 = wb.create_sheet("Evidence & Gap Map Data")
        ws2.views.sheetView[0].showGridLines = True
        ws2["A1"] = "Campbell Collaboration / EviAtlas Standard Evidence & Gap Map Data Table"
        ws2["A1"].font = title_font

        headers2 = [
            "Intervention & Subpopulation Domain", "Clinical Outcome Domain",
            "Mapped Gap ID", "Sample Dimension (N)", "Traffic Light Status",
            "Exact Provenance Coordinate"
        ]
        row_idx = 3
        for col_idx, h in enumerate(headers2, 1):
            cell = ws2.cell(row=row_idx, column=col_idx, value=h)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = align_center
            cell.border = thin_border

        for g in gaps:
            row_idx += 1
            ws2.row_dimensions[row_idx].height = 24
            vals = [
                f"{trial_data.drug_name or 'Investigational Agent'} Subpopulation Domain",
                g.title,
                g.gap_id,
                trial_data.total_sample_size if trial_data else 300,
                g.traffic_light_color,
                f"{g.source_sheet} [{g.row_coord}]",
            ]
            for col_idx, v in enumerate(vals, 1):
                cell = ws2.cell(row=row_idx, column=col_idx, value=v)
                cell.font = regular_font
                cell.border = thin_border
                cell.alignment = align_center if col_idx in [3, 4, 5, 6] else align_left

        # =========================================================================
        # Sheet 3: Sample Size & Power Models
        # =========================================================================
        ws3 = wb.create_sheet("Sample Size & Power Models")
        ws3.views.sheetView[0].showGridLines = True
        ws3["A1"] = "Biostatistical Sample Size Planning & Multi-Scenario Sensitivity Matrix"
        ws3["A1"].font = title_font

        if sensitivity_table and sensitivity_table.base_result:
            base = sensitivity_table.base_result
            ws3["A3"] = f"Primary Design: {base.design_name}"
            ws3["A3"].font = bold_font
            ws3["A4"] = f"Mathematical Formula: {base.formula_plain}"
            ws3["A4"].font = regular_font
            ws3["A5"] = f"Clinical Rationale: {base.justification_narrative}"
            ws3["A5"].font = sub_font

        headers3 = [
            "Effect Scenario", "Target Δ", "Alpha (α)", "Power (1-β)",
            "n / arm (evaluable)", "N Total (evaluable)", "N Enrolled (with Attrition)"
        ]
        row_idx = 7
        for col_idx, h in enumerate(headers3, 1):
            cell = ws3.cell(row=row_idx, column=col_idx, value=h)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = align_center
            cell.border = thin_border

        if sensitivity_table and sensitivity_table.scenarios:
            for sc in sensitivity_table.scenarios:
                row_idx += 1
                ws3.row_dimensions[row_idx].height = 22
                vals = list(sc.values())
                for col_idx, v in enumerate(vals, 1):
                    cell = ws3.cell(row=row_idx, column=col_idx, value=v)
                    cell.font = regular_font
                    cell.border = thin_border
                    cell.alignment = align_center if col_idx > 1 else align_left

        # =========================================================================
        # Sheet 4: Protocol Risk Audit
        # =========================================================================
        ws4 = wb.create_sheet("Protocol Risk Audit")
        ws4.views.sheetView[0].showGridLines = True
        ws4["A1"] = "Protocol Risk Auditor (Wood & McNair 2023 / fastdatascience standard)"
        ws4["A1"].font = title_font

        if risk_report:
            ws4["A2"] = f"Overall Informative Score: {risk_report.total_score:.1f}/100 — Status: {risk_report.risk_category}"
            ws4["A2"].font = bold_font

        headers4 = ["Risk Domain", "Score Awarded", "Findings in Uploaded Evidence", "Mandatory Protocol Safeguard"]
        row_idx = 4
        for col_idx, h in enumerate(headers4, 1):
            cell = ws4.cell(row=row_idx, column=col_idx, value=h)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = align_center
            cell.border = thin_border

        if risk_report and risk_report.domains:
            for d in risk_report.domains:
                row_idx += 1
                ws4.row_dimensions[row_idx].height = 36
                vals = [d.domain_name, f"{d.awarded_score:.1f} / {d.max_score:.1f}", d.findings, d.actionable_safeguard]
                for col_idx, v in enumerate(vals, 1):
                    cell = ws4.cell(row=row_idx, column=col_idx, value=v)
                    cell.font = regular_font
                    cell.border = thin_border
                    cell.alignment = align_center if col_idx == 2 else align_left

        # =========================================================================
        # Sheet 5: GRADE Summary of Findings
        # =========================================================================
        ws5 = wb.create_sheet("GRADE Summary of Findings")
        ws5.views.sheetView[0].showGridLines = True
        ws5["A1"] = "GRADE Summary of Findings (SoF) Table"
        ws5["A1"].font = title_font

        headers5 = [
            "Outcome", "Participants (Studies)", "Relative Effect (95% CI)",
            "Anticipated Absolute Effect", "Risk of Bias", "Inconsistency",
            "Indirectness", "Imprecision", "Publication Bias", "Certainty (GRADE)"
        ]
        row_idx = 3
        for col_idx, h in enumerate(headers5, 1):
            cell = ws5.cell(row=row_idx, column=col_idx, value=h)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = align_center
            cell.border = thin_border

        if blueprint and blueprint.grade_table:
            for gr in blueprint.grade_table.rows:
                row_idx += 1
                ws5.row_dimensions[row_idx].height = 30
                vals = [
                    gr.outcome_name, gr.participants_studies, gr.relative_effect,
                    gr.anticipated_absolute_effect, gr.risk_of_bias, gr.inconsistency,
                    gr.indirectness, gr.imprecision, gr.publication_bias, gr.overall_certainty
                ]
                for col_idx, v in enumerate(vals, 1):
                    cell = ws5.cell(row=row_idx, column=col_idx, value=v)
                    cell.font = regular_font
                    cell.border = thin_border
                    cell.alignment = align_center if col_idx in [2, 5, 6, 7, 8, 9, 10] else align_left

        # =========================================================================
        # Sheet 6: Search Strategies & Blueprints
        # =========================================================================
        ws6 = wb.create_sheet("Search Strategies & Blueprints")
        ws6.views.sheetView[0].showGridLines = True
        ws6["A1"] = "Validated Boolean Search Strategies & Academic Blueprints"
        ws6["A1"].font = title_font

        if blueprint:
            ws6["A3"] = "1. Reproducible PubMed Search Strategy:"
            ws6["A3"].font = bold_font
            ws6["A4"] = blueprint.pubmed_boolean_query
            ws6["A4"].font = regular_font

            ws6["A6"] = "2. Cochrane CENTRAL Search Strategy:"
            ws6["A6"].font = bold_font
            ws6["A7"] = blueprint.cochrane_boolean_query
            ws6["A7"].font = regular_font

            ws6["A9"] = "3. Embase Search Strategy:"
            ws6["A9"].font = bold_font
            ws6["A10"] = blueprint.embase_boolean_query
            ws6["A10"].font = regular_font

            ws6["A12"] = "4. Path A: PROSPERO Registration Protocol (Key Sections):"
            ws6["A12"].font = bold_font
            r = 13
            for k, val in list(blueprint.prospero_protocol_draft.items())[:10]:
                ws6.cell(row=r, column=1, value=f"{k}: {val}").font = regular_font
                r += 1

        # Auto-adjust column widths for all sheets
        for ws in wb.worksheets:
            for col in ws.columns:
                max_len = 0
                col_letter = get_column_letter(col[0].column)
                for cell in col:
                    if cell.value:
                        lines = str(cell.value).split("\n")
                        for l in lines:
                            if len(l) > max_len:
                                max_len = len(l)
                ws.column_dimensions[col_letter].width = min(50, max(12, max_len + 3))

        wb.save(output_path)
        return output_path

    @classmethod
    def export_html_dossier(
        cls,
        output_path: str,
        gaps: List[ScientificGap],
        sensitivity_table: Optional[SampleSizeSensitivityTable],
        risk_report: Optional[ProtocolRiskReport],
        blueprint: Optional[ThesisBlueprint],
        trial_data: Optional[IngestedTrialData] = None,
        egm_fig_html: str = "",
        rob_fig_html: str = "",
    ) -> str:
        """
        Exports a standalone, publication-quality HTML research dossier.
        """
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        drug = trial_data.drug_name if trial_data else "Investigational Agent"
        condition = trial_data.condition if trial_data else "Target Condition"

        gaps_rows_html = []
        for g in gaps:
            badge_class = "badge-green" if g.traffic_light_color == "GREEN" else ("badge-yellow" if g.traffic_light_color == "YELLOW" else "badge-red")
            gaps_rows_html.append(f"""
            <tr>
              <td><strong>{g.gap_id}</strong></td>
              <td><span class='badge'>{g.badge_label}</span></td>
              <td><strong>{g.title}</strong><br><small style='color: #64748B;'>{g.description}</small></td>
              <td><span class='code-pill'>{g.source_sheet} [{g.row_coord}]</span><br><em>"{g.exact_extracted_value_or_quote[:60]}..."</em></td>
              <td><span class='{badge_class}'>{g.traffic_light_color}: {g.status_label}</span></td>
              <td>PubMed: <strong>{g.pubmed_rct_count}</strong><br>CT.gov: <strong>{g.ctgov_total_count}</strong></td>
              <td><small>{g.actionable_recommendation}</small></td>
            </tr>
            """)

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>MANDOROS Phase 3: Research Gap &amp; Thesis Navigator Dossier</title>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background: #0F172A;
      color: #F8FAFC;
      margin: 0;
      padding: 30px;
    }}
    .container {{
      max-width: 1300px;
      margin: 0 auto;
    }}
    .header {{
      background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
      border: 1px solid #334155;
      border-radius: 16px;
      padding: 24px 32px;
      margin-bottom: 24px;
      box-shadow: 0 10px 25px rgba(0,0,0,0.5);
    }}
    .header h1 {{
      margin: 0 0 8px 0;
      font-size: 24px;
      color: #38BDF8;
    }}
    .header p {{
      margin: 0;
      color: #94A3B8;
      font-size: 14px;
    }}
    .card {{
      background: #1E293B;
      border: 1px solid #334155;
      border-radius: 12px;
      padding: 20px 24px;
      margin-bottom: 24px;
    }}
    .card h2 {{
      margin-top: 0;
      font-size: 18px;
      color: #F1F5F9;
      border-bottom: 1px solid #334155;
      padding-bottom: 10px;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin-top: 12px;
      font-size: 13px;
    }}
    th, td {{
      padding: 10px 12px;
      border: 1px solid #334155;
      text-align: left;
    }}
    th {{
      background: #0F172A;
      color: #94A3B8;
      font-weight: 700;
      text-transform: uppercase;
      font-size: 11px;
    }}
    tr:nth-child(even) {{
      background: rgba(15, 23, 42, 0.4);
    }}
    .badge {{
      display: inline-block;
      padding: 4px 8px;
      border-radius: 6px;
      font-size: 11px;
      font-weight: 700;
      background: #334155;
      color: #CBD5E1;
    }}
    .badge-green {{
      background: #D1FAE5;
      color: #065F46;
      padding: 4px 10px;
      border-radius: 9999px;
      font-weight: 800;
      font-size: 11px;
    }}
    .badge-yellow {{
      background: #FEF3C7;
      color: #92400E;
      padding: 4px 10px;
      border-radius: 9999px;
      font-weight: 800;
      font-size: 11px;
    }}
    .badge-red {{
      background: #FEE2E2;
      color: #991B1B;
      padding: 4px 10px;
      border-radius: 9999px;
      font-weight: 800;
      font-size: 11px;
    }}
    .code-pill {{
      font-family: monospace;
      font-size: 11px;
      background: #020617;
      color: #38BDF8;
      padding: 2px 6px;
      border-radius: 4px;
    }}
    .code-box {{
      background: #020617;
      border: 1px solid #1E293B;
      border-radius: 8px;
      padding: 12px 16px;
      font-family: monospace;
      font-size: 12px;
      color: #38BDF8;
      word-break: break-all;
      margin-top: 8px;
    }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>🧭 MANDOROS Phase 3: Research Gap &amp; Thesis Navigator</h1>
      <p>Target Agent: <strong>{drug}</strong> | Condition: <strong>{condition}</strong> | Generated: <strong>{timestamp}</strong></p>
    </div>

    <!-- Section 1: Visual EGM Matrix -->
    <div class="card">
      <h2>🗺️ Evidence &amp; Gap Map (Campbell / EviAtlas Standard)</h2>
      {egm_fig_html or '<p style="color:#94A3B8;">Evidence & Gap Map visualization ready.</p>'}
    </div>

    <!-- Section 2: Gap Taxonomy Table -->
    <div class="card">
      <h2>🔬 4-Type Gap Taxonomy &amp; Real-Time External Reality Checks</h2>
      <table>
        <thead>
          <tr>
            <th>Gap ID</th>
            <th>Category</th>
            <th>Title &amp; Target</th>
            <th>Source Provenance</th>
            <th>Reality Verdict</th>
            <th>Global Hits</th>
            <th>Actionable Thesis Protocol</th>
          </tr>
        </thead>
        <tbody>
          {"".join(gaps_rows_html)}
        </tbody>
      </table>
    </div>

    <!-- Section 3: Sample Size & Protocol Risk -->
    <div class="card">
      <h2>📐 Biostatistical Sample Size &amp; Protocol Risk Audit (0-100 Pts)</h2>
      <p style="color:#94A3B8;">Evaluated according to presize closed-form formulas and Wood &amp; McNair (2023) uninformative trial criteria.</p>
      {f'<p><strong>Protocol Informative Score:</strong> {risk_report.total_score:.1f}/100 (<span style="color:{risk_report.risk_badge_color}">{risk_report.risk_category}</span>)</p>' if risk_report else ''}
    </div>

    <!-- Section 4: Search Strategies & Blueprints -->
    <div class="card">
      <h2>📜 Reproducible Search Strategy &amp; PROSPERO Blueprint</h2>
      <p><strong>Validated PubMed Boolean Search Strategy:</strong></p>
      <div class="code-box">{blueprint.pubmed_boolean_query if blueprint else 'Query generated at runtime.'}</div>
    </div>
  </div>
</body>
</html>
"""
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        return output_path
