"""
finLine Financial Data Models

Core data structures for LBO analysis.
Ported from finForge with simplifications for finLine.
"""

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class FinFigs:
    """Time-series financial data container.

    Stores financial metrics over time with metadata about currency and units.
    Supports basic arithmetic operations for financial calculations.
    """
    label: str
    data: dict[str, float] = field(default_factory=dict)
    currency: str = "USD"
    unit: str = "millions"

    def get_value(self, year: str) -> float:
        """Get value for a specific year."""
        return self.data.get(year, 0.0)

    def set_value(self, year: str, value: float) -> None:
        """Set value for a specific year."""
        self.data[year] = value

    def get_years(self) -> list[str]:
        """Get sorted list of years with data."""
        return sorted(self.data.keys())

    def __add__(self, other: "FinFigs") -> "FinFigs":
        """Add two FinFigs together."""
        all_years = set(self.data.keys()) | set(other.data.keys())
        result_data = {year: self.get_value(year) + other.get_value(year) for year in all_years}
        return FinFigs(label=f"{self.label} + {other.label}", data=result_data, currency=self.currency, unit=self.unit)

    def __sub__(self, other: "FinFigs") -> "FinFigs":
        """Subtract one FinFigs from another."""
        all_years = set(self.data.keys()) | set(other.data.keys())
        result_data = {year: self.get_value(year) - other.get_value(year) for year in all_years}
        return FinFigs(label=f"{self.label} - {other.label}", data=result_data, currency=self.currency, unit=self.unit)

    def scale(self, factor: float) -> "FinFigs":
        """Scale all values by a factor."""
        return FinFigs(
            label=f"{self.label} * {factor}",
            data={year: value * factor for year, value in self.data.items()},
            currency=self.currency,
            unit=self.unit
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {"label": self.label, "data": self.data, "currency": self.currency, "unit": self.unit}


@dataclass
class DebtTranche:
    """Individual debt tranche with its characteristics."""
    tranche_id: str
    label: str
    tranche_type: str
    original_size: float
    interest_rate: float  # For bonds: coupon. For loans: margin
    interest_margin: float = 0.0
    pik_interest_rate: float = 0.0
    maturity_date: str | None = None
    amortization_schedule: str = ""  # Empty = bullet, "20/20/20/20/20" = schedule
    amortization_rate: float = 0.0  # Annual amortization rate (e.g., 0.10 = 10%)
    financing_fees: float = 0.01
    seniority: int = 1
    repayment_seniority: int = 1
    is_floating_rate: bool = False
    percentage_drawn_at_deal_date: float = 1.0
    drawn_amount: float = 0.0
    financing_fee_amount: float = 0.0

    def __post_init__(self):
        """Calculate derived values after initialization."""
        self.drawn_amount = self.original_size * self.percentage_drawn_at_deal_date
        self.financing_fee_amount = self.original_size * self.financing_fees
        logger.debug(f"DebtTranche: {self.label} - Size: {self.original_size:,.0f}, Drawn: {self.drawn_amount:,.0f}")


@dataclass
class DealParameters:
    """Deal parameters for LBO transaction."""
    purchase_price: float = 0.0
    entry_multiple: float = 0.0
    exit_multiple: float = 0.0
    entry_valuation_method: str = "multiple"
    exit_valuation_method: str = "multiple"
    hardcoded_entry_value: float = 0.0
    hardcoded_exit_value: float = 0.0
    entry_fee_percentage: float = 2.0
    exit_fee_percentage: float = 2.0
    tax_rate: float = 0.25
    minimum_cash: float = 0.0
    deal_date: str = "2024-12-31"
    exit_date: str = "2029-12-31"
    currency: str = "USD"
    transaction_fee_amount: float = 0.0

    def __post_init__(self):
        """Calculate derived values."""
        self.transaction_fee_amount = self.purchase_price * (self.entry_fee_percentage / 100)

    def calculate_entry_value(self, entry_ebitda: float) -> float:
        """Calculate entry firm value based on valuation method."""
        if self.entry_valuation_method == "hardcode" and self.hardcoded_entry_value > 0:
            return self.hardcoded_entry_value
        if self.entry_multiple > 0 and entry_ebitda > 0:
            return entry_ebitda * self.entry_multiple
        return self.purchase_price if self.purchase_price > 0 else 0.0

    def calculate_exit_value(self, exit_ebitda: float) -> float:
        """Calculate exit firm value based on valuation method."""
        if self.exit_valuation_method == "hardcode" and self.hardcoded_exit_value > 0:
            return self.hardcoded_exit_value
        if self.exit_multiple > 0 and exit_ebitda > 0:
            return exit_ebitda * self.exit_multiple
        return 0.0


class ReferenceRateCurve:
    """Reference rate curve for floating rate calculations."""

    def __init__(self, currency: str = "USD", rates_by_year: dict[str, float] | None = None):
        self.currency = currency
        self.rate_type = self._get_rate_type(currency)
        self.rates = rates_by_year or {str(year): 0.02 for year in range(2024, 2036)}

    def _get_rate_type(self, currency: str) -> str:
        """Get the reference rate type for a currency."""
        rate_types = {"USD": "SOFR", "EUR": "ESTR", "GBP": "SONIA", "CHF": "SARON", "JPY": "TONAR"}
        return rate_types.get(currency, "GENERIC")

    def get_rate_for_year(self, year: str) -> float:
        """Get the reference rate for a specific year."""
        return self.rates.get(year, 0.02)
