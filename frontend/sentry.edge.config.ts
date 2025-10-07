/**
 * Sentry configuration for edge runtime error monitoring
 *
 * This file configures Sentry for tracking errors in Next.js Edge Runtime.
 * Set SENTRY_DSN in your environment variables to enable.
 */

import * as Sentry from '@sentry/nextjs';

const SENTRY_DSN = process.env.SENTRY_DSN;
const SENTRY_ENVIRONMENT = process.env.SENTRY_ENVIRONMENT || process.env.NODE_ENV;

if (SENTRY_DSN) {
  Sentry.init({
    dsn: SENTRY_DSN,
    environment: SENTRY_ENVIRONMENT,

    // Performance Monitoring
    tracesSampleRate: 0.1, // 10% of transactions for performance monitoring

    // Don't send errors in development
    beforeSend(event, hint) {
      if (process.env.NODE_ENV === 'development') {
        return null;
      }
      return event;
    },
  });
}
