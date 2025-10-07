"""
Payment and subscription API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from sqlmodel import Session, select
from typing import Optional
from datetime import datetime
import stripe

from app.models.user import User
from app.models.subscription import (
    Subscription,
    SubscriptionStatus,
    SubscriptionPlan,
    SubscriptionResponse,
    APIUsage,
    UsageStats,
)
from app.core.dependencies import get_current_user, get_session
from app.services.stripe_service import StripeService
from app.core.config import settings
from app.utils.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)
stripe_service = StripeService()


@router.post("/create-checkout-session")
async def create_checkout_session(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Create a Stripe Checkout session for subscribing to Pro plan.

    Args:
        current_user: Current authenticated user
        session: Database session

    Returns:
        Checkout session URL and session ID

    Raises:
        HTTPException: If Stripe is not configured or session creation fails
    """
    if not settings.STRIPE_SECRET_KEY or not settings.STRIPE_PRICE_ID_PRO:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Payment processing is not configured"
        )

    # Get or create Stripe customer
    statement = select(Subscription).where(
        Subscription.user_id == current_user.id
    ).order_by(Subscription.created_at.desc())

    user_subscription = session.exec(statement).first()

    stripe_customer_id = None

    if user_subscription and user_subscription.stripe_customer_id.startswith("cus_"):
        # User has existing Stripe customer ID
        stripe_customer_id = user_subscription.stripe_customer_id
    else:
        # Create new Stripe customer
        try:
            stripe_customer = stripe_service.create_customer(
                email=current_user.email,
                name=current_user.full_name,
                metadata={"user_id": str(current_user.id)}
            )
            stripe_customer_id = stripe_customer.id

            # Update subscription with real Stripe customer ID
            if user_subscription:
                user_subscription.stripe_customer_id = stripe_customer_id
                session.add(user_subscription)
                session.commit()

        except stripe.error.StripeError as e:
            logger.error(f"Failed to create Stripe customer: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create payment customer"
            )

    # Create checkout session
    success_url = f"{settings.BACKEND_CORS_ORIGINS[0]}/dashboard?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{settings.BACKEND_CORS_ORIGINS[0]}/pricing?canceled=true"

    try:
        checkout_session = stripe_service.create_checkout_session(
            customer_id=stripe_customer_id,
            price_id=settings.STRIPE_PRICE_ID_PRO,
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                "user_id": str(current_user.id),
                "plan": SubscriptionPlan.PRO.value
            }
        )

        return {
            "checkout_url": checkout_session.url,
            "session_id": checkout_session.id
        }

    except stripe.error.StripeError as e:
        logger.error(f"Failed to create checkout session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create checkout session"
        )


@router.post("/create-portal-session")
async def create_portal_session(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Create a Stripe Customer Portal session for managing subscription.

    Args:
        current_user: Current authenticated user
        session: Database session

    Returns:
        Portal session URL

    Raises:
        HTTPException: If user has no subscription or portal creation fails
    """
    # Get user's subscription
    statement = select(Subscription).where(
        Subscription.user_id == current_user.id
    ).order_by(Subscription.created_at.desc())

    user_subscription = session.exec(statement).first()

    if not user_subscription or not user_subscription.stripe_customer_id.startswith("cus_"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription found"
        )

    # Create portal session
    return_url = f"{settings.BACKEND_CORS_ORIGINS[0]}/dashboard"

    try:
        portal_session = stripe_service.create_portal_session(
            customer_id=user_subscription.stripe_customer_id,
            return_url=return_url
        )

        return {
            "portal_url": portal_session.url
        }

    except stripe.error.StripeError as e:
        logger.error(f"Failed to create portal session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create billing portal session"
        )


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: Optional[str] = Header(None, alias="stripe-signature"),
    session: Session = Depends(get_session)
):
    """
    Handle Stripe webhook events.

    Processes subscription lifecycle events:
    - checkout.session.completed: Subscription created
    - customer.subscription.updated: Subscription updated
    - customer.subscription.deleted: Subscription canceled
    - invoice.payment_failed: Payment failed

    Args:
        request: FastAPI request object
        stripe_signature: Stripe webhook signature header
        session: Database session

    Returns:
        Success response

    Raises:
        HTTPException: If webhook verification fails
    """
    if not stripe_signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing stripe-signature header"
        )

    # Read raw body
    payload = await request.body()

    # Verify webhook signature and construct event
    try:
        event = stripe_service.construct_webhook_event(payload, stripe_signature)
    except stripe.error.SignatureVerificationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook signature"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    # Handle different event types
    event_type = event.type
    event_data = event.data.object

    logger.info(f"Processing webhook event: {event_type}", extra={"event_id": event.id})

    if event_type == "checkout.session.completed":
        # Payment successful, subscription created
        await handle_checkout_completed(event_data, session)

    elif event_type == "customer.subscription.updated":
        # Subscription updated (renewed, changed plan, etc.)
        await handle_subscription_updated(event_data, session)

    elif event_type == "customer.subscription.deleted":
        # Subscription canceled
        await handle_subscription_deleted(event_data, session)

    elif event_type == "invoice.payment_failed":
        # Payment failed
        await handle_payment_failed(event_data, session)

    return {"status": "success"}


async def handle_checkout_completed(checkout_session, db_session: Session):
    """Handle successful checkout session completion."""
    stripe_customer_id = checkout_session.customer
    stripe_subscription_id = checkout_session.subscription

    # Get user from metadata
    user_id = int(checkout_session.metadata.get("user_id"))

    # Get or update subscription
    statement = select(Subscription).where(
        Subscription.user_id == user_id
    ).order_by(Subscription.created_at.desc())

    subscription = db_session.exec(statement).first()

    if subscription:
        # Update existing subscription
        subscription.stripe_customer_id = stripe_customer_id
        subscription.stripe_subscription_id = stripe_subscription_id
        subscription.status = SubscriptionStatus.ACTIVE
        subscription.plan = SubscriptionPlan.PRO
        subscription.updated_at = datetime.utcnow()
    else:
        # Create new subscription (shouldn't happen, but handle it)
        subscription = Subscription(
            user_id=user_id,
            stripe_customer_id=stripe_customer_id,
            stripe_subscription_id=stripe_subscription_id,
            status=SubscriptionStatus.ACTIVE,
            plan=SubscriptionPlan.PRO
        )

    # Get subscription details from Stripe
    if stripe_subscription_id:
        stripe_subscription = stripe_service.get_subscription(stripe_subscription_id)
        subscription.current_period_start = datetime.fromtimestamp(stripe_subscription.current_period_start)
        subscription.current_period_end = datetime.fromtimestamp(stripe_subscription.current_period_end)
        subscription.cancel_at_period_end = stripe_subscription.cancel_at_period_end

    db_session.add(subscription)
    db_session.commit()

    logger.info(f"Subscription activated for user {user_id}", extra={"user_id": user_id})


async def handle_subscription_updated(stripe_subscription, db_session: Session):
    """Handle subscription update event."""
    stripe_subscription_id = stripe_subscription.id

    # Find subscription in database
    statement = select(Subscription).where(
        Subscription.stripe_subscription_id == stripe_subscription_id
    )

    subscription = db_session.exec(statement).first()

    if not subscription:
        logger.warning(f"Subscription not found: {stripe_subscription_id}")
        return

    # Update subscription details
    subscription.status = SubscriptionStatus(stripe_subscription.status)
    subscription.current_period_start = datetime.fromtimestamp(stripe_subscription.current_period_start)
    subscription.current_period_end = datetime.fromtimestamp(stripe_subscription.current_period_end)
    subscription.cancel_at_period_end = stripe_subscription.cancel_at_period_end
    subscription.updated_at = datetime.utcnow()

    db_session.add(subscription)
    db_session.commit()

    logger.info(f"Subscription updated: {stripe_subscription_id}", extra={"status": subscription.status.value})


async def handle_subscription_deleted(stripe_subscription, db_session: Session):
    """Handle subscription deletion event."""
    stripe_subscription_id = stripe_subscription.id

    # Find subscription in database
    statement = select(Subscription).where(
        Subscription.stripe_subscription_id == stripe_subscription_id
    )

    subscription = db_session.exec(statement).first()

    if not subscription:
        logger.warning(f"Subscription not found: {stripe_subscription_id}")
        return

    # Update subscription status
    subscription.status = SubscriptionStatus.CANCELED
    subscription.updated_at = datetime.utcnow()

    db_session.add(subscription)
    db_session.commit()

    logger.info(f"Subscription canceled: {stripe_subscription_id}")


async def handle_payment_failed(invoice, db_session: Session):
    """Handle failed payment event."""
    stripe_customer_id = invoice.customer
    stripe_subscription_id = invoice.subscription

    # Find subscription in database
    statement = select(Subscription).where(
        Subscription.stripe_subscription_id == stripe_subscription_id
    )

    subscription = db_session.exec(statement).first()

    if not subscription:
        logger.warning(f"Subscription not found for failed payment: {stripe_subscription_id}")
        return

    # Update subscription status
    subscription.status = SubscriptionStatus.PAST_DUE
    subscription.updated_at = datetime.utcnow()

    db_session.add(subscription)
    db_session.commit()

    logger.warning(
        f"Payment failed for subscription: {stripe_subscription_id}",
        extra={"user_id": subscription.user_id}
    )


@router.get("/subscription", response_model=SubscriptionResponse)
async def get_subscription(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
) -> SubscriptionResponse:
    """
    Get current user's subscription details.

    Args:
        current_user: Current authenticated user
        session: Database session

    Returns:
        Subscription details

    Raises:
        HTTPException: If no subscription found
    """
    statement = select(Subscription).where(
        Subscription.user_id == current_user.id
    ).order_by(Subscription.created_at.desc())

    subscription = session.exec(statement).first()

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No subscription found"
        )

    return SubscriptionResponse(
        id=subscription.id,
        user_id=subscription.user_id,
        status=subscription.status,
        plan=subscription.plan,
        current_period_start=subscription.current_period_start,
        current_period_end=subscription.current_period_end,
        cancel_at_period_end=subscription.cancel_at_period_end,
        stripe_customer_id=subscription.stripe_customer_id
    )


@router.get("/usage", response_model=UsageStats)
async def get_usage_stats(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
) -> UsageStats:
    """
    Get current user's API usage statistics.

    Args:
        current_user: Current authenticated user
        session: Database session

    Returns:
        Usage statistics (total analyses, monthly analyses, last analysis)
    """
    # Get subscription for billing period
    subscription_statement = select(Subscription).where(
        Subscription.user_id == current_user.id
    ).order_by(Subscription.created_at.desc())

    subscription = session.exec(subscription_statement).first()

    # Count total analyses
    total_statement = select(APIUsage).where(
        APIUsage.user_id == current_user.id,
        APIUsage.endpoint.like("%/analyze%")
    )

    total_analyses = len(session.exec(total_statement).all())

    # Count this month's analyses
    period_start = subscription.current_period_start if subscription and subscription.current_period_start else datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    monthly_statement = select(APIUsage).where(
        APIUsage.user_id == current_user.id,
        APIUsage.endpoint.like("%/analyze%"),
        APIUsage.timestamp >= period_start
    )

    analyses_this_month = len(session.exec(monthly_statement).all())

    # Get last analysis
    last_statement = select(APIUsage).where(
        APIUsage.user_id == current_user.id,
        APIUsage.endpoint.like("%/analyze%")
    ).order_by(APIUsage.timestamp.desc())

    last_usage = session.exec(last_statement).first()

    return UsageStats(
        total_analyses=total_analyses,
        analyses_this_month=analyses_this_month,
        last_analysis=last_usage.timestamp if last_usage else None
    )
