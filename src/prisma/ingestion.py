"""
PRISMA Ingestion Service.
Safe, read-only multi-sheet Excel workbook parser with atomic cell-level provenance tracking.
Preserves original values, distinguishes missing data from true zeros, and audits data completeness.
"""

import os
import re
from pathlib import Path
from typing import Any, Optional
import openpyxl
from openpyxl.utils import get_column_letter

from src.prisma.models import (
    PrismaProvenance,
    PrismaArm,
    PrismaEligibility,
    PrismaOutcome,
    PrismaTrial,
    PrismaValidationFinding,
)


class PrismaIngestionService:
    """Read-only ingestion engine for MANDOROS clinical trial Excel workbooks."""

    def __init__(self):
        self.trials: dict[str, PrismaTrial] = {}
        self.validation_findings: list[PrismaValidationFinding] = []
        self.imported_files: list[str] = []

    def ingest_workbooks(self, file_paths: list[str]) -> tuple[dict[str, PrismaTrial], list[PrismaValidationFinding], dict[str, Any]]:
        """
        Ingests multiple Excel workbooks into normalized PRISMA trial structures.
        Does not mutate the source workbooks.
        """
        self.trials.clear()
        self.validation_findings.clear()
        self.imported_files.clear()

        valid_paths = [p for p in file_paths if p and os.path.exists(p) and p.endswith(".xlsx")]
        
        for file_path in valid_paths:
            try:
                self._parse_single_workbook(file_path)
                self.imported_files.append(file_path)
            except Exception as ex:
                # Record parsing error without halting other workbooks
                finding = PrismaValidationFinding(
                    issue_id=f"ERR_INGEST_{len(self.validation_findings) + 1}",
                    study_id=os.path.basename(file_path),
                    target_entity="Workbook",
                    target_id=os.path.basename(file_path),
                    field_name="File_Structure",
                    issue_type="ingestion_error",
                    severity="critical",
                    original_value=file_path,
                    reason=f"Failed to read workbook: {str(ex)}",
                    recommended_action="Verify that the file is a valid uncorrupted Excel workbook (.xlsx).",
                    provenance=PrismaProvenance(source_file=os.path.basename(file_path)),
                )
                self.validation_findings.append(finding)

        # Run cross-trial completeness and consistency checks
        self._audit_cross_trial_completeness()

        overview = self._generate_overview_metrics()
        return self.trials, self.validation_findings, overview

    def _parse_single_workbook(self, file_path: str):
        """Parses a single workbook across all relevant sheets."""
        base_name = os.path.basename(file_path)
        wb = openpyxl.load_workbook(file_path, data_only=True, read_only=True)
        sheet_names = wb.sheetnames

        # Temporary trial container
        raw_studies = self._read_sheet_rows(wb, "Studies", base_name)
        raw_arms = self._read_sheet_rows(wb, "Arms", base_name)
        raw_eligibility = self._read_sheet_rows(wb, "Eligibility", base_name)
        raw_outcomes = self._read_sheet_rows(wb, "Outcomes", base_name)
        raw_val_log = self._read_sheet_rows(wb, "Validation_Log", base_name)

        wb.close()

        # If Studies sheet is available
        if raw_studies:
            for s_row in raw_studies:
                study_id = str(s_row.get("study_id") or "").strip()
                if not study_id:
                    study_id = Path(base_name).stem

                trial = PrismaTrial(
                    study_id=study_id,
                    title=str(s_row.get("title") or "").strip(),
                    authors=str(s_row.get("authors") or "").strip(),
                    publication_year=self._safe_int(s_row.get("publication_year")),
                    journal=str(s_row.get("journal") or "").strip(),
                    doi=str(s_row.get("doi") or "").strip(),
                    study_design=str(s_row.get("study_design") or "").strip(),
                    study_phase=str(s_row.get("study_phase") or "").strip(),
                    condition_studied=str(s_row.get("condition_studied") or "").strip(),
                    total_sample_size=self._safe_int(s_row.get("total_sample_size")),
                    duration_value=self._safe_float(s_row.get("duration_value")),
                    duration_unit=str(s_row.get("duration_unit") or "").strip(),
                    source_file=base_name,
                    sheets_present=sheet_names,
                    provenance=s_row.get("_provenance", PrismaProvenance(source_file=base_name, sheet_name="Studies")),
                )
                self.trials[study_id] = trial
        else:
            # Fallback: Create trial from filename
            study_id = Path(base_name).stem
            trial = PrismaTrial(
                study_id=study_id,
                title=study_id.replace("_", " ").title(),
                source_file=base_name,
                sheets_present=sheet_names,
                provenance=PrismaProvenance(source_file=base_name, sheet_name="Master"),
            )
            self.trials[study_id] = trial

        # Attach Arms
        default_study_id = list(self.trials.keys())[0] if self.trials else Path(base_name).stem
        for a_row in raw_arms:
            s_id = str(a_row.get("study_id") or "").strip() or default_study_id
            if s_id not in self.trials:
                self.trials[s_id] = PrismaTrial(study_id=s_id, source_file=base_name, sheets_present=sheet_names)

            arm = PrismaArm(
                arm_id=str(a_row.get("arm_id") or f"ARM_{len(self.trials[s_id].arms)+1}").strip(),
                study_id=s_id,
                arm_name=str(a_row.get("arm_name") or "Unnamed Arm").strip(),
                intervention_type=str(a_row.get("intervention_type") or "experimental").strip().lower(),
                drug_name=str(a_row.get("drug_name") or "").strip(),
                dose_value=self._safe_float(a_row.get("dose_value")),
                dose_unit=str(a_row.get("dose_unit") or "").strip(),
                frequency_number=self._safe_float(a_row.get("frequency_number")),
                frequency_unit=str(a_row.get("frequency_unit") or "").strip(),
                sample_size_allocated=self._safe_int(a_row.get("sample_size_allocated")),
                sample_size_analyzed=self._safe_int(a_row.get("sample_size_analyzed")),
                source_page=str(a_row.get("source_page") or "").strip(),
                provenance=a_row.get("_provenance", PrismaProvenance(source_file=base_name, sheet_name="Arms")),
            )
            self.trials[s_id].arms.append(arm)

        # Attach Eligibility
        for e_row in raw_eligibility:
            s_id = str(e_row.get("study_id") or "").strip() or default_study_id
            if s_id not in self.trials:
                self.trials[s_id] = PrismaTrial(study_id=s_id, source_file=base_name, sheets_present=sheet_names)

            # Determine operator
            op = ""
            for possible_op in ["less_than (<)", "greater_than (>)", "equal (=)", "between"]:
                if e_row.get(possible_op) is not None and str(e_row.get(possible_op)).strip() != "":
                    op = possible_op.split("(")[0].strip()
                    break

            elig = PrismaEligibility(
                criterion_id=str(e_row.get("criterion_id") or f"CRIT_{len(self.trials[s_id].eligibility)+1}").strip(),
                study_id=s_id,
                criterion_type=str(e_row.get("criterion_type") or "inclusion").strip().lower(),
                domain=str(e_row.get("domain") or "").strip(),
                criterion_name=str(e_row.get("criterion_name") or "").strip(),
                operator=op,
                value=str(e_row.get("value") or "").strip() or None,
                min_value=self._safe_float(e_row.get("min_value")),
                max_value=self._safe_float(e_row.get("max_value")),
                unit=str(e_row.get("unit") or "").strip(),
                raw_source_text=str(e_row.get("raw_source_text") or "").strip(),
                source_page=str(e_row.get("source_page") or "").strip(),
                provenance=e_row.get("_provenance", PrismaProvenance(source_file=base_name, sheet_name="Eligibility")),
            )
            self.trials[s_id].eligibility.append(elig)

        # Attach Outcomes
        for o_row in raw_outcomes:
            s_id = str(o_row.get("study_id") or "").strip() or default_study_id
            if s_id not in self.trials:
                self.trials[s_id] = PrismaTrial(study_id=s_id, source_file=base_name, sheets_present=sheet_names)

            arm_id = str(o_row.get("arm_id") or "").strip()
            # Resolve arm name if possible
            arm_name = ""
            for a in self.trials[s_id].arms:
                if a.arm_id == arm_id:
                    arm_name = a.arm_name
                    break

            tp_val = self._safe_float(o_row.get("Timepoint (value)") or o_row.get("timepoint_value"))
            tp_unit = str(o_row.get("Timepoint (unit)") or o_row.get("timepoint_unit") or "").strip()

            outcome = PrismaOutcome(
                outcome_id=str(o_row.get("outcome_id") or f"OUT_{len(self.trials[s_id].outcomes)+1}").strip(),
                study_id=s_id,
                arm_id=arm_id,
                arm_name=arm_name or arm_id,
                domain=str(o_row.get("domain") or "Efficacy").strip(),
                parameter_name=str(o_row.get("parameter_name") or "").strip(),
                statistical_type=str(o_row.get("statistical_type") or "continuous_mean_sd").strip(),
                timepoint_value=tp_val,
                timepoint_unit=tp_unit,
                sample_size=self._safe_int(o_row.get("sample_size")),
                mean=self._safe_float(o_row.get("mean")),
                sd=self._safe_float(o_row.get("sd")),
                change_value=self._safe_float(o_row.get("change_value")),
                change_sd=self._safe_float(o_row.get("change_sd")),
                events=self._safe_float(o_row.get("events")),
                total=self._safe_float(o_row.get("total")),
                percentage=self._safe_float(o_row.get("percentage")),
                unit=str(o_row.get("unit") or "").strip(),
                effect_measure=str(o_row.get("effect_measure") or "").strip(),
                effect_value=self._safe_float(o_row.get("effect_value")),
                p_value=str(o_row.get("p_value") or "").strip(),
                source_page=str(o_row.get("source_page") or "").strip(),
                raw_source_text=str(o_row.get("raw_source_text") or "").strip(),
                provenance=o_row.get("_provenance", PrismaProvenance(source_file=base_name, sheet_name="Outcomes")),
            )
            self.trials[s_id].outcomes.append(outcome)

        # Ingest pre-existing Validation_Log
        for v_row in raw_val_log:
            s_id = str(v_row.get("study_id") or "").strip() or default_study_id
            finding = PrismaValidationFinding(
                issue_id=str(v_row.get("issue_id") or f"VAL_{len(self.validation_findings)+1}").strip(),
                study_id=s_id,
                target_entity=str(v_row.get("target_entity") or "Study").strip(),
                target_id=str(v_row.get("target_id") or "").strip(),
                field_name=str(v_row.get("field_name") or "").strip(),
                issue_type=str(v_row.get("issue_type") or "validation_finding").strip(),
                severity="warning" if str(v_row.get("review_required") or "").lower() in ["true", "yes", "1"] else "info",
                original_value="",
                reason=str(v_row.get("comment") or "").strip(),
                recommended_action="Review source document against extracted cell value.",
                provenance=v_row.get("_provenance", PrismaProvenance(source_file=base_name, sheet_name="Validation_Log")),
            )
            self.validation_findings.append(finding)
            if s_id in self.trials:
                self.trials[s_id].validation_findings.append(finding)

    def _read_sheet_rows(self, wb: openpyxl.Workbook, sheet_name: str, base_name: str) -> list[dict[str, Any]]:
        """Reads rows from a sheet with exact cell provenance mapping."""
        # Check sheet name or case-insensitive match
        matched_sheet = None
        for name in wb.sheetnames:
            if name.lower() == sheet_name.lower():
                matched_sheet = name
                break
        
        if not matched_sheet:
            return []

        ws = wb[matched_sheet]
        rows = list(ws.iter_rows(values_only=False))
        if len(rows) < 2:
            return []

        headers = [c.value for c in rows[0]]
        cleaned_headers = [str(h).strip() if h is not None else f"col_{i}" for i, h in enumerate(headers)]

        results = []
        for r_idx, row in enumerate(rows[1:], start=2):
            # Check if row is not completely empty
            row_vals = [c.value for c in row]
            if not any(v is not None and str(v).strip() != "" for v in row_vals):
                continue

            row_dict: dict[str, Any] = {}
            for c_idx, cell in enumerate(row):
                if c_idx < len(cleaned_headers):
                    h = cleaned_headers[c_idx]
                    val = cell.value
                    row_dict[h] = val

            # Cell reference for row provenance
            cell_ref = f"{get_column_letter(1)}{r_idx}:{get_column_letter(len(row))}{r_idx}"
            row_dict["_provenance"] = PrismaProvenance(
                source_file=base_name,
                sheet_name=matched_sheet,
                row_index=r_idx,
                cell_ref=cell_ref,
                raw_text=str(row_vals[:4]),
            )
            results.append(row_dict)

        return results

    def _audit_cross_trial_completeness(self):
        """Audits loaded trials for scientific data integrity and completeness."""
        for s_id, trial in self.trials.items():
            # 1. Trial level checks
            if not trial.total_sample_size:
                # Sum of analyzed arm sample sizes
                sum_arms = sum(a.sample_size_analyzed or 0 for a in trial.arms if a.sample_size_analyzed)
                if sum_arms > 0:
                    trial.total_sample_size = sum_arms
                else:
                    self.validation_findings.append(
                        PrismaValidationFinding(
                            issue_id=f"CHK_SS_{s_id}",
                            study_id=s_id,
                            target_entity="Study",
                            target_id=s_id,
                            field_name="total_sample_size",
                            issue_type="missing_data",
                            severity="warning",
                            original_value="None",
                            reason="Total randomized trial sample size is not explicitly reported in study metadata.",
                            recommended_action="Verify trial protocol or abstract for total randomized N.",
                            provenance=PrismaProvenance(source_file=trial.source_file, sheet_name="Studies"),
                        )
                    )

            # 2. Arm level checks
            for arm in trial.arms:
                if arm.sample_size_analyzed is None and arm.sample_size_allocated is None:
                    self.validation_findings.append(
                        PrismaValidationFinding(
                            issue_id=f"CHK_ARM_N_{arm.arm_id}",
                            study_id=s_id,
                            target_entity="Arm",
                            target_id=arm.arm_id,
                            field_name="sample_size",
                            issue_type="missing_data",
                            severity="warning",
                            original_value="None",
                            reason=f"Arm '{arm.arm_name}' lacks explicit sample size (allocated or analyzed).",
                            recommended_action="Inspect Table 1 or Flowchart in source publication.",
                            provenance=arm.provenance,
                        )
                    )
                if arm.intervention_type == "experimental" and not arm.drug_name:
                    self.validation_findings.append(
                        PrismaValidationFinding(
                            issue_id=f"CHK_ARM_DRUG_{arm.arm_id}",
                            study_id=s_id,
                            target_entity="Arm",
                            target_id=arm.arm_id,
                            field_name="drug_name",
                            issue_type="missing_data",
                            severity="info",
                            original_value="None",
                            reason=f"Experimental arm '{arm.arm_name}' does not specify standardized drug name.",
                            recommended_action="Harmonize drug name from arm title or protocol text.",
                            provenance=arm.provenance,
                        )
                    )

            # 3. Outcome level checks
            for outcome in trial.outcomes:
                # If continuous mean reported without SD
                if outcome.mean is not None and outcome.sd is None and outcome.change_sd is None:
                    self.validation_findings.append(
                        PrismaValidationFinding(
                            issue_id=f"CHK_OUT_SD_{outcome.outcome_id}",
                            study_id=s_id,
                            target_entity="Outcome",
                            target_id=outcome.outcome_id,
                            field_name="sd",
                            issue_type="missing_variance",
                            severity="warning",
                            original_value=f"Mean={outcome.mean}, SD=None",
                            reason=f"Outcome '{outcome.parameter_name}' reports Mean without SD or SE. Direct REML continuous pooling requires variance estimation.",
                            recommended_action="Examine figure error bars or calculate SD from 95% CI/p-value.",
                            provenance=outcome.provenance,
                        )
                    )
                # If outcome lacks unit
                if not outcome.unit and outcome.statistical_type.startswith("continuous"):
                    self.validation_findings.append(
                        PrismaValidationFinding(
                            issue_id=f"CHK_OUT_UNIT_{outcome.outcome_id}",
                            study_id=s_id,
                            target_entity="Outcome",
                            target_id=outcome.outcome_id,
                            field_name="unit",
                            issue_type="missing_unit",
                            severity="info",
                            original_value="None",
                            reason=f"Continuous endpoint '{outcome.parameter_name}' has no measurement unit specified.",
                            recommended_action="Confirm whether measurement is %, mg/dL, mmol/L, or scale score.",
                            provenance=outcome.provenance,
                        )
                    )

    def _generate_overview_metrics(self) -> dict[str, Any]:
        """Calculates global metrics across all imported trials."""
        total_trials = len(self.trials)
        total_arms = sum(len(t.arms) for t in self.trials.values())
        total_outcomes = sum(len(t.outcomes) for t in self.trials.values())
        total_elig = sum(len(t.eligibility) for t in self.trials.values())
        total_patients = sum(t.total_sample_size or 0 for t in self.trials.values())
        total_findings = len(self.validation_findings)
        critical_findings = sum(1 for f in self.validation_findings if f.severity == "critical")
        warning_findings = sum(1 for f in self.validation_findings if f.severity == "warning")

        # Unique outcome parameters
        unique_params = set()
        for t in self.trials.values():
            for o in t.outcomes:
                if o.parameter_name:
                    unique_params.add(o.parameter_name.strip())

        # Data completeness score:
        # Penalize missing sample sizes and missing variances
        total_elements = max(1, total_trials * 5 + total_arms * 4 + total_outcomes * 4)
        penalties = warning_findings * 2 + critical_findings * 5
        completeness = max(0.0, min(100.0, 100.0 * (1.0 - (penalties / total_elements))))

        return {
            "workbooks_imported": len(self.imported_files),
            "trials_count": total_trials,
            "arms_count": total_arms,
            "outcomes_count": total_outcomes,
            "unique_parameters_count": len(unique_params),
            "eligibility_criteria_count": total_elig,
            "total_randomized_patients": total_patients,
            "total_findings": total_findings,
            "critical_findings": critical_findings,
            "warning_findings": warning_findings,
            "completeness_score": round(completeness, 1),
        }

    @staticmethod
    def _safe_float(val: Any) -> Optional[float]:
        if val is None:
            return None
        s = str(val).strip().replace(",", "")
        if s.lower() in ["", "none", "not_reported", "nr", "na", "n/a", "null"]:
            return None
        try:
            return float(s)
        except ValueError:
            # Try regex to extract first float
            m = re.search(r"[-+]?\d*\.?\d+", s)
            if m:
                try:
                    return float(m.group(0))
                except ValueError:
                    return None
            return None

    @staticmethod
    def _safe_int(val: Any) -> Optional[int]:
        if val is None:
            return None
        s = str(val).strip().replace(",", "")
        if s.lower() in ["", "none", "not_reported", "nr", "na", "n/a", "null"]:
            return None
        try:
            return int(float(s))
        except ValueError:
            m = re.search(r"\d+", s)
            if m:
                try:
                    return int(m.group(0))
                except ValueError:
                    return None
            return None


def load_prisma_workbooks(file_paths: list[str]) -> tuple[dict[str, PrismaTrial], list[PrismaValidationFinding], dict[str, Any]]:
    """Helper functional wrapper for PrismaIngestionService."""
    service = PrismaIngestionService()
    return service.ingest_workbooks(file_paths)
