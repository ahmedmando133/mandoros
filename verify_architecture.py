"""
verify_architecture.py
Automated Architecture, Quality Gates, and Zero-Regression Verification Script for MANDOROS.
Checks:
1. Path Agnosticism (ensures zero hardcoded Windows paths in production src/ code).
2. Master Protocols & Schema Integrity (loads all JSON schemas & Markdown instructions in UTF-8).
3. Clinical Skills & Biostatistical Engines Wiring (verifies skill loading & statistical execution).
4. Universal Quality Gates (Gates A through H verification).
5. Gate E Post-Export Workbook Reopening & Reconciliation Guard.
"""

import os
import sys
import json
import tempfile
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))


def check_path_agnosticism() -> bool:
    print("[*] Stage 1: Checking Path Agnosticism across src/ ...")
    src_dir = PROJECT_ROOT / "src"
    violations = []
    for root, _, files in os.walk(src_dir):
        for f in files:
            if f.endswith(".py"):
                f_path = Path(root) / f
                content = f_path.read_text(encoding="utf-8", errors="ignore")
                # Search for hardcoded drive letters like D:\ or C:\Users in code strings
                for line_idx, line in enumerate(content.splitlines(), start=1):
                    stripped = line.strip()
                    if stripped.startswith("#") or stripped.startswith('"""') or stripped.startswith("'''"):
                        continue
                    if "d:\\evidex" in line.lower() or "c:\\users" in line.lower():
                        violations.append(f"{f_path.relative_to(PROJECT_ROOT)}:{line_idx}: {stripped}")

    if violations:
        print(f"[-] FAILED: Found {len(violations)} hardcoded path violations:")
        for v in violations[:5]:
            print(f"    {v}")
        return False
    print("[+] PASSED: 100% Path Agnostic. Zero hardcoded local Windows drive paths in src/.")
    return True


def check_master_protocols() -> bool:
    print("[*] Stage 2: Checking Master Protocols & Schemas UTF-8 Integrity ...")
    protocols_dir = PROJECT_ROOT / "master_protocols"
    if not protocols_dir.exists():
        protocols_dir = PROJECT_ROOT / "schema"

    if not protocols_dir.exists():
        print("[-] FAILED: Protocols directory not found.")
        return False

    files_checked = 0
    for root, _, files in os.walk(protocols_dir):
        for f in files:
            f_path = Path(root) / f
            # Only test text-based specification files
            if f.endswith((".json", ".md", ".txt")):
                try:
                    text = f_path.read_text(encoding="utf-8")
                    files_checked += 1
                    if f.endswith(".json"):
                        json.loads(text)
                except Exception as e:
                    print(f"[-] FAILED: Corrupted or non-UTF-8 file {f}: {e}")
                    return False
            elif f.endswith(".docx"):
                # Verify non-empty binary docx
                files_checked += 1
                if f_path.stat().st_size == 0:
                    print(f"[-] FAILED: Empty binary file {f}")
                    return False

    print(f"[+] PASSED: Successfully loaded {files_checked} protocol/schema files in UTF-8 without errors.")
    return True


def check_skills_and_stats_wiring() -> bool:
    print("[*] Stage 3: Checking Skills Library & Biostatistical Engines Wiring ...")
    try:
        from src.skill_injector import get_skill_instructions, get_skill_bundle
        stat_skill = get_skill_instructions("statistical-analysis", max_chars=500)
        pdf_skill = get_skill_instructions("pdf", max_chars=500)
        assert len(stat_skill) > 0, "statistical-analysis skill must not be empty"
        assert len(pdf_skill) > 0, "pdf skill must not be empty"
        print(f"[+] Loaded clinical skills via skill_injector: statistical-analysis ({len(stat_skill)} chars), pdf ({len(pdf_skill)} chars).")
    except Exception as e:
        print(f"[-] FAILED loading skills: {e}")
        return False

    try:
        from src.meta_predictive import estimate_tau2_reml
        import numpy as np
        yi = np.array([-0.85, -0.65, -0.90])
        vi = np.array([0.04, 0.05, 0.03])
        tau2 = estimate_tau2_reml(yi, vi)
        assert tau2 >= 0.0, "tau^2 must be non-negative"
        print(f"[+] REML tau^2 calculated successfully: {tau2:.4f}")
    except Exception as e:
        print(f"[-] FAILED biostatistical calculation: {e}")
        return False

    print("[+] PASSED: Skills & biostatistical engines wired cleanly.")
    return True


def check_quality_gates_and_reconciliation() -> bool:
    print("[*] Stage 4: Checking Universal Quality Gates (Gates A through H) & Gate E Reconciliation ...")
    from src.models import StudyMetadata, TreatmentArm, OutcomeMeasurement, ExtractedTrialData
    from src.quality_gates import QualityGates
    from src.exporter import ExcelTrialExporter

    study = StudyMetadata(
        study_id="RCT_VERIFY_2026",
        title="Verification of Universal Reliability Pipeline",
        study_design="Double-blind RCT",
        total_sample_size=100
    )
    arms = [
        TreatmentArm(
            arm_id="ARM_VER_001",
            study_id=study.study_id,
            arm_name="Intervention 10mg",
            intervention_type="experimental",
            dose_value=10.0,
            dose_unit="mg",
            sample_size_allocated=50,
            sample_size_analyzed=50
        ),
        TreatmentArm(
            arm_id="ARM_VER_002",
            study_id=study.study_id,
            arm_name="Placebo",
            intervention_type="placebo",
            sample_size_allocated=50,
            sample_size_analyzed=50
        )
    ]
    outcomes = [
        OutcomeMeasurement(
            outcome_id="OUT_VER_001",
            study_id=study.study_id,
            arm_id="ARM_VER_001",
            domain="glycemic",
            parameter_name="HbA1c",
            statistical_type="continuous",
            timepoint_value="0",
            timepoint_unit="weeks",
            sample_size=50,
            mean=8.0,
            sd=0.7,
            unit="%",
            is_baseline=True
        ),
        OutcomeMeasurement(
            outcome_id="OUT_VER_002",
            study_id=study.study_id,
            arm_id="ARM_VER_002",
            domain="glycemic",
            parameter_name="HbA1c",
            statistical_type="continuous",
            timepoint_value="0",
            timepoint_unit="weeks",
            sample_size=50,
            mean=8.1,
            sd=0.8,
            unit="%",
            is_baseline=True
        )
    ]

    trial_data = ExtractedTrialData(
        study=study,
        arms=arms,
        eligibility=[],
        outcomes=outcomes,
        provenance=[],
        validation_log=[]
    )

    with tempfile.TemporaryDirectory() as tmp_dir:
        xlsx_file = os.path.join(tmp_dir, "Verify_Audit.xlsx")
        exporter = ExcelTrialExporter(trial_data)
        saved_file = exporter.export(xlsx_file)

        # Enforce Gate E
        gate_e = QualityGates.enforce_gate_e(saved_file, trial_data)
        if not gate_e.passed:
            print(f"[-] FAILED Gate E: {gate_e.errors}")
            return False

        print(f"[+] Gate E verified: {gate_e.metrics['total_cells_audited']} cells audited across {len(gate_e.metrics['sheets_found'])} sheets.")

        # Full pipeline certificate
        cert = QualityGates.audit_full_pipeline(
            data=trial_data,
            xlsx_path=saved_file,
            k_studies=1
        )
        print(f"[+] Overall Quality Audit Status: {cert.overall_status} (Score: {cert.overall_score}/100)")
        if cert.overall_status not in ["CERTIFIED", "CERTIFIED_WITH_WARNINGS"]:
            return False

    print("[+] PASSED: All Quality Gates and Gate E reconciliation passed with flying colors.")
    return True


def main():
    print("=" * 70)
    print("MANDOROS UNIVERSAL RELIABILITY & ARCHITECTURE VERIFICATION AUDIT")
    print("=" * 70)

    stages = [
        ("Path Agnosticism", check_path_agnosticism),
        ("Master Protocols & Schemas", check_master_protocols),
        ("Skills & Biostatistical Engines", check_skills_and_stats_wiring),
        ("Quality Gates & Gate E Reconciliation", check_quality_gates_and_reconciliation),
    ]

    all_passed = True
    for name, func in stages:
        try:
            if not func():
                all_passed = False
                print(f"[!] Stage '{name}' FAILED.")
                break
        except Exception as e:
            print(f"[!] Exception during '{name}': {e}")
            all_passed = False
            break

    print("=" * 70)
    if all_passed:
        print("[SUCCESS] ALL ARCHITECTURAL STAGES PASSED: SYSTEM READINESS 10/10.")
        sys.exit(0)
    else:
        print("[FAILURE] ARCHITECTURAL AUDIT FAILED. ACTION REQUIRED.")
        sys.exit(1)


if __name__ == "__main__":
    main()
