# Sentry Setup - Quick Reference Card

## ⚡ 5-Minute Setup

### 1. Create Sentry Projects
Go to https://sentry.io → Create 2 projects:

**Backend Project:**
- Platform: Python → FastAPI
- Name: `parcel-feasibility-backend`
- Copy DSN → Save as `BACKEND_DSN`

**Frontend Project:**
- Platform: JavaScript → Next.js
- Name: `parcel-feasibility-frontend`
- Copy DSN → Save as `FRONTEND_DSN`

**Organization Slug:**
- URL: `https://sentry.io/organizations/YOUR-ORG-SLUG/`
- Save as `SENTRY_ORG`

### 2. Run Configuration Script

```bash
cd "/Users/Jordan_Ostwald/Parcel Feasibility Engine"
./scripts/configure_sentry.sh
```

Enter when prompted:
1. Backend DSN (from step 1)
2. Frontend DSN (from step 1)
3. Organization slug (from step 1)

### 3. Deploy

```bash
# Backend
railway up

# Frontend
cd frontend && vercel --prod
```

---

## 🔍 Manual Commands (if script fails)

### Railway Backend
```bash
railway variables set SENTRY_DSN="YOUR_BACKEND_DSN"
railway variables set SENTRY_ENABLED=true
railway variables set SENTRY_ENVIRONMENT=production
railway variables set RATE_LIMIT_ENABLED=true
railway up
```

### Vercel Frontend
```bash
cd frontend
vercel env add NEXT_PUBLIC_SENTRY_DSN production
# Enter: YOUR_FRONTEND_DSN
vercel env add SENTRY_ORG production
# Enter: YOUR_ORG_SLUG
vercel env add SENTRY_PROJECT production
# Enter: parcel-feasibility-frontend
vercel --prod
```

---

## ✅ Verification

```bash
# Health check (should show error_monitoring: true)
curl https://parcel-feasibility-engine-production.up.railway.app/health

# Check Railway logs for Sentry
railway logs | grep -i sentry

# Check environment variables
railway variables | grep SENTRY
```

---

## 📱 Quick Links

- **Sentry Dashboard:** https://sentry.io/organizations/YOUR-ORG/
- **Railway Project:** https://railway.app/project/9385a16b-6ca2-48eb-9a4e-67c3e49c3068
- **Backend URL:** https://parcel-feasibility-engine-production.up.railway.app
- **Full Guide:** [SENTRY_SETUP_GUIDE.md](SENTRY_SETUP_GUIDE.md)

---

## 🆘 Troubleshooting

**Sentry not working?**
```bash
# Check if variables are set
railway variables | grep SENTRY_ENABLED
# Should return: SENTRY_ENABLED=true

# Check logs for initialization
railway logs | grep "Sentry error monitoring initialized"
```

**Need to update DSN?**
```bash
railway variables set SENTRY_DSN="new-dsn-here"
railway up  # Redeploy
```
