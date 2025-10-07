"""
Subscription models for payment and billing management.
"""
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from datetime import datetime
from enum import Enum


class SubscriptionStatus(str, Enum):
    """Stripe subscription status values."""
    ACTIVE = "active"
    PAST_DUE = "past_due"
    UNPAID = "unpaid"
    CANCELED = "canceled"
    INCOMPLETE = "incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired"
    TRIALING = "trialing"


class SubscriptionPlan(str, Enum):
    """Available subscription plans."""
    FREE = "free"
    PRO = "pro"


class Subscription(SQLModel, table=True):
    """
    Subscription database model.

    Stores Stripe subscription data and links to users.
    Updated via Stripe webhooks.
    """
    __tablename__ = "subscriptions"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True, description="User ID")

    # Stripe identifiers
    stripe_customer_id: str = Field(unique=True, index=True, description="Stripe customer ID")
    stripe_subscription_id: Optional[str] = Field(default=None, unique=True, index=True, description="Stripe subscription ID")

    # Subscription details
    status: SubscriptionStatus = Field(default=SubscriptionStatus.INCOMPLETE, description="Subscription status")
    plan: SubscriptionPlan = Field(default=SubscriptionPlan.FREE, description="Subscription plan")

    # Billing cycle
    current_period_start: Optional[datetime] = Field(default=None, description="Current billing period start")
    current_period_end: Optional[datetime] = Field(default=None, description="Current billing period end")
    cancel_at_period_end: bool = Field(default=False, description="Whether subscription will cancel at period end")

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Subscription creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")

    # Relationships
    user: "User" = Relationship(back_populates="subscriptions")


class SubscriptionResponse(SQLModel):
    """Subscription response model."""
    id: int
    user_id: int
    status: SubscriptionStatus
    plan: SubscriptionPlan
    current_period_start: Optional[datetime]
    current_period_end: Optional[datetime]
    cancel_at_period_end: bool
    stripe_customer_id: str


class APIUsage(SQLModel, table=True):
    """
    API usage tracking model.

    Tracks API calls for analytics and rate limiting.
    """
    __tablename__ = "api_usage"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True, description="User ID")
    endpoint: str = Field(index=True, description="API endpoint called")
    method: str = Field(description="HTTP method (GET, POST, etc.)")
    status_code: int = Field(description="HTTP status code")
    timestamp: datetime = Field(default_factory=datetime.utcnow, index=True, description="Request timestamp")

    # Optional metadata
    parcel_apn: Optional[str] = Field(default=None, description="Parcel APN if applicable")

    # Relationships
    user: "User" = Relationship(back_populates="api_usage")


class UsageStats(SQLModel):
    """User usage statistics response model."""
    total_analyses: int = Field(description="Total analyses run")
    analyses_this_month: int = Field(description="Analyses run this billing period")
    last_analysis: Optional[datetime] = Field(default=None, description="Last analysis timestamp")
