"""
Phase 3 UI Components for MANDOROS: Research Gap & Thesis Navigator.
Provides high-density clinical dashboard components including:
- Interactive Plotly Evidence & Gap Map (Campbell/EviAtlas standard)
- Cochrane RoB 2.0 traffic-light and summary visualizations
- 4-Type Gap Taxonomy with cell coordinates and quotes
- Live 3-Color Traffic-Light Reality Check (PubMed, ClinicalTrials.gov, OpenAlex)
- Biostatistical sensitivity matrix & protocol risk audit (0-100 score)
- GRADE Summary of Findings (SoF) & academic blueprints (PROSPERO & SPIRIT 2013)
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, Tuple
import gradio as gr
import pandas as pd

from phase3_navigator.schema_ingestor import SchemaIngestor, IngestedTrialData
from phase3_navigator.gap_taxonomy_extractor import GapTaxonomyExtractor, ScientificGap
from phase3_navigator.global_reality_checker import GlobalRealityChecker, RealityCheckVerdict
from phase3_navigator.egm_robvis_plotter import EGMRobvisPlotter
from phase3_navigator.sample_size_and_risk import (
    SampleSizeAndRiskEngine,
    SampleSizeResult,
    SampleSizeSensitivityTable,
    ProtocolRiskReport,
)
from phase3_navigator.thesis_protocol_builder import ThesisProtocolBuilder, ThesisBlueprint
from phase3_navigator.excel_html_exporter import Phase3DossierExporter


def render_reality_check_cards_html(verdicts: List[RealityCheckVerdict]) -> str:
    """Renders sleek HTML cards for real-time external reality check matches."""
    if not verdicts:
        return "<p style='color: #94A3B8;'>No external reality check queries executed yet.</p>"

    cards = []
    for v in verdicts:
        badge_style = "background: rgba(16,185,129,0.15); border: 1px solid #10B981; color: #34D399;" if v.traffic_light_color.value == "GREEN" else (
            "background: rgba(245,158,11,0.15); border: 1px solid #F59E0B; color: #FBBF24;" if v.traffic_light_color.value == "YELLOW" else
            "background: rgba(239,68,68,0.15); border: 1px solid #EF4444; color: #F87171;"
        )

        pubmed_links = []
        for art in v.pubmed_articles[:3]:
            pubmed_links.append(f"""
            <div style='background: rgba(15,23,42,0.6); border: 1px solid #334155; border-radius: 6px; padding: 6px 10px; margin-top: 4px;'>
              <a href='{art.get("url", "#")}' target='_blank' style='color: #38BDF8; font-size: 12px; font-weight: 600; text-decoration: none;'>PMID {art.get("pmid")}: {art.get("title", "")[:70]}...</a>
            </div>
            """)

        ctgov_links = []
        for st in v.ctgov_studies[:3]:
            ctgov_links.append(f"""
            <div style='background: rgba(15,23,42,0.6); border: 1px solid #334155; border-radius: 6px; padding: 6px 10px; margin-top: 4px;'>
              <div style='display: flex; justify-content: space-between;'>
                <a href='{st.get("url", "#")}' target='_blank' style='color: #A855F7; font-size: 12px; font-weight: 700; text-decoration: none;'>{st.get("nct_id")}</a>
                <span style='color: #F59E0B; font-size: 11px;'>{st.get("overall_status")}</span>
              </div>
              <div style='color: #CBD5E1; font-size: 11px; margin-top: 2px;'>{st.get("title", "")[:70]}...</div>
            </div>
            """)

        pubmed_block = "".join(pubmed_links) if pubmed_links else "<div style='font-size:11px; color:#64748B;'>No published RCTs found</div>"
        ctgov_block = "".join(ctgov_links) if ctgov_links else "<div style='font-size:11px; color:#64748B;'>No registered trials found</div>"

        cards.append(f"""
        <div style='background: rgba(15,23,42,0.85); border: 1px solid #334155; border-radius: 12px; padding: 16px; margin-bottom: 12px;'>
          <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;'>
            <strong style='color: #F8FAFC; font-size: 14px;'>Target: {v.gap_id}</strong>
            <span style='{badge_style} padding: 3px 10px; border-radius: 9999px; font-size: 11px; font-weight: 800;'>
              {v.traffic_light_color.value}: {v.badge_label}
            </span>
          </div>
          <div style='font-size: 12px; color: #94A3B8; margin-bottom: 8px;'>
            PubMed RCTs: <strong style='color:#F1F5F9;'>{v.pubmed_rct_count}</strong> |
            ClinicalTrials.gov: <strong style='color:#F1F5F9;'>{v.ctgov_total_count}</strong> (Ongoing: {v.ctgov_ongoing_count}) |
            OpenAlex: <strong style='color:#F1F5F9;'>{v.openalex_count}</strong>
          </div>
          <div style='background: rgba(30,41,59,0.7); border-radius: 8px; padding: 8px 12px; font-size: 12px; color: #E2E8F0; margin-bottom: 8px;'>
            <strong>Actionable Resolution:</strong> {v.actionable_recommendation}
          </div>
          <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 8px;'>
            <div>
              <span style='font-size: 11px; color: #94A3B8; text-transform: uppercase;'>📚 PubMed Evidence</span>
              {pubmed_block}
            </div>
            <div>
              <span style='font-size: 11px; color: #94A3B8; text-transform: uppercase;'>🏛️ ClinicalTrials.gov Studies</span>
              {ctgov_block}
            </div>
          </div>
        </div>
        """)

    return "".join(cards)


def run_phase3_pipeline(
    uploaded_files: Optional[List[Any]],
    selected_gap_choice: str,
    design_choice: str,
    alpha: float,
    power: float,
    attrition: float,
    mean_diff: float,
    pooled_sd: float,
    p1_rate: float,
    p2_rate: float,
    ni_margin: float,
    skip_network: bool = False,
) -> Tuple[
    str,            # status_html
    Any,            # egm_plot (Plotly Figure)
    Any,            # rob_plot (Plotly Figure)
    pd.DataFrame,   # gaps_df
    str,            # reality_check_html
    pd.DataFrame,   # sensitivity_df
    str,            # protocol_risk_html
    pd.DataFrame,   # grade_df
    str,            # blueprint_html
    Optional[str],  # excel_file_path
    Optional[str],  # html_dossier_path
]:
    """
    Core executor running the complete Phase 3 pipeline on user-uploaded files.
    Strictly forbids demo/benchmark fallbacks when no files are uploaded.
    """
    if not uploaded_files:
        err_msg = (
            "<div style='padding: 18px; background: rgba(239,68,68,0.15); border: 1.5px solid #EF4444; border-radius: 12px; color: #FCA5A5; text-align: center;'>"
            "<h4 style='margin:0 0 4px 0; color:#EF4444; font-size:15px;'>⚠️ Missing Uploaded Trial Files</h4>"
            "Please upload one or more RCT PDFs or Phase 1 Excel workbooks (.xlsx). "
            "MANDOROS enforces strict evidence isolation: no synthetic benchmark data will ever be processed."
            "</div>"
        )
        empty_df = pd.DataFrame({"Status": ["Awaiting uploaded trial files..."]})
        return (
            err_msg,
            None,
            None,
            empty_df,
            "<p style='color: #94A3B8;'>Awaiting file upload.</p>",
            empty_df,
            "<p style='color: #94A3B8;'>Awaiting file upload.</p>",
            empty_df,
            "<p style='color: #94A3B8;'>Awaiting file upload.</p>",
            None,
            None
        )

    # 1. Ingest files dynamically
    trial_data = SchemaIngestor.ingest_files(uploaded_files)
    if not trial_data:
        return (
            "<div style='color:#EF4444; padding:12px;'>⚠️ Please upload an RCT PDF or Phase 1 Excel workbook first.</div>",
            go.Figure(), go.Figure(), pd.DataFrame(), "<p>No files uploaded.</p>",
            pd.DataFrame(), "<p>No data</p>", pd.DataFrame(), "<p>No blueprint</p>",
            None, None
        )

    # 2. Extract gaps into 4-Type Taxonomy
    gaps = GapTaxonomyExtractor.extract_gaps(trial_data)

    # 3. Execute live parallel reality check across PubMed, ClinicalTrials.gov, and OpenAlex (<3 seconds)
    verdicts = GlobalRealityChecker.verify_all_gaps_parallel(
        gaps=gaps,
        condition=trial_data.condition,
        drug_name=trial_data.drug_name,
        skip_network=skip_network
    )

    # 4. Generate Plotly Figures: EGM Bubble Map and Cochrane robvis
    egm_fig = EGMRobvisPlotter.build_egm_bubble_matrix(gaps, trial_data)
    rob_fig = EGMRobvisPlotter.build_rob2_traffic_light_plot(trial_data)

    # 5. Calculate Sample Size & Sensitivity Matrix
    if "Binary" in str(design_choice):
        base_sample = SampleSizeAndRiskEngine.calculate_binary_superiority(
            p_treatment=float(p1_rate or 0.45),
            p_control=float(p2_rate or 0.25),
            alpha=float(alpha or 0.05),
            power=float(power or 0.80),
            attrition_rate=float(attrition or 0.15),
        )
    else:
        base_sample = SampleSizeAndRiskEngine.calculate_continuous_superiority(
            delta=float(mean_diff or 5.0),
            sigma=float(pooled_sd or 10.0),
            alpha=float(alpha or 0.05),
            power=float(power or 0.80),
            attrition_rate=float(attrition or 0.15),
        )

    sensitivity_matrix = SampleSizeAndRiskEngine.build_sensitivity_matrix(
        base_result=base_sample,
        delta=float(mean_diff or 5.0),
        sigma=float(pooled_sd or 10.0),
        attrition_rate=float(attrition or 0.15),
    )

    # 6. Audit Protocol Risk (Wood & McNair 2023)
    risk_report = SampleSizeAndRiskEngine.audit_protocol_risk(trial_data)

    # 7. Select Target Gap for Blueprint
    target_gap = gaps[0] if gaps else None
    if selected_gap_choice:
        for g in gaps:
            if g.gap_id in selected_gap_choice or g.title[:20].lower() in selected_gap_choice.lower():
                target_gap = g
                break

    # 8. Build Academic Blueprint, GRADE Table, and Search Strategies
    blueprint = ThesisProtocolBuilder.build_blueprint(target_gap or gaps[0], trial_data) if gaps else None

    # 9. Export 6-Sheet Excel Workbook and Standalone HTML Dossier
    output_dir = "outputs"
    os.makedirs(output_dir, exist_ok=True)
    drug_clean = (trial_data.drug_name or "Trial").replace(" ", "_")[:25]
    excel_path = os.path.join(output_dir, f"MANDOROS_Phase3_{drug_clean}_Gap_Matrix.xlsx")
    html_path = os.path.join(output_dir, f"MANDOROS_Phase3_{drug_clean}_Thesis_Dossier.html")

    Phase3DossierExporter.export_excel(
        output_path=excel_path,
        gaps=gaps,
        sensitivity_table=sensitivity_matrix,
        risk_report=risk_report,
        blueprint=blueprint,
        trial_data=trial_data,
    )

    Phase3DossierExporter.export_html_dossier(
        output_path=html_path,
        gaps=gaps,
        sensitivity_table=sensitivity_matrix,
        risk_report=risk_report,
        blueprint=blueprint,
        trial_data=trial_data,
    )

    # Build UI Summaries
    from dashboard_engine.shared_ui_components import build_instant_download_banner
    download_banner = build_instant_download_banner(html_path, excel_path, phase_label="Phase 3 Gap & Thesis")

    status_html = f"""
    {download_banner}
    <div style="background: rgba(15,23,42,0.85); border: 1.5px solid #10B981; border-radius: 14px; padding: 18px 24px; margin-bottom: 16px; box-shadow: 0 10px 25px rgba(0,0,0,0.5);">
      <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
        <div>
          <h3 style="margin: 0; color: #F8FAFC; font-size: 18px; font-weight: 800;">🧭 Phase 3 Research Gap &amp; Thesis Navigator Active</h3>
          <p style="margin: 2px 0 0 0; color: #94A3B8; font-size: 13px;">Synthesized from <strong>{len(uploaded_files)} uploaded file(s)</strong> | Target: <strong>{trial_data.drug_name}</strong> in <strong>{trial_data.condition}</strong> (Pooled N={trial_data.total_sample_size})</p>
        </div>
        <div style="display: flex; gap: 8px;">
          <span style="background: rgba(16,185,129,0.15); border: 1px solid #10B981; color: #34D399; padding: 4px 12px; border-radius: 9999px; font-size: 12px; font-weight: 800;">
            📍 {len(gaps)} Gaps Classified
          </span>
          <span style="background: rgba(56,189,248,0.15); border: 1px solid #38BDF8; color: #38BDF8; padding: 4px 12px; border-radius: 9999px; font-size: 12px; font-weight: 800;">
            🛡️ Informative Score: {risk_report.total_score:.1f}/100
          </span>
        </div>
      </div>
    </div>
    """

    # Gaps DataFrame
    gap_rows = []
    for g in gaps:
        gap_rows.append({
            "Gap ID": g.gap_id,
            "Taxonomy": g.badge_label,
            "Title & Target": g.title,
            "Source Provenance": f"{g.source_sheet} [{g.row_coord}]",
            "Extracted Quote / Evidence": g.exact_extracted_value_or_quote,
            "Reality Verdict": f"{g.traffic_light_color}: {g.status_label}",
            "PubMed RCTs": g.pubmed_rct_count,
            "CT.gov Total": g.ctgov_total_count,
            "Resolution": g.actionable_recommendation[:80] + "..." if len(g.actionable_recommendation) > 80 else g.actionable_recommendation,
        })
    gaps_df = pd.DataFrame(gap_rows) if gap_rows else pd.DataFrame()

    # Reality check HTML
    reality_check_html = render_reality_check_cards_html(verdicts)

    # Sensitivity DataFrame
    sensitivity_df = sensitivity_matrix.dataframe if sensitivity_matrix and sensitivity_matrix.dataframe is not None else pd.DataFrame()

    # Protocol risk HTML
    risk_html = f"""
    <div style='background: rgba(15,23,42,0.85); border: 1px solid #334155; border-radius: 12px; padding: 18px; margin-bottom: 12px;'>
      <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;'>
        <h4 style='margin:0; color:#F8FAFC; font-size:16px;'>🛡️ Uninformative Clinical Trial Risk Audit (Wood &amp; McNair 2023)</h4>
        <span style='background: rgba(16,185,129,0.15); border: 1px solid {risk_report.risk_badge_color}; color: {risk_report.risk_badge_color}; padding: 4px 12px; border-radius: 9999px; font-weight: 800; font-size: 12px;'>
          {risk_report.total_score:.1f}/100 ({risk_report.risk_category})
        </span>
      </div>
      <p style='color: #CBD5E1; font-size: 13px; margin-bottom: 16px;'>{risk_report.executive_summary}</p>
    </div>
    """

    # GRADE DataFrame
    grade_df = blueprint.grade_table.to_dataframe() if blueprint and blueprint.grade_table else pd.DataFrame()

    # Blueprint HTML
    bp_html = f"""
    <div style='background: rgba(15,23,42,0.85); border: 1px solid #334155; border-radius: 12px; padding: 20px; color: #E2E8F0;'>
      <h3 style='color: #38BDF8; margin: 0 0 12px 0; font-size: 17px;'>🎓 Proposed Academic Thesis Titles</h3>
      <ol style='margin: 0 0 16px 20px; padding: 0;'>
        {"".join([f"<li style='margin-bottom:6px; font-weight:600; color:#F1F5F9;'>{t}</li>" for t in blueprint.proposed_academic_titles])}
      </ol>

      <h4 style='color: #F8FAFC; margin: 16px 0 8px 0; font-size: 15px;'>🔎 Reproducible PubMed Boolean Search Query</h4>
      <div style='background: #020617; border: 1px solid #1E293B; padding: 12px 16px; border-radius: 8px; font-family: monospace; font-size: 12px; color: #38BDF8; word-break: break-all;'>
        {blueprint.pubmed_boolean_query}
      </div>

      <h4 style='color: #F8FAFC; margin: 16px 0 8px 0; font-size: 15px;'>🏛️ PROSPERO Systematic Review Protocol Synopsis (Key Items)</h4>
      <div style='background: rgba(30,41,59,0.7); border-radius: 8px; padding: 12px 16px; font-size: 12.5px; line-height: 1.6;'>
        <div><strong>Field 7 (Review Question):</strong> {blueprint.prospero_protocol_draft.get("7. Review Question", "")}</div>
        <div style='margin-top:4px;'><strong>Field 13 (Included Studies):</strong> {blueprint.prospero_protocol_draft.get("13. Types of Study to be Included", "")}</div>
        <div style='margin-top:4px;'><strong>Field 19 (Synthesis Strategy):</strong> {blueprint.prospero_protocol_draft.get("19. Strategy for Data Synthesis", "")}</div>
      </div>
    </div>
    """ if blueprint else "<p>Blueprint generation complete.</p>"

    return (
        status_html,
        egm_fig,
        rob_fig,
        gaps_df,
        reality_check_html,
        sensitivity_df,
        risk_html,
        grade_df,
        bp_html,
        excel_path,
        html_path,
    )
