# Production Deployment Guide

## Overview

This guide covers best practices for deploying the Parcel Feasibility Engine to production with proper environment configuration and Sentry error monitoring.

---

## Environment Strategy

### Development (Local)
- **Environment:** `development`
- **Sentry:** ❌ Events filtered (not sent to Sentry)
- **Purpose:** Local development and testing
- **Console logs:** Show captured errors but don't send

### Staging/Testing (GitHub/Vercel Preview)
- **Environment:** `staging` or `preview`
- **Sentry:** ❌ Events filtered (not sent to Sentry)
- **Purpose:** Testing before production deployment
- **Optional:** Can enable Sentry with separate staging project

### Production (Railway + Vercel)
- **Environment:** `production`
- **Sentry:** ✅ All events sent to Sentry dashboard
- **Purpose:** Live production deployment
- **Monitoring:** Full error tracking and performance monitoring

---

## Backend Deployment (Railway)

### Current Status
✅ Already deployed to Railway with production configuration

###Environment Variables on Railway

**Required for Production:**
```bash
# Application
ENVIRONMENT=production
PROJECT_NAME=Parcel Feasibility Engine API
VERSION=1.0.0

# Database (PostgreSQL)
DATABASE_URL=postgresql://user:password@host:port/database

# Sentry Error Monitoring
SENTRY_DSN=https://e2d8a4e6cf15c114a1de078a757fad6e@o4510146612101120.ingest.us.sentry.io/4510146633072640
SENTRY_ENABLED=true
SENTRY_TRACES_SAMPLE_RATE=0.1
SENTRY_ENVIRONMENT=production

# JWT Authentication
JWT_SECRET_KEY=<your-production-secret-min-32-chars>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# Stripe (Production Keys)
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_ID_PRO=price_...

# External APIs
FRED_API_KEY=<your-key>
HUD_API_TOKEN=<your-token>
```

### Deployment Process

1. **Push to GitHub:**
   ```bash
   git push origin main
   ```

2. **Railway Auto-Deploy:**
   - Railway automatically detects the push
   - Runs `scripts/startup.sh`:
     - Executes database migrations (`alembic upgrade head`)
     - Starts uvicorn server
   - Health check at `/health`
   - Restarts on failure (max 10 retries)

3. **Verify Deployment:**
   ```bash
   # Check health
   curl https://parcel-feasibility-backend-production.up.railway.app/health

   # Check Sentry initialization
   # Look for "error_monitoring": true in health response
   ```

4. **Monitor Errors:**
   - Visit: https://sentry.io/organizations/d3ai/issues/?project=4510146633072640
   - Only production errors appear (dev/staging filtered out)

---

## Frontend Deployment (Vercel)

### Environment Variables for Vercel

**Production Environment:**
```bash
# Backend API
NEXT_PUBLIC_API_URL=https://parcel-feasibility-backend-production.up.railway.app

# Stripe
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_live_...

# Sentry (Frontend)
NEXT_PUBLIC_SENTRY_DSN=https://6afbe26ee5c14d5a0416ebb6a5658aa3@o4510146612101120.ingest.us.sentry.io/4510151500496896
SENTRY_ORG=d3ai
SENTRY_PROJECT=parcel-feasibility-frontend
NEXT_PUBLIC_SENTRY_ENVIRONMENT=production
SENTRY_ENVIRONMENT=production

# Auth Token (for uploading source maps)
SENTRY_AUTH_TOKEN=<get-from-sentry-settings>
```

**Preview/Staging Environment (Optional):**
```bash
# Same as production but:
NEXT_PUBLIC_SENTRY_ENVIRONMENT=staging
SENTRY_ENVIRONMENT=staging

# Note: With current config, staging events are filtered out
# To enable staging monitoring, create separate Sentry project
```

### Deployment Steps

1. **Connect to Vercel:**
   ```bash
   cd frontend
   vercel login
   vercel link
   ```

2. **Set Environment Variables:**
   - Go to Vercel Dashboard → Project → Settings → Environment Variables
   - Add all variables above
   - Set scope: Production, Preview, or both

3. **Deploy:**
   ```bash
   # Deploy to production
   git push origin main

   # Or manual deploy
   vercel --prod
   ```

4. **Verify:**
   - Visit your Vercel URL
   - Check browser console: "[Sentry Dev] Error captured locally (not sent)" should NOT appear in production
   - Trigger test error (if needed) and verify it appears in Sentry

---

## How Sentry Filtering Works

### Backend ([app/main.py](app/main.py:47))
```python
before_send=lambda event, hint: event if settings.ENVIRONMENT == "production" else None,
```

**Behavior:**
- ✅ `ENVIRONMENT=production` → Events sent to Sentry
- ❌ `ENVIRONMENT=development` → Events filtered (logged locally)
- ❌ `ENVIRONMENT=staging` → Events filtered
- ❌ Any other value → Events filtered

### Frontend

**Client-side ([frontend/instrumentation-client.ts](frontend/instrumentation-client.ts:34-44)):**
```typescript
beforeSend(event, hint) {
  const environment = process.env.NEXT_PUBLIC_SENTRY_ENVIRONMENT || process.env.NODE_ENV;

  if (environment !== 'production') {
    console.log('[Sentry Dev] Error captured locally (not sent):', ...);
    return null;
  }

  return event;
}
```

**Server-side ([frontend/sentry.server.config.ts](frontend/sentry.server.config.ts:26-32)):**
```typescript
beforeSend(event, hint) {
  if (SENTRY_ENVIRONMENT !== 'production') {
    console.log('[Sentry Server Dev] Event captured locally (not sent):', ...);
    return null;
  }
  return event;
}
```

**Behavior:**
- ✅ `NEXT_PUBLIC_SENTRY_ENVIRONMENT=production` → Events sent
- ❌ `development` / `staging` / anything else → Events filtered

---

## Git Workflow Best Practices

### Development → Staging → Production

```bash
# 1. Work on feature branch locally
git checkout -b feature/my-feature
# Make changes, test locally
# Sentry is disabled, errors only logged to console

# 2. Commit and push to GitHub
git add .
git commit -m "Add new feature"
git push origin feature/my-feature

# 3. Create Pull Request
# GitHub Actions can run tests
# Deploy to preview environment (optional)
# Sentry still disabled in preview

# 4. Merge to main
# After review and approval
git checkout main
git merge feature/my-feature
git push origin main

# 5. Production Deploy
# Railway auto-deploys backend
# Vercel auto-deploys frontend
# Sentry automatically enabled (ENVIRONMENT=production)
```

### Environment Variables Auto-Update

**Railway:**
- Set environment variables once in Railway dashboard
- Variables persist across deployments
- `ENVIRONMENT=production` is always set
- Sentry automatically enabled on every deploy

**Vercel:**
- Set environment variables in Vercel dashboard
- Separate configs for Production vs Preview
- Production: `NEXT_PUBLIC_SENTRY_ENVIRONMENT=production`
- Preview: `NEXT_PUBLIC_SENTRY_ENVIRONMENT=preview` (events filtered)

**No manual intervention needed** - once environment variables are configured on the platforms, they automatically apply to all future deployments.

---

## Testing Sentry in Production

### Safe Testing Method

**Option 1: Use Sentry Test Endpoints (Recommended)**

Backend:
```bash
# This triggers a controlled test error
curl https://your-backend.up.railway.app/sentry-debug
```

Frontend:
- Visit: `https://your-frontend.vercel.app/sentry-test-simple`
- Click "Send Test Message" or "Send Test Error"
- Check Sentry dashboard

**Option 2: Temporary Test Mode**

If you need to test Sentry from local/dev environment:

1. Temporarily change environment:
   ```bash
   # Local backend
   ENVIRONMENT=production ./venv/bin/uvicorn app.main:app

   # Local frontend
   NEXT_PUBLIC_SENTRY_ENVIRONMENT=production npm run dev
   ```

2. Test error capture

3. Change back to `development`

**⚠️ Warning:** Don't leave this in production mode locally - you'll send dev errors to production Sentry!

---

## Monitoring Production

### Sentry Dashboards

**Backend Errors:**
https://sentry.io/organizations/d3ai/issues/?project=4510146633072640

**Frontend Errors:**
https://sentry.io/organizations/d3ai/issues/?project=4510151500496896

**What to Monitor:**
- ✅ Error frequency and trends
- ✅ Performance issues (slow endpoints)
- ✅ User session replays (frontend)
- ✅ Stack traces and context
- ✅ Affected users and browsers

### Railway Monitoring

- **Logs:** Railway Dashboard → Deployments → Logs
- **Metrics:** CPU, Memory, Request count
- **Health:** Check `/health` endpoint

### Vercel Monitoring

- **Analytics:** Vercel Dashboard → Analytics
- **Logs:** Vercel Dashboard → Deployments → Function Logs
- **Performance:** Core Web Vitals

---

## Troubleshooting

### "Events not appearing in Sentry"

**Check:**
1. Environment variable is `production` (not `prod`, `Production`, etc.)
2. Sentry DSN is correctly set
3. Look for initialization log: "Sentry error monitoring initialized"
4. Check environment in Sentry event (should show "production")

**Debug:**
```bash
# Backend - check logs
railway logs

# Frontend - check browser console
# Should NOT see "[Sentry Dev] Error captured locally"
```

### "Dev errors appearing in production Sentry"

**Issue:** Environment variable not set correctly

**Fix:**
```bash
# Railway - verify
railway variables

# Vercel - check dashboard
# Settings → Environment Variables
# Ensure NEXT_PUBLIC_SENTRY_ENVIRONMENT=production
```

### "Sentry not initializing"

**Check:**
1. DSN is set and valid
2. `SENTRY_ENABLED=true` (backend)
3. Sentry SDK is installed (`@sentry/nextjs`, `sentry-sdk[fastapi]`)
4. Check for initialization errors in logs

---

## Security Best Practices

### Environment Variables

❌ **Never commit:**
- `.env` files
- `frontend/.env.local` files
- Sentry DSNs, auth tokens
- API keys, secrets

✅ **Always:**
- Use platform environment variable managers (Railway, Vercel)
- Keep `.env.example` for documentation
- Rotate secrets regularly
- Use different DSNs for different environments (if monitoring staging)

### Sentry Configuration

✅ **Enabled:**
- `send_default_pii=False` (backend) - Don't send user IPs/headers
- `maskAllText: true` (frontend) - Mask sensitive data in replays
- `blockAllMedia: true` (frontend) - Block media in replays
- Error filtering for known browser extensions

✅ **Sample Rates:**
- Performance: 10% (to reduce costs)
- Session Replay: 10% normal, 100% on errors
- Adjust based on traffic and budget

---

## Deployment Checklist

### Before First Production Deploy

Backend:
- [ ] Set `ENVIRONMENT=production` on Railway
- [ ] Configure production `DATABASE_URL` (PostgreSQL)
- [ ] Set Sentry DSN and enable Sentry
- [ ] Use production Stripe keys
- [ ] Set secure `JWT_SECRET_KEY`
- [ ] Configure external API keys

Frontend:
- [ ] Set `NEXT_PUBLIC_SENTRY_ENVIRONMENT=production` on Vercel
- [ ] Set frontend Sentry DSN
- [ ] Configure production `NEXT_PUBLIC_API_URL`
- [ ] Use production Stripe publishable key
- [ ] Add Sentry auth token for source maps

### Every Deploy

- [ ] Test locally first (`development` environment)
- [ ] Push to GitHub (triggers auto-deploy)
- [ ] Verify deployment health endpoints
- [ ] Check Sentry for initialization
- [ ] Monitor for errors in first 10 minutes
- [ ] Verify key features work correctly

---

## Quick Reference

| Environment | Backend Env Var | Frontend Env Var | Sentry Events | Where |
|-------------|----------------|------------------|---------------|-------|
| **Local Dev** | `ENVIRONMENT=development` | `NODE_ENV=development` | ❌ Filtered | Your machine |
| **GitHub Actions** | `ENVIRONMENT=test` | `NODE_ENV=test` | ❌ Filtered | CI/CD |
| **Vercel Preview** | N/A | `NEXT_PUBLIC_SENTRY_ENVIRONMENT=preview` | ❌ Filtered | Vercel PR deploys |
| **Production** | `ENVIRONMENT=production` | `NEXT_PUBLIC_SENTRY_ENVIRONMENT=production` | ✅ Sent to Sentry | Railway + Vercel |

---

**Last Updated:** October 7, 2025
**Sentry Configuration:** Production-only monitoring enabled
