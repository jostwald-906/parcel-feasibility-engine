# Frontend Sentry Setup Guide

Complete guide to configure Sentry error monitoring for the Next.js frontend.

## ✅ What's Already Done

- ✅ Sentry SDK installed (`@sentry/nextjs`)
- ✅ Configuration files created:
  - `sentry.client.config.ts` - Browser error tracking
  - `sentry.server.config.ts` - Server-side error tracking
  - `sentry.edge.config.ts` - Edge runtime error tracking
- ✅ `next.config.ts` wrapped with Sentry
- ✅ Instrumentation hook enabled

## 🚀 Quick Setup (5 minutes)

### Step 1: Get Your Sentry DSN

1. Go to https://sentry.io
2. Navigate to your frontend project (the one showing errors in your dashboard)
3. Click **Settings** → **Client Keys (DSN)**
4. Copy the DSN - looks like: `https://xxxxx@oXXXXXX.ingest.us.sentry.io/XXXXXXX`
5. Note your organization slug from the URL

### Step 2: Add to `.env.local`

Open `frontend/.env.local` and fill in these values:

```bash
# Sentry Configuration
NEXT_PUBLIC_SENTRY_DSN=https://your-dsn-here@sentry.io/project-id
SENTRY_ORG=your-org-slug
SENTRY_PROJECT=parcel-feasibility-frontend
```

### Step 3: Restart Dev Server

```bash
cd frontend
npm run dev
```

The server will pick up the new environment variables.

### Step 4: Test Sentry

Open your browser console and run:

```javascript
Sentry.captureMessage('Test error from frontend');
```

Then check your Sentry dashboard - you should see the message!

## 🎯 For Production (Vercel)

Add the same environment variables to Vercel:

```bash
# Option 1: Using Vercel CLI
vercel env add NEXT_PUBLIC_SENTRY_DSN production
# Paste your DSN when prompted

vercel env add SENTRY_ORG production
# Paste your org slug

vercel env add SENTRY_PROJECT production
# Enter: parcel-feasibility-frontend

# Option 2: Using Vercel Dashboard
```

Or via dashboard:
1. Go to https://vercel.com/dashboard
2. Select your project
3. Go to **Settings** → **Environment Variables**
4. Add each variable for **Production** environment

## 📊 What Will Be Captured

Once configured, Sentry will automatically capture:

- **JavaScript Errors**: All unhandled exceptions
- **React Errors**: Component errors via Error Boundaries
- **Network Errors**: Failed fetch requests
- **Session Replays**: 10% of sessions, 100% with errors
- **Performance**: Page load times, component rendering
- **User Context**: Browser, OS, screen resolution

## 🔍 Verify It's Working

### Local Development

1. Check browser console for: `[Sentry] Successfully initialized`
2. Trigger a test error:
   ```javascript
   window.Sentry.captureException(new Error('Test error'));
   ```
3. Visit Sentry dashboard to see the error

### Production

1. Deploy to Vercel
2. Visit your production URL
3. Check browser Network tab - you should see requests to `sentry.io`
4. Any errors will appear in your Sentry dashboard

## 🛠️ Configuration Details

### Privacy Settings

The configuration uses privacy-first settings:
- ✅ All text masked in session replays
- ✅ All media blocked in session replays
- ✅ No PII (Personally Identifiable Information) sent
- ✅ Browser extension errors filtered out

### Sampling Rates

- **Error Tracking**: 100% of errors captured
- **Session Replay**: 10% of normal sessions
- **Session Replay (with errors)**: 100% of error sessions
- **Performance Monitoring**: 10% of transactions

### Environments

The configuration auto-detects the environment:
- `development` - Local dev server
- `production` - Vercel production
- `preview` - Vercel preview deployments

## 🐛 Troubleshooting

### "Sentry not defined"

Make sure environment variables are set and server is restarted:
```bash
# Check if variables are loaded
echo $NEXT_PUBLIC_SENTRY_DSN

# Restart dev server
npm run dev
```

### "No DSN provided"

- Verify `NEXT_PUBLIC_SENTRY_DSN` is set in `.env.local`
- Ensure it starts with `https://`
- Check there are no extra spaces

### Errors not appearing in Sentry

1. Check browser console for Sentry initialization messages
2. Verify DSN is correct
3. Check Network tab for requests to `sentry.io`
4. Make sure you're looking at the correct Sentry project

### Source maps not uploading

If you're not seeing readable stack traces:

1. Verify `SENTRY_ORG` and `SENTRY_PROJECT` are set
2. Create a Sentry auth token:
   - Go to https://sentry.io/settings/account/api/auth-tokens/
   - Create new token with `project:releases` scope
   - Add to Vercel as `SENTRY_AUTH_TOKEN`

## 📚 Resources

- **Sentry Docs**: https://docs.sentry.io/platforms/javascript/guides/nextjs/
- **Configuration**: [next.config.ts](next.config.ts)
- **Client Config**: [sentry.client.config.ts](sentry.client.config.ts)
- **Server Config**: [sentry.server.config.ts](sentry.server.config.ts)
