"""
finLine Debt Schedule Tracker

Tracks debt balances, interest expense, and amortization over time.
Handles floating/fixed rate instruments and revolver as unlimited plug.
Ported from finForge.
"""

import logging
from typing import Any

from .models import DebtTranche, ReferenceRateCurve

logger = logging.getLogger(__name__)


class DebtScheduleTracker:
    """Tracks debt balances and payments over time."""

    def __init__(self, debt_tranches: list[DebtTranche], currency: str = "USD"):
        """Initialize with debt tranches.

        Args:
            debt_tranches: List of debt tranches from capital structure
            currency: Currency for reference rates
        """
        self.debt_tranches = debt_tranches
        self.currency = currency
        self.schedules: dict[str, dict[str, Any]] = {}
        self.reference_curve = ReferenceRateCurve(currency=currency)

        # Initialize schedules for each tranche
        for tranche in debt_tranches:
            tranche_type_lower = tranche.tranche_type.lower()
            is_revolver = tranche_type_lower in ["revolver", "revolving credit facility", "rcf"]

            self.schedules[tranche.label] = {
                "type": tranche.tranche_type,
                "starting_balance": tranche.drawn_amount,
                "original_size": tranche.original_size,
                "is_revolver": is_revolver,
                "is_floating": tranche.is_floating_rate,
                "interest_margin": tranche.interest_margin if tranche.is_floating_rate else 0,
                "cash_interest_rate": tranche.interest_rate,
                "pik_interest_rate": tranche.pik_interest_rate,
                "amortization": tranche.amortization_schedule,
                "maturity": tranche.maturity_date,
                "repayment_seniority": tranche.repayment_seniority,
                "balances": {},
                "principal_payments": {},
                "interest_expense": {},
                "pik_interest": {},
                "revolver_draws": {},
            }
            logger.debug(f"Initialized {tranche.label}: balance {tranche.drawn_amount:,.0f}")

    def _calculate_interest_rate(self, tranche: DebtTranche, year: str) -> float:
        """Calculate applicable cash interest rate for a year."""
        if tranche.is_floating_rate:
            ref_rate = self.reference_curve.get_rate_for_year(year)
            return ref_rate + tranche.interest_margin
        return tranche.interest_rate

    def _get_amortization_schedule(self, tranche: DebtTranche) -> list[float]:
        """Parse amortization schedule string into percentages."""
        if not tranche.amortization_schedule:
            return []

        schedule_str = tranche.amortization_schedule.strip()
        if not schedule_str or schedule_str == "0":
            return []

        parts = schedule_str.split("/")
        schedule = []
        for part in parts:
            try:
                pct = float(part) / 100
                schedule.append(pct)
            except ValueError:
                schedule.append(0)

        return schedule

    def calculate_schedules(
        self,
        cash_flows: dict[str, dict[str, float]],
        minimum_cash: float = 0,
        cash_sweep_enabled: bool = True,
        max_iterations: int = 10,
        convergence_threshold: float = 0.01
    ) -> tuple[dict[str, Any], dict[str, float], dict[str, float], dict[str, float]]:
        """Calculate debt schedules for all tranches with waterfall logic.

        Waterfall Logic:
        1. Calculate PIK interest first (adds to balance)
        2. Calculate available cash: Opening + CFADS - Minimum
        3. Pay mandatory amortization by seniority (use RCF if needed)
        4. If excess cash: First repay RCF, then sweep other tranches

        Returns:
            Tuple of (schedules, total_interest_by_year, cash_interest_by_year, cash_balance)
        """
        # Find revolver if exists
        revolver_tranche = None
        revolver_schedule = None
        for tranche in self.debt_tranches:
            if self.schedules[tranche.label]["is_revolver"]:
                revolver_tranche = tranche
                revolver_schedule = self.schedules[tranche.label]
                logger.info(f"Found revolver: {tranche.label}")
                break

        years = sorted(cash_flows.keys())
        total_interest_by_year: dict[str, float] = {}
        cash_interest_by_year: dict[str, float] = {}
        cash_balance: dict[str, float] = {}

        # Initialize balances (year before first forecast)
        for tranche in self.debt_tranches:
            schedule = self.schedules[tranche.label]
            schedule["balances"][str(int(years[0]) - 1)] = schedule["starting_balance"]

        prev_year_cash = minimum_cash

        for year_idx, year in enumerate(years):
            logger.debug(f"Processing Year {year}")

            ebitda = cash_flows[year].get("ebitda", 0)
            ebit = cash_flows[year].get("ebit", 0)
            capex = cash_flows[year].get("capex", 0)
            change_wc = cash_flows[year].get("change_wc", 0)

            # Iterative calculation for revolver convergence
            prev_revolver_balance = 0
            if revolver_tranche:
                prev_year = str(int(year) - 1)
                prev_revolver_balance = revolver_schedule["balances"].get(prev_year, 0)

            for iteration in range(max_iterations):
                # STEP 1: Calculate Interest
                total_cash_interest = 0.0
                total_pik_interest = 0.0

                for tranche in self.debt_tranches:
                    schedule = self.schedules[tranche.label]
                    prev_year = str(int(year) - 1)
                    beginning_balance = schedule["balances"].get(prev_year, schedule["starting_balance"])

                    if beginning_balance > 0:
                        applicable_rate = self._calculate_interest_rate(tranche, year)
                        cash_interest = beginning_balance * applicable_rate
                        pik_interest = beginning_balance * tranche.pik_interest_rate

                        schedule["interest_expense"][year] = cash_interest
                        schedule["pik_interest"][year] = pik_interest

                        total_cash_interest += cash_interest
                        total_pik_interest += pik_interest

                # STEP 2: Apply PIK Interest to Balances
                for tranche in self.debt_tranches:
                    if tranche == revolver_tranche:
                        continue
                    schedule = self.schedules[tranche.label]
                    prev_year = str(int(year) - 1)
                    beginning_balance = schedule["balances"].get(prev_year, schedule["starting_balance"])
                    pik_interest = schedule["pik_interest"].get(year, 0)
                    schedule["balances"][year] = beginning_balance + pik_interest

                # STEP 3: Calculate CFADS and Available Cash
                initial_tax = abs(cash_flows[year].get("cash_taxes", 0))
                tax_rate = (initial_tax / ebit) if ebit > 0 else 0.25
                pbt = ebit - (total_cash_interest + total_pik_interest)
                cash_taxes = max(0, pbt * tax_rate)

                cfads = ebitda - total_cash_interest - cash_taxes + capex + change_wc
                available_for_debt = prev_year_cash + cfads - minimum_cash

                # STEP 4: Calculate Mandatory Amortization
                mandatory_by_tranche: dict[str, float] = {}
                non_rcf_tranches = sorted(
                    [t for t in self.debt_tranches if not self.schedules[t.label]["is_revolver"]],
                    key=lambda x: (x.repayment_seniority, x.label)
                )

                for tranche in non_rcf_tranches:
                    schedule = self.schedules[tranche.label]
                    amort_schedule = self._get_amortization_schedule(tranche)

                    if amort_schedule and year_idx < len(amort_schedule):
                        amort_pct = amort_schedule[year_idx]
                        amort_amount = tranche.original_size * amort_pct
                        current_balance = schedule["balances"].get(year, 0)
                        amort_amount = min(amort_amount, current_balance)
                        mandatory_by_tranche[tranche.label] = amort_amount

                total_mandatory = sum(mandatory_by_tranche.values())

                # STEP 5: Process Mandatory Payments
                remaining_cash = available_for_debt
                rcf_draw_needed = 0.0

                for tranche in self.debt_tranches:
                    schedule = self.schedules[tranche.label]
                    schedule["principal_payments"][year] = {"mandatory": 0.0, "sweep": 0.0, "total": 0.0}

                for tranche in non_rcf_tranches:
                    mandatory_due = mandatory_by_tranche.get(tranche.label, 0)
                    if mandatory_due <= 0:
                        continue

                    schedule = self.schedules[tranche.label]
                    if remaining_cash >= mandatory_due:
                        schedule["principal_payments"][year]["mandatory"] = mandatory_due
                        schedule["balances"][year] -= mandatory_due
                        remaining_cash -= mandatory_due
                    else:
                        cash_portion = max(0, remaining_cash)
                        rcf_portion = mandatory_due - cash_portion
                        schedule["principal_payments"][year]["mandatory"] = mandatory_due
                        schedule["balances"][year] -= mandatory_due
                        rcf_draw_needed += rcf_portion
                        remaining_cash = 0

                # Apply RCF draw if needed
                if revolver_tranche and rcf_draw_needed > 0:
                    prev_year = str(int(year) - 1)
                    prev_balance = revolver_schedule["balances"].get(prev_year, 0)
                    new_balance = prev_balance + rcf_draw_needed
                    revolver_schedule["balances"][year] = new_balance
                    revolver_schedule["revolver_draws"][year] = rcf_draw_needed
                    revolver_schedule["principal_payments"][year] = {"mandatory": 0, "sweep": 0, "total": -rcf_draw_needed}
                    logger.debug(f"RCF draw: {rcf_draw_needed:,.0f}")

                # STEP 6: Cash Sweep
                if cash_sweep_enabled and remaining_cash > 0:
                    # First: Pay down RCF
                    if revolver_tranche and rcf_draw_needed == 0:
                        prev_year = str(int(year) - 1)
                        opening_rcf = revolver_schedule["balances"].get(prev_year, 0)
                        current_rcf = revolver_schedule["balances"].get(year, opening_rcf)

                        if current_rcf > 0:
                            rcf_repayment = min(remaining_cash, current_rcf)
                            revolver_schedule["balances"][year] = current_rcf - rcf_repayment
                            revolver_schedule["principal_payments"][year]["sweep"] = rcf_repayment
                            revolver_schedule["principal_payments"][year]["total"] += rcf_repayment
                            remaining_cash -= rcf_repayment

                    # Then: Sweep other tranches by seniority
                    for tranche in non_rcf_tranches:
                        if remaining_cash <= 0:
                            break
                        schedule = self.schedules[tranche.label]
                        current_balance = schedule["balances"].get(year, 0)
                        if current_balance > 0:
                            sweep_amount = min(remaining_cash, current_balance)
                            schedule["principal_payments"][year]["sweep"] = sweep_amount
                            schedule["principal_payments"][year]["total"] += sweep_amount
                            schedule["balances"][year] -= sweep_amount
                            remaining_cash -= sweep_amount

                # STEP 7: Set RCF Balance if No Activity
                if revolver_tranche and year not in revolver_schedule["balances"]:
                    prev_year = str(int(year) - 1)
                    revolver_schedule["balances"][year] = revolver_schedule["balances"].get(prev_year, 0)
                    revolver_schedule["principal_payments"][year] = {"mandatory": 0, "sweep": 0, "total": 0}

                # STEP 8: Update Principal Payment Totals
                for tranche in self.debt_tranches:
                    schedule = self.schedules[tranche.label]
                    if year in schedule["principal_payments"]:
                        payments = schedule["principal_payments"][year]
                        payments["total"] = payments["mandatory"] + payments["sweep"]

                # STEP 9: Calculate Ending Cash Balance
                total_cash_used = 0.0
                for tranche in self.debt_tranches:
                    schedule = self.schedules[tranche.label]
                    if year in schedule["principal_payments"]:
                        if schedule["is_revolver"]:
                            total_cash_used -= schedule["principal_payments"][year]["total"]
                        else:
                            total_cash_used += schedule["principal_payments"][year]["total"]

                cash_balance[year] = prev_year_cash + cfads - total_cash_used

                # STEP 10: Check Convergence
                if revolver_tranche:
                    current_revolver = revolver_schedule["balances"].get(year, 0)
                    if abs(current_revolver - prev_revolver_balance) < convergence_threshold:
                        break
                    prev_revolver_balance = current_revolver
                else:
                    break

            # Store interest for this year
            total_interest_by_year[year] = total_cash_interest + total_pik_interest
            cash_interest_by_year[year] = total_cash_interest
            prev_year_cash = cash_balance[year]

            logger.debug(f"Year {year}: Cash Interest={total_cash_interest:.0f}, Ending Cash={cash_balance[year]:.0f}")

        # Calculate total paydown for each tranche
        final_year = years[-1]
        for tranche in self.debt_tranches:
            schedule = self.schedules[tranche.label]
            starting = schedule["starting_balance"]
            ending = schedule["balances"].get(final_year, 0)
            schedule["total_paydown"] = starting - ending

        return self.schedules, total_interest_by_year, cash_interest_by_year, cash_balance

    def get_total_debt_balance(self, year: str) -> float:
        """Get total debt balance for a specific year."""
        return sum(s["balances"].get(year, 0) for s in self.schedules.values())

    def get_total_debt_by_year(self) -> dict[str, float]:
        """Get total debt balance for all years."""
        years = set()
        for schedule in self.schedules.values():
            years.update(schedule["balances"].keys())
        return {year: self.get_total_debt_balance(year) for year in years}

    def get_leverage_metrics(
        self,
        ebitda_by_year: dict[str, float],
        cash_balance: dict[str, float]
    ) -> dict[str, dict[str, float]]:
        """Calculate leverage metrics for all years."""
        leverage_metrics = {}

        for year in ebitda_by_year.keys():
            total_debt = self.get_total_debt_balance(year)
            cash = cash_balance.get(year, 0)
            net_debt = total_debt - cash
            ebitda = ebitda_by_year[year]

            if ebitda > 0:
                net_leverage = net_debt / ebitda
                gross_leverage = total_debt / ebitda
            else:
                net_leverage = 0
                gross_leverage = 0

            leverage_metrics[year] = {
                "net_leverage": net_leverage,
                "gross_leverage": gross_leverage,
                "total_debt": total_debt,
                "cash": cash,
                "net_debt": net_debt,
            }

        return leverage_metrics
