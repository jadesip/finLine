"""
finLine LBO Analysis Engine

Core LBO analysis orchestrator that combines all phases:
1. Sources & Uses
2. Cash Flow Analysis
3. Debt Schedule & Paydown
4. Returns Calculation

Ported from finForge.
"""

import logging
from typing import Any

from .cash_flow import CashFlowEngine
from .debt import DebtScheduleTracker
from .extractor import ProjectExtractor
from .returns import ReturnsCalculator
from .sources_uses import calculate_sources_uses

logger = logging.getLogger(__name__)


async def run_lbo_analysis(project_data: dict[str, Any], case_id: str = "base_case") -> dict[str, Any]:
    """Run full LBO analysis on a project case.

    This function:
    1. Extracts deal parameters and financials
    2. Calculates Sources & Uses (entry valuation, equity check)
    3. Projects cash flows (EBITDA → CFADS → debt service)
    4. Builds debt schedules (amortization, interest, PIK)
    5. Calculates exit proceeds and returns (IRR, MOIC)

    Args:
        project_data: Full project data dict (from database)
        case_id: Which case to analyze

    Returns:
        Analysis results including IRR, MOIC, schedules, cash flows
    """
    logger.info(f"Running LBO analysis for case: {case_id}")

    try:
        # Extract data from project
        extractor = ProjectExtractor(project_data, case_id)
        extracted = extractor.extract_all()

        financial_data = extracted["financial_data"]
        debt_tranches = extracted["debt_tranches"]
        deal_params = extracted["deal_parameters"]

        # Validate required data
        if not financial_data.get("ebitda"):
            return {
                "success": False,
                "case_id": case_id,
                "error": "No EBITDA data found - cannot run LBO analysis",
            }

        if deal_params.purchase_price <= 0:
            return {
                "success": False,
                "case_id": case_id,
                "error": "No purchase price calculated - check entry multiple and EBITDA",
            }

        # Run the analysis
        result = _run_complete_lbo_analysis(
            financial_data=financial_data,
            debt_tranches=debt_tranches,
            deal_params=deal_params,
            case_id=case_id
        )

        result["success"] = True
        return result

    except Exception as e:
        logger.error(f"LBO analysis failed: {e}", exc_info=True)
        return {
            "success": False,
            "case_id": case_id,
            "error": str(e),
        }


def _run_complete_lbo_analysis(
    financial_data: dict[str, Any],
    debt_tranches: list[Any],
    deal_params: Any,
    case_id: str = "base_case"
) -> dict[str, Any]:
    """Run complete LBO analysis for a single case.

    Internal function that performs the actual analysis.
    """
    logger.info(f"Starting complete LBO analysis for {case_id}")

    # Phase 1: Sources & Uses
    sources_uses = calculate_sources_uses(deal_params, debt_tranches)
    entry_equity = sources_uses["sources"].get("equity", 0)
    logger.info(f"Entry equity: {entry_equity:,.0f}")

    # Phase 2: Cash Flow Analysis
    cf_engine = CashFlowEngine(financial_data, deal_params, debt_tranches)
    annual_cash_flows = cf_engine.calculate_annual_cash_flows()

    # Phase 3: Debt Schedule with waterfall paydown
    currency = getattr(deal_params, "currency", "USD")
    debt_tracker = DebtScheduleTracker(debt_tranches, currency=currency)
    minimum_cash = getattr(deal_params, "minimum_cash", 0.0)

    debt_schedules, total_interest_by_year, cash_interest_by_year, cash_balance = debt_tracker.calculate_schedules(
        annual_cash_flows,
        minimum_cash=minimum_cash,
        cash_sweep_enabled=True,
    )

    # Update cash flows with actual interest
    annual_cash_flows = cf_engine.update_with_interest(
        annual_cash_flows,
        total_interest_by_year,
        cash_interest_by_year
    )

    # Get leverage metrics
    ebitda_by_year = {year: cf["ebitda"] for year, cf in annual_cash_flows.items()}
    leverage_metrics = debt_tracker.get_leverage_metrics(ebitda_by_year, cash_balance)

    # Phase 4: Returns Calculation
    final_year = max(annual_cash_flows.keys())
    final_cash = cash_balance.get(final_year, 0)
    final_debt = debt_tracker.get_total_debt_by_year().get(final_year, 0)

    # Find exit EBITDA - use last year with actual EBITDA data
    exit_ebitda = annual_cash_flows[final_year]["ebitda"]
    if exit_ebitda == 0:
        # Fall back to last year with non-zero EBITDA
        for year in sorted(annual_cash_flows.keys(), reverse=True):
            if annual_cash_flows[year]["ebitda"] > 0:
                exit_ebitda = annual_cash_flows[year]["ebitda"]
                logger.info(f"Using {year} EBITDA ({exit_ebitda:.1f}) for exit calculation")
                break

    # Calculate exit
    exit_multiple = deal_params.exit_multiple
    exit_enterprise_value = exit_ebitda * exit_multiple
    exit_fees = exit_enterprise_value * (deal_params.exit_fee_percentage / 100)
    exit_proceeds = exit_enterprise_value + final_cash - final_debt - exit_fees

    # Calculate returns
    deal_year = int(deal_params.deal_date.split("-")[0]) if deal_params.deal_date else 2024
    exit_year = int(deal_params.exit_date.split("-")[0]) if deal_params.exit_date else int(final_year)
    holding_period = exit_year - deal_year

    moic = exit_proceeds / entry_equity if entry_equity > 0 else 0
    irr = (moic ** (1 / holding_period)) - 1 if moic > 0 and holding_period > 0 else 0

    logger.info(f"Analysis complete: {moic:.2f}x MOIC, {irr:.1%} IRR")

    # Calculate total debt paydown
    total_debt_paydown = sum(s.get("total_paydown", 0) for s in debt_schedules.values())

    # Compile result
    return {
        "case_id": case_id,

        # Sources & Uses
        "sources_uses": sources_uses,

        # Cash Flows & Debt
        "annual_cash_flows": annual_cash_flows,
        "debt_schedules": debt_schedules,
        "cash_balance": cash_balance,
        "leverage_metrics": leverage_metrics,

        # Returns
        "returns": {
            "entry_equity": entry_equity,
            "exit_enterprise_value": exit_enterprise_value,
            "exit_cash": final_cash,
            "exit_debt": final_debt,
            "exit_fees": exit_fees,
            "exit_proceeds": exit_proceeds,
            "moic": moic,
            "irr": irr,
            "holding_period": holding_period,
        },

        # Summary
        "summary": {
            "case_id": case_id,
            "irr": irr,
            "moic": moic,
            "entry_equity": entry_equity,
            "exit_proceeds": exit_proceeds,
            "total_debt_paydown": total_debt_paydown,
            "final_cash": final_cash,
            "final_leverage": leverage_metrics.get(final_year, {}).get("net_leverage", 0),
            "holding_period": holding_period,
            "currency": getattr(deal_params, "currency", "USD"),
        }
    }


async def run_lbo_analysis_all_cases(project_data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Run LBO analysis for all cases in a project.

    Args:
        project_data: Full project data dict

    Returns:
        Dictionary with case names as keys, each containing analysis results
    """
    logger.info("Running LBO analysis for all cases")

    cases = project_data.get("cases", {})
    results = {}

    for case_id in cases.keys():
        logger.info(f"Analyzing case: {case_id}")
        results[case_id] = await run_lbo_analysis(project_data, case_id)

    return results
