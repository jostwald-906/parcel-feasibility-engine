# Sentry DSN Configuration Guide

## Current Status

### ✅ Frontend Sentry Setup
**Status:** Code configured, waiting for DSN

**Files:**
- [frontend/sentry.client.config.ts](frontend/sentry.client.config.ts) - Browser error tracking
- [frontend/sentry.server.config.ts](frontend/sentry.server.config.ts) - Server-side error tracking
- [frontend/sentry.edge.config.ts](frontend/sentry.edge.config.ts) - Edge runtime tracking
- [frontend/instrumentation.ts](frontend/instrumentation.ts) - Next.js instrumentation
- [frontend/next.config.ts](frontend/next.config.ts) - Wrapped with Sentry

**Current `.env.local`:**
```bash
NEXT_PUBLIC_SENTRY_DSN=          # ❌ Empty - needs DSN
SENTRY_ORG=                      # ❌ Empty - needs org slug
SENTRY_PROJECT=parcel-feasibility-frontend  # ✅ Set
```

### ✅ Backend Sentry Setup
**Status:** Code configured, needs DSN in environment

**Files:**
- [app/main.py](app/main.py#L45-L65) - Sentry initialization
- [app/core/config.py](app/core/config.py) - Sentry configuration

**Current `.env`:**
```bash
# ❌ No Sentry configuration found in local .env file
# Railway production has SENTRY_DSN configured
```

**Required Environment Variables:**
```bash
SENTRY_DSN=https://xxxxx@sentry.io/project-id
SENTRY_ENABLED=true
SENTRY_TRACES_SAMPLE_RATE=0.1
SENTRY_ENVIRONMENT=development  # or production
```

---

## How to Set Up Sentry DSNs

### Step 1: Log into Sentry
Visit https://sentry.io and log in to your account.

### Step 2: Create Projects (if not already created)

#### Backend Project
1. Click "Projects" in the left sidebar
2. Click "Create Project"
3. Platform: **Python** → **FastAPI**
4. Project name: `parcel-feasibility-backend`
5. Click "Create Project"
6. Copy the DSN (format: `https://xxxxx@sentry.io/1234567`)

#### Frontend Project
1. Click "Create Project" again
2. Platform: **JavaScript** → **Next.js**
3. Project name: `parcel-feasibility-frontend`
4. Click "Create Project"
5. Copy the DSN (format: `https://xxxxx@sentry.io/7654321`)

### Step 3: Get Your Organization Slug
1. Click Settings (⚙️) in the left sidebar
2. Under "Organization", click your organization name
3. The **Organization Slug** is shown at the top (e.g., `my-company-ab12cd`)

---

## Configuration Steps

### Frontend Configuration

1. **Edit `frontend/.env.local`:**
   ```bash
   # Sentry Configuration
   NEXT_PUBLIC_SENTRY_DSN=https://xxxxx@sentry.io/FRONTEND_PROJECT_ID
   SENTRY_ORG=your-org-slug
   SENTRY_PROJECT=parcel-feasibility-frontend
   ```

2. **Restart the dev server:**
   ```bash
   cd frontend
   npm run dev
   ```

3. **Test the integration:**
   - Visit http://localhost:3000/sentry-example-page
   - Click the "Trigger Test Error" button
   - Check browser console for the error
   - Check Sentry dashboard for the captured event

### Backend Configuration

#### Local Development

1. **Edit `.env` in project root:**
   ```bash
   # Add these lines to .env
   SENTRY_DSN=https://xxxxx@sentry.io/BACKEND_PROJECT_ID
   SENTRY_ENABLED=true
   SENTRY_TRACES_SAMPLE_RATE=0.1
   SENTRY_ENVIRONMENT=development
   ```

2. **Restart the backend server:**
   ```bash
   ./venv/bin/uvicorn app.main:app --reload --port 8000
   ```

3. **Test the integration:**
   - Visit http://localhost:8000/sentry-debug
   - Check terminal output
   - Check Sentry dashboard for the captured error

#### Production (Railway)

The backend is already deployed to Railway with Sentry configured!

**Railway Environment Variables (Already Set):**
- `SENTRY_DSN` - ✅ Configured on Railway
- `SENTRY_ENABLED=true` - ✅ Set
- `SENTRY_TRACES_SAMPLE_RATE=0.1` - ✅ Set
- `SENTRY_ENVIRONMENT=production` - ✅ Set

**Production Test Endpoint:**
https://parcel-feasibility-backend-production.up.railway.app/sentry-debug

---

## Verification

### Frontend Verification

**Development Mode Note:**
The frontend Sentry configuration has `beforeSend` filtering that prevents events from being sent in development mode. To test locally:

**Option 1: Test in Browser Console**
```javascript
// Open browser console and run:
Sentry.captureMessage('Test from frontend dev');
```

**Option 2: Temporarily Disable Dev Filter**
Edit [frontend/sentry.client.config.ts](frontend/sentry.client.config.ts):
```typescript
beforeSend(event, hint) {
  // Comment out the dev check temporarily
  // if (process.env.NODE_ENV === 'development') {
  //   return null;
  // }
  return event;
},
```

**Option 3: Deploy to Vercel**
Deploy the frontend to production where events will be sent automatically.

### Backend Verification

**Local:**
```bash
curl http://localhost:8000/sentry-debug
```

**Production:**
```bash
curl https://parcel-feasibility-backend-production.up.railway.app/sentry-debug
```

Check your Sentry dashboard at:
- Backend: https://sentry.io/organizations/YOUR-ORG/issues/?project=BACKEND_PROJECT_ID
- Frontend: https://sentry.io/organizations/YOUR-ORG/issues/?project=FRONTEND_PROJECT_ID

---

## Sentry Dashboard URLs

Once configured, you can access:

**Backend Project:**
https://sentry.io/organizations/YOUR-ORG/projects/parcel-feasibility-backend/

**Frontend Project:**
https://sentry.io/organizations/YOUR-ORG/projects/parcel-feasibility-frontend/

**Issues Dashboard:**
https://sentry.io/organizations/YOUR-ORG/issues/

---

## Current DSN Status

| Component | Environment | DSN Status | Location |
|-----------|-------------|------------|----------|
| **Frontend** | Local Dev | ❌ Not Set | `frontend/.env.local` |
| **Frontend** | Production | ⏳ Pending Vercel Deployment | Vercel env vars |
| **Backend** | Local Dev | ❌ Not Set | `.env` |
| **Backend** | Production | ✅ Configured | Railway env vars |

---

## Next Steps

1. ✅ **Backend Production** - Already working on Railway
2. ⏳ **Get Frontend DSN** - Create Sentry project and add to `.env.local`
3. ⏳ **Get Backend DSN** - Add to local `.env` for development testing
4. ⏳ **Deploy Frontend** - Deploy to Vercel with Sentry env vars

---

## Troubleshooting

### No Events in Sentry

**Check:**
1. DSN is correctly formatted (starts with `https://`)
2. Environment variable is loaded (restart dev server after changes)
3. In development, `beforeSend` might be filtering events
4. Check browser/terminal console for Sentry initialization messages

### Events Not Captured

**Frontend:**
- Check browser console for Sentry SDK messages
- Verify `NEXT_PUBLIC_` prefix on client-side variables
- Check Network tab for requests to `sentry.io`

**Backend:**
- Check terminal logs for Sentry initialization
- Verify `SENTRY_ENABLED=true`
- Test with `/sentry-debug` endpoint

### DSN Format

**Correct Format:**
```
https://examplePublicKey@o0.ingest.sentry.io/0
```

**Common Mistakes:**
- ❌ Missing `https://`
- ❌ Missing `@` separator
- ❌ Wrong project ID
- ❌ Expired or revoked DSN

---

**Last Updated:** October 7, 2025
