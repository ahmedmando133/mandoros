# -*- coding: utf-8 -*-
"""
MANDOROS Presentation Suite Synchronizer
Permanently updates both PowerPoint (.pptx) and HTML (.html) presentations
with Slides 13, 14, 15, and 16 across the repository.
"""

import os
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


def add_slide_15_phase3(prs: Presentation):
    """Adds Slide 15: Phase 3 Research Gap & Thesis Navigator."""
    blank_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank_layout)

    # Dark background
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

    # Top right Keynote badge
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

    # 3. Three Radiant Cards
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


def add_slide_16_phase2_rules(prs: Presentation):
    """Adds Slide 16: Phase 2 Scientific Restructuring & 20 Supreme Rules."""
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
    p_top.text = "SCIENTIFIC RESTRUCTURING & PROTOCOL ENFORCEMENT"
    p_top.font.name = "Arial"
    p_top.font.size = Pt(10)
    p_top.font.bold = True
    p_top.font.color.rgb = RGBColor(56, 189, 248) # Sky Blue

    # Keynote badge
    keynote_box = slide.shapes.add_textbox(Inches(9.2), Inches(0.4), Inches(3.3), Inches(0.35))
    tf_k = keynote_box.text_frame
    p_k = tf_k.paragraphs[0]
    p_k.text = "20 SUPREME RULES"
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
            "tag_color": RGBColor(16, 185, 129), # Emerald
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
            "tag_color": RGBColor(56, 189, 248), # Sky Blue
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
            "tag_color": RGBColor(244, 63, 94), # Coral / Rose
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


HTML_SLIDES_APPEND = """
  <!-- ========================================================================= -->
  <!-- SLIDE 13: CLINICAL AI GOVERNANCE & ARCHITECTURE                           -->
  <!-- ========================================================================= -->
  <div class="slide" id="slide-governance">
    <div class="slide-header">
      <div>
        <div style="font-size:13px; font-weight:800; color:#00F5D4; letter-spacing:0.1em; text-transform:uppercase; margin-bottom:6px;">CLINICAL AI GOVERNANCE &amp; ARCHITECTURE</div>
        <h2 style="font-size:32px; font-weight:900; color:#F8FAFC; margin:0;">Two-Phase Architecture &amp; 10/10 Programmatic Quality Gate</h2>
        <p style="font-size:14px; color:#94A3B8; margin-top:4px;">Enforcing Supreme Master Protocols on top of Dynamic Clinical Skills for Zero-Hallucination Evidence Synthesis.</p>
      </div>
      <div style="background:rgba(56,189,248,0.15); border:1px solid #38BDF8; color:#38BDF8; font-weight:800; font-size:12px; padding:6px 16px; border-radius:9999px;">
        MANDOROS PROTOCOL v2.0
      </div>
    </div>

    <div style="display:grid; grid-template-columns:repeat(3, 1fr); gap:24px; flex-grow:1; margin-bottom:24px;">
      <div style="background:rgba(15,23,42,0.85); border:1.5px solid #EF4444; border-radius:18px; padding:24px; display:flex; flex-direction:column; justify-content:space-between;">
        <div>
          <span style="font-size:11px; font-weight:800; color:#EF4444; letter-spacing:0.08em; text-transform:uppercase;">TIER 1: SUPREME LAW</span>
          <h3 style="font-size:18px; font-weight:800; color:#F8FAFC; margin:8px 0 14px 0;">Master Protocols (Non-Negotiable)</h3>
          <ul style="color:#CBD5E1; font-size:13px; line-height:1.6; margin-left:18px;">
            <li><strong>Phase 1 Extraction:</strong> 35 mandatory rules, zero duplication, PICO alignment, and CONSORT cell-level data normalization.</li>
            <li><strong>Phase 2 Meta-Analysis:</strong> 21 verified worksheets, Cochrane RoB 2.0 (5 domains), and GRADE certainty framework.</li>
            <li><strong>Absolute Authority:</strong> Tier 1 protocols override general skills or external LLM defaults 100% without exception.</li>
            <li><strong>Zero Assumption Policy:</strong> Original research PDF is the supreme source of truth; zero extrapolation.</li>
          </ul>
        </div>
        <div style="font-size:11px; color:#EF4444; font-weight:700; border-top:1px solid rgba(239,68,68,0.3); padding-top:8px;">NON-NEGOTIABLE ARCHITECTURAL LAW</div>
      </div>

      <div style="background:rgba(15,23,42,0.85); border:1.5px solid #38BDF8; border-radius:18px; padding:24px; display:flex; flex-direction:column; justify-content:space-between;">
        <div>
          <span style="font-size:11px; font-weight:800; color:#38BDF8; letter-spacing:0.08em; text-transform:uppercase;">TIER 2: TECHNICAL MUSCLE</span>
          <h3 style="font-size:18px; font-weight:800; color:#F8FAFC; margin:8px 0 14px 0;">Clinical Skills Library (Execution)</h3>
          <ul style="color:#CBD5E1; font-size:13px; line-height:1.6; margin-left:18px;">
            <li><strong>Extraction Skills (Phase 1):</strong> 'pdf' (spatial table extraction), 'clinical-reports' (AE taxonomy), 'clinicaltrials-database'.</li>
            <li><strong>Biostatistical Skills (Phase 2):</strong> 'statistical-analysis' (APA reporting), 'statsmodels' (mixed models, meta-regression).</li>
            <li><strong>Decision Support &amp; Review:</strong> 'clinical-decision-support' (evidence profiles) and 'peer-review' (CONSORT compliance).</li>
            <li><strong>Dynamic Runtime Injection:</strong> Injected directly into backend LLM request-response middleware.</li>
          </ul>
        </div>
        <div style="font-size:11px; color:#38BDF8; font-weight:700; border-top:1px solid rgba(56,189,248,0.3); padding-top:8px;">HIGH-PRECISION SPECIALIST TOOLS</div>
      </div>

      <div style="background:rgba(15,23,42,0.85); border:1.5px solid #10B981; border-radius:18px; padding:24px; display:flex; flex-direction:column; justify-content:space-between;">
        <div>
          <span style="font-size:11px; font-weight:800; color:#10B981; letter-spacing:0.08em; text-transform:uppercase;">QUALITY GATE: 10/10</span>
          <h3 style="font-size:18px; font-weight:800; color:#F8FAFC; margin:8px 0 14px 0;">Deterministic Validation &amp; Retry Loop</h3>
          <ul style="color:#CBD5E1; font-size:13px; line-height:1.6; margin-left:18px;">
            <li><strong>Hard Programmatic Quality Gate:</strong> Validates output against strict JSON schemas (phase1_schema &amp; phase2_schema).</li>
            <li><strong>Automated Self-Correction Loop:</strong> Feeds schema validation errors back to LLM for instant automated self-repair.</li>
            <li><strong>Mathematical Sanity Verification:</strong> Enforces I² in [0, 100], τ² &gt;= 0, CI lower &lt;= CI upper, and positive ratio scales.</li>
            <li><strong>Path Agnosticism:</strong> 100% relative path resolution guaranteed across Windows dev and Render Linux cloud.</li>
          </ul>
        </div>
        <div style="font-size:11px; color:#10B981; font-weight:700; border-top:1px solid rgba(16,185,129,0.3); padding-top:8px;">DETERMINISTIC RETRY RESILIENCE</div>
      </div>
    </div>

    <div class="slide-footer">
      <span>MANDOROS — Clinical AI Governance &amp; Deterministic Architecture</span>
      <span class="slide-num">SLIDE 13 / 16</span>
    </div>
  </div>

  <!-- ========================================================================= -->
  <!-- SLIDE 14: EVIDENCE SYNTHESIS & METHODOLOGICAL AUDIT (TRIALMIND & RCTMETHOD)-->
  <!-- ========================================================================= -->
  <div class="slide" id="slide-trialmind">
    <div class="slide-header">
      <div>
        <div style="font-size:13px; font-weight:800; color:#00F5D4; letter-spacing:0.1em; text-transform:uppercase; margin-bottom:6px;">EVIDENCE SYNTHESIS &amp; DEEP METHODOLOGICAL AUDIT</div>
        <h2 style="font-size:32px; font-weight:900; color:#F8FAFC; margin:0;">Unified 4-Layer Clinical Evidence &amp; Methodological Audit Engine</h2>
        <p style="font-size:14px; color:#94A3B8; margin-top:4px;">Production Web Integration: Nature npj Digital Medicine 2025 &amp; AMIA / CONSORT 2010 Verification Gates.</p>
      </div>
      <div style="background:rgba(16,185,129,0.15); border:1px solid #10B981; color:#10B981; font-weight:800; font-size:12px; padding:6px 16px; border-radius:9999px;">
        TRIALMIND &amp; RCTMETHODOLOGYIE
      </div>
    </div>

    <div style="display:grid; grid-template-columns:repeat(3, 1fr); gap:24px; flex-grow:1; margin-bottom:24px;">
      <div style="background:rgba(15,23,42,0.85); border:1.5px solid #10B981; border-radius:18px; padding:24px; display:flex; flex-direction:column; justify-content:space-between;">
        <div>
          <span style="font-size:11px; font-weight:800; color:#10B981; letter-spacing:0.08em; text-transform:uppercase;">LAYER 3: EVIDENCE SYNTHESIS</span>
          <h3 style="font-size:18px; font-weight:800; color:#F8FAFC; margin:8px 0 14px 0;">TrialMind Synthesis Engine (Nature npj 2025)</h3>
          <ul style="color:#CBD5E1; font-size:13px; line-height:1.6; margin-left:18px;">
            <li><strong>PICO Deconstruction:</strong> Formalizes PICO, prunes noise terms, expands MeSH synonyms for &gt;= 78% search recall.</li>
            <li><strong>Atomic Eligibility Builder:</strong> Dissects trial goals into single testable inclusion and exclusion properties.</li>
            <li><strong>Ternary Screening (+1, -1, 0):</strong> Score 0 never eliminates an article; passes to full-text review (Zero-FN safeguard).</li>
            <li><strong>Chunk-Anchored Extraction:</strong> Text partitioned into chunks; claims unanchored to chunks are rejected.</li>
            <li><strong>PRISMA 2020 Flow:</strong> Automated flow tracking from identification to final inclusion.</li>
          </ul>
        </div>
        <div style="font-size:11px; color:#10B981; font-weight:700; border-top:1px solid rgba(16,185,129,0.3); padding-top:8px;">NATURE NPJ DIGITAL MEDICINE 2025</div>
      </div>

      <div style="background:rgba(15,23,42,0.85); border:1.5px solid #38BDF8; border-radius:18px; padding:24px; display:flex; flex-direction:column; justify-content:space-between;">
        <div>
          <span style="font-size:11px; font-weight:800; color:#38BDF8; letter-spacing:0.08em; text-transform:uppercase;">LAYER 4: METHODOLOGICAL AUDIT</span>
          <h3 style="font-size:18px; font-weight:800; color:#F8FAFC; margin:8px 0 14px 0;">RCTMethodologyIE Validity Gate (AMIA 2022)</h3>
          <ul style="color:#CBD5E1; font-size:13px; line-height:1.6; margin-left:18px;">
            <li><strong>4-Entity Blinding Auditor:</strong> Independent dissection across Patients, Care Providers, Assessors, and Statisticians.</li>
            <li><strong>Granular Randomization Extractor:</strong> Sequence generation (computer/IWRS), subtype (Block/Stratified), and allocation ratios.</li>
            <li><strong>Allocation Concealment Auditor:</strong> Centralized pharmacy, IWRS/IVRS, and SNOSE mechanisms against selection bias.</li>
            <li><strong>Power &amp; Sample Size Validator:</strong> Cross-checks planned N vs actual enrollment vs analyzed cohort.</li>
            <li><strong>Trial Architecture Classifier:</strong> Parallel Group, Crossover, Factorial; Phase 1–4; Superiority/Non-inferiority.</li>
          </ul>
        </div>
        <div style="font-size:11px; color:#38BDF8; font-weight:700; border-top:1px solid rgba(56,189,248,0.3); padding-top:8px;">AMIA 2022 / PMC10148349 RIGOR</div>
      </div>

      <div style="background:rgba(15,23,42,0.85); border:1.5px solid #F59E0B; border-radius:18px; padding:24px; display:flex; flex-direction:column; justify-content:space-between;">
        <div>
          <span style="font-size:11px; font-weight:800; color:#F59E0B; letter-spacing:0.08em; text-transform:uppercase;">VERIFICATION GATES: 10/10</span>
          <h3 style="font-size:18px; font-weight:800; color:#F8FAFC; margin:8px 0 14px 0;">Live Web Middleware &amp; Deterministic Guard</h3>
          <ul style="color:#CBD5E1; font-size:13px; line-height:1.6; margin-left:18px;">
            <li><strong>Verbatim Verification Hook:</strong> Server-side validator checks quotes against text chunks. Zero hallucination guaranteed.</li>
            <li><strong>Deterministic Code Interpreter:</strong> Strictly eliminates LLM mental math. Pure Python calculates SE, CIs, and rates.</li>
            <li><strong>Algorithmic Cochrane RoB 2.0:</strong> Synthesizes extracted features into formal domains (D1–D5) with justifications.</li>
            <li><strong>Production Web Integration:</strong> Planted in app.py so every live web visitor automatically executes this pipeline.</li>
          </ul>
        </div>
        <div style="font-size:11px; color:#F59E0B; font-weight:700; border-top:1px solid rgba(245,158,11,0.3); padding-top:8px;">PRODUCTION RUNTIME VALIDATION</div>
      </div>
    </div>

    <div class="slide-footer">
      <span>MANDOROS — Evidence Synthesis &amp; Deep Methodological Audit</span>
      <span class="slide-num">SLIDE 14 / 16</span>
    </div>
  </div>

  <!-- ========================================================================= -->
  <!-- SLIDE 15: PHASE 3 RESEARCH GAP & THESIS NAVIGATOR                         -->
  <!-- ========================================================================= -->
  <div class="slide" id="slide-phase3">
    <div class="slide-header">
      <div>
        <div style="font-size:13px; font-weight:800; color:#C084FC; letter-spacing:0.1em; text-transform:uppercase; margin-bottom:6px;">RESEARCH TRANSLATION &amp; THESIS ARCHITECTURE</div>
        <h2 style="font-size:32px; font-weight:900; color:#F8FAFC; margin:0;">Phase 3 — Research Gap &amp; Thesis Navigator Engine</h2>
        <p style="font-size:14px; color:#94A3B8; margin-top:4px;">Autonomous Clinical Research Planning: From Unresolved Evidence Gaps to Actionable FINER Theses &amp; SPIRIT Protocols.</p>
      </div>
      <div style="background:rgba(192,132,252,0.15); border:1px solid #C084FC; color:#C084FC; font-weight:800; font-size:12px; padding:6px 16px; border-radius:9999px;">
        PHASE 3 BLUEPRINT
      </div>
    </div>

    <div style="display:grid; grid-template-columns:repeat(3, 1fr); gap:24px; flex-grow:1; margin-bottom:24px;">
      <div style="background:rgba(15,23,42,0.85); border:1.5px solid #F59E0B; border-radius:18px; padding:24px; display:flex; flex-direction:column; justify-content:space-between;">
        <div>
          <span style="font-size:11px; font-weight:800; color:#F59E0B; letter-spacing:0.08em; text-transform:uppercase;">PILLARS I &amp; II: MAPPING &amp; REALITY CHECK</span>
          <h3 style="font-size:18px; font-weight:800; color:#F8FAFC; margin:8px 0 14px 0;">Evidence Matrix &amp; Scholarly Check</h3>
          <ul style="color:#CBD5E1; font-size:13px; line-height:1.6; margin-left:18px;">
            <li><strong>Cross-Study Evidence Matrix:</strong> Aggregates PICO, sample sizes, and endpoints across multi-trial cohorts.</li>
            <li><strong>5 Discovered Gap Archetypes:</strong> Unresolved head-to-head comparisons, biomarker subpopulation gaps, underrepresented cohorts, dose optimization, and safety signals.</li>
            <li><strong>Scholarly Reality Check:</strong> Automated query validation via ClinicalTrials.gov APIv2 and PubMed for ongoing trial status.</li>
            <li><strong>Novelty &amp; Feasibility Gate:</strong> Classifies detected gaps as Open Unexplored, In-Progress, or Saturated to prevent redundant research.</li>
          </ul>
        </div>
        <div style="font-size:11px; color:#F59E0B; font-weight:700; border-top:1px solid rgba(245,158,11,0.3); padding-top:8px;">DISCOVERY &amp; REALITY CHECK</div>
      </div>

      <div style="background:rgba(15,23,42,0.85); border:1.5px solid #00F5D4; border-radius:18px; padding:24px; display:flex; flex-direction:column; justify-content:space-between;">
        <div>
          <span style="font-size:11px; font-weight:800; color:#00F5D4; letter-spacing:0.08em; text-transform:uppercase;">PILLARS III &amp; IV: QUALITY &amp; FORMULATION</span>
          <h3 style="font-size:18px; font-weight:800; color:#F8FAFC; margin:8px 0 14px 0;">Methodological Audit &amp; Thesis Blueprint</h3>
          <ul style="color:#CBD5E1; font-size:13px; line-height:1.6; margin-left:18px;">
            <li><strong>Algorithmic Cochrane RoB 2.0:</strong> Evaluates 5 core domains of bias with automated text-anchored justifications.</li>
            <li><strong>CONSORT 2010 Compliance Scoring:</strong> Dissects reporting transparency across randomization, blinding, and attrition.</li>
            <li><strong>FINER Research Hypothesis Architect:</strong> Formulates Feasible, Interesting, Novel, Ethical, and Relevant thesis proposals.</li>
            <li><strong>Structured Academic IMRAD Outline:</strong> Formats background rationale, specific primary/secondary aims, and clinical implications.</li>
          </ul>
        </div>
        <div style="font-size:11px; color:#00F5D4; font-weight:700; border-top:1px solid rgba(0,245,212,0.3); padding-top:8px;">ROB 2.0 &amp; FINER PROPOSAL</div>
      </div>

      <div style="background:rgba(15,23,42,0.85); border:1.5px solid #C084FC; border-radius:18px; padding:24px; display:flex; flex-direction:column; justify-content:space-between;">
        <div>
          <span style="font-size:11px; font-weight:800; color:#C084FC; letter-spacing:0.08em; text-transform:uppercase;">PILLAR V &amp; EXPORTS: BIOSTATISTICS</span>
          <h3 style="font-size:18px; font-weight:800; color:#F8FAFC; margin:8px 0 14px 0;">Protocol Outline &amp; Biostatistical Planning</h3>
          <ul style="color:#CBD5E1; font-size:13px; line-height:1.6; margin-left:18px;">
            <li><strong>Deterministic Power &amp; Sample Size:</strong> Calculates required N for alpha=0.05, 80% &amp; 90% power with attrition margin.</li>
            <li><strong>Statistical Analysis Plan (SAP):</strong> Prespecified ANCOVA / mixed-effects model, primary estimand, and sensitivity checks.</li>
            <li><strong>Standardized 7-Sheet Phase 3 Research Package:</strong> Exports full evidence matrix, gap inventory, reality check, and protocol plan.</li>
            <li><strong>Markdown Thesis Dossier:</strong> Ready-to-publish academic document for thesis defense, grant proposals, and IRB submissions.</li>
          </ul>
        </div>
        <div style="font-size:11px; color:#C084FC; font-weight:700; border-top:1px solid rgba(192,132,252,0.3); padding-top:8px;">80/90% POWER &amp; SPIRIT PROTOCOL</div>
      </div>
    </div>

    <div class="slide-footer">
      <span>MANDOROS — Phase 3 Research Gap &amp; Thesis Navigator</span>
      <span class="slide-num">SLIDE 15 / 16</span>
    </div>
  </div>

  <!-- ========================================================================= -->
  <!-- SLIDE 16: PHASE 2 SCIENTIFIC RESTRUCTURING (20 SUPREME RULES)             -->
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
      <span class="slide-num">SLIDE 16 / 16</span>
    </div>
  </div>
"""


def update_pptx_files():
    for p in PPTX_TARGETS:
        if p.exists():
            print(f"[*] Processing PPTX: {p}")
            prs = Presentation(str(p))
            existing_titles = []
            for s in prs.slides:
                for sh in s.shapes:
                    if sh.has_text_frame and sh.text_frame.text:
                        existing_titles.append(sh.text_frame.text)

            # Check and add Slide 15
            if not any("Phase 3 — Research Gap" in t for t in existing_titles):
                add_slide_15_phase3(prs)
                print(f"  [+] Added Slide 15 to {p.name}")
            else:
                print(f"  [-] Slide 15 already present in {p.name}")

            # Check and add Slide 16
            if not any("Phase 2 Scientific Restructuring" in t for t in existing_titles):
                add_slide_16_phase2_rules(prs)
                print(f"  [+] Added Slide 16 to {p.name}")
            else:
                print(f"  [-] Slide 16 already present in {p.name}")

            prs.save(str(p))
            print(f"[+] Successfully saved PPTX: {p} (Total slides: {len(prs.slides)})")


def update_html_files():
    for h in HTML_TARGETS:
        if h.exists():
            print(f"[*] Processing HTML: {h}")
            content = h.read_text(encoding="utf-8")
            if "slide-phase3" not in content and "slide-phase2-rules" not in content:
                # Update SLIDE 12 / 12 footer to SLIDE 12 / 16
                content = content.replace("SLIDE 12 / 12", "SLIDE 12 / 16")
                # Insert new slides before </body>
                if "</body>" in content:
                    content = content.replace("</body>", HTML_SLIDES_APPEND + "\n</body>")
                    h.write_text(content, encoding="utf-8")
                    print(f"[+] Successfully appended Slides 13, 14, 15, 16 to {h.name}")
                else:
                    print(f"[!] Warning: </body> tag not found in {h}")
            else:
                print(f"[-] Slides already present in {h.name}")


def main():
    print("=== MANDOROS Presentation Suite Synchronizer ===")
    update_pptx_files()
    update_html_files()
    print("=== Synchronization Complete ===")


if __name__ == "__main__":
    main()
