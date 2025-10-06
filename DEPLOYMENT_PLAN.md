# Deployment Plan

## Overview

This document outlines the deployment strategy for the Parcel Feasibility Engine, a full-stack application with a FastAPI backend and Next.js frontend.

## Deployment Architecture

- **Backend**: Railway (FastAPI + Python 3.13)
- **Frontend**: Vercel (Next.js 15.5.4)
- **Version Control**: GitHub

## Pre-Deployment Checklist

- [x] Create Dockerfile with Python 3.13
- [x] Create .dockerignore
- [x] Create railway.json configuration
- [x] Create Procfile for Railway
- [x] Create runtime.txt specifying Python version
- [x] Create frontend/vercel.json configuration
- [x] Update .gitignore with deployment artifacts
- [x] Initialize Git repository
- [ ] Create initial Git commit
- [ ] Create GitHub repository
- [ ] Push code to GitHub
- [ ] Deploy backend to Railway
- [ ] Deploy frontend to Vercel
- [ ] Configure environment variables
- [ ] Test production deployment

## Step-by-Step Deployment

### 1. GitHub Repository Setup

```bash
# Create initial commit (run from project root)
git add .
git commit -m "Initial commit: Parcel Feasibility Engine

- FastAPI backend with SB 9, SB 35, AB 2011, Density Bonus analysis
- Next.js frontend with Turbopack
- GIS integration for Santa Monica parcels
- Rent control database lookup with caching
- Environmental constraint checking
- Deployment configurations for Railway and Vercel

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# Create GitHub repository (via GitHub CLI or web interface)
gh repo create parcel-feasibility-engine --public --source=. --remote=origin

# Or manually:
# 1. Go to https://github.com/new
# 2. Create repository named "parcel-feasibility-engine"
# 3. Add remote:
git remote add origin https://github.com/YOUR_USERNAME/parcel-feasibility-engine.git

# Push to GitHub
git branch -M main
git push -u origin main
```

### 2. Railway Backend Deployment

#### Install Railway CLI
```bash
npm install -g @railway/cli
```

#### Deploy Backend
```bash
# Login to Railway
railway login

# Initialize Railway project
railway init

# Link to existing project (if already created) or create new
railway link

# Deploy
railway up

# Get the deployed URL
railway domain
```

#### Set Environment Variables in Railway Dashboard
1. Go to https://railway.app/dashboard
2. Select your project
3. Go to Variables tab
4. Add:
   - `PORT`: (auto-set by Railway)
   - `ENVIRONMENT`: `production`

#### Verify Deployment
- Check health endpoint: `https://your-app.railway.app/health`
- Check API docs: `https://your-app.railway.app/docs`

### 3. Vercel Frontend Deployment

#### Install Vercel CLI
```bash
npm install -g vercel
```

#### Deploy Frontend
```bash
# Navigate to frontend directory
cd frontend

# Deploy (follow prompts)
vercel

# For production deployment
vercel --prod
```

#### Set Environment Variables in Vercel Dashboard
1. Go to https://vercel.com/dashboard
2. Select your project
3. Go to Settings → Environment Variables
4. Add:
   - `NEXT_PUBLIC_API_URL`: Your Railway backend URL (e.g., `https://your-app.railway.app`)

#### Redeploy with Environment Variables
```bash
vercel --prod
```

### 4. Post-Deployment Verification

#### Backend Health Check
```bash
curl https://your-app.railway.app/health
# Expected: {"status":"healthy"}
```

#### Frontend Connection Test
1. Visit your Vercel URL
2. Enter a Santa Monica address
3. Verify API calls succeed (check Network tab)
4. Confirm analysis results display correctly

#### Test API Endpoints
```bash
# Test analyze endpoint
curl -X POST https://your-app.railway.app/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "address": "1234 Main St, Santa Monica, CA 90401",
    "apn": "4293-001-001",
    "existing_units": 1,
    "include_sb9": true,
    "include_sb35": false,
    "include_ab2011": false,
    "include_density_bonus": true
  }'
```

## Environment Variables Reference

### Backend (Railway)
| Variable | Value | Required |
|----------|-------|----------|
| `PORT` | Auto-set by Railway | Yes |
| `ENVIRONMENT` | `production` | No |

### Frontend (Vercel)
| Variable | Value | Required |
|----------|-------|----------|
| `NEXT_PUBLIC_API_URL` | Railway backend URL | Yes |

## Monitoring and Maintenance

### Railway Monitoring
- Dashboard: https://railway.app/dashboard
- View logs: `railway logs`
- Restart service: `railway restart`

### Vercel Monitoring
- Dashboard: https://vercel.com/dashboard
- View deployments and logs in web interface
- Rollback: Select previous deployment → Promote to Production

## Rollback Procedures

### Backend Rollback (Railway)
1. Go to Railway dashboard
2. Select Deployments tab
3. Find previous working deployment
4. Click "Redeploy"

### Frontend Rollback (Vercel)
1. Go to Vercel dashboard
2. Select Deployments tab
3. Find previous working deployment
4. Click "Promote to Production"

## Troubleshooting

### Common Issues

#### Backend 502/503 Errors
- Check Railway logs: `railway logs`
- Verify health endpoint is responding
- Check if server is binding to `0.0.0.0:$PORT`

#### Frontend Can't Connect to Backend
- Verify `NEXT_PUBLIC_API_URL` is set correctly in Vercel
- Check CORS settings in FastAPI (should allow Vercel domain)
- Verify Railway backend is running

#### Build Failures
- **Railway**: Check Python version matches runtime.txt (3.13)
- **Vercel**: Check Node.js version compatibility (18+)
- Review build logs in respective dashboards

## CI/CD (Optional Future Enhancement)

### GitHub Actions Workflow
Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to Railway
        run: |
          npm install -g @railway/cli
          railway up
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}

  deploy-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to Vercel
        run: |
          npm install -g vercel
          vercel --prod --token=${{ secrets.VERCEL_TOKEN }}
```

## Cost Estimates

- **Railway**: $5-10/month for hobby plan (includes 512MB RAM, shared CPU)
- **Vercel**: Free tier (100GB bandwidth, unlimited deployments)
- **GitHub**: Free for public repositories

## Security Considerations

1. **Environment Variables**: Never commit `.env` files (already in .gitignore)
2. **API Keys**: Store all secrets in platform dashboards, not in code
3. **CORS**: Configure FastAPI to only allow your Vercel domain
4. **Rate Limiting**: Consider adding rate limiting for production API
5. **HTTPS**: Both Railway and Vercel provide SSL certificates automatically

## Next Steps

1. Complete GitHub repository creation and push
2. Deploy backend to Railway
3. Deploy frontend to Vercel
4. Configure environment variables
5. Test production deployment end-to-end
6. Set up custom domains (optional)
7. Configure monitoring and alerts
8. Document any API rate limits or usage quotas
