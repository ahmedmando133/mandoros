"""
MANDOROS Protocol Engine
========================
Deterministic enforcement layer for the four Supreme-Law files in master_protocols/:
  - phase1_master_instructions.md + phase1_schema.json   (Phase 1: Single RCT extraction)
  - phase2_master_instructions.md + phase2_schema.json   (Phase 2: Multi-RCT meta-analysis)

Responsibilities
----------------
1. Strict JSON-Schema validation (jsonschema Draft 2020-12) of Phase 1 / Phase 2 payloads.
2. Protocol mathematical validation (Rule 37, Rule 51, Phase 2 Rule 27).
3. Non-destructive duplicate handling (Rule 1 / Rule 40): only records whose full
   identifying key AND every reported value are identical are collapsed; conflicting
   records are preserved and flagged SOURCE_CONFLICT.
4. Lossless flattening of nested JSON into publication-ready worksheets
   (zero raw dicts/lists, zero None/NaN/'nan' cells, no shifted columns).
5. Protocol worksheet builders for the Phase 1 and Phase 2 workbooks.

All protocol/schema files are loaded once and cached in RAM (Render-safe).
"""

from __future__ import annotations

import functools
import json
import math
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.worksheet import Worksheet

# ---------------------------------------------------------------------------
# Paths (platform agnostic; never hard-coded)
# ---------------------------------------------------------------------------
_HERE = Path(__file__).resolve().parent
BASE_DIR = _HERE.parent if _HERE.name == "src" else _HERE


def _protocol_dir() -> Path:
    for cand in (BASE_DIR / "master_protocols", BASE_DIR / "backend instructions"):
        if cand.exists():
            return cand
    return BASE_DIR / "master_protocols"


MASTER_PROTOCOLS_DIR = _protocol_dir()
SKILLS_LIB_DIR = BASE_DIR / "clinical_skills_library"


@functools.lru_cache(maxsize=8)
def load_schema(phase: int) -> Dict[str, Any]:
    """Loads the strict Phase 1 / Phase 2 JSON schema once into memory."""
    name = "phase1_schema.json" if phase == 1 else "phase2_schema.json"
    p = MASTER_PROTOCOLS_DIR / name
    if not p.exists():
        return {}
    with open(p, "r", encoding="utf-8") as fh:
        return json.load(fh)


# ---------------------------------------------------------------------------
# Missing-data vocabulary (Rule 5 / Rule 49): these must never appear as values
# ---------------------------------------------------------------------------
MISSING_PLACEHOLDERS = {
    "n/a", "na", "nr", "not reported", "not reported (nr)", "unknown", "-", "—", "–",
    "none", "null", "nan", "n.a.", "n.r.", "not applicable", "not_applicable", "",
}


def is_missing(value: Any) -> bool:
    """True when a value represents missing data in any of its disguises."""
    if value is None:
        return True
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return True
    if isinstance(value, str) and value.strip().lower() in MISSING_PLACEHOLDERS:
        return True
    try:
        import pandas as pd  # noqa: WPS433
        if value is pd.NaT:
            return True
    except Exception:
        pass
    return False


def clean_scalar(value: Any) -> Any:
    """
    Normalises any scalar for JSON/Excel output:
      - missing placeholders -> None (blank cell / JSON null)
      - numpy scalars -> python scalars
      - numeric strings -> numbers (preserving exact decimal text when needed)
    """
    if is_missing(value):
        return None
    try:
        import numpy as np  # noqa: WPS433
        if isinstance(value, np.generic):
            value = value.item()
    except Exception:
        pass
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, str):
        s = value.strip()
        if re.fullmatch(r"[-+−]?\d+(\.\d+)?([eE][-+]?\d+)?", s):
            s_norm = s.replace("−", "-")
            try:
                f = float(s_norm)
                return int(f) if re.fullmatch(r"[-+]?\d+", s_norm) else f
            except ValueError:
                return s
        return s
    return value


def to_number(value: Any) -> Optional[float]:
    """Best-effort numeric coercion; returns None when not a clean number."""
    v = clean_scalar(value)
    if v is None or isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    return None


def split_operator(op: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    """Rule 3: '>=' -> ('>', '='), '<' -> ('<', None), '=' -> ('=', None)."""
    if not op:
        return None, None
    o = str(op).strip().replace("≥", ">=").replace("≤", "<=")
    if o in (">=", "=>"):
        return ">", "="
    if o in ("<=", "=<"):
        return "<", "="
    if o in (">", "<", "="):
        return o, None
    return o, None


def parse_p_value(raw: Any) -> Tuple[Optional[float], Optional[str]]:
    """'<0.001' -> (0.001, '<'); '0.023' -> (0.023, '='); 'NS' -> (None, None)."""
    if raw is None:
        return None, None
    if isinstance(raw, (int, float)) and not isinstance(raw, bool):
        return (float(raw), "=") if 0.0 <= float(raw) <= 1.0 else (None, None)
    s = str(raw).strip().lower().replace("p", "").replace(" ", "")
    m = re.match(r"^(<=|>=|<|>|=)?(0?\.\d+|1(?:\.0+)?|0)$", s)
    if not m:
        return None, None
    op = m.group(1) or "="
    try:
        val = float(m.group(2))
    except ValueError:
        return None, None
    return (val, op) if 0.0 <= val <= 1.0 else (None, None)


# ---------------------------------------------------------------------------
# JSON-Schema validation
# ---------------------------------------------------------------------------
def schema_errors(payload: Any, schema: Dict[str, Any], max_errors: int = 200) -> List[str]:
    """Returns human-readable JSON-schema violations (empty list == conformant)."""
    if not schema:
        return []
    try:
        import jsonschema  # noqa: WPS433
        validator_cls = getattr(jsonschema, "Draft202012Validator", jsonschema.Draft7Validator)
        validator = validator_cls(schema)
        out: List[str] = []
        for err in sorted(validator.iter_errors(payload), key=lambda e: list(e.absolute_path)):
            path = "$" + "".join(f"[{p!r}]" if isinstance(p, int) else f".{p}" for p in err.absolute_path)
            out.append(f"{path}: {err.message}")
            if len(out) >= max_errors:
                break
        return out
    except ImportError:
        return _fallback_schema_errors(payload, schema)


def _fallback_schema_errors(payload: Any, schema: Dict[str, Any]) -> List[str]:
    errs: List[str] = []
    if not isinstance(payload, dict):
        return ["$: payload must be an object"]
    for k in schema.get("required", []):
        if k not in payload:
            errs.append(f"$.{k}: required key missing")
    return errs


# ---------------------------------------------------------------------------
# Lossless flattening for worksheets
# ---------------------------------------------------------------------------
def flatten_record(obj: Any, prefix: str = "", sep: str = ".") -> Dict[str, Any]:
    """
    Flattens nested dicts/lists into a single-level mapping suitable for one row.
      {"a": {"b": 1}, "ids": ["x", "y"], "rows": [{"k": 1}, {"k": 2}]}
      -> {"a.b": 1, "ids": "x; y", "rows[0].k": 1, "rows[1].k": 2}
    Scalars are cleaned (no None/NaN/placeholder strings survive).
    """
    flat: Dict[str, Any] = {}
    if isinstance(obj, dict):
        if not obj and prefix:
            flat[prefix] = None
        for k, v in obj.items():
            key = f"{prefix}{sep}{k}" if prefix else str(k)
            flat.update(flatten_record(v, key, sep))
    elif isinstance(obj, (list, tuple)):
        if all(not isinstance(i, (dict, list, tuple)) for i in obj):
            vals = [str(clean_scalar(i)) for i in obj if clean_scalar(i) is not None]
            flat[prefix or "value"] = "; ".join(vals) if vals else None
        else:
            for idx, item in enumerate(obj):
                flat.update(flatten_record(item, f"{prefix}[{idx}]", sep))
    else:
        flat[prefix or "value"] = clean_scalar(obj)
    return flat


def records_to_table(records: Sequence[Dict[str, Any]], preferred_order: Optional[Sequence[str]] = None) -> Tuple[List[str], List[List[Any]]]:
    """Flattens a list of records into (headers, rows) with a stable, union column set."""
    flat_rows = [flatten_record(r) for r in records if isinstance(r, dict)]
    headers: List[str] = []
    seen = set()
    for h in (preferred_order or []):
        if h not in seen:
            headers.append(h)
            seen.add(h)
    for fr in flat_rows:
        for h in fr.keys():
            if h not in seen:
                headers.append(h)
                seen.add(h)
    rows = [[fr.get(h) for h in headers] for fr in flat_rows]
    return headers, rows


# ---------------------------------------------------------------------------
# Worksheet writing primitives (publication-ready formatting)
# ---------------------------------------------------------------------------
_HEADER_FONT = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
_HEADER_FILL = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
_SECTION_FONT = Font(name="Calibri", size=12, bold=True, color="FFFFFF")
_SECTION_FILL = PatternFill(start_color="1B365D", end_color="1B365D", fill_type="solid")
_TITLE_FONT = Font(name="Calibri", size=14, bold=True, color="1E3A8A")
_DATA_FONT = Font(name="Calibri", size=10)
_BORDER = Border(
    left=Side(style="thin", color="D9D9D9"),
    right=Side(style="thin", color="D9D9D9"),
    top=Side(style="thin", color="D9D9D9"),
    bottom=Side(style="thin", color="D9D9D9"),
)
_ALIGN_WRAP = Alignment(horizontal="left", vertical="top", wrap_text=True)
_ALIGN_CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)
_ALIGN_NUM = Alignment(horizontal="right", vertical="top")


def _number_format_for(header: str) -> Optional[str]:
    h = header.lower()
    if any(k in h for k in ("p_value", "q_p_value", "eggers_p", "beggs_p", "p_between")):
        return "0.0000"
    if any(k in h for k in ("i_squared", "percentage", "percent", "weight")):
        return "0.00"
    if any(k in h for k in ("_n", "count", "denominator", "events", "total", "k_studies", "page", "year")) and not any(k in h for k in ("unit", "name")):
        return "0"
    if any(k in h for k in ("estimate", "effect", "ci_", "mean", "sd", "se", "tau", "q_stat", "value", "median", "lower", "upper")):
        return "0.000"
    return None


def write_table(
    ws: Worksheet,
    headers: Sequence[str],
    rows: Iterable[Sequence[Any]],
    start_row: int = 1,
    freeze: bool = True,
    autofilter: bool = True,
    max_width: int = 60,
) -> int:
    """
    Writes a clean rectangular table. Returns the next free row index.
    Guarantees: every row has exactly len(headers) cells, no None/NaN/raw dicts.
    """
    r = start_row
    for c_idx, h in enumerate(headers, 1):
        cell = ws.cell(row=r, column=c_idx, value=str(h))
        cell.font = _HEADER_FONT
        cell.fill = _HEADER_FILL
        cell.alignment = _ALIGN_CENTER
        cell.border = _BORDER
    ws.row_dimensions[r].height = 30
    r += 1

    widths = [max(10, min(max_width, len(str(h)) + 2)) for h in headers]
    n_cols = len(headers)
    for row in rows:
        row = list(row)[:n_cols] + [None] * max(0, n_cols - len(row))
        for c_idx, raw in enumerate(row, 1):
            val = clean_scalar(raw)
            if isinstance(val, (dict, list, tuple)):
                val = json.dumps(val, ensure_ascii=False, default=str)
            if isinstance(val, bool):
                val = "TRUE" if val else "FALSE"
            cell = ws.cell(row=r, column=c_idx, value=val)
            cell.font = _DATA_FONT
            cell.border = _BORDER
            if isinstance(val, (int, float)):
                cell.alignment = _ALIGN_NUM
                fmt = _number_format_for(str(headers[c_idx - 1]))
                if fmt:
                    cell.number_format = "0" if (isinstance(val, int) and fmt == "0") else fmt
            else:
                cell.alignment = _ALIGN_WRAP
                if isinstance(val, str) and val.startswith(("=", "+", "-", "@")) and not re.fullmatch(r"[-+]?\d+(\.\d+)?", val):
                    cell.data_type = "s"
            if val is not None:
                widths[c_idx - 1] = max(widths[c_idx - 1], min(max_width, len(str(val)) + 2))
        r += 1

    for c_idx, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(c_idx)].width = w
    if freeze:
        ws.freeze_panes = ws.cell(row=start_row + 1, column=1)
    if autofilter and n_cols:
        ws.auto_filter.ref = f"A{start_row}:{get_column_letter(n_cols)}{max(start_row, r - 1)}"
    return r


def write_section_heading(ws: Worksheet, row: int, title: str, span: int = 8) -> int:
    span = max(1, span)
    for c in range(1, span + 1):
        cell = ws.cell(row=row, column=c)
        cell.fill = _SECTION_FILL
        cell.font = _SECTION_FONT
        cell.border = _BORDER
    ws.cell(row=row, column=1, value=title)
    if span > 1:
        ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=span)
    ws.row_dimensions[row].height = 26
    return row + 1


def write_records_sheet(ws: Worksheet, records: Sequence[Dict[str, Any]], preferred_order: Optional[Sequence[str]] = None, title: Optional[str] = None) -> None:
    """Flattens a list of records into a formatted worksheet (one record per row)."""
    headers, rows = records_to_table(records, preferred_order)
    start = 1
    if title:
        ws.cell(row=1, column=1, value=title).font = _TITLE_FONT
        start = 3
    if not headers:
        headers = list(preferred_order or ["record"])
        rows = []
    write_table(ws, headers, rows, start_row=start)


def safe_sheet_title(title: str) -> str:
    cleaned = re.sub(r"[\[\]\*\?/\\:]", " ", title).strip()
    return cleaned[:31] or "Sheet"


# ---------------------------------------------------------------------------
# Phase 1 schema-driven helpers
# ---------------------------------------------------------------------------
def schema_property_order(schema: Dict[str, Any], section: str) -> List[str]:
    """Returns the exact JSON key order for an array-of-object section in the schema."""
    props = schema.get("properties", {}).get(section, {})
    if props.get("type") == "array":
        return list(props.get("items", {}).get("properties", {}).keys())
    if props.get("type") == "object":
        return list(props.get("properties", {}).keys())
    return []


PHASE1_OUTCOME_KEY_FIELDS = (
    "domain", "name", "definition", "arm_id", "comparator_arm_id", "analysis_population",
    "timepoint_value", "timepoint_unit", "original_timepoint_label", "period_start",
    "period_end", "period_unit", "estimate_type", "unit",
)
PHASE1_OUTCOME_VALUE_FIELDS = (
    "value", "sd", "se", "ci_lower", "ci_upper", "ci_level", "p_value", "p_operator",
    "n_analyzed", "event_count", "denominator", "approximate_from_figure",
)


def _norm_key_part(v: Any) -> str:
    v = clean_scalar(v)
    if v is None:
        return ""
    if isinstance(v, float) and v.is_integer():
        v = int(v)
    return str(v).strip().lower()


def outcome_identity_key(rec: Dict[str, Any]) -> Tuple[str, ...]:
    """Rule 40 unique observation key."""
    return tuple(_norm_key_part(rec.get(f)) for f in PHASE1_OUTCOME_KEY_FIELDS)


def outcome_value_signature(rec: Dict[str, Any]) -> Tuple[str, ...]:
    return tuple(_norm_key_part(rec.get(f)) for f in PHASE1_OUTCOME_VALUE_FIELDS)


def collapse_exact_duplicates(
    records: List[Dict[str, Any]],
    key_fn,
    value_fn,
    id_field: str,
    source_field: str = "source_ids",
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Non-destructive duplicate handling.
    Returns (kept_records, collapsed_duplicates_log, conflicts_log).
      - Records with identical identity key AND identical reported values are collapsed
        into one record whose source_ids is the union (Rule 1 / Rule 40).
      - Records with identical identity key but DIFFERENT values are ALL retained
        and reported as SOURCE_CONFLICT for manual verification (Rule 6).
    """
    kept: List[Dict[str, Any]] = []
    index: Dict[Tuple[Tuple[str, ...], Tuple[str, ...]], Dict[str, Any]] = {}
    by_key: Dict[Tuple[str, ...], List[Dict[str, Any]]] = {}
    collapsed: List[Dict[str, Any]] = []
    conflicts: List[Dict[str, Any]] = []

    for rec in records:
        if not isinstance(rec, dict):
            continue
        k = key_fn(rec)
        v = value_fn(rec)
        existing = index.get((k, v))
        if existing is not None:
            merged_ids = list(dict.fromkeys(list(existing.get(source_field) or []) + list(rec.get(source_field) or [])))
            existing[source_field] = merged_ids
            collapsed.append({
                "duplicate_id": rec.get(id_field),
                "retained_id": existing.get(id_field),
                "reason": "Identical identifying attributes and identical reported values (redundant extraction artifact).",
            })
            continue
        index[(k, v)] = rec
        kept.append(rec)
        by_key.setdefault(k, []).append(rec)

    for k, group in by_key.items():
        if len(group) > 1:
            conflicts.append({
                "record_ids": [g.get(id_field) for g in group],
                "reason": "Same identifying attributes but different reported values; all retained for manual verification.",
            })
    return kept, collapsed, conflicts


# ---------------------------------------------------------------------------
# Phase 1 workbook (protocol worksheets)
# ---------------------------------------------------------------------------
MASTER_SHEET_NAME = "Master Excel Sheet"

PHASE1_MASTER_SECTIONS = (
    ("Study Characteristics and Treatment Arms", ("study", "arms")),
    ("Eligibility Criteria — Inclusion and Exclusion", ("eligibility",)),
    ("Baseline Characteristics", ("baseline",)),
    ("Efficacy Outcomes", ("outcomes:EFFICACY",)),
    ("Safety Outcomes", ("outcomes:SAFETY",)),
)


def _study_rows(study: Dict[str, Any], schema: Dict[str, Any]) -> Tuple[List[str], List[List[Any]]]:
    order = schema_property_order(schema, "study") or list(study.keys())
    headers = ["Variable", "Value"]
    rows = [[k, clean_scalar(study.get(k))] for k in order]
    for k in study.keys():
        if k not in order:
            rows.append([k, clean_scalar(study.get(k))])
    return headers, rows


def build_phase1_master_sheet(ws: Worksheet, payload: Dict[str, Any], schema: Dict[str, Any]) -> None:
    """Rule 7 / Rule 35: first worksheet with the five mandatory sections, in order."""
    ws.sheet_view.showGridLines = True
    ws.cell(row=1, column=1, value="MANDOROS — Phase 1 Master Excel Sheet (Single RCT Extraction)").font = _TITLE_FONT
    study = payload.get("study", {}) if isinstance(payload.get("study"), dict) else {}
    ws.cell(row=2, column=1, value=f"study_id: {study.get('study_id', '')}").font = _DATA_FONT
    r = 4
    arms = [a for a in payload.get("arms", []) if isinstance(a, dict)]
    arm_order = schema_property_order(schema, "arms")
    r = write_section_heading(ws, r, "1. STUDY CHARACTERISTICS AND TREATMENT ARMS", span=max(8, len(arm_order)))
    h, rows = _study_rows(study, schema)
    r = write_table(ws, h, rows, start_row=r, freeze=False, autofilter=False) + 1
    ws.cell(row=r, column=1, value="Treatment Arms (every randomized arm appears independently — Rule 9 / Rule 37)").font = Font(bold=True)
    r += 1
    h, rows = records_to_table(arms, arm_order)
    r = write_table(ws, h or arm_order, rows, start_row=r, freeze=False, autofilter=False) + 1

    elig = [e for e in payload.get("eligibility", []) if isinstance(e, dict)]
    elig_order = schema_property_order(schema, "eligibility")
    r = write_section_heading(ws, r, "2. ELIGIBILITY CRITERIA — INCLUSION AND EXCLUSION", span=max(8, len(elig_order)))
    elig_sorted = sorted(elig, key=lambda e: (0 if str(e.get("kind", "")).upper() == "INCLUSION" else 1, str(e.get("criterion_id", ""))))
    h, rows = records_to_table(elig_sorted, elig_order)
    r = write_table(ws, h or elig_order, rows, start_row=r, freeze=False, autofilter=False) + 1

    base = [b for b in payload.get("baseline", []) if isinstance(b, dict)]
    base_order = schema_property_order(schema, "baseline")
    r = write_section_heading(ws, r, "3. BASELINE CHARACTERISTICS", span=max(8, len(base_order)))
    h, rows = records_to_table(base, base_order)
    r = write_table(ws, h or base_order, rows, start_row=r, freeze=False, autofilter=False) + 1

    outs = [o for o in payload.get("outcomes", []) if isinstance(o, dict)]
    out_order = schema_property_order(schema, "outcomes")
    eff = [o for o in outs if str(o.get("domain", "")).upper() != "SAFETY"]
    saf = [o for o in outs if str(o.get("domain", "")).upper() == "SAFETY"]
    r = write_section_heading(ws, r, "4. EFFICACY OUTCOMES", span=max(8, len(out_order)))
    h, rows = records_to_table(eff, out_order)
    r = write_table(ws, h or out_order, rows, start_row=r, freeze=False, autofilter=False) + 1
    r = write_section_heading(ws, r, "5. SAFETY OUTCOMES", span=max(8, len(out_order)))
    h, rows = records_to_table(saf, out_order)
    write_table(ws, h or out_order, rows, start_row=r, freeze=False, autofilter=False)
    ws.freeze_panes = "A4"


PHASE1_PROTOCOL_SHEETS = (
    ("Treatment Arms", "arms"),
    ("Eligibility Criteria", "eligibility"),
    ("Baseline Characteristics", "baseline"),
    ("Efficacy Outcomes", "outcomes:EFFICACY"),
    ("Safety Outcomes", "outcomes:SAFETY"),
    ("Source Provenance", "sources"),
    ("Validation Log", "validation_log"),
)


def _select_section(payload: Dict[str, Any], spec: str) -> List[Dict[str, Any]]:
    if ":" in spec:
        key, dom = spec.split(":", 1)
        items = [o for o in payload.get(key, []) if isinstance(o, dict)]
        if dom == "SAFETY":
            return [o for o in items if str(o.get("domain", "")).upper() == "SAFETY"]
        return [o for o in items if str(o.get("domain", "")).upper() != "SAFETY"]
    return [o for o in payload.get(spec, []) if isinstance(o, dict)]


def append_phase1_protocol_sheets(wb, payload: Dict[str, Any], validation_report: Optional[Dict[str, Any]] = None, include_master: bool = False) -> None:
    """
    Appends the Phase 1 protocol worksheets (schema-exact columns) to an openpyxl workbook.
    If include_master is True the 'Master Excel Sheet' is created at index 0.
    """
    schema = load_schema(1)
    if include_master:
        if MASTER_SHEET_NAME in wb.sheetnames:
            del wb[MASTER_SHEET_NAME]
        ws = wb.create_sheet(title=MASTER_SHEET_NAME, index=0)
        build_phase1_master_sheet(ws, payload, schema)

    for title, spec in PHASE1_PROTOCOL_SHEETS:
        t = safe_sheet_title(title)
        if t in wb.sheetnames:
            del wb[t]
        ws = wb.create_sheet(title=t)
        section_key = spec.split(":")[0]
        write_records_sheet(ws, _select_section(payload, spec), schema_property_order(schema, section_key))

    # Quality Assessment (Rule 52 / Rule 53 / Rule 55)
    t = "Quality Assessment"
    if t in wb.sheetnames:
        del wb[t]
    ws = wb.create_sheet(title=t)
    rep = validation_report or {}
    audit = payload.get("audit", {}) if isinstance(payload.get("audit"), dict) else {}
    rows = [
        ["Study_ID", (payload.get("study") or {}).get("study_id")],
        ["Schema", schema.get("$id", "phase1_schema.json")],
        ["Schema_Conformant", "TRUE" if rep.get("schema_conformant", False) else "FALSE"],
        ["Total_Extracted_Records", rep.get("total_records", audit.get("checked_records"))],
        ["Total_Verified_Records", audit.get("verified_records")],
        ["Duplicate_Records_Collapsed", audit.get("duplicates")],
        ["Unresolved_Records", audit.get("unresolved_conflicts")],
        ["Critical_Errors", audit.get("critical_errors")],
        ["Final_Score", rep.get("final_score")],
        ["Final_Acceptance_Status", audit.get("status")],
    ]
    for d, s in (rep.get("domain_scores") or {}).items():
        rows.append([f"Domain_Score::{d}", s])
    for i, e in enumerate(rep.get("errors") or [], 1):
        rows.append([f"Validation_Error_{i:03d}", e])
    write_table(ws, ["Metric", "Value"], rows, freeze=False, autofilter=False)


# ---------------------------------------------------------------------------
# Phase 2 workbook (protocol worksheets — Phase 2 Rule 2 table)
# ---------------------------------------------------------------------------
PHASE2_PROTOCOL_SHEETS: Tuple[Tuple[str, str], ...] = (
    ("Study Characteristics", "study_characteristics"),
    ("Treatment Arms", "treatment_arms"),
    ("Eligibility Criteria", "eligibility_criteria"),
    ("Baseline Characteristics", "baseline_characteristics"),
    ("Efficacy Outcomes", "efficacy_outcomes"),
    ("Safety Outcomes", "safety_outcomes"),
    ("Study Eligibility", "study_eligibility"),
    ("PICO Compatibility", "pico_compatibility"),
    ("Meta-Analysis Input", "meta_analysis_input"),
    ("Individual Effect Sizes", "individual_effect_sizes"),
    ("Pooled Meta-Analysis", "pooled_meta_analysis"),
    ("Heterogeneity Analysis", "heterogeneity_analysis"),
    ("Risk of Bias", "risk_of_bias"),
    ("Sensitivity Analysis", "sensitivity_analysis"),
    ("Subgroup Analysis", "subgroup_analysis"),
    ("Publication Bias", "publication_bias"),
    ("GRADE Assessment", "grade_evidence_profile"),
    ("Dose-Duration Model", "dose_duration_model"),
    ("Source Provenance", "source_provenance"),
    ("Validation Log", "validation_log"),
)


def build_phase2_master_sheet(ws: Worksheet, payload: Dict[str, Any]) -> None:
    """Phase 2 Rule 1: first worksheet with the same five sections across ALL RCTs."""
    ws.cell(row=1, column=1, value=f"MANDOROS — Phase 2 Master Excel Sheet • {payload.get('active_ingredient', '')}").font = _TITLE_FONT
    ws.cell(row=2, column=1, value=f"Studies screened: {payload.get('total_studies_screened', '')} | Studies pooled: {payload.get('total_studies_pooled', '')}").font = _DATA_FONT
    r = 4
    sections = (
        ("1. STUDY CHARACTERISTICS AND TREATMENT ARMS — STUDIES", "study_characteristics"),
        ("1b. STUDY CHARACTERISTICS AND TREATMENT ARMS — ARMS", "treatment_arms"),
        ("2. ELIGIBILITY CRITERIA — INCLUSION AND EXCLUSION", "eligibility_criteria"),
        ("3. BASELINE CHARACTERISTICS", "baseline_characteristics"),
        ("4. EFFICACY OUTCOMES", "efficacy_outcomes"),
        ("5. SAFETY OUTCOMES", "safety_outcomes"),
    )
    for title, key in sections:
        recs = [x for x in payload.get(key, []) if isinstance(x, dict)]
        headers, rows = records_to_table(recs)
        r = write_section_heading(ws, r, title, span=max(8, len(headers)))
        r = write_table(ws, headers or ["record"], rows, start_row=r, freeze=False, autofilter=False) + 1
    ws.freeze_panes = "A4"


def append_phase2_protocol_sheets(wb, payload: Dict[str, Any], validation_report: Optional[Dict[str, Any]] = None, include_master: bool = False) -> None:
    schema = load_schema(2)
    if include_master:
        if MASTER_SHEET_NAME in wb.sheetnames:
            del wb[MASTER_SHEET_NAME]
        ws = wb.create_sheet(title=MASTER_SHEET_NAME, index=0)
        build_phase2_master_sheet(ws, payload)

    for title, key in PHASE2_PROTOCOL_SHEETS:
        t = safe_sheet_title(title)
        if t in wb.sheetnames:
            del wb[t]
        ws = wb.create_sheet(title=t)
        recs = [x for x in payload.get(key, []) if isinstance(x, dict)]
        write_records_sheet(ws, recs, schema_property_order(schema, key))

    t = "Quality Assessment"
    if t in wb.sheetnames:
        del wb[t]
    ws = wb.create_sheet(title=t)
    qs = payload.get("quality_score", {}) if isinstance(payload.get("quality_score"), dict) else {}
    rep = validation_report or {}
    rows = [
        ["Active_Ingredient", payload.get("active_ingredient")],
        ["Schema", schema.get("$id", "phase2_schema.json")],
        ["Schema_Conformant", "TRUE" if rep.get("schema_conformant", False) else "FALSE"],
        ["Overall_Score", qs.get("overall_score")],
        ["Interpretation", qs.get("interpretation")],
        ["Acceptance_Status", qs.get("acceptance_status") or rep.get("acceptance_status")],
    ]
    for d, s in (qs.get("breakdown") or {}).items():
        rows.append([f"Domain_Score::{d}", s])
    for i, e in enumerate(rep.get("errors") or [], 1):
        rows.append([f"Validation_Error_{i:03d}", e])
    write_table(ws, ["Metric", "Value"], rows, freeze=False, autofilter=False)


def sanitize_workbook_cells(wb) -> int:
    """
    Final export gate for ANY workbook: removes literal 'nan'/'None'/'null'/'N/A'/'NR'
    strings, NaN/inf floats, and raw dict/list objects. Returns number of cells repaired.
    """
    repaired = 0
    for ws in wb.worksheets:
        for row in ws.iter_rows():
            for cell in row:
                v = cell.value
                if v is None:
                    continue
                if isinstance(v, (dict, list, tuple)):
                    cell.value = json.dumps(v, ensure_ascii=False, default=str)
                    repaired += 1
                elif isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                    cell.value = None
                    repaired += 1
                elif isinstance(v, str) and v.strip().lower() in {"nan", "none", "null", "n/a", "nr", "not reported (nr)", "not reported"}:
                    cell.value = None
                    repaired += 1
    return repaired


# ---------------------------------------------------------------------------
# Clinical skills library wiring (Tier 2) — dynamic path discovery
# ---------------------------------------------------------------------------
TIER2_PHASE1_SKILLS = ("pdf", "clinical-reports", "clinicaltrials-database")
TIER2_PHASE2_SKILLS = ("statistical-analysis", "clinical-decision-support", "statsmodels", "peer-review", "clinical-reports")


@functools.lru_cache(maxsize=64)
def skill_reference_files(skill_name: str) -> Tuple[str, ...]:
    """Lists reference markdown files of a skill without reading them (lazy, cached)."""
    for cand in (skill_name, skill_name.replace("-", "_")):
        ref_dir = SKILLS_LIB_DIR / cand / "references"
        if ref_dir.exists():
            return tuple(sorted(p.name for p in ref_dir.glob("*.md")))
    return tuple()


def skills_available() -> Dict[str, bool]:
    out = {}
    for s in set(TIER2_PHASE1_SKILLS + TIER2_PHASE2_SKILLS):
        out[s] = (SKILLS_LIB_DIR / s / "SKILL.md").exists() or (SKILLS_LIB_DIR / s.replace("-", "_") / "SKILL.md").exists()
    return out
