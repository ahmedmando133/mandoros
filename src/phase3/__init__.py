"""
MANDOROS Phase 3: Research Gap & Thesis Navigator Package.
Modular, zero-regression evidence synthesis, reality-check, and protocol planning engine.
"""

from src.phase3.models import (
    EvidenceStudy,
    EvidenceMatrix,
    ObservedResearchGap,
    LiteratureMatch,
    RealityCheckReport,
    MethodologicalAssessment,
    ThesisProposal,
    SampleSizeSpec,
    ProtocolDraft,
    Phase3Dossier
)
from src.phase3.orchestrator import Phase3NavigatorOrchestrator

__all__ = [
    "EvidenceStudy",
    "EvidenceMatrix",
    "ObservedResearchGap",
    "LiteratureMatch",
    "RealityCheckReport",
    "MethodologicalAssessment",
    "ThesisProposal",
    "SampleSizeSpec",
    "ProtocolDraft",
    "Phase3Dossier",
    "Phase3NavigatorOrchestrator"
]
