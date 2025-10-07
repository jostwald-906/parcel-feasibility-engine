"""
Dependency injection providers for FastAPI endpoints.

Provides singleton instances of services for efficient resource management.
"""

from functools import lru_cache
from typing import Annotated, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import Session, select
from datetime import datetime

from app.services.ami_calculator import AMICalculator, get_ami_calculator
from app.core.config import Settings, settings as app_settings
from app.core.database import get_session


# Cache service instances for reuse across requests
_fred_client_instance = None
_hud_client_instance = None


async def get_fred_client():
    """
    Provide FRED client singleton.

    Returns:
        FredClient instance for accessing Federal Reserve Economic Data
    """
    from app.clients.fred_client import FREDClient

    global _fred_client_instance
    if _fred_client_instance is None:
        _fred_client_instance = FREDClient()
    return _fred_client_instance


async def get_hud_client():
    """
    Provide HUD FMR client singleton.

    Returns:
        HudFMRClient instance for accessing HUD Fair Market Rent data
    """
    from app.clients.hud_fmr_client import HudFMRClient

    global _hud_client_instance
    if _hud_client_instance is None:
        _hud_client_instance = HudFMRClient()
    return _hud_client_instance


def get_ami_calculator_dep() -> AMICalculator:
    """
    Provide AMI calculator dependency.

    Returns:
        AMICalculator instance for affordable housing calculations
    """
    return get_ami_calculator()


def get_settings() -> Settings:
    """
    Provide application settings.

    Returns:
        Settings instance with environment configuration
    """
    return app_settings


# ============================================
# Authentication Dependencies
# ============================================

# HTTP Bearer token security scheme
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    session: Session = Depends(get_session)
):
    """
    Get the current authenticated user from JWT token.

    Args:
        credentials: HTTP Bearer token credentials
        session: Database session

    Returns:
        User object if authenticated

    Raises:
        HTTPException: If token is invalid or user not found
    """
    from app.core.security import verify_token
    from app.models.user import User

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    # Verify token
    token_payload = verify_token(token, token_type="access")
    if token_payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user from database
    user = session.get(User, token_payload.sub)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account",
        )

    return user


async def get_current_active_user(
    current_user = Depends(get_current_user)
):
    """
    Get the current active user (convenience wrapper).

    Args:
        current_user: Current authenticated user

    Returns:
        User object if active

    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account"
        )
    return current_user


async def require_active_subscription(
    current_user = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Require user to have an active subscription.

    Args:
        current_user: Current authenticated user
        session: Database session

    Returns:
        User object if subscription is active

    Raises:
        HTTPException: If subscription is not active or required
    """
    from app.models.subscription import Subscription, SubscriptionStatus

    # If subscriptions not required (development mode), allow access
    if not app_settings.REQUIRE_SUBSCRIPTION:
        return current_user

    # Get user's subscription
    statement = select(Subscription).where(
        Subscription.user_id == current_user.id
    ).order_by(Subscription.created_at.desc())

    subscription = session.exec(statement).first()

    # No subscription found
    if subscription is None:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Active subscription required. Please subscribe at /pricing",
        )

    # Check subscription status
    if subscription.status != SubscriptionStatus.ACTIVE:
        # Check if subscription is trialing (allow access)
        if subscription.status == SubscriptionStatus.TRIALING:
            return current_user

        # Check if past due but within grace period
        if subscription.status == SubscriptionStatus.PAST_DUE:
            if subscription.current_period_end and subscription.current_period_end > datetime.utcnow():
                return current_user

        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Subscription {subscription.status.value}. Please update payment at /billing",
        )

    # Check if subscription is canceled but still active until period end
    if subscription.cancel_at_period_end:
        if subscription.current_period_end and subscription.current_period_end < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="Subscription expired. Please renew at /pricing",
            )

    return current_user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    session: Session = Depends(get_session)
) -> Optional:
    """
    Get the current user if authenticated, None otherwise.

    Useful for endpoints that have optional authentication.

    Args:
        credentials: HTTP Bearer token credentials
        session: Database session

    Returns:
        User object if authenticated, None otherwise
    """
    from app.core.security import verify_token
    from app.models.user import User

    if credentials is None:
        return None

    try:
        token = credentials.credentials
        token_payload = verify_token(token, token_type="access")
        if token_payload is None:
            return None

        user = session.get(User, token_payload.sub)
        if user is None or not user.is_active:
            return None

        return user

    except Exception:
        return None


async def require_auth_with_usage_limit(
    current_user = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Require authentication and enforce usage limits.

    Free tier users get FREE_TIER_MONTHLY_LIMIT analyses per month.
    Subscribed users get unlimited access.

    Args:
        current_user: Current authenticated user
        session: Database session

    Returns:
        User object if within usage limits or has active subscription

    Raises:
        HTTPException: If usage limit exceeded and no active subscription
    """
    from app.models.subscription import Subscription, SubscriptionStatus, APIUsage
    from sqlmodel import func
    from dateutil.relativedelta import relativedelta

    # Check if user has active subscription
    subscription_statement = select(Subscription).where(
        Subscription.user_id == current_user.id,
        Subscription.status.in_([SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING])
    )
    subscription = session.exec(subscription_statement).first()

    # If user has active subscription, allow unlimited access
    if subscription:
        return current_user

    # Check free tier usage for current month
    now = datetime.utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    usage_statement = select(func.count(APIUsage.id)).where(
        APIUsage.user_id == current_user.id,
        APIUsage.endpoint.like('/api/v1/analyze%'),
        APIUsage.timestamp >= month_start
    )
    usage_count = session.exec(usage_statement).one()

    # Check if user exceeded free tier limit
    if usage_count >= app_settings.FREE_TIER_MONTHLY_LIMIT:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "error": "usage_limit_exceeded",
                "message": f"You've used all {app_settings.FREE_TIER_MONTHLY_LIMIT} free analyses this month. Please subscribe for unlimited access.",
                "usage": {
                    "used": usage_count,
                    "limit": app_settings.FREE_TIER_MONTHLY_LIMIT,
                    "resets_at": (month_start + relativedelta(months=1)).isoformat()
                },
                "upgrade_url": "/pricing"
            }
        )

    # Within free tier limit
    return current_user


async def track_api_usage(
    endpoint: str,
    current_user = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Track API usage for the current user.

    Args:
        endpoint: API endpoint path
        current_user: Current authenticated user
        session: Database session
    """
    from app.models.subscription import APIUsage

    usage = APIUsage(
        user_id=current_user.id,
        endpoint=endpoint,
        created_at=datetime.utcnow()
    )
    session.add(usage)
    session.commit()
