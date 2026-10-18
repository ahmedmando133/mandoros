"""
PRISMA Models & Data Structures.
Strict, strongly-typed representations for clinical trial intelligence, provenance, and readiness.
"""

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class PrismaProvenance:
    """Cell-level and text-level provenance citation linking back to source workbook."""
    source_file: str = ""
    sheet_name: str = ""
    row_index: int = 0
    cell_ref: str = ""
    raw_text: str = ""

    def citation(self) -> str:
        loc = []
        if self.source_file:
            loc.append(self.source_file)
        if self.sheet_name:
            loc.append(f"Sheet: {self.sheet_name}")
        if self.cell_ref:
            loc.append(f"Cell: {self.cell_ref}")
        elif self.row_index > 0:
            loc.append(f"Row: {self.row_index}")
        return " | ".join(loc) if loc else "Provenance: Unspecified"

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_file": self.source_file,
            "sheet_name": self.sheet_name,
            "row_index": self.row_index,
            "cell_ref": self.cell_ref,
            "raw_text": self.raw_text,
            "citation": self.citation(),
        }


@dataclass
class PrismaArm:
    """Intervention or comparator treatment arm extracted from an RCT."""
    arm_id: str
    study_id: str
    arm_name: str
    intervention_type: str = "experimental"  # experimental, active_comparator, placebo, control
    drug_name: str = ""
    dose_value: Optional[float] = None
    dose_unit: str = ""
    frequency_number: Optional[float] = None
    frequency_unit: str = ""
    sample_size_allocated: Optional[int] = None
    sample_size_analyzed: Optional[int] = None
    source_page: str = ""
    provenance: PrismaProvenance = field(default_factory=PrismaProvenance)

    def dose_label(self) -> str:
        parts = []
        if self.drug_name:
            parts.append(self.drug_name)
        if self.dose_value is not None:
            parts.append(f"{self.dose_value} {self.dose_unit}".strip())
        if self.frequency_number is not None:
            freq = f"{self.frequency_number} {self.frequency_unit}".strip()
            parts.append(f"({freq})")
        return " ".join(parts) if parts else self.arm_name

    def to_dict(self) -> dict[str, Any]:
        return {
            "arm_id": self.arm_id,
            "study_id": self.study_id,
            "arm_name": self.arm_name,
            "intervention_type": self.intervention_type,
            "drug_name": self.drug_name,
            "dose_value": self.dose_value,
            "dose_unit": self.dose_unit,
            "dose_label": self.dose_label(),
            "frequency_number": self.frequency_number,
            "frequency_unit": self.frequency_unit,
            "sample_size_allocated": self.sample_size_allocated,
            "sample_size_analyzed": self.sample_size_analyzed,
            "source_page": self.source_page,
            "provenance": self.provenance.to_dict(),
        }


@dataclass
class PrismaEligibility:
    """Eligibility criteria (inclusion / exclusion) with strict operators."""
    criterion_id: str
    study_id: str
    criterion_type: str = "inclusion"  # inclusion, exclusion
    domain: str = ""
    criterion_name: str = ""
    operator: str = ""  # <, >, =, between
    value: Optional[str] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    unit: str = ""
    raw_source_text: str = ""
    source_page: str = ""
    provenance: PrismaProvenance = field(default_factory=PrismaProvenance)

    def formatted_condition(self) -> str:
        if self.operator == "between" and self.min_value is not None and self.max_value is not None:
            return f"{self.criterion_name}: {self.min_value} - {self.max_value} {self.unit}".strip()
        if self.operator and self.value:
            return f"{self.criterion_name} {self.operator} {self.value} {self.unit}".strip()
        if self.value:
            return f"{self.criterion_name}: {self.value} {self.unit}".strip()
        return self.raw_source_text or self.criterion_name

    def to_dict(self) -> dict[str, Any]:
        return {
            "criterion_id": self.criterion_id,
            "study_id": self.study_id,
            "criterion_type": self.criterion_type,
            "domain": self.domain,
            "criterion_name": self.criterion_name,
            "operator": self.operator,
            "value": self.value,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "unit": self.unit,
            "condition_display": self.formatted_condition(),
            "source_page": self.source_page,
            "provenance": self.provenance.to_dict(),
        }


@dataclass
class PrismaOutcome:
    """Extracted efficacy or safety outcome endpoint."""
    outcome_id: str
    study_id: str
    arm_id: str
    arm_name: str = ""
    domain: str = "Efficacy"  # Efficacy, Safety, Biomarker, Baseline
    parameter_name: str = ""
    statistical_type: str = "continuous_mean_sd"
    timepoint_value: Optional[float] = None
    timepoint_unit: str = ""
    sample_size: Optional[int] = None
    mean: Optional[float] = None
    sd: Optional[float] = None
    change_value: Optional[float] = None
    change_sd: Optional[float] = None
    events: Optional[float] = None
    total: Optional[float] = None
    percentage: Optional[float] = None
    unit: str = ""
    effect_measure: str = ""
    effect_value: Optional[float] = None
    p_value: str = ""
    source_page: str = ""
    raw_source_text: str = ""
    provenance: PrismaProvenance = field(default_factory=PrismaProvenance)

    def timepoint_label(self) -> str:
        if self.timepoint_value is not None:
            return f"{self.timepoint_value} {self.timepoint_unit}".strip()
        return "Endpoint"

    def summary_display(self) -> str:
        parts = []
        if self.mean is not None:
            parts.append(f"Mean: {self.mean}")
        if self.sd is not None:
            parts.append(f"± {self.sd}")
        if self.change_value is not None:
            parts.append(f"Δ: {self.change_value}")
        if self.change_sd is not None:
            parts.append(f"(SDΔ: {self.change_sd})")
        if self.events is not None and self.total is not None:
            pct = f" ({self.percentage}%)" if self.percentage is not None else ""
            parts.append(f"{int(self.events)}/{int(self.total)}{pct}")
        if self.unit:
            parts.append(self.unit)
        return " ".join(parts) if parts else "Not reported"

    def to_dict(self) -> dict[str, Any]:
        return {
            "outcome_id": self.outcome_id,
            "study_id": self.study_id,
            "arm_id": self.arm_id,
            "arm_name": self.arm_name,
            "domain": self.domain,
            "parameter_name": self.parameter_name,
            "statistical_type": self.statistical_type,
            "timepoint": self.timepoint_label(),
            "sample_size": self.sample_size,
            "mean": self.mean,
            "sd": self.sd,
            "change_value": self.change_value,
            "change_sd": self.change_sd,
            "events": self.events,
            "total": self.total,
            "percentage": self.percentage,
            "unit": self.unit,
            "summary_display": self.summary_display(),
            "effect_measure": self.effect_measure,
            "effect_value": self.effect_value,
            "p_value": self.p_value,
            "source_page": self.source_page,
            "provenance": self.provenance.to_dict(),
        }


@dataclass
class PrismaValidationFinding:
    """Scientific data completeness or methodological quality warning."""
    issue_id: str
    study_id: str
    target_entity: str = "Study"  # Study, Arm, Outcome, Eligibility
    target_id: str = ""
    field_name: str = ""
    issue_type: str = "missing_data"  # missing_data, scale_mismatch, sample_size_discrepancy, divergence, quality_flag
    severity: str = "warning"  # info, warning, critical
    original_value: str = ""
    reason: str = ""
    recommended_action: str = ""
    provenance: PrismaProvenance = field(default_factory=PrismaProvenance)

    def to_dict(self) -> dict[str, Any]:
        return {
            "issue_id": self.issue_id,
            "study_id": self.study_id,
            "target_entity": self.target_entity,
            "target_id": self.target_id,
            "field_name": self.field_name,
            "issue_type": self.issue_type,
            "severity": self.severity,
            "original_value": self.original_value,
            "reason": self.reason,
            "recommended_action": self.recommended_action,
            "provenance": self.provenance.to_dict(),
        }


@dataclass
class PrismaTrial:
    """Full representation of a clinical trial extracted from a research workbook."""
    study_id: str
    title: str = ""
    authors: str = ""
    publication_year: Optional[int] = None
    journal: str = ""
    doi: str = ""
    study_design: str = ""
    study_phase: str = ""
    condition_studied: str = ""
    total_sample_size: Optional[int] = None
    duration_value: Optional[float] = None
    duration_unit: str = ""
    source_file: str = ""
    sheets_present: list[str] = field(default_factory=list)
    arms: list[PrismaArm] = field(default_factory=list)
    outcomes: list[PrismaOutcome] = field(default_factory=list)
    eligibility: list[PrismaEligibility] = field(default_factory=list)
    validation_findings: list[PrismaValidationFinding] = field(default_factory=list)
    provenance: PrismaProvenance = field(default_factory=PrismaProvenance)

    def duration_label(self) -> str:
        if self.duration_value is not None:
            return f"{self.duration_value} {self.duration_unit}".strip()
        return "Unspecified"

    def citation_short(self) -> str:
        author = self.authors.split(",")[0].strip() if self.authors else self.study_id
        year = f" ({self.publication_year})" if self.publication_year else ""
        return f"{author}{year}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "study_id": self.study_id,
            "title": self.title,
            "authors": self.authors,
            "publication_year": self.publication_year,
            "journal": self.journal,
            "doi": self.doi,
            "study_design": self.study_design,
            "study_phase": self.study_phase,
            "condition_studied": self.condition_studied,
            "total_sample_size": self.total_sample_size,
            "duration": self.duration_label(),
            "source_file": self.source_file,
            "sheets_count": len(self.sheets_present),
            "arms_count": len(self.arms),
            "outcomes_count": len(self.outcomes),
            "eligibility_count": len(self.eligibility),
            "findings_count": len(self.validation_findings),
        }


@dataclass
class StatisticalReadinessSpec:
    """Readiness specification for synthesizing a specific outcome across trials."""
    outcome_name: str
    domain: str = "Efficacy"
    reporting_trials_count: int = 0
    total_patients: int = 0
    arms_count: int = 0
    statistical_type: str = "continuous_mean_sd"
    common_unit: str = ""
    all_units: list[str] = field(default_factory=list)
    units_harmonized: bool = True
    feasible_analyses: list[str] = field(default_factory=list)
    missing_inputs: list[str] = field(default_factory=list)
    readiness_score: float = 0.0  # 0 to 100%
    readiness_status: str = "Insufficient Data"
    recommendations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "outcome_name": self.outcome_name,
            "domain": self.domain,
            "reporting_trials": self.reporting_trials_count,
            "total_patients": self.total_patients,
            "arms_count": self.arms_count,
            "common_unit": self.common_unit,
            "units_harmonized": "✅ Harmonized" if self.units_harmonized else "⚠️ Discrepancy",
            "feasible_analyses": ", ".join(self.feasible_analyses) if self.feasible_analyses else "None",
            "missing_inputs": "; ".join(self.missing_inputs) if self.missing_inputs else "None (Complete)",
            "readiness_score": f"{self.readiness_score:.1f}%",
            "readiness_status": self.readiness_status,
            "recommendations": " | ".join(self.recommendations) if self.recommendations else "Ready for REML pooling",
        }


@dataclass
class PrismaComparisonMatrix:
    """Cross-trial comparison matrix containing side-by-side attributes."""
    trials: list[str] = field(default_factory=list)
    categories: list[str] = field(default_factory=list)
    rows: list[dict[str, Any]] = field(default_factory=list)
    divergences: list[dict[str, str]] = field(default_factory=list)
