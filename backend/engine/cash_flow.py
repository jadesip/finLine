"""
finLine Cash Flow Engine

Calculates annual free cash flows, CFADS, and tracks cash generation.
Ported from finForge.
"""

import logging
from typing import Any

from .models import DealParameters, DebtTranche, FinFigs

logger = logging.getLogger(__name__)


class CashFlowEngine:
    """Calculates annual cash flows for LBO analysis."""

    def __init__(
        self,
        financial_data: dict[str, FinFigs],
        deal_params: DealParameters,
        debt_tranches: list[DebtTranche]
    ):
        """Initialize cash flow engine.

        Args:
            financial_data: Dictionary of FinFigs objects
            deal_params: Deal parameters including tax rate
            debt_tranches: List of debt tranches
        """
        self.financial_data = financial_data
        self.deal_params = deal_params
        self.debt_tranches = debt_tranches

        self.ebitda = financial_data.get("ebitda")
        self.ebit = financial_data.get("ebit")
        self.d_and_a = financial_data.get("d_and_a")
        self.capex = financial_data.get("capex")
        self.working_capital = financial_data.get("working_capital")

        logger.info(f"CashFlowEngine initialized with {len(debt_tranches)} debt tranches")

    def calculate_annual_cash_flows(
        self,
        start_year: str | None = None,
        end_year: str | None = None
    ) -> dict[str, dict[str, float]]:
        """Calculate cash flows for each year.

        Returns:
            Dictionary with years as keys, containing:
            - ebitda, ebit, d_and_a, cash_taxes, capex, change_wc
            - unlevered_fcf, cash_interest, fcf, cfads
        """
        cash_flows = {}

        # Determine years from deal parameters
        if start_year is None:
            deal_date = self.deal_params.deal_date
            deal_year = int(deal_date.split("-")[0]) if deal_date else 2024
            start_year = str(deal_year + 1)

        if end_year is None:
            exit_date = self.deal_params.exit_date
            end_year = exit_date.split("-")[0] if exit_date else "2029"

        years = [str(year) for year in range(int(start_year), int(end_year) + 1)]
        logger.info(f"Calculating cash flows for years: {years}")

        # Track working capital for change calculation
        prev_wc = 0.0
        if self.working_capital:
            # Get last historical WC (year before first forecast)
            prev_year = str(int(start_year) - 1)
            prev_wc = self.working_capital.get_value(prev_year)

        for year in years:
            year_cf: dict[str, float] = {}

            # EBITDA
            ebitda = self.ebitda.get_value(year) if self.ebitda else 0.0
            year_cf["ebitda"] = ebitda

            # EBIT (use EBITDA - D&A if not available)
            if self.ebit:
                ebit = self.ebit.get_value(year)
            else:
                d_and_a = self.d_and_a.get_value(year) if self.d_and_a else 0.0
                ebit = ebitda - d_and_a
            year_cf["ebit"] = ebit

            # D&A
            d_and_a = self.d_and_a.get_value(year) if self.d_and_a else 0.0
            year_cf["d_and_a"] = d_and_a

            # Cash taxes (on EBIT, before interest deduction)
            tax_rate = self.deal_params.tax_rate
            cash_taxes = max(0, ebit * tax_rate)
            year_cf["cash_taxes"] = -cash_taxes  # Negative = outflow

            # CapEx (should be negative as outflow)
            capex = self.capex.get_value(year) if self.capex else 0.0
            if capex > 0:
                capex = -capex
            year_cf["capex"] = capex

            # Change in working capital
            change_wc = 0.0
            if self.working_capital:
                current_wc = self.working_capital.get_value(year)
                if current_wc != 0 or prev_wc != 0:
                    change_wc = current_wc - prev_wc
                    prev_wc = current_wc
            year_cf["change_wc"] = -change_wc  # Increase in WC = cash outflow

            # Unlevered FCF (before interest)
            unlevered_fcf = ebitda + year_cf["cash_taxes"] + year_cf["capex"] + year_cf["change_wc"]
            year_cf["unlevered_fcf"] = unlevered_fcf

            # Placeholders for interest (calculated by debt schedule)
            year_cf["cash_interest"] = 0.0
            year_cf["fcf"] = unlevered_fcf
            year_cf["cfads"] = unlevered_fcf

            cash_flows[year] = year_cf

            logger.debug(
                f"Year {year}: EBITDA={ebitda:.0f}, Tax={cash_taxes:.0f}, "
                f"CapEx={capex:.0f}, ΔWC={change_wc:.0f}, FCF={unlevered_fcf:.0f}"
            )

        logger.info(f"Calculated cash flows for {len(cash_flows)} years")
        return cash_flows

    def update_with_interest(
        self,
        cash_flows: dict[str, dict[str, float]],
        total_interest_schedule: dict[str, float],
        cash_interest_schedule: dict[str, float]
    ) -> dict[str, dict[str, float]]:
        """Update cash flows with actual interest expense and recalculate taxes.

        Args:
            cash_flows: Cash flow dictionary to update
            total_interest_schedule: Total interest (cash + PIK) by year
            cash_interest_schedule: Cash interest only by year

        Returns:
            Updated cash flows
        """
        tax_rate = self.deal_params.tax_rate

        for year in cash_flows.keys():
            total_interest = total_interest_schedule.get(year, 0)
            cash_interest = cash_interest_schedule.get(year, 0)

            # Recalculate taxes on PBT (EBIT - total interest)
            ebit = cash_flows[year]["ebit"]
            pbt = ebit - total_interest
            cash_taxes = max(0, pbt * tax_rate)
            cash_flows[year]["cash_taxes"] = -cash_taxes

            # Store cash interest
            cash_flows[year]["cash_interest"] = -cash_interest

            # Recalculate unlevered FCF with corrected taxes
            ebitda = cash_flows[year]["ebitda"]
            unlevered_fcf = (
                ebitda +
                cash_flows[year]["cash_taxes"] +
                cash_flows[year]["capex"] +
                cash_flows[year]["change_wc"]
            )
            cash_flows[year]["unlevered_fcf"] = unlevered_fcf

            # Update FCF (includes cash interest)
            cash_flows[year]["fcf"] = unlevered_fcf + cash_flows[year]["cash_interest"]
            cash_flows[year]["cfads"] = cash_flows[year]["fcf"]

            logger.debug(
                f"Year {year}: EBIT={ebit:.0f}, Interest={total_interest:.0f}, "
                f"PBT={pbt:.0f}, Tax={cash_taxes:.0f}, FCF={cash_flows[year]['fcf']:.0f}"
            )

        return cash_flows
