# Authentication & Payment System - Setup Guide

## 🎉 Implementation Complete!

Your Parcel Feasibility Engine now has a complete authentication and payment system with:
- ✅ User registration and login
- ✅ JWT token-based authentication
- ✅ Stripe subscription integration ($5/month)
- ✅ Protected routes
- ✅ User dashboard
- ✅ Usage tracking

## 🚀 Quick Start

### 1. Backend Setup

```bash
# From project root: /Users/Jordan_Ostwald/Parcel Feasibility Engine/

# Activate virtual environment
source venv/bin/activate

# Dependencies are already installed!
# Database tables are already created!

# Create .env file
cp .env.example .env
# Edit .env and add your JWT secret and Stripe keys

# Run backend server
./venv/bin/uvicorn app.main:app --reload
```

Backend will run at: **http://localhost:8000**

### 2. Frontend Setup

```bash
# Navigate to frontend
cd frontend

# Dependencies are already installed!

# Create .env.local file
cp .env.local.example .env.local
# Edit .env.local (default values should work for local development)

# Run frontend
npm run dev
```

Frontend will run at: **http://localhost:3000**

## 🔐 Testing Authentication Locally

### Test User Registration

1. Go to http://localhost:3000
2. Click "Sign Up" or visit http://localhost:3000/auth/register
3. Fill in the form:
   - Email: test@example.com
   - Password: Test1234 (must have uppercase, lowercase, numbers)
   - Full Name: Test User
4. Click "Create Account"
5. You'll be automatically logged in and redirected to dashboard

### Test User Login

1. Visit http://localhost:3000/auth/login
2. Enter credentials
3. Click "Sign In"
4. You'll be redirected to dashboard

### Test Protected Routes

1. Try to visit http://localhost:3000/dashboard without logging in
2. You'll be redirected to the login page
3. After logging in, you can access the dashboard

## 💳 Setting Up Stripe (Required for Production)

### 1. Create/Login to Stripe Account

Visit https://stripe.com and create an account or log in.

### 2. Get API Keys

**Development (Test Mode):**
1. Go to Developers > API keys
2. Copy "Publishable key" (starts with `pk_test_`)
3. Copy "Secret key" (starts with `sk_test_`)

**Production:**
1. Toggle to "Live mode" in Stripe dashboard
2. Get live keys (`pk_live_...` and `sk_live_...`)

### 3. Create Product and Price

1. Go to Products
2. Click "+ Add product"
3. Name: "Parcel Feasibility Engine Pro"
4. Price: $5/month (recurring)
5. Click "Save product"
6. Copy the **Price ID** (starts with `price_...`)

### 4. Configure Webhook

1. Go to Developers > Webhooks
2. Click "+ Add endpoint"
3. Endpoint URL:
   - **Local testing**: Use Stripe CLI (see below)
   - **Production**: `https://your-api.railway.app/api/v1/payments/webhook`
4. Select events to listen for:
   - `checkout.session.completed`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_failed`
5. Click "Add endpoint"
6. Copy the **Signing secret** (starts with `whsec_...`)

### 5. Update Environment Variables

**Backend (.env):**
```env
STRIPE_SECRET_KEY=sk_test_your_key_here
STRIPE_PUBLISHABLE_KEY=pk_test_your_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_secret_here
STRIPE_PRICE_ID_PRO=price_your_price_id_here
```

**Frontend (.env.local):**
```env
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_your_key_here
```

### 6. Test Webhooks Locally (Optional)

Install Stripe CLI:
```bash
brew install stripe/stripe-cli/stripe

# Login to Stripe
stripe login

# Forward webhooks to local backend
stripe listen --forward-to localhost:8000/api/v1/payments/webhook

# This will give you a webhook signing secret (whsec_...)
# Add this to your .env file
```

In another terminal, trigger a test event:
```bash
stripe trigger checkout.session.completed
```

## 📝 Environment Variables Reference

### Required for Authentication
```env
JWT_SECRET_KEY=<generate-random-32+-character-string>
```

Generate a secure secret:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Required for Payments
```env
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_ID_PRO=price_...
```

### Optional Settings
```env
REQUIRE_SUBSCRIPTION=false  # Set to true to enforce subscriptions
FREE_TIER_MONTHLY_LIMIT=3   # Free analyses per month
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
```

## 🧪 Testing the Payment Flow

### Using Test Cards

Stripe provides test card numbers:

**Successful Payment:**
- Card: `4242 4242 4242 4242`
- Expiry: Any future date
- CVC: Any 3 digits
- ZIP: Any 5 digits

**Payment Fails:**
- Card: `4000 0000 0000 0002`

**Requires Authentication (3D Secure):**
- Card: `4000 0027 6000 3184`

### Test Flow

1. Log in to your account
2. Visit http://localhost:3000/pricing
3. Click "Subscribe Now"
4. You'll be redirected to Stripe Checkout
5. Use test card: 4242 4242 4242 4242
6. Complete checkout
7. You'll be redirected back with `?session_id=...`
8. Check your dashboard - subscription should be active!

## 📊 Available API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login with email/password
- `POST /api/v1/auth/refresh` - Refresh access token
- `POST /api/v1/auth/logout` - Logout
- `GET /api/v1/auth/me` - Get current user profile
- `PATCH /api/v1/auth/me` - Update user profile

### Payments
- `POST /api/v1/payments/create-checkout-session` - Start subscription
- `POST /api/v1/payments/create-portal-session` - Manage billing
- `POST /api/v1/payments/webhook` - Stripe webhook handler
- `GET /api/v1/payments/subscription` - Get subscription details
- `GET /api/v1/payments/usage` - Get usage statistics

### Protected Analysis Endpoints
All existing analysis endpoints now support optional authentication.
Set `REQUIRE_SUBSCRIPTION=true` to enforce authentication.

## 🌐 Deployment

### Backend (Railway)

1. **Push code to GitHub**
   ```bash
   git add .
   git commit -m "Add authentication and payment system"
   git push origin main
   ```

2. **Set environment variables in Railway:**
   - All variables from `.env.example`
   - **IMPORTANT**: Use a strong JWT_SECRET_KEY in production!
   - Use production Stripe keys (sk_live_..., pk_live_...)

3. **Set DATABASE_URL to PostgreSQL:**
   ```
   DATABASE_URL=postgresql://user:pass@host:5432/dbname
   ```

4. **Create database tables:**
   Railway console > Run:
   ```python
   from app.core.database import create_db_and_tables
   create_db_and_tables()
   ```

### Frontend (Vercel)

1. **Set environment variables in Vercel:**
   ```
   NEXT_PUBLIC_API_URL=https://your-api.railway.app
   NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_live_...
   ```

2. **Deploy:**
   ```bash
   cd frontend
   vercel --prod
   ```

## 🔒 Security Best Practices

✅ **Implemented:**
- Password hashing with bcrypt
- JWT tokens with short expiry
- HTTP-only cookie storage (recommended)
- Webhook signature verification
- HTTPS enforcement (via deployment platforms)
- Input validation with Pydantic

🔜 **Recommended Additions:**
- Rate limiting on auth endpoints
- Email verification
- Password reset flow
- Two-factor authentication (2FA)
- Account lockout after failed attempts

## 📈 Migration Strategy

### Soft Launch (Recommended)

**Week 1-2:**
- Deploy with `REQUIRE_SUBSCRIPTION=false`
- Add banner: "Subscribe for $5/month for unlimited access"
- Free users: 3 analyses/month
- Subscribers: Unlimited

**Week 3-4:**
- Show usage counter for free users
- Encourage subscription with benefits
- Collect feedback

**Week 5+:**
- Set `REQUIRE_SUBSCRIPTION=true`
- All analyses require subscription
- Email existing users with 1-week grace period

## 🎯 Next Steps

### Immediate
1. ✅ Test registration and login locally
2. ✅ Set up Stripe account and get test keys
3. ✅ Test complete payment flow
4. ✅ Verify webhook handling

### Before Production
1. Generate strong JWT_SECRET_KEY
2. Switch to Stripe live mode keys
3. Set up production webhook endpoint
4. Test with production Stripe checkout
5. Enable `REQUIRE_SUBSCRIPTION=true` when ready

### Optional Enhancements
1. Email notifications (SendGrid/Postmark)
2. Password reset flow
3. Email verification
4. Admin dashboard for user management
5. Analytics and revenue tracking
6. Team accounts / multi-user subscriptions

## 💰 Pricing Information

**Current Plan: Pro - $5/month**
- Unlimited parcel analyses
- All state law scenarios (SB 9, SB 35, AB 2011, Density Bonus)
- PDF export
- Economic feasibility analysis
- Priority support
- New cities added first

## 🐛 Troubleshooting

### "Invalid authentication token"
- Token expired - frontend will auto-refresh
- If persists, logout and login again
- Check JWT_SECRET_KEY matches between .env and runtime

### "Stripe webhook signature verification failed"
- Check STRIPE_WEBHOOK_SECRET matches Stripe dashboard
- For local testing, use Stripe CLI webhook secret
- Verify webhook endpoint URL in Stripe dashboard

### "Database session not configured"
- Make sure database tables are created
- Run: `python -c "from app.core.database import create_db_and_tables; create_db_and_tables()"`

### Checkout redirects but subscription not active
- Check Railway logs for webhook errors
- Verify all 4 webhook events are configured in Stripe
- Check STRIPE_WEBHOOK_SECRET is correct

## 📚 Resources

- [Stripe Testing](https://stripe.com/docs/testing)
- [Stripe Webhooks](https://stripe.com/docs/webhooks)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [Next.js Authentication](https://nextjs.org/docs/authentication)

## ✅ Implementation Checklist

### Backend ✅
- [x] User and Subscription models
- [x] JWT authentication utilities
- [x] Authentication endpoints
- [x] Stripe service
- [x] Payment endpoints
- [x] Webhook handling
- [x] Protected route dependencies
- [x] Database migrations

### Frontend ✅
- [x] Authentication types
- [x] Auth API client
- [x] Auth context provider
- [x] Login page
- [x] Registration page
- [x] Protected route middleware
- [x] Pricing page
- [x] User dashboard
- [x] Layout integration

### Documentation ✅
- [x] Environment variable examples
- [x] Setup instructions
- [x] API documentation
- [x] Deployment guide
- [x] Testing guide

---

**🎉 Congratulations! Your payment system is ready to go!**

For questions or issues, refer to the comprehensive documentation in [PAYMENT_INTEGRATION_SUMMARY.md](PAYMENT_INTEGRATION_SUMMARY.md).
