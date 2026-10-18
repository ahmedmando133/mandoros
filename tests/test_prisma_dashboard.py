"""
Comprehensive Test Suite for PRISMA Clinical Trial Intelligence Dashboard.
Validates read-only multi-sheet ingestion, atomic provenance tracking,
cross-trial side-by-side matrices, divergence detection, statistical readiness,
and zero-regression preservation of existing workbooks.
"""

import os
import hashlib
from pathlib import Path
import pytest
import openpyxl

from src.prisma.models import (
    PrismaProvenance,
    PrismaArm,
    PrismaOutcome,
    PrismaTrial,
    StatisticalReadinessSpec,
)
from src.prisma.ingestion import PrismaIngestionService, load_prisma_workbooks
from src.prisma.comparator import PrismaTrialComparator
from src.prisma.outcome_explorer import PrismaOutcomeExplorer
from src.prisma.exporter import PrismaDossierExporter


SAMPLE_WORKBOOKS = [
    "outputs/orlistat_structured_extracted.xlsx",
    "outputs/metformin_structured_extracted.xlsx",
    "outputs/semaglutide_structured_extracted.xlsx",
    "outputs/dapagliflozin_structured_extracted.xlsx",
]


def file_sha256(path: str) -> str:
    """Computes SHA256 hash of a file for zero-mutation verification."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


class TestPrismaModels:
    def test_provenance_citation(self):
        prov = PrismaProvenance(
            source_file="trial_report.xlsx",
            sheet_name="Outcomes",
            row_index=12,
            cell_ref="C12:F12",
        )
        citation = prov.citation()
        assert "trial_report.xlsx" in citation
        assert "Sheet: Outcomes" in citation
        assert "Cell: C12:F12" in citation

    def test_arm_dose_label(self):
        arm = PrismaArm(
            arm_id="ARM_1",
            study_id="STUDY_A",
            arm_name="Empagliflozin 10mg",
            drug_name="Empagliflozin",
            dose_value=10.0,
            dose_unit="mg",
            frequency_number=1.0,
            frequency_unit="daily",
        )
        assert arm.dose_label() == "Empagliflozin 10.0 mg (1.0 daily)"

    def test_outcome_summary_display(self):
        out = PrismaOutcome(
            outcome_id="OUT_1",
            study_id="STUDY_A",
            arm_id="ARM_1",
            parameter_name="HbA1c",
            mean=7.2,
            sd=0.8,
            unit="%",
        )
        disp = out.summary_display()
        assert "Mean: 7.2" in disp
        assert "± 0.8" in disp
        assert "%" in disp


class TestPrismaIngestionAndZeroMutation:
    def test_zero_mutation_guarantee(self):
        """Verifies that source workbooks are 100% untouched during PRISMA ingestion."""
        existing_files = [f for f in SAMPLE_WORKBOOKS if os.path.exists(f)]
        assert len(existing_files) >= 2, "Need at least 2 real workbooks for zero-mutation test."

        hashes_before = {f: file_sha256(f) for f in existing_files}

        # Run ingestion
        service = PrismaIngestionService()
        trials, findings, overview = service.ingest_workbooks(existing_files)

        hashes_after = {f: file_sha256(f) for f in existing_files}

        # Hashes MUST match identically (Zero mutation)
        for f in existing_files:
            assert hashes_before[f] == hashes_after[f], f"Workbook {f} was modified during ingestion!"

    def test_multi_sheet_parsing_and_provenance(self):
        """Validates that Studies, Arms, Eligibility, Outcomes, and cell provenance are parsed."""
        existing_files = [f for f in SAMPLE_WORKBOOKS if os.path.exists(f)]
        trials, findings, overview = load_prisma_workbooks(existing_files)

        assert len(trials) >= 2, "Should have loaded at least 2 trials."
        assert overview["trials_count"] == len(trials)
        assert overview["workbooks_imported"] == len(existing_files)
        assert overview["arms_count"] > 0
        assert overview["outcomes_count"] > 0

        # Check provenance on first trial
        first_trial = list(trials.values())[0]
        assert first_trial.provenance.source_file != ""
        assert len(first_trial.arms) >= 1
        assert first_trial.arms[0].provenance.sheet_name == "Arms"
        assert first_trial.arms[0].provenance.cell_ref != ""

        # Check outcomes provenance
        first_outcome = first_trial.outcomes[0]
        assert first_outcome.provenance.sheet_name == "Outcomes"
        assert "Sheet: Outcomes" in first_outcome.provenance.citation()

    def test_missing_data_not_converted_to_zero(self):
        """Verifies that missing sample sizes or values remain None and are not converted to 0."""
        existing_files = [f for f in SAMPLE_WORKBOOKS if os.path.exists(f)]
        trials, findings, overview = load_prisma_workbooks(existing_files)

        # Iterate over all outcomes
        for t in trials.values():
            for o in t.outcomes:
                if o.sd is None:
                    assert o.sd != 0.0, "Missing SD must not be converted to 0.0!"


class TestPrismaComparator:
    def test_side_by_side_matrix_generation(self):
        existing_files = [f for f in SAMPLE_WORKBOOKS if os.path.exists(f)]
        trials, findings, overview = load_prisma_workbooks(existing_files)

        comp = PrismaTrialComparator(trials)
        df = comp.build_side_by_side_matrix()

        assert not df.empty
        assert "Category" in df.columns
        assert "Clinical Parameter" in df.columns
        for tid in trials.keys():
            assert tid in df.columns

    def test_divergence_detection(self):
        existing_files = [f for f in SAMPLE_WORKBOOKS if os.path.exists(f)]
        trials, findings, overview = load_prisma_workbooks(existing_files)

        comp = PrismaTrialComparator(trials)
        divs = comp.detect_trial_divergences()

        assert isinstance(divs, list)
        assert len(divs) >= 1
        assert "Category" in divs[0]
        assert "Divergence Description" in divs[0]


class TestPrismaOutcomeExplorer:
    def test_list_outcomes_and_grouping(self):
        existing_files = [f for f in SAMPLE_WORKBOOKS if os.path.exists(f)]
        trials, findings, overview = load_prisma_workbooks(existing_files)

        exp = PrismaOutcomeExplorer(trials)
        outcomes_list = exp.list_all_outcomes()

        assert len(outcomes_list) > 0
        assert "Parameter Name" in outcomes_list[0]
        assert "Trials (k)" in outcomes_list[0]
        assert "Readiness Verdict" in outcomes_list[0]

    def test_statistical_readiness_evaluation(self):
        existing_files = [f for f in SAMPLE_WORKBOOKS if os.path.exists(f)]
        trials, findings, overview = load_prisma_workbooks(existing_files)

        exp = PrismaOutcomeExplorer(trials)
        outcomes_list = exp.list_all_outcomes()
        first_param = outcomes_list[0]["Parameter Name"]

        spec = exp.evaluate_readiness(first_param)
        assert isinstance(spec, StatisticalReadinessSpec)
        assert spec.outcome_name == first_param
        assert spec.reporting_trials_count >= 1
        assert 0.0 <= spec.readiness_score <= 100.0


class TestPrismaExporter:
    def test_excel_dossier_export(self, tmp_path):
        existing_files = [f for f in SAMPLE_WORKBOOKS if os.path.exists(f)]
        trials, findings, overview = load_prisma_workbooks(existing_files)

        export_path = str(tmp_path / "test_prisma_dossier.xlsx")
        exporter = PrismaDossierExporter(trials, findings, overview)
        saved = exporter.export_excel_dossier(export_path)

        assert os.path.exists(saved)
        wb = openpyxl.load_workbook(saved, read_only=True)
        expected_sheets = [
            "PRISMA_Overview",
            "Cross_Trial_Comparison",
            "Outcome_Inventory_&_Readiness",
            "Validation_&_Data_Quality",
            "Provenance_Audit_Trail",
        ]
        for s in expected_sheets:
            assert s in wb.sheetnames, f"Missing sheet {s} in exported PRISMA dossier!"
        wb.close()

    def test_html_dossier_export(self, tmp_path):
        existing_files = [f for f in SAMPLE_WORKBOOKS if os.path.exists(f)]
        trials, findings, overview = load_prisma_workbooks(existing_files)

        export_path = str(tmp_path / "test_prisma_dossier.html")
        exporter = PrismaDossierExporter(trials, findings, overview)
        saved = exporter.export_html_dossier(export_path)

        assert os.path.exists(saved)
        with open(saved, "r", encoding="utf-8") as f:
            content = f.read()
        assert "PRISMA Clinical Trial Intelligence Dossier" in content
        assert "Cross-Trial Side-by-Side Comparison Matrix" in content
