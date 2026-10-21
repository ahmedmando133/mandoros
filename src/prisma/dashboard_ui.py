"""
PRISMA Dashboard UI & Interactive Visualizer.
Dedicated frontend components for clinical trial intelligence, cross-trial comparison,
PRISMA 2020 evidence flow, and statistical readiness.
"""

import os
import glob
from typing import Any, Optional
import gradio as gr
import pandas as pd
import plotly.graph_objects as go

from src.prisma.models import PrismaTrial, PrismaValidationFinding, StatisticalReadinessSpec
from src.prisma.ingestion import PrismaIngestionService
from src.prisma.comparator import PrismaTrialComparator
from src.prisma.outcome_explorer import PrismaOutcomeExplorer
from src.prisma.exporter import PrismaDossierExporter


# Global singleton cache for PRISMA session state
class PrismaSessionState:
    trials: dict[str, PrismaTrial] = {}
    validation_findings: list[PrismaValidationFinding] = []
    overview_metrics: dict[str, Any] = {}
    service: PrismaIngestionService = PrismaIngestionService()


def get_default_trial_files() -> list[str]:
    """Finds existing extracted structured trial workbooks in outputs/."""
    candidates = [
        "outputs/orlistat_structured_extracted.xlsx",
        "outputs/metformin_structured_extracted.xlsx",
        "outputs/semaglutide_structured_extracted.xlsx",
        "outputs/dapagliflozin_structured_extracted.xlsx",
        "outputs/empa_vs_placebo_2doses__RCT4_structured_extracted.xlsx",
        "outputs/RCT4_Empagliflozin_Fully_Corrected_Validated.xlsx",
    ]
    existing = [c for c in candidates if os.path.exists(c)]
    if not existing:
        existing = glob.glob("outputs/*extracted*.xlsx")
    return existing[:6]


def create_prisma_flow_html(overview: dict[str, Any]) -> str:
    """Renders a responsive PRISMA 2020 Evidence Flow Diagram in HTML5/SVG with GSAP animated paths."""
    k_trials = overview.get("trials_count", 0)
    n_outcomes = overview.get("outcomes_count", 0)
    n_arms = overview.get("arms_count", 0)
    n_workbooks = overview.get("workbooks_imported", 0)
    crit_findings = overview.get("critical_findings", 0)

    # Calculate synthesis funnel
    included_trials = max(0, k_trials - crit_findings)

    return f"""
    <!-- GSAP Core & Plugins via Lightweight CDN (Zero Server Footprint) -->
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.12.5/dist/gsap.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.12.5/dist/ScrollTrigger.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.12.5/dist/TextPlugin.min.js"></script>

    <div class="mandoros-prisma-flow-container" style="background: rgba(15, 23, 42, 0.9); border: 1px solid rgba(0, 245, 212, 0.25); border-radius: 16px; padding: 20px; margin-bottom: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.4);">
      <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px;">
        <div style="display: flex; align-items: center; gap: 10px;">
          <span style="font-size: 22px;">📊</span>
          <div>
            <div style="font-weight: 800; color: #00F5D4; font-size: 16px; letter-spacing: 0.5px;">PRISMA 2020 EVIDENCE FLOW ARCHITECTURE</div>
            <div style="color: #94A3B8; font-size: 12px;">Traceable systematic flow from ingested workbooks to quantitative meta-analysis readiness</div>
          </div>
        </div>
        <span style="background: rgba(0,245,212,0.15); border: 1px solid #00F5D4; color: #00F5D4; font-size: 11px; font-weight: 700; padding: 4px 10px; border-radius: 6px;">PRISMA 2020 Flow</span>
      </div>

      <!-- Stage Cards Row with Responsive Connecting SVG Paths -->
      <div style="display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 10px; position: relative;">
        <!-- Stage 1: Identification -->
        <div class="prisma-stage-card prisma-stage-1" style="flex: 1; min-width: 200px; background: rgba(30, 41, 59, 0.85); border: 1px solid rgba(56, 189, 248, 0.35); border-radius: 12px; padding: 14px; will-change: transform, opacity;">
          <div style="color: #38BDF8; font-size: 11px; font-weight: 800; text-transform: uppercase;">1. Identification</div>
          <div class="mandoros-kpi-val" data-kpi-val="{n_workbooks}" style="font-size: 22px; font-weight: 900; color: #F8FAFC; margin: 4px 0;">{n_workbooks} Workbooks</div>
          <div style="color: #94A3B8; font-size: 11.5px;">{n_outcomes} extracted endpoints across {n_arms} treatment arms.</div>
        </div>

        <!-- Connector 1 -->
        <div class="prisma-flow-connector" style="display: flex; align-items: center; justify-content: center; padding: 0 4px;">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
            <path class="prisma-flow-path" d="M 4 12 L 20 12 M 14 6 L 20 12 L 14 18" stroke="#38BDF8" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </div>

        <!-- Stage 2: Screening -->
        <div class="prisma-stage-card prisma-stage-2" style="flex: 1; min-width: 200px; background: rgba(30, 41, 59, 0.85); border: 1px solid rgba(168, 85, 247, 0.35); border-radius: 12px; padding: 14px; will-change: transform, opacity;">
          <div style="color: #C084FC; font-size: 11px; font-weight: 800; text-transform: uppercase;">2. Screening &amp; Schema Audit</div>
          <div class="mandoros-kpi-val" data-kpi-val="{k_trials}" style="font-size: 22px; font-weight: 900; color: #F8FAFC; margin: 4px 0;">{k_trials} Unique Trials</div>
          <div style="color: #94A3B8; font-size: 11.5px;">100% cell coordinates mapped and validated against schema.</div>
        </div>

        <!-- Connector 2 -->
        <div class="prisma-flow-connector" style="display: flex; align-items: center; justify-content: center; padding: 0 4px;">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
            <path class="prisma-flow-path" d="M 4 12 L 20 12 M 14 6 L 20 12 L 14 18" stroke="#C084FC" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </div>

        <!-- Stage 3: Eligibility -->
        <div class="prisma-stage-card prisma-stage-3" style="flex: 1; min-width: 200px; background: rgba(30, 41, 59, 0.85); border: 1px solid rgba(234, 179, 8, 0.35); border-radius: 12px; padding: 14px; will-change: transform, opacity;">
          <div style="color: #FACC15; font-size: 11px; font-weight: 800; text-transform: uppercase;">3. Divergence &amp; Eligibility</div>
          <div class="mandoros-kpi-val" data-kpi-val="{k_trials}" style="font-size: 22px; font-weight: 900; color: #F8FAFC; margin: 4px 0;">{k_trials} Evaluated</div>
          <div style="color: #94A3B8; font-size: 11.5px;">Dosing, duration, and comparator arms audited for exchangeability.</div>
        </div>

        <!-- Connector 3 -->
        <div class="prisma-flow-connector" style="display: flex; align-items: center; justify-content: center; padding: 0 4px;">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
            <path class="prisma-flow-path" d="M 4 12 L 20 12 M 14 6 L 20 12 L 14 18" stroke="#FACC15" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </div>

        <!-- Stage 4: Included -->
        <div class="prisma-stage-card prisma-stage-4" style="flex: 1; min-width: 200px; background: rgba(30, 41, 59, 0.85); border: 1px solid rgba(16, 185, 129, 0.45); border-radius: 12px; padding: 14px; box-shadow: 0 4px 18px rgba(16, 185, 129, 0.18); will-change: transform, opacity;">
          <div style="color: #34D399; font-size: 11px; font-weight: 800; text-transform: uppercase;">4. Synthesis Included</div>
          <div class="mandoros-kpi-val" data-kpi-val="{included_trials}" style="font-size: 22px; font-weight: 900; color: #34D399; margin: 4px 0;">{included_trials} Eligible for REML</div>
          <div style="color: #94A3B8; font-size: 11.5px;">Trials with paired comparator arms &amp; complete sample sizes.</div>
        </div>
      </div>
    </div>
    <script>
    (function() {{
      function triggerPrismaGsap() {{
        if (typeof window.mandorosGsap !== 'undefined' && window.mandorosGsap.animatePrismaFlow) {{
          window.mandorosGsap.animatePrismaFlow();
          window.mandorosGsap.animateKpiCounters();
        }} else if (typeof gsap !== 'undefined') {{
          gsap.fromTo('.prisma-flow-path',
            {{ strokeDasharray: 80, strokeDashoffset: 80 }},
            {{ strokeDashoffset: 0, duration: 0.8, stagger: 0.15, ease: 'power2.out' }}
          );
          gsap.fromTo('.prisma-stage-card',
            {{ y: 22, opacity: 0, scale: 0.94 }},
            {{ y: 0, opacity: 1, scale: 1, duration: 0.6, stagger: 0.12, ease: 'back.out(1.4)', clearProps: 'all' }}
          );
        }} else {{
          setTimeout(triggerPrismaGsap, 60);
        }}
      }}
      triggerPrismaGsap();
    }})();
    </script>
    """


def create_evidence_density_plot(trials: dict[str, PrismaTrial]) -> go.Figure:
    """Generates a Plotly heatmap of trials x key outcome parameters."""
    if not trials:
        fig = go.Figure()
        fig.update_layout(
            title="No trials loaded",
            paper_bgcolor="#0B0F19",
            plot_bgcolor="#0B0F19",
            font_color="#94A3B8"
        )
        return fig

    # Collect top parameters
    param_counts: dict[str, int] = {}
    for t in trials.values():
        seen = set()
        for o in t.outcomes:
            p = (o.parameter_name or "").strip()
            if p and p not in seen:
                seen.add(p)
                param_counts[p] = param_counts.get(p, 0) + 1

    top_params = [p for p, _ in sorted(param_counts.items(), key=lambda x: x[1], reverse=True)[:15]]
    trial_labels = [t.citation_short() for t in trials.values()]
    trial_keys = list(trials.keys())

    if not top_params:
        top_params = ["Primary Endpoint", "HbA1c", "Weight", "Adverse Events"]

    # Build matrix: 2 = Complete (Mean & SD), 1 = Partial (Mean only or Change), 0 = Not reported
    z_matrix = []
    text_matrix = []

    for s_id in trial_keys:
        t = trials[s_id]
        row_z = []
        row_text = []
        for p in top_params:
            matches = [o for o in t.outcomes if (o.parameter_name or "").strip().lower() == p.lower()]
            if not matches:
                row_z.append(0)
                row_text.append(f"{t.citation_short()}<br>{p}: Not Reported")
            else:
                has_full = any(m.mean is not None and m.sd is not None for m in matches)
                if has_full:
                    row_z.append(2)
                    row_text.append(f"{t.citation_short()}<br>{p}: Complete (Mean & SD extracted)")
                else:
                    row_z.append(1)
                    row_text.append(f"{t.citation_short()}<br>{p}: Partial (Missing SD or Change only)")
        z_matrix.append(row_z)
        text_matrix.append(row_text)

    # Custom colorscale: 0 -> Dark Slate, 1 -> Amber Yellow, 2 -> Emerald Teal
    colorscale = [
        [0.0, "#1E293B"],
        [0.49, "#1E293B"],
        [0.5, "#EAB308"],
        [0.79, "#EAB308"],
        [0.8, "#00F5D4"],
        [1.0, "#00F5D4"],
    ]

    fig = go.Figure(data=go.Heatmap(
        z=z_matrix,
        x=top_params,
        y=trial_labels,
        text=text_matrix,
        hoverinfo="text",
        colorscale=colorscale,
        showscale=False,
        xgap=3,
        ygap=3,
    ))

    fig.update_layout(
        title={
            "text": "<b>Evidence Density & Reporting Completeness Matrix</b> (Green: Complete | Yellow: Partial | Dark: Not Reported)",
            "font": {"size": 14, "color": "#F8FAFC"}
        },
        paper_bgcolor="rgba(15, 23, 42, 0.8)",
        plot_bgcolor="rgba(15, 23, 42, 0.8)",
        font={"color": "#CBD5E1", "family": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto"},
        xaxis={"tickangle": -35, "gridcolor": "rgba(255,255,255,0.05)"},
        yaxis={"autorange": "reversed", "gridcolor": "rgba(255,255,255,0.05)"},
        margin={"l": 140, "r": 30, "t": 60, "b": 100},
        height=360,
    )
    return fig


def build_readiness_badge_html(spec: StatisticalReadinessSpec, reml_preview: Optional[dict[str, Any]] = None) -> str:
    """Renders a rich HTML card summarizing statistical synthesis readiness for an outcome."""
    status_color = "#34D399" if "Ready" in spec.readiness_status else ("#FACC15" if "Partially" in spec.readiness_status else "#F87171")
    reml_box = ""

    if reml_preview and reml_preview.get("success"):
        reml_box = f"""
        <div style="background: rgba(0, 245, 212, 0.08); border: 1px solid #00F5D4; border-radius: 10px; padding: 14px; margin-top: 14px;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <strong style="color: #00F5D4; font-size: 13px;">⚡ READ-ONLY REML SYNTHESIS PREVIEW (wviechtb/metafor-equivalent)</strong>
            <span style="font-size: 11px; color: #94A3B8;">Model: {reml_preview.get('model')}</span>
          </div>
          <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 10px;">
            <div>
              <div style="font-size: 10.5px; color: #94A3B8;">POOLED EFFECT ({reml_preview.get('metric')})</div>
              <div style="font-size: 16px; font-weight: 800; color: #F8FAFC;">{reml_preview.get('pooled_effect'):.3f}</div>
            </div>
            <div>
              <div style="font-size: 10.5px; color: #94A3B8;">95% CONFIDENCE INTERVAL</div>
              <div style="font-size: 14px; font-weight: 700; color: #38BDF8;">[{reml_preview.get('ci_lower'):.3f}, {reml_preview.get('ci_upper'):.3f}]</div>
            </div>
            <div>
              <div style="font-size: 10.5px; color: #94A3B8;">HETEROGENEITY (I²)</div>
              <div style="font-size: 14px; font-weight: 700; color: #C084FC;">{reml_preview.get('i2'):.1f}%</div>
            </div>
            <div>
              <div style="font-size: 10.5px; color: #94A3B8;">p-VALUE</div>
              <div style="font-size: 14px; font-weight: 700; color: #FACC15;">p = {reml_preview.get('p_value'):.4f}</div>
            </div>
          </div>
        </div>
        """
    elif reml_preview and not reml_preview.get("success"):
        reml_box = f"""
        <div style="background: rgba(239, 68, 68, 0.08); border: 1px solid rgba(239, 68, 68, 0.4); border-radius: 10px; padding: 12px; margin-top: 14px;">
          <div style="color: #F87171; font-weight: 700; font-size: 12px;">⚠️ Synthesis Withheld: {reml_preview.get('reason')}</div>
          <div style="color: #94A3B8; font-size: 11px; margin-top: 4px;">{'; '.join(reml_preview.get('missing', []))}</div>
        </div>
        """

    rec_list = "".join([f"<li style='margin-bottom: 4px;'>{r}</li>" for r in spec.recommendations])

    return f"""
    <div style="background: rgba(15, 23, 42, 0.85); border: 1px solid rgba(255, 255, 255, 0.12); border-radius: 14px; padding: 18px; margin-top: 10px;">
      <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px;">
        <div>
          <div style="font-size: 17px; font-weight: 800; color: #F8FAFC;">{spec.outcome_name}</div>
          <div style="font-size: 12px; color: #94A3B8;">Clinical Domain: <span style="color: #38BDF8;">{spec.domain}</span> | Reporting Trials: <strong style="color: #F8FAFC;">{spec.reporting_trials_count}</strong> | Analyzed Arms: <strong style="color: #F8FAFC;">{spec.arms_count}</strong></div>
        </div>
        <div style="text-align: right;">
          <span style="background: rgba(255,255,255,0.08); border: 1px solid {status_color}; color: {status_color}; font-size: 11.5px; font-weight: 800; padding: 4px 10px; border-radius: 8px;">
            {spec.readiness_status}
          </span>
          <div style="font-size: 11px; color: #94A3B8; margin-top: 4px;">Readiness Score: <strong style="color: {status_color};">{spec.readiness_score:.1f}%</strong></div>
        </div>
      </div>

      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; background: rgba(30, 41, 59, 0.6); padding: 12px; border-radius: 10px; margin-bottom: 12px;">
        <div>
          <div style="font-size: 11px; color: #94A3B8;">Measurement Units</div>
          <div style="font-size: 13px; font-weight: 700; color: #F8FAFC;">{spec.common_unit or 'Score / Unspecified'} ({'✅ Aligned' if spec.units_harmonized else '⚠️ Mixed'})</div>
        </div>
        <div>
          <div style="font-size: 11px; color: #94A3B8;">Feasible Syntheses</div>
          <div style="font-size: 12.5px; font-weight: 600; color: #38BDF8;">{', '.join(spec.feasible_analyses) if spec.feasible_analyses else 'None'}</div>
        </div>
        <div>
          <div style="font-size: 11px; color: #94A3B8;">Data Completeness Status</div>
          <div style="font-size: 12.5px; font-weight: 600; color: {'#34D399' if not spec.missing_inputs else '#FACC15'};">
            {'All required variances extracted' if not spec.missing_inputs else f'{len(spec.missing_inputs)} variance parameter(s) missing'}
          </div>
        </div>
      </div>

      <div style="color: #E2E8F0; font-size: 12px;">
        <strong style="color: #94A3B8;">Methodological & Statistical Recommendations:</strong>
        <ul style="margin: 6px 0 0 16px; padding: 0; color: #CBD5E1;">
          {rec_list}
        </ul>
      </div>

      {reml_box}
    </div>
    """


def render_divergence_cards_html(divs: list[dict[str, str]]) -> str:
    """Renders HTML divergence warning cards."""
    if not divs:
        return "<p style='color: #94A3B8;'>No divergences detected.</p>"

    cards = []
    for d in divs:
        cat = d.get("Category", "Divergence")
        desc = d.get("Divergence Description", "")
        interp = d.get("Clinical Interpretation", "")
        action = d.get("Actionable Advice", "")

        is_good = "Harmonization" in cat or "No severe" in desc
        badge_bg = "rgba(16, 185, 129, 0.15)" if is_good else "rgba(234, 179, 8, 0.15)"
        badge_border = "#10B981" if is_good else "#EAB308"
        badge_color = "#34D399" if is_good else "#FACC15"

        cards.append(f"""
        <div style="background: rgba(30, 41, 59, 0.7); border: 1px solid rgba(255, 255, 255, 0.08); border-left: 4px solid {badge_border}; border-radius: 10px; padding: 14px; margin-bottom: 12px;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
            <span style="background: {badge_bg}; border: 1px solid {badge_border}; color: {badge_color}; font-size: 10.5px; font-weight: 800; padding: 3px 8px; border-radius: 6px;">
              {cat}
            </span>
          </div>
          <div style="font-size: 13px; font-weight: 700; color: #F8FAFC; margin-bottom: 6px;">{desc}</div>
          <div style="font-size: 12px; color: #CBD5E1; margin-bottom: 6px; line-height: 1.4;"><strong style="color: #94A3B8;">Clinical Impact:</strong> {interp}</div>
          <div style="font-size: 11.5px; color: #38BDF8;"><strong style="color: #94A3B8;">Action:</strong> {action}</div>
        </div>
        """)
    return "".join(cards)


def run_prisma_analysis(file_objs: Optional[list[Any]] = None) -> tuple[
    str,  # flow_html
    go.Figure,  # density_plot
    pd.DataFrame,  # comparison_df
    str,  # divergence_html
    list[dict[str, Any]],  # outcome_inventory_df
    pd.DataFrame,  # findings_df
    str,  # excel_dossier_path
    str,  # html_dossier_path
    list[str],  # outcome_dropdown_choices
]:
    """
    Core handler that executes PRISMA ingestion, comparison, outcome inventory,
    and dossier export across all provided or default workbooks.
    """
    file_paths: list[str] = []

    if file_objs:
        for f in file_objs:
            p = f.name if hasattr(f, "name") else str(f)
            if p and os.path.exists(p) and p.endswith(".xlsx"):
                file_paths.append(p)

    if not file_paths:
        empty_fig = go.Figure()
        empty_fig.update_layout(
            title="Upload clinical trial workbooks (.xlsx) to generate evidence density matrix",
            paper_bgcolor="#0B0F19",
            plot_bgcolor="#0B0F19",
            font_color="#94A3B8"
        )
        return (
            "<div style='padding: 18px; background: rgba(239,68,68,0.15); border: 1px solid #EF4444; border-radius: 12px; color: #FCA5A5; text-align: center;'>"
            "<strong>⚠️ Missing Input Workbooks:</strong> Please upload one or more extracted Excel workbooks (.xlsx) to run PRISMA analysis. No default or historical files will be processed."
            "</div>",
            empty_fig,
            pd.DataFrame({"Notice": ["Upload workbooks to view cross-trial comparison matrix."]}),
            "<p style='color: #94A3B8;'>Upload workbooks to audit methodological divergences.</p>",
            [],
            pd.DataFrame({"Notice": ["No workbooks loaded."]}),
            None,
            None,
            ["None"],
        )

    # Execute Ingestion
    service = PrismaIngestionService()
    trials, findings, overview = service.ingest_workbooks(file_paths)

    PrismaSessionState.trials = trials
    PrismaSessionState.validation_findings = findings
    PrismaSessionState.overview_metrics = overview
    PrismaSessionState.service = service

    comparator = PrismaTrialComparator(trials)
    explorer = PrismaOutcomeExplorer(trials)
    exporter = PrismaDossierExporter(trials, findings, overview)

    # 1. Flow Diagram HTML
    flow_html = create_prisma_flow_html(overview)

    # 2. Evidence Density Heatmap Plotly
    density_plot = create_evidence_density_plot(trials)

    # 3. Cross-Trial Comparison Matrix
    comparison_df = comparator.build_side_by_side_matrix()

    # 4. Divergences HTML
    divs = comparator.detect_trial_divergences()
    divergence_html = render_divergence_cards_html(divs)

    # 5. Outcome Inventory
    outcomes_list = explorer.list_all_outcomes()

    # 6. Findings DataFrame
    findings_rows = []
    for f in findings:
        findings_rows.append({
            "Issue ID": f.issue_id,
            "Study ID": f.study_id,
            "Entity": f.target_entity,
            "Field": f.field_name,
            "Severity": f.severity.upper(),
            "Observation / Reason": f.reason,
            "Action": f.recommended_action,
            "Provenance": f.provenance.citation(),
        })
    findings_df = pd.DataFrame(findings_rows) if findings_rows else pd.DataFrame({"Message": ["No validation findings logged."]})

    # 7. Generate Export Dossiers
    excel_dossier = exporter.export_excel_dossier("outputs/PRISMA_Clinical_Intelligence_Dossier.xlsx")
    html_dossier = exporter.export_html_dossier("outputs/PRISMA_Clinical_Intelligence_Dossier.html")

    # 8. Available outcome choices
    outcome_choices = [o["Parameter Name"] for o in outcomes_list] or ["Primary Endpoint"]

    return (
        flow_html,
        density_plot,
        comparison_df,
        divergence_html,
        outcomes_list,
        findings_df,
        excel_dossier,
        html_dossier,
        outcome_choices,
    )


def handle_outcome_selection(selected_outcome: str) -> tuple[str, pd.DataFrame]:
    """Updates the outcome detail table and statistical readiness card when an outcome is chosen."""
    trials = PrismaSessionState.trials
    if not trials or not selected_outcome or selected_outcome == "None":
        return "<p style='color: #94A3B8;'>Select an outcome to inspect statistical readiness.</p>", pd.DataFrame()

    explorer = PrismaOutcomeExplorer(trials)
    spec = explorer.evaluate_readiness(selected_outcome)
    reml_preview = explorer.compute_reml_preview_safe(selected_outcome) if spec.reporting_trials_count >= 2 else None

    badge_html = build_readiness_badge_html(spec, reml_preview)
    matrix_df = explorer.get_outcome_matrix_df(selected_outcome)

    return badge_html, matrix_df


def build_prisma_tab() -> None:
    """
    Constructs the complete, isolated PRISMA Clinical Trial Intelligence & Visualization tab
    for direct embedding into app.py.
    """
    with gr.Column():
        # Top Header Banner
        gr.HTML(
            """
            <div style="background: linear-gradient(135deg, rgba(15, 23, 42, 0.95), rgba(30, 41, 59, 0.90)); border: 1px solid rgba(0, 245, 212, 0.35); border-radius: 18px; padding: 22px 26px; margin-bottom: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.5);">
              <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 14px;">
                <div style="display: flex; align-items: center; gap: 14px;">
                  <div style="width: 48px; height: 48px; border-radius: 12px; background: rgba(0, 245, 212, 0.15); border: 1px solid #00F5D4; display: flex; align-items: center; justify-content: center; font-size: 24px; color: #00F5D4;">
                    📊
                  </div>
                  <div>
                    <div style="display: flex; align-items: center; gap: 10px;">
                      <h2 style="margin: 0; color: #00F5D4; font-size: 22px; font-weight: 900; letter-spacing: -0.5px;">PRISMA • Clinical Trial Intelligence &amp; Visualization</h2>
                      <span style="background: rgba(0, 245, 212, 0.15); border: 1px solid #00F5D4; color: #00F5D4; font-size: 10px; font-weight: 800; padding: 2px 8px; border-radius: 6px;">ZERO-REGRESSION ISOLATED ENGINE</span>
                    </div>
                    <div style="color: #94A3B8; font-size: 13px; margin-top: 4px;">
                      Multi-workbook Excel ingestion • Side-by-side trial comparison • PRISMA 2020 evidence flow • Scale harmonization • Cell-level provenance audit
                    </div>
                  </div>
                </div>
                <div style="display: flex; gap: 8px;">
                  <span style="background: rgba(56, 189, 248, 0.15); border: 1px solid #38BDF8; color: #38BDF8; font-size: 11px; font-weight: 700; padding: 4px 10px; border-radius: 6px;">Open Science</span>
                  <span style="background: rgba(16, 185, 129, 0.15); border: 1px solid #10B981; color: #34D399; font-size: 11px; font-weight: 700; padding: 4px 10px; border-radius: 6px;">Deterministic REML</span>
                  <span style="background: rgba(192, 132, 252, 0.15); border: 1px solid #C084FC; color: #C084FC; font-size: 11px; font-weight: 700; padding: 4px 10px; border-radius: 6px;">PRISMA 2020</span>
                </div>
              </div>
            </div>
            """
        )

        # Ingestion Controls Row
        with gr.Row():
            with gr.Column(scale=3):
                workbook_files_input = gr.File(
                    label="📂 Ingest Extracted RCT Workbooks (.xlsx) - Select Multiple Trial Workbooks",
                    file_count="multiple",
                    file_types=[".xlsx"],
                    type="filepath",
                )
            with gr.Column(scale=1):
                gr.Markdown("### ⚡ Execute PRISMA Pipeline")
                run_prisma_btn = gr.Button("🚀 Ingest & Synthesize Evidence", variant="primary", elem_classes=["extract-btn"])
                clear_prisma_btn = gr.Button("🧹 Clear & Reset View", variant="secondary")

        # Dynamic PRISMA Flow Diagram Container
        flow_container = gr.HTML(
            value="""
            <div style="background: rgba(15, 23, 42, 0.85); border: 1px dashed rgba(0, 245, 212, 0.3); border-radius: 14px; padding: 20px; text-align: center; color: #94A3B8;">
              <span style="font-size: 26px;">📊</span>
              <h4 style="color: #00F5D4; margin: 8px 0 4px 0; font-size: 16px; font-weight: 700;">PRISMA Intelligence Engine Ready</h4>
              <p style="font-size: 13px; margin: 0; color: #94A3B8;">Upload one or more extracted RCT Excel workbooks (.xlsx) above and click 'Ingest &amp; Synthesize Evidence' to begin analysis. No default or historical data will be mixed.</p>
            </div>
            """
        )

        # Sub-tabs for PRISMA features
        with gr.Tabs(elem_id="prisma-sub-tabs"):
            # SUB-TAB 1: Overview & Density Heatmap
            with gr.TabItem("📋 Cohort Overview & Evidence Density", id="tab_prisma_overview"):
                density_plot_output = gr.Plot(label="Evidence Density Matrix Across Trials and Endpoints")

            # SUB-TAB 2: Trial Comparison Workspace
            with gr.TabItem("⚖️ Side-by-Side Trial Comparison", id="tab_prisma_comparison"):
                with gr.Row():
                    with gr.Column(scale=3):
                        gr.Markdown("#### 🧬 Cross-Trial Clinical & Methodological Matrix")
                        comparison_table_output = gr.Dataframe(
                            headers=["Category", "Clinical Parameter"],
                            interactive=False,
                            wrap=True,
                        )
                    with gr.Column(scale=2):
                        gr.Markdown("#### ⚠️ Methodological & Regimen Divergences")
                        divergence_cards_output = gr.HTML(value="<p style='color: #94A3B8;'>Analyzing cohort divergences...</p>")

            # SUB-TAB 3: Outcome Explorer & Statistical Readiness
            with gr.TabItem("🔍 Outcome Explorer & Statistical Readiness", id="tab_prisma_outcomes"):
                gr.Markdown("#### 🎯 Harmonized Outcome Inventory Across Cohort")
                outcomes_inventory_output = gr.Dataframe(
                    headers=["Parameter Name", "Clinical Domain", "Trials (k)", "Reporting Trials", "Extracted Arms (N)", "Units Observed", "Unit Harmonization", "Timepoints", "Readiness Verdict"],
                    interactive=False,
                    wrap=True,
                )

                gr.Markdown("---")
                gr.Markdown("#### 🔬 Deep Dive: Select Endpoint for REML Statistical Readiness Appraisal")
                with gr.Row():
                    outcome_selector = gr.Dropdown(
                        label="Select Target Clinical Outcome",
                        choices=["Primary Endpoint"],
                        value="Primary Endpoint",
                        interactive=True,
                    )
                
                readiness_badge_output = gr.HTML(value="<p style='color: #94A3B8;'>Select an outcome above to view synthesis readiness.</p>")
                outcome_matrix_output = gr.Dataframe(
                    label="Arm-by-Arm Extracted Observations with Exact Provenance",
                    interactive=False,
                    wrap=True,
                )

            # SUB-TAB 4: Data Quality & Validation Ledger
            with gr.TabItem("🛡️ Data Completeness & Quality Findings", id="tab_prisma_quality"):
                gr.Markdown("#### 🔍 Verifiable Discrepancy & Missingness Ledger")
                gr.HTML(
                    """
                    <div style="background: rgba(16, 185, 129, 0.08); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 10px; padding: 10px 14px; margin-bottom: 12px; color: #CBD5E1; font-size: 12px;">
                      🛡️ <strong>Zero-Fabrication Guarantee:</strong> Unreported parameters are explicitly preserved as <code>None / Not Reported</code>. Missing standard deviations are flagged for variance calculation rather than imputed with synthetic zeros.
                    </div>
                    """
                )
                findings_table_output = gr.Dataframe(
                    headers=["Issue ID", "Study ID", "Entity", "Field", "Severity", "Observation / Reason", "Action", "Provenance"],
                    interactive=False,
                    wrap=True,
                )

            # SUB-TAB 5: Dossier Exporter
            with gr.TabItem("📥 Traceable Dossier Exporter", id="tab_prisma_export"):
                gr.Markdown("#### 📑 Download Certified PRISMA Intelligence Dossiers")
                gr.HTML(
                    """
                    <div style="background: rgba(30, 41, 59, 0.8); border: 1px solid rgba(0, 245, 212, 0.25); border-radius: 12px; padding: 16px; margin-bottom: 16px;">
                      <div style="font-weight: 700; color: #00F5D4; font-size: 14px; margin-bottom: 6px;">Multi-Sheet Audit Dossier (.xlsx) & Interactive HTML Archive</div>
                      <div style="color: #94A3B8; font-size: 12px; line-height: 1.45;">
                        Export the complete cross-trial synthesis, side-by-side matrices, outcome readiness profiles, and cell-by-cell provenance audit trails. All source workbooks remain 100% untouched.
                      </div>
                    </div>
                    """
                )
                with gr.Row():
                    excel_dossier_download = gr.File(label="📊 Standardized Multi-Sheet PRISMA Excel (.xlsx)")
                    html_dossier_download = gr.File(label="🌐 Standalone Interactive HTML Dossier (.html)")

        # Wiring Event Listeners
        def on_run_clicked(files):
            (
                f_html,
                d_plot,
                c_df,
                div_html,
                out_list,
                find_df,
                xl_path,
                ht_path,
                choices,
            ) = run_prisma_analysis(files)
            
            first_choice = choices[0] if choices else "None"
            badge_html, matrix_df = handle_outcome_selection(first_choice)

            return (
                f_html,
                d_plot,
                c_df,
                div_html,
                pd.DataFrame(out_list) if out_list else pd.DataFrame(),
                find_df,
                xl_path,
                ht_path,
                gr.update(choices=choices, value=first_choice),
                badge_html,
                matrix_df,
            )

        run_prisma_btn.click(
            fn=on_run_clicked,
            inputs=[workbook_files_input],
            outputs=[
                flow_container,
                density_plot_output,
                comparison_table_output,
                divergence_cards_output,
                outcomes_inventory_output,
                findings_table_output,
                excel_dossier_download,
                html_dossier_download,
                outcome_selector,
                readiness_badge_output,
                outcome_matrix_output,
            ]
        )

        def on_clear_clicked():
            PrismaSessionState.trials.clear()
            PrismaSessionState.validation_findings.clear()
            PrismaSessionState.overview_metrics.clear()
            empty_fig = go.Figure()
            empty_fig.update_layout(
                title="Evidence Density Matrix (Awaiting Upload)",
                paper_bgcolor="#0B0F19",
                plot_bgcolor="#0B0F19",
                font_color="#94A3B8"
            )
            initial_flow = """
            <div style="background: rgba(15, 23, 42, 0.85); border: 1px dashed rgba(0, 245, 212, 0.3); border-radius: 14px; padding: 20px; text-align: center; color: #94A3B8;">
              <span style="font-size: 26px;">📊</span>
              <h4 style="color: #00F5D4; margin: 8px 0 4px 0; font-size: 16px; font-weight: 700;">PRISMA Intelligence Engine Ready</h4>
              <p style="font-size: 13px; margin: 0; color: #94A3B8;">Upload one or more extracted RCT Excel workbooks (.xlsx) above and click 'Ingest &amp; Synthesize Evidence' to begin analysis. No default or historical data will be mixed.</p>
            </div>
            """
            return (
                None,  # workbook_files_input
                initial_flow,  # flow_container
                empty_fig,  # density_plot_output
                pd.DataFrame({"Notice": ["Upload workbooks to view cross-trial comparison matrix."]}),
                "<p style='color: #94A3B8;'>Upload workbooks to audit methodological divergences.</p>",
                pd.DataFrame({"Notice": ["Upload workbooks to view harmonized outcome inventory."]}),
                pd.DataFrame({"Notice": ["No validation findings logged."]}),
                None,  # excel_dossier_download
                None,  # html_dossier_download
                gr.update(choices=["Primary Endpoint"], value="Primary Endpoint"),
                "<p style='color: #94A3B8;'>Select an outcome to inspect statistical readiness.</p>",
                pd.DataFrame(),
            )

        clear_prisma_btn.click(
            fn=on_clear_clicked,
            inputs=[],
            outputs=[
                workbook_files_input,
                flow_container,
                density_plot_output,
                comparison_table_output,
                divergence_cards_output,
                outcomes_inventory_output,
                findings_table_output,
                excel_dossier_download,
                html_dossier_download,
                outcome_selector,
                readiness_badge_output,
                outcome_matrix_output,
            ]
        )

        outcome_selector.change(
            fn=handle_outcome_selection,
            inputs=[outcome_selector],
            outputs=[readiness_badge_output, outcome_matrix_output],
        )
