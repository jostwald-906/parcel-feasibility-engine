/**
 * Instrumentation file for Next.js
 * Used to initialize Sentry and other monitoring tools
 */

export async function register() {
  // Server-side initialization
  if (process.env.NEXT_RUNTIME === 'nodejs') {
    await import('./sentry.server.config');
  }

  // Edge runtime initialization
  if (process.env.NEXT_RUNTIME === 'edge') {
    await import('./sentry.edge.config');
  }

  // Client-side initialization happens in sentry.client.config.ts
  // which is automatically loaded by the Sentry SDK
}
