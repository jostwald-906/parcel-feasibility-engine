# Sentry Error Monitoring Setup Guide

Complete guide to set up error monitoring for the Parcel Feasibility Engine.

## 📋 Prerequisites

- [x] Railway account with deployed backend
- [x] Vercel account (for frontend deployment)
- [ ] Sentry account (free tier available)
- [x] Railway CLI installed (`npm i -g @railway/cli`)
- [ ] Vercel CLI installed (`npm i -g vercel`)

## 🎯 Quick Start (5 Minutes)

### Step 1: Create Sentry Projects (3 minutes)

1. **Go to [https://sentry.io](https://sentry.io)** and sign up/login

2. **Create Backend Project:**
   - Click "**Create Project**"
   - Platform: **Python** → **FastAPI**
   - Project Name: `parcel-feasibility-backend`
   - Team: Default
   - Alert frequency: **Alert me on every new issue**
   - Click "**Create Project**"
   - **📋 Copy the DSN** - looks like: `https://xxxxx@o123456.ingest.sentry.io/7891011`
   - Save this as `BACKEND_DSN`

3. **Create Frontend Project:**
   - Click "**Projects**" → "**Create Project**"
   - Platform: **JavaScript** → **Next.js**
   - Project Name: `parcel-feasibility-frontend`
   - Team: Default
   - Alert frequency: **Alert me on every new issue**
   - Click "**Create Project**"
   - **📋 Copy the DSN** - looks like: `https://yyyyy@o123456.ingest.sentry.io/7891012`
   - Save this as `FRONTEND_DSN`

4. **Get Your Organization Slug:**
   - Look at your browser URL: `https://sentry.io/organizations/YOUR-ORG-SLUG/`
   - Or go to **Settings** → **General Settings**
   - Save this as `SENTRY_ORG`

### Step 2: Run Configuration Script (2 minutes)

Once you have all three values (BACKEND_DSN, FRONTEND_DSN, SENTRY_ORG), run:

```bash
cd "/Users/Jordan_Ostwald/Parcel Feasibility Engine"
./scripts/configure_sentry.sh
```

The script will prompt you for:
1. Backend Sentry DSN
2. Frontend Sentry DSN
3. Sentry Organization Slug

Then it will automatically:
- ✅ Configure Railway environment variables
- ✅ Configure Vercel environment variables (if CLI installed)
- ✅ Enable rate limiting on Railway

### Step 3: Deploy (2 minutes)

```bash
# Redeploy backend to Railway
railway up

# Deploy frontend to Vercel
cd frontend
vercel --prod
```

---

## 🔧 Manual Configuration (Alternative)

If you prefer to configure manually or the script fails:

### Railway Backend Configuration

```bash
cd "/Users/Jordan_Ostwald/Parcel Feasibility Engine"

# Set Sentry variables
railway variables set SENTRY_DSN="https://your-backend-dsn@sentry.io/project-id"
railway variables set SENTRY_ENABLED=true
railway variables set SENTRY_ENVIRONMENT=production
railway variables set SENTRY_TRACES_SAMPLE_RATE=0.1

# Enable rate limiting
railway variables set RATE_LIMIT_ENABLED=true
railway variables set RATE_LIMIT_PER_MINUTE=60

# Redeploy
railway up
```

### Vercel Frontend Configuration

**Option A: Using Vercel CLI**
```bash
cd frontend

# Add environment variables
vercel env add NEXT_PUBLIC_SENTRY_DSN production
# Paste: https://your-frontend-dsn@sentry.io/project-id

vercel env add SENTRY_ORG production
# Paste: your-org-slug

vercel env add SENTRY_PROJECT production
# Paste: parcel-feasibility-frontend

vercel env add NEXT_PUBLIC_SENTRY_ENVIRONMENT production
# Paste: production

# Deploy
vercel --prod
```

**Option B: Using Vercel Dashboard**
1. Go to https://vercel.com/dashboard
2. Select your project
3. Go to **Settings** → **Environment Variables**
4. Add each variable:

| Name | Value | Environment |
|------|-------|-------------|
| `NEXT_PUBLIC_SENTRY_DSN` | `https://your-frontend-dsn@sentry.io/project-id` | Production |
| `SENTRY_ORG` | `your-org-slug` | Production |
| `SENTRY_PROJECT` | `parcel-feasibility-frontend` | Production |
| `NEXT_PUBLIC_SENTRY_ENVIRONMENT` | `production` | Production |

5. **Redeploy** → Deployments → Click menu → Redeploy

---

## ✅ Verification

### 1. Check Railway Backend

```bash
# Check health endpoint
curl https://parcel-feasibility-engine-production.up.railway.app/health

# Should return:
{
  "status": "healthy",
  "services": {
    "error_monitoring": true,
    "rate_limiting": true
  }
}
```

### 2. Check Sentry Integration

**Backend Test:**
```bash
# Trigger a test error
curl https://parcel-feasibility-engine-production.up.railway.app/api/v1/analyze \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"apn": "INVALID-APN-12345"}'

# Go to Sentry dashboard - you should see the error
```

**Frontend Test:**
1. Visit your Vercel URL
2. Open browser console: `Sentry.captureMessage('Test error from frontend')`
3. Check Sentry frontend project - you should see the message

### 3. Check Rate Limiting

```bash
# Make 11 rapid requests (should get 429 on 11th)
for i in {1..11}; do
  echo "Request $i:"
  curl -w "\nStatus: %{http_code}\n" \
    https://parcel-feasibility-engine-production.up.railway.app/health
  sleep 0.5
done

# Request 11 should return 429 (Too Many Requests)
```

---

## 📊 Monitoring & Alerts

### Sentry Dashboard

- **Backend:** https://sentry.io/organizations/YOUR-ORG/projects/parcel-feasibility-backend/
- **Frontend:** https://sentry.io/organizations/YOUR-ORG/projects/parcel-feasibility-frontend/

### Key Metrics to Watch

1. **Error Rate**
   - Target: < 1% of requests
   - Alert: Set up email alerts for new issues

2. **Performance (Transaction Traces)**
   - Backend: 10% sampling rate
   - Frontend: 10% sampling rate
   - Watch for slow endpoints

3. **GIS Service Health**
   - Monitor `GISServiceUnavailable` errors
   - Check stale cache usage via `/admin/cache/stats`

### Recommended Alerts

Set up in Sentry → Alerts:

1. **Critical Error Alert**
   - Trigger: Any error with "Critical" tag
   - Notify: Email + Slack
   - Frequency: Immediately

2. **High Error Volume**
   - Trigger: > 10 errors in 5 minutes
   - Notify: Email
   - Frequency: Once per hour

3. **GIS Service Down**
   - Trigger: `GISServiceUnavailable` error
   - Notify: Email
   - Frequency: Once per 30 minutes

---

## 🔍 Troubleshooting

### "Sentry not capturing errors"

**Check 1: Environment variables set?**
```bash
railway variables | grep SENTRY
# Should show SENTRY_DSN and SENTRY_ENABLED=true
```

**Check 2: DSN format correct?**
```
✅ Correct: https://abc123@o456789.ingest.sentry.io/1234567
❌ Wrong: abc123 (missing https://)
❌ Wrong: https://sentry.io/... (must be ingest.sentry.io)
```

**Check 3: Check Railway logs**
```bash
railway logs | grep -i sentry
# Should see: "Sentry error monitoring initialized"
```

### "Rate limiting not working"

```bash
railway variables | grep RATE_LIMIT
# Should show RATE_LIMIT_ENABLED=true
```

### "Frontend Sentry not working"

**Check browser console:**
```javascript
// Should be defined
window.Sentry

// Test it
Sentry.captureMessage('Test')
// Check Sentry dashboard for the message
```

---

## 🎓 Best Practices

### 1. Tag Your Errors

```python
# In Python backend
import sentry_sdk

sentry_sdk.set_tag("feature", "gis-lookup")
sentry_sdk.set_tag("user_type", "premium")
```

### 2. Add Context

```python
sentry_sdk.set_context("parcel", {
    "apn": "4285-030-032",
    "zoning": "R2",
    "lot_size": 7500
})
```

### 3. Filter Sensitive Data

Already configured in `app/main.py`:
- `send_default_pii=False` - No personally identifiable information
- Custom `before_send` hook filters dev errors

### 4. Monitor Performance

Key endpoints to watch:
- `/api/v1/analyze` - Should be < 5s
- `/api/v1/export/pdf` - Should be < 10s
- GIS API calls - Should be < 1s (with cache)

---

## 📚 Resources

- **Sentry Docs:** https://docs.sentry.io/platforms/python/guides/fastapi/
- **Next.js Integration:** https://docs.sentry.io/platforms/javascript/guides/nextjs/
- **Railway Docs:** https://docs.railway.app/
- **Vercel Docs:** https://vercel.com/docs/concepts/projects/environment-variables

---

## 🆘 Need Help?

1. Check Railway logs: `railway logs`
2. Check Sentry dashboard: https://sentry.io
3. Verify environment variables: `railway variables`
4. Test health endpoint: `curl .../health`

If issues persist, check:
- [app/main.py](app/main.py) - Backend Sentry initialization
- [frontend/sentry.client.config.ts](frontend/sentry.client.config.ts) - Frontend config
- [Dockerfile](Dockerfile) - Deployment configuration
