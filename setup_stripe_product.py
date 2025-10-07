#!/usr/bin/env python3
"""
Script to create Stripe product and price for the Parcel Feasibility Engine.
Run this once to set up your Stripe account with the $5/month subscription.
"""
import stripe
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set Stripe API key
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

def create_product_and_price():
    """Create Stripe product and $5/month price."""

    print("🔧 Setting up Stripe product and price...\n")

    # Check if product already exists
    products = stripe.Product.list(limit=100)
    existing_product = None

    for product in products.data:
        if product.name == "Parcel Feasibility Engine Pro":
            existing_product = product
            print(f"✅ Found existing product: {product.name}")
            print(f"   Product ID: {product.id}\n")
            break

    # Create product if it doesn't exist
    if not existing_product:
        print("Creating new product...")
        product = stripe.Product.create(
            name="Parcel Feasibility Engine Pro",
            description="Professional California housing development analysis with unlimited parcel analyses, PDF export, and economic feasibility modeling.",
            metadata={
                "app": "parcel-feasibility-engine",
                "plan": "pro"
            }
        )
        print(f"✅ Created product: {product.name}")
        print(f"   Product ID: {product.id}\n")
    else:
        product = existing_product

    # Check if $5/month price exists
    prices = stripe.Price.list(product=product.id, limit=100)
    existing_price = None

    for price in prices.data:
        if (price.unit_amount == 500 and
            price.recurring and
            price.recurring.interval == 'month' and
            price.active):
            existing_price = price
            print(f"✅ Found existing $5/month price")
            print(f"   Price ID: {price.id}\n")
            break

    # Create price if it doesn't exist
    if not existing_price:
        print("Creating $5/month recurring price...")
        price = stripe.Price.create(
            product=product.id,
            unit_amount=500,  # $5.00 in cents
            currency="usd",
            recurring={
                "interval": "month",
                "interval_count": 1
            },
            metadata={
                "plan": "pro"
            }
        )
        print(f"✅ Created price: ${price.unit_amount / 100}/month")
        print(f"   Price ID: {price.id}\n")
    else:
        price = existing_price

    print("=" * 60)
    print("✨ Stripe Setup Complete!")
    print("=" * 60)
    print(f"\n📝 Add this to your .env file:")
    print(f"\nSTRIPE_PRICE_ID_PRO={price.id}")
    print(f"\n🔗 View in Stripe Dashboard:")
    print(f"   Product: https://dashboard.stripe.com/test/products/{product.id}")
    print(f"   Price: https://dashboard.stripe.com/test/prices/{price.id}")
    print("\n" + "=" * 60)

    return product, price

if __name__ == "__main__":
    try:
        product, price = create_product_and_price()
    except stripe.error.AuthenticationError:
        print("❌ Error: Invalid Stripe API key.")
        print("   Make sure STRIPE_SECRET_KEY is set in your .env file")
    except Exception as e:
        print(f"❌ Error: {e}")
