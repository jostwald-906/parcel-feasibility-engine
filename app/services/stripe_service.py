"""
Stripe payment processing service.
"""
import stripe
from typing import Optional, Dict, Any
from datetime import datetime

from app.core.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)

# Initialize Stripe with secret key
if settings.STRIPE_SECRET_KEY:
    stripe.api_key = settings.STRIPE_SECRET_KEY


class StripeService:
    """Service for handling Stripe payment operations."""

    @staticmethod
    def create_customer(email: str, name: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> stripe.Customer:
        """
        Create a Stripe customer.

        Args:
            email: Customer email address
            name: Customer name
            metadata: Additional metadata to store

        Returns:
            Stripe Customer object

        Raises:
            stripe.error.StripeError: If customer creation fails
        """
        try:
            customer = stripe.Customer.create(
                email=email,
                name=name or email,
                metadata=metadata or {}
            )

            logger.info(f"Created Stripe customer: {customer.id}", extra={"email": email})

            return customer

        except stripe.error.StripeError as e:
            logger.error(f"Failed to create Stripe customer: {e}", extra={"email": email})
            raise

    @staticmethod
    def create_checkout_session(
        customer_id: str,
        price_id: str,
        success_url: str,
        cancel_url: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> stripe.checkout.Session:
        """
        Create a Stripe Checkout session for subscription.

        Args:
            customer_id: Stripe customer ID
            price_id: Stripe price ID for subscription
            success_url: URL to redirect after successful payment
            cancel_url: URL to redirect after canceled payment
            metadata: Additional metadata to store

        Returns:
            Stripe Checkout Session object

        Raises:
            stripe.error.StripeError: If session creation fails
        """
        try:
            session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=["card"],
                line_items=[
                    {
                        "price": price_id,
                        "quantity": 1,
                    },
                ],
                mode="subscription",
                success_url=success_url,
                cancel_url=cancel_url,
                metadata=metadata or {},
                allow_promotion_codes=True,  # Allow users to apply promo codes
            )

            logger.info(
                f"Created checkout session: {session.id}",
                extra={"customer_id": customer_id, "price_id": price_id}
            )

            return session

        except stripe.error.StripeError as e:
            logger.error(f"Failed to create checkout session: {e}", extra={"customer_id": customer_id})
            raise

    @staticmethod
    def create_portal_session(customer_id: str, return_url: str) -> stripe.billing_portal.Session:
        """
        Create a Stripe Customer Portal session for managing subscription.

        Args:
            customer_id: Stripe customer ID
            return_url: URL to return to after portal session

        Returns:
            Stripe Customer Portal Session object

        Raises:
            stripe.error.StripeError: If portal session creation fails
        """
        try:
            portal_session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=return_url,
            )

            logger.info(
                f"Created portal session: {portal_session.id}",
                extra={"customer_id": customer_id}
            )

            return portal_session

        except stripe.error.StripeError as e:
            logger.error(f"Failed to create portal session: {e}", extra={"customer_id": customer_id})
            raise

    @staticmethod
    def get_subscription(subscription_id: str) -> stripe.Subscription:
        """
        Retrieve a Stripe subscription.

        Args:
            subscription_id: Stripe subscription ID

        Returns:
            Stripe Subscription object

        Raises:
            stripe.error.StripeError: If retrieval fails
        """
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            return subscription

        except stripe.error.StripeError as e:
            logger.error(f"Failed to retrieve subscription: {e}", extra={"subscription_id": subscription_id})
            raise

    @staticmethod
    def cancel_subscription(subscription_id: str, at_period_end: bool = True) -> stripe.Subscription:
        """
        Cancel a Stripe subscription.

        Args:
            subscription_id: Stripe subscription ID
            at_period_end: If True, cancel at end of current period; if False, cancel immediately

        Returns:
            Cancelled Stripe Subscription object

        Raises:
            stripe.error.StripeError: If cancellation fails
        """
        try:
            if at_period_end:
                subscription = stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True
                )
            else:
                subscription = stripe.Subscription.delete(subscription_id)

            logger.info(
                f"Cancelled subscription: {subscription_id}",
                extra={"subscription_id": subscription_id, "at_period_end": at_period_end}
            )

            return subscription

        except stripe.error.StripeError as e:
            logger.error(f"Failed to cancel subscription: {e}", extra={"subscription_id": subscription_id})
            raise

    @staticmethod
    def construct_webhook_event(payload: bytes, sig_header: str) -> stripe.Event:
        """
        Construct and verify a Stripe webhook event.

        Args:
            payload: Raw request body bytes
            sig_header: Stripe signature header value

        Returns:
            Verified Stripe Event object

        Raises:
            stripe.error.SignatureVerificationError: If signature verification fails
        """
        if not settings.STRIPE_WEBHOOK_SECRET:
            raise ValueError("STRIPE_WEBHOOK_SECRET not configured")

        try:
            event = stripe.Webhook.construct_event(
                payload,
                sig_header,
                settings.STRIPE_WEBHOOK_SECRET
            )

            logger.info(f"Received webhook event: {event.type}", extra={"event_id": event.id})

            return event

        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Webhook signature verification failed: {e}")
            raise

    @staticmethod
    def get_customer(customer_id: str) -> stripe.Customer:
        """
        Retrieve a Stripe customer.

        Args:
            customer_id: Stripe customer ID

        Returns:
            Stripe Customer object

        Raises:
            stripe.error.StripeError: If retrieval fails
        """
        try:
            customer = stripe.Customer.retrieve(customer_id)
            return customer

        except stripe.error.StripeError as e:
            logger.error(f"Failed to retrieve customer: {e}", extra={"customer_id": customer_id})
            raise
