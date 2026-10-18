"""
PRISMA Dossier Exporter.
Exports traceable multi-sheet Excel intelligence workbooks, CSV audits,
and standalone self-contained HTML research dossiers.
"""

import os
from typing import Any
import pandas as pd
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from src.prisma.models import PrismaTrial, PrismaValidationFinding
from src.prisma.comparator import PrismaTrialComparator
from src.prisma.outcome_explorer import PrismaOutcomeExplorer


class PrismaDossierExporter:
    """Export service for PRISMA intelligence reports with 100% cell-level traceability."""

    def __init__(
        self,
        trials: dict[str, PrismaTrial],
        validation_findings: list[PrismaValidationFinding],
        overview_metrics: dict[str, Any],
    ):
        self.trials = trials
        self.validation_findings = validation_findings
        self.overview_metrics = overview_metrics
        self.comparator = PrismaTrialComparator(trials)
        self.explorer = PrismaOutcomeExplorer(trials)

    def export_excel_dossier(self, output_path: str = "outputs/PRISMA_Clinical_Intelligence_Dossier.xlsx") -> str:
        """
        Creates a dedicated, multi-sheet PRISMA Excel dossier without altering any source workbooks.
        Includes full provenance trail and data-quality audit ledger.
        """
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        wb = openpyxl.Workbook()
        wb.remove(wb.active)  # Remove default sheet

        # Styles
        header_fill = PatternFill(start_color="0F172A", end_color="0F172A", fill_type="solid")
        header_font = Font(name="Calibri", size=11, bold=True, color="00F5D4")
        sub_fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
        sub_font = Font(name="Calibri", size=10, bold=True, color="38BDF8")
        data_font = Font(name="Calibri", size=10, color="000000")
        thin_border = Border(
            left=Side(style="thin", color="CBD5E1"),
            right=Side(style="thin", color="CBD5E1"),
            top=Side(style="thin", color="CBD5E1"),
            bottom=Side(style="thin", color="CBD5E1"),
        )

        # ----------------------------------------------------
        # Sheet 1: PRISMA_Overview
        # ----------------------------------------------------
        ws_over = wb.create_sheet("PRISMA_Overview")
        ws_over.views.sheetView[0].showGridLines = True
        
        ws_over.cell(row=1, column=1, value="PRISMA CLINICAL TRIAL INTELLIGENCE REPORT").font = Font(name="Calibri", size=14, bold=True, color="0F172A")
        ws_over.cell(row=2, column=1, value="Synthesized evidence overview across imported RCT workbooks with atomic provenance.").font = Font(name="Calibri", size=10, italic=True)

        over_headers = ["Metric / Indicator", "Quantified Value", "Methodological Significance"]
        for c_idx, h in enumerate(over_headers, 1):
            cell = ws_over.cell(row=4, column=c_idx, value=h)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center")

        overview_data = [
            ("Imported Clinical Trial Workbooks", self.overview_metrics.get("workbooks_imported", 0), "Source Excel workbooks ingested without mutation"),
            ("Identified Randomized Trials (k)", self.overview_metrics.get("trials_count", 0), "Independent study protocols extracted"),
            ("Randomized & Analyzed Arms", self.overview_metrics.get("arms_count", 0), "Experimental, active comparator, and placebo cohorts"),
            ("Extracted Outcomes & Endpoints", self.overview_metrics.get("outcomes_count", 0), "Continuous and binary efficacy & safety endpoints"),
            ("Unique Clinical Parameters", self.overview_metrics.get("unique_parameters_count", 0), "Harmonized target biomarker and clinical variables"),
            ("Total Randomized Participants (N)", self.overview_metrics.get("total_randomized_patients", 0), "Aggregated trial population sample size"),
            ("Data Completeness Index", f"{self.overview_metrics.get('completeness_score', 0)}%", "Penalized score accounting for missing variance or sample sizes"),
            ("Scientific Validation Findings", self.overview_metrics.get("total_findings", 0), "Identified discrepancies, missing variables, or divergence warnings"),
            ("Critical Verification Warnings", self.overview_metrics.get("critical_findings", 0), "High-priority items requiring source text inspection"),
        ]

        for r_idx, (m, v, desc) in enumerate(overview_data, start=5):
            c1 = ws_over.cell(row=r_idx, column=1, value=m)
            c2 = ws_over.cell(row=r_idx, column=2, value=v)
            c3 = ws_over.cell(row=r_idx, column=3, value=desc)
            for c in [c1, c2, c3]:
                c.font = data_font
                c.border = thin_border
            c2.alignment = Alignment(horizontal="center")

        # ----------------------------------------------------
        # Sheet 2: Cross_Trial_Comparison
        # ----------------------------------------------------
        ws_comp = wb.create_sheet("Cross_Trial_Comparison")
        ws_comp.views.sheetView[0].showGridLines = True
        df_comp = self.comparator.build_side_by_side_matrix()

        for c_idx, col in enumerate(df_comp.columns, 1):
            cell = ws_comp.cell(row=1, column=c_idx, value=str(col))
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center")

        for r_idx, row in enumerate(df_comp.values, start=2):
            for c_idx, val in enumerate(row, 1):
                cell = ws_comp.cell(row=r_idx, column=c_idx, value=str(val) if val is not None else "")
                cell.font = data_font
                cell.border = thin_border

        # ----------------------------------------------------
        # Sheet 3: Outcome_Inventory_&_Readiness
        # ----------------------------------------------------
        ws_out = wb.create_sheet("Outcome_Inventory_&_Readiness")
        ws_out.views.sheetView[0].showGridLines = True
        out_list = self.explorer.list_all_outcomes()

        if out_list:
            headers = list(out_list[0].keys())
            for c_idx, h in enumerate(headers, 1):
                cell = ws_out.cell(row=1, column=c_idx, value=h)
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal="center", vertical="center")

            for r_idx, row_dict in enumerate(out_list, start=2):
                for c_idx, h in enumerate(headers, 1):
                    val = row_dict.get(h, "")
                    cell = ws_out.cell(row=r_idx, column=c_idx, value=str(val))
                    cell.font = data_font
                    cell.border = thin_border
                    if h in ["Trials (k)", "Extracted Arms (N)", "Readiness Verdict"]:
                        cell.alignment = Alignment(horizontal="center")

        # ----------------------------------------------------
        # Sheet 4: Validation_&_Data_Quality
        # ----------------------------------------------------
        ws_val = wb.create_sheet("Validation_&_Data_Quality")
        ws_val.views.sheetView[0].showGridLines = True
        val_headers = ["Issue ID", "Trial ID", "Target Entity", "Target ID", "Field Name", "Issue Type", "Severity", "Reason / Observation", "Recommended Action", "Provenance"]

        for c_idx, h in enumerate(val_headers, 1):
            cell = ws_val.cell(row=1, column=c_idx, value=h)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center")

        for r_idx, f in enumerate(self.validation_findings, start=2):
            vals = [
                f.issue_id,
                f.study_id,
                f.target_entity,
                f.target_id,
                f.field_name,
                f.issue_type,
                f.severity.upper(),
                f.reason,
                f.recommended_action,
                f.provenance.citation(),
            ]
            for c_idx, val in enumerate(vals, 1):
                cell = ws_val.cell(row=r_idx, column=c_idx, value=str(val))
                cell.font = data_font
                cell.border = thin_border
                if c_idx == 7:
                    cell.alignment = Alignment(horizontal="center")
                    if f.severity == "critical":
                        cell.font = Font(name="Calibri", size=10, bold=True, color="DC2626")
                    elif f.severity == "warning":
                        cell.font = Font(name="Calibri", size=10, bold=True, color="D97706")

        # ----------------------------------------------------
        # Sheet 5: Provenance_Audit_Trail
        # ----------------------------------------------------
        ws_prov = wb.create_sheet("Provenance_Audit_Trail")
        ws_prov.views.sheetView[0].showGridLines = True
        prov_headers = ["Trial ID", "Entity Type", "Identifier", "Parameter / Name", "Source Workbook", "Worksheet", "Cell Coordinates"]

        for c_idx, h in enumerate(prov_headers, 1):
            cell = ws_prov.cell(row=1, column=c_idx, value=h)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center")

        prov_rows = []
        for tid, t in self.trials.items():
            prov_rows.append((tid, "Study", tid, t.title[:40], t.provenance.source_file, t.provenance.sheet_name, t.provenance.cell_ref))
            for a in t.arms:
                prov_rows.append((tid, "Arm", a.arm_id, a.arm_name, a.provenance.source_file, a.provenance.sheet_name, a.provenance.cell_ref))
            for o in t.outcomes:
                prov_rows.append((tid, "Outcome", o.outcome_id, o.parameter_name, o.provenance.source_file, o.provenance.sheet_name, o.provenance.cell_ref))

        for r_idx, row in enumerate(prov_rows, start=2):
            for c_idx, val in enumerate(row, 1):
                cell = ws_prov.cell(row=r_idx, column=c_idx, value=str(val))
                cell.font = data_font
                cell.border = thin_border

        # Adjust column widths automatically across all sheets
        for ws in wb.worksheets:
            for col in ws.columns:
                max_len = 0
                col_letter = get_column_letter(col[0].column)
                for cell in col:
                    if cell.value:
                        lines = str(cell.value).split("\n")
                        max_len = max(max_len, max(len(l) for l in lines))
                ws.column_dimensions[col_letter].width = min(50, max(12, max_len + 3))

        wb.save(output_path)
        wb.close()
        return output_path

    def export_html_dossier(self, output_path: str = "outputs/PRISMA_Clinical_Intelligence_Dossier.html") -> str:
        """Exports an isolated, responsive, publication-ready PRISMA HTML dossier."""
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        df_comp = self.comparator.build_side_by_side_matrix()
        out_list = self.explorer.list_all_outcomes()
        df_out = pd.DataFrame(out_list) if out_list else pd.DataFrame()
        divs = self.comparator.detect_trial_divergences()

        comp_html = df_comp.to_html(classes="prisma-table", index=False)
        out_html = df_out.to_html(classes="prisma-table", index=False) if not df_out.empty else "<p>No outcomes.</p>"

        div_cards = ""
        for d in divs:
            div_cards += f"""
            <div class="div-card">
              <div class="div-badge">{d.get('Category', '')}</div>
              <div class="div-desc"><strong>Finding:</strong> {d.get('Divergence Description', '')}</div>
              <div class="div-interp"><strong>Methodological Impact:</strong> {d.get('Clinical Interpretation', '')}</div>
              <div class="div-action"><strong>Action:</strong> {d.get('Actionable Advice', '')}</div>
            </div>
            """

        findings_rows = ""
        for f in self.validation_findings[:30]:
            sev_class = "sev-crit" if f.severity == "critical" else ("sev-warn" if f.severity == "warning" else "sev-info")
            findings_rows += f"""
            <tr>
              <td><code>{f.issue_id}</code></td>
              <td><strong>{f.study_id}</strong></td>
              <td>{f.field_name}</td>
              <td><span class="badge {sev_class}">{f.severity.upper()}</span></td>
              <td>{f.reason}</td>
              <td><small>{f.provenance.citation()}</small></td>
            </tr>
            """

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>PRISMA Clinical Trial Intelligence Dossier</title>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background: #0B0F19;
      color: #E2E8F0;
      margin: 0;
      padding: 30px;
    }}
    .container {{
      max-width: 1400px;
      margin: 0 auto;
    }}
    .header {{
      background: linear-gradient(135deg, rgba(15, 23, 42, 0.95), rgba(30, 41, 59, 0.85));
      border: 1px solid rgba(0, 245, 212, 0.3);
      border-radius: 16px;
      padding: 24px;
      margin-bottom: 24px;
      box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }}
    .header h1 {{
      margin: 0 0 8px 0;
      color: #00F5D4;
      font-size: 26px;
      letter-spacing: -0.5px;
    }}
    .header p {{
      margin: 0;
      color: #94A3B8;
      font-size: 14px;
    }}
    .kpi-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 16px;
      margin-bottom: 24px;
    }}
    .kpi-card {{
      background: #111827;
      border: 1px solid rgba(255,255,255,0.08);
      border-radius: 12px;
      padding: 18px;
      text-align: center;
    }}
    .kpi-val {{
      font-size: 28px;
      font-weight: 800;
      color: #38BDF8;
      margin-bottom: 4px;
    }}
    .kpi-label {{
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: #94A3B8;
    }}
    .section-title {{
      font-size: 20px;
      font-weight: 700;
      color: #F8FAFC;
      margin: 32px 0 16px 0;
      display: flex;
      align-items: center;
      gap: 10px;
    }}
    .section-title::before {{
      content: "";
      width: 4px;
      height: 20px;
      background: #00F5D4;
      border-radius: 2px;
      display: inline-block;
    }}
    .prisma-table {{
      width: 100%;
      border-collapse: collapse;
      margin-bottom: 24px;
      background: #111827;
      border-radius: 10px;
      overflow: hidden;
      font-size: 13px;
    }}
    .prisma-table th {{
      background: #1E293B;
      color: #38BDF8;
      font-weight: 700;
      text-align: left;
      padding: 12px 14px;
      border-bottom: 1px solid rgba(255,255,255,0.1);
    }}
    .prisma-table td {{
      padding: 10px 14px;
      border-bottom: 1px solid rgba(255,255,255,0.05);
      color: #CBD5E1;
    }}
    .prisma-table tr:hover td {{
      background: rgba(56, 189, 248, 0.05);
    }}
    .div-card {{
      background: #131D31;
      border: 1px solid rgba(234, 179, 8, 0.3);
      border-radius: 10px;
      padding: 16px;
      margin-bottom: 14px;
    }}
    .div-badge {{
      display: inline-block;
      background: rgba(234, 179, 8, 0.15);
      color: #FACC15;
      font-size: 11px;
      font-weight: 700;
      padding: 3px 8px;
      border-radius: 6px;
      margin-bottom: 8px;
    }}
    .div-desc, .div-interp, .div-action {{
      font-size: 13px;
      margin-bottom: 6px;
      line-height: 1.4;
    }}
    .badge {{
      display: inline-block;
      padding: 2px 6px;
      border-radius: 4px;
      font-size: 10px;
      font-weight: 700;
    }}
    .sev-crit {{ background: rgba(220, 38, 38, 0.2); color: #EF4444; border: 1px solid #DC2626; }}
    .sev-warn {{ background: rgba(217, 119, 6, 0.2); color: #F59E0B; border: 1px solid #D97706; }}
    .sev-info {{ background: rgba(56, 189, 248, 0.2); color: #38BDF8; border: 1px solid #0284C7; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>MANDOROS • PRISMA Clinical Trial Intelligence Dossier</h1>
      <p>Automated Multi-Workbook Ingestion, Methodological Cross-Trial Comparison, Endpoint Inventory & Synthesis Readiness Audit</p>
    </div>

    <div class="kpi-grid">
      <div class="kpi-card">
        <div class="kpi-val">{self.overview_metrics.get('workbooks_imported', 0)}</div>
        <div class="kpi-label">Workbooks Ingested</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-val">{self.overview_metrics.get('trials_count', 0)}</div>
        <div class="kpi-label">Independent Trials</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-val">{self.overview_metrics.get('arms_count', 0)}</div>
        <div class="kpi-label">Treatment Arms</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-val">{self.overview_metrics.get('outcomes_count', 0)}</div>
        <div class="kpi-label">Extracted Outcomes</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-val" style="color: #00F5D4;">{self.overview_metrics.get('completeness_score', 0)}%</div>
        <div class="kpi-label">Completeness Index</div>
      </div>
    </div>

    <div class="section-title">Cross-Trial Side-by-Side Comparison Matrix</div>
    {comp_html}

    <div class="section-title">Cohort Methodological & Regimen Divergences</div>
    {div_cards}

    <div class="section-title">Harmonized Outcome Inventory & Synthesis Readiness</div>
    {out_html}

    <div class="section-title">Data Completeness & Quality Findings Ledger</div>
    <table class="prisma-table">
      <thead>
        <tr>
          <th>Issue ID</th>
          <th>Study ID</th>
          <th>Target Field</th>
          <th>Severity</th>
          <th>Observation & Reason</th>
          <th>Source Provenance</th>
        </tr>
      </thead>
      <tbody>
        {findings_rows if findings_rows else '<tr><td colspan="6">No validation findings.</td></tr>'}
      </tbody>
    </table>
  </div>
</body>
</html>
"""
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        return output_path
