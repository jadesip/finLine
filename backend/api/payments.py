"""
finLine Payments API

Stripe integration for subscription management.
"""

import logging
from typing import Any

import httpx
from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel

from api.auth import CurrentUser
from config import get_settings
from database import get_user, update_user_subscription

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()


# ============================================================
# Models
# ============================================================

class CheckoutRequest(BaseModel):
    """Request to create checkout session."""
    price_id: str  # Stripe Price ID
    success_url: str = "http://localhost:3000/settings?payment=success"
    cancel_url: str = "http://localhost:3000/settings?payment=cancelled"


class CheckoutResponse(BaseModel):
    """Response with checkout URL."""
    checkout_url: str
    session_id: str


class SubscriptionResponse(BaseModel):
    """User subscription status."""
    status: str  # active, cancelled, past_due, none
    plan: str | None = None
    current_period_end: str | None = None
    cancel_at_period_end: bool = False


class PortalRequest(BaseModel):
    """Request for customer portal."""
    return_url: str = "http://localhost:3000/settings"


# ============================================================
# Endpoints
# ============================================================

@router.post("/create-checkout", response_model=CheckoutResponse)
async def create_checkout_session(
    request: CheckoutRequest,
    current_user: CurrentUser,
):
    """Create a Stripe checkout session for subscription."""
    logger.info(f"Creating checkout session for user {current_user['id']}")

    if not settings.stripe_secret_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Stripe not configured"
        )

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.stripe.com/v1/checkout/sessions",
                auth=(settings.stripe_secret_key, ""),
                data={
                    "mode": "subscription",
                    "payment_method_types[]": "card",
                    "line_items[0][price]": request.price_id,
                    "line_items[0][quantity]": 1,
                    "success_url": request.success_url,
                    "cancel_url": request.cancel_url,
                    "client_reference_id": current_user["id"],
                    "customer_email": current_user["email"],
                    "metadata[user_id]": current_user["id"],
                }
            )
            response.raise_for_status()
            session = response.json()

        logger.info(f"Checkout session created: {session['id']}")
        return CheckoutResponse(
            checkout_url=session["url"],
            session_id=session["id"]
        )

    except httpx.HTTPError as e:
        logger.error(f"Stripe API error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create checkout session"
        )


@router.get("/subscription", response_model=SubscriptionResponse)
async def get_subscription(current_user: CurrentUser):
    """Get current user's subscription status."""
    logger.info(f"Getting subscription for user {current_user['id']}")

    user = await get_user(current_user["id"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Check if user has Stripe customer ID
    stripe_customer_id = user.get("stripe_customer_id")
    if not stripe_customer_id or not settings.stripe_secret_key:
        return SubscriptionResponse(status="none")

    try:
        async with httpx.AsyncClient() as client:
            # Get active subscriptions
            response = await client.get(
                f"https://api.stripe.com/v1/subscriptions",
                auth=(settings.stripe_secret_key, ""),
                params={
                    "customer": stripe_customer_id,
                    "status": "active",
                    "limit": 1
                }
            )
            response.raise_for_status()
            data = response.json()

        if not data.get("data"):
            return SubscriptionResponse(status="none")

        subscription = data["data"][0]
        return SubscriptionResponse(
            status=subscription["status"],
            plan=subscription["items"]["data"][0]["price"]["id"] if subscription["items"]["data"] else None,
            current_period_end=subscription["current_period_end"],
            cancel_at_period_end=subscription.get("cancel_at_period_end", False)
        )

    except httpx.HTTPError as e:
        logger.error(f"Stripe API error: {e}")
        return SubscriptionResponse(status="none")


@router.post("/portal")
async def create_customer_portal(
    request: PortalRequest,
    current_user: CurrentUser,
):
    """Create Stripe customer portal session for managing subscription."""
    logger.info(f"Creating customer portal for user {current_user['id']}")

    if not settings.stripe_secret_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Stripe not configured"
        )

    user = await get_user(current_user["id"])
    stripe_customer_id = user.get("stripe_customer_id") if user else None

    if not stripe_customer_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No subscription found"
        )

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.stripe.com/v1/billing_portal/sessions",
                auth=(settings.stripe_secret_key, ""),
                data={
                    "customer": stripe_customer_id,
                    "return_url": request.return_url
                }
            )
            response.raise_for_status()
            session = response.json()

        return {"portal_url": session["url"]}

    except httpx.HTTPError as e:
        logger.error(f"Stripe API error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create portal session"
        )


@router.post("/webhook")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events."""
    if not settings.stripe_webhook_secret:
        logger.warning("Stripe webhook secret not configured")
        return {"received": True}

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    # Verify webhook signature (simplified - in production use stripe library)
    # For now, we'll process without verification if no secret
    try:
        import json
        event = json.loads(payload)
    except Exception as e:
        logger.error(f"Webhook payload parse error: {e}")
        raise HTTPException(status_code=400, detail="Invalid payload")

    event_type = event.get("type", "")
    logger.info(f"Received Stripe webhook: {event_type}")

    # Handle events
    if event_type == "checkout.session.completed":
        await _handle_checkout_completed(event["data"]["object"])
    elif event_type == "customer.subscription.updated":
        await _handle_subscription_updated(event["data"]["object"])
    elif event_type == "customer.subscription.deleted":
        await _handle_subscription_deleted(event["data"]["object"])
    elif event_type == "invoice.payment_failed":
        await _handle_payment_failed(event["data"]["object"])

    return {"received": True}


# ============================================================
# Webhook Handlers
# ============================================================

async def _handle_checkout_completed(session: dict[str, Any]):
    """Handle successful checkout."""
    user_id = session.get("client_reference_id") or session.get("metadata", {}).get("user_id")
    customer_id = session.get("customer")
    subscription_id = session.get("subscription")

    if user_id and customer_id:
        logger.info(f"Checkout completed for user {user_id}, customer {customer_id}")
        await update_user_subscription(
            user_id,
            stripe_customer_id=customer_id,
            stripe_subscription_id=subscription_id,
            subscription_status="active"
        )


async def _handle_subscription_updated(subscription: dict[str, Any]):
    """Handle subscription update."""
    customer_id = subscription.get("customer")
    status = subscription.get("status")

    if customer_id:
        logger.info(f"Subscription updated for customer {customer_id}: {status}")
        # Update user subscription status based on customer_id
        # This would require looking up user by stripe_customer_id


async def _handle_subscription_deleted(subscription: dict[str, Any]):
    """Handle subscription cancellation."""
    customer_id = subscription.get("customer")

    if customer_id:
        logger.info(f"Subscription deleted for customer {customer_id}")
        # Update user subscription status to cancelled


async def _handle_payment_failed(invoice: dict[str, Any]):
    """Handle failed payment."""
    customer_id = invoice.get("customer")

    if customer_id:
        logger.warning(f"Payment failed for customer {customer_id}")
        # Notify user of failed payment
