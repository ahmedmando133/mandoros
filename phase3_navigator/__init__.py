"""
MANDOROS Phase 3: Research Gap & Thesis Navigator (Global Standards Edition).
Strict deterministic backend engine for clinical gap taxonomy extraction,
real-time global reality checks (PubMed, ClinicalTrials.gov, OpenAlex),
Evidence & Gap Maps, presize sample size calculation, and SPIRIT/PROSPERO protocol synthesis.
"""

from phase3_navigator.schema_ingestor import SchemaIngestor, IngestedTrialData
from phase3_navigator.gap_taxonomy_extractor import (
    GapTaxonomyExtractor,
    ScientificGap,
    GapCategory,
)
from phase3_navigator.global_reality_checker import (
    GlobalRealityChecker,
    RealityCheckVerdict,
    TrafficLightColor,
)
from phase3_navigator.egm_robvis_plotter import EGMRobvisPlotter
from phase3_navigator.sample_size_and_risk import (
    SampleSizeAndRiskEngine,
    SampleSizeSensitivityTable,
    ProtocolRiskReport,
)
from phase3_navigator.thesis_protocol_builder import (
    ThesisProtocolBuilder,
    ThesisBlueprint,
    GRADESummaryOfFindings,
)
from phase3_navigator.excel_html_exporter import Phase3DossierExporter

__all__ = [
    "SchemaIngestor",
    "IngestedTrialData",
    "GapTaxonomyExtractor",
    "ScientificGap",
    "GapCategory",
    "GlobalRealityChecker",
    "RealityCheckVerdict",
    "TrafficLightColor",
    "EGMRobvisPlotter",
    "SampleSizeAndRiskEngine",
    "SampleSizeSensitivityTable",
    "ProtocolRiskReport",
    "ThesisProtocolBuilder",
    "ThesisBlueprint",
    "GRADESummaryOfFindings",
    "Phase3DossierExporter",
]
