import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.clinical_audit_engine import UnifiedEvidenceSynthesisOrchestrator

mock_study = {
    'study': {
        'study_id': 'RCT_SEMAGLUTIDE_2024',
        'title': 'Once-Weekly Semaglutide in Adults with Overweight or Obesity',
        'condition_studied': 'Obesity and Type 2 Diabetes',
        'total_sample_size': 1961,
        'study_phase': 'Phase 3'
    },
    'arms': [
        {'arm_id': 'ARM_SEMA', 'arm_name': 'Semaglutide 2.4mg', 'intervention_type': 'experimental', 'raw_source_text': 'Semaglutide 2.4 mg once weekly administered subcutaneously'},
        {'arm_id': 'ARM_PBO', 'arm_name': 'Placebo', 'intervention_type': 'placebo', 'raw_source_text': 'Matching placebo once weekly'}
    ],
    'eligibility': [
        {'criterion_id': 'CRIT_01', 'criterion_type': 'inclusion', 'criterion_name': 'age', 'value': 18, 'unit': 'years', 'raw_source_text': 'Adults aged 18 years or older'},
        {'criterion_id': 'CRIT_02', 'criterion_type': 'inclusion', 'criterion_name': 'bmi', 'value': 30, 'unit': 'kg/m2', 'raw_source_text': 'BMI of 30 or greater'}
    ],
    'outcomes': [
        {'parameter_name': 'Body Weight Change', 'ci_lower': -12.5, 'ci_upper': -17.5, 'events': 150, 'sample_size': 1306}
    ]
}

full_text_sample = """
Once-Weekly Semaglutide in Adults with Overweight or Obesity.
A randomized, double-blind, placebo-controlled, multicenter phase 3 trial.
Adults aged 18 years or older with a BMI of 30 or greater were enrolled.
Participants were randomly assigned via an interactive web-response system (IWRS) in a 2:1 ratio.
Semaglutide 2.4 mg once weekly administered subcutaneously or matching placebo once weekly.
Patients, treating clinicians, and outcome assessors were masked to treatment allocation.
With 1961 patients, the study had 90% power to detect a significant difference at alpha 0.05 assuming a 15% dropout rate.
Mean body weight change was significantly greater with semaglutide.
"""

certified_payload, cert = UnifiedEvidenceSynthesisOrchestrator.process_and_certify_study(mock_study, full_text_sample)
print("AUDIT CERTIFICATE GENERATED:")
print(f"Study ID: {cert.study_id}")
print(f"Compliance Score: {cert.compliance_score_100}/100")
print(f"Trial Architecture: {cert.architecture.design_type} ({cert.architecture.phase})")
print(f"Blinding Type: {cert.blinding.blinding_type}")
print(f"Patients Blinded: {cert.blinding.patients_blinded}")
print(f"Clinicians Blinded: {cert.blinding.care_providers_blinded}")
print(f"Assessors Blinded: {cert.blinding.outcome_assessors_blinded}")
print(f"Randomization: {cert.randomization.sequence_generation_method} (Ratio: {cert.randomization.allocation_ratio})")
print(f"Allocation Concealment: {cert.allocation_concealment.mechanism}")
print(f"Cochrane RoB 2.0 Overall: {cert.cochrane_rob2.overall_risk_of_bias}")
print(f"Quotes Audited: {cert.verbatim_verification.total_quotes_audited}, Verified: {cert.verbatim_verification.verified_quotes}")
print(f"Code Inversions Corrected: {cert.code_interpreter.scale_inversions_fixed}")
print(f"Corrected CI: {certified_payload['outcomes'][0]['ci_lower']} to {certified_payload['outcomes'][0]['ci_upper']}")
badge = UnifiedEvidenceSynthesisOrchestrator.generate_html_audit_badge(cert)
print(f"HTML Badge Length: {len(badge)} characters")
print("TEST COMPLETED SUCCESSFULLY!")
