# 🧪 Testing Guide - Payment & Authentication System

## ✅ Setup Complete!

Your Stripe account is configured and ready to test:
- ✅ Product created: "Parcel Feasibility Engine Pro"
- ✅ Price created: $5.00/month
- ✅ Environment variables configured
- ✅ Database tables created

## 🚀 Start the Application

### Terminal 1: Backend Server
```bash
cd "/Users/Jordan_Ostwald/Parcel Feasibility Engine"
./venv/bin/uvicorn app.main:app --reload
```
**Backend:** http://localhost:8000
**API Docs:** http://localhost:8000/docs

### Terminal 2: Frontend Server
```bash
cd "/Users/Jordan_Ostwald/Parcel Feasibility Engine/frontend"
npm run dev
```
**Frontend:** http://localhost:3000

## 🧪 Test Scenarios

### Test 1: User Registration ✨
1. Visit: http://localhost:3000/auth/register
2. Fill in:
   - Email: `test@example.com`
   - Password: `Test1234` (uppercase, lowercase, numbers)
   - Full Name: `Test User` (optional)
3. Click "Create Account"
4. ✅ Should auto-login and redirect to dashboard

### Test 2: User Login 🔐
1. Logout (from dashboard)
2. Visit: http://localhost:3000/auth/login
3. Enter:
   - Email: `test@example.com`
   - Password: `Test1234`
4. Click "Sign In"
5. ✅ Should redirect to dashboard

### Test 3: Protected Routes 🛡️
1. Logout if logged in
2. Try to visit: http://localhost:3000/dashboard
3. ✅ Should redirect to login page
4. After login, dashboard should be accessible

### Test 4: User Dashboard 📊
1. Login to your account
2. Visit: http://localhost:3000/dashboard
3. ✅ Should see:
   - Your account info (email, name)
   - Subscription status (currently no subscription)
   - Usage stats (0 analyses)
   - "Subscribe Now" button

### Test 5: Pricing Page 💰
1. Visit: http://localhost:3000/pricing
2. ✅ Should see:
   - $5/month pricing card
   - List of features
   - "Subscribe Now" button
   - FAQ section

### Test 6: Stripe Checkout (Without Webhook) 💳
**Note:** Webhooks won't work locally yet, so subscription won't activate automatically.

1. Login to your account
2. Visit: http://localhost:3000/pricing
3. Click "Subscribe Now"
4. ✅ Should redirect to Stripe Checkout page
5. Use test card:
   - Card: `4242 4242 4242 4242`
   - Expiry: Any future date (e.g., 12/25)
   - CVC: Any 3 digits (e.g., 123)
   - Name: Test User
   - Country: United States
   - ZIP: Any 5 digits (e.g., 90401)
6. Click "Subscribe"
7. ✅ Should redirect back to dashboard
8. ⚠️ Subscription won't show as active yet (webhook needed)

### Test 7: API Endpoints 🔌
1. Visit: http://localhost:8000/docs
2. Test authentication endpoints:
   - **POST /api/v1/auth/register** - Create new user
   - **POST /api/v1/auth/login** - Get JWT tokens
   - **GET /api/v1/auth/me** - Get user profile (click "Authorize" button first)
3. Test payment endpoints (after authentication):
   - **POST /api/v1/payments/create-checkout-session**
   - **GET /api/v1/payments/usage**

## 🎯 Advanced Testing: Stripe Webhooks (Optional)

To test the complete flow with webhooks, you need Stripe CLI:

### Install Stripe CLI
```bash
brew install stripe/stripe-cli/stripe

# Login to Stripe
stripe login
```

### Forward Webhooks to Local Backend
```bash
# In Terminal 3:
stripe listen --forward-to localhost:8000/api/v1/payments/webhook

# This will output a webhook signing secret like:
# whsec_abc123...

# Copy that secret and add to .env:
# STRIPE_WEBHOOK_SECRET=whsec_abc123...

# Restart backend server to load new secret
```

### Test Complete Subscription Flow with Webhooks
1. With Stripe CLI running, complete Test 6 above
2. Watch the Stripe CLI terminal - you'll see webhook events
3. After checkout, subscription should activate automatically
4. Refresh dashboard - subscription status should show "ACTIVE"
5. ✅ Complete flow working!

### Trigger Test Webhooks
```bash
# Test subscription created
stripe trigger checkout.session.completed

# Test subscription updated
stripe trigger customer.subscription.updated

# Test payment failed
stripe trigger invoice.payment_failed
```

## 🧪 Test Cards (Stripe)

### Success
- **Visa:** 4242 4242 4242 4242
- **Mastercard:** 5555 5555 5555 4444
- **Amex:** 3782 822463 10005

### Requires Authentication (3D Secure)
- **Visa:** 4000 0027 6000 3184

### Declined
- **Generic Decline:** 4000 0000 0000 0002
- **Insufficient Funds:** 4000 0000 0000 9995
- **Lost Card:** 4000 0000 0000 9987

## 📊 Expected User Flow

### New User Journey
1. Visit homepage → Click "Sign Up"
2. Register account
3. Auto-login → Redirect to dashboard
4. See "Subscribe Now" button (no subscription)
5. Click pricing link → View $5/month plan
6. Click "Subscribe Now" → Stripe Checkout
7. Enter test card → Complete payment
8. Return to dashboard → Subscription active (with webhooks)
9. Start analyzing parcels!

### Returning User Journey
1. Visit homepage → Click "Sign In"
2. Login with credentials
3. Redirect to dashboard
4. View subscription status and usage
5. Click "Manage Billing" → Stripe Customer Portal
6. Can update card, cancel, view invoices

## ✅ Validation Checklist

### Authentication
- [ ] Registration validates email format
- [ ] Password requires 8+ chars, uppercase, lowercase, numbers
- [ ] Login with wrong password shows error
- [ ] Login with correct credentials works
- [ ] Protected routes redirect to login when not authenticated
- [ ] After login, can access dashboard
- [ ] Logout clears session and redirects to home

### User Interface
- [ ] Login page renders correctly
- [ ] Registration page renders correctly
- [ ] Dashboard shows user info
- [ ] Pricing page displays $5/month plan
- [ ] Error messages display clearly

### Payment Flow
- [ ] Subscribe button redirects to Stripe Checkout
- [ ] Can enter test card details
- [ ] Checkout completes successfully
- [ ] Returns to app after payment
- [ ] (With webhooks) Subscription activates

### API
- [ ] All auth endpoints respond correctly
- [ ] JWT tokens are generated
- [ ] Protected endpoints require authentication
- [ ] Stripe integration works
- [ ] Error responses are clear

## 🐛 Common Issues & Solutions

### "Module not found" errors
```bash
cd frontend
npm install --legacy-peer-deps
```

### "Database session not configured"
```bash
./venv/bin/python -c "from app.core.database import create_db_and_tables; create_db_and_tables()"
```

### Can't login / "Invalid token"
- Check JWT_SECRET_KEY is set in .env
- Try logging out and logging in again
- Clear browser cookies

### Subscription doesn't activate after payment
- This is normal without webhooks setup
- Set up Stripe CLI webhook forwarding (see Advanced Testing above)
- Or manually set subscription status in database for testing

### Frontend can't reach backend
- Make sure backend is running on localhost:8000
- Check NEXT_PUBLIC_API_URL in frontend/.env.local
- Check browser console for CORS errors

## 📈 Success Metrics

After testing, you should have:
- ✅ At least 1 registered user
- ✅ Successful login/logout
- ✅ Dashboard displaying correctly
- ✅ Stripe checkout flow working
- ✅ All API endpoints responding
- ✅ (Optional) Webhook events processing

## 🎉 Next Steps

Once testing is complete:

1. **For Production:**
   - Generate strong JWT_SECRET_KEY
   - Switch to Stripe live mode
   - Set up production webhooks
   - Deploy to Railway + Vercel

2. **For Development:**
   - Set up Stripe CLI for local webhook testing
   - Add email notifications
   - Build password reset flow
   - Add email verification

3. **For Launch:**
   - Set REQUIRE_SUBSCRIPTION=true
   - Announce to users
   - Start marketing!

---

**🚀 Your payment system is ready to test! Start both servers and begin testing!**
