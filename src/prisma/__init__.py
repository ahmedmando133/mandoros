"""
PRISMA: Clinical Trial Intelligence & Visualization Engine.
Independent, zero-regression analytical dashboard for multi-workbook RCT evidence exploration.
"""

from src.prisma.models import (
    PrismaProvenance,
    PrismaArm,
    PrismaEligibility,
    PrismaOutcome,
    PrismaTrial,
    PrismaValidationFinding,
    StatisticalReadinessSpec,
    PrismaComparisonMatrix,
)
from src.prisma.ingestion import PrismaIngestionService, load_prisma_workbooks
from src.prisma.comparator import PrismaTrialComparator
from src.prisma.outcome_explorer import PrismaOutcomeExplorer
from src.prisma.exporter import PrismaDossierExporter
from src.prisma.dashboard_ui import build_prisma_tab

__all__ = [
    "PrismaProvenance",
    "PrismaArm",
    "PrismaEligibility",
    "PrismaOutcome",
    "PrismaTrial",
    "PrismaValidationFinding",
    "StatisticalReadinessSpec",
    "PrismaComparisonMatrix",
    "PrismaIngestionService",
    "load_prisma_workbooks",
    "PrismaTrialComparator",
    "PrismaOutcomeExplorer",
    "PrismaDossierExporter",
    "build_prisma_tab",
]
