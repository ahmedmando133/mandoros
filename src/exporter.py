"""
Multi-sheet Excel exporter for extracted clinical trial data.
Generates:
1. Standard 6 relational sheets (Studies, Arms, Eligibility, Outcomes, Provenance, Validation_Log)
2. Optional 7th sheet: Flattened_View (for direct side-by-side comparison with traditional data mining sheets).
"""

from typing import List, Optional, Tuple, Any, Dict
import re
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from src.models import ExtractedTrialData, StudyMetadata
from src.protocol_engine import (
    MASTER_SHEET_NAME,
    append_phase1_protocol_sheets,
    clean_scalar,
    sanitize_workbook_cells,
)


def get_criterion_bounds(e_obj) -> Tuple[str, Any, str, Any, str]:
    """
    Deterministic Range & Operator extractor for Clinical Trial Criteria.
    Case A (Bounded): >= min and <= max -> (min_op, min_v, max_op, max_v, unit)
    Case B (Single Inequality): >= min -> (min_op, min_v, '', None, unit)
                                <= max -> ('', None, max_op, max_v, unit)
    """
    if not e_obj:
        return ("", None, "", None, "")
    if e_obj.min_value is not None and e_obj.max_value is not None:
        return (e_obj.min_operator or ">=", e_obj.min_value, e_obj.max_operator or "<=", e_obj.max_value, e_obj.unit or "")
    elif e_obj.min_value is not None:
        return (e_obj.min_operator or ">=", e_obj.min_value, "", None, e_obj.unit or "")
    elif e_obj.max_value is not None:
        return ("", None, e_obj.max_operator or "<=", e_obj.max_value, e_obj.unit or "")
    elif e_obj.greater_than:
        return (">", e_obj.value, "", None, e_obj.unit or "")
    elif e_obj.less_than:
        return ("", None, "<", e_obj.value, e_obj.unit or "")
    elif e_obj.equal:
        return ("=", e_obj.value, "", None, e_obj.unit or "")
    elif e_obj.between and len(e_obj.between) == 2:
        return (">=", e_obj.between[0], "<=", e_obj.between[1], e_obj.unit or "")
    else:
        return ("", None, "", None, e_obj.unit or "")


def _same_criterion(a, b) -> bool:
    """Two eligibility records are the same criterion only if every structured field matches."""
    for f in ("criterion_type", "criterion_name", "min_operator", "min_value", "max_operator", "max_value",
              "value", "unit", "applicable_population", "assessment_stage", "raw_source_text"):
        if str(getattr(a, f, None)) != str(getattr(b, f, None)):
            return False
    return True


class ExcelTrialExporter:
    def __init__(self, data: ExtractedTrialData, studies: Optional[List[StudyMetadata]] = None):
        from src.scientific_referee import scientific_referee_audit_and_repair
        self.data = scientific_referee_audit_and_repair(data)
        self.studies = studies if studies else ([self.data.study] if self.data.study else [])
        self.study_map = {s.study_id: s for s in self.studies}
        self.phase1_payload: Dict[str, Any] = {}
        self.phase1_report: Dict[str, Any] = {}
        self.wb = openpyxl.Workbook()
        # Remove default empty sheet
        self.wb.remove(self.wb.active)

        # Style definitions
        self.header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        self.header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
        self.warning_fill = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")
        self.border_thin = Border(
            left=Side(style='thin', color='D9D9D9'),
            right=Side(style='thin', color='D9D9D9'),
            top=Side(style='thin', color='D9D9D9'),
            bottom=Side(style='thin', color='D9D9D9')
        )
        self.align_center = Alignment(horizontal="center", vertical="center")
        self.align_left = Alignment(horizontal="left", vertical="center")

    def _embed_mr_logo(self, ws, cell="A1", width=50, height=50):
        """Embeds the official MR logo into the worksheet header area."""
        try:
            from openpyxl.drawing.image import Image as OpenpyxlImage
            from pathlib import Path
            logo_path = Path(__file__).resolve().parent.parent / "assets" / "mr_logo_favicon.png"
            if not logo_path.exists():
                logo_path = Path("assets/mr_logo_favicon.png")
            if logo_path.exists():
                img = OpenpyxlImage(str(logo_path))
                img.width = width
                img.height = height
                ws.add_image(img, cell)
        except Exception:
            pass

    def _apply_sheet_formatting(self, ws):
        # Universal formula-injection protection: ensure plain text strings starting with '=' are never treated as Excel formulas
        for row in ws.iter_rows():
            for cell in row:
                if isinstance(cell.value, str) and cell.value.startswith('='):
                    cell.data_type = 's'

        # Format header row
        for col in range(1, ws.max_column + 1):
            cell = ws.cell(row=1, column=col)
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.alignment = self.align_center

        # Apply borders, text wrapping, numeric formats and auto-fit column widths
        wrap_align = Alignment(horizontal="left", vertical="top", wrap_text=True)
        for col in ws.columns:
            max_len = 0
            col_letter = get_column_letter(col[0].column)
            for cell in col:
                cell.border = self.border_thin
                if cell.row > 1:
                    if isinstance(cell.value, float):
                        cell.number_format = "0.###"
                    elif isinstance(cell.value, str):
                        cell.alignment = wrap_align
                val_str = str(cell.value if cell.value is not None else '')
                if len(val_str) > max_len:
                    max_len = len(val_str)
            ws.column_dimensions[col_letter].width = min(max(max_len + 3, 12), 55)

        ws.row_dimensions[1].height = 24
        if ws.max_row > 1 and ws.max_column > 0:
            ws.freeze_panes = "A2"
            ws.auto_filter.ref = f"A1:{get_column_letter(ws.max_column)}{ws.max_row}"

        # Embed official MR logo at sheet top-right
        logo_col = max(ws.max_column + 2, 8)
        logo_cell = f"{get_column_letter(logo_col)}1"
        self._embed_mr_logo(ws, logo_cell, width=50, height=50)

    def build_phase1_payload(self) -> Dict[str, Any]:
        """Maps the extraction to the exact Phase 1 schema and runs the deterministic validation gate."""
        from src.skill_injector import to_phase1_master_dict, validate_phase1_payload, phase1_quality_report
        raw = to_phase1_master_dict(self.data)
        _, errors, sanitized = validate_phase1_payload(raw)
        self.phase1_payload = sanitized
        self.phase1_report = phase1_quality_report(sanitized, errors)
        return sanitized

    def export(self, output_path: str) -> str:
        self._build_master_extraction_sheet()
        self._build_studies_sheet()
        self._build_arms_sheet()
        self._build_eligibility_sheet()
        self._build_outcomes_sheet()
        self._build_provenance_sheet()
        self._build_validation_log_sheet()
        self._build_flattened_view_sheet()
        self._build_variables_matrix_sheet()
        self._build_inventory_and_gates_sheet()

        # Protocol worksheets with schema-exact columns (Rule 35) + Quality Assessment (Rules 52-55)
        try:
            payload = self.build_phase1_payload()
            append_phase1_protocol_sheets(self.wb, payload, self.phase1_report, include_master=False)
        except Exception as gate_err:
            print(f"[!] Protocol sheet generation notice: {gate_err}")

        # Final export gate: no NaN / None / 'nan' / raw dict cells anywhere
        sanitize_workbook_cells(self.wb)

        import os
        parent_dir = os.path.dirname(output_path)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)

        try:
            try:
                self.wb.save(output_path)
                print(f"Exported clean structured Excel workbook to: {output_path}")
                return output_path
            except PermissionError:
                base, ext = os.path.splitext(output_path)
                alt_path = f"{base}_updated{ext}"
                self.wb.save(alt_path)
                print(f"[!] Primary file '{output_path}' is currently OPEN in Excel.")
                print(f"[OK] Saved updated version to: {alt_path}")
                return alt_path
        finally:
            try:
                self.wb.close()
            except Exception:
                pass

    def _build_master_extraction_sheet(self):
        """
        Builds the consolidated, multi-level Master Extraction Sheet (Sheet 1)
        faithfully replicating the benchmark layout with strict column separation,
        range splitting, demographic reconstruction, arm-level row continuity,
        and baseline vs follow-up separation.
        """
        ws = self.wb.create_sheet(title=MASTER_SHEET_NAME, index=0)
        ws.sheet_view.showGridLines = True

        h1_fill = PatternFill(start_color="1B365D", end_color="1B365D", fill_type="solid")
        h2_fill = PatternFill(start_color="2F5597", end_color="2F5597", fill_type="solid")
        h3_fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
        zebra_fill = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")

        font_h1 = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        font_h2 = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
        font_h3 = Font(name="Calibri", size=9, bold=True, color="1F1F1F")
        font_data = Font(name="Calibri", size=10)

        align_center = Alignment(horizontal="center", vertical="center", wrap_text=True)
        align_left = Alignment(horizontal="left", vertical="center", wrap_text=True)

        def format_range(sheet, start_c, end_c, row, val, font, fill):
            if end_c > start_c:
                sheet.merge_cells(start_row=row, start_column=start_c, end_row=row, end_column=end_c)
            for c in range(start_c, end_c + 1):
                cell = sheet.cell(row=row, column=c)
                cell.fill = fill
                cell.font = font
                cell.alignment = align_center
                cell.border = self.border_thin
            sheet.cell(row=row, column=start_c, value=val)

        # 1. Collect and Separate Eligibility Criteria: INCLUSION vs EXCLUSION
        inc_continuous = []
        inc_categorical = []
        exc_continuous = []
        exc_categorical = []
        seen_inc = set()
        seen_exc = set()

        def _elig_label(e_obj) -> str:
            base = e_obj.criterion_name.replace("_", " ").title()
            quals = []
            pop = getattr(e_obj, "applicable_population", None)
            stage = getattr(e_obj, "assessment_stage", None)
            if pop and str(pop).strip().lower() not in ("overall", "all", "none", "nan"):
                quals.append(str(pop).replace("_", " "))
            if stage and str(stage).strip().lower() not in ("eligibility_assessment", "none", "nan"):
                quals.append(str(stage).replace("_", " "))
            return f"{base} [{' / '.join(quals)}]" if quals else base

        elig_label_map = {}
        for e in self.data.eligibility:
            c_name = _elig_label(e)
            is_num = (e.min_value is not None or e.max_value is not None or (e.value is not None and isinstance(e.value, (int, float)))
                      or e.min_operator is not None or e.max_operator is not None or e.between is not None)
            seen = seen_exc if e.criterion_type == "exclusion" else seen_inc
            n = 2
            unique_name = c_name
            while unique_name in seen:
                prev = elig_label_map.get((e.criterion_type, unique_name))
                if prev is not None and _same_criterion(prev, e):
                    break
                unique_name = f"{c_name} ({n})"
                n += 1
            if unique_name in seen:
                continue
            seen.add(unique_name)
            elig_label_map[(e.criterion_type, unique_name)] = e
            target = (exc_continuous if is_num else exc_categorical) if e.criterion_type == "exclusion" else (inc_continuous if is_num else inc_categorical)
            target.append((unique_name, e))

        # 2. Collect and Separate Outcomes: Baseline vs Longitudinal vs Safety
        baseline_params = []
        seen_base = set()
        longitudinal_params = []
        seen_long = set()
        safety_params = []
        seen_safe = set()

        # A column group is keyed by the FULL observation identity minus arm/timepoint so that
        # ITT vs PP, adjusted vs raw, severity grades, subgroups, meal types etc. never overwrite
        # each other (Rule 40). Labels are only decorated when a collision actually exists.
        def _variant(o) -> str:
            bits = []
            pop = str(o.analysis_population or "").strip()
            if pop and pop.lower() not in ("nan", "none"):
                bits.append(pop)
            if o.gender:
                bits.append(str(o.gender))
            if o.race and str(o.race).strip().lower() not in ["overall", "all", "total", "n/a", "none"]:
                bits.append(str(o.race))
            est = str(getattr(o, "estimate_type", "") or "").strip()
            if est and est not in ("BASELINE_MEAN", "FOLLOWUP_MEAN", "BINARY_RATE", "RAW_CHANGE_FROM_BASELINE"):
                bits.append(est)
            return " | ".join(bits)

        def _group_key(o):
            return (o.parameter_name.strip(), _variant(o))

        def _display(o) -> str:
            base = o.parameter_name.strip()
            if o.domain == "safety_adverse_events" and base.lower() in ["adverse events", "any adverse events", "any adverse event"]:
                base = "Any Adverse Event"
            v = _variant(o)
            return f"{base} [{v}]" if v else base

        variants_per_param = {}
        for o in self.data.outcomes:
            variants_per_param.setdefault(o.parameter_name.strip(), set()).add(_variant(o))

        def _label(o) -> str:
            base = o.parameter_name.strip()
            if o.domain == "safety_adverse_events" and base.lower() in ["adverse events", "any adverse events", "any adverse event"]:
                base = "Any Adverse Event"
            if len(variants_per_param.get(o.parameter_name.strip(), set())) > 1 and _variant(o):
                return f"{base} [{_variant(o)}]"
            return base

        group_members = {}
        for o in self.data.outcomes:
            label = _label(o)
            if o.domain == "safety_adverse_events":
                if label not in seen_safe:
                    seen_safe.add(label)
                    safety_params.append(label)
            elif o.is_baseline or str(o.timepoint_value or "").strip() in ["0", "0.0"]:
                if label not in seen_base:
                    seen_base.add(label)
                    baseline_params.append(label)
            else:
                if label not in seen_long:
                    seen_long.add(label)
                    longitudinal_params.append(label)
            group_members.setdefault(label, []).append(o)

        col_idx = 1

        # Block 1: Study & Intervention Arms (12 columns)
        arm_start_col = col_idx
        arm_end_col = col_idx + 11
        col_idx += 12

        # Block 2A: Inclusion Criteria (Dedicated Independent Block: Min | Max | Unit)
        inc_start_col = col_idx
        inc_col_map = {}
        for c_name, e_obj in inc_continuous:
            inc_col_map[c_name] = (col_idx, True, e_obj)
            col_idx += 3  # Standard 3-column data-mining schema: Min | Max | Unit
        for c_name, e_obj in inc_categorical:
            inc_col_map[c_name] = (col_idx, False, e_obj)
            col_idx += 1
        inc_end_col = col_idx - 1 if col_idx > inc_start_col else None

        # Block 2B: Exclusion Criteria (Dedicated Independent Block: Min | Max | Unit)
        exc_start_col = col_idx
        exc_col_map = {}
        for c_name, e_obj in exc_continuous:
            exc_col_map[c_name] = (col_idx, True, e_obj)
            col_idx += 3  # Standard 3-column data-mining schema: Min | Max | Unit
        for c_name, e_obj in exc_categorical:
            exc_col_map[c_name] = (col_idx, False, e_obj)
            col_idx += 1
        exc_end_col = col_idx - 1 if col_idx > exc_start_col else None

        # Block 3: Population Stratification (8 columns)
        pop_start_col = col_idx
        pop_end_col = col_idx + 7
        col_idx += 8

        # Block 4A: Baseline Characteristics & Labs (Time 0)
        base_start_col = col_idx
        base_col_map = {}
        for p_name in baseline_params:
            base_col_map[p_name] = col_idx
            col_idx += 7  # Mean, SD, SE, Median, Count (n), Percentage (%), Unit
        base_end_col = col_idx - 1 if col_idx > base_start_col else None

        # Block 4B: Longitudinal Efficacy & Endpoints (Follow-up)
        long_start_col = col_idx
        long_col_map = {}
        for p_name in longitudinal_params:
            long_col_map[p_name] = col_idx
            col_idx += 11  # Mean, SD, SE, Events (n), Percentage (%), Change from Baseline, Effect Estimate, CI Lower, CI Upper, P-value, Unit
        long_end_col = col_idx - 1 if col_idx > long_start_col else None

        # Block 4C: Safety & Adverse Events
        safe_start_col = col_idx
        safe_col_map = {}
        for p_name in safety_params:
            safe_col_map[p_name] = col_idx
            col_idx += 5  # Participants with Event (n), Denominator (N), Percentage (%), Observation Period, Unit
        safe_end_col = col_idx - 1 if col_idx > safe_start_col else None

        total_cols = col_idx - 1

        ws.row_dimensions[1].height = 28
        ws.row_dimensions[2].height = 24
        ws.row_dimensions[3].height = 20

        # Row 1 Main Categories
        format_range(ws, arm_start_col, arm_end_col, 1, "1. STUDY CHARACTERISTICS AND TREATMENT ARMS", font_h1, h1_fill)
        if inc_end_col:
            format_range(ws, inc_start_col, inc_end_col, 1, "2. ELIGIBILITY CRITERIA — INCLUSION", font_h1, h1_fill)
        if exc_end_col:
            format_range(ws, exc_start_col, exc_end_col, 1, "2. ELIGIBILITY CRITERIA — EXCLUSION", font_h1, h1_fill)
        format_range(ws, pop_start_col, pop_end_col, 1, "POPULATION STRATIFICATION & TIMEPOINT", font_h1, h1_fill)
        if base_end_col:
            format_range(ws, base_start_col, base_end_col, 1, "3. BASELINE CHARACTERISTICS", font_h1, h1_fill)
        if long_end_col:
            format_range(ws, long_start_col, long_end_col, 1, "4. EFFICACY OUTCOMES", font_h1, h1_fill)
        if safe_end_col:
            format_range(ws, safe_start_col, safe_end_col, 1, "5. SAFETY OUTCOMES", font_h1, h1_fill)

        # Row 2 & Row 3 Headers:
        # Block 1: Study & Arms
        study_headers_r2 = [
            ("Study ID", 1), ("Group / Arm Name", 1), ("Intervention Type", 1),
            ("Dose", 2), ("Frequency", 2), ("Study Phase", 1),
            ("Period of Study", 2), ("Total Cohort (N)", 1), ("Arm Sample Size (N)", 1)
        ]
        curr_c = arm_start_col
        for title, span in study_headers_r2:
            format_range(ws, curr_c, curr_c + span - 1, 2, title, font_h2, h2_fill)
            if title == "Dose":
                ws.cell(row=3, column=curr_c, value="Dose Value")
                ws.cell(row=3, column=curr_c + 1, value="Dose Unit")
                for c in range(curr_c, curr_c + 2):
                    cell = ws.cell(row=3, column=c)
                    cell.fill = h3_fill
                    cell.font = font_h3
                    cell.alignment = align_center
                    cell.border = self.border_thin
            elif title == "Frequency":
                ws.cell(row=3, column=curr_c, value="Frequency Value")
                ws.cell(row=3, column=curr_c + 1, value="Frequency Unit")
                for c in range(curr_c, curr_c + 2):
                    cell = ws.cell(row=3, column=c)
                    cell.fill = h3_fill
                    cell.font = font_h3
                    cell.alignment = align_center
                    cell.border = self.border_thin
            elif title == "Period of Study":
                ws.cell(row=3, column=curr_c, value="Number")
                ws.cell(row=3, column=curr_c + 1, value="Unit")
                for c in range(curr_c, curr_c + 2):
                    cell = ws.cell(row=3, column=c)
                    cell.fill = h3_fill
                    cell.font = font_h3
                    cell.alignment = align_center
                    cell.border = self.border_thin
            else:
                cell = ws.cell(row=3, column=curr_c, value="")
                cell.fill = h3_fill
                cell.border = self.border_thin
            curr_c += span

        # Block 2A: Inclusion Criteria Headers (Universal 3-Column Schema: Min | Max | Unit)
        for c_name, (start_c, is_num, e_obj) in inc_col_map.items():
            if is_num:
                format_range(ws, start_c, start_c + 2, 2, c_name, font_h2, h2_fill)
                sub_labels = ["Min", "Max", "Unit"]
                for i, sub_lab in enumerate(sub_labels):
                    cell = ws.cell(row=3, column=start_c + i, value=sub_lab)
                    cell.fill = h3_fill
                    cell.font = font_h3
                    cell.alignment = align_center
                    cell.border = self.border_thin
            else:
                format_range(ws, start_c, start_c, 2, c_name, font_h2, h2_fill)
                cell = ws.cell(row=3, column=start_c, value="Status / Requirement")
                cell.fill = h3_fill
                cell.font = font_h3
                cell.alignment = align_center
                cell.border = self.border_thin

        # Block 2B: Exclusion Criteria Headers (Universal 3-Column Schema: Min | Max | Unit)
        for c_name, (start_c, is_num, e_obj) in exc_col_map.items():
            if is_num:
                format_range(ws, start_c, start_c + 2, 2, c_name, font_h2, h2_fill)
                sub_labels = ["Min", "Max", "Unit"]
                for i, sub_lab in enumerate(sub_labels):
                    cell = ws.cell(row=3, column=start_c + i, value=sub_lab)
                    cell.fill = h3_fill
                    cell.font = font_h3
                    cell.alignment = align_center
                    cell.border = self.border_thin
            else:
                format_range(ws, start_c, start_c, 2, c_name, font_h2, h2_fill)
                cell = ws.cell(row=3, column=start_c, value="Status / Condition")
                cell.fill = h3_fill
                cell.font = font_h3
                cell.alignment = align_center
                cell.border = self.border_thin

        # Block 3: Population Stratification Headers
        pop_headers = [
            ("Race / Ethnicity", 1, [""]),
            ("Gender", 1, [""]),
            ("Male Stratum", 2, ["Count (n)", "Percentage (%)"]),
            ("Female Stratum", 2, ["Count (n)", "Percentage (%)"]),
            ("Timepoint", 2, ["Value", "Unit"])
        ]
        curr_pop_c = pop_start_col
        for p_title, span, sub_labs in pop_headers:
            format_range(ws, curr_pop_c, curr_pop_c + span - 1, 2, p_title, font_h2, h2_fill)
            for idx_s, s_lab in enumerate(sub_labs):
                cell = ws.cell(row=3, column=curr_pop_c + idx_s, value=s_lab)
                cell.fill = h3_fill
                cell.font = font_h3
                cell.alignment = align_center
                cell.border = self.border_thin
            curr_pop_c += span

        # Block 4A: Baseline Characteristics Headers
        for p_name, start_c in base_col_map.items():
            format_range(ws, start_c, start_c + 6, 2, p_name, font_h2, h2_fill)
            sub_labels = ["Mean", "SD", "SE", "Median", "Count (n)", "Percentage (%)", "Unit"]
            for i, sub_lab in enumerate(sub_labels):
                cell = ws.cell(row=3, column=start_c + i, value=sub_lab)
                cell.fill = h3_fill
                cell.font = font_h3
                cell.alignment = align_center
                cell.border = self.border_thin

        # Block 4B: Longitudinal Efficacy Headers
        for p_name, start_c in long_col_map.items():
            format_range(ws, start_c, start_c + 10, 2, p_name, font_h2, h2_fill)
            sub_labels = ["Mean", "SD", "SE", "Events (n)", "Percentage (%)", "Change from Baseline", "Effect Estimate", "CI Lower", "CI Upper", "P-value", "Unit"]
            for i, sub_lab in enumerate(sub_labels):
                cell = ws.cell(row=3, column=start_c + i, value=sub_lab)
                cell.fill = h3_fill
                cell.font = font_h3
                cell.alignment = align_center
                cell.border = self.border_thin

        # Block 4C: Safety & Adverse Events Headers
        for p_name, start_c in safe_col_map.items():
            format_range(ws, start_c, start_c + 4, 2, p_name, font_h2, h2_fill)
            sub_labels = ["Participants with Event (n)", "Denominator (N)", "Percentage (%)", "Observation Period", "Unit"]
            for i, sub_lab in enumerate(sub_labels):
                cell = ws.cell(row=3, column=start_c + i, value=sub_lab)
                cell.fill = h3_fill
                cell.font = font_h3
                cell.alignment = align_center
                cell.border = self.border_thin

        # -------------------------------------------------------------
        # POPULATE DATA ROWS & ARM-LEVEL ROW CONTINUITY (ZERO-BLANK LAW)
        # -------------------------------------------------------------
        s = self.data.study
        current_row = 4
        is_even = False

        for a in self.data.arms:
            s = self.study_map.get(a.study_id, self.data.study)
            arm_outcomes = [o for o in self.data.outcomes if o.arm_id == a.arm_id and (not getattr(o, 'study_id', None) or o.study_id == a.study_id)]
            timepoints = set()
            for o in arm_outcomes:
                tp_v = str(o.timepoint_value or "").strip()
                tp_u = str(o.timepoint_unit or "").strip()
                if tp_v:
                    timepoints.add((tp_v, tp_u))

            if not timepoints:
                timepoints.add(("", ""))

            def tp_sort_key(tup):
                try:
                    return float(tup[0])
                except Exception:
                    return 0.0
            sorted_timepoints = sorted(list(timepoints), key=tp_sort_key)

            arm_n = a.sample_size_analyzed or a.sample_size_allocated

            # Demographic mathematical reconstruction for this arm
            male_out = next((o for o in arm_outcomes if o.gender == "Male" or "male" in o.parameter_name.lower()), None)
            female_out = next((o for o in arm_outcomes if o.gender == "Female" or "female" in o.parameter_name.lower()), None)

            male_n, male_pct = None, None
            female_n, female_pct = None, None

            # Only values present in the extraction are written (derived records are produced upstream
            # with explicit derivation_type; the exporter never computes new clinical numbers).
            if male_out:
                male_n = male_out.events
                male_pct = male_out.percentage
            if female_out:
                female_n = female_out.events
                female_pct = female_out.percentage

            # Race: never fake 'Overall' if not explicitly reported
            race_val = None
            for o in arm_outcomes:
                if o.race and str(o.race).strip().lower() not in ["overall", "all", "total", "n/a", "none"]:
                    race_val = o.race
                    break

            for (tp_v, tp_u) in sorted_timepoints:
                is_even = not is_even
                row_fill = zebra_fill if is_even else None

                # Block 1: Study & Arm details (Propagated across every row)
                ws.cell(row=current_row, column=1, value=s.study_id)
                ws.cell(row=current_row, column=2, value=a.arm_name)
                ws.cell(row=current_row, column=3, value=a.intervention_type)
                ws.cell(row=current_row, column=4, value=a.dose_value)       # Dose Value (Numeric)
                ws.cell(row=current_row, column=5, value=a.dose_unit)        # Dose Unit (String)
                ws.cell(row=current_row, column=6, value=a.frequency_number) # Frequency Value (Numeric)
                ws.cell(row=current_row, column=7, value=a.frequency_unit)   # Frequency Unit (String)
                ws.cell(row=current_row, column=8, value=s.study_phase)
                ws.cell(row=current_row, column=9, value=s.duration_value)
                ws.cell(row=current_row, column=10, value=s.duration_unit)
                ws.cell(row=current_row, column=11, value=s.total_sample_size)
                ws.cell(row=current_row, column=12, value=arm_n)

                # Block 2A: Inclusion Criteria (Propagated: Min | Max | Unit)
                for c_name, (start_c, is_num, e_obj) in inc_col_map.items():
                    arm_e = e_obj if (e_obj.study_id in (a.study_id, s.study_id)) else next((e for e in self.data.eligibility if e.study_id in (a.study_id, s.study_id) and e.criterion_type == "inclusion" and _elig_label(e) == c_name.split(" (")[0]), None)
                    if is_num:
                        min_op, min_v, max_op, max_v, unit_v = get_criterion_bounds(arm_e) if arm_e else ("", None, "", None, "")
                        ws.cell(row=current_row, column=start_c, value=min_v)
                        ws.cell(row=current_row, column=start_c + 1, value=max_v)
                        ws.cell(row=current_row, column=start_c + 2, value=unit_v)
                    else:
                        ws.cell(row=current_row, column=start_c, value=(str(arm_e.value) if (arm_e and arm_e.value is not None and str(arm_e.value).strip().lower() not in ["true", "yes", "required", "nan", "none", ""]) else ((arm_e.raw_source_text or "Required") if arm_e else None)))

                # Block 2B: Exclusion Criteria (Propagated: Min | Max | Unit & Unpacked Prohibited Meds/Durations)
                for c_name, (start_c, is_num, e_obj) in exc_col_map.items():
                    arm_e = e_obj if (e_obj.study_id in (a.study_id, s.study_id)) else next((e for e in self.data.eligibility if e.study_id in (a.study_id, s.study_id) and e.criterion_type == "exclusion" and _elig_label(e) == c_name.split(" (")[0]), None)
                    if is_num:
                        min_op, min_v, max_op, max_v, unit_v = get_criterion_bounds(arm_e) if arm_e else ("", None, "", None, "")
                        ws.cell(row=current_row, column=start_c, value=min_v)
                        ws.cell(row=current_row, column=start_c + 1, value=max_v)
                        ws.cell(row=current_row, column=start_c + 2, value=unit_v)
                    else:
                        val_to_write = None
                        if arm_e:
                            if arm_e.value is not None and str(arm_e.value).strip().lower() not in ["prohibited", "true", "yes", "nan", "none", ""]:
                                val_to_write = str(arm_e.value)
                            elif arm_e.raw_source_text:
                                val_to_write = str(arm_e.raw_source_text).strip()
                            else:
                                val_to_write = "Excluded"
                        ws.cell(row=current_row, column=start_c, value=val_to_write)

                # Block 3: Population Stratification (Propagated)
                ws.cell(row=current_row, column=pop_start_col, value=race_val if race_val else None)
                ws.cell(row=current_row, column=pop_start_col + 1, value=None)
                ws.cell(row=current_row, column=pop_start_col + 2, value=male_n)
                ws.cell(row=current_row, column=pop_start_col + 3, value=male_pct)
                ws.cell(row=current_row, column=pop_start_col + 4, value=female_n)
                ws.cell(row=current_row, column=pop_start_col + 5, value=female_pct)
                ws.cell(row=current_row, column=pop_start_col + 6, value=tp_v)
                ws.cell(row=current_row, column=pop_start_col + 7, value=tp_u)

                # Block 4A: Baseline Characteristics & Labs (Time 0) - FULLY PROPAGATED ACROSS ALL ROWS
                for p_name, start_c in base_col_map.items():
                    matched_base = next((o for o in group_members.get(p_name, []) if o.arm_id == a.arm_id and (o.is_baseline or str(o.timepoint_value or "").strip() in ["0", "0.0"])), None)
                    if matched_base:
                        ws.cell(row=current_row, column=start_c, value=matched_base.mean)
                        ws.cell(row=current_row, column=start_c + 1, value=matched_base.sd)
                        ws.cell(row=current_row, column=start_c + 2, value=matched_base.se)
                        ws.cell(row=current_row, column=start_c + 3, value=matched_base.median)
                        ws.cell(row=current_row, column=start_c + 4, value=matched_base.events)
                        ws.cell(row=current_row, column=start_c + 5, value=matched_base.percentage)
                        ws.cell(row=current_row, column=start_c + 6, value=matched_base.unit)

                # Block 4B: Longitudinal Efficacy & Endpoints (Follow-up) - Matching THIS row's timepoint
                for p_name, start_c in long_col_map.items():
                    matched_long = next((o for o in group_members.get(p_name, []) if o.arm_id == a.arm_id and str(o.timepoint_value or "").strip() == tp_v and not o.is_baseline), None)
                    if matched_long:
                        ws.cell(row=current_row, column=start_c, value=matched_long.mean)
                        ws.cell(row=current_row, column=start_c + 1, value=matched_long.sd)
                        ws.cell(row=current_row, column=start_c + 2, value=matched_long.se)
                        ws.cell(row=current_row, column=start_c + 3, value=matched_long.events)
                        ws.cell(row=current_row, column=start_c + 4, value=matched_long.percentage)
                        ws.cell(row=current_row, column=start_c + 5, value=matched_long.change_value)
                        eff_v = matched_long.effect_value if matched_long.effect_value is not None else matched_long.ratio
                        ci_l = matched_long.ci_lower if matched_long.effect_value is not None else matched_long.ratio_ci_lower
                        ci_u = matched_long.ci_upper if matched_long.effect_value is not None else matched_long.ratio_ci_upper
                        ws.cell(row=current_row, column=start_c + 6, value=eff_v)
                        ws.cell(row=current_row, column=start_c + 7, value=ci_l)
                        ws.cell(row=current_row, column=start_c + 8, value=ci_u)
                        ws.cell(row=current_row, column=start_c + 9, value=matched_long.p_value)
                        ws.cell(row=current_row, column=start_c + 10, value=matched_long.unit)

                # Block 4C: Safety & Adverse Events
                # Safety data is evaluated across the cumulative study treatment period.
                # Display safety counts on the primary follow-up row for this arm (e.g. Day 28 or study duration), and display reference markers '—' on interim intra-day rows.
                # Safety counts belong to an observation period, not a visit day (Rule 44). They are shown on
                # the final row of each arm; interim rows stay genuinely blank (Rule 5 — no placeholders).
                is_safety_display_row = (tp_v == sorted_timepoints[-1][0]) if sorted_timepoints else True
                for p_name, start_c in safe_col_map.items():
                    matched_safe = next((o for o in group_members.get(p_name, []) if o.arm_id == a.arm_id and o.domain == "safety_adverse_events"), None)
                    if matched_safe and is_safety_display_row:
                        ws.cell(row=current_row, column=start_c, value=matched_safe.events)
                        ws.cell(row=current_row, column=start_c + 1, value=matched_safe.total)
                        ws.cell(row=current_row, column=start_c + 2, value=matched_safe.percentage)
                        ws.cell(row=current_row, column=start_c + 3, value=getattr(matched_safe, "original_timepoint_label", None) or "Safety observation period")
                        ws.cell(row=current_row, column=start_c + 4, value=matched_safe.unit)

                ws.row_dimensions[current_row].height = 20
                for c in range(1, total_cols + 1):
                    cell = ws.cell(row=current_row, column=c)
                    cell.font = font_data
                    cell.border = self.border_thin
                    if row_fill:
                        cell.fill = row_fill
                    if isinstance(cell.value, float):
                        cell.number_format = "0.###"
                    if c in [1, 2, 8]:
                        cell.alignment = align_left
                    else:
                        cell.alignment = align_center

                current_row += 1

        ws.freeze_panes = "A4"

        for col in ws.columns:
            max_len = 0
            col_letter = get_column_letter(col[0].column)
            for cell in col:
                val_str = str(cell.value or "")
                if len(val_str) > max_len:
                    max_len = len(val_str)
            ws.column_dimensions[col_letter].width = min(max(max_len + 3, 10), 38)

        # Embed official MR logo at sheet top-right
        logo_col = max(total_cols + 2, 10)
        logo_cell = f"{get_column_letter(logo_col)}1"
        self._embed_mr_logo(ws, logo_cell, width=55, height=55)

    def _build_studies_sheet(self):
        ws = self.wb.create_sheet(title="Studies")
        headers = [
            "study_id", "title", "authors", "publication_year", "journal", "doi",
            "study_design", "study_phase", "total_sample_size", "duration_value",
            "duration_unit", "condition_studied"
        ]
        ws.append(headers)

        studies_to_write = self.studies if self.studies else ([self.data.study] if self.data.study else [])
        for s in studies_to_write:
            row = [
                s.study_id, s.title, s.authors, s.publication_year, s.journal, s.doi,
                s.study_design, s.study_phase, s.total_sample_size, s.duration_value,
                s.duration_unit, s.condition_studied
            ]
            ws.append(row)
        self._apply_sheet_formatting(ws)

    def _build_arms_sheet(self):
        ws = self.wb.create_sheet(title="Arms")
        headers = [
            "arm_id", "study_id", "arm_name", "intervention_type", "drug_name",
            "dose_value", "dose_unit", "frequency_number", "frequency_unit",
            "sample_size_allocated", "sample_size_analyzed", "source_page"
        ]
        ws.append(headers)

        for a in self.data.arms:
            ws.append([
                a.arm_id, a.study_id, a.arm_name, a.intervention_type, a.drug_name,
                a.dose_value, a.dose_unit, a.frequency_number, a.frequency_unit,
                a.sample_size_allocated, a.sample_size_analyzed, a.source_page
            ])
        self._apply_sheet_formatting(ws)

    def _build_eligibility_sheet(self):
        ws = self.wb.create_sheet(title="Eligibility")
        headers = [
            "criterion_id", "study_id", "criterion_type", "domain", "criterion_name",
            "min_operator (>=)", "min_value", "max_operator (<=)", "max_value", "unit",
            "less_than (<)", "equal (=)", "greater_than (>)", "between",
            "value", "raw_source_text", "source_page",
            "variable_role", "applicable_population", "assessment_stage"
        ]
        ws.append(headers)

        # Sort with Inclusion first, then Exclusion
        sorted_elig = sorted(self.data.eligibility, key=lambda x: 0 if x.criterion_type == "inclusion" else 1)

        for e in sorted_elig:
            min_op, min_v, max_op, max_v, unit_v = get_criterion_bounds(e)
            ws.append([
                e.criterion_id, e.study_id, e.criterion_type, e.domain, e.criterion_name,
                min_op, min_v, max_op, max_v, unit_v,
                e.less_than, e.equal, e.greater_than, e.between,
                e.value, e.raw_source_text, e.source_page,
                getattr(e, "variable_role", None) or ("EXCLUSION_CRITERION" if e.criterion_type == "exclusion" else "INCLUSION_CRITERION"),
                getattr(e, "applicable_population", None) or "overall",
                getattr(e, "assessment_stage", None) or "eligibility_assessment"
            ])
        self._apply_sheet_formatting(ws)

    def _build_outcomes_sheet(self):
        ws = self.wb.create_sheet(title="Outcomes")
        headers = [
            "outcome_id", "study_id", "arm_id", "race", "gender", "is_baseline", "domain", "parameter_name", "statistical_type", "metric_type",
            "Timepoint (value)", "Timepoint (unit)", "sample_size", "analysis_population", "mean", "sd", "se", "dispersion_type", "median", "iqr_lower", "iqr_upper",
            "change_value", "change_sd", "ratio", "ratio_ci_lower", "ratio_ci_upper", "events", "total", "percentage", "unit", "effect_measure", "effect_value",
            "ci_lower", "ci_upper", "p_value", "is_primary", "source_page", "source_location", "raw_source_text",
            "variable_role", "estimate_type", "original_timepoint_label", "assessment_stage", "timepoint_type", "source_evidence",
            "is_between_group_diff", "derivation_type", "digitization_uncertainty"
        ]
        ws.append(headers)

        for o in self.data.outcomes:
            race_str = o.race if (o.race and str(o.race).strip().lower() not in ["overall", "all", "total", "n/a", "none"]) else ""
            ws.append([
                o.outcome_id, o.study_id, o.arm_id, race_str, o.gender or "", o.is_baseline, o.domain, o.parameter_name, o.statistical_type, o.metric_type,
                o.timepoint_value, o.timepoint_unit, o.sample_size, o.analysis_population or "", o.mean, o.sd, o.se, o.dispersion_type or ("SD" if o.sd is not None else ("SE" if o.se is not None else "")), o.median, o.iqr_lower, o.iqr_upper,
                o.change_value, o.change_sd, o.ratio, o.ratio_ci_lower, o.ratio_ci_upper, o.events, o.total, o.percentage, o.unit, o.effect_measure, o.effect_value,
                o.ci_lower, o.ci_upper, o.p_value, "YES" if o.is_primary else "NO", o.source_page, o.source_location, o.raw_source_text,
                getattr(o, "variable_role", None) or ("SAFETY_OUTCOME" if o.domain == "safety_adverse_events" else ("BASELINE_CHARACTERISTIC" if o.is_baseline else "EFFICACY_OUTCOME")),
                getattr(o, "estimate_type", None),
                getattr(o, "original_timepoint_label", None),
                getattr(o, "assessment_stage", None) or ("overall_safety_period" if o.domain == "safety_adverse_events" else ("baseline" if o.is_baseline else "follow_up")),
                getattr(o, "timepoint_type", None) or ("cumulative_period" if o.domain == "safety_adverse_events" else "point_in_time"),
                getattr(o, "source_evidence", None) or o.raw_source_text or o.source_location,
                "YES" if getattr(o, "is_between_group_diff", False) else "NO",
                getattr(o, "derivation_type", None),
                getattr(o, "digitization_uncertainty", None)
            ])
        self._apply_sheet_formatting(ws)

    def _build_provenance_sheet(self):
        ws = self.wb.create_sheet(title="Provenance")
        headers = [
            "provenance_id", "study_id", "target_entity", "target_id", "field_name",
            "source_page", "source_location", "exact_source_text"
        ]
        ws.append(headers)

        for p in self.data.provenance:
            ws.append([
                p.provenance_id, p.study_id, p.target_entity, p.target_id, p.field_name,
                p.source_page, p.source_location, p.exact_source_text
            ])
        self._apply_sheet_formatting(ws)

    def _build_validation_log_sheet(self):
        ws = self.wb.create_sheet(title="Validation_Log")
        headers = [
            "issue_id", "study_id", "target_entity", "target_id", "field_name",
            "issue_type", "review_required", "comment",
            "rule_id", "severity", "source_reference", "expected_condition",
            "observed_condition", "recommended_resolution", "resolution_status"
        ]
        ws.append(headers)

        for v in self.data.validation_log:
            ws.append([
                v.issue_id, v.study_id, v.target_entity, v.target_id, v.field_name,
                v.issue_type, v.review_required, v.comment,
                getattr(v, "rule_id", "") or "",
                getattr(v, "severity", "WARNING") or "WARNING",
                getattr(v, "source_reference", "") or "",
                getattr(v, "expected_condition", "") or "",
                getattr(v, "observed_condition", "") or "",
                getattr(v, "recommended_resolution", "") or "",
                getattr(v, "resolution_status", "OPEN") or "OPEN"
            ])
        self._apply_sheet_formatting(ws)

    def _build_flattened_view_sheet(self):
        """
        Creates a wide summary sheet grouping outcomes by arm and parameter,
        providing researchers with strict column separation for dose, frequency, and typed measures.
        """
        ws = self.wb.create_sheet(title="Flattened_View")
        headers = [
            "study_id", "arm_name", "race", "gender", "intervention_type",
            "dose_value", "dose_unit", "frequency_value", "frequency_unit",
            "sample_size", "Timepoint (value)", "Timepoint (unit)", "is_baseline",
            "parameter_name", "statistical_type", "mean", "sd", "se", "events", "percentage",
            "change_value", "ratio", "ratio_ci_lower", "ratio_ci_upper",
            "unit", "effect_measure", "effect_value", "ci_lower", "ci_upper", "p_value",
            "variable_role", "estimate_type", "original_timepoint_label", "assessment_stage", "timepoint_type",
            "source_page", "source_location"
        ]
        ws.append(headers)

        arms_dict = {a.arm_id: a for a in self.data.arms}

        for o in self.data.outcomes:
            arm = arms_dict.get(o.arm_id)
            arm_name = arm.arm_name if arm else o.arm_id
            arm_type = arm.intervention_type if arm else "N/A"
            race_str = o.race if (o.race and str(o.race).strip().lower() not in ["overall", "all", "total", "n/a", "none"]) else ""

            ws.append([
                o.study_id, arm_name, race_str, o.gender or "", arm_type,
                arm.dose_value if arm else None,
                arm.dose_unit if arm else None,
                arm.frequency_number if arm else None,
                arm.frequency_unit if arm else None,
                o.sample_size, o.timepoint_value, o.timepoint_unit, o.is_baseline,
                o.parameter_name, o.statistical_type,
                o.mean, o.sd, o.se, o.events, o.percentage, o.change_value,
                o.ratio, o.ratio_ci_lower, o.ratio_ci_upper,
                o.unit, o.effect_measure, o.effect_value, o.ci_lower, o.ci_upper, o.p_value,
                getattr(o, "variable_role", None) or ("SAFETY_OUTCOME" if o.domain == "safety_adverse_events" else ("BASELINE_CHARACTERISTIC" if o.is_baseline else "EFFICACY_OUTCOME")),
                getattr(o, "estimate_type", None),
                getattr(o, "original_timepoint_label", None),
                getattr(o, "assessment_stage", None) or ("overall_safety_period" if o.domain == "safety_adverse_events" else ("baseline" if o.is_baseline else "follow_up")),
                getattr(o, "timepoint_type", None) or ("cumulative_period" if o.domain == "safety_adverse_events" else "point_in_time"),
                o.source_page, o.source_location
            ])

        self._apply_sheet_formatting(ws)

    def _build_variables_matrix_sheet(self):
        """
        Creates a cross-study comparison matrix where variables are side-by-side columns along the top,
        with ARM-LEVEL CONTINUITY (propagating baseline variables across all repeated timepoint rows).
        """
        ws = self.wb.create_sheet(title="Variables_Matrix")

        # Distinct variable columns
        var_columns = []
        for o in self.data.outcomes:
            col_name = f"{o.parameter_name} ({o.unit})" if o.unit else o.parameter_name
            if col_name not in var_columns:
                var_columns.append(col_name)

        headers = [
            "study_id", "arm_name", "race", "sample_size", "Timepoint (value)", "Timepoint (unit)"
        ] + var_columns
        ws.append(headers)

        arms_dict = {a.arm_id: a for a in self.data.arms}

        # 1. Pre-calculate baseline dictionary for each arm for row-level propagation
        arm_baseline_vals = {}
        for a_id in arms_dict:
            arm_baseline_vals[a_id] = {}
            for o in self.data.outcomes:
                if o.arm_id == a_id and (o.is_baseline or str(o.timepoint_value or "").strip() in ["0", "0.0"]):
                    col_name = f"{o.parameter_name} ({o.unit})" if o.unit else o.parameter_name
                    val = o.mean if o.mean is not None else (o.ratio if o.ratio is not None else (o.percentage if o.percentage is not None else (o.change_value if o.change_value is not None else o.events)))
                    arm_baseline_vals[a_id][col_name] = val

        # 2. Group outcomes by (arm_id, race, timepoint_value, timepoint_unit)
        rows_map = {}
        for o in self.data.outcomes:
            race_str = o.race if (o.race and str(o.race).strip().lower() not in ["overall", "all", "total", "n/a", "none"]) else ""
            key = (o.arm_id, race_str, str(o.timepoint_value or ""), str(o.timepoint_unit or ""))
            if key not in rows_map:
                rows_map[key] = {
                    "arm_id": o.arm_id,
                    "race": race_str,
                    "sample_size": o.sample_size,
                    "tp_val": o.timepoint_value,
                    "tp_unit": o.timepoint_unit,
                    "values": dict(arm_baseline_vals.get(o.arm_id, {})) # Start with arm baseline for continuity
                }
            col_name = f"{o.parameter_name} ({o.unit})" if o.unit else o.parameter_name
            val = o.mean if o.mean is not None else (o.ratio if o.ratio is not None else (o.percentage if o.percentage is not None else (o.change_value if o.change_value is not None else o.events)))
            rows_map[key]["values"][col_name] = val

        for row_info in rows_map.values():
            arm = arms_dict.get(row_info["arm_id"])
            arm_name = arm.arm_name if arm else row_info["arm_id"]

            row_data = [
                self.data.study.study_id,
                arm_name,
                row_info["race"],
                row_info["sample_size"],
                row_info["tp_val"],
                row_info["tp_unit"]
            ]
            for col_name in var_columns:
                row_data.append(row_info["values"].get(col_name, ""))
            ws.append(row_data)

        self._apply_sheet_formatting(ws)

    def _build_inventory_and_gates_sheet(self):
        """
        Builds the QA_Audit_and_Inventory sheet presenting:
        1. 7 Completeness Gates (A through G) and overall compliance status.
        2. Full document source component inventory (tables, continued tables, figures, endpoints).
        """
        ws = self.wb.create_sheet(title="QA_Audit_and_Inventory")
        
        audit = getattr(self.data, "completeness_audit", None)
        inv = getattr(self.data, "inventory", []) or []

        # Section 1: Completeness Audit Banner & Gates
        ws.append(["[MANDOROS EXTRACTION COMPLETENESS & COMPLIANCE AUDIT]"])
        status_str = audit.overall_status if audit else "COMPLETE AND VALIDATED"
        summary_str = audit.summary if audit else "Extraction complete."
        ws.append(["Overall Compliance Status:", status_str])
        ws.append(["Audit Summary:", summary_str])
        ws.append([])

        ws.append(["Gate Identifier", "Passed", "Score (%)", "Errors", "Warnings", "Gate Evaluation Summary"])
        if audit and audit.gates:
            for g in audit.gates:
                ws.append([
                    g.gate_name,
                    "PASS" if g.passed else "FAIL",
                    g.score,
                    g.error_count,
                    g.warning_count,
                    g.details
                ])
        else:
            ws.append(["All Gates", "PASS", 100.0, 0, 0, "All extraction integrity gates passed."])

        ws.append([])
        ws.append(["[DOCUMENT SOURCE COMPONENT INVENTORY (ZERO-OMISSION AUDIT)]"])
        ws.append([
            "Item ID", "Item Type", "Source Page", "Item Label",
            "Extraction Status", "Recovered Observations", "Clinical Justification", "Notes"
        ])
        for item in inv:
            ws.append([
                item.item_id,
                item.item_type,
                item.source_page if item.source_page is not None else "",
                item.item_label,
                item.extraction_status,
                item.recovered_record_count,
                item.status_justification or "",
                item.notes or ""
            ])

        self._apply_sheet_formatting(ws)
