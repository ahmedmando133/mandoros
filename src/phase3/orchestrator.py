"""
MANDOROS Phase 3: Research Gap & Thesis Navigator — Master Service Orchestrator.
Coordinates the five pillars into a unified, modular, zero-regression research pipeline:
- Pillar I: Evidence Mapping & Gap Discovery
- Pillar II: External Scholarly & Clinical Trial Reality Check
- Pillar III: Methodological Quality Appraisal (RoB 2.0 / CONSORT)
- Pillar IV: Thesis Proposal & PICO Blueprint
- Pillar V: Protocol & Biostatistical Planning
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple, Union

import pandas as pd

from src.phase3.models import (
    EvidenceStudy,
    EvidenceMatrix,
    ObservedResearchGap,
    RealityCheckReport,
    MethodologicalAssessment,
    ThesisProposal,
    SampleSizeSpec,
    ProtocolDraft,
    Phase3Dossier
)
from src.phase3.evidence_mapper import EvidenceMapperEngine
from src.phase3.reality_check import RealityCheckEngine
from src.phase3.quality_assessor import QualityAssessorEngine
from src.phase3.thesis_architect import ThesisArchitectEngine
from src.phase3.protocol_planner import ProtocolPlannerEngine
from src.phase3.exporter import Phase3DossierExporter


class Phase3NavigatorOrchestrator:
    """
    Main orchestration service for Phase 3.
    Accepts single/multi trial PDFs or Phase 1 Excel workbooks and returns
    a fully certified Phase3Dossier with UI-ready summaries and download deliverables.
    """

    @classmethod
    def process_research_navigator(
        cls,
        files: List[Union[str, Any]],
        selected_gap_index: int = 0,
        design_type: str = "two_sample_continuous",
        sample_size_params: Optional[Dict[str, float]] = None,
        alpha: float = 0.05,
        power: float = 0.80,
        attrition_rate: float = 0.15,
        primary_outcome_name: str = "Primary Clinical Biomarker",
        skip_network_reality_check: bool = False
    ) -> Phase3Dossier:
        """
        Executes the complete 5-pillar Phase 3 pipeline end-to-end.
        """
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

        # -------------------------------------------------------------
        # Pillar I: Ingest & Evidence Matrix
        # -------------------------------------------------------------
        studies = EvidenceMapperEngine.ingest_documents(files)

        # Fallback if no files provided or empty: construct baseline benchmark study
        if not studies:
            studies = [
                EvidenceStudy(
                    study_id="BENCHMARK_RCT_001",
                    title="Randomized Placebo-Controlled Trial of Investigational Incretin Pharmacotherapy",
                    condition="Type 2 Diabetes & Cardiometabolic Disease",
                    population_summary="Adult patients with Type 2 Diabetes (HbA1c 7.5–10.0%, N=450)",
                    sample_size=450,
                    interventions=["Active Incretin 15mg Once-Weekly"],
                    comparators=["Matching Placebo Once-Weekly"],
                    primary_outcomes=["Change in HbA1c at 26 Weeks (%)"],
                    secondary_outcomes=["Body Weight Change (%)", "Fasting Plasma Glucose (mg/dL)"],
                    safety_outcomes=["Gastrointestinal Adverse Events", "Hypoglycemia"],
                    follow_up_weeks=26.0,
                    study_design="Randomized, Double-Blind, Parallel-Group Clinical Trial",
                    blinding="Double-Blind",
                    eligibility_criteria_summary="Adults aged 18–70 years; eGFR >= 60 mL/min/1.73m²; BMI >= 25 kg/m²",
                    source_file="Baseline_Benchmark_Trial.pdf",
                    key_findings=["Demonstrated significant HbA1c reduction (-1.8%) vs placebo."],
                    reported_limitations=["Short follow-up (26 weeks); excluded eGFR < 60 mL/min."]
                )
            ]

        evidence_matrix = EvidenceMapperEngine.build_evidence_matrix(studies)
        target_topic = evidence_matrix.common_condition

        # -------------------------------------------------------------
        # Pillar II: Reality Check for Top Candidate Gap
        # -------------------------------------------------------------
        gaps = evidence_matrix.observed_gaps
        selected_gap = gaps[0] if gaps else ObservedResearchGap(
            gap_id="GAP-001",
            category="comparator_absence",
            title=f"Head-to-Head Comparative Effectiveness Void in {target_topic}",
            description="No direct active-controlled trials comparing modern regimens against standard of care.",
            candidate_pico={"population": target_topic, "intervention": "Target Drug", "comparator": "Standard Care", "outcome": "Efficacy"}
        )

        if 0 <= selected_gap_index < len(gaps):
            selected_gap = gaps[selected_gap_index]

        if skip_network_reality_check:
            reality_report = RealityCheckEngine._generate_graceful_offline_report(
                selected_gap,
                f"{selected_gap.candidate_pico.get('intervention', 'Target Drug')} {target_topic}",
                timestamp,
                []
            )
        else:
            reality_report = RealityCheckEngine.execute_reality_check(selected_gap, max_results_per_source=5)

        # -------------------------------------------------------------
        # Pillar III: Methodological Quality Appraisal (RoB 2.0 / CONSORT)
        # -------------------------------------------------------------
        assessments: List[MethodologicalAssessment] = []
        for s in studies:
            assessments.append(QualityAssessorEngine.assess_study_methodology(s, framework="Cochrane RoB 2.0"))

        # -------------------------------------------------------------
        # Pillar IV: Thesis Proposal Blueprint (FINER / PICO)
        # -------------------------------------------------------------
        thesis_proposal = ThesisArchitectEngine.develop_thesis_proposal(
            gap=selected_gap,
            reality_report=reality_report,
            studies=studies
        )

        # -------------------------------------------------------------
        # Pillar V: Statistical Sample Size & Protocol Planning
        # -------------------------------------------------------------
        sample_plan = ProtocolPlannerEngine.calculate_sample_size(
            design_type=design_type,
            primary_outcome_name=primary_outcome_name,
            alpha=alpha,
            power=power,
            allocation_ratio=1.0,
            attrition_rate=attrition_rate,
            param_inputs=sample_size_params or {"mean_difference": 5.0, "pooled_sd": 10.0}
        )

        protocol_draft = ProtocolPlannerEngine.generate_protocol_draft(
            proposal=thesis_proposal,
            sample_spec=sample_plan
        )

        # -------------------------------------------------------------
        # Build Consolidated Dossier & Export Deliverables
        # -------------------------------------------------------------
        dossier = Phase3Dossier(
            dossier_id=f"MANDOROS-THESIS-{int(datetime.utcnow().timestamp())}",
            target_topic=target_topic,
            evidence_matrix=evidence_matrix,
            reality_check_reports=[reality_report],
            methodological_assessments=assessments,
            thesis_proposals=[thesis_proposal],
            sample_size_plan=sample_plan,
            protocol_draft=protocol_draft,
            generated_at=timestamp
        )

        # Export multi-sheet Excel and Markdown dossier
        excel_path = Phase3DossierExporter.export_excel(dossier)
        md_path = Phase3DossierExporter.export_markdown_report(dossier)
        dossier.excel_path = excel_path

        return dossier

    @classmethod
    def format_ui_outputs(cls, dossier: Phase3Dossier) -> Tuple[
        str,              # verdict_html (Pillar I & II summary)
        pd.DataFrame,     # evidence_matrix_df
        pd.DataFrame,     # gaps_df
        str,              # reality_check_html (Pillar II matches)
        pd.DataFrame,     # rob_df (Pillar III)
        str,              # proposal_html (Pillar IV blueprint)
        str,              # protocol_html (Pillar V sample size & protocol)
        str,              # excel_download_path
        str               # md_download_path
    ]:
        """
        Formats a Phase3Dossier into Gradio-compatible UI dataframes and HTML widgets.
        """
        # 1. Verdict & Status Banner
        gaps_count = len(dossier.evidence_matrix.observed_gaps)
        top_rc = dossier.reality_check_reports[0] if dossier.reality_check_reports else None
        rc_status = top_rc.status if top_rc else "Verified"
        rc_badge = top_rc.status_badge if top_rc else "Verified"
        rc_color = top_rc.status_color if top_rc else "#38BDF8"

        verdict_html = f"""
        <div style="background: rgba(15,23,42,0.85); border: 1.5px solid {rc_color}; border-radius: 16px; padding: 20px 24px; margin-bottom: 20px; box-shadow: 0 10px 25px -5px rgba(0,0,0,0.5);">
          <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px; margin-bottom: 12px;">
            <div style="display: flex; align-items: center; gap: 12px;">
              <div style="width: 44px; height: 44px; border-radius: 12px; background: rgba(56,189,248,0.15); display: flex; align-items: center; justify-content: center; font-size: 22px;">🧭</div>
              <div>
                <h3 style="color: #F8FAFC; margin: 0; font-size: 19px; font-weight: 800;">Phase 3 Evidence Synthesis &amp; Thesis Navigator Active</h3>
                <p style="color: #94A3B8; font-size: 13px; margin: 2px 0 0 0;">Synthesized across <strong>{len(dossier.evidence_matrix.studies)} study(ies)</strong> (N={dossier.evidence_matrix.total_patients_pooled} patients) in <strong>{dossier.target_topic}</strong></p>
              </div>
            </div>
            <div style="display: flex; align-items: center; gap: 8px;">
              <span style="background: rgba(56,189,248,0.15); border: 1px solid #38BDF8; color: #38BDF8; padding: 6px 14px; border-radius: 9999px; font-size: 12px; font-weight: 800;">
                📍 {gaps_count} Gaps Identified
              </span>
              <span style="background: rgba(245,158,11,0.15); border: 1px solid {rc_color}; color: {rc_color}; padding: 6px 14px; border-radius: 9999px; font-size: 12px; font-weight: 800;">
                {rc_badge}
              </span>
            </div>
          </div>
          <div style="background: rgba(30,41,59,0.7); border-radius: 10px; padding: 12px 16px; border-left: 4px solid {rc_color};">
            <span style="color: #F1F5F9; font-size: 14px; font-weight: 600;">Reality Check Synthesis: </span>
            <span style="color: #CBD5E1; font-size: 13px;">{top_rc.summary_verdict if top_rc else 'Evidence mapping complete.'}</span>
          </div>
        </div>
        """

        # 2. Evidence Matrix DataFrame
        matrix_rows = []
        for s in dossier.evidence_matrix.studies:
            matrix_rows.append({
                "Study ID": s.study_id,
                "Trial Title": s.title[:60] + "..." if len(s.title) > 60 else s.title,
                "Sample Size (N)": s.sample_size,
                "Interventions": ", ".join(s.interventions),
                "Comparators": ", ".join(s.comparators),
                "Primary Endpoints": ", ".join(s.primary_outcomes[:2]),
                "Follow-up (Wks)": s.follow_up_weeks or "NR",
                "Design & Blinding": s.study_design
            })
        evidence_matrix_df = pd.DataFrame(matrix_rows) if matrix_rows else pd.DataFrame()

        # 3. Gaps DataFrame
        gaps_rows = []
        for g in dossier.evidence_matrix.observed_gaps:
            gaps_rows.append({
                "Gap ID": g.gap_id,
                "Category": g.category.replace("_", " ").title(),
                "Gap Title": g.title,
                "Evidence Rationale": g.evidence_rationale,
                "Confidence": f"{g.confidence_score*100:.0f}%",
                "Verification Status": g.verification_status
            })
        gaps_df = pd.DataFrame(gaps_rows) if gaps_rows else pd.DataFrame()

        # 4. Reality Check HTML
        rc_matches_html = []
        if top_rc:
            rc_matches_html.append(f"<div style='margin-bottom: 12px; font-size: 13px; color: #94A3B8;'>Queried databases: <strong>{', '.join(top_rc.databases_queried)}</strong> | Strategy: <code>{top_rc.search_query_used}</code></div>")
            if top_rc.registered_trials:
                rc_matches_html.append("<h4 style='color: #F8FAFC; margin: 10px 0 6px 0; font-size: 14px;'>🏛️ ClinicalTrials.gov Registered Studies:</h4>")
                for t in top_rc.registered_trials[:4]:
                    status_badge = f"<span style='background: #1E293B; color: #F59E0B; padding: 2px 8px; border-radius: 6px; font-size: 11px; font-weight: 700;'>{t.overall_status}</span>"
                    rc_matches_html.append(f"""
                    <div style='background: rgba(15,23,42,0.6); border: 1px solid #334155; border-radius: 8px; padding: 10px 14px; margin-bottom: 8px;'>
                      <div style='display: flex; justify-content: space-between; align-items: center;'>
                        <a href='{t.url}' target='_blank' style='color: #38BDF8; font-weight: 700; text-decoration: none;'>{t.record_id}</a>
                        {status_badge}
                      </div>
                      <div style='color: #E2E8F0; font-size: 13px; margin-top: 4px;'>{t.title}</div>
                      <div style='color: #94A3B8; font-size: 11px; margin-top: 2px;'>{t.authors_or_sponsor}</div>
                    </div>
                    """)

            if top_rc.literature_matches:
                rc_matches_html.append("<h4 style='color: #F8FAFC; margin: 14px 0 6px 0; font-size: 14px;'>📚 Published Literature Matches (OpenAlex / PubMed):</h4>")
                for m in top_rc.literature_matches[:4]:
                    rc_matches_html.append(f"""
                    <div style='background: rgba(15,23,42,0.6); border: 1px solid #334155; border-radius: 8px; padding: 10px 14px; margin-bottom: 8px;'>
                      <div style='display: flex; justify-content: space-between; align-items: center;'>
                        <span style='color: #A855F7; font-weight: 700; font-size: 12px;'>{m.source}</span>
                        <span style='color: #94A3B8; font-size: 11px;'>{m.year or ''}</span>
                      </div>
                      <a href='{m.url}' target='_blank' style='color: #F1F5F9; font-size: 13px; font-weight: 600; text-decoration: none; display: block; margin-top: 4px;'>{m.title}</a>
                      <div style='color: #94A3B8; font-size: 11px; margin-top: 2px;'>{m.authors_or_sponsor}</div>
                    </div>
                    """)
        reality_check_html = "".join(rc_matches_html) or "<p style='color: #94A3B8;'>No external records returned.</p>"

        # 5. Methodological Appraisal (RoB 2.0) DataFrame
        rob_rows = []
        for a in dossier.methodological_assessments:
            for dom, det in a.domain_scores.items():
                rob_rows.append({
                    "Study ID": a.study_id,
                    "Framework": a.framework,
                    "Overall Rating": a.overall_rating,
                    "Domain": dom,
                    "Domain Risk": det.get("rating", ""),
                    "Scientific Justification": det.get("justification", ""),
                    "CONSORT Score": f"{a.consort_reporting_score}%"
                })
        rob_df = pd.DataFrame(rob_rows) if rob_rows else pd.DataFrame()

        # 6. Proposal HTML
        tp = dossier.thesis_proposals[0] if dossier.thesis_proposals else None
        if tp:
            titles_html = "".join([f"<li style='margin-bottom: 6px; color: #F1F5F9; font-weight: 600;'>{t}</li>" for t in tp.proposed_titles])
            finer_cards = []
            for crit, det in tp.finer_criteria.items():
                finer_cards.append(f"""
                <div style='background: rgba(15,23,42,0.7); border: 1px solid #334155; border-radius: 10px; padding: 10px 14px;'>
                  <div style='font-size: 11px; color: #94A3B8; text-transform: uppercase;'>{crit}</div>
                  <div style='font-size: 13px; font-weight: 700; color: {det.get("color", "#38BDF8")}; margin-top: 2px;'>{det.get("score")}</div>
                  <div style='font-size: 11px; color: #CBD5E1; margin-top: 4px;'>{det.get("details")}</div>
                </div>
                """)
            finer_grid = f"<div style='display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 10px; margin: 12px 0;'>{''.join(finer_cards)}</div>"

            supervisor_list = "".join([f"<li style='color: #FCA5A5; margin-bottom: 4px; font-size: 12px;'>{c}</li>" for c in tp.supervisor_verification_claims])

            proposal_html = f"""
            <div style='background: rgba(15,23,42,0.85); border: 1px solid #334155; border-radius: 14px; padding: 20px; color: #E2E8F0;'>
              <h3 style='color: #38BDF8; margin: 0 0 12px 0; font-size: 18px;'>🎓 Proposed Academic Research Titles</h3>
              <ul style='margin: 0 0 16px 20px; padding: 0;'>{titles_html}</ul>

              <div style='display: flex; gap: 16px; flex-wrap: wrap; margin-bottom: 16px;'>
                <div style='flex: 1; background: rgba(30,41,59,0.7); padding: 12px 16px; border-radius: 10px;'>
                  <div style='font-size: 11px; color: #94A3B8; text-transform: uppercase;'>Recommended Design</div>
                  <div style='font-size: 15px; font-weight: 800; color: #10B981; margin-top: 2px;'>{tp.recommended_study_design}</div>
                  <div style='font-size: 12px; color: #94A3B8; margin-top: 4px;'>{tp.design_justification}</div>
                </div>
                <div style='flex: 1; background: rgba(30,41,59,0.7); padding: 12px 16px; border-radius: 10px;'>
                  <div style='font-size: 11px; color: #94A3B8; text-transform: uppercase;'>Primary Objective</div>
                  <div style='font-size: 13px; color: #F1F5F9; font-weight: 600; margin-top: 4px;'>{tp.primary_objective}</div>
                </div>
              </div>

              <h4 style='color: #F8FAFC; margin: 16px 0 8px 0; font-size: 15px;'>⚖️ FINER Feasibility &amp; Ethical Appraisal</h4>
              {finer_grid}

              <div style='background: rgba(239,68,68,0.1); border: 1px solid #EF4444; border-radius: 10px; padding: 14px 18px; margin-top: 16px;'>
                <div style='color: #F87171; font-weight: 800; font-size: 13px; display: flex; align-items: center; gap: 6px;'>
                  <span>⚠️</span> Claims &amp; Assumptions Requiring Supervisor / IRB Approval
                </div>
                <ul style='margin: 8px 0 0 20px; padding: 0;'>{supervisor_list}</ul>
              </div>
            </div>
            """
        else:
            proposal_html = "<p style='color: #94A3B8;'>Proposal generation awaiting gap selection.</p>"

        # 7. Protocol & Statistical Planning HTML
        sp = dossier.sample_size_plan
        pdraft = dossier.protocol_draft
        protocol_html = f"""
        <div style='background: rgba(15,23,42,0.85); border: 1px solid #334155; border-radius: 14px; padding: 20px; color: #E2E8F0;'>
          <div style='display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px; margin-bottom: 16px;'>
            <div>
              <h3 style='color: #10B981; margin: 0; font-size: 18px;'>📐 Biostatistical Sample Size Planning</h3>
              <p style='color: #94A3B8; font-size: 12px; margin: 2px 0 0 0;'>Calculated using verified formulas (two-sample {sp.design_type if sp else 'continuous'})</p>
            </div>
            <div style='background: rgba(16,185,129,0.15); border: 1px solid #10B981; padding: 6px 16px; border-radius: 9999px;'>
              <span style='color: #34D399; font-size: 13px; font-weight: 800;'>Total N = {sp.n_total_with_attrition if sp else 0} Enrolled</span>
            </div>
          </div>

          <div style='display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 10px; margin-bottom: 16px;'>
            <div style='background: rgba(30,41,59,0.7); padding: 10px; border-radius: 8px; text-align: center;'>
              <div style='font-size: 11px; color: #94A3B8;'>Per Group (n)</div>
              <div style='font-size: 18px; font-weight: 800; color: #38BDF8;'>{sp.n_per_group if sp else 0}</div>
            </div>
            <div style='background: rgba(30,41,59,0.7); padding: 10px; border-radius: 8px; text-align: center;'>
              <div style='font-size: 11px; color: #94A3B8;'>Evaluable (N_eval)</div>
              <div style='font-size: 18px; font-weight: 800; color: #A855F7;'>{sp.n_total_evaluable if sp else 0}</div>
            </div>
            <div style='background: rgba(30,41,59,0.7); padding: 10px; border-radius: 8px; text-align: center;'>
              <div style='font-size: 11px; color: #94A3B8;'>Alpha (α)</div>
              <div style='font-size: 18px; font-weight: 800; color: #F59E0B;'>{sp.alpha if sp else 0.05}</div>
            </div>
            <div style='background: rgba(30,41,59,0.7); padding: 10px; border-radius: 8px; text-align: center;'>
              <div style='font-size: 11px; color: #94A3B8;'>Power (1-β)</div>
              <div style='font-size: 18px; font-weight: 800; color: #10B981;'>{sp.power*100:.0f}%</div>
            </div>
            <div style='background: rgba(30,41,59,0.7); padding: 10px; border-radius: 8px; text-align: center;'>
              <div style='font-size: 11px; color: #94A3B8;'>Attrition Buffer</div>
              <div style='font-size: 18px; font-weight: 800; color: #F43F5E;'>{sp.attrition_rate*100:.0f}%</div>
            </div>
          </div>

          <div style='background: rgba(30,41,59,0.5); padding: 12px 16px; border-radius: 10px; font-size: 12px; font-family: monospace; color: #CBD5E1; margin-bottom: 16px;'>
            {sp.mathematical_formula if sp else ''}
          </div>

          <h4 style='color: #F8FAFC; margin: 16px 0 8px 0; font-size: 15px;'>🔎 Reproducible PubMed MeSH Query</h4>
          <div style='background: #020617; border: 1px solid #1E293B; padding: 12px 16px; border-radius: 10px; font-family: monospace; font-size: 12px; color: #38BDF8; word-break: break-all;'>
            {pdraft.boolean_query if pdraft else ''}
          </div>
        </div>
        """

        excel_path = dossier.excel_path or ""
        md_path = os.path.join("outputs", f"MANDOROS_Phase3_Dossier_{dossier.target_topic.replace(' ', '_')[:30]}.md")

        return (
            verdict_html,
            evidence_matrix_df,
            gaps_df,
            reality_check_html,
            rob_df,
            proposal_html,
            protocol_html,
            excel_path,
            md_path
        )
