"""
finLine JSON Extractor

Extracts financial data from project JSON and converts to analysis objects.
Adapted from finForge for the simplified finLine schema.
"""

import logging
from typing import Any

from .models import DealParameters, DebtTranche, FinFigs

logger = logging.getLogger(__name__)


class ProjectExtractor:
    """Extracts financial data from finLine project JSON."""

    def __init__(self, project_data: dict[str, Any], case_id: str = "base_case"):
        """Initialize with project data.

        Args:
            project_data: Complete project data dict (from project.data column)
            case_id: Case to extract (default: base_case)
        """
        self.project_data = project_data
        self.case_id = case_id
        self.meta = project_data.get("meta", {})
        self.currency = self.meta.get("currency", "USD")
        self.unit = self.meta.get("unit", "millions")
        self.cases = project_data.get("cases", {})
        self.case_data = self.cases.get(case_id, {})

        if not self.case_data:
            logger.warning(f"Case '{case_id}' not found in project")

        logger.info(f"ProjectExtractor initialized for case '{case_id}' ({self.currency} {self.unit})")

    def extract_all(self) -> dict[str, Any]:
        """Extract all components needed for LBO analysis.

        Returns:
            Dictionary with financial_data, debt_tranches, deal_parameters
        """
        return {
            "financial_data": self.extract_financial_data(),
            "debt_tranches": self.extract_debt_structure(),
            "deal_parameters": self.extract_deal_parameters(),
        }

    def extract_financial_data(self) -> dict[str, FinFigs]:
        """Extract all financial time series data."""
        result = {}
        financials = self.case_data.get("financials", {})

        # Income statement items
        income_statement = financials.get("income_statement", {})

        # Revenue (standard format: {year: {value_type, value}})
        if "revenue" in income_statement:
            result["revenue"] = self._extract_standard_metric(income_statement["revenue"], "Revenue")

        # EBITDA (array format: [{origin, primary_use, data: {year: {value_type, value}}}])
        if "ebitda" in income_statement:
            result["ebitda"] = self._extract_array_metric(income_statement["ebitda"], "EBITDA")

        # EBIT (array format)
        if "ebit" in income_statement:
            result["ebit"] = self._extract_array_metric(income_statement["ebit"], "EBIT")

        # D&A (array format) - finLine uses d_and_a
        if "d_and_a" in income_statement:
            result["d_and_a"] = self._extract_array_metric(income_statement["d_and_a"], "D&A")
        elif "d&a" in income_statement:
            result["d_and_a"] = self._extract_array_metric(income_statement["d&a"], "D&A")

        # Cash flow statement items
        cash_flow = financials.get("cash_flow_statement", {})

        # CapEx
        if "capex" in cash_flow:
            result["capex"] = self._extract_standard_metric(cash_flow["capex"], "CapEx")

        # Working capital
        if "working_capital" in cash_flow:
            result["working_capital"] = self._extract_standard_metric(cash_flow["working_capital"], "Working Capital")

        logger.info(f"Extracted {len(result)} financial metrics")
        return result

    def _extract_standard_metric(self, data: Any, label: str) -> FinFigs:
        """Extract standard format metric.

        Supports multiple formats:
        1. finLine simple list: [{year, value}, ...]
        2. finLine with values array: {values: [{year, value}, ...]}
        3. Year as key: {year: {value_type, value}} or {year: value}
        """
        finfigs_data = {}

        # Check if it's a simple list: [{year, value}, ...]
        if isinstance(data, list):
            for entry in data:
                if isinstance(entry, dict) and "year" in entry and "value" in entry:
                    year = str(entry["year"])
                    value = entry.get("value", 0.0)
                    if value is not None:
                        finfigs_data[year] = float(value)
            logger.debug(f"Extracted {label} using simple list format: {len(finfigs_data)} periods")
        # Check for finLine format with 'values' array
        elif isinstance(data, dict) and "values" in data and isinstance(data["values"], list):
            for entry in data["values"]:
                if isinstance(entry, dict) and "year" in entry and "value" in entry:
                    year = str(entry["year"])
                    value = entry.get("value", 0.0)
                    if value is not None:
                        finfigs_data[year] = float(value)
            logger.debug(f"Extracted {label} using values array format: {len(finfigs_data)} periods")
        elif isinstance(data, dict):
            # Standard format: year as key
            for year, year_data in data.items():
                if isinstance(year_data, dict):
                    value = year_data.get("value", 0.0)
                    if value is not None:
                        finfigs_data[year] = float(value)
                elif isinstance(year_data, (int, float)):
                    finfigs_data[year] = float(year_data)

        return FinFigs(label=label, data=finfigs_data, currency=self.currency, unit=self.unit)

    def _extract_array_metric(self, data: Any, label: str) -> FinFigs:
        """Extract array format metric (EBITDA/EBIT/D&A).

        Supports multiple formats:
        1. finLine simple: [{year: "2024", value: 100}, ...]
        2. finForge complex: [{primary_use: 1, data: {year: {value_type, value}}}]
        3. Dict format: {year: value} or {year: {value}}
        """
        finfigs_data = {}

        if isinstance(data, list):
            # Check if it's the simple finLine format: [{year, value}, ...]
            if data and isinstance(data[0], dict) and "year" in data[0] and "value" in data[0]:
                for entry in data:
                    year = str(entry.get("year", ""))
                    value = entry.get("value", 0.0)
                    if year and value is not None:
                        finfigs_data[year] = float(value)
                logger.debug(f"Extracted {label} using simple array format: {len(finfigs_data)} periods")
            else:
                # finForge format: find primary entry (primary_use = 1)
                primary_entry = None
                for entry in data:
                    if entry.get("primary_use") == 1:
                        primary_entry = entry
                        break
                # Fallback to first entry
                if not primary_entry and data:
                    primary_entry = data[0]

                if primary_entry and "data" in primary_entry:
                    for year, year_data in primary_entry["data"].items():
                        if isinstance(year_data, dict):
                            value = year_data.get("value", 0.0)
                            if value is not None:
                                finfigs_data[year] = float(value)

        elif isinstance(data, dict):
            # Standard dict format fallback
            for year, year_data in data.items():
                if isinstance(year_data, dict) and "value" in year_data:
                    finfigs_data[year] = float(year_data["value"])
                elif isinstance(year_data, (int, float)):
                    finfigs_data[year] = float(year_data)

        return FinFigs(label=label, data=finfigs_data, currency=self.currency, unit=self.unit)

    def extract_debt_structure(self) -> list[DebtTranche]:
        """Extract debt tranches from capital structure."""
        debt_tranches = []
        deal_params = self.case_data.get("deal_parameters", {})
        capital_structure = deal_params.get("capital_structure", {})
        tranches = capital_structure.get("tranches", [])

        for tranche_data in tranches:
            # Support both 'type' and 'tranche_type' field names
            tranche_type = tranche_data.get("tranche_type") or tranche_data.get("type", "Bond")
            is_floating = tranche_type.lower() in ["loan", "syndicated loan", "revolver", "rcf", "frn", "term_loan"]

            # Default percentage drawn: 0% for revolvers, 100% for others
            if "percentage_drawn_at_deal_date" in tranche_data:
                percentage_drawn = tranche_data["percentage_drawn_at_deal_date"]
            else:
                percentage_drawn = 0.0 if tranche_type.lower() in ["revolver", "rcf"] else 1.0

            # Get interest rate - support multiple field names
            interest_rate = (
                tranche_data.get("interest_rate", 0.0) or
                tranche_data.get("interest_margin", 0.0) or
                tranche_data.get("cash_interest_rate", 0.0)
            )

            # Get amortization - support multiple field names
            amortization = (
                tranche_data.get("amortization_schedule", "") or
                tranche_data.get("amortization", "")
            )

            # Support multiple field names for size
            original_size = (
                tranche_data.get("original_size") or
                tranche_data.get("amount") or
                tranche_data.get("size") or
                0.0
            )

            # Support multiple field names for label
            label = (
                tranche_data.get("label") or
                tranche_data.get("name") or
                "Debt Tranche"
            )

            # Get amortization rate if amortization_schedule not provided
            if not amortization and "amortization_rate" in tranche_data:
                # Convert rate to schedule string (e.g., 0.10 -> "10% annual")
                rate = tranche_data.get("amortization_rate", 0)
                amortization = f"{rate * 100:.0f}% annual" if rate > 0 else ""

            debt_tranche = DebtTranche(
                tranche_id=tranche_data.get("tranche_id", ""),
                label=label,
                tranche_type=tranche_type,
                original_size=original_size,
                interest_rate=interest_rate,
                interest_margin=tranche_data.get("interest_margin", 0.0),
                pik_interest_rate=tranche_data.get("pik_interest_rate", 0.0),
                maturity_date=tranche_data.get("maturity"),
                amortization_schedule=amortization,
                amortization_rate=tranche_data.get("amortization_rate", 0.0),
                financing_fees=tranche_data.get("financing_fees", 0.01),
                seniority=tranche_data.get("seniority", 1),
                repayment_seniority=tranche_data.get("repayment_seniority", 1),
                is_floating_rate=is_floating,
                percentage_drawn_at_deal_date=percentage_drawn,
            )
            debt_tranches.append(debt_tranche)
            logger.debug(f"Extracted {tranche_type}: {debt_tranche.label} - {debt_tranche.original_size:,.0f} @ {interest_rate:.1%}")

        logger.info(f"Extracted {len(debt_tranches)} debt tranches")
        return debt_tranches

    def extract_deal_parameters(self) -> DealParameters:
        """Extract deal parameters."""
        deal_params_data = self.case_data.get("deal_parameters", {})

        # Entry valuation
        entry_valuation = deal_params_data.get("entry_valuation", {})
        entry_method = entry_valuation.get("method", "multiple")
        entry_multiple = entry_valuation.get("multiple", 0.0)

        # Exit valuation
        exit_valuation = deal_params_data.get("exit_valuation", {})
        exit_method = exit_valuation.get("method", "multiple")
        exit_multiple = exit_valuation.get("multiple", 0.0)

        # Calculate purchase price from EBITDA * multiple if not set
        purchase_price = 0.0
        if entry_multiple > 0:
            financial_data = self.extract_financial_data()
            ebitda = financial_data.get("ebitda")
            if ebitda:
                # Get deal year EBITDA
                deal_date = deal_params_data.get("deal_date", "2024-12-31")
                deal_year = deal_date.split("-")[0] if deal_date else "2024"
                ebitda_value = ebitda.get_value(deal_year)
                if ebitda_value > 0:
                    purchase_price = ebitda_value * entry_multiple
                    logger.info(f"Purchase price: {ebitda_value:,.0f} × {entry_multiple}x = {purchase_price:,.0f}")

        return DealParameters(
            purchase_price=purchase_price,
            entry_multiple=entry_multiple,
            exit_multiple=exit_multiple,
            entry_valuation_method=entry_method,
            exit_valuation_method=exit_method,
            entry_fee_percentage=deal_params_data.get("entry_fee_percentage", 2.0),
            exit_fee_percentage=deal_params_data.get("exit_fee_percentage", 2.0),
            tax_rate=deal_params_data.get("tax_rate", 0.25),
            minimum_cash=deal_params_data.get("minimum_cash", 0.0),
            deal_date=deal_params_data.get("deal_date", "2024-12-31"),
            exit_date=deal_params_data.get("exit_date", "2029-12-31"),
            currency=self.currency,
        )

    def get_forecast_years(self) -> list[str]:
        """Get list of forecast years based on deal and exit dates."""
        deal_params = self.case_data.get("deal_parameters", {})
        deal_date = deal_params.get("deal_date", "2024-12-31")
        exit_date = deal_params.get("exit_date", "2029-12-31")

        deal_year = int(deal_date.split("-")[0]) if deal_date else 2024
        exit_year = int(exit_date.split("-")[0]) if exit_date else 2029

        return [str(year) for year in range(deal_year + 1, exit_year + 1)]
