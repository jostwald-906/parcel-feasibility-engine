#!/bin/bash
# Configure Sentry for Railway and Vercel
# Usage: ./scripts/configure_sentry.sh

set -e

echo "🔐 Sentry Configuration Helper"
echo "================================"
echo ""

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Please install it first:"
    echo "   npm i -g @railway/cli"
    exit 1
fi

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "⚠️  Vercel CLI not found. Install it for frontend deployment:"
    echo "   npm i -g vercel"
    echo ""
fi

echo "📝 Please provide your Sentry configuration:"
echo ""

# Get backend DSN
read -p "Backend Sentry DSN (from parcel-feasibility-backend project): " BACKEND_DSN
if [ -z "$BACKEND_DSN" ]; then
    echo "❌ Backend DSN is required"
    exit 1
fi

# Get frontend DSN
read -p "Frontend Sentry DSN (from parcel-feasibility-frontend project): " FRONTEND_DSN
if [ -z "$FRONTEND_DSN" ]; then
    echo "❌ Frontend DSN is required"
    exit 1
fi

# Get org slug
read -p "Sentry Organization Slug: " SENTRY_ORG
if [ -z "$SENTRY_ORG" ]; then
    echo "❌ Organization slug is required"
    exit 1
fi

echo ""
echo "🚂 Configuring Railway Backend..."
echo "================================"

# Set Railway variables
railway variables set SENTRY_DSN="$BACKEND_DSN"
railway variables set SENTRY_ENABLED=true
railway variables set SENTRY_ENVIRONMENT=production
railway variables set SENTRY_TRACES_SAMPLE_RATE=0.1
railway variables set RATE_LIMIT_ENABLED=true
railway variables set RATE_LIMIT_PER_MINUTE=60

echo "✅ Railway variables configured"
echo ""

# Check if Vercel CLI is available
if command -v vercel &> /dev/null; then
    echo "🔷 Configuring Vercel Frontend..."
    echo "================================"

    cd frontend

    # Set Vercel environment variables for production
    vercel env add NEXT_PUBLIC_SENTRY_DSN production <<< "$FRONTEND_DSN"
    vercel env add SENTRY_ORG production <<< "$SENTRY_ORG"
    vercel env add SENTRY_PROJECT production <<< "parcel-feasibility-frontend"
    vercel env add NEXT_PUBLIC_SENTRY_ENVIRONMENT production <<< "production"

    echo "✅ Vercel variables configured"

    cd ..
else
    echo "⚠️  Skipping Vercel configuration (CLI not installed)"
    echo ""
    echo "To configure Vercel manually, add these environment variables:"
    echo "  NEXT_PUBLIC_SENTRY_DSN=$FRONTEND_DSN"
    echo "  SENTRY_ORG=$SENTRY_ORG"
    echo "  SENTRY_PROJECT=parcel-feasibility-frontend"
    echo "  NEXT_PUBLIC_SENTRY_ENVIRONMENT=production"
fi

echo ""
echo "✅ Configuration Complete!"
echo ""
echo "📋 Next Steps:"
echo "1. Trigger Railway redeploy: railway up"
echo "2. Deploy frontend to Vercel: cd frontend && vercel --prod"
echo "3. Test Sentry: Visit Sentry dashboard to see events"
echo ""
echo "🔗 Useful Links:"
echo "  Railway App: https://railway.app/project/9385a16b-6ca2-48eb-9a4e-67c3e49c3068"
echo "  Backend URL: https://parcel-feasibility-engine-production.up.railway.app"
echo "  Sentry Dashboard: https://sentry.io/organizations/$SENTRY_ORG/"
echo ""
