"""
finLine LBO Analysis Engine

Provides complete LBO analysis including:
- Sources & Uses calculation
- Cash flow projections
- Debt schedule tracking with waterfall logic
- Returns calculations (IRR, MOIC)
"""

from .lbo import run_lbo_analysis, run_lbo_analysis_all_cases
from .models import DealParameters, DebtTranche, FinFigs, ReferenceRateCurve
from .extractor import ProjectExtractor
from .sources_uses import calculate_sources_uses
from .cash_flow import CashFlowEngine
from .debt import DebtScheduleTracker
from .returns import ReturnsCalculator, calculate_irr, calculate_moic

__all__ = [
    # Main entry points
    "run_lbo_analysis",
    "run_lbo_analysis_all_cases",
    # Models
    "DealParameters",
    "DebtTranche",
    "FinFigs",
    "ReferenceRateCurve",
    # Components
    "ProjectExtractor",
    "CashFlowEngine",
    "DebtScheduleTracker",
    "ReturnsCalculator",
    "calculate_sources_uses",
    "calculate_irr",
    "calculate_moic",
]
