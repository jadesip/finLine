"""
finLine Sources and Uses Calculation

Calculates the sources and uses of funds for an LBO transaction.
Ported from finForge.
"""

import logging
from typing import Any

from .models import DealParameters, DebtTranche

logger = logging.getLogger(__name__)


def calculate_sources_uses(
    deal_params: DealParameters,
    debt_tranches: list[DebtTranche],
    equity_amount: float | None = None
) -> dict[str, dict[str, Any]]:
    """Calculate sources and uses table for the transaction.

    Sources (how the deal is funded):
    - Debt tranches (each listed separately)
    - Equity injection (calculated as plug to balance)

    Uses (what the money is spent on):
    - Purchase price (enterprise value)
    - Transaction fees
    - Financing fees (from debt tranches)
    - Minimum cash balance

    Args:
        deal_params: Deal parameters including purchase price and fees
        debt_tranches: List of debt tranches in the capital structure
        equity_amount: Optional pre-specified equity amount (if None, calculated as plug)

    Returns:
        Dictionary with 'sources', 'uses', 'details', and 'validation' sections
    """
    logger.info("Calculating Sources & Uses table")

    sources = {}
    uses = {}

    # === USES SIDE ===

    # Purchase price
    uses["purchase_price"] = deal_params.purchase_price
    logger.debug(f"Purchase Price: {deal_params.purchase_price:,.0f}")

    # Transaction fees
    if deal_params.transaction_fee_amount > 0:
        uses["transaction_fees"] = deal_params.transaction_fee_amount
        logger.debug(f"Transaction Fees: {deal_params.transaction_fee_amount:,.0f}")

    # Financing fees
    total_financing_fees = sum(t.financing_fee_amount for t in debt_tranches)
    if total_financing_fees > 0:
        uses["financing_fees"] = total_financing_fees
        logger.debug(f"Financing Fees: {total_financing_fees:,.0f}")

    # Minimum cash
    if deal_params.minimum_cash > 0:
        uses["minimum_cash"] = deal_params.minimum_cash
        logger.debug(f"Minimum Cash: {deal_params.minimum_cash:,.0f}")

    total_uses = sum(uses.values())
    uses["total_uses"] = total_uses
    logger.info(f"Total Uses: {total_uses:,.0f}")

    # === SOURCES SIDE ===

    # Debt tranches (use drawn_amount)
    total_debt = 0.0
    for tranche in debt_tranches:
        sources[tranche.label] = tranche.drawn_amount
        total_debt += tranche.drawn_amount
        logger.debug(f"{tranche.label}: {tranche.drawn_amount:,.0f}")

    if len(debt_tranches) > 1:
        sources["total_debt"] = total_debt

    # Equity (calculated as plug)
    if equity_amount is None:
        equity_amount = total_uses - total_debt
        logger.info(f"Equity (plug): {total_uses:,.0f} - {total_debt:,.0f} = {equity_amount:,.0f}")

    sources["equity"] = equity_amount
    total_sources = total_debt + equity_amount
    sources["total_sources"] = total_sources
    logger.info(f"Total Sources: {total_sources:,.0f}")

    # === VALIDATION ===
    imbalance = abs(total_sources - total_uses)
    balanced = imbalance <= 0.01
    if not balanced:
        logger.warning(f"Sources & Uses imbalance: {imbalance:,.2f}")
    else:
        logger.info("Sources & Uses balanced")

    # === METRICS ===
    details = {
        "debt_to_equity_ratio": total_debt / equity_amount if equity_amount > 0 else 0,
        "equity_percentage": equity_amount / total_sources if total_sources > 0 else 0,
        "debt_percentage": total_debt / total_sources if total_sources > 0 else 0,
        "total_fees": deal_params.transaction_fee_amount + total_financing_fees,
    }

    logger.info(f"D/E: {details['debt_to_equity_ratio']:.1f}x, Equity: {details['equity_percentage']:.1%}")

    return {
        "sources": sources,
        "uses": uses,
        "details": details,
        "validation": {"balanced": balanced, "imbalance": imbalance}
    }
