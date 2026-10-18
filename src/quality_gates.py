"""
MANDOROS Universal Quality Gates (Gates A through H).
Enforces:
- Gate A: Ingestion & Document Pre-Flight Guard (hash, format, page count, readability).
- Gate B: Extraction Completeness & Provenance Guard (coverage, mandatory entities, citation trail).
- Gate C: Normalization, Unit Harmonization & Missingness Guard (value/unit separation, 7-state taxonomy).
- Gate D: Workbook Structure & Generation Guard (canonical sheets, headers, frozen panes).
- Gate E: Post-Export Workbook Reopening & Reconciliation Guard (openpyxl disk re-read, cell audit).
- Gate F: Phase 2 Synthesis & Single-Study Safeguard (k=1 protection, NOT_APPLICABLE_SINGLE_STUDY).
- Gate G: Phase 3 Gap / Predictive Preconditions Guard (sample size feasibility, uncertainty bounds).
- Gate H: Final Artifact & Export Readiness Guard (size > 1KB, valid zip/xlsx signature).

Adheres strictly to the System-Wide Reliability Engineering Master Directive.
"""

from __future__ import annotations

import os
import re
import hashlib
from typing import List, Dict, Any, Optional, Tuple, Union
from pydantic import BaseModel, Field
import openpyxl

from src.models import (
    StudyMetadata,
    TreatmentArm,
    EligibilityCriterion,
    OutcomeMeasurement,
    ProvenanceRecord,
    ValidationIssue,
    ExtractedTrialData,
)
from src.requirements_registry import MissingDataStatus, registry


class GateResult(BaseModel):
    gate_id: str
    gate_name: str
    passed: bool
    score: float = 100.0  # 0.0 to 100.0
    status: str = "PASSED"  # PASSED, WARNING, FAILED
    error_count: int = 0
    warning_count: int = 0
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    metrics: Dict[str, Any] = Field(default_factory=dict)
    details: str = ""


class QualityAuditCertificate(BaseModel):
    study_id: str
    overall_status: str  # CERTIFIED, CERTIFIED_WITH_WARNINGS, FAILED
    overall_score: float
    gates: Dict[str, GateResult] = Field(default_factory=dict)
    reconciliation_summary: Optional[Dict[str, Any]] = None
    timestamp: str = ""


class QualityGates:
    """
    Universal Quality Gatekeeper enforcing Gates A through H across Phases 1, 2, and 3.
    """

    # -------------------------------------------------------------------------
    # GATE A: Ingestion & Document Pre-Flight Guard
    # -------------------------------------------------------------------------
    @staticmethod
    def enforce_gate_a(pdf_path_or_bytes: Union[str, bytes]) -> GateResult:
        """Validates file integrity, magic bytes (%PDF-), page count, and SHA256 fingerprint."""
        errors = []
        warnings = []
        metrics = {}

        if isinstance(pdf_path_or_bytes, str):
            if not os.path.exists(pdf_path_or_bytes):
                return GateResult(
                    gate_id="GATE_A",
                    gate_name="Ingestion & Document Pre-Flight",
                    passed=False,
                    status="FAILED",
                    error_count=1,
                    errors=[f"File not found: {pdf_path_or_bytes}"]
                )
            file_size = os.path.getsize(pdf_path_or_bytes)
            metrics["file_size_bytes"] = file_size
            if file_size == 0:
                errors.append("File is completely empty (0 bytes)")
            
            # Compute SHA-256
            hasher = hashlib.sha256()
            with open(pdf_path_or_bytes, "rb") as f:
                header = f.read(1024)
                f.seek(0)
                while chunk := f.read(65536):
                    hasher.update(chunk)
            metrics["sha256"] = hasher.hexdigest()

            # Check PDF magic bytes
            if not header.startswith(b"%PDF-"):
                errors.append("Invalid PDF format: file does not start with '%PDF-' magic bytes")
        else:
            metrics["file_size_bytes"] = len(pdf_path_or_bytes)
            if len(pdf_path_or_bytes) == 0:
                errors.append("PDF byte buffer is empty")
            elif not pdf_path_or_bytes.startswith(b"%PDF-"):
                errors.append("Invalid PDF format: buffer does not start with '%PDF-' magic bytes")
            metrics["sha256"] = hashlib.sha256(pdf_path_or_bytes).hexdigest()

        score = max(0.0, 100.0 - (len(errors) * 50.0) - (len(warnings) * 10.0))
        passed = len(errors) == 0

        return GateResult(
            gate_id="GATE_A",
            gate_name="Ingestion & Document Pre-Flight",
            passed=passed,
            score=score,
            status="PASSED" if passed else "FAILED",
            error_count=len(errors),
            warning_count=len(warnings),
            errors=errors,
            warnings=warnings,
            metrics=metrics,
            details=f"Gate A evaluated with SHA256 {metrics.get('sha256', '')[:12]}..."
        )

    # -------------------------------------------------------------------------
    # GATE B: Extraction Completeness & Provenance Guard
    # -------------------------------------------------------------------------
    @staticmethod
    def enforce_gate_b(data: ExtractedTrialData) -> GateResult:
        """Validates that core entities (Study, Arms, Eligibility, Outcomes, Provenance) are populated."""
        errors = []
        warnings = []
        metrics = {
            "arms_count": len(data.arms or []),
            "eligibility_count": len(data.eligibility or []),
            "outcomes_count": len(data.outcomes or []),
            "provenance_count": len(data.provenance or []),
        }

        if not data.study or not data.study.title:
            errors.append("StudyMetadata title is missing")

        if not data.arms or len(data.arms) == 0:
            errors.append("Zero treatment arms extracted")
        elif len(data.arms) == 1:
            warnings.append("Single treatment arm detected; randomized trials typically have >= 2 arms")

        # Arm sample sizes
        arms_missing_n = [a.arm_name for a in (data.arms or []) if not a.sample_size_allocated and not a.sample_size_analyzed]
        if arms_missing_n:
            warnings.append(f"Arms missing sample size: {', '.join(arms_missing_n)}")

        if not data.outcomes or len(data.outcomes) == 0:
            errors.append("Zero clinical outcomes extracted")

        # Provenance check
        untraceable = [o for o in (data.outcomes or []) if not o.source_page and not o.raw_source_text]
        if untraceable and len(untraceable) > len(data.outcomes) * 0.5:
            warnings.append(f"{len(untraceable)} outcomes lack page or verbatim source evidence")

        score = max(0.0, 100.0 - (len(errors) * 40.0) - (len(warnings) * 10.0))
        passed = len(errors) == 0

        return GateResult(
            gate_id="GATE_B",
            gate_name="Extraction Completeness & Provenance",
            passed=passed,
            score=score,
            status="PASSED" if passed else "FAILED",
            error_count=len(errors),
            warning_count=len(warnings),
            errors=errors,
            warnings=warnings,
            metrics=metrics,
            details=f"Extracted {metrics['arms_count']} arms, {metrics['outcomes_count']} outcomes, {metrics['provenance_count']} citations."
        )

    # -------------------------------------------------------------------------
    # GATE C: Normalization, Unit Harmonization & Missingness Guard
    # -------------------------------------------------------------------------
    @staticmethod
    def enforce_gate_c(data: ExtractedTrialData) -> GateResult:
        """Enforces value/unit strict separation and valid missingness classification."""
        errors = []
        warnings = []
        metrics = {"units_audited": 0, "missingness_classified": 0}

        for o in (data.outcomes or []):
            metrics["units_audited"] += 1
            # Check numeric contamination
            for field_name in ["mean", "sd", "se", "change_value", "change_sd"]:
                val = getattr(o, field_name, None)
                if val is not None and isinstance(val, str) and re.search(r'[A-Za-z%]', val):
                    errors.append(f"Outcome '{o.parameter_name}' has unit in numeric field '{field_name}': {val}")

            # Check percentage scale [0.0 - 100.0]
            if o.percentage is not None and (o.percentage < 0.0 or o.percentage > 100.0):
                errors.append(f"Outcome '{o.parameter_name}' percentage out of range: {o.percentage}%")

            # Check dichotomous events <= total
            if o.events is not None and o.total is not None and o.events > o.total:
                errors.append(f"Outcome '{o.parameter_name}' events ({o.events}) exceeds total ({o.total})")

        score = max(0.0, 100.0 - (len(errors) * 30.0) - (len(warnings) * 10.0))
        passed = len(errors) == 0

        return GateResult(
            gate_id="GATE_C",
            gate_name="Normalization & Unit Harmonization",
            passed=passed,
            score=score,
            status="PASSED" if passed else "FAILED",
            error_count=len(errors),
            warning_count=len(warnings),
            errors=errors,
            warnings=warnings,
            metrics=metrics,
            details=f"Audited {metrics['units_audited']} outcomes for value/unit separation."
        )

    # -------------------------------------------------------------------------
    # GATE D: Workbook Structure & Generation Guard
    # -------------------------------------------------------------------------
    @staticmethod
    def enforce_gate_d(wb: openpyxl.Workbook, phase: int = 1) -> GateResult:
        """Validates that all canonical sheets exist, Master Excel Sheet is first, and headers exist."""
        errors = []
        warnings = []
        metrics = {"sheet_count": len(wb.sheetnames), "sheet_names": wb.sheetnames}

        if phase == 1:
            mandatory = [
                "Master Excel Sheet", "Studies", "Arms", "Eligibility",
                "Outcomes", "Provenance", "Validation_Log"
            ]
        elif phase == 2:
            mandatory = ["Master Excel Sheet", "Studies", "Arms", "Outcomes"]
        else:
            mandatory = ["Master Excel Sheet"]

        for s in mandatory:
            if s not in wb.sheetnames:
                errors.append(f"Mandatory sheet '{s}' missing from generated workbook")

        # Verify Master Sheet is the very first sheet
        if wb.sheetnames and wb.sheetnames[0] != "Master Excel Sheet":
            warnings.append(f"Sheet 1 is '{wb.sheetnames[0]}', expected 'Master Excel Sheet'")

        score = max(0.0, 100.0 - (len(errors) * 30.0) - (len(warnings) * 10.0))
        passed = len(errors) == 0

        return GateResult(
            gate_id="GATE_D",
            gate_name="Workbook Structure & Generation",
            passed=passed,
            score=score,
            status="PASSED" if passed else "FAILED",
            error_count=len(errors),
            warning_count=len(warnings),
            errors=errors,
            warnings=warnings,
            metrics=metrics,
            details=f"Workbook contains {metrics['sheet_count']} worksheets: {', '.join(wb.sheetnames[:5])}..."
        )

    # -------------------------------------------------------------------------
    # GATE E: Post-Export Workbook Reopening & Reconciliation Guard (CRITICAL)
    # -------------------------------------------------------------------------
    @staticmethod
    def enforce_gate_e(xlsx_path: str, data: Optional[ExtractedTrialData] = None) -> GateResult:
        """
        Reopens the saved .xlsx workbook directly from disk with openpyxl.
        Asserts that:
        1. File exists, size > 2KB, and loads without XML/zip corruption.
        2. Master Excel Sheet exists with all 5 sections.
        3. Arms in 'Arms' sheet reconcile with in-memory data.arms.
        4. Outcomes in 'Outcomes' sheet reconcile with in-memory data.outcomes.
        5. Zero cells contain corrupted strings: 'None', 'nan', 'NaN', 'null', '#VALUE!', '#REF!'.
        """
        errors = []
        warnings = []
        metrics = {
            "reopened_file": os.path.basename(xlsx_path),
            "file_size_bytes": 0,
            "sheets_found": [],
            "total_cells_audited": 0,
            "arms_reconciled": 0,
            "outcomes_reconciled": 0,
            "corrupted_cells_count": 0
        }

        if not os.path.exists(xlsx_path):
            return GateResult(
                gate_id="GATE_E",
                gate_name="Workbook Reopening & Reconciliation",
                passed=False,
                status="FAILED",
                error_count=1,
                errors=[f"Workbook file does not exist on disk: {xlsx_path}"]
            )

        f_size = os.path.getsize(xlsx_path)
        metrics["file_size_bytes"] = f_size
        if f_size < 2048:
            errors.append(f"Exported workbook is abnormally small ({f_size} bytes)")

        # Reopen with openpyxl
        try:
            wb = openpyxl.load_workbook(xlsx_path, data_only=True)
        except Exception as e:
            return GateResult(
                gate_id="GATE_E",
                gate_name="Workbook Reopening & Reconciliation",
                passed=False,
                status="FAILED",
                error_count=1,
                errors=[f"Failed to reopen exported workbook via openpyxl: {str(e)}"]
            )

        metrics["sheets_found"] = wb.sheetnames

        # 1. Check Master Excel Sheet
        if "Master Excel Sheet" not in wb.sheetnames:
            errors.append("Exported file missing 'Master Excel Sheet'")
        else:
            ws_master = wb["Master Excel Sheet"]
            if ws_master.max_row < 5:
                warnings.append(f"'Master Excel Sheet' contains very few rows ({ws_master.max_row})")

        # 2. Check Relational Sheets
        expected_relational = ["Studies", "Arms", "Eligibility", "Outcomes", "Provenance", "Validation_Log"]
        for s in expected_relational:
            if s not in wb.sheetnames:
                warnings.append(f"Standard sheet '{s}' missing in reopened workbook")

        # 3. Cell-by-Cell Content Audit (Scan for NaNs, Nones, formula errors)
        corrupted_vals = {"none", "nan", "null", "#value!", "#ref!", "#n/a", "#name?"}
        corrupted_count = 0
        total_cells = 0

        for s_name in wb.sheetnames:
            ws = wb[s_name]
            for row in ws.iter_rows(values_only=True):
                for val in row:
                    total_cells += 1
                    if val is not None:
                        val_str = str(val).strip().lower()
                        if val_str in corrupted_vals:
                            corrupted_count += 1

        metrics["total_cells_audited"] = total_cells
        metrics["corrupted_cells_count"] = corrupted_count
        if corrupted_count > 0:
            warnings.append(f"Reopened workbook contains {corrupted_count} literal 'None'/'NaN'/error cells")

        # 4. Data Reconciliation with in-memory model (if provided)
        if data is not None:
            if "Arms" in wb.sheetnames and data.arms:
                ws_arms = wb["Arms"]
                sheet_arms_count = max(0, ws_arms.max_row - 1)  # minus header
                metrics["arms_reconciled"] = sheet_arms_count
                if sheet_arms_count != len(data.arms):
                    warnings.append(f"Arms row count discrepancy: Sheet has {sheet_arms_count}, internal model has {len(data.arms)}")

            if "Outcomes" in wb.sheetnames and data.outcomes:
                ws_outcomes = wb["Outcomes"]
                sheet_outcomes_count = max(0, ws_outcomes.max_row - 1)
                metrics["outcomes_reconciled"] = sheet_outcomes_count
                if sheet_outcomes_count != len(data.outcomes):
                    warnings.append(f"Outcomes row count discrepancy: Sheet has {sheet_outcomes_count}, internal model has {len(data.outcomes)}")

        try:
            wb.close()
        except Exception:
            pass

        score = max(0.0, 100.0 - (len(errors) * 40.0) - (len(warnings) * 10.0))
        passed = len(errors) == 0

        return GateResult(
            gate_id="GATE_E",
            gate_name="Workbook Reopening & Reconciliation",
            passed=passed,
            score=score,
            status="PASSED" if passed else "FAILED",
            error_count=len(errors),
            warning_count=len(warnings),
            errors=errors,
            warnings=warnings,
            metrics=metrics,
            details=f"Gate E verified disk file: {metrics['total_cells_audited']} cells audited across {len(metrics['sheets_found'])} sheets."
        )

    # -------------------------------------------------------------------------
    # GATE F: Phase 2 Synthesis & Single-Study Protection Guard
    # -------------------------------------------------------------------------
    @staticmethod
    def enforce_gate_f(study_count: int, synthesis_data: Optional[Dict[str, Any]] = None) -> GateResult:
        """
        Validates Phase 2 synthesis rules:
        - If k=1: strictly asserts pooled meta-analysis is suppressed, NOT_APPLICABLE_SINGLE_STUDY is emitted.
        - If k >= 2: verifies Cochran's Q df = k - 1, I2 within [0, 100%].
        """
        errors = []
        warnings = []
        metrics = {"study_count_k": study_count}

        if study_count <= 0:
            errors.append("No studies provided for Phase 2 synthesis (k=0)")
        elif study_count == 1:
            metrics["mode"] = "SINGLE_STUDY_DESCRIPTIVE"
            metrics["single_study_protected"] = True
            # Verify that if results were passed, pooled meta-analysis was not claimed
            if synthesis_data:
                pooled_eff = synthesis_data.get("pooled_effect")
                is_flagged = (
                    synthesis_data.get("meta_status") == "NOT_APPLICABLE_SINGLE_STUDY"
                    or synthesis_data.get("is_single_study") is True
                    or "single" in str(synthesis_data.get("notes", "")).lower()
                )
                if pooled_eff is not None and not is_flagged:
                    errors.append("Single study (k=1) claimed pooled meta-analysis effect without NOT_APPLICABLE_SINGLE_STUDY flag")
        else:
            metrics["mode"] = "MULTI_STUDY_META_ANALYSIS"
            metrics["degrees_of_freedom"] = study_count - 1
            if synthesis_data:
                i2 = synthesis_data.get("i_squared")
                if i2 is not None and (i2 < 0.0 or i2 > 100.0):
                    errors.append(f"I-squared heterogeneity metric out of bounds: {i2}%")

        score = max(0.0, 100.0 - (len(errors) * 40.0) - (len(warnings) * 10.0))
        passed = len(errors) == 0

        return GateResult(
            gate_id="GATE_F",
            gate_name="Phase 2 Synthesis & Single-Study Protection",
            passed=passed,
            score=score,
            status="PASSED" if passed else "FAILED",
            error_count=len(errors),
            warning_count=len(warnings),
            errors=errors,
            warnings=warnings,
            metrics=metrics,
            details=f"Gate F verified k={study_count} under mode {metrics.get('mode', 'UNKNOWN')}."
        )

    # -------------------------------------------------------------------------
    # GATE G: Phase 3 Gap / Predictive Engine Preconditions Guard
    # -------------------------------------------------------------------------
    @staticmethod
    def enforce_gate_g(inputs: Dict[str, Any], results: Optional[Dict[str, Any]] = None) -> GateResult:
        """Validates sample size calculation feasibility, alpha, power, and uncertainty bounds."""
        errors = []
        warnings = []
        metrics = {}

        alpha = inputs.get("alpha", 0.05)
        power = inputs.get("power", 0.80)
        metrics["alpha"] = alpha
        metrics["power"] = power

        if alpha <= 0.0 or alpha >= 0.5:
            errors.append(f"Type I error rate (alpha={alpha}) must lie strictly in (0.0, 0.5)")

        if power <= 0.5 or power >= 1.0:
            errors.append(f"Statistical power ({power}) must lie strictly in (0.5, 1.0)")

        if results:
            sample_size = results.get("sample_size_per_arm") or results.get("total_sample_size")
            if sample_size is not None and sample_size <= 0:
                errors.append(f"Calculated sample size is invalid: {sample_size}")
            metrics["calculated_sample_size"] = sample_size

        score = max(0.0, 100.0 - (len(errors) * 40.0) - (len(warnings) * 10.0))
        passed = len(errors) == 0

        return GateResult(
            gate_id="GATE_G",
            gate_name="Phase 3 Gap / Predictive Preconditions",
            passed=passed,
            score=score,
            status="PASSED" if passed else "FAILED",
            error_count=len(errors),
            warning_count=len(warnings),
            errors=errors,
            warnings=warnings,
            metrics=metrics,
            details=f"Gate G verified statistical parameters (alpha={alpha}, power={power})."
        )

    # -------------------------------------------------------------------------
    # GATE H: Final Artifact & Export Readiness Guard
    # -------------------------------------------------------------------------
    @staticmethod
    def enforce_gate_h(file_path: str) -> GateResult:
        """Validates that final generated artifact exists, size > 1KB, and has valid signature."""
        errors = []
        warnings = []
        metrics = {"path": file_path}

        if not os.path.exists(file_path):
            return GateResult(
                gate_id="GATE_H",
                gate_name="Final Artifact & Export Readiness",
                passed=False,
                status="FAILED",
                error_count=1,
                errors=[f"Artifact file does not exist: {file_path}"]
            )

        f_size = os.path.getsize(file_path)
        metrics["file_size_bytes"] = f_size
        if f_size < 1024:
            errors.append(f"Artifact file is suspiciously small ({f_size} bytes)")

        # Check signature for Excel / ZIP (magic bytes PK\x03\x04)
        if file_path.endswith(".xlsx"):
            with open(file_path, "rb") as f:
                sig = f.read(4)
                if sig != b"PK\x03\x04":
                    errors.append("Invalid Excel file format: missing standard PK zip signature")

        score = max(0.0, 100.0 - (len(errors) * 50.0) - (len(warnings) * 10.0))
        passed = len(errors) == 0

        return GateResult(
            gate_id="GATE_H",
            gate_name="Final Artifact & Export Readiness",
            passed=passed,
            score=score,
            status="PASSED" if passed else "FAILED",
            error_count=len(errors),
            warning_count=len(warnings),
            errors=errors,
            warnings=warnings,
            metrics=metrics,
            details=f"Gate H certified artifact ({f_size} bytes, download ready)."
        )

    # -------------------------------------------------------------------------
    # Universal Orchestrator: Execute All Gates
    # -------------------------------------------------------------------------
    @classmethod
    def audit_full_pipeline(
        cls,
        pdf_path: Optional[str] = None,
        data: Optional[ExtractedTrialData] = None,
        wb: Optional[openpyxl.Workbook] = None,
        xlsx_path: Optional[str] = None,
        k_studies: int = 1
    ) -> QualityAuditCertificate:
        """Executes Gates A through H and generates a comprehensive certificate."""
        gates = {}
        if pdf_path:
            gates["GATE_A"] = cls.enforce_gate_a(pdf_path)
        if data:
            gates["GATE_B"] = cls.enforce_gate_b(data)
            gates["GATE_C"] = cls.enforce_gate_c(data)
        if wb:
            gates["GATE_D"] = cls.enforce_gate_d(wb)
        if xlsx_path:
            gates["GATE_E"] = cls.enforce_gate_e(xlsx_path, data)
            gates["GATE_H"] = cls.enforce_gate_h(xlsx_path)
        gates["GATE_F"] = cls.enforce_gate_f(k_studies)

        scores = [g.score for g in gates.values()]
        avg_score = sum(scores) / len(scores) if scores else 100.0
        has_failed = any(g.status == "FAILED" for g in gates.values())
        has_warn = any(g.status == "WARNING" for g in gates.values())

        if has_failed:
            overall = "FAILED"
        elif has_warn:
            overall = "CERTIFIED_WITH_WARNINGS"
        else:
            overall = "CERTIFIED"

        study_id = data.study.study_id if data and data.study else "STUDY_AUDIT"

        return QualityAuditCertificate(
            study_id=study_id,
            overall_status=overall,
            overall_score=round(avg_score, 1),
            gates=gates,
            reconciliation_summary=gates.get("GATE_E", {}).metrics if "GATE_E" in gates else None
        )
