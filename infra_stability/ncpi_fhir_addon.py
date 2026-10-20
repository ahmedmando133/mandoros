"""
MANDOROS - NIH NCPI / HL7 FHIR (EBMonFHIR) Zero-Server-Load Add-on
Frontend Explanatory Pillar, Phase 1 Multi-Format Export (JSON, Excel, Dashboard),
Phase 2 RxNorm Tagging, and Phase 3 ClinicalTrials.gov Side-by-Side Verification.

100% Client-Side Vanilla JavaScript (Zero Server RAM / Zero Backend Mutation).
All UI copy rendered in high-impact, academic English.
"""

from __future__ import annotations

import os


def get_ncpi_fhir_head_tags() -> str:
    """
    Returns head tags and client-side JavaScript module injection for the NCPI/FHIR Add-on.
    Inlines static/ncpiFhirAddon.js content or provides script tag for offline/CDN resilience.
    """
    js_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "ncpiFhirAddon.js")
    js_content = ""
    if os.path.exists(js_path):
        try:
            with open(js_path, "r", encoding="utf-8") as f:
                js_content = f.read()
        except Exception:
            js_content = ""

    return f"""
    <!-- MANDOROS NIH NCPI / HL7 FHIR Add-on Stack -->
    <style>
      .mandoros-ncpi-fhir-tool {{
        transition: all 0.25s ease;
      }}
      .ncpi-hidden {{
        display: none !important;
      }}
      .ncpi-switch input:checked + .ncpi-slider {{
        background: linear-gradient(135deg, #8B5CF6, #6D28D9);
      }}
      .ncpi-switch input:checked + .ncpi-slider:before {{
        transform: translateX(20px);
      }}
    </style>
    <script>
    {js_content}
    </script>
    """


def render_ncpi_fhir_pillar_html() -> str:
    """
    Renders the Frontend Explanatory Pillar in academic English
    with the 3 Mini-Pillar Highlights and the Optional Master Toggle.
    """
    return """
    <img src="data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg'></svg>"
         onload="if(!window.ncpiFhirAddonLoaded){window.ncpiFhirAddonLoaded=true;var s=document.createElement('script');s.src='/ncpiFhirAddon.js';s.async=true;document.head.appendChild(s);}"
         style="display:none;" />
    <div class="mandoros-ncpi-pillar-container" style="
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.95) 0%, rgba(46, 16, 101, 0.4) 50%, rgba(15, 23, 42, 0.95) 100%);
        border: 1.5px solid rgba(139, 92, 246, 0.45);
        border-radius: 16px;
        padding: 18px 22px;
        margin: 0 0 18px 0;
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.45), 0 0 20px rgba(139, 92, 246, 0.15);
        backdrop-filter: blur(14px);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    ">
      <!-- Top Row: Title, Subtitle & Master Toggle -->
      <div style="display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 14px; border-bottom: 1px solid rgba(139, 92, 246, 0.25); padding-bottom: 12px; margin-bottom: 14px;">
        <div style="flex: 1; min-width: 300px;">
          <div style="display: flex; align-items: center; gap: 10px;">
            <div style="width: 32px; height: 32px; border-radius: 9px; background: rgba(139, 92, 246, 0.2); border: 1px solid #8B5CF6; display: flex; align-items: center; justify-content: center; font-size: 16px;">
              🧬
            </div>
            <div>
              <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
                <span style="color: #F8FAFC; font-weight: 800; font-size: 15px; letter-spacing: -0.01em;">
                  Cloud Interoperability &amp; Evidence Standards (NIH NCPI &amp; HL7 FHIR Add-on — Optional)
                </span>
                <span style="background: rgba(16, 185, 129, 0.2); border: 1px solid #10B981; color: #34D399; padding: 2px 8px; border-radius: 9999px; font-size: 10.5px; font-weight: 700;">
                  Zero-Server-Load (100% Client-Side)
                </span>
              </div>
              <div style="color: #CBD5E1; font-size: 12px; margin-top: 3px; line-height: 1.4;">
                An on-demand standard layer mapping the 88 atomic fields into NIH NCPI &amp; HL7 FHIR (EBMonFHIR) specifications, harmonizing global drug codes via NIH RxNorm, and detecting outcome reporting bias with zero server overhead.
              </div>
            </div>
          </div>
        </div>

        <!-- Master Toggle Switch -->
        <div style="display: flex; align-items: center; gap: 10px; background: rgba(30, 41, 59, 0.7); border: 1px solid rgba(139, 92, 246, 0.35); padding: 6px 14px; border-radius: 9999px;">
          <label style="display: flex; align-items: center; gap: 8px; cursor: pointer; margin: 0;">
            <input type="checkbox" id="ncpi-master-toggle" onchange="window.toggleNcpiAddon(this.checked)" checked style="
                width: 16px;
                height: 16px;
                accent-color: #8B5CF6;
                cursor: pointer;
            ">
            <span style="color: #E2E8F0; font-size: 12px; font-weight: 700;">
              Enable Global NIH NCPI / HL7 FHIR Interoperability Tools
            </span>
          </label>
        </div>
      </div>

      <!-- 3 Mini-Pillar Highlights -->
      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 12px;">
        <!-- Card 1: Phase 1 -->
        <div style="
            background: rgba(30, 41, 59, 0.55);
            border: 1px solid rgba(56, 189, 248, 0.25);
            border-left: 3px solid #38BDF8;
            border-radius: 10px;
            padding: 10px 14px;
        ">
          <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px;">
            <span style="color: #38BDF8; font-size: 11px; font-weight: 800; text-transform: uppercase;">
              Phase 1 · Multi-Format FHIR Export
            </span>
            <span style="font-size: 12px;">📤</span>
          </div>
          <div style="color: #F8FAFC; font-size: 12.5px; font-weight: 700; margin-bottom: 3px;">
            HL7 FHIR JSON, Relational Excel (.xlsx) &amp; Dashboard
          </div>
          <div style="color: #94A3B8; font-size: 11px; line-height: 1.4;">
            Instant 1-click transformation of all 88 atomic fields into HL7 FHIR (JSON, Excel workbook &amp; interactive dashboard) conforming to ResearchStudy, EvidenceVariable, and Evidence resources.
          </div>
        </div>

        <!-- Card 2: Phase 2 -->
        <div style="
            background: rgba(30, 41, 59, 0.55);
            border: 1px solid rgba(16, 185, 129, 0.25);
            border-left: 3px solid #10B981;
            border-radius: 10px;
            padding: 10px 14px;
        ">
          <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px;">
            <span style="color: #34D399; font-size: 11px; font-weight: 800; text-transform: uppercase;">
              Phase 2 · Pharmacological Harmonization
            </span>
            <span style="font-size: 12px;">🏷️</span>
          </div>
          <div style="color: #F8FAFC; font-size: 12.5px; font-weight: 700; margin-bottom: 3px;">
            NIH RxNorm Auto-Tagging (RxCUI)
          </div>
          <div style="color: #94A3B8; font-size: 11px; line-height: 1.4;">
            Direct on-demand resolution against NIH NLM RxNorm database to display standardized RxCUI codes and eliminate brand/generic naming conflicts with instant browser caching.
          </div>
        </div>

        <!-- Card 3: Phase 3 -->
        <div style="
            background: rgba(30, 41, 59, 0.55);
            border: 1px solid rgba(192, 132, 252, 0.25);
            border-left: 3px solid #C084FC;
            border-radius: 10px;
            padding: 10px 14px;
        ">
          <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px;">
            <span style="color: #C084FC; font-size: 11px; font-weight: 800; text-transform: uppercase;">
              Phase 3 · Cloud Benchmark &amp; Verification
            </span>
            <span style="font-size: 12px;">⚖️</span>
          </div>
          <div style="color: #F8FAFC; font-size: 12.5px; font-weight: 700; margin-bottom: 3px;">
            ClinicalTrials.gov Protocol Verification
          </div>
          <div style="color: #94A3B8; font-size: 11px; line-height: 1.4;">
            Real-time side-by-side protocol comparison against ClinicalTrials.gov API v2 to detect outcome reporting bias and audit published sample sizes and primary endpoints.
          </div>
        </div>
      </div>
    </div>
    """


def render_phase2_rxnorm_component_html() -> str:
    """
    Renders the interactive Phase 2 RxNorm Drug Standardizer bar in academic English.
    """
    return """
    <div class="mandoros-ncpi-fhir-tool" style="
        background: rgba(15, 23, 42, 0.85);
        border: 1px solid rgba(16, 185, 129, 0.35);
        border-radius: 12px;
        padding: 12px 16px;
        margin-bottom: 14px;
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        justify-content: space-between;
        gap: 12px;
        font-family: 'Inter', -apple-system, sans-serif;
    ">
      <div style="display: flex; align-items: center; gap: 8px;">
        <span style="font-size: 18px;">🏷️</span>
        <div>
          <div style="color: #F8FAFC; font-size: 13px; font-weight: 700;">
            NIH RxNorm Pharmacological Harmonization &amp; Standardization
          </div>
          <div style="color: #94A3B8; font-size: 11px;">
            Click any target drug below to resolve its standardized RxCUI code directly from the NIH NLM repository with zero server overhead:
          </div>
        </div>
      </div>

      <!-- Quick Drug Chips with 🔍 Resolve RxCUI -->
      <div style="display: flex; flex-wrap: wrap; align-items: center; gap: 8px;">
        <button type="button" class="rxnorm-fetch-btn" data-drug="Empagliflozin" style="
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: rgba(30, 41, 59, 0.9);
            border: 1px solid #38BDF8;
            color: #38BDF8;
            padding: 5px 12px;
            border-radius: 9999px;
            font-size: 11.5px;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.2s;
        " onmouseover="this.style.background='rgba(56, 189, 248, 0.2)'" onmouseout="this.style.background='rgba(30, 41, 59, 0.9)'">
          💊 Empagliflozin (🔍 Resolve RxCUI)
        </button>

        <button type="button" class="rxnorm-fetch-btn" data-drug="Dapagliflozin" style="
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: rgba(30, 41, 59, 0.9);
            border: 1px solid #34D399;
            color: #34D399;
            padding: 5px 12px;
            border-radius: 9999px;
            font-size: 11.5px;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.2s;
        " onmouseover="this.style.background='rgba(16, 185, 129, 0.2)'" onmouseout="this.style.background='rgba(30, 41, 59, 0.9)'">
          💊 Dapagliflozin (🔍 Resolve RxCUI)
        </button>

        <button type="button" class="rxnorm-fetch-btn" data-drug="Metformin" style="
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: rgba(30, 41, 59, 0.9);
            border: 1px solid #A78BFA;
            color: #A78BFA;
            padding: 5px 12px;
            border-radius: 9999px;
            font-size: 11.5px;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.2s;
        " onmouseover="this.style.background='rgba(167, 139, 250, 0.2)'" onmouseout="this.style.background='rgba(30, 41, 59, 0.9)'">
          💊 Metformin (🔍 Resolve RxCUI)
        </button>

        <button type="button" class="rxnorm-fetch-btn" data-drug="Semaglutide" style="
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: rgba(30, 41, 59, 0.9);
            border: 1px solid #F472B6;
            color: #F472B6;
            padding: 5px 12px;
            border-radius: 9999px;
            font-size: 11.5px;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.2s;
        " onmouseover="this.style.background='rgba(244, 114, 182, 0.2)'" onmouseout="this.style.background='rgba(30, 41, 59, 0.9)'">
          💊 Semaglutide (🔍 Resolve RxCUI)
        </button>
      </div>
    </div>
    """


def render_phase3_nih_benchmark_html() -> str:
    """
    Renders the Phase 3 Side-by-Side ClinicalTrials.gov Protocol Verification
    & Outcome Reporting Bias Appraisal workspace in academic English.
    """
    return """
    <div class="mandoros-ncpi-fhir-tool" style="
        background: rgba(15, 23, 42, 0.9);
        border: 1.5px solid rgba(192, 132, 252, 0.35);
        border-radius: 16px;
        padding: 22px;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    ">
      <!-- Header -->
      <div style="border-bottom: 1px solid rgba(255, 255, 255, 0.1); padding-bottom: 14px; margin-bottom: 16px; display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 12px;">
        <div>
          <div style="display: inline-flex; align-items: center; gap: 8px; margin-bottom: 4px;">
            <span style="background: rgba(192, 132, 252, 0.18); border: 1px solid #C084FC; color: #C084FC; padding: 2px 10px; border-radius: 9999px; font-size: 11px; font-weight: 800;">
              🏛️ NIH CLINICALTRIALS.GOV V2 PROTOCOL BENCHMARK
            </span>
            <span style="background: rgba(16, 185, 129, 0.15); border: 1px solid #10B981; color: #34D399; padding: 2px 8px; border-radius: 9999px; font-size: 10.5px; font-weight: 700;">
              Lazy-Loaded On-Demand
            </span>
          </div>
          <h3 style="color: #F8FAFC; margin: 4px 0 2px 0; font-size: 18px; font-weight: 800;">
            Clinical Evidence Cross-Verification · Side-by-Side Reporting Bias Appraisal
          </h3>
          <p style="color: #94A3B8; margin: 0; font-size: 12.5px; line-height: 1.5;">
            Direct comparison between findings extracted by MANDOROS from the published manuscript and the registered protocol on ClinicalTrials.gov API v2 to identify publication bias and outcome switching.
          </p>
        </div>

        <!-- 3 Standard Export Actions -->
        <div style="display: flex; flex-wrap: wrap; gap: 8px;">
          <button type="button" onclick="if(window.exportToNCPIFhir){window.exportToNCPIFhir();}else{var s=document.createElement('script');s.src='/ncpiFhirAddon.js';s.onload=function(){if(window.exportToNCPIFhir)window.exportToNCPIFhir();};document.head.appendChild(s);}" style="
              display: inline-flex;
              align-items: center;
              gap: 6px;
              background: linear-gradient(135deg, #8B5CF6, #6D28D9);
              border: none;
              border-radius: 8px;
              color: #fff;
              padding: 8px 14px;
              font-size: 12px;
              font-weight: 700;
              cursor: pointer;
              box-shadow: 0 4px 12px rgba(139, 92, 246, 0.35);
              transition: all 0.2s;
          " onmouseover="this.style.transform='translateY(-1px)'" onmouseout="this.style.transform='none'">
            🧬 FHIR (JSON)
          </button>

          <button type="button" onclick="if(window.exportToNCPIFhirExcel){window.exportToNCPIFhirExcel();}else{var s=document.createElement('script');s.src='/ncpiFhirAddon.js';s.onload=function(){if(window.exportToNCPIFhirExcel)window.exportToNCPIFhirExcel();};document.head.appendChild(s);}" style="
              display: inline-flex;
              align-items: center;
              gap: 6px;
              background: linear-gradient(135deg, #10B981, #059669);
              border: none;
              border-radius: 8px;
              color: #fff;
              padding: 8px 14px;
              font-size: 12px;
              font-weight: 700;
              cursor: pointer;
              box-shadow: 0 4px 12px rgba(16, 185, 129, 0.35);
              transition: all 0.2s;
          " onmouseover="this.style.transform='translateY(-1px)'" onmouseout="this.style.transform='none'">
            📊 FHIR (Excel)
          </button>

          <button type="button" onclick="if(window.exportToNCPIFhirDashboard){window.exportToNCPIFhirDashboard();}else{var s=document.createElement('script');s.src='/ncpiFhirAddon.js';s.onload=function(){if(window.exportToNCPIFhirDashboard)window.exportToNCPIFhirDashboard();};document.head.appendChild(s);}" style="
              display: inline-flex;
              align-items: center;
              gap: 6px;
              background: linear-gradient(135deg, #0EA5E9, #0284C7);
              border: none;
              border-radius: 8px;
              color: #fff;
              padding: 8px 14px;
              font-size: 12px;
              font-weight: 700;
              cursor: pointer;
              box-shadow: 0 4px 12px rgba(14, 165, 233, 0.35);
              transition: all 0.2s;
          " onmouseover="this.style.transform='translateY(-1px)'" onmouseout="this.style.transform='none'">
            🌐 Dashboard
          </button>
        </div>
      </div>

      <!-- NCT / Query Input & Quick Buttons -->
      <div style="background: rgba(30, 41, 59, 0.6); border: 1px solid #334155; border-radius: 12px; padding: 14px; margin-bottom: 18px;">
        <div style="display: flex; flex-wrap: wrap; gap: 10px; align-items: center;">
          <input type="text" id="phase3-nct-input" value="NCT01131676" placeholder="Enter NCT ID (e.g., NCT01131676) or study / drug query..." style="
              flex: 1;
              min-width: 250px;
              background: #0F172A;
              border: 1px solid #475569;
              border-radius: 8px;
              color: #F8FAFC;
              padding: 9px 14px;
              font-size: 13px;
              font-family: monospace;
          ">
          <button type="button" onclick="window.runPhase3ClinicalTrialsCheck(null, 'phase3-nih-benchmark-results')" style="
              background: linear-gradient(135deg, #0EA5E9, #0284C7);
              border: none;
              border-radius: 8px;
              color: #fff;
              padding: 9px 18px;
              font-weight: 700;
              font-size: 13px;
              cursor: pointer;
              transition: all 0.2s;
          " onmouseover="this.style.transform='translateY(-1px)'" onmouseout="this.style.transform='none'">
            🔍 Fetch &amp; Compare Registered Protocol
          </button>
        </div>

        <!-- Quick Demo Chips -->
        <div style="display: flex; flex-wrap: wrap; align-items: center; gap: 8px; margin-top: 10px;">
          <span style="color: #94A3B8; font-size: 11px; font-weight: 600;">Pre-indexed benchmark trials:</span>
          <button type="button" onclick="document.getElementById('phase3-nct-input').value='NCT01131676'; window.runPhase3ClinicalTrialsCheck('NCT01131676', 'phase3-nih-benchmark-results');" style="background:rgba(56,189,248,0.12);border:1px solid rgba(56,189,248,0.4);color:#38BDF8;padding:3px 10px;border-radius:9999px;font-size:11px;font-weight:700;cursor:pointer;">
            EMPA-REG OUTCOME (NCT01131676)
          </button>
          <button type="button" onclick="document.getElementById('phase3-nct-input').value='NCT01730534'; window.runPhase3ClinicalTrialsCheck('NCT01730534', 'phase3-nih-benchmark-results');" style="background:rgba(16,185,129,0.12);border:1px solid rgba(16,185,129,0.4);color:#34D399;padding:3px 10px;border-radius:9999px;font-size:11px;font-weight:700;cursor:pointer;">
            DECLARE-TIMI 58 (NCT01730534)
          </button>
          <button type="button" onclick="document.getElementById('phase3-nct-input').value='NCT00870337'; window.runPhase3ClinicalTrialsCheck('NCT00870337', 'phase3-nih-benchmark-results');" style="background:rgba(167,139,250,0.12);border:1px solid rgba(167,139,250,0.4);color:#A78BFA;padding:3px 10px;border-radius:9999px;font-size:11px;font-weight:700;cursor:pointer;">
            Metformin Monotherapy (NCT00870337)
          </button>
        </div>
      </div>

      <!-- Results Container (Lazy-loaded upon click) -->
      <div id="phase3-nih-benchmark-results">
        <div style="padding: 24px; text-align: center; color: #94A3B8; background: rgba(15, 23, 42, 0.5); border: 1px dashed #334155; border-radius: 12px; font-size: 13px;">
          💡 Click <strong>"🔍 Fetch &amp; Compare Registered Protocol"</strong> or select a benchmark trial above to cross-verify trial endpoints directly against ClinicalTrials.gov API v2.
        </div>
      </div>
    </div>
    """
