"""
finLine Returns Calculations

IRR and MOIC calculations for LBO analysis.
Ported from finForge.
"""

import logging
from typing import Any

import numpy_financial as npf

from .models import DealParameters, FinFigs

logger = logging.getLogger(__name__)


def calculate_irr(cash_flows: list[float]) -> float | None:
    """Calculate Internal Rate of Return.

    Args:
        cash_flows: List of cash flows, starting with negative (investment)

    Returns:
        IRR as decimal (e.g., 0.25 for 25%), or None if cannot calculate
    """
    if not cash_flows or len(cash_flows) < 2:
        logger.warning("Cannot calculate IRR: insufficient cash flows")
        return None

    try:
        irr = npf.irr(cash_flows)
        if irr is None or irr != irr:  # Check for NaN
            logger.warning("IRR calculation returned invalid result")
            return None
        return float(irr)
    except Exception as e:
        logger.error(f"IRR calculation error: {e}")
        return None


def calculate_moic(equity_invested: float, equity_returned: float) -> float | None:
    """Calculate Multiple on Invested Capital.

    Args:
        equity_invested: Total equity invested (positive number)
        equity_returned: Total equity returned at exit (positive number)

    Returns:
        MOIC as multiple (e.g., 2.5 for 2.5x), or None if invalid
    """
    if equity_invested <= 0:
        logger.warning("Cannot calculate MOIC: equity invested must be positive")
        return None

    moic = equity_returned / equity_invested
    return float(moic)


class ReturnsCalculator:
    """Calculates LBO return metrics."""

    def __init__(self, deal_params: DealParameters, financial_data: dict[str, FinFigs]):
        """Initialize with deal parameters and financial data."""
        self.deal_params = deal_params
        self.financial_data = financial_data

    def calculate_entry_equity(self, sources_uses: dict) -> float:
        """Calculate entry equity investment from Sources & Uses."""
        return sources_uses["sources"].get("equity", 0)

    def calculate_exit_proceeds(
        self,
        exit_ebitda: float,
        exit_cash: float,
        exit_debt: float
    ) -> tuple[float, float, float]:
        """Calculate exit proceeds for equity holders.

        Args:
            exit_ebitda: EBITDA at exit year
            exit_cash: Cash at exit
            exit_debt: Total debt at exit

        Returns:
            Tuple of (exit_proceeds, exit_enterprise_value, exit_fees)
        """
        # Calculate exit enterprise value
        exit_multiple = self.deal_params.exit_multiple
        exit_enterprise_value = exit_ebitda * exit_multiple

        # Calculate exit fees
        exit_fee_rate = self.deal_params.exit_fee_percentage / 100
        exit_fees = exit_enterprise_value * exit_fee_rate

        # Calculate exit proceeds
        exit_proceeds = exit_enterprise_value + exit_cash - exit_debt - exit_fees

        logger.info(
            f"Exit: EV={exit_enterprise_value:,.0f} ({exit_ebitda:,.0f} × {exit_multiple}x), "
            f"Cash={exit_cash:,.0f}, Debt={exit_debt:,.0f}, Fees={exit_fees:,.0f}, "
            f"Proceeds={exit_proceeds:,.0f}"
        )

        return exit_proceeds, exit_enterprise_value, exit_fees

    def calculate_irr_moic(
        self,
        entry_equity: float,
        exit_proceeds: float,
        holding_period: int
    ) -> tuple[float, float]:
        """Calculate IRR and MOIC.

        Args:
            entry_equity: Initial equity investment
            exit_proceeds: Exit proceeds to equity
            holding_period: Years held

        Returns:
            Tuple of (IRR, MOIC)
        """
        # Calculate MOIC
        if entry_equity > 0:
            moic = exit_proceeds / entry_equity
        else:
            logger.warning("Entry equity is zero or negative")
            moic = 0

        # Calculate IRR using simple formula: IRR = (MOIC^(1/years)) - 1
        if moic > 0 and holding_period > 0:
            irr = (moic ** (1 / holding_period)) - 1
        else:
            irr = 0

        logger.info(f"Returns: {moic:.2f}x MOIC over {holding_period} years = {irr:.1%} IRR")

        return irr, moic

    def calculate_returns_waterfall(
        self,
        sources_uses: dict,
        exit_ebitda: float,
        exit_cash: float,
        exit_debt: float
    ) -> dict[str, Any]:
        """Calculate complete returns waterfall.

        Returns:
            Dictionary with entry, exit, returns, and metrics sections
        """
        logger.info("Calculating returns waterfall")

        # Entry
        entry_equity = self.calculate_entry_equity(sources_uses)

        # Exit
        exit_proceeds, exit_ev, exit_fees = self.calculate_exit_proceeds(
            exit_ebitda, exit_cash, exit_debt
        )

        # Holding period
        deal_date = self.deal_params.deal_date
        exit_date = self.deal_params.exit_date

        deal_year = int(deal_date.split("-")[0]) if deal_date else 2024
        exit_year = int(exit_date.split("-")[0]) if exit_date else 2029
        holding_period = exit_year - deal_year

        # Calculate returns
        irr, moic = self.calculate_irr_moic(entry_equity, exit_proceeds, holding_period)

        return {
            "entry": {
                "purchase_price": sources_uses["uses"].get("purchase_price", 0),
                "transaction_fees": sources_uses["uses"].get("transaction_fees", 0),
                "total_uses": sources_uses["uses"].get("total_uses", 0),
                "total_debt": sources_uses["sources"].get("total_debt", 0),
                "entry_equity": entry_equity,
                "entry_multiple": self.deal_params.entry_multiple,
            },
            "exit": {
                "exit_enterprise_value": exit_ev,
                "exit_cash": exit_cash,
                "exit_debt": exit_debt,
                "exit_fees": exit_fees,
                "exit_proceeds": exit_proceeds,
                "exit_multiple": self.deal_params.exit_multiple,
            },
            "returns": {
                "moic": moic,
                "irr": irr,
                "holding_period": holding_period,
                "total_value_creation": exit_proceeds - entry_equity,
            },
            "metrics": {
                "entry_leverage": (
                    sources_uses["sources"].get("total_debt", 0) /
                    sources_uses["uses"].get("purchase_price", 1)
                    if sources_uses["uses"].get("purchase_price", 0) > 0 else 0
                ),
                "equity_percentage": sources_uses["details"].get("equity_percentage", 0),
                "multiple_expansion": self.deal_params.exit_multiple - self.deal_params.entry_multiple,
            }
        }
