"""
MANDOROS Centralized Requirements Registry.
Separates:
- Category A: Deterministic Rules (schema conformance, value/unit separation, sample size tracking, 
  workbook layouts, cell sanitization, mandatory fields).
- Category B: Scientific Interpretation Rules (single-study safeguards, heterogeneity metrics, 
  effect measure bounds, timepoint temporal separation, missing data categorization).

Adheres to MANDOROS Permanent System-Wide Reliability Engineering Master Directive.
"""

from __future__ import annotations

import re
from enum import Enum
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field

from src.models import (
    StudyMetadata,
    TreatmentArm,
    EligibilityCriterion,
    OutcomeMeasurement,
    ExtractedTrialData,
    ValidationIssue,
)


class MissingDataStatus(str, Enum):
    """
    Standardized 7-State Clinical Missing Data Taxonomy.
    Prevents false assumptions: never conflates an extraction failure with a source non-report.
    """
    REPORTED_EXTRACTED = "REPORTED_EXTRACTED"
    DERIVED_CALCULATED = "DERIVED_CALCULATED"
    NOT_REPORTED_AFTER_SEARCH = "NOT_REPORTED_AFTER_SEARCH"
    AMBIGUOUS_CONTRADICTORY = "AMBIGUOUS_CONTRADICTORY"
    UNREADABLE_INACCESSIBLE = "UNREADABLE_INACCESSIBLE"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    EXTRACTION_FAILED = "EXTRACTION_FAILED"


class RequirementCategory(str, Enum):
    CATEGORY_A_DETERMINISTIC = "CATEGORY_A_DETERMINISTIC"
    CATEGORY_B_SCIENTIFIC = "CATEGORY_B_SCIENTIFIC"


class RequirementRule(BaseModel):
    rule_id: str
    category: RequirementCategory
    name: str
    description: str
    scope: str = "Universal"
    severity: str = "ERROR"  # BLOCKING, ERROR, WARNING, INFORMATION
    remediation: str = ""


# -------------------------------------------------------------------------
# CANONICAL RULE INVENTORY
# -------------------------------------------------------------------------
CANONICAL_REQUIREMENTS: List[RequirementRule] = [
    # CATEGORY A: Deterministic Requirements
    RequirementRule(
        rule_id="REQ_DET_001",
        category=RequirementCategory.CATEGORY_A_DETERMINISTIC,
        name="Study Metadata Non-Null Primitives",
        description="StudyMetadata must have non-empty study_id, title, and study_design.",
        scope="Phase 1",
        severity="BLOCKING",
        remediation="Extract title and design from title/abstract pages; synthesize fallback RCT identifier."
    ),
    RequirementRule(
        rule_id="REQ_DET_002",
        category=RequirementCategory.CATEGORY_A_DETERMINISTIC,
        name="Treatment Arm Enumeration & Sample Size",
        description="At least 1 treatment arm (preferably >=2 for RCT) with non-null allocated/analyzed sample sizes.",
        scope="Phase 1",
        severity="ERROR",
        remediation="Map arm sample sizes from Table 1 header or trial description; propagate total N across arms."
    ),
    RequirementRule(
        rule_id="REQ_DET_003",
        category=RequirementCategory.CATEGORY_A_DETERMINISTIC,
        name="Strict Value and Unit Separation",
        description="Numeric measurements (mean, sd, se, change_value, dose_value) must never contain string units.",
        scope="Phase 1",
        severity="BLOCKING",
        remediation="Strip unit suffixes from numbers and populate dedicated unit field."
    ),
    RequirementRule(
        rule_id="REQ_DET_004",
        category=RequirementCategory.CATEGORY_A_DETERMINISTIC,
        name="Canonical Sheet Structure Enforcement",
        description="Phase 1 must contain 7 standard sheets + Master Excel Sheet; Phase 2 must contain 10 sheets; Phase 3 must contain 7 sheets.",
        scope="Universal",
        severity="BLOCKING",
        remediation="Ensure workbook generator constructs all mandatory worksheets in specified order."
    ),
    RequirementRule(
        rule_id="REQ_DET_005",
        category=RequirementCategory.CATEGORY_A_DETERMINISTIC,
        name="Master Excel Sheet 5-Section Ordering",
        description="Master Excel Sheet must contain sections 1 (Study/Arms), 2 (Eligibility), 3 (Baseline), 4 (Efficacy), 5 (Safety).",
        scope="Phase 1",
        severity="ERROR",
        remediation="Reorder Master Sheet generation sequence to match 5-section benchmark."
    ),
    RequirementRule(
        rule_id="REQ_DET_006",
        category=RequirementCategory.CATEGORY_A_DETERMINISTIC,
        name="Universal Formula Injection & Cell Type Sanitization",
        description="No Excel cell may contain unescaped '=' formulas, literal 'None', 'nan', 'NaN', or raw dictionaries.",
        scope="Universal",
        severity="BLOCKING",
        remediation="Sanitize all workbook cells via sanitize_workbook_cells before saving."
    ),

    # CATEGORY B: Scientific Interpretation Requirements
    RequirementRule(
        rule_id="REQ_SCI_001",
        category=RequirementCategory.CATEGORY_B_SCIENTIFIC,
        name="Single-Study Synthesis Safeguard (k=1 Protection)",
        description="When k=1, pooled meta-analysis is mathematically invalid. Must flag NOT_APPLICABLE_SINGLE_STUDY and suppress pooled effect/I2.",
        scope="Phase 2",
        severity="BLOCKING",
        remediation="Provide structured single-study descriptive profile; block multi-study pooling routines."
    ),
    RequirementRule(
        rule_id="REQ_SCI_002",
        category=RequirementCategory.CATEGORY_B_SCIENTIFIC,
        name="Heterogeneity Quantification & Degrees of Freedom",
        description="When k >= 2, Cochran's Q degrees of freedom must strictly equal k - 1; I2 must lie within [0.0%, 100.0%].",
        scope="Phase 2",
        severity="ERROR",
        remediation="Compute df = k - 1; bound I2 between 0.0 and 1.0; compute tau^2 via DerSimonian-Laird or REML."
    ),
    RequirementRule(
        rule_id="REQ_SCI_003",
        category=RequirementCategory.CATEGORY_B_SCIENTIFIC,
        name="Temporal Separation of Baseline vs Follow-up",
        description="Baseline measurements (timepoint 0) must never include longitudinal change_value or treatment differences.",
        scope="Phase 1",
        severity="ERROR",
        remediation="Assign is_baseline=True only to timepoint 0; allocate longitudinal measurements to follow-up timepoints."
    ),
    RequirementRule(
        rule_id="REQ_SCI_004",
        category=RequirementCategory.CATEGORY_B_SCIENTIFIC,
        name="Biomarker Domain Integrity & Zero-Cross-Contamination",
        description="Biomarkers must map strictly to valid physiological domains (e.g. Glucose to glycemic, ALT/AST to liver).",
        scope="Phase 1",
        severity="ERROR",
        remediation="Sanitize biomarker domain classifications using domain taxonomy."
    ),
    RequirementRule(
        rule_id="REQ_SCI_005",
        category=RequirementCategory.CATEGORY_B_SCIENTIFIC,
        name="Missing Data Scientific Categorization",
        description="Missing data must be explicitly categorized into 7-state taxonomy; extraction failures must never be labeled not reported.",
        scope="Universal",
        severity="WARNING",
        remediation="Run classify_missingness() for unpopulated mandatory fields."
    ),
    RequirementRule(
        rule_id="REQ_SCI_006",
        category=RequirementCategory.CATEGORY_B_SCIENTIFIC,
        name="Phase 3 Predictive Feasibility & Uncertainty Bounds",
        description="Sample size calculation prerequisites (alpha in (0, 0.2), power in (0.5, 0.99)) must be verified with positive sample sizes.",
        scope="Phase 3",
        severity="BLOCKING",
        remediation="Validate statistical inputs before invoking sample size and power calculation models."
    )
]


class RequirementsRegistry:
    """
    Centralized execution registry for MANDOROS Category A & Category B rules.
    """

    def __init__(self):
        self.rules: Dict[str, RequirementRule] = {r.rule_id: r for r in CANONICAL_REQUIREMENTS}

    def get_category_a_rules(self) -> List[RequirementRule]:
        return [r for r in self.rules.values() if r.category == RequirementCategory.CATEGORY_A_DETERMINISTIC]

    def get_category_b_rules(self) -> List[RequirementRule]:
        return [r for r in self.rules.values() if r.category == RequirementCategory.CATEGORY_B_SCIENTIFIC]

    def classify_missingness(
        self,
        field_name: str,
        raw_source_text: Optional[str] = None,
        extracted_value: Any = None,
        field_searched: bool = True,
        extraction_attempted: bool = True,
        study_design: str = "RCT"
    ) -> MissingDataStatus:
        """
        Determines the exact scientific missingness state for any trial variable.
        Zero Tolerance for Conflation: Never classifies extraction failure as not reported.
        """
        if extracted_value is not None and str(extracted_value).strip() not in ["", "None", "nan", "NaN", "null"]:
            return MissingDataStatus.REPORTED_EXTRACTED

        # If not searched or attempted, it's an extraction failure
        if not field_searched or not extraction_attempted:
            return MissingDataStatus.EXTRACTION_FAILED

        raw_low = (raw_source_text or "").lower()

        # Check for unreadable / degraded text
        if any(k in raw_low for k in ["illegible", "degraded", "unreadable", "poor resolution", "cut off"]):
            return MissingDataStatus.UNREADABLE_INACCESSIBLE

        # Check for contradictory or ambiguous text
        if any(k in raw_low for k in ["contradictory", "discrepancy", "conflicting", "inconsistent"]):
            return MissingDataStatus.AMBIGUOUS_CONTRADICTORY

        # Check for not applicable
        if "single" in study_design.lower() and field_name in ["pooled_effect", "i_squared", "heterogeneity_p"]:
            return MissingDataStatus.NOT_APPLICABLE
        if "crossover" not in study_design.lower() and field_name in ["washout_duration", "period_effect"]:
            return MissingDataStatus.NOT_APPLICABLE

        # If searched thoroughly and document text does not report it
        return MissingDataStatus.NOT_REPORTED_AFTER_SEARCH

    def validate_trial_data(self, data: ExtractedTrialData) -> List[ValidationIssue]:
        """
        Executes Category A & Category B validation across an extracted trial model.
        Returns a list of structured ValidationIssue objects.
        """
        issues: List[ValidationIssue] = []
        issue_idx = 1

        def next_id() -> str:
            nonlocal issue_idx
            res = f"REG_VAL_{issue_idx:03d}"
            issue_idx += 1
            return res

        study_id = data.study.study_id if data.study else "UNKNOWN_STUDY"

        # -------------------------------------------------------------
        # CATEGORY A CHECKS
        # -------------------------------------------------------------
        # Rule REQ_DET_001: Study Metadata
        if not data.study or not data.study.study_id or not data.study.title:
            issues.append(ValidationIssue(
                issue_id=next_id(),
                study_id=study_id,
                target_entity="Studies",
                target_id=study_id,
                field_name="title",
                issue_type="missing_mandatory_field",
                severity="ERROR",
                comment="Study title or ID is missing in StudyMetadata",
                rule_id="REQ_DET_001",
                expected_condition="Non-null study_id and title",
                observed_condition=f"study_id='{getattr(data.study, 'study_id', None)}', title='{getattr(data.study, 'title', None)}'",
                recommended_resolution="Extract title from header lines or generate fallback identifier."
            ))

        # Rule REQ_DET_002: Treatment Arms
        if not data.arms or len(data.arms) == 0:
            issues.append(ValidationIssue(
                issue_id=next_id(),
                study_id=study_id,
                target_entity="Arms",
                target_id=study_id,
                field_name="arms",
                issue_type="missing_arms",
                severity="ERROR",
                comment="No treatment arms extracted for trial",
                rule_id="REQ_DET_002",
                expected_condition="At least 1 treatment arm (preferably >= 2 for RCT)",
                observed_condition="0 arms extracted",
                recommended_resolution="Run generic arm extraction from title, abstract, and Table 1."
            ))
        else:
            for arm in data.arms:
                if arm.sample_size_allocated is None and arm.sample_size_analyzed is None:
                    issues.append(ValidationIssue(
                        issue_id=next_id(),
                        study_id=study_id,
                        target_entity="Arms",
                        target_id=arm.arm_id,
                        field_name="sample_size_allocated",
                        issue_type="missing_arm_sample_size",
                        severity="WARNING",
                        comment=f"Arm '{arm.arm_name}' lacks allocated/analyzed sample size",
                        rule_id="REQ_DET_002",
                        expected_condition="Sample size >= 1",
                        observed_condition="None",
                        recommended_resolution="Extract N from Table 1 header or randomize text."
                    ))

        # Rule REQ_DET_003: Strict Value and Unit Separation
        for o in (data.outcomes or []):
            for attr in ["mean", "sd", "se", "change_value", "change_sd", "events", "percentage"]:
                val = getattr(o, attr, None)
                if val is not None and isinstance(val, str) and re.search(r'[A-Za-z%]', val):
                    issues.append(ValidationIssue(
                        issue_id=next_id(),
                        study_id=study_id,
                        target_entity="Outcomes",
                        target_id=o.outcome_id,
                        field_name=attr,
                        issue_type="unit_in_numeric_field",
                        severity="ERROR",
                        comment=f"Outcome '{o.parameter_name}' has string/unit in numeric field '{attr}': {val}",
                        rule_id="REQ_DET_003",
                        expected_condition="Pure float or integer numeric value",
                        observed_condition=str(val),
                        recommended_resolution="Parse numeric portion and move unit to unit field."
                    ))

        # -------------------------------------------------------------
        # CATEGORY B CHECKS
        # -------------------------------------------------------------
        # Rule REQ_SCI_003: Temporal Separation
        for o in (data.outcomes or []):
            if o.is_baseline is True:
                if o.change_value is not None:
                    issues.append(ValidationIssue(
                        issue_id=next_id(),
                        study_id=study_id,
                        target_entity="Outcomes",
                        target_id=o.outcome_id,
                        field_name="change_value",
                        issue_type="baseline_followup_conflation",
                        severity="ERROR",
                        comment=f"Baseline outcome '{o.parameter_name}' contains change_value={o.change_value}",
                        rule_id="REQ_SCI_003",
                        expected_condition="Baseline observations should have change_value=None",
                        observed_condition=f"change_value={o.change_value}",
                        recommended_resolution="Set is_baseline=False or clear change_value for baseline observation."
                    ))

        # Rule REQ_SCI_004: Biomarker Domain Integrity
        for o in (data.outcomes or []):
            p_low = str(o.parameter_name).lower()
            d_low = str(o.domain).lower()
            if any(k in p_low for k in ["glucose", "fpg", "hba1c"]) and d_low == "liver":
                issues.append(ValidationIssue(
                    issue_id=next_id(),
                    study_id=study_id,
                    target_entity="Outcomes",
                    target_id=o.outcome_id,
                    field_name="domain",
                    issue_type="biomarker_domain_mismatch",
                    severity="ERROR",
                    comment=f"Glucose outcome '{o.parameter_name}' mistakenly assigned to liver domain",
                    rule_id="REQ_SCI_004",
                    expected_condition="Domain should be 'glycemic'",
                    observed_condition=o.domain,
                    recommended_resolution="Reassign domain to 'glycemic'."
                ))

        return issues


# Global singleton instance for clean cross-module access
registry = RequirementsRegistry()
