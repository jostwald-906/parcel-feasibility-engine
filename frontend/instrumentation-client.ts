/**
 * Sentry configuration for client-side error monitoring
 *
 * This file configures Sentry for tracking errors in the browser.
 * Set NEXT_PUBLIC_SENTRY_DSN in your environment variables to enable.
 */

import * as Sentry from '@sentry/nextjs';

const SENTRY_DSN = process.env.NEXT_PUBLIC_SENTRY_DSN;
const SENTRY_ENVIRONMENT = process.env.NEXT_PUBLIC_SENTRY_ENVIRONMENT || process.env.NODE_ENV;

if (SENTRY_DSN) {
  Sentry.init({
    dsn: SENTRY_DSN,
    environment: SENTRY_ENVIRONMENT,

    // Performance Monitoring
    tracesSampleRate: 0.1, // 10% of transactions for performance monitoring

    // Session Replay
    replaysSessionSampleRate: 0.1, // 10% of sessions
    replaysOnErrorSampleRate: 1.0, // 100% of sessions with errors

    integrations: [
      Sentry.replayIntegration({
        maskAllText: true, // Privacy: mask all text
        blockAllMedia: true, // Privacy: block all media
      }),
      Sentry.browserTracingIntegration(),
    ],

    // Only send errors in production environment
    beforeSend(event, hint) {
      const environment = process.env.NEXT_PUBLIC_SENTRY_ENVIRONMENT || process.env.NODE_ENV;

      // Only send to Sentry in production
      if (environment !== 'production') {
        console.log('[Sentry Dev] Error captured locally (not sent):', event.exception?.values?.[0]?.type);
        return null;
      }

      return event;
    },

    // Filter out known browser extension errors
    ignoreErrors: [
      // Browser extensions
      'top.GLOBALS',
      'chrome-extension://',
      'moz-extension://',
      // Network errors that are expected
      'NetworkError',
      'Failed to fetch',
    ],
  });
}

// Export router transition hook for navigation tracking
export const onRouterTransitionStart = Sentry.captureRouterTransitionStart;
