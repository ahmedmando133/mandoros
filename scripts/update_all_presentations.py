# -*- coding: utf-8 -*-
"""
MANDOROS Academic Keynote Presentation Suite Synchronizer
Permanently updates both PowerPoint (.pptx) and HTML (.html) presentations
across the repository with the complete 20-slide Master Academic Suite:
- Slide 02: Comprehensive 5-Part Academic Agenda & Table of Contents
- Slide 13: Clinical AI Governance & Two-Phase 10/10 Quality Gate
- Slide 14: Evidence Synthesis & Deep Methodological Audit (TrialMind & AMIA 2022)
- Slide 15: Phase 3 — Research Gap & Thesis Navigator Engine (Overview & FINER Architecture)
- Slide 16: The 5 Pillars of Academic Rigor & Biostatistical Power Calibration
- Slide 17: PRISMA 2020 Clinical Trial Intelligence & Interactive Flow Architecture
- Slide 18: External Clinical Databases, PubMed & NCBI FHIR Ecosystem
- Slide 19: Phase 2 Scientific Restructuring & 20 Supreme Rules
- Slide 20: Enterprise Cloud Security, Render RAM Optimization & 24/7 Zero-Cold-Start Reliability
"""

import os
import re
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

BASE_DIR = Path(__file__).resolve().parent.parent

PPTX_TARGETS = [
    BASE_DIR / "MANDOROS_Global_Academic_Presentation.pptx",
    BASE_DIR / "mandoros_dossier" / "MANDOROS_Global_Academic_Presentation.pptx"
]

HTML_TARGETS = [
    BASE_DIR / "MANDOROS_Global_Academic_Presentation.html",
    BASE_DIR / "mandoros_dossier" / "MANDOROS_Global_Academic_Presentation.html"
]


# =========================================================================
# PPTX BUILDERS FOR SLIDES 15 - 20
# =========================================================================

def add_slide_15_phase3(prs: Presentation):
    """Adds Slide 15: Phase 3 Research Gap & Thesis Navigator."""
    blank_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank_layout)

    background = slide.background
    fill = background.fill
    fill.solid()
    fill.fore_color.rgb = RGBColor(11, 17, 32)

    # 1. Category Tracker
    top_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(8), Inches(0.35))
    tf_top = top_box.text_frame
    tf_top.word_wrap = True
    p_top = tf_top.paragraphs[0]
    p_top.text = "RESEARCH TRANSLATION & THESIS ARCHITECTURE"
    p_top.font.name = "Arial"
    p_top.font.size = Pt(10)
    p_top.font.bold = True
    p_top.font.color.rgb = RGBColor(192, 132, 252) # Purple

    # Keynote badge
    keynote_box = slide.shapes.add_textbox(Inches(9.2), Inches(0.4), Inches(3.3), Inches(0.35))
    tf_k = keynote_box.text_frame
    p_k = tf_k.paragraphs[0]
    p_k.text = "PHASE 3 BLUEPRINT"
    p_k.alignment = PP_ALIGN.RIGHT
    p_k.font.name = "Arial"
    p_k.font.size = Pt(10)
    p_k.font.bold = True
    p_k.font.color.rgb = RGBColor(148, 163, 184)

    # 2. Main Title
    title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.75), Inches(11.5), Inches(0.75))
    tf_title = title_box.text_frame
    tf_title.word_wrap = True
    p_title = tf_title.paragraphs[0]
    p_title.text = "Phase 3 — Research Gap & Thesis Navigator Engine"
    p_title.font.name = "Arial"
    p_title.font.size = Pt(21)
    p_title.font.bold = True
    p_title.font.color.rgb = RGBColor(248, 250, 252)

    p_sub = tf_title.add_paragraph()
    p_sub.text = "Autonomous Clinical Research Planning: From Unresolved Evidence Gaps to Actionable FINER Theses & SPIRIT Protocols."
    p_sub.font.name = "Arial"
    p_sub.font.size = Pt(11)
    p_sub.font.color.rgb = RGBColor(148, 163, 184)

    cards_data = [
        {
            "tag": "PILLARS I & II: MAPPING & REALITY CHECK",
            "tag_color": RGBColor(245, 158, 11), # Amber
            "title": "Evidence Matrix & Scholarly Check",
            "bullets": [
                "Cross-Study Evidence Matrix: Aggregates PICO, sample sizes, and endpoints across multi-trial cohorts.",
                "5 Discovered Gap Archetypes: Unresolved head-to-head comparisons, biomarker subpopulation gaps, underrepresented cohorts, dose optimization, and safety signals.",
                "Scholarly Reality Check: Automated query validation via ClinicalTrials.gov APIv2 and PubMed for ongoing trial status.",
                "Novelty & Feasibility Gate: Classifies detected gaps as Open Unexplored, In-Progress, or Saturated to prevent redundant research."
            ]
        },
        {
            "tag": "PILLARS III & IV: QUALITY & FORMULATION",
            "tag_color": RGBColor(0, 245, 212), # Cyan
            "title": "Methodological Audit & Thesis Blueprint",
            "bullets": [
                "Algorithmic Cochrane RoB 2.0: Evaluates 5 core domains of bias with automated text-anchored justifications.",
                "CONSORT 2010 Compliance Scoring: Dissects reporting transparency across randomization, blinding, and attrition.",
                "FINER Research Hypothesis Architect: Formulates Feasible, Interesting, Novel, Ethical, and Relevant thesis proposals.",
                "Structured Academic IMRAD Outline: Formats background rationale, specific primary/secondary aims, and clinical implications."
            ]
        },
        {
            "tag": "PILLAR V & EXPORTS: BIOSTATISTICS",
            "tag_color": RGBColor(192, 132, 252), # Purple
            "title": "Protocol Outline & Biostatistical Planning",
            "bullets": [
                "Deterministic Power & Sample Size: Calculates required N for alpha=0.05, 80% & 90% power with attrition margin.",
                "Statistical Analysis Plan (SAP): Prespecified ANCOVA / mixed-effects model, primary estimand, and sensitivity checks.",
                "Standardized 7-Sheet Phase 3 Research Package: Exports full evidence matrix, gap inventory, reality check, and protocol plan.",
                "Markdown Thesis Dossier: Ready-to-publish academic document for thesis defense, grant proposals, and IRB submissions."
            ]
        }
    ]

    card_width = Inches(3.7)
    card_height = Inches(4.7)
    card_gap = Inches(0.3)
    card_top = Inches(1.65)
    left_margin = Inches(0.8)

    for i, cdata in enumerate(cards_data):
        card_left = left_margin + i * (card_width + card_gap)
        shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, card_left, card_top, card_width, card_height)
        shape.fill.solid()
        shape.fill.fore_color.rgb = RGBColor(15, 23, 42)
        shape.line.color.rgb = cdata["tag_color"]
        shape.line.width = Pt(1.5)

        c_box = slide.shapes.add_textbox(card_left + Inches(0.18), card_top + Inches(0.18), card_width - Inches(0.36), card_height - Inches(0.36))
        tf = c_box.text_frame
        tf.word_wrap = True

        p_tag = tf.paragraphs[0]
        p_tag.text = cdata["tag"]
        p_tag.font.name = "Arial"
        p_tag.font.size = Pt(9.5)
        p_tag.font.bold = True
        p_tag.font.color.rgb = cdata["tag_color"]
        p_tag.space_after = Pt(4)

        p_t = tf.add_paragraph()
        p_t.text = cdata["title"]
        p_t.font.name = "Arial"
        p_t.font.size = Pt(13)
        p_t.font.bold = True
        p_t.font.color.rgb = RGBColor(248, 250, 252)
        p_t.space_after = Pt(10)

        for b in cdata["bullets"]:
            p_b = tf.add_paragraph()
            p_b.text = "• " + b
            p_b.font.name = "Arial"
            p_b.font.size = Pt(9.5)
            p_b.font.color.rgb = RGBColor(203, 213, 225)
            p_b.space_after = Pt(6)

    # Footer
    foot_shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(6.55), Inches(11.7), Inches(0.48))
    foot_shape.fill.solid()
    foot_shape.fill.fore_color.rgb = RGBColor(30, 41, 59)
    foot_shape.line.color.rgb = RGBColor(51, 65, 85)
    foot_shape.line.width = Pt(1)

    foot_box = slide.shapes.add_textbox(Inches(0.9), Inches(6.58), Inches(11.5), Inches(0.42))
    tf_f = foot_box.text_frame
    p_f = tf_f.paragraphs[0]
    p_f.text = "PHASE 3 CERTIFIED: 5 Pillars of Rigor  |  ClinicalTrials.gov Live Validation  |  80/90% Power Calibration  |  Standardized 7-Sheet Research Package"
    p_f.font.name = "Arial"
    p_f.font.size = Pt(10)
    p_f.font.bold = True
    p_f.font.color.rgb = RGBColor(192, 132, 252)
    p_f.alignment = PP_ALIGN.CENTER

    return slide


def add_slide_16_five_pillars(prs: Presentation):
    """Adds Slide 16: The 5 Pillars of Academic Rigor & Biostatistical Calibration."""
    blank_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank_layout)

    background = slide.background
    fill = background.fill
    fill.solid()
    fill.fore_color.rgb = RGBColor(11, 17, 32)

    top_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(8), Inches(0.35))
    tf_top = top_box.text_frame
    tf_top.word_wrap = True
    p_top = tf_top.paragraphs[0]
    p_top.text = "RESEARCH TRANSLATION & BIOSTATISTICAL RIGOR"
    p_top.font.name = "Arial"
    p_top.font.size = Pt(10)
    p_top.font.bold = True
    p_top.font.color.rgb = RGBColor(192, 132, 252)

    keynote_box = slide.shapes.add_textbox(Inches(9.2), Inches(0.4), Inches(3.3), Inches(0.35))
    tf_k = keynote_box.text_frame
    p_k = tf_k.paragraphs[0]
    p_k.text = "THE 5 PILLARS OF RIGOR"
    p_k.alignment = PP_ALIGN.RIGHT
    p_k.font.name = "Arial"
    p_k.font.size = Pt(10)
    p_k.font.bold = True
    p_k.font.color.rgb = RGBColor(148, 163, 184)

    title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.75), Inches(11.5), Inches(0.75))
    tf_title = title_box.text_frame
    tf_title.word_wrap = True
    p_title = tf_title.paragraphs[0]
    p_title.text = "The 5 Pillars of Academic Rigor & Biostatistical Calibration"
    p_title.font.name = "Arial"
    p_title.font.size = Pt(21)
    p_title.font.bold = True
    p_title.font.color.rgb = RGBColor(248, 250, 252)

    p_sub = tf_title.add_paragraph()
    p_sub.text = "End-to-End Methodology: From Cross-Study Evidence Matrix to Deterministic Power Calibration & SPIRIT 2013 Protocol."
    p_sub.font.name = "Arial"
    p_sub.font.size = Pt(11)
    p_sub.font.color.rgb = RGBColor(148, 163, 184)

    cards_data = [
        {
            "tag": "PILLARS I & II: DISCOVERY & REALITY GATE",
            "tag_color": RGBColor(245, 158, 11),
            "title": "Cross-Study Evidence Matrix & Reality Gate",
            "bullets": [
                "Cross-Study Evidence Matrix (Pillar I): Dynamically aggregates PICO characteristics, comparator arms, patient demographics, and multi-endpoint data across all ingested trials.",
                "5 Algorithmic Gap Archetypes: Detects active comparator voids, unmeasured patient-reported outcomes (PROs), high-risk subpopulations (e.g. eGFR < 30 / geriatrics), duration plateaus, and dose-titration voids.",
                "Live Scholarly Reality Check (Pillar II): Automates real-time verification queries against ClinicalTrials.gov APIv2, PubMed, and OpenAlex to cross-reference ongoing research.",
                "Evidence Saturation Classification: Categorizes candidate hypotheses as Open Unexplored, In-Progress, or Saturated to eliminate redundant academic waste."
            ]
        },
        {
            "tag": "PILLAR III: METHODOLOGICAL QUALITY",
            "tag_color": RGBColor(0, 245, 212),
            "title": "Cochrane RoB 2.0 & robvis Traffic-Light",
            "bullets": [
                "Domain-by-Domain Bias Appraisal: Programmatically audits Cochrane RoB 2.0 domains (D1: Randomization, D2: Deviations, D3: Missing Outcomes, D4: Measurement, D5: Reporting).",
                "Verbatim-Anchored Justifications: Binds every RoB rating to exact chunk-level text quotes extracted from the trial PDF; zero unreferenced judgments.",
                "robvis-Grade Traffic-Light Visualization: Generates interactive Cochrane summary matrix and bar charts displaying risk distributions across the trial cohort.",
                "CONSORT 2010 Reporting Completeness: Dissects 25-item checklist compliance including sample size prespecification, blinding mechanisms, and ITT fidelity."
            ]
        },
        {
            "tag": "PILLARS IV & V: PROTOCOL & POWER",
            "tag_color": RGBColor(192, 132, 252),
            "title": "FINER Blueprint & Deterministic Power",
            "bullets": [
                "FINER Hypothesis Formulation (Pillar IV): Structures hypotheses satisfying Feasible, Interesting, Novel, Ethical, and Relevant criteria with full academic IMRAD rationale.",
                "Deterministic Power & Sample Size (Pillar V): Code-level biostatistical calculation for continuous & binary endpoints; solves for N at alpha=0.05, 80% & 90% power with attrition buffer.",
                "Superiority & Non-Inferiority Architecture: Supports two-sample superiority designs and non-inferiority trials with customizable margin (Delta_NI) and pooled SD (sigma).",
                "7-Sheet Phase 3 Research Package: Exports standardized Excel sheets (Evidence Matrix, Gaps, Reality Check, RoB, SAP, Power) plus ready-to-defend Markdown thesis dossier."
            ]
        }
    ]

    card_width = Inches(3.7)
    card_height = Inches(4.7)
    card_gap = Inches(0.3)
    card_top = Inches(1.65)
    left_margin = Inches(0.8)

    for i, cdata in enumerate(cards_data):
        card_left = left_margin + i * (card_width + card_gap)
        shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, card_left, card_top, card_width, card_height)
        shape.fill.solid()
        shape.fill.fore_color.rgb = RGBColor(15, 23, 42)
        shape.line.color.rgb = cdata["tag_color"]
        shape.line.width = Pt(1.5)

        c_box = slide.shapes.add_textbox(card_left + Inches(0.18), card_top + Inches(0.18), card_width - Inches(0.36), card_height - Inches(0.36))
        tf = c_box.text_frame
        tf.word_wrap = True

        p_tag = tf.paragraphs[0]
        p_tag.text = cdata["tag"]
        p_tag.font.name = "Arial"
        p_tag.font.size = Pt(9.5)
        p_tag.font.bold = True
        p_tag.font.color.rgb = cdata["tag_color"]
        p_tag.space_after = Pt(4)

        p_t = tf.add_paragraph()
        p_t.text = cdata["title"]
        p_t.font.name = "Arial"
        p_t.font.size = Pt(13)
        p_t.font.bold = True
        p_t.font.color.rgb = RGBColor(248, 250, 252)
        p_t.space_after = Pt(10)

        for b in cdata["bullets"]:
            p_b = tf.add_paragraph()
            p_b.text = "• " + b
            p_b.font.name = "Arial"
            p_b.font.size = Pt(9.5)
            p_b.font.color.rgb = RGBColor(203, 213, 225)
            p_b.space_after = Pt(6)

    # Footer
    foot_shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(6.55), Inches(11.7), Inches(0.48))
    foot_shape.fill.solid()
    foot_shape.fill.fore_color.rgb = RGBColor(30, 41, 59)
    foot_shape.line.color.rgb = RGBColor(51, 65, 85)
    foot_shape.line.width = Pt(1)

    foot_box = slide.shapes.add_textbox(Inches(0.9), Inches(6.58), Inches(11.5), Inches(0.42))
    tf_f = foot_box.text_frame
    p_f = tf_f.paragraphs[0]
    p_f.text = "5 PILLARS CERTIFIED: Evidence Matrix  |  PubMed & ClinicalTrials.gov Reality Gate  |  Cochrane RoB 2.0  |  FINER Thesis  |  80/90% Power Calibration"
    p_f.font.name = "Arial"
    p_f.font.size = Pt(10)
    p_f.font.bold = True
    p_f.font.color.rgb = RGBColor(192, 132, 252)
    p_f.alignment = PP_ALIGN.CENTER

    return slide


def add_slide_17_prisma_engine(prs: Presentation):
    """Adds Slide 17: PRISMA 2020 Clinical Trial Intelligence & Interactive Flow Architecture."""
    blank_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank_layout)

    background = slide.background
    fill = background.fill
    fill.solid()
    fill.fore_color.rgb = RGBColor(11, 17, 32)

    top_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(8), Inches(0.35))
    tf_top = top_box.text_frame
    tf_top.word_wrap = True
    p_top = tf_top.paragraphs[0]
    p_top.text = "SYSTEMATIC REVIEW STANDARDS & FLOW INTEGRITY"
    p_top.font.name = "Arial"
    p_top.font.size = Pt(10)
    p_top.font.bold = True
    p_top.font.color.rgb = RGBColor(16, 185, 129)

    keynote_box = slide.shapes.add_textbox(Inches(9.2), Inches(0.4), Inches(3.3), Inches(0.35))
    tf_k = keynote_box.text_frame
    p_k = tf_k.paragraphs[0]
    p_k.text = "PRISMA 2020 CERTIFIED"
    p_k.alignment = PP_ALIGN.RIGHT
    p_k.font.name = "Arial"
    p_k.font.size = Pt(10)
    p_k.font.bold = True
    p_k.font.color.rgb = RGBColor(148, 163, 184)

    title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.75), Inches(11.5), Inches(0.75))
    tf_title = title_box.text_frame
    tf_title.word_wrap = True
    p_title = tf_title.paragraphs[0]
    p_title.text = "PRISMA 2020 Intelligence & Interactive Flow Architecture"
    p_title.font.name = "Arial"
    p_title.font.size = Pt(21)
    p_title.font.bold = True
    p_title.font.color.rgb = RGBColor(248, 250, 252)

    p_sub = tf_title.add_paragraph()
    p_sub.text = "Transparent Study Selection: 4-Stage Flow Diagram, Automated Deduplication, Zero-FN Screening, and Reporting Auditing."
    p_sub.font.name = "Arial"
    p_sub.font.size = Pt(11)
    p_sub.font.color.rgb = RGBColor(148, 163, 184)

    cards_data = [
        {
            "tag": "4-STAGE SELECTION ARCHITECTURE",
            "tag_color": RGBColor(16, 185, 129),
            "title": "PRISMA 2020 Flow Diagram Engine",
            "bullets": [
                "Stage 1 — Identification: Consolidates literature hits from PubMed/Medline, clinical registers (ClinicalTrials.gov), and manual PDF uploads with automated title/DOI deduplication.",
                "Stage 2 — Screening: Systematic screening of titles and abstracts; records evaluated against pre-defined inclusion criteria with quantified exclusion logging.",
                "Stage 3 — Eligibility: Full-text appraisal against atomic eligibility properties; every excluded record is tagged with an immutable, transparent exclusion reason.",
                "Stage 4 — Included: Final cohort synthesis determining studies eligible for qualitative systematic review and quantitative metafor-grade pooling."
            ]
        },
        {
            "tag": "ZERO-FN REASONING MIDDLEWARE",
            "tag_color": RGBColor(56, 189, 248),
            "title": "Ternary Screening & Zero-FN Gate",
            "bullets": [
                "Ternary Decision Logic (+1, -1, 0): AI assesses text chunks using strict ternary voting; indeterminate evidence (0) is never prematurely discarded.",
                "Zero-False-Negative Safeguard: Ambiguous or borderline trials automatically pass to full-text human referee inspection, preventing accidental exclusion of key evidence.",
                "Chunk-Level Provenance Anchoring: Every inclusion/exclusion decision is permanently anchored to document chunk IDs with verbatim justification quotes.",
                "Multi-Reviewer Emulation: Replicates dual independent reviewer paradigms with consensus resolution for Cochrane-standard review fidelity."
            ]
        },
        {
            "tag": "COMPLIANCE & VISUALIZATION",
            "tag_color": RGBColor(244, 63, 94),
            "title": "PRISMA 2020 Checklist & Dashboard",
            "bullets": [
                "27-Item PRISMA 2020 Checklist Auditor: Evaluates reporting fidelity across Title, Abstract, Introduction, Methods, Results, Discussion, and Funding.",
                "Stand-Alone Interactive HTML Dashboard: Renders dynamic SVG/Plotly PRISMA flowcharts with clickable nodes revealing study IDs, counts, and exclusion breakdowns.",
                "Deterministic Attrition Accounting: Enforces mathematical consistency across nodes: Identified - Duplicates = Screened; Screened - Excluded = Eligible.",
                "Publication-Ready Vector & Data Export: One-click export of PRISMA flowcharts in SVG/PNG and full audit logs in Excel for peer-reviewed journal submission."
            ]
        }
    ]

    card_width = Inches(3.7)
    card_height = Inches(4.7)
    card_gap = Inches(0.3)
    card_top = Inches(1.65)
    left_margin = Inches(0.8)

    for i, cdata in enumerate(cards_data):
        card_left = left_margin + i * (card_width + card_gap)
        shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, card_left, card_top, card_width, card_height)
        shape.fill.solid()
        shape.fill.fore_color.rgb = RGBColor(15, 23, 42)
        shape.line.color.rgb = cdata["tag_color"]
        shape.line.width = Pt(1.5)

        c_box = slide.shapes.add_textbox(card_left + Inches(0.18), card_top + Inches(0.18), card_width - Inches(0.36), card_height - Inches(0.36))
        tf = c_box.text_frame
        tf.word_wrap = True

        p_tag = tf.paragraphs[0]
        p_tag.text = cdata["tag"]
        p_tag.font.name = "Arial"
        p_tag.font.size = Pt(9.5)
        p_tag.font.bold = True
        p_tag.font.color.rgb = cdata["tag_color"]
        p_tag.space_after = Pt(4)

        p_t = tf.add_paragraph()
        p_t.text = cdata["title"]
        p_t.font.name = "Arial"
        p_t.font.size = Pt(13)
        p_t.font.bold = True
        p_t.font.color.rgb = RGBColor(248, 250, 252)
        p_t.space_after = Pt(10)

        for b in cdata["bullets"]:
            p_b = tf.add_paragraph()
            p_b.text = "• " + b
            p_b.font.name = "Arial"
            p_b.font.size = Pt(9.5)
            p_b.font.color.rgb = RGBColor(203, 213, 225)
            p_b.space_after = Pt(6)

    # Footer
    foot_shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(6.55), Inches(11.7), Inches(0.48))
    foot_shape.fill.solid()
    foot_shape.fill.fore_color.rgb = RGBColor(30, 41, 59)
    foot_shape.line.color.rgb = RGBColor(51, 65, 85)
    foot_shape.line.width = Pt(1)

    foot_box = slide.shapes.add_textbox(Inches(0.9), Inches(6.58), Inches(11.5), Inches(0.42))
    tf_f = foot_box.text_frame
    p_f = tf_f.paragraphs[0]
    p_f.text = "PRISMA 2020 AUDIT: 4-Stage Flow Diagram  |  Ternary Zero-FN Screening  |  27-Item Checklist  |  Interactive SVG Dashboard"
    p_f.font.name = "Arial"
    p_f.font.size = Pt(10)
    p_f.font.bold = True
    p_f.font.color.rgb = RGBColor(16, 185, 129)
    p_f.alignment = PP_ALIGN.CENTER

    return slide


def add_slide_18_clinical_databases(prs: Presentation):
    """Adds Slide 18: External Clinical Databases, PubMed & NCBI FHIR Ecosystem."""
    blank_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank_layout)

    background = slide.background
    fill = background.fill
    fill.solid()
    fill.fore_color.rgb = RGBColor(11, 17, 32)

    top_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(8), Inches(0.35))
    tf_top = top_box.text_frame
    tf_top.word_wrap = True
    p_top = tf_top.paragraphs[0]
    p_top.text = "CLINICAL KNOWLEDGE BASES & INTEROPERABILITY"
    p_top.font.name = "Arial"
    p_top.font.size = Pt(10)
    p_top.font.bold = True
    p_top.font.color.rgb = RGBColor(56, 189, 248)

    keynote_box = slide.shapes.add_textbox(Inches(9.2), Inches(0.4), Inches(3.3), Inches(0.35))
    tf_k = keynote_box.text_frame
    p_k = tf_k.paragraphs[0]
    p_k.text = "NCBI FHIR & NIH APIS"
    p_k.alignment = PP_ALIGN.RIGHT
    p_k.font.name = "Arial"
    p_k.font.size = Pt(10)
    p_k.font.bold = True
    p_k.font.color.rgb = RGBColor(148, 163, 184)

    title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.75), Inches(11.5), Inches(0.75))
    tf_title = title_box.text_frame
    tf_title.word_wrap = True
    p_title = tf_title.paragraphs[0]
    p_title.text = "External Clinical Databases, PubMed & NCBI FHIR Ecosystem"
    p_title.font.name = "Arial"
    p_title.font.size = Pt(21)
    p_title.font.bold = True
    p_title.font.color.rgb = RGBColor(248, 250, 252)

    p_sub = tf_title.add_paragraph()
    p_sub.text = "Live Bidirectional Interoperability: PubMed E-utilities, ClinicalTrials.gov APIv2, NLM RxNorm, and HL7 FHIR R4 ResearchStudy."
    p_sub.font.name = "Arial"
    p_sub.font.size = Pt(11)
    p_sub.font.color.rgb = RGBColor(148, 163, 184)

    cards_data = [
        {
            "tag": "BIOMEDICAL LITERATURE ENGINE",
            "tag_color": RGBColor(56, 189, 248),
            "title": "PubMed & NCBI E-utilities Integration",
            "bullets": [
                "Direct E-utilities Protocol: Interfaces NCBI Entrez API (esearch, esummary, efetch) for real-time biomedical literature verification.",
                "PICO Deconstruction & MeSH Expansion: Automatically decomposes research questions into MeSH ontology descriptors, achieving >= 78% search recall.",
                "Scholarly Gap Saturation Verification: Queries Medline to verify if discovered evidence gaps have already been addressed in recent published trials.",
                "PubMed Central (PMC) BioC Text Mining: Extracts open-access full-text sections, tables, and XML metadata for automated citation cross-matching."
            ]
        },
        {
            "tag": "TRIAL REGISTRY & BENCHMARKING",
            "tag_color": RGBColor(245, 158, 11),
            "title": "Live ClinicalTrials.gov APIv2 Registry",
            "bullets": [
                "Live Registry Synchronization: Native HTTP client directly queries ClinicalTrials.gov APIv2 REST endpoints without third-party middleware.",
                "Automated NCT Protocol Benchmarking: Pulls official registered study protocols by NCT ID to verify pre-specified primary/secondary endpoints vs published outcomes.",
                "Trial Recruitment & Status Tracking: Audits active recruiting, completed, active-not-recruiting, and terminated trials across global sponsor portfolios.",
                "Outcome Reporting Bias Detection: Flags discrepancies between registered trial registry endpoints and selectively reported journal publications."
            ]
        },
        {
            "tag": "STANDARDS & INTEROPERABILITY",
            "tag_color": RGBColor(16, 185, 129),
            "title": "NLM RxNorm & HL7 FHIR Interoperability",
            "bullets": [
                "NLM RxNorm Drug Normalization: Client-side integration with rxnav.nlm.nih.gov resolves brand names and dosage forms into canonical RxCUI codes.",
                "Client-Side Session Caching: Caches public RxCUI mappings in sessionStorage to minimize API latency and ensure offline browser speed.",
                "HL7 FHIR R4 ResearchStudy Mapping: Formats extracted trial evidence into standardized FHIR ResearchStudy JSON-LD clinical trial models.",
                "NCBI FHIR Interactive Action Badges: Embedded UI badges enable one-click verification of trial identifiers, regulatory codes, and standardized vocabularies."
            ]
        }
    ]

    card_width = Inches(3.7)
    card_height = Inches(4.7)
    card_gap = Inches(0.3)
    card_top = Inches(1.65)
    left_margin = Inches(0.8)

    for i, cdata in enumerate(cards_data):
        card_left = left_margin + i * (card_width + card_gap)
        shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, card_left, card_top, card_width, card_height)
        shape.fill.solid()
        shape.fill.fore_color.rgb = RGBColor(15, 23, 42)
        shape.line.color.rgb = cdata["tag_color"]
        shape.line.width = Pt(1.5)

        c_box = slide.shapes.add_textbox(card_left + Inches(0.18), card_top + Inches(0.18), card_width - Inches(0.36), card_height - Inches(0.36))
        tf = c_box.text_frame
        tf.word_wrap = True

        p_tag = tf.paragraphs[0]
        p_tag.text = cdata["tag"]
        p_tag.font.name = "Arial"
        p_tag.font.size = Pt(9.5)
        p_tag.font.bold = True
        p_tag.font.color.rgb = cdata["tag_color"]
        p_tag.space_after = Pt(4)

        p_t = tf.add_paragraph()
        p_t.text = cdata["title"]
        p_t.font.name = "Arial"
        p_t.font.size = Pt(13)
        p_t.font.bold = True
        p_t.font.color.rgb = RGBColor(248, 250, 252)
        p_t.space_after = Pt(10)

        for b in cdata["bullets"]:
            p_b = tf.add_paragraph()
            p_b.text = "• " + b
            p_b.font.name = "Arial"
            p_b.font.size = Pt(9.5)
            p_b.font.color.rgb = RGBColor(203, 213, 225)
            p_b.space_after = Pt(6)

    # Footer
    foot_shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(6.55), Inches(11.7), Inches(0.48))
    foot_shape.fill.solid()
    foot_shape.fill.fore_color.rgb = RGBColor(30, 41, 59)
    foot_shape.line.color.rgb = RGBColor(51, 65, 85)
    foot_shape.line.width = Pt(1)

    foot_box = slide.shapes.add_textbox(Inches(0.9), Inches(6.58), Inches(11.5), Inches(0.42))
    tf_f = foot_box.text_frame
    p_f = tf_f.paragraphs[0]
    p_f.text = "INTEROPERABILITY CERTIFIED: PubMed E-utilities  |  ClinicalTrials.gov APIv2  |  NLM RxNorm RxCUI  |  HL7 FHIR R4 ResearchStudy"
    p_f.font.name = "Arial"
    p_f.font.size = Pt(10)
    p_f.font.bold = True
    p_f.font.color.rgb = RGBColor(56, 189, 248)
    p_f.alignment = PP_ALIGN.CENTER

    return slide


def add_slide_19_phase2_rules(prs: Presentation):
    """Adds Slide 19: Phase 2 Scientific Restructuring & 20 Supreme Rules."""
    blank_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank_layout)

    background = slide.background
    fill = background.fill
    fill.solid()
    fill.fore_color.rgb = RGBColor(11, 17, 32)

    top_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(8), Inches(0.35))
    tf_top = top_box.text_frame
    tf_top.word_wrap = True
    p_top = tf_top.paragraphs[0]
    p_top.text = "SCIENTIFIC RESTRUCTURING & PROTOCOL ENFORCEMENT"
    p_top.font.name = "Arial"
    p_top.font.size = Pt(10)
    p_top.font.bold = True
    p_top.font.color.rgb = RGBColor(56, 189, 248)

    keynote_box = slide.shapes.add_textbox(Inches(9.2), Inches(0.4), Inches(3.3), Inches(0.35))
    tf_k = keynote_box.text_frame
    p_k = tf_k.paragraphs[0]
    p_k.text = "20 SUPREME RULES"
    p_k.alignment = PP_ALIGN.RIGHT
    p_k.font.name = "Arial"
    p_k.font.size = Pt(10)
    p_k.font.bold = True
    p_k.font.color.rgb = RGBColor(148, 163, 184)

    title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.75), Inches(11.5), Inches(0.75))
    tf_title = title_box.text_frame
    tf_title.word_wrap = True
    p_title = tf_title.paragraphs[0]
    p_title.text = "Phase 2 Scientific Restructuring & Zero-Contamination Pipeline"
    p_title.font.name = "Arial"
    p_title.font.size = Pt(21)
    p_title.font.bold = True
    p_title.font.color.rgb = RGBColor(248, 250, 252)

    p_sub = tf_title.add_paragraph()
    p_sub.text = "Complete Elimination of Data Blending, Single-Study Pooling Protection, and Standardized Master Extraction Sheet."
    p_sub.font.name = "Arial"
    p_sub.font.size = Pt(11)
    p_sub.font.color.rgb = RGBColor(148, 163, 184)

    cards_data = [
        {
            "tag": "RULES 1–5: WORKBOOK INTEGRITY",
            "tag_color": RGBColor(16, 185, 129),
            "title": "Standardized Master Excel Sheet",
            "bullets": [
                "Strict 5-Section Architecture: Study Characteristics, Eligibility Criteria, Baseline, Efficacy, and Safety Outcomes.",
                "Clean Outcome Titles: Eradicates bracketed sample sizes and demographic noise; preserves pure clinical endpoints.",
                "Independent Sample Size Columns: Dedicated 'Sample Analyzed (N)', 'N Randomized', and 'N Baseline Analyzed' fields.",
                "Dispersion Normalization: Explicit separation of Mean, SD, SE, Median, Q1, Q3, Adjusted Change, and Treatment Difference."
            ]
        },
        {
            "tag": "RULES 11–15: BIOSTATISTICAL PURITY",
            "tag_color": RGBColor(56, 189, 248),
            "title": "Single-Study Protection (Rule 12)",
            "bullets": [
                "Single-Trial Safeguard (k=1): Completely prohibits artificial multi-arm pooling and fabricated I²=0.0% heterogeneity.",
                "Status Flagging: Sets analysis status to 'NOT_APPLICABLE_SINGLE_STUDY' and leaves non-applicable metrics blank.",
                "Shared Control Normalization (Rule 13): Multi-arm active doses sharing a comparator never double-count control participants.",
                "Statistical Operators & Exact P-Values (Rule 15): Eliminates rounding underflow (p=0); separates operator and value."
            ]
        },
        {
            "tag": "RULES 16–20 & UPLOAD ISOLATION",
            "tag_color": RGBColor(244, 63, 94),
            "title": "Strict Upload Isolation & Express Lab",
            "bullets": [
                "Strict User Upload Isolation: Automatically purges prior cohort state so newly uploaded files are never blended with past trials.",
                "current_input_stems Gate: Processing strictly limited to files present in the active user upload session.",
                "Adverse-Event Extraction (Rule 16): Explicitly separates event count, denominator, and percentage.",
                "Student & Junior Researcher Express Lab: Generates plain-language executive briefs, thesis guidance, and research roadmaps."
            ]
        }
    ]

    card_width = Inches(3.7)
    card_height = Inches(4.7)
    card_gap = Inches(0.3)
    card_top = Inches(1.65)
    left_margin = Inches(0.8)

    for i, cdata in enumerate(cards_data):
        card_left = left_margin + i * (card_width + card_gap)
        shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, card_left, card_top, card_width, card_height)
        shape.fill.solid()
        shape.fill.fore_color.rgb = RGBColor(15, 23, 42)
        shape.line.color.rgb = cdata["tag_color"]
        shape.line.width = Pt(1.5)

        c_box = slide.shapes.add_textbox(card_left + Inches(0.18), card_top + Inches(0.18), card_width - Inches(0.36), card_height - Inches(0.36))
        tf = c_box.text_frame
        tf.word_wrap = True

        p_tag = tf.paragraphs[0]
        p_tag.text = cdata["tag"]
        p_tag.font.name = "Arial"
        p_tag.font.size = Pt(9.5)
        p_tag.font.bold = True
        p_tag.font.color.rgb = cdata["tag_color"]
        p_tag.space_after = Pt(4)

        p_t = tf.add_paragraph()
        p_t.text = cdata["title"]
        p_t.font.name = "Arial"
        p_t.font.size = Pt(13)
        p_t.font.bold = True
        p_t.font.color.rgb = RGBColor(248, 250, 252)
        p_t.space_after = Pt(10)

        for b in cdata["bullets"]:
            p_b = tf.add_paragraph()
            p_b.text = "• " + b
            p_b.font.name = "Arial"
            p_b.font.size = Pt(9.5)
            p_b.font.color.rgb = RGBColor(203, 213, 225)
            p_b.space_after = Pt(6)

    # Footer
    foot_shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(6.55), Inches(11.7), Inches(0.48))
    foot_shape.fill.solid()
    foot_shape.fill.fore_color.rgb = RGBColor(30, 41, 59)
    foot_shape.line.color.rgb = RGBColor(51, 65, 85)
    foot_shape.line.width = Pt(1)

    foot_box = slide.shapes.add_textbox(Inches(0.9), Inches(6.58), Inches(11.5), Inches(0.42))
    tf_f = foot_box.text_frame
    p_f = tf_f.paragraphs[0]
    p_f.text = "SUPREME PRODUCTION DIRECTIVE: 20/20 Rules Enforced  |  Strict User Upload Isolation  |  Zero Hallucination  |  100% Deterministic Reproducibility"
    p_f.font.name = "Arial"
    p_f.font.size = Pt(10)
    p_f.font.bold = True
    p_f.font.color.rgb = RGBColor(56, 189, 248)
    p_f.alignment = PP_ALIGN.CENTER

    return slide


def add_slide_20_cloud_security(prs: Presentation):
    """Adds Slide 20: Cloud Security, Render RAM Optimization & 24/7 Zero-Cold-Start Reliability."""
    blank_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank_layout)

    background = slide.background
    fill = background.fill
    fill.solid()
    fill.fore_color.rgb = RGBColor(11, 17, 32)

    top_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(8), Inches(0.35))
    tf_top = top_box.text_frame
    tf_top.word_wrap = True
    p_top = tf_top.paragraphs[0]
    p_top.text = "ENTERPRISE CLOUD ARCHITECTURE & 24/7 RELIABILITY"
    p_top.font.name = "Arial"
    p_top.font.size = Pt(10)
    p_top.font.bold = True
    p_top.font.color.rgb = RGBColor(16, 185, 129)

    keynote_box = slide.shapes.add_textbox(Inches(9.2), Inches(0.4), Inches(3.3), Inches(0.35))
    tf_k = keynote_box.text_frame
    p_k = tf_k.paragraphs[0]
    p_k.text = "PRODUCTION HARDENED"
    p_k.alignment = PP_ALIGN.RIGHT
    p_k.font.name = "Arial"
    p_k.font.size = Pt(10)
    p_k.font.bold = True
    p_k.font.color.rgb = RGBColor(148, 163, 184)

    title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.75), Inches(11.5), Inches(0.75))
    tf_title = title_box.text_frame
    tf_title.word_wrap = True
    p_title = tf_title.paragraphs[0]
    p_title.text = "Cloud Security, Render RAM Optimization & 24/7 Reliability"
    p_title.font.name = "Arial"
    p_title.font.size = Pt(21)
    p_title.font.bold = True
    p_title.font.color.rgb = RGBColor(248, 250, 252)

    p_sub = tf_title.add_paragraph()
    p_sub.text = "Perpetual High Availability, 512MB RAM Leak-Free Operations, Path-Traversal Defense, and Zero-Latency Instant Wakeup."
    p_sub.font.name = "Arial"
    p_sub.font.size = Pt(11)
    p_sub.font.color.rgb = RGBColor(148, 163, 184)

    cards_data = [
        {
            "tag": "ENTERPRISE SECURITY & DEFENSE",
            "tag_color": RGBColor(16, 185, 129),
            "title": "Zero-Trust Path Defense & Secret Isolation",
            "bullets": [
                "Canonical Root Path Verification: Eliminates path traversal on /api/view & /api/download; strictly confines file access to resolved whitelist roots (outputs/, SESSION_ROOT, temp).",
                "Secret Isolation in Transport Headers: Relocated sensitive Gemini API keys to secure x-goog-api-key HTTP headers, eliminating token exposure in proxy logs and referrer headers.",
                "Contextual XSS Neutralization: Sanitizes dynamic table headers, author credits, and study titles via deterministic html.escape(), preserving interactive Plotly charts and NCBI FHIR actions.",
                "Opt-In Access Control: Built-in basic HTTP authentication guard (MANDOROS_AUTH_*) activating strictly when environment credentials exist without breaking open clinical testing."
            ]
        },
        {
            "tag": "RENDER 512MB RAM OPTIMIZATION",
            "tag_color": RGBColor(56, 189, 248),
            "title": "Deterministic Memory & Leak-Free Architecture",
            "bullets": [
                "Deterministic Workbook DOM Destruction: Every openpyxl.load_workbook is wrapped in try...finally: wb.close(), immediately freeing heavy XML/DOM memory trees upon dashboard render.",
                "Zero File-Descriptor Leaks: PDF ingestion wrapped in guarded Python context managers (with open() as stream), ensuring streams are closed instantly after PyPDF extraction on Linux.",
                "Resilient AI Timeout Guards: Strict 60.0s network timeout caps across OpenAI, Anthropic, and Google GenAI SDK clients prevent thread hangs, process accumulation, and worker starvation.",
                "Lightweight Zero-Load Footprint: Operates comfortably within Render's tight 512MB free tier RAM ceiling without requiring heavyweight Celery/Redis workers or external caching daemons."
            ]
        },
        {
            "tag": "24/7 HIGH AVAILABILITY & SPEED",
            "tag_color": RGBColor(245, 158, 11),
            "title": "Perpetual Uptime & Zero Cold-Start Latency",
            "bullets": [
                "Automated Keep-Alive Ping Engine: Dedicated /health heartbeat endpoint probed every 5 minutes (UptimeRobot / GitHub Actions), completely neutralizing Render's 15-min idle container spin-down.",
                "Sub-Second First-Interaction Time: Slashes initial cold-start latency from ~75 seconds down to <1 second, ensuring instant, freeze-free access for clinicians and peer reviewers at all hours.",
                "Multi-Cloud Failover Monitoring: Redundant external ping orchestrators with automated retry loops and email alerts for zero-downtime academic hosting.",
                "Progressive Web App (PWA) Offline Cache: Caches RxNorm, NCBI FHIR, and public drug mappings locally in sessionStorage/localStorage for immediate client-side responsiveness."
            ]
        }
    ]

    card_width = Inches(3.7)
    card_height = Inches(4.7)
    card_gap = Inches(0.3)
    card_top = Inches(1.65)
    left_margin = Inches(0.8)

    for i, cdata in enumerate(cards_data):
        card_left = left_margin + i * (card_width + card_gap)
        shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, card_left, card_top, card_width, card_height)
        shape.fill.solid()
        shape.fill.fore_color.rgb = RGBColor(15, 23, 42)
        shape.line.color.rgb = cdata["tag_color"]
        shape.line.width = Pt(1.5)

        c_box = slide.shapes.add_textbox(card_left + Inches(0.18), card_top + Inches(0.18), card_width - Inches(0.36), card_height - Inches(0.36))
        tf = c_box.text_frame
        tf.word_wrap = True

        p_tag = tf.paragraphs[0]
        p_tag.text = cdata["tag"]
        p_tag.font.name = "Arial"
        p_tag.font.size = Pt(9.5)
        p_tag.font.bold = True
        p_tag.font.color.rgb = cdata["tag_color"]
        p_tag.space_after = Pt(4)

        p_t = tf.add_paragraph()
        p_t.text = cdata["title"]
        p_t.font.name = "Arial"
        p_t.font.size = Pt(13)
        p_t.font.bold = True
        p_t.font.color.rgb = RGBColor(248, 250, 252)
        p_t.space_after = Pt(10)

        for b in cdata["bullets"]:
            p_b = tf.add_paragraph()
            p_b.text = "• " + b
            p_b.font.name = "Arial"
            p_b.font.size = Pt(9.5)
            p_b.font.color.rgb = RGBColor(203, 213, 225)
            p_b.space_after = Pt(6)

    # Footer
    foot_shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(6.55), Inches(11.7), Inches(0.48))
    foot_shape.fill.solid()
    foot_shape.fill.fore_color.rgb = RGBColor(30, 41, 59)
    foot_shape.line.color.rgb = RGBColor(51, 65, 85)
    foot_shape.line.width = Pt(1)

    foot_box = slide.shapes.add_textbox(Inches(0.9), Inches(6.58), Inches(11.5), Inches(0.42))
    tf_f = foot_box.text_frame
    p_f = tf_f.paragraphs[0]
    p_f.text = "PRODUCTION HARDENED: 24/7 Keep-Alive  |  512MB RAM Leak-Free  |  Canonical Path Defense  |  Header Token Isolation  |  <1s Instant Wakeup"
    p_f.font.name = "Arial"
    p_f.font.size = Pt(10)
    p_f.font.bold = True
    p_f.font.color.rgb = RGBColor(16, 185, 129)
    p_f.alignment = PP_ALIGN.CENTER

    return slide


def update_slide_2_agenda_pptx(prs: Presentation):
    """Updates Slide 2 Agenda in PPTX to cover all 20 slides in 3 rich parts."""
    s2 = prs.slides[1]

    card1_text = (
        "PART I: FOUNDATIONS & EXTRACTION\n"
        "1. The Systematic Review Bottleneck & Clinical Need\n"
        "2. System Architecture & 8-Node Pipeline (M-A-N-D-O-R-O-S)\n"
        "3. Stage-1 Atomic Curation (7 Sheets / 88 Fields)\n"
        "4. Verbatim Provenance & Zero-Imputation Guarantee\n"
        "5. Clinical AI Governance & Two-Phase 10/10 Gate"
    )

    card2_text = (
        "PART II: SYNTHESIS & METHODOLOGICAL AUDIT\n"
        "6. Phase-2 Multi-Trial REML & 20 Supreme Rules\n"
        "7. Network Meta-Analysis (NMA) & SUCRA Hierarchy\n"
        "8. TrialMind & RCTMethodologyIE Validity Audit\n"
        "9. In-Silico Synthesis & Virtual Clinical Trials\n"
        "10. User Walkthrough & Google AI Studio BYOK"
    )

    card3_text = (
        "PART III: RESEARCH GAPS, PRISMA & ECOSYSTEM\n"
        "11. Phase 3 Research Gap & Thesis Navigator\n"
        "12. The 5 Pillars of Rigor & Power Calibration\n"
        "13. PRISMA 2020 Intelligence & 4-Stage Flow Diagram\n"
        "14. External Clinical Databases (PubMed, NCT, RxNorm, FHIR)\n"
        "15. Enterprise Cloud Security, 512MB RAM & 24/7 Keep-Alive"
    )

    cards = [
        (s2.shapes[5], card1_text, RGBColor(0, 245, 212)),
        (s2.shapes[6], card2_text, RGBColor(56, 189, 248)),
        (s2.shapes[7], card3_text, RGBColor(192, 132, 252))
    ]
    for shape, text, header_color in cards:
        tf = shape.text_frame
        tf.word_wrap = True
        lines = text.split("\n")
        p0 = tf.paragraphs[0]
        p0.text = lines[0]
        p0.font.name = "Arial"
        p0.font.size = Pt(11)
        p0.font.bold = True
        p0.font.color.rgb = header_color
        p0.space_after = Pt(8)

        p_elems = list(tf._txBody.p_lst)
        for p_elem in p_elems[1:]:
            tf._txBody.remove(p_elem)

        for line in lines[1:]:
            p = tf.add_paragraph()
            p.text = line
            p.font.name = "Arial"
            p.font.size = Pt(9.5)
            p.font.color.rgb = RGBColor(203, 213, 225)
            p.space_after = Pt(4)


# =========================================================================
# HTML SLIDES 16 - 20 (APPEND STRING)
# =========================================================================

HTML_SLIDES_16_TO_20 = """
  <!-- ========================================================================= -->
  <!-- SLIDE 16: THE 5 PILLARS OF ACADEMIC RIGOR & BIOSTATISTICAL CALIBRATION    -->
  <!-- ========================================================================= -->
  <div class="slide" id="slide-five-pillars">
    <div class="slide-header">
      <div>
        <div style="font-size:13px; font-weight:800; color:#C084FC; letter-spacing:0.1em; text-transform:uppercase; margin-bottom:6px;">RESEARCH TRANSLATION &amp; BIOSTATISTICAL RIGOR</div>
        <h2 style="font-size:32px; font-weight:900; color:#F8FAFC; margin:0;">The 5 Pillars of Academic Rigor &amp; Biostatistical Calibration</h2>
        <p style="font-size:14px; color:#94A3B8; margin-top:4px;">End-to-End Methodology: From Cross-Study Evidence Matrix to Deterministic Power Calibration &amp; SPIRIT 2013 Protocol.</p>
      </div>
      <div style="background:rgba(192,132,252,0.15); border:1px solid #C084FC; color:#C084FC; font-weight:800; font-size:12px; padding:6px 16px; border-radius:9999px;">
        THE 5 PILLARS OF RIGOR
      </div>
    </div>

    <div style="display:grid; grid-template-columns:repeat(3, 1fr); gap:24px; flex-grow:1; margin-bottom:24px;">
      <div style="background:rgba(15,23,42,0.85); border:1.5px solid #F59E0B; border-radius:18px; padding:24px; display:flex; flex-direction:column; justify-content:space-between;">
        <div>
          <span style="font-size:11px; font-weight:800; color:#F59E0B; letter-spacing:0.08em; text-transform:uppercase;">PILLARS I &amp; II: DISCOVERY &amp; REALITY GATE</span>
          <h3 style="font-size:18px; font-weight:800; color:#F8FAFC; margin:8px 0 14px 0;">Cross-Study Evidence Matrix &amp; Reality Gate</h3>
          <ul style="color:#CBD5E1; font-size:13px; line-height:1.6; margin-left:18px;">
            <li><strong>Cross-Study Evidence Matrix (Pillar I):</strong> Dynamically aggregates PICO characteristics, comparator arms, patient demographics, and multi-endpoint data across all ingested trials.</li>
            <li><strong>5 Algorithmic Gap Archetypes:</strong> Detects active comparator voids, unmeasured patient-reported outcomes (PROs), high-risk subpopulations (e.g. eGFR &lt; 30 / geriatrics), duration plateaus, and dose-titration voids.</li>
            <li><strong>Live Scholarly Reality Check (Pillar II):</strong> Automates real-time verification queries against ClinicalTrials.gov APIv2, PubMed, and OpenAlex to cross-reference ongoing research.</li>
            <li><strong>Evidence Saturation Classification:</strong> Categorizes candidate hypotheses as Open Unexplored, In-Progress, or Saturated to eliminate redundant academic waste.</li>
          </ul>
        </div>
        <div style="font-size:11px; color:#F59E0B; font-weight:700; border-top:1px solid rgba(245,158,11,0.3); padding-top:8px;">DISCOVERY &amp; REALITY CHECK</div>
      </div>

      <div style="background:rgba(15,23,42,0.85); border:1.5px solid #00F5D4; border-radius:18px; padding:24px; display:flex; flex-direction:column; justify-content:space-between;">
        <div>
          <span style="font-size:11px; font-weight:800; color:#00F5D4; letter-spacing:0.08em; text-transform:uppercase;">PILLAR III: METHODOLOGICAL QUALITY</span>
          <h3 style="font-size:18px; font-weight:800; color:#F8FAFC; margin:8px 0 14px 0;">Cochrane RoB 2.0 &amp; robvis Traffic-Light</h3>
          <ul style="color:#CBD5E1; font-size:13px; line-height:1.6; margin-left:18px;">
            <li><strong>Domain-by-Domain Bias Appraisal:</strong> Programmatically audits Cochrane RoB 2.0 domains (D1: Randomization, D2: Deviations, D3: Missing Outcomes, D4: Measurement, D5: Reporting).</li>
            <li><strong>Verbatim-Anchored Justifications:</strong> Binds every RoB rating to exact chunk-level text quotes extracted from the trial PDF; zero unreferenced judgments.</li>
            <li><strong>robvis-Grade Traffic-Light Visualization:</strong> Generates interactive Cochrane summary matrix and bar charts displaying risk distributions across the trial cohort.</li>
            <li><strong>CONSORT 2010 Reporting Completeness:</strong> Dissects 25-item checklist compliance including sample size prespecification, blinding mechanisms, and ITT fidelity.</li>
          </ul>
        </div>
        <div style="font-size:11px; color:#00F5D4; font-weight:700; border-top:1px solid rgba(0,245,212,0.3); padding-top:8px;">ROB 2.0 &amp; ROBVIS MATRIX</div>
      </div>

      <div style="background:rgba(15,23,42,0.85); border:1.5px solid #C084FC; border-radius:18px; padding:24px; display:flex; flex-direction:column; justify-content:space-between;">
        <div>
          <span style="font-size:11px; font-weight:800; color:#C084FC; letter-spacing:0.08em; text-transform:uppercase;">PILLARS IV &amp; V: PROTOCOL &amp; POWER</span>
          <h3 style="font-size:18px; font-weight:800; color:#F8FAFC; margin:8px 0 14px 0;">FINER Blueprint &amp; Deterministic Power</h3>
          <ul style="color:#CBD5E1; font-size:13px; line-height:1.6; margin-left:18px;">
            <li><strong>FINER Hypothesis Formulation (Pillar IV):</strong> Structures hypotheses satisfying Feasible, Interesting, Novel, Ethical, and Relevant criteria with full academic IMRAD rationale.</li>
            <li><strong>Deterministic Power &amp; Sample Size (Pillar V):</strong> Code-level biostatistical calculation for continuous &amp; binary endpoints; solves for N at alpha=0.05, 80% &amp; 90% power with attrition buffer.</li>
            <li><strong>Superiority &amp; Non-Inferiority Architecture:</strong> Supports two-sample superiority designs and non-inferiority trials with customizable margin (&Delta;_NI) and pooled SD (&sigma;).</li>
            <li><strong>7-Sheet Phase 3 Research Package:</strong> Exports standardized Excel sheets (Evidence Matrix, Gaps, Reality Check, RoB, SAP, Power) plus ready-to-defend Markdown thesis dossier.</li>
          </ul>
        </div>
        <div style="font-size:11px; color:#C084FC; font-weight:700; border-top:1px solid rgba(192,132,252,0.3); padding-top:8px;">80/90% POWER &amp; SPIRIT PROTOCOL</div>
      </div>
    </div>

    <div class="slide-footer">
      <span>MANDOROS — The 5 Pillars of Academic Rigor &amp; Biostatistical Calibration</span>
      <span class="slide-num">SLIDE 16 / 20</span>
    </div>
  </div>

  <!-- ========================================================================= -->
  <!-- SLIDE 17: PRISMA 2020 CLINICAL TRIAL INTELLIGENCE & FLOW ENGINE           -->
  <!-- ========================================================================= -->
  <div class="slide" id="slide-prisma-engine">
    <div class="slide-header">
      <div>
        <div style="font-size:13px; font-weight:800; color:#10B981; letter-spacing:0.1em; text-transform:uppercase; margin-bottom:6px;">SYSTEMATIC REVIEW STANDARDS &amp; FLOW INTEGRITY</div>
        <h2 style="font-size:32px; font-weight:900; color:#F8FAFC; margin:0;">PRISMA 2020 Intelligence &amp; Interactive Flow Architecture</h2>
        <p style="font-size:14px; color:#94A3B8; margin-top:4px;">Transparent Study Selection: 4-Stage Flow Diagram, Automated Deduplication, Zero-FN Screening, and Reporting Auditing.</p>
      </div>
      <div style="background:rgba(16,185,129,0.15); border:1px solid #10B981; color:#10B981; font-weight:800; font-size:12px; padding:6px 16px; border-radius:9999px;">
        PRISMA 2020 CERTIFIED
      </div>
    </div>

    <div style="display:grid; grid-template-columns:repeat(3, 1fr); gap:24px; flex-grow:1; margin-bottom:24px;">
      <div style="background:rgba(15,23,42,0.85); border:1.5px solid #10B981; border-radius:18px; padding:24px; display:flex; flex-direction:column; justify-content:space-between;">
        <div>
          <span style="font-size:11px; font-weight:800; color:#10B981; letter-spacing:0.08em; text-transform:uppercase;">4-STAGE SELECTION ARCHITECTURE</span>
          <h3 style="font-size:18px; font-weight:800; color:#F8FAFC; margin:8px 0 14px 0;">PRISMA 2020 Flow Diagram Engine</h3>
          <ul style="color:#CBD5E1; font-size:13px; line-height:1.6; margin-left:18px;">
            <li><strong>Stage 1 — Identification:</strong> Consolidates literature hits from PubMed/Medline, clinical registers (ClinicalTrials.gov), and manual PDF uploads with automated title/DOI deduplication.</li>
            <li><strong>Stage 2 — Screening:</strong> Systematic screening of titles and abstracts; records evaluated against pre-defined inclusion criteria with quantified exclusion logging.</li>
            <li><strong>Stage 3 — Eligibility:</strong> Full-text appraisal against atomic eligibility properties; every excluded record is tagged with an immutable, transparent exclusion reason.</li>
            <li><strong>Stage 4 — Included:</strong> Final cohort synthesis determining studies eligible for qualitative systematic review and quantitative metafor-grade pooling.</li>
          </ul>
        </div>
        <div style="font-size:11px; color:#10B981; font-weight:700; border-top:1px solid rgba(16,185,129,0.3); padding-top:8px;">4-STAGE TRANSPARENCY PIPELINE</div>
      </div>

      <div style="background:rgba(15,23,42,0.85); border:1.5px solid #38BDF8; border-radius:18px; padding:24px; display:flex; flex-direction:column; justify-content:space-between;">
        <div>
          <span style="font-size:11px; font-weight:800; color:#38BDF8; letter-spacing:0.08em; text-transform:uppercase;">ZERO-FN REASONING MIDDLEWARE</span>
          <h3 style="font-size:18px; font-weight:800; color:#F8FAFC; margin:8px 0 14px 0;">Ternary Screening &amp; Zero-FN Gate</h3>
          <ul style="color:#CBD5E1; font-size:13px; line-height:1.6; margin-left:18px;">
            <li><strong>Ternary Decision Logic (+1, -1, 0):</strong> AI assesses text chunks using strict ternary voting; indeterminate evidence (0) is never prematurely discarded.</li>
            <li><strong>Zero-False-Negative Safeguard:</strong> Ambiguous or borderline trials automatically pass to full-text human referee inspection, preventing accidental exclusion of key evidence.</li>
            <li><strong>Chunk-Level Provenance Anchoring:</strong> Every inclusion/exclusion decision is permanently anchored to document chunk IDs with verbatim justification quotes.</li>
            <li><strong>Multi-Reviewer Emulation:</strong> Replicates dual independent reviewer paradigms with consensus resolution for Cochrane-standard review fidelity.</li>
          </ul>
        </div>
        <div style="font-size:11px; color:#38BDF8; font-weight:700; border-top:1px solid rgba(56,189,248,0.3); padding-top:8px;">ZERO FALSE-NEGATIVE REASONING</div>
      </div>

      <div style="background:rgba(15,23,42,0.85); border:1.5px solid #F43F5E; border-radius:18px; padding:24px; display:flex; flex-direction:column; justify-content:space-between;">
        <div>
          <span style="font-size:11px; font-weight:800; color:#F43F5E; letter-spacing:0.08em; text-transform:uppercase;">COMPLIANCE &amp; VISUALIZATION</span>
          <h3 style="font-size:18px; font-weight:800; color:#F8FAFC; margin:8px 0 14px 0;">PRISMA 2020 Checklist &amp; Dashboard</h3>
          <ul style="color:#CBD5E1; font-size:13px; line-height:1.6; margin-left:18px;">
            <li><strong>27-Item PRISMA 2020 Checklist Auditor:</strong> Evaluates reporting fidelity across Title, Abstract, Introduction, Methods, Results, Discussion, and Funding.</li>
            <li><strong>Stand-Alone Interactive HTML Dashboard:</strong> Renders dynamic SVG/Plotly PRISMA flowcharts with clickable nodes revealing study IDs, counts, and exclusion breakdowns.</li>
            <li><strong>Deterministic Attrition Accounting:</strong> Enforces mathematical consistency across nodes: Identified - Duplicates = Screened; Screened - Excluded = Eligible.</li>
            <li><strong>Publication-Ready Vector &amp; Data Export:</strong> One-click export of PRISMA flowcharts in SVG/PNG and full audit logs in Excel for peer-reviewed journal submission.</li>
          </ul>
        </div>
        <div style="font-size:11px; color:#F43F5E; font-weight:700; border-top:1px solid rgba(244,63,94,0.3); padding-top:8px;">INTERACTIVE PRISMA DASHBOARD</div>
      </div>
    </div>

    <div class="slide-footer">
      <span>MANDOROS — PRISMA 2020 Clinical Trial Intelligence &amp; Flow Architecture</span>
      <span class="slide-num">SLIDE 17 / 20</span>
    </div>
  </div>

  <!-- ========================================================================= -->
  <!-- SLIDE 18: EXTERNAL CLINICAL DATABASES, PUBMED & NCBI FHIR ECOSYSTEM       -->
  <!-- ========================================================================= -->
  <div class="slide" id="slide-clinical-databases">
    <div class="slide-header">
      <div>
        <div style="font-size:13px; font-weight:800; color:#38BDF8; letter-spacing:0.1em; text-transform:uppercase; margin-bottom:6px;">CLINICAL KNOWLEDGE BASES &amp; INTEROPERABILITY</div>
        <h2 style="font-size:32px; font-weight:900; color:#F8FAFC; margin:0;">External Clinical Databases, PubMed &amp; NCBI FHIR Ecosystem</h2>
        <p style="font-size:14px; color:#94A3B8; margin-top:4px;">Live Bidirectional Interoperability: PubMed E-utilities, ClinicalTrials.gov APIv2, NLM RxNorm, and HL7 FHIR R4 ResearchStudy.</p>
      </div>
      <div style="background:rgba(56,189,248,0.15); border:1px solid #38BDF8; color:#38BDF8; font-weight:800; font-size:12px; padding:6px 16px; border-radius:9999px;">
        NCBI FHIR &amp; NIH APIS
      </div>
    </div>

    <div style="display:grid; grid-template-columns:repeat(3, 1fr); gap:24px; flex-grow:1; margin-bottom:24px;">
      <div style="background:rgba(15,23,42,0.85); border:1.5px solid #38BDF8; border-radius:18px; padding:24px; display:flex; flex-direction:column; justify-content:space-between;">
        <div>
          <span style="font-size:11px; font-weight:800; color:#38BDF8; letter-spacing:0.08em; text-transform:uppercase;">BIOMEDICAL LITERATURE ENGINE</span>
          <h3 style="font-size:18px; font-weight:800; color:#F8FAFC; margin:8px 0 14px 0;">PubMed &amp; NCBI E-utilities Integration</h3>
          <ul style="color:#CBD5E1; font-size:13px; line-height:1.6; margin-left:18px;">
            <li><strong>Direct E-utilities Protocol:</strong> Interfaces NCBI Entrez API (esearch, esummary, efetch) for real-time biomedical literature verification.</li>
            <li><strong>PICO Deconstruction &amp; MeSH Expansion:</strong> Automatically decomposes research questions into MeSH ontology descriptors, achieving &gt;= 78% search recall.</li>
            <li><strong>Scholarly Gap Saturation Verification:</strong> Queries Medline to verify if discovered evidence gaps have already been addressed in recent published trials.</li>
            <li><strong>PubMed Central (PMC) BioC Text Mining:</strong> Extracts open-access full-text sections, tables, and XML metadata for automated citation cross-matching.</li>
          </ul>
        </div>
        <div style="font-size:11px; color:#38BDF8; font-weight:700; border-top:1px solid rgba(56,189,248,0.3); padding-top:8px;">NCBI PUBMED LIVE RETRIEVAL</div>
      </div>

      <div style="background:rgba(15,23,42,0.85); border:1.5px solid #F59E0B; border-radius:18px; padding:24px; display:flex; flex-direction:column; justify-content:space-between;">
        <div>
          <span style="font-size:11px; font-weight:800; color:#F59E0B; letter-spacing:0.08em; text-transform:uppercase;">TRIAL REGISTRY &amp; BENCHMARKING</span>
          <h3 style="font-size:18px; font-weight:800; color:#F8FAFC; margin:8px 0 14px 0;">Live ClinicalTrials.gov APIv2 Registry</h3>
          <ul style="color:#CBD5E1; font-size:13px; line-height:1.6; margin-left:18px;">
            <li><strong>Live Registry Synchronization:</strong> Native HTTP client directly queries ClinicalTrials.gov APIv2 REST endpoints without third-party middleware.</li>
            <li><strong>Automated NCT Protocol Benchmarking:</strong> Pulls official registered study protocols by NCT ID to verify pre-specified primary/secondary endpoints vs published outcomes.</li>
            <li><strong>Trial Recruitment &amp; Status Tracking:</strong> Audits active recruiting, completed, active-not-recruiting, and terminated trials across global sponsor portfolios.</li>
            <li><strong>Outcome Reporting Bias Detection:</strong> Flags discrepancies between registered trial registry endpoints and selectively reported journal publications.</li>
          </ul>
        </div>
        <div style="font-size:11px; color:#F59E0B; font-weight:700; border-top:1px solid rgba(245,158,11,0.3); padding-top:8px;">NIH REGISTRY SYNCHRONIZATION</div>
      </div>

      <div style="background:rgba(15,23,42,0.85); border:1.5px solid #10B981; border-radius:18px; padding:24px; display:flex; flex-direction:column; justify-content:space-between;">
        <div>
          <span style="font-size:11px; font-weight:800; color:#10B981; letter-spacing:0.08em; text-transform:uppercase;">STANDARDS &amp; INTEROPERABILITY</span>
          <h3 style="font-size:18px; font-weight:800; color:#F8FAFC; margin:8px 0 14px 0;">NLM RxNorm &amp; HL7 FHIR Interoperability</h3>
          <ul style="color:#CBD5E1; font-size:13px; line-height:1.6; margin-left:18px;">
            <li><strong>NLM RxNorm Drug Normalization:</strong> Client-side integration with rxnav.nlm.nih.gov resolves brand names and dosage forms into canonical RxCUI codes.</li>
            <li><strong>Client-Side Session Caching:</strong> Caches public RxCUI mappings in sessionStorage to minimize API latency and ensure offline browser speed.</li>
            <li><strong>HL7 FHIR R4 ResearchStudy Mapping:</strong> Formats extracted trial evidence into standardized FHIR ResearchStudy JSON-LD clinical trial models.</li>
            <li><strong>NCBI FHIR Interactive Action Badges:</strong> Embedded UI badges enable one-click verification of trial identifiers, regulatory codes, and standardized vocabularies.</li>
          </ul>
        </div>
        <div style="font-size:11px; color:#10B981; font-weight:700; border-top:1px solid rgba(16,185,129,0.3); padding-top:8px;">HL7 FHIR R4 &amp; RXNORM CODING</div>
      </div>
    </div>

    <div class="slide-footer">
      <span>MANDOROS — External Clinical Databases, PubMed &amp; NCBI FHIR Ecosystem</span>
      <span class="slide-num">SLIDE 18 / 20</span>
    </div>
  </div>

  <!-- ========================================================================= -->
  <!-- SLIDE 19: PHASE 2 SCIENTIFIC RESTRUCTURING (20 SUPREME RULES)             -->
  <!-- ========================================================================= -->
  <div class="slide" id="slide-phase2-rules">
    <div class="slide-header">
      <div>
        <div style="font-size:13px; font-weight:800; color:#38BDF8; letter-spacing:0.1em; text-transform:uppercase; margin-bottom:6px;">SCIENTIFIC RESTRUCTURING &amp; PROTOCOL ENFORCEMENT</div>
        <h2 style="font-size:32px; font-weight:900; color:#F8FAFC; margin:0;">Phase 2 Scientific Restructuring &amp; Zero-Contamination Pipeline</h2>
        <p style="font-size:14px; color:#94A3B8; margin-top:4px;">Complete Elimination of Data Blending, Single-Study Pooling Protection, and Standardized Master Extraction Sheet.</p>
      </div>
      <div style="background:rgba(56,189,248,0.15); border:1px solid #38BDF8; color:#38BDF8; font-weight:800; font-size:12px; padding:6px 16px; border-radius:9999px;">
        20 SUPREME RULES
      </div>
    </div>

    <div style="display:grid; grid-template-columns:repeat(3, 1fr); gap:24px; flex-grow:1; margin-bottom:24px;">
      <div style="background:rgba(15,23,42,0.85); border:1.5px solid #10B981; border-radius:18px; padding:24px; display:flex; flex-direction:column; justify-content:space-between;">
        <div>
          <span style="font-size:11px; font-weight:800; color:#10B981; letter-spacing:0.08em; text-transform:uppercase;">RULES 1–5: WORKBOOK INTEGRITY</span>
          <h3 style="font-size:18px; font-weight:800; color:#F8FAFC; margin:8px 0 14px 0;">Standardized Master Excel Sheet</h3>
          <ul style="color:#CBD5E1; font-size:13px; line-height:1.6; margin-left:18px;">
            <li><strong>Strict 5-Section Architecture:</strong> Study Characteristics, Eligibility Criteria, Baseline, Efficacy, and Safety Outcomes.</li>
            <li><strong>Clean Outcome Titles:</strong> Eradicates bracketed sample sizes and demographic noise; preserves pure clinical endpoints.</li>
            <li><strong>Independent Sample Size Columns:</strong> Dedicated 'Sample Analyzed (N)', 'N Randomized', and 'N Baseline Analyzed' fields.</li>
            <li><strong>Dispersion Normalization:</strong> Explicit separation of Mean, SD, SE, Median, Q1, Q3, Adjusted Change, and Treatment Difference.</li>
          </ul>
        </div>
        <div style="font-size:11px; color:#10B981; font-weight:700; border-top:1px solid rgba(16,185,129,0.3); padding-top:8px;">STANDARDIZED MASTER SHEET</div>
      </div>

      <div style="background:rgba(15,23,42,0.85); border:1.5px solid #38BDF8; border-radius:18px; padding:24px; display:flex; flex-direction:column; justify-content:space-between;">
        <div>
          <span style="font-size:11px; font-weight:800; color:#38BDF8; letter-spacing:0.08em; text-transform:uppercase;">RULES 11–15: BIOSTATISTICAL PURITY</span>
          <h3 style="font-size:18px; font-weight:800; color:#F8FAFC; margin:8px 0 14px 0;">Single-Study Protection (Rule 12)</h3>
          <ul style="color:#CBD5E1; font-size:13px; line-height:1.6; margin-left:18px;">
            <li><strong>Single-Trial Safeguard (k=1):</strong> Completely prohibits artificial multi-arm pooling and fabricated I²=0.0% heterogeneity.</li>
            <li><strong>Status Flagging:</strong> Sets analysis status to 'NOT_APPLICABLE_SINGLE_STUDY' and leaves non-applicable metrics blank.</li>
            <li><strong>Shared Control Normalization (Rule 13):</strong> Multi-arm active doses sharing a comparator never double-count control participants.</li>
            <li><strong>Statistical Operators &amp; Exact P-Values (Rule 15):</strong> Eliminates rounding underflow (p=0); separates operator and value.</li>
          </ul>
        </div>
        <div style="font-size:11px; color:#38BDF8; font-weight:700; border-top:1px solid rgba(56,189,248,0.3); padding-top:8px;">RULE 12 BIOSTATISTICAL SAFEGUARDS</div>
      </div>

      <div style="background:rgba(15,23,42,0.85); border:1.5px solid #F43F5E; border-radius:18px; padding:24px; display:flex; flex-direction:column; justify-content:space-between;">
        <div>
          <span style="font-size:11px; font-weight:800; color:#F43F5E; letter-spacing:0.08em; text-transform:uppercase;">RULES 16–20 &amp; UPLOAD ISOLATION</span>
          <h3 style="font-size:18px; font-weight:800; color:#F8FAFC; margin:8px 0 14px 0;">Strict Upload Isolation &amp; Express Lab</h3>
          <ul style="color:#CBD5E1; font-size:13px; line-height:1.6; margin-left:18px;">
            <li><strong>Strict User Upload Isolation:</strong> Automatically purges prior cohort state so newly uploaded files are never blended with past trials.</li>
            <li><strong>current_input_stems Gate:</strong> Processing strictly limited to files present in the active user upload session.</li>
            <li><strong>Adverse-Event Extraction (Rule 16):</strong> Explicitly separates event count, denominator, and percentage.</li>
            <li><strong>Student Express Lab:</strong> Plain-language executive briefs, thesis guidance, and actionable research roadmaps.</li>
          </ul>
        </div>
        <div style="font-size:11px; color:#F43F5E; font-weight:700; border-top:1px solid rgba(244,63,94,0.3); padding-top:8px;">STRICT SESSION ISOLATION</div>
      </div>
    </div>

    <div class="slide-footer">
      <span>MANDOROS — Phase 2 Scientific Restructuring &amp; 20 Supreme Rules</span>
      <span class="slide-num">SLIDE 19 / 20</span>
    </div>
  </div>

  <!-- ========================================================================= -->
  <!-- SLIDE 20: CLOUD SECURITY, RAM OPTIMIZATION & 24/7 ZERO-COLD-START         -->
  <!-- ========================================================================= -->
  <div class="slide" id="slide-cloud-security">
    <div class="slide-header">
      <div>
        <div style="font-size:13px; font-weight:800; color:#10B981; letter-spacing:0.1em; text-transform:uppercase; margin-bottom:6px;">ENTERPRISE CLOUD ARCHITECTURE &amp; 24/7 RELIABILITY</div>
        <h2 style="font-size:32px; font-weight:900; color:#F8FAFC; margin:0;">Cloud Security, Render RAM Optimization &amp; 24/7 Zero-Cold-Start Reliability</h2>
        <p style="font-size:14px; color:#94A3B8; margin-top:4px;">Perpetual High Availability, 512MB RAM Leak-Free Operations, Path-Traversal Defense, and Zero-Latency Instant Wakeup.</p>
      </div>
      <div style="background:rgba(16,185,129,0.15); border:1px solid #10B981; color:#10B981; font-weight:800; font-size:12px; padding:6px 16px; border-radius:9999px;">
        PRODUCTION HARDENED
      </div>
    </div>

    <div style="display:grid; grid-template-columns:repeat(3, 1fr); gap:24px; flex-grow:1; margin-bottom:24px;">
      <div style="background:rgba(15,23,42,0.85); border:1.5px solid #10B981; border-radius:18px; padding:24px; display:flex; flex-direction:column; justify-content:space-between;">
        <div>
          <span style="font-size:11px; font-weight:800; color:#10B981; letter-spacing:0.08em; text-transform:uppercase;">ENTERPRISE SECURITY &amp; DEFENSE</span>
          <h3 style="font-size:18px; font-weight:800; color:#F8FAFC; margin:8px 0 14px 0;">Zero-Trust Path Defense &amp; Secret Isolation</h3>
          <ul style="color:#CBD5E1; font-size:13px; line-height:1.6; margin-left:18px;">
            <li><strong>Canonical Root Path Verification:</strong> Eliminates arbitrary path traversal on /api/view and /api/download; strictly confines file access to resolved whitelist roots (outputs/, SESSION_ROOT, system temp).</li>
            <li><strong>Secret Isolation in Transport Headers:</strong> Relocated sensitive Gemini API keys from URL query strings to secure x-goog-api-key HTTP headers, eliminating token exposure in proxy logs, browser histories, and referrer leaks.</li>
            <li><strong>Contextual XSS Neutralization:</strong> Sanitizes runtime dynamic tables, author credits, and study titles via deterministic html.escape(), while preserving interactive Plotly charts and NCBI FHIR action badges.</li>
            <li><strong>Opt-In Production Access Control:</strong> Built-in basic HTTP authentication guard (MANDOROS_AUTH_USER/PASSWORD) that activates strictly when environment credentials exist without breaking open clinical testing.</li>
          </ul>
        </div>
        <div style="font-size:11px; color:#10B981; font-weight:700; border-top:1px solid rgba(16,185,129,0.3); padding-top:8px;">SEC-01 TO SEC-05 COMPLIANT</div>
      </div>

      <div style="background:rgba(15,23,42,0.85); border:1.5px solid #38BDF8; border-radius:18px; padding:24px; display:flex; flex-direction:column; justify-content:space-between;">
        <div>
          <span style="font-size:11px; font-weight:800; color:#38BDF8; letter-spacing:0.08em; text-transform:uppercase;">RENDER 512MB RAM OPTIMIZATION</span>
          <h3 style="font-size:18px; font-weight:800; color:#F8FAFC; margin:8px 0 14px 0;">Deterministic Memory &amp; Leak-Free Architecture</h3>
          <ul style="color:#CBD5E1; font-size:13px; line-height:1.6; margin-left:18px;">
            <li><strong>Deterministic Workbook DOM Destruction:</strong> Every openpyxl.load_workbook across all 3 phases is wrapped in try...finally: wb.close(), releasing heavy XML/DOM memory trees immediately upon dashboard render.</li>
            <li><strong>Zero File-Descriptor Leaks:</strong> PDF ingestion wrapped in guarded Python context managers (with open() as stream), ensuring streams are closed instantly after PyPDF extraction on Render's Linux file system.</li>
            <li><strong>Resilient AI Timeout Guards:</strong> Added strict 60.0s network timeout caps across OpenAI, Anthropic, and Google GenAI SDK clients to prevent thread hangs, process accumulation, and worker starvation.</li>
            <li><strong>Lightweight Zero-Load Footprint:</strong> Runs comfortably within Render's tight 512MB free tier RAM ceiling without requiring heavyweight Celery/Redis workers or external caching daemons.</li>
          </ul>
        </div>
        <div style="font-size:11px; color:#38BDF8; font-weight:700; border-top:1px solid rgba(56,189,248,0.3); padding-top:8px;">512MB RAM SAFE &amp; LEAK-FREE</div>
      </div>

      <div style="background:rgba(15,23,42,0.85); border:1.5px solid #F59E0B; border-radius:18px; padding:24px; display:flex; flex-direction:column; justify-content:space-between;">
        <div>
          <span style="font-size:11px; font-weight:800; color:#F59E0B; letter-spacing:0.08em; text-transform:uppercase;">24/7 HIGH AVAILABILITY &amp; SPEED</span>
          <h3 style="font-size:18px; font-weight:800; color:#F8FAFC; margin:8px 0 14px 0;">Perpetual Uptime &amp; Zero Cold-Start Latency</h3>
          <ul style="color:#CBD5E1; font-size:13px; line-height:1.6; margin-left:18px;">
            <li><strong>Automated Keep-Alive Ping Engine:</strong> Dedicated /health heartbeat endpoint probed every 5 minutes (UptimeRobot / GitHub Actions cron), completely neutralizing Render's 15-minute idle container spin-down.</li>
            <li><strong>Sub-Second First-Interaction Time:</strong> Slashes initial cold-start latency from ~75 seconds down to &lt;1 second, ensuring instant, freeze-free access for clinicians and peer reviewers at all hours.</li>
            <li><strong>Multi-Cloud Failover Monitoring:</strong> Redundant external ping orchestrators with automated retry loops and email alerts for zero-downtime academic hosting.</li>
            <li><strong>Progressive Web App (PWA) Offline Cache:</strong> Caches RxNorm, NCBI FHIR, and public drug mappings locally in sessionStorage/localStorage for immediate client-side responsiveness.</li>
          </ul>
        </div>
        <div style="font-size:11px; color:#F59E0B; font-weight:700; border-top:1px solid rgba(245,158,11,0.3); padding-top:8px;">&lt;1s RESPONSE &amp; 24/7 UPTIME</div>
      </div>
    </div>

    <div class="slide-footer">
      <span>MANDOROS — Cloud Security, Render RAM Optimization &amp; 24/7 Zero-Cold-Start Reliability</span>
      <span class="slide-num">SLIDE 20 / 20</span>
    </div>
  </div>
"""

HTML_SLIDE_2_GRID = """      <div class="grid-3">
        <div class="card p-1">
          <div class="card-badge" style="background:rgba(0,245,212,0.15); color:#00F5D4;">PART I — FOUNDATIONS &amp; EXTRACTION</div>
          <h2 class="card-h2" style="margin-top:8px;">1. Systematic Review Bottleneck &amp; Need</h2>
          <p class="card-p">Clinical latency, PDF data silos, and verbatim quote provenance solving LLM hallucination.</p>
          <h2 class="card-h2" style="margin-top:14px;">2. System Architecture &amp; 8-Node Pipeline</h2>
          <p class="card-p">M-A-N-D-O-R-O-S process architecture, zero-loss ingestion, and dual-layer consensus AI.</p>
          <h2 class="card-h2" style="margin-top:14px;">3. Stage-1 Curation &amp; 10/10 Quality Gate</h2>
          <p class="card-p">7 relational sheets, 88 canonical fields, 4-operator eligibility, and Two-Phase Master Governance.</p>
        </div>

        <div class="card p-2">
          <div class="card-badge" style="background:rgba(56,189,248,0.15); color:#38BDF8;">PART II — SYNTHESIS &amp; AUDIT</div>
          <h2 class="card-h2" style="margin-top:8px;">4. Multi-Trial REML &amp; SUCRA Hierarchy</h2>
          <p class="card-p">Restricted Maximum Likelihood, Knapp-Hartung, NMA Bucher comparisons, and Monte Carlo SUCRA.</p>
          <h2 class="card-h2" style="margin-top:14px;">5. 20 Supreme Rules &amp; Upload Isolation</h2>
          <p class="card-p">Strict Rule 12 single-study protection, session upload isolation, and standardized Master Excel.</p>
          <h2 class="card-h2" style="margin-top:14px;">6. TrialMind &amp; In-Silico Virtual Trials</h2>
          <p class="card-p">AMIA 4-entity blinding audit, surrogate missing-data splines, and virtual trial simulation.</p>
        </div>

        <div class="card p-3">
          <div class="card-badge" style="background:rgba(168,85,247,0.15); color:#C084FC;">PART III — GAPS, PRISMA &amp; ECOSYSTEM</div>
          <h2 class="card-h2" style="margin-top:8px;">7. Phase 3 &amp; The 5 Pillars of Rigor</h2>
          <p class="card-p">Cross-study evidence matrix, Cochrane RoB 2.0 / robvis, FINER thesis, and SPIRIT protocol.</p>
          <h2 class="card-h2" style="margin-top:14px;">8. PRISMA 2020 4-Stage Flow Engine</h2>
          <p class="card-p">Identification, ternary zero-FN screening, eligibility auditing, and dynamic SVG flowcharts.</p>
          <h2 class="card-h2" style="margin-top:14px;">9. Clinical Databases &amp; 24/7 Cloud Rigor</h2>
          <p class="card-p">Live PubMed E-utilities, ClinicalTrials.gov APIv2, NCBI FHIR R4, and 24/7 zero-cold-start keep-alive.</p>
        </div>
      </div>"""


# =========================================================================
# SYNCHRONIZATION RUNNERS
# =========================================================================

def update_pptx_files():
    for p in PPTX_TARGETS:
        if p.exists():
            print(f"[*] Processing PPTX: {p}")
            prs = Presentation(str(p))

            # 1. Update Slide 2 Agenda
            update_slide_2_agenda_pptx(prs)
            print(f"  [+] Updated Slide 2 Agenda with 20-slide Master Outline")

            # 2. Reset slides beyond Slide 15 to ensure exact canonical order
            # Keep slides 1-15 (indices 0-14)
            while len(prs.slides) > 15:
                del_idx = len(prs.slides) - 1
                rId = prs.slides._sldIdLst[del_idx].rId
                prs.part.drop_rel(rId)
                del prs.slides._sldIdLst[del_idx]

            # 3. Add Slides 16 - 20 in exact order
            add_slide_16_five_pillars(prs)
            print(f"  [+] Added Slide 16: The 5 Pillars of Rigor & Power Calibration")

            add_slide_17_prisma_engine(prs)
            print(f"  [+] Added Slide 17: PRISMA 2020 Flow Diagram & Intelligence")

            add_slide_18_clinical_databases(prs)
            print(f"  [+] Added Slide 18: External Clinical Databases, PubMed & NCBI FHIR")

            add_slide_19_phase2_rules(prs)
            print(f"  [+] Added Slide 19: Phase 2 Scientific Restructuring & 20 Supreme Rules")

            add_slide_20_cloud_security(prs)
            print(f"  [+] Added Slide 20: Cloud Security, Render RAM & 24/7 Zero-Cold-Start")

            prs.save(str(p))
            print(f"[+] Successfully saved PPTX: {p} (Total slides: {len(prs.slides)})")


def update_html_files():
    for h in HTML_TARGETS:
        if h.exists():
            print(f"[*] Processing HTML: {h}")
            content = h.read_text(encoding="utf-8")

            # 1. Update Slide 2 Grid content
            idx_s2_grid_start = content.find('<div class="grid-3">')
            if idx_s2_grid_start != -1:
                idx_s2_grid_end = content.find('</div>\n    </div>\n\n    <div class="slide-footer">', idx_s2_grid_start)
                if idx_s2_grid_end != -1:
                    content = content[:idx_s2_grid_start] + HTML_SLIDE_2_GRID + content[idx_s2_grid_end + 6:]
                    print(f"  [+] Updated Slide 2 Agenda grid in {h.name}")

            # 2. Re-cut slides from Slide 16 onwards
            # Find the end of Slide 15 (id="slide-phase3")
            idx_p3 = content.find('id="slide-phase3"')
            if idx_p3 != -1:
                # Find the footer of slide 15
                idx_p3_end = content.find('</div>\n  </div>', idx_p3)
                if idx_p3_end != -1:
                    # Clean everything after Slide 15 up to </body>
                    idx_body = content.find('</body>', idx_p3_end)
                    if idx_body != -1:
                        cut_point = idx_p3_end + len('</div>\n  </div>')
                        content = content[:cut_point] + "\n" + HTML_SLIDES_16_TO_20 + "\n</body>\n</html>\n"
                        print(f"  [+] Spliced Slides 16 - 20 into {h.name}")

            # 3. Normalize all slide footers to / 20
            def repl_footer(m):
                num = m.group(1)
                return f"SLIDE {num} / 20"
            content = re.sub(r'SLIDE (\d+) / (?:12|16|17|20)', repl_footer, content)

            h.write_text(content, encoding="utf-8")
            print(f"[+] Successfully updated and saved HTML: {h.name}")


def main():
    print("=== MANDOROS Academic Keynote Presentation Suite Synchronizer ===")
    update_pptx_files()
    update_html_files()
    print("=== Complete Synchronization to 20-Slide Master Deck Finished ===")


if __name__ == "__main__":
    main()
