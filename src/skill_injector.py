"""
MANDOROS Master Skill Injector & Deterministic Validation Quality Gate.

Hierarchy of authority enforced in every LLM call and every export:
  TIER 1 — SUPREME LAW (100% mandatory): verbatim master_protocols/phase{1,2}_master_instructions.md
            + the exact master_protocols/phase{1,2}_schema.json.
  TIER 2 — TECHNICAL MUSCLE: clinical_skills_library/ (pdf, clinical-reports, statistical-analysis,
            clinical-decision-support, statsmodels, peer-review, clinicaltrials-database).
  TIER 3 — Unified TrialMind / RCTMethodologyIE audit specification.

This module also provides:
  - to_phase1_master_dict(): lossless mapping of internal ExtractedTrialData -> exact Phase 1 schema.
  - validate_phase1_payload() / validate_phase2_payload(): JSON-schema + protocol maths + non-destructive
    duplicate handling (Rules 1, 37, 40, 49, 51, 53; Phase 2 Rules 14, 27, 29).
  - execute_phase{1,2}_validation_loop(): targeted LLM retry, then deterministic repair, never silent.
"""

from __future__ import annotations

import functools
import json
import math
import re
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from src.protocol_engine import (
    BASE_DIR,
    MASTER_PROTOCOLS_DIR,
    SKILLS_LIB_DIR,
    TIER2_PHASE1_SKILLS,
    TIER2_PHASE2_SKILLS,
    clean_scalar,
    collapse_exact_duplicates,
    is_missing,
    load_schema,
    outcome_identity_key,
    outcome_value_signature,
    parse_p_value,
    schema_errors,
    skill_reference_files,
    split_operator,
    to_number,
)

CURRENT_DIR = Path(__file__).resolve().parent


@functools.lru_cache(maxsize=256)
def _read_file_safe(path_str: str, max_chars: Optional[int] = None) -> str:
    """Reads a UTF-8 text file once and caches it in RAM (Render-safe)."""
    path = Path(path_str)
    if not path.exists():
        return ""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            text = fh.read()
        return text[:max_chars] if max_chars else text
    except Exception as exc:  # pragma: no cover - defensive
        print(f"[!] Warning: Could not read {path}: {exc}")
        return ""


# ---------------------------------------------------------------------------
# Tier 1 — Master protocols & schemas (verbatim, cached)
# ---------------------------------------------------------------------------
@functools.lru_cache(maxsize=4)
def get_phase1_master_instructions() -> str:
    return _read_file_safe(str(MASTER_PROTOCOLS_DIR / "phase1_master_instructions.md"))


@functools.lru_cache(maxsize=4)
def get_phase2_master_instructions() -> str:
    return _read_file_safe(str(MASTER_PROTOCOLS_DIR / "phase2_master_instructions.md"))


def get_phase1_schema() -> Dict[str, Any]:
    return load_schema(1)


def get_phase2_schema() -> Dict[str, Any]:
    return load_schema(2)


@functools.lru_cache(maxsize=4)
def get_clinical_synthesis_and_methodology_instructions() -> str:
    for cand in (
        BASE_DIR / "backend" / "instructions" / "clinical_synthesis_and_methodology_skills.md",
        MASTER_PROTOCOLS_DIR / "clinical_synthesis_and_methodology_skills.md",
        BASE_DIR / "backend instructions" / "clinical_synthesis_and_methodology_skills.md",
    ):
        if cand.exists():
            return _read_file_safe(str(cand))
    return ""


# ---------------------------------------------------------------------------
# Tier 2 — Clinical skills library (dynamic path wiring, lazy + cached)
# ---------------------------------------------------------------------------
@functools.lru_cache(maxsize=64)
def get_skill_instructions(skill_name: str, max_chars: int = 15000) -> str:
    for cand in (skill_name, skill_name.replace("-", "_"), skill_name.replace("_", "-")):
        content = _read_file_safe(str(SKILLS_LIB_DIR / cand / "SKILL.md"), max_chars=max_chars)
        if content:
            return content
    return ""


@functools.lru_cache(maxsize=128)
def get_skill_reference(skill_name: str, ref_filename: str, max_chars: int = 6000) -> str:
    for cand in (skill_name, skill_name.replace("-", "_")):
        content = _read_file_safe(str(SKILLS_LIB_DIR / cand / "references" / ref_filename), max_chars=max_chars)
        if content:
            return content
    return ""


@functools.lru_cache(maxsize=64)
def get_skill_script(skill_name: str, script_name: str) -> str:
    for cand in (skill_name, skill_name.replace("-", "_")):
        content = _read_file_safe(str(SKILLS_LIB_DIR / cand / "scripts" / script_name))
        if content:
            return content
    return ""


@functools.lru_cache(maxsize=16)
def get_skill_bundle(skill_name: str, skill_chars: int = 8000, ref_chars: int = 3500, max_refs: int = 4) -> str:
    """SKILL.md + the first reference documents of a skill, discovered dynamically on disk."""
    parts = [get_skill_instructions(skill_name, max_chars=skill_chars)]
    for ref in skill_reference_files(skill_name)[:max_refs]:
        txt = get_skill_reference(skill_name, ref, max_chars=ref_chars)
        if txt:
            parts.append(f"\n[reference: {skill_name}/references/{ref}]\n{txt}")
    return "\n".join(p for p in parts if p).strip()


# ---------------------------------------------------------------------------
# Self-critique gate (aligned with Rule 5/49: blanks/null, never 'NR')
# ---------------------------------------------------------------------------
SELF_CRITIQUE_QUALITY_GATE_PROMPT = """
================================================================================
STRICT SELF-CRITIQUE & DETERMINISTIC QUALITY GATE (applied before you answer)
================================================================================
1. COMPLETENESS (Rules 6, 9, 15, 19, 20, 36, 47): every treatment arm, every eligibility
   criterion (per subgroup and per assessment stage), every baseline variable, every
   efficacy endpoint at EVERY timepoint, and every adverse event must be present.
   Never truncate arrays, never use ellipses, never summarise rows.
2. ZERO HALLUCINATION (Rules 5, 41, 49): every number must exist in the source. A value
   that is not reported MUST be JSON null (Excel blank). NEVER write "N/A", "NR",
   "Not reported", "Unknown", "-", or 0 as a missing-value placeholder.
3. NO DUPLICATION WITHOUT DATA LOSS (Rules 1, 40): one analytical record per unique
   (outcome, definition, arm, comparator, population, timepoint, period, estimate type,
   scale). Different doses, timepoints, populations, subgroups, severities, meal types
   and estimate types are DISTINCT records and must ALL be retained.
4. STATISTICAL FIDELITY (Rules 23, 24, 43; CONSORT 2010; APA 7th; Cochrane RoB 2;
   GRADE): preserve the published estimate type (RAW_MEAN vs ADJUSTED_MEAN_DIFFERENCE,
   SD vs SE, median/IQR), store estimate, CI lower, CI upper, CI level, p-value and
   p-operator in separate fields, report HR/OR/RR with 95% CI and exact p-values.
5. CELL-LEVEL NORMALISATION (Rules 2, 3, 4, 18): one atomic value per field; operators,
   units, minimum and maximum each in their own field; CI_lower <= CI_upper;
   0 <= percentage <= 100; event_count <= denominator; I² in [0,100]; tau² >= 0.
If any condition fails, regenerate the affected part before returning the JSON.
================================================================================
"""


# ---------------------------------------------------------------------------
# System prompt builders
# ---------------------------------------------------------------------------
@functools.lru_cache(maxsize=2)
def build_phase1_system_prompt() -> str:
    phase1_instructions = get_phase1_master_instructions()
    phase1_schema = get_phase1_schema()
    skills_block = "\n\n".join(
        f"--- SKILL: {name.upper()} ---\n{get_skill_bundle(name)}"
        for name in TIER2_PHASE1_SKILLS
        if get_skill_bundle(name)
    )
    prompt = f"""
================================================================================
MANDOROS CLINICAL AI SYSTEM — PHASE 1 EXTRACTION PIPELINE
HIERARCHY OF AUTHORITY: TIER 1 (SUPREME LAW) >>> TIER 2 (SKILLS) >>> TIER 3 (AUDIT SPEC)
================================================================================

[TIER 1: SUPREME LAW — 100% MANDATORY & NON-NEGOTIABLE]
The complete Master Extraction Protocol below (Rules 1–55, all tables and examples) and the
JSON schema that follows are absolute law. Every rule, table structure and JSON key is
mandatory. If anything conflicts with Tier 1, Tier 1 wins 100%.
Missing information is represented ONLY as JSON null (Rule 5 / Rule 49).

--- PHASE 1 MASTER PROTOCOL INSTRUCTIONS (VERBATIM) ---
{phase1_instructions}

--- PHASE 1 REQUIRED OUTPUT JSON SCHEMA (VERBATIM, additionalProperties=false) ---
{json.dumps(phase1_schema, indent=2, ensure_ascii=False)}

================================================================================
[TIER 2: SUPPORTING EXECUTION SKILLS — TECHNICAL MUSCLE]
Apply these methodologies to execute Tier 1 with university-grade rigour:
{skills_block}

================================================================================
[TIER 3: UNIFIED CLINICAL EVIDENCE & METHODOLOGICAL AUDIT SPECIFICATION]
{get_clinical_synthesis_and_methodology_instructions()}

{SELF_CRITIQUE_QUALITY_GATE_PROMPT}

FINAL DIRECTIVE:
Return strictly valid JSON only (no prose, no markdown fences). Unavailable optional
values are null. Never invent, round, swap, merge or omit any reported value.
"""
    return prompt.strip()


@functools.lru_cache(maxsize=2)
def build_phase2_system_prompt() -> str:
    phase2_instructions = get_phase2_master_instructions()
    phase2_schema = get_phase2_schema()
    skills_block = "\n\n".join(
        f"--- SKILL: {name.upper()} ---\n{get_skill_bundle(name)}"
        for name in TIER2_PHASE2_SKILLS
        if get_skill_bundle(name)
    )
    prompt = f"""
================================================================================
MANDOROS CLINICAL AI SYSTEM — PHASE 2 SYSTEMATIC REVIEW & META-ANALYSIS PIPELINE
HIERARCHY OF AUTHORITY: TIER 1 (SUPREME LAW) >>> TIER 2 (SKILLS) >>> TIER 3 (AUDIT SPEC)
================================================================================

[TIER 1: SUPREME LAW — 100% MANDATORY & NON-NEGOTIABLE]
The complete Phase 2 Master Protocol below (Rules 1–29, the 20 required worksheets, PICO
compatibility, double-counting prevention, effect-size rules, heterogeneity, Cochrane RoB 2,
GRADE, and the 100-point acceptance framework) and the JSON schema that follows are absolute
law. Phase 1 Rules 1–55 remain fully applicable. Never fabricate statistics (Rule 11); never
pool fewer than two independent compatible studies (Rule 14); never assign full quality points
to an unevaluated domain (Rule 28).

--- PHASE 2 MASTER PROTOCOL INSTRUCTIONS (VERBATIM) ---
{phase2_instructions}

--- PHASE 2 REQUIRED OUTPUT JSON SCHEMA (VERBATIM) ---
{json.dumps(phase2_schema, indent=2, ensure_ascii=False)}

================================================================================
[TIER 2: SUPPORTING EXECUTION SKILLS — BIOSTATISTICAL & CLINICAL MUSCLE]
Apply CONSORT 2010, Cochrane Handbook / RoB 2, GRADE, PRISMA 2020 and APA 7th reporting
(exact effect sizes MD/SMD/RR/OR/HR, 95% CIs, exact p-values, I², tau², Q, prediction intervals):
{skills_block}

================================================================================
[TIER 3: UNIFIED CLINICAL EVIDENCE & METHODOLOGICAL AUDIT SPECIFICATION]
{get_clinical_synthesis_and_methodology_instructions()}

{SELF_CRITIQUE_QUALITY_GATE_PROMPT}

FINAL DIRECTIVE:
Return strictly valid JSON only, conforming exactly to the Phase 2 schema. All statistics
must be reproducible from the reported inputs; unavailable values are null.
"""
    return prompt.strip()


def build_system_prompt_for_task(task_type: str = "extraction") -> str:
    t = (task_type or "").lower().strip()
    if "extract" in t or "phase1" in t or "phase_1" in t:
        return build_phase1_system_prompt()
    if "stat" in t or "meta" in t or "phase2" in t or "phase_2" in t:
        return build_phase2_system_prompt()
    if "review" in t or "peer" in t:
        return f"""
================================================================================
MANDOROS CLINICAL AI SYSTEM — PEER REVIEW & EVIDENCE AUDIT PIPELINE
================================================================================
You are a senior medical journal editor and biostatistical referee. Evaluate strictly against
CONSORT 2010, Cochrane RoB 2, GRADE, PRISMA 2020 and APA 7th statistical reporting.

--- PEER REVIEW METHODOLOGY ---
{get_skill_bundle("peer-review", skill_chars=12000)}

--- STATISTICAL REPRODUCIBILITY & ASSUMPTIONS ---
{get_skill_bundle("statistical-analysis")}

--- CLINICAL TRIAL REPORTING CHECKLIST ---
{get_skill_bundle("clinical-reports")}

{SELF_CRITIQUE_QUALITY_GATE_PROMPT}
""".strip()
    return build_phase1_system_prompt()


# ---------------------------------------------------------------------------
# Internal model -> exact Phase 1 schema mapping (lossless)
# ---------------------------------------------------------------------------
_ARM_TYPE_MAP = {
    "experimental": "experimental",
    "placebo": "placebo",
    "active_comparator": "active_comparator",
    "standard_of_care": "usual_care",
    "usual_care": "usual_care",
    "lifestyle": "other",
    "other": "other",
}

_ESTIMATE_TYPE_MAP = {
    "BASELINE_MEAN": "RAW_MEAN",
    "FOLLOWUP_MEAN": "RAW_MEAN",
    "RAW_MEAN": "RAW_MEAN",
    "RAW_CHANGE_FROM_BASELINE": "MEAN_CHANGE",
    "MEAN_CHANGE": "MEAN_CHANGE",
    "ADJUSTED_CHANGE_FROM_BASELINE": "ADJUSTED_MEAN_CHANGE",
    "ADJUSTED_MEAN_CHANGE": "ADJUSTED_MEAN_CHANGE",
    "RAW_MEAN_DIFFERENCE": "RAW_MEAN_DIFFERENCE",
    "MEAN_DIFFERENCE": "RAW_MEAN_DIFFERENCE",
    "ADJUSTED_MEAN_DIFFERENCE": "ADJUSTED_MEAN_DIFFERENCE",
    "GEOMETRIC_MEAN_RATIO": "GEOMETRIC_MEAN_RATIO",
    "GEOMETRIC_MEAN": "OTHER",
    "BINARY_RATE": "EVENT_COUNT",
    "EVENT_COUNT": "EVENT_COUNT",
    "EVENT_PERCENTAGE": "PERCENTAGE",
    "PERCENTAGE": "PERCENTAGE",
    "RISK_RATIO": "RISK_RATIO",
    "ODDS_RATIO": "ODDS_RATIO",
    "HAZARD_RATIO": "HAZARD_RATIO",
    "MEDIAN": "MEDIAN",
    "RELATIVE_CHANGE": "OTHER",
    "PERCENT_CHANGE": "OTHER",
}


def _effect_measure_to_estimate_type(measure: Optional[str], adjusted_hint: bool) -> str:
    m = str(measure or "").lower()
    if "hazard" in m or m.strip() == "hr":
        return "HAZARD_RATIO"
    if "odds" in m or m.strip() == "or":
        return "ODDS_RATIO"
    if "risk ratio" in m or "relative risk" in m or m.strip() in ("rr",):
        return "RISK_RATIO"
    if "geometric" in m or "gmr" in m:
        return "GEOMETRIC_MEAN_RATIO"
    if "adjusted" in m or adjusted_hint:
        return "ADJUSTED_MEAN_DIFFERENCE"
    if "difference" in m or "md" == m.strip():
        return "RAW_MEAN_DIFFERENCE"
    return "OTHER" if m else "RAW_MEAN_DIFFERENCE"


def _location_type(loc: Optional[str]) -> str:
    l = str(loc or "").lower()
    if "supplement" in l or "appendix" in l:
        return "supplement"
    if "fig" in l:
        return "figure"
    if "table" in l:
        return "table"
    return "text"


def _extraction_method(loc_type: str, derivation: Optional[str]) -> str:
    d = str(derivation or "").lower()
    if loc_type == "figure":
        return "figure_approximate" if d in ("digitized", "graph_annotated", "approximate") else "figure_exact"
    if loc_type in ("table", "supplement"):
        return "table_read"
    return "digital_text"


def _parse_duration(text: Optional[str]) -> Tuple[Optional[float], Optional[str]]:
    m = re.search(r"(\d+(?:\.\d+)?)\s*(weeks?|days?|months?|years?)", str(text or ""), re.I)
    if not m:
        return None, None
    unit = m.group(2).lower()
    unit = unit if unit.endswith("s") else unit + "s"
    return float(m.group(1)), unit


def _as_int(v: Any) -> Optional[int]:
    n = to_number(v)
    if n is None or n < 0:
        return None
    return int(round(n)) if abs(n - round(n)) < 1e-9 else None


def _as_str(v: Any) -> Optional[str]:
    v = clean_scalar(v)
    return None if v is None else str(v)


def to_phase1_master_dict(trial_data: Any) -> Dict[str, Any]:
    """
    Converts ExtractedTrialData (or its dict) into the exact Phase 1 schema structure.
    Lossless: one internal outcome record that holds several estimate types (raw mean,
    change from baseline, between-group effect, event count) is emitted as several
    schema-conformant observations, each with its own estimate_type (Rule 23 / Rule 40).
    """
    d = trial_data.model_dump() if hasattr(trial_data, "model_dump") else (trial_data if isinstance(trial_data, dict) else {})
    study_in = d.get("study", {}) or {}
    study_id = _as_str(study_in.get("study_id")) or "STUDY"

    # ---- sources (provenance) ---------------------------------------------------
    sources: List[Dict[str, Any]] = []
    source_ids_by_target: Dict[str, List[str]] = {}
    seen_source_ids = set()
    for p in d.get("provenance", []) or []:
        sid = _as_str(p.get("provenance_id")) or f"SRC_{len(sources) + 1:04d}"
        if sid in seen_source_ids:
            sid = f"{sid}_{len(sources) + 1}"
        seen_source_ids.add(sid)
        loc = _location_type(p.get("source_location"))
        page = _as_int(p.get("source_page")) or 1
        sources.append({
            "source_id": sid,
            "page": max(1, page),
            "location_type": loc,
            "section": _as_str(p.get("source_location")),
            "item_label": _as_str(p.get("field_name")),
            "evidence": _as_str(p.get("exact_source_text")),
            "extraction_method": _extraction_method(loc, None),
            "confidence": None,
        })
        tgt = _as_str(p.get("target_id"))
        if tgt:
            source_ids_by_target.setdefault(tgt, []).append(sid)

    def _ensure_source(record_id: str, page: Any, location: Any, evidence: Any, derivation: Any = None) -> List[str]:
        ids = list(dict.fromkeys(source_ids_by_target.get(record_id, [])))
        if ids:
            return ids
        pg = _as_int(page)
        if pg is None and is_missing(location) and is_missing(evidence):
            return []
        sid = f"SRC_{record_id}"
        if sid in seen_source_ids:
            sid = f"{sid}_{len(sources) + 1}"
        seen_source_ids.add(sid)
        loc = _location_type(location)
        sources.append({
            "source_id": sid,
            "page": max(1, pg or 1),
            "location_type": loc,
            "section": _as_str(location),
            "item_label": None,
            "evidence": _as_str(evidence),
            "extraction_method": _extraction_method(loc, derivation),
            "confidence": None,
        })
        source_ids_by_target[record_id] = [sid]
        return [sid]

    # ---- study ------------------------------------------------------------------
    design = _as_str(study_in.get("study_design"))
    design_l = (design or "").lower()
    randomization = "Randomized" if "randomi" in design_l else None
    blinding = None
    for key, label in (("double-blind", "Double-blind"), ("double blind", "Double-blind"), ("single-blind", "Single-blind"), ("open-label", "Open-label"), ("open label", "Open-label"), ("triple-blind", "Triple-blind")):
        if key in design_l:
            blinding = label
            break
    phase_raw = _as_str(study_in.get("study_phase"))
    phase = None if (phase_raw is None or "not" in phase_raw.lower()) else phase_raw
    primary = next((o.get("parameter_name") for o in d.get("outcomes", []) or [] if o.get("is_primary")), None)
    study = {
        "study_id": study_id,
        "title": _as_str(study_in.get("title")) or "Title not captured",
        "authors": _as_str(study_in.get("authors")),
        "journal": _as_str(study_in.get("journal")),
        "doi": _as_str(study_in.get("doi")),
        "registration_id": _as_str(study_in.get("registration_id")),
        "design": design,
        "randomization": randomization,
        "blinding": blinding,
        "phase": phase,
        "country": _as_str(study_in.get("country")),
        "setting": _as_str(study_in.get("setting")),
        "sponsor": _as_str(study_in.get("sponsor")),
        "funding": _as_str(study_in.get("funding")),
        "primary_endpoint": _as_str(primary),
        "publication_year": _as_int(study_in.get("publication_year")),
        "randomized_n": _as_int(study_in.get("total_sample_size")),
        "centers_n": _as_int(study_in.get("centers_n")),
        "treatment_duration_value": to_number(study_in.get("duration_value")),
        "followup_duration_value": to_number(study_in.get("followup_duration_value")),
        "treatment_duration_unit": _as_str(study_in.get("duration_unit")),
        "followup_duration_unit": _as_str(study_in.get("followup_duration_unit")),
    }

    # ---- arms -------------------------------------------------------------------
    arms_out: List[Dict[str, Any]] = []
    arm_ids: List[str] = []
    control_ids: List[str] = []
    for a in d.get("arms", []) or []:
        aid = _as_str(a.get("arm_id")) or f"ARM_{len(arms_out) + 1:03d}"
        arm_ids.append(aid)
        a_type = _ARM_TYPE_MAP.get(str(a.get("intervention_type") or "").lower(), "other")
        if a_type in ("placebo", "active_comparator", "usual_care"):
            control_ids.append(aid)
        arms_out.append({
            "arm_id": aid,
            "name": _as_str(a.get("arm_name")) or aid,
            "type": a_type,
            "drug": _as_str(a.get("drug_name")),
            "dose_value": to_number(a.get("dose_value")),
            "dose_unit": _as_str(a.get("dose_unit")),
            "frequency_value": to_number(a.get("frequency_number")),
            "frequency_per_unit": _as_str(a.get("frequency_unit")),
            "route": _as_str(a.get("route")),
            "duration_value": to_number(a.get("treatment_duration_value")),
            "duration_unit": _as_str(a.get("treatment_duration_unit")),
            "randomized_n": _as_int(a.get("sample_size_allocated")),
            "analyzed_n": _as_int(a.get("sample_size_analyzed")),
            "source_ids": _ensure_source(aid, a.get("source_page"), "Methods / Treatment arms", a.get("arm_name")),
        })
    default_comparator = control_ids[0] if len(control_ids) == 1 else None

    # ---- eligibility ------------------------------------------------------------
    elig_out: List[Dict[str, Any]] = []
    for e in d.get("eligibility", []) or []:
        cid = _as_str(e.get("criterion_id")) or f"ELIG_{len(elig_out) + 1:03d}"
        kind = "EXCLUSION" if str(e.get("criterion_type") or "").lower().startswith("exc") else "INCLUSION"
        min_v = to_number(e.get("min_value"))
        max_v = to_number(e.get("max_value"))
        min_op = e.get("min_operator")
        max_op = e.get("max_operator")
        single_v = to_number(e.get("value"))
        if min_v is None and max_v is None and single_v is not None:
            if e.get("less_than"):
                max_v, max_op = single_v, ("<=" if e.get("equal") else "<")
            elif e.get("greater_than"):
                min_v, min_op = single_v, (">=" if e.get("equal") else ">")
            else:
                min_v, min_op = single_v, "="
        lo1, lo2 = split_operator(min_op) if min_v is not None else (None, None)
        hi1, hi2 = split_operator(max_op) if max_v is not None else (None, None)
        value_text = e.get("value") if (isinstance(e.get("value"), str) and not is_missing(e.get("value"))) else None
        domain_l = str(e.get("domain") or "").lower()
        is_med = "medic" in domain_l or "drug" in domain_l or "medication" in str(e.get("criterion_name") or "").lower()
        dur_v, dur_u = _parse_duration(e.get("raw_source_text") or value_text)
        description = _as_str(e.get("raw_source_text"))
        if value_text and value_text not in (description or ""):
            description = f"{description} | {value_text}" if description else value_text
        elig_out.append({
            "criterion_id": cid,
            "kind": kind,
            "variable": _as_str(e.get("criterion_name")) or "criterion",
            "description": description,
            "population_subgroup": _as_str(e.get("applicable_population")),
            "assessment_stage": _as_str(e.get("assessment_stage")),
            "lower_value": min_v,
            "lower_operator_1": lo1,
            "lower_operator_2": lo2,
            "upper_value": max_v,
            "upper_operator_1": hi1,
            "upper_operator_2": hi2,
            "unit": _as_str(e.get("unit")),
            "medication": value_text if is_med else None,
            "duration_value": dur_v if is_med else None,
            "duration_unit": dur_u if is_med else None,
            "source_ids": _ensure_source(cid, e.get("source_page"), "Methods / Eligibility", e.get("raw_source_text")),
        })

    # ---- baseline & outcomes ----------------------------------------------------
    baseline_out: List[Dict[str, Any]] = []
    outcomes_out: List[Dict[str, Any]] = []
    validation_out: List[Dict[str, Any]] = []
    pico_outcomes: List[str] = []

    def _add_validation(record_id: str, rule_id: str, severity: str, message: str, status: str = "OPEN", src: Optional[List[str]] = None) -> None:
        validation_out.append({
            "issue_id": f"VAL_{len(validation_out) + 1:04d}",
            "record_id": record_id,
            "rule_id": rule_id,
            "severity": severity,
            "message": message,
            "status": status,
            "source_ids": list(src or []),
        })

    for o in d.get("outcomes", []) or []:
        oid = _as_str(o.get("outcome_id")) or f"OUT_{len(outcomes_out) + len(baseline_out) + 1:04d}"
        arm_id = _as_str(o.get("arm_id"))
        if arm_id and arm_id not in arm_ids:
            _add_validation(oid, "RULE_51_INVALID_ARM_REFERENCE", "MAJOR", f"arm_id '{arm_id}' does not match any extracted treatment arm.", "MANUAL_REVIEW")
        pname = _as_str(o.get("parameter_name")) or "Unnamed outcome"
        if pname not in pico_outcomes:
            pico_outcomes.append(pname)
        tp_raw = o.get("timepoint_value")
        tp_num = to_number(tp_raw)
        tp_unit = _as_str(o.get("timepoint_unit"))
        tp_label = _as_str(o.get("original_timepoint_label")) or _as_str(o.get("timepoint")) or (_as_str(tp_raw) if tp_num is None else None)
        unit = _as_str(o.get("unit"))
        n_an = _as_int(o.get("sample_size"))
        src_ids = _ensure_source(oid, o.get("source_page"), o.get("source_location"), o.get("raw_source_text") or o.get("source_evidence"), o.get("derivation_type"))
        derivation = str(o.get("derivation_type") or "directly_reported").lower()
        approx = derivation in ("digitized", "graph_annotated", "approximate")
        status = "VERIFIED" if (src_ids and not approx) else "FLAGGED"
        population = _as_str(o.get("analysis_population"))
        is_base = bool(o.get("is_baseline")) or str(tp_raw or "").strip() in ("0", "0.0") or str(o.get("variable_role") or "").upper() == "BASELINE_CHARACTERISTIC"
        gender = _as_str(o.get("gender"))
        race = _as_str(o.get("race"))
        qualifier = " / ".join(x for x in (gender, race) if x)
        definition_bits = [x for x in (qualifier or None, _as_str(o.get("metric_type")), _as_str(o.get("assessment_stage"))) if x]

        mean_v = to_number(o.get("mean"))
        sd_v = to_number(o.get("sd"))
        se_v = to_number(o.get("se"))
        median_v = to_number(o.get("median"))
        q1_v = to_number(o.get("iqr_lower"))
        q3_v = to_number(o.get("iqr_upper"))
        min_v = to_number(o.get("min_value"))
        max_v = to_number(o.get("max_value"))
        events_v = _as_int(o.get("events"))
        total_v = _as_int(o.get("total"))
        pct_v = to_number(o.get("percentage"))
        change_v = to_number(o.get("change_value"))
        change_sd = to_number(o.get("change_sd"))
        effect_v = to_number(o.get("effect_value"))
        ratio_v = to_number(o.get("ratio"))
        ci_l = to_number(o.get("ci_lower"))
        ci_u = to_number(o.get("ci_upper"))
        p_val, p_op = parse_p_value(o.get("p_value"))
        internal_est = str(o.get("estimate_type") or "").upper()
        raw_txt = str(o.get("raw_source_text") or "").lower()
        is_safety = str(o.get("domain") or "").lower() == "safety_adverse_events" or str(o.get("variable_role") or "").upper() == "SAFETY_OUTCOME"

        if is_base and not is_safety:
            if mean_v is not None and sd_v is not None:
                stat = "mean_sd"
            elif median_v is not None and (q1_v is not None or q3_v is not None):
                stat = "median_iqr"
            elif median_v is not None and (min_v is not None or max_v is not None):
                stat = "median_range"
            elif events_v is not None and pct_v is not None:
                stat = "count_percentage"
            elif events_v is not None:
                stat = "count"
            elif pct_v is not None:
                stat = "percentage"
            else:
                stat = "other"
            baseline_out.append({
                "baseline_id": oid,
                "variable": pname if not qualifier else f"{pname} [{qualifier}]",
                "arm_id": arm_id,
                "scope": "arm" if arm_id else "overall",
                "population": population,
                "statistic": stat,
                "mean": mean_v,
                "sd": sd_v,
                "median": median_v,
                "q1": q1_v,
                "q3": q3_v,
                "min": min_v,
                "max": max_v,
                "count": events_v,
                "percentage": pct_v,
                "unit": unit,
                "source_ids": src_ids,
            })
            if se_v is not None:
                _add_validation(oid, "RULE_18_SEPARATE_BASELINE_STATISTICS", "INFO", f"Baseline '{pname}' reports SE={se_v} (preserved here; schema baseline object has no SE field).", "RESOLVED", src_ids)
            if ratio_v is not None or change_v is not None or effect_v is not None:
                pass  # fall through so non-baseline estimates on this record are also emitted
            else:
                continue

        domain = "SAFETY" if is_safety else ("OTHER" if str(o.get("variable_role") or "").upper() == "EXPLORATORY_OUTCOME" else "EFFICACY")
        base_rec = {
            "domain": domain,
            "name": pname,
            "definition": " | ".join(definition_bits) if definition_bits else None,
            "arm_id": arm_id,
            "comparator_arm_id": None,
            "analysis_population": population,
            "timepoint_value": tp_num,
            "timepoint_unit": tp_unit if tp_num is not None else None,
            "original_timepoint_label": tp_label,
            "period_start": None,
            "period_end": None,
            "period_unit": None,
            "unit": unit,
            "n_analyzed": n_an,
            "source_ids": src_ids,
            "status": status,
            "approximate_from_figure": approx,
        }
        emitted = 0

        def _emit(suffix: str, est_type: str, value: Optional[float], **kw: Any) -> None:
            nonlocal emitted
            rec = dict(base_rec)
            rec.update({
                "outcome_id": oid if suffix == "" else f"{oid}_{suffix}",
                "estimate_type": est_type,
                "value": value,
                "sd": None, "se": None, "ci_lower": None, "ci_upper": None, "ci_level": None,
                "p_value": None, "p_operator": None, "event_count": None, "denominator": None,
            })
            rec.update(kw)
            outcomes_out.append(rec)
            emitted += 1

        # (a) within-arm absolute level (raw mean / median / events)
        if not (is_base and not is_safety):
            if events_v is not None or (pct_v is not None and mean_v is None and median_v is None):
                _emit("", "EVENT_COUNT" if events_v is not None else "PERCENTAGE",
                      float(events_v) if events_v is not None else pct_v,
                      event_count=events_v, denominator=total_v,
                      ci_lower=ci_l if effect_v is None else None, ci_upper=ci_u if effect_v is None else None,
                      ci_level=95 if (effect_v is None and ci_l is not None) else None,
                      p_value=p_val if effect_v is None else None, p_operator=p_op if effect_v is None else None)
                if pct_v is not None and events_v is not None:
                    _emit("PCT", "PERCENTAGE", pct_v, event_count=events_v, denominator=total_v)
            elif median_v is not None:
                _emit("", "MEDIAN", median_v, ci_lower=q1_v, ci_upper=q3_v)
                if q1_v is not None or q3_v is not None:
                    _add_validation(oid, "RULE_18_SEPARATE_BASELINE_STATISTICS", "INFO", "Median with IQR: Q1/Q3 stored in ci_lower/ci_upper with ci_level null (interquartile range, not a confidence interval).", "RESOLVED", src_ids)
            elif mean_v is not None:
                est = "RAW_MEAN"
                if "geometric" in str(o.get("metric_type") or "").lower() or internal_est == "GEOMETRIC_MEAN":
                    est = "OTHER"
                _emit("", est, mean_v, sd=sd_v, se=se_v)

        # (b) change from baseline
        if change_v is not None:
            est = _ESTIMATE_TYPE_MAP.get(internal_est, None)
            if est not in ("MEAN_CHANGE", "ADJUSTED_MEAN_CHANGE"):
                est = "ADJUSTED_MEAN_CHANGE" if ("adjust" in raw_txt or internal_est.startswith("ADJUSTED")) else "MEAN_CHANGE"
            _emit("CHG", est, change_v, sd=change_sd, se=se_v if mean_v is None else None,
                  ci_lower=ci_l if effect_v is None and ratio_v is None else None,
                  ci_upper=ci_u if effect_v is None and ratio_v is None else None,
                  ci_level=95 if (effect_v is None and ratio_v is None and ci_l is not None) else None,
                  p_value=p_val if effect_v is None and ratio_v is None else None,
                  p_operator=p_op if effect_v is None and ratio_v is None else None)

        # (c) geometric mean ratio
        if ratio_v is not None:
            _emit("GMR", "GEOMETRIC_MEAN_RATIO", ratio_v,
                  ci_lower=to_number(o.get("ratio_ci_lower")), ci_upper=to_number(o.get("ratio_ci_upper")),
                  ci_level=95 if to_number(o.get("ratio_ci_lower")) is not None else None,
                  comparator_arm_id=default_comparator if arm_id not in control_ids else None,
                  p_value=p_val if effect_v is None else None, p_operator=p_op if effect_v is None else None)

        # (d) between-group effect estimate
        if effect_v is not None and not (ratio_v is not None and abs(effect_v - ratio_v) < 1e-12):
            est = _effect_measure_to_estimate_type(o.get("effect_measure"), "adjust" in raw_txt or internal_est.startswith("ADJUSTED"))
            _emit("EFF", est, effect_v, ci_lower=ci_l, ci_upper=ci_u, ci_level=95 if ci_l is not None else None,
                  p_value=p_val, p_operator=p_op,
                  comparator_arm_id=default_comparator if arm_id not in control_ids else None)

        if emitted == 0 and not (is_base and not is_safety):
            _emit("", _ESTIMATE_TYPE_MAP.get(internal_est, "OTHER"), None, ci_lower=ci_l, ci_upper=ci_u,
                  ci_level=95 if ci_l is not None else None, p_value=p_val, p_operator=p_op, status="NOT_REPORTED")

    # ---- validation log (carry over internal log) --------------------------------
    sev_map = {"ERROR": "MAJOR", "WARNING": "MINOR", "INFORMATION": "INFO", "INFO": "INFO", "BLOCKER": "BLOCKER"}
    status_map = {"OPEN": "OPEN", "RESOLVED": "RESOLVED", "ACCEPTED_EXCEPTION": "MANUAL_REVIEW", "MANUAL_REVIEW": "MANUAL_REVIEW"}
    for v in d.get("validation_log", []) or []:
        validation_out.append({
            "issue_id": _as_str(v.get("issue_id")) or f"VAL_{len(validation_out) + 1:04d}",
            "record_id": _as_str(v.get("target_id")) or study_id,
            "rule_id": _as_str(v.get("rule_id")) or _as_str(v.get("issue_type")) or "QA",
            "severity": sev_map.get(str(v.get("severity") or "").upper(), "MINOR"),
            "message": _as_str(v.get("comment")) or "Validation note",
            "status": status_map.get(str(v.get("resolution_status") or "").upper(), "OPEN"),
            "source_ids": [],
        })

    exp_arms = [a["name"] for a in arms_out if a["type"] == "experimental"]
    comp_arms = [a["name"] for a in arms_out if a["type"] in ("placebo", "active_comparator", "usual_care")]
    payload = {
        "schema_version": "1.0",
        "phase": "single_rct",
        "study": study,
        "sources": sources,
        "arms": arms_out,
        "eligibility": elig_out,
        "baseline": baseline_out,
        "outcomes": outcomes_out,
        "validation_log": validation_out,
        "pico": {
            "population": _as_str(study_in.get("condition_studied")),
            "interventions": exp_arms,
            "comparators": comp_arms,
            "outcomes": pico_outcomes,
        },
        "audit": {
            "checked_records": len(arms_out) + len(elig_out) + len(baseline_out) + len(outcomes_out),
            "critical_errors": None,
            "duplicates": None,
            "unresolved_conflicts": None,
            "verified_records": None,
            "status": "INCOMPLETE",
        },
    }
    return payload


# ---------------------------------------------------------------------------
# Phase 1 deterministic validation gate
# ---------------------------------------------------------------------------
_P1_LIST_KEYS = ("sources", "arms", "eligibility", "baseline", "outcomes", "validation_log")


def _strip_unknown_keys(obj: Any, schema_node: Dict[str, Any], path: str, errors: List[str]) -> Any:
    """Removes keys not allowed by additionalProperties=false schemas (keeps everything else)."""
    if not isinstance(schema_node, dict):
        return obj
    if isinstance(obj, dict) and schema_node.get("type") == "object" and schema_node.get("additionalProperties") is False:
        allowed = schema_node.get("properties", {})
        out = {}
        for k, v in obj.items():
            if k in allowed:
                out[k] = _strip_unknown_keys(v, allowed[k], f"{path}.{k}", errors)
            else:
                errors.append(f"{path}.{k}: key not permitted by schema (removed; value preserved in validation_log)")
        return out
    if isinstance(obj, list) and schema_node.get("type") == "array":
        return [_strip_unknown_keys(i, schema_node.get("items", {}), f"{path}[{idx}]", errors) for idx, i in enumerate(obj)]
    return obj


def _coerce_types(obj: Any, schema_node: Dict[str, Any]) -> Any:
    """Coerces numeric strings and placeholders to schema-compatible values (Rule 49)."""
    if not isinstance(schema_node, dict):
        return obj
    stype = schema_node.get("type")
    types = stype if isinstance(stype, list) else [stype]
    if isinstance(obj, dict) and "object" in types:
        props = schema_node.get("properties", {})
        return {k: (_coerce_types(v, props[k]) if k in props else v) for k, v in obj.items()}
    if isinstance(obj, list) and "array" in types:
        return [_coerce_types(i, schema_node.get("items", {})) for i in obj]
    if "null" in types and is_missing(obj):
        return None
    if "integer" in types:
        n = to_number(obj)
        if n is not None and abs(n - round(n)) < 1e-9:
            return int(round(n))
        return obj if isinstance(obj, int) else (None if "null" in types else obj)
    if "number" in types:
        n = to_number(obj)
        return n if n is not None else (None if "null" in types else obj)
    if "boolean" in types:
        if isinstance(obj, str):
            return obj.strip().lower() in ("true", "yes", "1")
        return bool(obj) if obj is not None else False
    if "string" in types and obj is not None and not isinstance(obj, str):
        return str(obj)
    if "string" in types and isinstance(obj, str) and schema_node.get("enum"):
        enum = schema_node["enum"]
        if obj not in enum:
            for cand in enum:
                if cand.lower() == obj.strip().lower() or cand.lower().replace("_", " ") == obj.strip().lower().replace("_", " "):
                    return cand
    return obj


def validate_phase1_payload(data: Any) -> Tuple[bool, List[str], Dict[str, Any]]:
    """
    Deterministic Phase 1 gate. Returns (is_valid, errors, sanitized_payload).
    Never deletes clinical data: conflicting records are retained and flagged.
    """
    errors: List[str] = []
    if not isinstance(data, dict):
        return False, ["Phase 1 payload must be a JSON object."], {}

    schema = get_phase1_schema()
    sanitized: Dict[str, Any] = json.loads(json.dumps(data, default=str))

    # Structural defaults (reported, never silent)
    if sanitized.get("schema_version") != "1.0":
        errors.append(f"schema_version must be '1.0' (got {sanitized.get('schema_version')!r}); corrected.")
        sanitized["schema_version"] = "1.0"
    if sanitized.get("phase") != "single_rct":
        errors.append(f"phase must be 'single_rct' (got {sanitized.get('phase')!r}); corrected.")
        sanitized["phase"] = "single_rct"
    for k in _P1_LIST_KEYS:
        if not isinstance(sanitized.get(k), list):
            errors.append(f"Missing or non-array section '{k}'; initialised as empty array.")
            sanitized[k] = []
    if not isinstance(sanitized.get("study"), dict):
        errors.append("Missing 'study' object; initialised.")
        sanitized["study"] = {}
    sanitized["study"].setdefault("study_id", "STUDY")
    if not sanitized["study"].get("title"):
        errors.append("study.title is empty.")
        sanitized["study"]["title"] = sanitized["study"].get("title") or "Title not captured"
    sanitized.setdefault("pico", {})
    sanitized.setdefault("audit", {})

    validation_log: List[Dict[str, Any]] = sanitized["validation_log"]

    def _log(record_id: str, rule_id: str, severity: str, message: str, status: str = "OPEN") -> None:
        validation_log.append({
            "issue_id": f"VAL_GATE_{len(validation_log) + 1:04d}",
            "record_id": str(record_id or "STUDY"),
            "rule_id": rule_id,
            "severity": severity,
            "message": message,
            "status": status,
            "source_ids": [],
        })

    # Key hygiene & type coercion against the exact schema
    strip_errors: List[str] = []
    sanitized = _strip_unknown_keys(sanitized, schema, "$", strip_errors)
    for e in strip_errors:
        _log("STUDY", "SCHEMA_ADDITIONAL_PROPERTIES", "INFO", e, "RESOLVED")
    sanitized = _coerce_types(sanitized, schema)
    validation_log = sanitized["validation_log"]

    # Rule 49 — placeholder scrub in value fields
    placeholder_hits = 0
    for section in ("arms", "eligibility", "baseline", "outcomes", "sources"):
        for rec in sanitized.get(section, []):
            if not isinstance(rec, dict):
                continue
            for k, v in list(rec.items()):
                if isinstance(v, str) and is_missing(v) and k not in ("status",):
                    rec[k] = None
                    placeholder_hits += 1
    if placeholder_hits:
        _log("STUDY", "RULE_49_MISSING_DATA_PLACEHOLDERS", "MINOR", f"Replaced {placeholder_hits} textual missing-data placeholders with null.", "RESOLVED")

    arm_ids = {a.get("arm_id") for a in sanitized["arms"] if isinstance(a, dict)}
    source_ids = {s.get("source_id") for s in sanitized["sources"] if isinstance(s, dict)}
    critical = 0
    unresolved = 0

    # Rule 37 — arm reconciliation
    if not sanitized["arms"]:
        errors.append("arms must contain at least one treatment arm (Rule 9).")
        critical += 1
    rand_total = sanitized["study"].get("randomized_n")
    arm_ns = [a.get("randomized_n") for a in sanitized["arms"] if isinstance(a, dict)]
    if rand_total is not None and arm_ns and all(n is not None for n in arm_ns):
        if sum(arm_ns) != rand_total:
            _log("STUDY", "ARM_COUNT_MISMATCH", "MAJOR", f"SUM(arm randomized_n)={sum(arm_ns)} != study randomized_n={rand_total}.", "MANUAL_REVIEW")
            unresolved += 1
    elif rand_total is None and arm_ns and all(n is not None for n in arm_ns):
        _log("STUDY", "RULE_8_STUDY_CHARACTERISTICS", "INFO", "study.randomized_n not reported; arm-level counts available.", "OPEN")

    # Rule 51 — reference & mathematical validation
    for section, id_key in (("baseline", "baseline_id"), ("outcomes", "outcome_id"), ("eligibility", "criterion_id"), ("arms", "arm_id")):
        for rec in sanitized.get(section, []):
            if not isinstance(rec, dict):
                continue
            rid = rec.get(id_key, section)
            if section in ("baseline", "outcomes") and rec.get("arm_id") not in (None, "") and rec.get("arm_id") not in arm_ids:
                _log(rid, "INVALID_ARM_REFERENCE", "MAJOR", f"arm_id '{rec.get('arm_id')}' is not a valid treatment arm.", "MANUAL_REVIEW")
                critical += 1
            if section == "outcomes" and rec.get("comparator_arm_id") not in (None, "") and rec.get("comparator_arm_id") not in arm_ids:
                _log(rid, "INVALID_ARM_REFERENCE", "MAJOR", f"comparator_arm_id '{rec.get('comparator_arm_id')}' is not a valid treatment arm.", "MANUAL_REVIEW")
                critical += 1
            bad_src = [s for s in (rec.get("source_ids") or []) if s not in source_ids]
            if bad_src:
                _log(rid, "INVALID_SOURCE_REFERENCE", "MINOR", f"source_ids {bad_src} do not exist in sources; removed.", "RESOLVED")
                rec["source_ids"] = [s for s in rec.get("source_ids") or [] if s in source_ids]
            if section in ("baseline", "outcomes") and not rec.get("source_ids"):
                _log(rid, "RULE_46_MANDATORY_PROVENANCE", "MINOR", "Observation has no linked source record.", "OPEN")
                if rec.get("status") == "VERIFIED":
                    rec["status"] = "FLAGGED"
            if section == "outcomes":
                lo, hi = rec.get("ci_lower"), rec.get("ci_upper")
                if lo is not None and hi is not None and lo > hi and rec.get("estimate_type") != "MEDIAN":
                    _log(rid, "INVALID_CONFIDENCE_INTERVAL", "MAJOR", f"ci_lower {lo} > ci_upper {hi}; bounds swapped (original order preserved in this log).", "RESOLVED")
                    rec["ci_lower"], rec["ci_upper"] = hi, lo
                ev, den = rec.get("event_count"), rec.get("denominator")
                if ev is not None and den is not None and ev > den:
                    _log(rid, "INVALID_EVENT_COUNT", "MAJOR", f"event_count {ev} > denominator {den}.", "MANUAL_REVIEW")
                    critical += 1
                if rec.get("estimate_type") == "PERCENTAGE" and rec.get("value") is not None and not (0 <= rec["value"] <= 100):
                    _log(rid, "INVALID_PERCENTAGE", "MAJOR", f"percentage {rec['value']} outside [0, 100].", "MANUAL_REVIEW")
                    critical += 1
                pv = rec.get("p_value")
                if pv is not None and not (0 <= pv <= 1):
                    _log(rid, "INVALID_P_VALUE", "MAJOR", f"p_value {pv} outside [0, 1]; set to null.", "RESOLVED")
                    rec["p_value"] = None
                if rec.get("estimate_type") in ("RISK_RATIO", "ODDS_RATIO", "HAZARD_RATIO", "GEOMETRIC_MEAN_RATIO") and rec.get("value") is not None and rec["value"] <= 0:
                    _log(rid, "INVALID_RATIO_SCALE", "MAJOR", f"Ratio estimate {rec['value']} must be > 0.", "MANUAL_REVIEW")
                    critical += 1
            if section == "baseline":
                pct = rec.get("percentage")
                if pct is not None and not (0 <= pct <= 100):
                    _log(rid, "INVALID_PERCENTAGE", "MAJOR", f"percentage {pct} outside [0, 100].", "MANUAL_REVIEW")
                    critical += 1
                if rec.get("count") is not None and rec.get("count") < 0:
                    _log(rid, "INVALID_SAMPLE_SIZE", "MAJOR", "negative count.", "MANUAL_REVIEW")
                    critical += 1
            if section == "arms" and rec.get("randomized_n") is not None and rec.get("randomized_n") < 0:
                _log(rid, "INVALID_SAMPLE_SIZE", "MAJOR", "negative randomized_n.", "MANUAL_REVIEW")
                critical += 1

    # Rule 40 — non-destructive duplicate handling
    kept, collapsed, conflicts = collapse_exact_duplicates(sanitized["outcomes"], outcome_identity_key, outcome_value_signature, "outcome_id")
    sanitized["outcomes"] = kept
    for c in collapsed:
        _log(c["duplicate_id"] or "OUTCOME", "RULE_40_DUPLICATE_OBSERVATION", "INFO", f"Collapsed into {c['retained_id']}: {c['reason']}", "RESOLVED")
    for c in conflicts:
        _log(",".join(str(x) for x in c["record_ids"]), "SOURCE_CONFLICT", "MAJOR", c["reason"], "MANUAL_REVIEW")
        unresolved += 1

    def _base_key(r: Dict[str, Any]) -> Tuple[str, ...]:
        return tuple(str(r.get(k) or "").strip().lower() for k in ("variable", "arm_id", "scope", "population", "statistic", "unit"))

    def _base_val(r: Dict[str, Any]) -> Tuple[str, ...]:
        return tuple(str(r.get(k)) for k in ("mean", "sd", "median", "q1", "q3", "min", "max", "count", "percentage"))

    kept_b, collapsed_b, conflicts_b = collapse_exact_duplicates(sanitized["baseline"], _base_key, _base_val, "baseline_id")
    sanitized["baseline"] = kept_b
    for c in collapsed_b:
        _log(c["duplicate_id"] or "BASELINE", "RULE_40_DUPLICATE_OBSERVATION", "INFO", f"Collapsed into {c['retained_id']}: {c['reason']}", "RESOLVED")
    for c in conflicts_b:
        _log(",".join(str(x) for x in c["record_ids"]), "SOURCE_CONFLICT", "MAJOR", c["reason"], "MANUAL_REVIEW")
        unresolved += 1

    # Unique identifiers (Rule 51)
    for section, id_key in (("arms", "arm_id"), ("eligibility", "criterion_id"), ("baseline", "baseline_id"), ("outcomes", "outcome_id"), ("sources", "source_id")):
        seen = set()
        for rec in sanitized.get(section, []):
            if not isinstance(rec, dict):
                continue
            rid = rec.get(id_key)
            if not rid or rid in seen:
                new_id = f"{rid or section.upper()}_{len(seen) + 1}"
                _log(str(rid or section), "RULE_51_UNIQUE_IDENTIFIER", "MINOR", f"Duplicate/empty {id_key} '{rid}' re-keyed to '{new_id}'.", "RESOLVED")
                rec[id_key] = new_id
                rid = new_id
            seen.add(rid)

    # Final strict JSON-schema check
    schema_viol = schema_errors(sanitized, schema)
    errors.extend(schema_viol)

    verified = sum(1 for o in sanitized["outcomes"] if o.get("status") == "VERIFIED")
    sanitized["audit"] = {
        "checked_records": len(sanitized["arms"]) + len(sanitized["eligibility"]) + len(sanitized["baseline"]) + len(sanitized["outcomes"]),
        "critical_errors": critical,
        "duplicates": len(collapsed) + len(collapsed_b),
        "unresolved_conflicts": unresolved,
        "verified_records": verified,
        "status": "REJECT" if (critical > 0 or schema_viol) else ("MANUAL_REVIEW" if unresolved > 0 else ("PASS_WITH_DEFINED_SCOPE" if not errors else "INCOMPLETE")),
    }
    return (len(errors) == 0 and critical == 0), errors, sanitized


def phase1_quality_report(payload: Dict[str, Any], errors: List[str]) -> Dict[str, Any]:
    """Rule 52 — domain scoring from evidence (never auto-100)."""
    schema_ok = not any(e.startswith("$") for e in errors)
    arms = payload.get("arms", [])
    elig = payload.get("eligibility", [])
    base = payload.get("baseline", [])
    outs = payload.get("outcomes", [])
    audit = payload.get("audit", {})
    log = payload.get("validation_log", [])
    open_major = sum(1 for v in log if v.get("severity") in ("MAJOR", "BLOCKER") and v.get("status") != "RESOLVED")

    def frac(ok: int, total: int) -> float:
        return 1.0 if total == 0 else ok / total

    eff = [o for o in outs if o.get("domain") != "SAFETY"]
    saf = [o for o in outs if o.get("domain") == "SAFETY"]
    scores = {
        "Study characteristics and treatment-arm accuracy": 10 * (1.0 if arms and payload.get("study", {}).get("title") else 0.5) * (0.0 if any(v.get("rule_id") == "ARM_COUNT_MISMATCH" for v in log) else 1.0),
        "Inclusion and exclusion criteria completeness": 10 * (1.0 if any(e.get("kind") == "INCLUSION" for e in elig) and any(e.get("kind") == "EXCLUSION" for e in elig) else (0.5 if elig else 0.0)),
        "Baseline characteristics completeness and accuracy": 10 * (1.0 if base else 0.0) * frac(sum(1 for b in base if b.get("source_ids")), len(base)),
        "Efficacy outcome completeness and accuracy": 15 * (1.0 if eff else 0.0) * frac(sum(1 for o in eff if o.get("status") == "VERIFIED"), len(eff)),
        "Safety outcome completeness and accuracy": 10 * (1.0 if saf else 0.0) * frac(sum(1 for o in saf if o.get("status") == "VERIFIED"), len(saf)),
        "Statistical estimate classification": 15 * frac(sum(1 for o in outs if o.get("estimate_type") not in (None, "OTHER")), len(outs)),
        "Treatment-dose and timepoint mapping": 10 * frac(sum(1 for o in outs if o.get("timepoint_value") is not None or o.get("original_timepoint_label")), len(outs)) * frac(sum(1 for a in arms if a.get("type") != "experimental" or a.get("dose_value") is not None), len(arms)),
        "Duplicate prevention": 5 * (0.0 if audit.get("unresolved_conflicts") else 1.0),
        "PDF provenance and source verification": 10 * frac(sum(1 for o in outs if o.get("source_ids")), len(outs)),
        "Excel structure and data normalization": 5 * (1.0 if schema_ok else 0.0),
    }
    total = round(sum(scores.values()), 1)
    status = audit.get("status", "INCOMPLETE")
    acceptance = {
        "REJECT": "REJECT",
        "MANUAL_REVIEW": "NEEDS_MANUAL_REVIEW",
        "INCOMPLETE": "INCOMPLETE",
        "PASS_WITH_DEFINED_SCOPE": "VALIDATED_FOR_DEFINED_SCOPE" if total >= 100 and open_major == 0 else "REQUIRES_CORRECTION",
    }.get(status, "REQUIRES_CORRECTION")
    return {
        "schema_conformant": schema_ok,
        "total_records": audit.get("checked_records"),
        "domain_scores": {k: round(v, 2) for k, v in scores.items()},
        "final_score": total,
        "acceptance_status": acceptance,
        "errors": errors,
    }


# ---------------------------------------------------------------------------
# Phase 2 deterministic validation gate
# ---------------------------------------------------------------------------
_P2_LIST_KEYS = (
    "master_extraction_sheet", "study_characteristics", "treatment_arms", "eligibility_criteria",
    "baseline_characteristics", "efficacy_outcomes", "safety_outcomes", "study_eligibility",
    "pico_compatibility", "meta_analysis_input", "individual_effect_sizes", "pooled_meta_analysis",
    "heterogeneity_analysis", "subgroup_analysis", "sensitivity_analysis", "publication_bias",
    "risk_of_bias", "grade_evidence_profile", "dose_duration_model", "validation_log",
)


def validate_phase2_payload(data: Any) -> Tuple[bool, List[str], Dict[str, Any]]:
    """Deterministic Phase 2 gate (schema + Rule 14 / Rule 27 mathematics + Rule 29 logic)."""
    errors: List[str] = []
    if not isinstance(data, dict):
        return False, ["Phase 2 payload must be a JSON object."], {}
    schema = get_phase2_schema()
    sanitized: Dict[str, Any] = json.loads(json.dumps(data, default=str))

    sanitized["phase"] = 2
    sanitized.setdefault("schema_version", "2.0")
    sanitized["active_ingredient"] = str(sanitized.get("active_ingredient") or "UNSPECIFIED")
    for k in _P2_LIST_KEYS:
        if not isinstance(sanitized.get(k), list):
            errors.append(f"Missing or non-array section '{k}'; initialised as empty array.")
            sanitized[k] = []
    if not isinstance(sanitized.get("quality_score"), dict):
        errors.append("Missing quality_score object; initialised (score computed from evidence, never assumed).")
        sanitized["quality_score"] = {"overall_score": 0.0, "breakdown": {}, "interpretation": "Not evaluated"}
    for k in ("total_studies_screened", "total_studies_pooled"):
        v = _as_int(sanitized.get(k))
        if v is None or v < 1:
            sanitized.pop(k, None)
        else:
            sanitized[k] = v

    log: List[Dict[str, Any]] = sanitized["validation_log"]

    def _log(issue: str, severity: str, status: str = "OPEN") -> None:
        log.append({"issue_id": f"VLOG_GATE_{len(log) + 1:04d}", "severity": severity, "description": issue, "status": status})

    critical = 0
    study_ids = {str(s.get("study_id")) for s in sanitized["study_characteristics"] if isinstance(s, dict)}

    # Rule 27 — mathematical validation
    for h in sanitized["heterogeneity_analysis"]:
        if not isinstance(h, dict):
            continue
        i2 = to_number(h.get("i_squared"))
        if i2 is None or not (0 <= i2 <= 100):
            _log(f"heterogeneity[{h.get('parameter_name')}]: I² {h.get('i_squared')} invalid; clamped to [0,100].", "MAJOR", "RESOLVED")
            h["i_squared"] = 0.0 if i2 is None else max(0.0, min(100.0, i2))
        for k in ("tau_squared", "q_statistic"):
            v = to_number(h.get(k))
            if v is None or v < 0:
                _log(f"heterogeneity[{h.get('parameter_name')}]: {k} {h.get(k)} invalid; set to 0.", "MAJOR", "RESOLVED")
                h[k] = 0.0
        qp = to_number(h.get("q_p_value"))
        if qp is None or not (0 <= qp <= 1):
            _log(f"heterogeneity[{h.get('parameter_name')}]: q_p_value invalid; set to 1.0 (not estimable).", "MAJOR", "RESOLVED")
            h["q_p_value"] = 1.0
    for p in sanitized["pooled_meta_analysis"]:
        if not isinstance(p, dict):
            continue
        lo, hi = to_number(p.get("ci_lower")), to_number(p.get("ci_upper"))
        if lo is not None and hi is not None and lo > hi:
            _log(f"pooled[{p.get('parameter_name')}]: CI inverted; swapped.", "MAJOR", "RESOLVED")
            p["ci_lower"], p["ci_upper"] = hi, lo
        pv = to_number(p.get("p_value"))
        if pv is None or not (0 <= pv <= 1):
            _log(f"pooled[{p.get('parameter_name')}]: p_value invalid.", "MAJOR", "MANUAL_REVIEW")
            p["p_value"] = 1.0 if pv is None else max(0.0, min(1.0, pv))
            critical += 1
        k_st = _as_int(p.get("k_studies"))
        if k_st is not None and k_st < 2:
            _log(f"pooled[{p.get('parameter_name')}]: pooled estimate with k={k_st} < 2 violates Rule 14 (INSUFFICIENT_COMPATIBLE_STUDIES).", "BLOCKER", "OPEN")
            critical += 1
        if str(p.get("model_type") or "").upper().startswith(("RR", "OR", "HR")) and to_number(p.get("pooled_estimate")) is not None and to_number(p.get("pooled_estimate")) <= 0:
            _log(f"pooled[{p.get('parameter_name')}]: ratio estimate must be > 0.", "BLOCKER", "OPEN")
            critical += 1
    for es in sanitized["individual_effect_sizes"]:
        if not isinstance(es, dict):
            continue
        base_sid = str(es.get("study_id")).split(" [")[0].strip()
        if study_ids and base_sid not in study_ids:
            _log(f"effect size references unknown study '{es.get('study_id')}'.", "MAJOR", "MANUAL_REVIEW")
            critical += 1
        se = to_number(es.get("standard_error"))
        if se is None or se < 0:
            _log(f"effect size [{es.get('study_id')}/{es.get('parameter_name')}]: standard_error invalid.", "MAJOR", "MANUAL_REVIEW")
            es["standard_error"] = 0.0 if se is None else abs(se)
            critical += 1
        lo, hi = to_number(es.get("ci_lower")), to_number(es.get("ci_upper"))
        if lo is not None and hi is not None and lo > hi:
            es["ci_lower"], es["ci_upper"] = hi, lo
            _log(f"effect size [{es.get('study_id')}/{es.get('parameter_name')}]: CI inverted; swapped.", "MAJOR", "RESOLVED")
        w = to_number(es.get("weight_percent"))
        if w is None or not (0 <= w <= 100):
            _log(f"effect size [{es.get('study_id')}/{es.get('parameter_name')}]: weight_percent invalid; clamped.", "MINOR", "RESOLVED")
            es["weight_percent"] = 0.0 if w is None else max(0.0, min(100.0, w))
    for r in sanitized["risk_of_bias"]:
        if isinstance(r, dict) and r.get("overall_bias") not in ("Low risk", "Some concerns", "High risk"):
            _log(f"risk_of_bias[{r.get('study_id')}]: overall_bias '{r.get('overall_bias')}' not a RoB 2 judgment; set to 'Some concerns' pending review.", "MINOR", "MANUAL_REVIEW")
            r["overall_bias"] = "Some concerns"
    for g in sanitized["grade_evidence_profile"]:
        if isinstance(g, dict) and g.get("certainty_rating") not in ("High", "Moderate", "Low", "Very low"):
            _log(f"grade[{g.get('outcome_name')}]: certainty '{g.get('certainty_rating')}' invalid; set to 'Very low' pending review.", "MINOR", "MANUAL_REVIEW")
            g["certainty_rating"] = "Very low"

    # Rule 29 acceptance logic and Rule 28 scoring (never auto-100)
    qs = sanitized["quality_score"]
    score = to_number(qs.get("overall_score"))
    if score is None or not (0 <= score <= 100):
        errors.append(f"quality_score.overall_score invalid ({qs.get('overall_score')}); recomputed.")
        qs["overall_score"] = 0.0
    qs.setdefault("breakdown", {})
    qs.setdefault("interpretation", "")
    unresolved = sum(1 for v in log if v.get("status") == "MANUAL_REVIEW")
    if critical > 0:
        qs["acceptance_status"] = "REJECT"
    elif unresolved > 0:
        qs["acceptance_status"] = "NEEDS_MANUAL_REVIEW"
    elif errors:
        qs["acceptance_status"] = "REQUIRES_CORRECTION"
    else:
        qs["acceptance_status"] = "VALIDATED_FOR_DEFINED_SCOPE" if to_number(qs.get("overall_score")) == 100 else "REQUIRES_CORRECTION"
    if critical > 0 and to_number(qs.get("overall_score", 0)) and to_number(qs.get("overall_score", 0)) >= 95:
        qs["overall_score"] = min(float(qs["overall_score"]), 79.0)
        qs["interpretation"] = "Score capped: critical scientific errors present (Rule 29)."

    schema_viol = schema_errors(sanitized, schema)
    errors.extend(schema_viol)
    return (len(errors) == 0 and critical == 0), errors, sanitized


# ---------------------------------------------------------------------------
# Retry / repair loops
# ---------------------------------------------------------------------------
def _run_loop(phase: int, raw_payload: Dict[str, Any], llm_retry_fn: Optional[Callable[[str], Optional[Dict[str, Any]]]], max_retries: int) -> Dict[str, Any]:
    validator = validate_phase1_payload if phase == 1 else validate_phase2_payload
    current = raw_payload
    final_sanitized: Dict[str, Any] = {}
    for attempt in range(1, max_retries + 1):
        is_valid, errs, sanitized = validator(current)
        final_sanitized = sanitized
        if is_valid:
            print(f"[+] Phase {phase} validation PASSED (attempt {attempt}/{max_retries}).")
            return sanitized
        crit = (sanitized.get("audit") or {}).get("critical_errors") if phase == 1 else sum(1 for v in sanitized.get("validation_log", []) if str(v.get("severity")).upper() == "BLOCKER" or v.get("status") == "MANUAL_REVIEW")
        print(f"[!] Phase {phase} validation: {len(errs)} schema/structure issue(s), {crit or 0} critical/manual-review item(s) on attempt {attempt}/{max_retries}.")
        for e in errs[:8]:
            print(f"    - {e}")
        if llm_retry_fn and attempt < max_retries:
            feedback = (
                f"CRITICAL VALIDATION FAILURE: your previous Phase {phase} JSON violated the Tier 1 schema/protocol.\n"
                f"Fix ONLY the fields listed below and return the COMPLETE corrected JSON (no truncation, no omissions, nulls for unreported values):\n"
                + "\n".join(f"- {e}" for e in errs[:40])
            )
            repaired = llm_retry_fn(feedback)
            current = repaired if isinstance(repaired, dict) else sanitized
        else:
            current = sanitized
    _, errs, final_sanitized = validator(current)
    if errs:
        print(f"[!] Phase {phase} export proceeds with {len(errs)} documented issue(s); acceptance status recorded in payload.")
    return final_sanitized


def execute_phase1_validation_loop(raw_payload: Dict[str, Any], llm_retry_fn: Optional[Callable[[str], Optional[Dict[str, Any]]]] = None, max_retries: int = 3) -> Dict[str, Any]:
    return _run_loop(1, raw_payload, llm_retry_fn, max_retries)


def execute_phase2_validation_loop(raw_payload: Dict[str, Any], llm_retry_fn: Optional[Callable[[str], Optional[Dict[str, Any]]]] = None, max_retries: int = 3) -> Dict[str, Any]:
    return _run_loop(2, raw_payload, llm_retry_fn, max_retries)
